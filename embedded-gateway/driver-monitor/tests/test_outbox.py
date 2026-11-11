#!/usr/bin/env python3
"""DurableOutbox 单测(纯标准库)—— 两阶段/幂等/优先级/存储转发/健康。ADR-0001 ③⑤。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.outbox import DurableOutbox, OutboxConfig, OutboxState   # noqa: E402
from uplink.transport import FakeUplinkTransport                     # noqa: E402
from uplink.envelope import EventEnvelope                            # noqa: E402


def _env(eid, phase="open", ts=1.0, prio="high"):
    e = EventEnvelope.from_event({"type": "person_observation", "event_kind": phase,
                                  "event_id": eid, "ts_start": ts})
    e.priority_class = prio
    return e


def _statuses(h):
    return [x["status"] for x in h]


def test_two_phase_queued_sent_custody_delivered():
    tx = FakeUplinkTransport()
    delivered = []
    ob = DurableOutbox(tx, on_delivered=lambda e: delivered.append(e.event_id))
    e = _env("po-1")
    ob.enqueue(e, now=0.0)
    assert ob.state_of(e.msg_key) == OutboxState.QUEUED
    ob.pump(now=0.0)
    assert ob.state_of(e.msg_key) == OutboxState.SENT
    tx.feed_custody_ack(e.msg_key); ob.pump(now=1.0)
    assert ob.state_of(e.msg_key) == OutboxState.CUSTODY
    tx.feed_delivery_ack(e.msg_key); ob.pump(now=2.0)
    assert ob.state_of(e.msg_key) == OutboxState.DELIVERED
    assert delivered == ["po-1"]                      # on_delivered 回调(→ ring.mark_delivered)


def test_enqueue_idempotent():
    ob = DurableOutbox(FakeUplinkTransport())
    e = _env("po-1")
    ob.enqueue(e, 0.0); ob.enqueue(e, 0.0)
    assert ob.pending_count == 1


def test_reenqueue_after_delivered_ignored():
    tx = FakeUplinkTransport(auto_delivery=True)
    ob = DurableOutbox(tx)
    e = _env("po-1")
    ob.enqueue(e, 0.0); ob.pump(0.0); ob.pump(0.1)
    assert ob.state_of(e.msg_key) == OutboxState.DELIVERED
    ob.enqueue(e, 1.0)                                # 已投递再入队 → 幂等忽略
    assert ob.pending_count == 0


def test_delivery_ack_idempotent_calls_once():
    tx = FakeUplinkTransport()
    calls = []
    ob = DurableOutbox(tx, on_delivered=lambda e: calls.append(e.event_id))
    e = _env("po-1")
    ob.enqueue(e, 0.0); ob.pump(0.0)
    tx.feed_delivery_ack(e.msg_key); tx.feed_delivery_ack(e.msg_key)
    ob.pump(1.0); ob.pump(2.0)
    assert calls == ["po-1"]                           # 重复 delivery_ack 只回调一次


def test_store_and_forward_when_offline():
    tx = FakeUplinkTransport(online=False)
    ob = DurableOutbox(tx)
    e = _env("po-1")
    ob.enqueue(e, 0.0); ob.pump(0.0)
    assert ob.state_of(e.msg_key) == OutboxState.QUEUED   # 断网 → 留队,不丢
    tx.set_online(True); ob.pump(1.0)
    assert ob.state_of(e.msg_key) == OutboxState.SENT


def test_redelivery_order_priority_then_occurred_at():
    tx = FakeUplinkTransport()
    ob = DurableOutbox(tx)
    ob.enqueue(_env("low-old", ts=1.0, prio="low"), 0.0)
    ob.enqueue(_env("high-new", ts=9.0, prio="high"), 0.0)
    ob.enqueue(_env("high-old", ts=2.0, prio="high"), 0.0)
    ob.pump(now=0.0)
    order = [env.event_id for env in tx._published]
    assert order == ["high-old", "high-new", "low-old"], order   # high 先(旧先)→ low


def test_custody_stops_resend():
    tx = FakeUplinkTransport()
    ob = DurableOutbox(tx, config=OutboxConfig(resend_after_s=1.0))
    e = _env("po-1")
    ob.enqueue(e, 0.0); ob.pump(0.0)                  # SENT(1 次)
    tx.feed_custody_ack(e.msg_key); ob.pump(1.0)      # → CUSTODY
    before = tx.publish_attempts
    ob.pump(100.0); ob.pump(200.0)                    # CUSTODY 不再重推
    assert tx.publish_attempts == before


def test_sent_resends_after_timeout_until_custody():
    tx = FakeUplinkTransport()
    ob = DurableOutbox(tx, config=OutboxConfig(resend_after_s=10.0))
    e = _env("po-1")
    ob.enqueue(e, 0.0); ob.pump(0.0)                  # 1
    ob.pump(5.0)                                       # 未到重推间隔
    assert tx.publish_attempts == 1
    ob.pump(11.0)                                      # 超间隔 → 重推
    assert tx.publish_attempts == 2


def test_low_priority_dropped_over_cap_not_silent():
    ob = DurableOutbox(FakeUplinkTransport(),
                       config=OutboxConfig(low_priority_cap=2))
    h = []
    for i in range(3):
        h += ob.enqueue(_env(f"low-{i}", ts=float(i), prio="low"), now=float(i))
    assert "low_priority_dropped" in _statuses(h)      # 淘汰但发告警,非静默
    assert ob.pending_count == 2                        # 最旧 low 被淘


def test_unknown_delivery_ack_does_not_poison_key():
    """乱序/误投的 delivery_ack(对应包还没入队)不得毒化 key、不得误回调,
    随后真包必须仍能正常投递(防静默丢失)。"""
    tx = FakeUplinkTransport()
    delivered = []
    ob = DurableOutbox(tx, on_delivered=lambda e: delivered.append(e.event_id))
    tx.feed_delivery_ack("po-1:open"); ob.pump(0.0)   # 先于 enqueue 的 ack
    assert delivered == []                             # 不误回调
    e = _env("po-1"); ob.enqueue(e, 1.0); ob.pump(1.0)  # 真包随后到达
    assert ob.pending_count == 1, "不应被毒化 key 幂等丢弃"
    tx.feed_delivery_ack(e.msg_key); ob.pump(2.0)
    assert ob.state_of(e.msg_key) == OutboxState.DELIVERED
    assert delivered == ["po-1"]


def test_low_cap_does_not_drop_inflight_entry():
    """low 超容量淘汰只淘 QUEUED;在途(SENT)的 low 不丢(否则其证据 clip 会 pin 死)。"""
    ob = DurableOutbox(FakeUplinkTransport(), config=OutboxConfig(low_priority_cap=1))
    a = _env("low-a", ts=1.0, prio="low")
    ob.enqueue(a, 0.0); ob.pump(0.0)                  # a → SENT(在途)
    assert ob.state_of(a.msg_key) == OutboxState.SENT
    h = ob.enqueue(_env("low-b", ts=2.0, prio="low"), now=1.0)   # 超容量
    assert ob.state_of(a.msg_key) == OutboxState.SENT  # 在途 a 不被淘
    assert "low_priority_dropped" in _statuses(h)      # 淘的是 QUEUED 的 b


def test_backlog_health_once():
    ob = DurableOutbox(FakeUplinkTransport(),
                       config=OutboxConfig(max_backlog=2, oldest_age_warn_s=1e9))
    for i in range(3):
        ob.enqueue(_env(f"po-{i}", ts=float(i)), now=0.0)
    h1 = ob.pump(now=0.0)
    assert "uplink_backlog" in _statuses(h1)
    h2 = ob.pump(now=0.0)
    assert "uplink_backlog" not in _statuses(h2)       # 去重


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

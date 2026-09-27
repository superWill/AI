#!/usr/bin/env python3
"""P2c-a 端到端(离线,纯标准库):person_observation(+P2a 证据)→ envelope → outbox →
transport(custody→delivery)→ 回喂 ring;并行四级分类 + 通知升级。

两路径:真人 → 上行成功 + 分类 + (窗外)升级;蒸汽(无 person 事件)→ 零上行。
不变量:证据(evidence_ref)投递确认后才回喂 ring.mark_delivered;断网存储转发不丢。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.envelope import EventEnvelope                        # noqa: E402
from uplink.transport import FakeUplinkTransport                 # noqa: E402
from uplink.outbox import DurableOutbox, OutboxState             # noqa: E402
from uplink.classify import PersonClassifier, Presence           # noqa: E402
from uplink.workorder_cache import WorkOrderCache, WorkOrderWindow  # noqa: E402
from uplink.escalate import NotificationEscalator, EscalateConfig  # noqa: E402


def _person(phase, eid="po-1", ts_start=15.0):
    return {"type": "person_observation", "event_kind": phase,
            "event_id": eid, "ts_start": ts_start, "confidence": 0.9}


def test_person_event_uplinks_and_marks_ring_on_evidence_delivery():
    tx = FakeUplinkTransport(auto_custody=True, auto_delivery=True)
    ring_marks = []
    # 只有带证据(close 的 evidence_ref)投递确认才回喂 ring.mark_delivered
    ob = DurableOutbox(tx, on_delivered=lambda e: ring_marks.append(e.event_id)
                       if e.evidence_ref else None)
    open_env = EventEnvelope.from_event(_person("open"))
    close_env = EventEnvelope.from_event(
        _person("close"), evidence_ref={"evidence_status": "complete", "segments": [1, 2, 3]})
    ob.enqueue(open_env, 0.0); ob.enqueue(close_env, 0.0)
    ob.pump(0.0); ob.pump(0.1)
    assert ob.state_of(open_env.msg_key) == OutboxState.DELIVERED
    assert ob.state_of(close_env.msg_key) == OutboxState.DELIVERED
    assert ring_marks == ["po-1"], ring_marks          # 仅带证据的 close 触发


def test_steam_no_person_event_no_uplink():
    tx = FakeUplinkTransport(auto_custody=True, auto_delivery=True)
    ob = DurableOutbox(tx)
    # 蒸汽期:P1 confirm 没产 person_observation → pipeline 没东西入队
    ob.pump(0.0)
    assert tx.publish_attempts == 0
    assert ob.pending_count == 0


def test_offline_then_reconnect_delivers_without_loss():
    tx = FakeUplinkTransport(online=False, auto_custody=True, auto_delivery=True)
    ob = DurableOutbox(tx)
    e = EventEnvelope.from_event(_person("open"))
    ob.enqueue(e, 0.0); ob.pump(0.0)
    assert ob.state_of(e.msg_key) == OutboxState.QUEUED    # 断网留队
    tx.set_online(True); ob.pump(5.0); ob.pump(5.1)
    assert ob.state_of(e.msg_key) == OutboxState.DELIVERED  # 重连后投递,不丢


def test_classification_in_window_expected_outside_suspected():
    cache = WorkOrderCache(ttl_s=100.0)
    cache.update("v1", 0.0, [WorkOrderWindow("w1", 10.0, 20.0)])
    clf = PersonClassifier(cache)
    assert clf.classify(_person("open", ts_start=15.0), now=50.0)["classification"] \
        == Presence.EXPECTED
    assert clf.classify(_person("open", ts_start=30.0), now=50.0)["classification"] \
        == Presence.SUSPECTED


def test_suspected_triggers_escalation_but_never_changes_class():
    """窗外 → suspected_intrusion → 通知升级;升级只升通知等级,不改事件分类。"""
    cache = WorkOrderCache(ttl_s=100.0)
    cache.update("v1", 0.0, [WorkOrderWindow("w1", 10.0, 20.0)])
    clf = PersonClassifier(cache)
    esc = NotificationEscalator(EscalateConfig(timeouts=(60.0,), max_level=2))
    cls = clf.classify(_person("open", eid="po-9", ts_start=30.0), now=50.0)
    assert cls["classification"] == Presence.SUSPECTED
    n0 = esc.notify("po-9", now=50.0)
    esc_events = esc.tick(now=111.0)                    # 无 ack 超时 → 升通知等级
    assert n0["notify_level"] == 1 and esc_events[0]["notify_level"] == 2
    # 升级事件里没有事件分类字段,分类仍是 suspected(未变 confirmed)
    assert all("classification" not in e for e in [n0] + esc_events)
    assert cls["classification"] == Presence.SUSPECTED


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

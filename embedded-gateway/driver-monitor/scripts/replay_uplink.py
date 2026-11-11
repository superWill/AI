#!/usr/bin/env python3
"""离线回放 —— P2c-a 上行整链(纯逻辑,不依赖板子/MQTT/numpy)。

演示:person_observation → envelope → outbox 两阶段托管 → Fake transport;
并行四级分类 + 通知升级;含一次断网→存储转发→重连投递。

  python3 scripts/replay_uplink.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.envelope import EventEnvelope                        # noqa: E402
from uplink.transport import FakeUplinkTransport                 # noqa: E402
from uplink.outbox import DurableOutbox, OutboxState             # noqa: E402
from uplink.classify import PersonClassifier                     # noqa: E402
from uplink.workorder_cache import WorkOrderCache, WorkOrderWindow  # noqa: E402
from uplink.escalate import NotificationEscalator, EscalateConfig  # noqa: E402


def main() -> int:
    tx = FakeUplinkTransport(auto_custody=True, auto_delivery=True)
    ring_marks = []
    ob = DurableOutbox(tx, on_delivered=lambda e: ring_marks.append(e.event_id)
                       if e.evidence_ref else None)
    cache = WorkOrderCache(ttl_s=3600.0)
    cache.update("wo-v3", as_of_ts=0.0, windows=[WorkOrderWindow("day-shift", 10.0, 20.0)])
    clf = PersonClassifier(cache)
    esc = NotificationEscalator(EscalateConfig(timeouts=(60.0, 180.0), max_level=3))

    # 两个真人事件:A 在工单窗内(expected)、B 在窗外(suspected → 升级)
    persons = [
        ("po-000001", 15.0, {"evidence_status": "complete", "segments": [11, 12, 13]}),
        ("po-000002", 30.0, {"evidence_status": "partial", "segments": [28, 29]}),
    ]

    print("P2c-a 上行回放:两个 person_observation(A 窗内 / B 窗外)+ 一次断网\n")
    for eid, ts, ev_ref in persons:
        cls = clf.classify({"event_id": eid, "ts_start": ts}, now=50.0)
        print(f"  {eid} @t={ts}:分类 = {cls['classification']}  ({cls['reason']})")
        if cls["classification"] == "suspected_intrusion":
            n = esc.notify(eid, now=50.0)
            print(f"           → 通知 L{n['notify_level']}(要求 ack)")
        # OPEN(证据 pending)+ CLOSE(带证据)两条消息,同 event_id 不同 msg_key
        ob.enqueue(EventEnvelope.from_event(
            {"type": "person_observation", "event_kind": "open",
             "event_id": eid, "ts_start": ts}), now=50.0)
        ob.enqueue(EventEnvelope.from_event(
            {"type": "person_observation", "event_kind": "close",
             "event_id": eid, "ts_start": ts}, evidence_ref=ev_ref), now=50.0)

    # 断网:pump 一次(publish 失败留队),再重连
    tx.set_online(False)
    ob.pump(now=51.0)
    print(f"\n  [断网] pump:发送尝试={tx.publish_attempts},待投递={ob.pending_count}(留队不丢)")
    tx.set_online(True)
    ob.pump(now=52.0); ob.pump(now=52.1)               # 重连:发送 + 收 custody/delivery
    print(f"  [重连] pump:已回喂 ring.mark_delivered = {ring_marks}")

    # B 无人 ack → 通知升级
    esc_events = esc.tick(now=111.0)
    for e in esc_events:
        print(f"  [超时] {e['event_id']} 升到通知 L{e['notify_level']}(事件分类不变)")

    all_delivered = all(
        ob.state_of(f"{eid}:{ph}") == OutboxState.DELIVERED
        for eid, _, _ in persons for ph in ("open", "close"))
    ok = (all_delivered and sorted(ring_marks) == ["po-000001", "po-000002"]
          and esc_events and esc_events[0]["notify_level"] == 2)
    print(f"\n结论:{'✅ 两事件均投递;证据回喂 ring;窗外事件通知升级(分类不变)' if ok else '⚠️ 异常'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

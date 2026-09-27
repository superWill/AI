#!/usr/bin/env python3
"""P2a 端到端(离线,纯标准库):person_observation 事件 → ClipManager+Ring → evidence。

两条路径:
  - 真人(有 person_observation)→ 产 ClipManifest,evidence 挂回事件。
  - 蒸汽(只录像、无 person_observation)→ **零 clip**(录像照常进 ring,但不生成证据片段)。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.segment_source import FakeSegmentSource                # noqa: E402
from record.ring import SegmentRing, RingConfig                    # noqa: E402
from record.clip import ClipManager, ClipConfig                    # noqa: E402


def run(person_events, *, gap_at=None, until=15.0, seg_dur=1.0,
        r_pre=5.0, r_post=5.0, ring_cap=10**9):
    """person_events: [(ts, "open"|"close", event_id), ...]。
    返回 (manifests, ring)。段与事件跑同一时钟(seg_dur 步进)。"""
    src = FakeSegmentSource(seg_dur=seg_dur, gap_at=gap_at or set())
    ring = SegmentRing(RingConfig(max_bytes=ring_cap))
    cm = ClipManager(ring, ClipConfig(r_pre=r_pre, r_post=r_post))
    pe = sorted(person_events)
    pi = 0
    manifests = []
    now = 0.0
    while now <= until + 1e-9:
        for seg in src.poll(now):
            ring.add(seg)
            manifests += cm.on_segment(seg)
        while pi < len(pe) and pe[pi][0] <= now + 1e-9:
            ts, kind, eid = pe[pi]; pi += 1
            if kind == "open":
                cm.on_person_open(eid, ts)
            else:
                cm.on_person_close(eid, ts)
        manifests += cm.tick(now)
        ring.prune(now)
        now = round(now + seg_dur, 3)
    manifests += cm.force_finalize_all()
    return manifests, ring


def test_person_event_produces_evidence_clip():
    mans, _ = run([(6.0, "open", "po-1"), (8.0, "close", "po-1")], until=15.0)
    assert len(mans) == 1, [m.event_id for m in mans]
    m = mans[0]
    assert m.event_id == "po-1"
    assert {1, 2, 3, 4, 5} <= set(m.segments), m.segments   # 前卷存在
    assert m.evidence_status == "complete", m.evidence_status


def test_steam_only_no_person_no_clip():
    """蒸汽:只有录像、没有 person_observation → 零 clip(证据不无端生成)。"""
    mans, ring = run([], until=15.0)
    assert mans == [], [m.event_id for m in mans]
    assert len(ring.segments()) > 0, "录像仍照常进 ring"


def test_evidence_ref_carries_event_id_and_status():
    mans, _ = run([(6.0, "open", "po-7"), (8.0, "close", "po-7")], until=15.0)
    ref = mans[0].as_evidence_ref()
    assert ref["event_id"] == "po-7"
    assert ref["evidence_status"] in ("complete", "partial", "unavailable")


def test_gap_in_event_window_yields_partial():
    """事件期录像段含缺口 → evidence_status=partial(端到端)。"""
    mans, _ = run([(6.0, "open", "po-1"), (8.0, "close", "po-1")],
                  gap_at={6}, until=15.0)             # 段6 在事件窗内且 has_gap
    assert mans[0].evidence_status == "partial", mans[0].evidence_status


def test_two_events_get_distinct_clips():
    mans, _ = run([(6.0, "open", "po-1"), (8.0, "close", "po-1"),
                   (20.0, "open", "po-2"), (22.0, "close", "po-2")], until=30.0)
    ids = sorted(m.event_id for m in mans)
    assert ids == ["po-1", "po-2"], ids


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

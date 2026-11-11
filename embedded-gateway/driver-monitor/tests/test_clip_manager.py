#!/usr/bin/env python3
"""ClipManager 单测(纯标准库)—— 前卷/滚动 pin/后卷/evidence_status。

覆盖 7 条中的:#1 前卷存在 · #6 OPEN 滚动 pin · #7 缺口→partial · #5 段丢→unavailable
（含推荐语义:core 段丢→unavailable,仅前/后卷丢→partial）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.ring import SegmentRing, RingConfig                  # noqa: E402
from record.clip import ClipManager, ClipConfig                 # noqa: E402
from record.segment_source import SegmentRecord                 # noqa: E402


def _seg(i, gap=False):
    return SegmentRecord(i, float(i), float(i + 1), f"/rec/{i}.mp4", 100, gap)


def _setup(gap_at=None):
    """ring 容量足够(不触发淘汰);ClipConfig r_pre=r_post=5。"""
    gap_at = gap_at or set()
    ring = SegmentRing(RingConfig(max_bytes=10**9))
    cm = ClipManager(ring, ClipConfig(r_pre=5.0, r_post=5.0))
    return ring, cm, (lambda i: _seg(i, i in gap_at))


def _run_one_clip(ring, cm, mkseg, *, open_ts=6.0, close_ts=8.0,
                  preload=range(6), roll=(6, 7, 8), post=(9, 10, 11, 12, 13),
                  lose=None):
    """预载 preload 段 → open → 滚动 roll 段 → close → 灌 post 段直至 finalize。
    lose: 在 finalize 前 mark_lost 的 seg_id。返回 finalize 出的 manifests。"""
    for i in preload:
        ring.add(mkseg(i))
    cm.on_person_open("po-1", open_ts)
    for i in roll:
        s = mkseg(i); ring.add(s); cm.on_segment(s)
    cm.on_person_close("po-1", close_ts)
    mans = []
    for i in post:
        s = mkseg(i); ring.add(s)
        if lose is not None and i == post[-1]:       # 临 finalize 前制造损失
            ring.mark_lost(lose)
        mans += cm.on_segment(s)
    return mans


def test_preroll_present_and_complete():
    """#1 前卷存在:open 在 t=6,前卷 [1,6] 段 1..5 应被 pin,连续覆盖 → complete。"""
    ring, cm, mk = _setup()
    mans = _run_one_clip(ring, cm, mk)
    assert len(mans) == 1
    m = mans[0]
    assert {1, 2, 3, 4, 5} <= set(m.segments), m.segments   # 前卷
    assert m.evidence_status == "complete", m.evidence_status
    assert m.gaps == [], m.gaps


def test_rolling_pin_while_open():
    """#6 OPEN 滚动 pin:事件期到达的段 6,7,8 应被 pin 进 manifest。"""
    ring, cm, mk = _setup()
    m = _run_one_clip(ring, cm, mk)[0]
    assert {6, 7, 8} <= set(m.segments), m.segments


def test_gap_segment_marks_partial():
    """#7 缺口标 partial:事件期某段 has_gap → evidence_status=partial。"""
    ring, cm, mk = _setup(gap_at={7})
    m = _run_one_clip(ring, cm, mk)[0]
    assert 7 in m.segments
    assert m.evidence_status == "partial", m.evidence_status


def test_lost_core_segment_marks_unavailable():
    """#5 段丢标 unavailable:core 段(重叠事件窗 [6,8])丢 → unavailable。"""
    ring, cm, mk = _setup()
    m = _run_one_clip(ring, cm, mk, lose=6)[0]       # 段6 [6,7] 属 core
    assert m.evidence_status == "unavailable", m.evidence_status
    assert 6 in m.lost_segments
    assert 6 not in m.segments


def test_lost_rollonly_segment_marks_partial():
    """仅前/后卷段丢 → partial(不把整事件判死)。段2 [2,3] 属前卷,非 core。"""
    ring, cm, mk = _setup()
    m = _run_one_clip(ring, cm, mk, lose=2)[0]
    assert m.evidence_status == "partial", m.evidence_status
    assert 2 in m.lost_segments


def test_manifest_times_are_original_not_faked():
    """补投不冒充发生时间:manifest 时间 = 事件原始 ts。"""
    ring, cm, mk = _setup()
    m = _run_one_clip(ring, cm, mk, open_ts=6.0, close_ts=8.0)[0]
    assert (m.ts_start, m.ts_end) == (6.0, 8.0)


def test_tick_finalizes_when_recording_stops():
    """录制停(无后段)时,tick 过后卷截止也能收尾,不留悬空 clip。"""
    ring, cm, mk = _setup()
    for i in range(6):
        ring.add(mk(i))
    cm.on_person_open("po-1", 6.0)
    cm.on_person_close("po-1", 8.0)                  # deadline=13
    assert cm.tick(12.0) == []                        # 未到截止
    mans = cm.tick(13.0)                              # 到截止 → finalize
    assert len(mans) == 1 and mans[0].event_id == "po-1"


def test_evidence_ref_shape():
    ring, cm, mk = _setup()
    m = _run_one_clip(ring, cm, mk)[0]
    ref = m.as_evidence_ref()
    for k in ("event_id", "evidence_status", "segments", "gaps",
              "lost_segments", "ts_start", "ts_end"):
        assert k in ref, k


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

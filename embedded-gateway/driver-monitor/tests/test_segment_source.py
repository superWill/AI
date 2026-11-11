#!/usr/bin/env python3
"""FakeSegmentSource + SegmentRecord 单测(纯标准库)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.segment_source import FakeSegmentSource, SegmentRecord, SegmentSource  # noqa: E402


def test_fake_is_a_segment_source():
    assert isinstance(FakeSegmentSource(), SegmentSource)


def test_poll_emits_completed_segments_only_once():
    src = FakeSegmentSource(seg_dur=1.0)
    assert src.poll(0.5) == []                       # 首段未完成
    segs = src.poll(3.0)                              # 完成 0,1,2(end 1,2,3 ≤3)
    assert [s.seg_id for s in segs] == [0, 1, 2]
    assert src.poll(3.0) == []                        # 不重复吐
    segs2 = src.poll(5.0)
    assert [s.seg_id for s in segs2] == [3, 4]


def test_segment_times_and_bytes():
    src = FakeSegmentSource(seg_dur=2.0, seg_bytes=500)
    s = src.poll(2.0)[0]
    assert (s.start_ts, s.end_ts, s.bytes) == (0.0, 2.0, 500)
    assert s.path.endswith("000000.mp4")


def test_gap_injection():
    src = FakeSegmentSource(seg_dur=1.0, gap_at={2})
    segs = src.poll(5.0)
    assert [s.seg_id for s in segs if s.has_gap] == [2]


def test_overlaps():
    s = SegmentRecord(0, 5.0, 7.0, "/x", 100)
    assert s.overlaps(6.0, 8.0)
    assert s.overlaps(4.0, 6.0)
    assert not s.overlaps(7.0, 9.0)                  # 相接不算叠
    assert not s.overlaps(0.0, 5.0)


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

#!/usr/bin/env python3
"""KeyframeThrottle 单测(纯标准库,注入时钟)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from capture.keyframe import KeyframeThrottle, KeyframeConfig      # noqa: E402


def test_first_offer_yields_first_frame_immediately():
    """事件首帧立即出 first_frame(seq0),不受节流约束。"""
    k = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0))
    cap = k.offer("po-1", now=100.0)
    assert cap is not None
    assert cap.seq == 0 and cap.name == "first_frame" and cap.is_first


def test_second_frame_throttled_until_interval():
    """间隔未到 → None;到点 → frame-001。"""
    k = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0))
    k.offer("po-1", now=100.0)                       # first_frame
    assert k.offer("po-1", now=101.0) is None        # 1s < 5s,节流
    assert k.offer("po-1", now=104.9) is None        # 仍未到
    cap = k.offer("po-1", now=105.0)                 # 到点
    assert cap is not None and cap.seq == 1 and cap.name == "frame-001" and not cap.is_first


def test_max_frames_cap_enforced():
    """每事件封顶(含 first_frame);超出后即便间隔已到也返回 None。"""
    k = KeyframeThrottle(KeyframeConfig(min_interval_s=1.0, max_frames_per_event=3))
    now = 0.0
    got = []
    for _ in range(10):
        cap = k.offer("po-1", now=now)
        if cap is not None:
            got.append(cap.name)
        now += 2.0                                   # 每次都超过间隔
    assert got == ["first_frame", "frame-001", "frame-002"]   # 恰好 3 帧


def test_events_are_independent():
    """不同 event_id 各自计时,互不影响。"""
    k = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0))
    a = k.offer("po-A", now=100.0)
    b = k.offer("po-B", now=100.1)
    assert a.name == "first_frame" and b.name == "first_frame"
    assert k.active_events() == 2


def test_close_releases_state():
    k = KeyframeThrottle()
    k.offer("po-1", now=0.0)
    assert k.active_events() == 1
    k.close("po-1")
    assert k.active_events() == 0
    k.close("po-1")                                  # 幂等,无异常


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

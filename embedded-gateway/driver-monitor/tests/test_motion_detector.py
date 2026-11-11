#!/usr/bin/env python3
"""MotionDetector 单测(需 numpy → 用带 numpy 的 python 跑,如 python3.10 tests/test_motion_detector.py)。

无 numpy 的解释器上自动 skip(退出码 0),不阻塞纯逻辑测试链。
验证:冷启动 warmup 不判决、静止不 moving、白块出现判 moving、前景占比合理。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

try:
    import numpy as np
except ImportError:
    print("SKIP test_motion_detector: numpy 不可用(用 python3.10 跑)")
    sys.exit(0)

from motion.detector import MotionDetector, MotionConfig     # noqa: E402


def _frame(h=360, w=640, block=None, val=255, bg=0):
    """合成帧:bg 底色,block=(y0,y1,x0,x1) 处填 val。"""
    img = np.full((h, w, 3), bg, np.uint8)
    if block is not None:
        y0, y1, x0, x1 = block
        img[y0:y1, x0:x1] = val
    return img


def test_first_frame_and_warmup_never_moving():
    det = MotionDetector(MotionConfig(warmup_s=3.0))
    # 首帧:建背景,warming
    s = det.process(0.0, _frame())
    assert s.warming and not s.moving
    # warmup 期内即便突然出现大白块,也强制不 moving
    s = det.process(1.0, _frame(block=(0, 360, 0, 640), val=255))
    assert s.warming and not s.moving, (s.warming, s.moving)


def test_static_scene_not_moving_after_warmup():
    det = MotionDetector(MotionConfig(warmup_s=1.0))
    t = 0.0
    for _ in range(30):                       # 3s 静止黑底
        s = det.process(t, _frame()); t += 0.1
    assert not s.moving and not s.warming
    assert s.score < 0.001, s.score


def test_appearing_block_triggers_moving():
    det = MotionDetector(MotionConfig(warmup_s=1.0, fg_ratio_thresh=0.01))
    t = 0.0
    for _ in range(20):                       # 2s 静止,背景收敛(且过 warmup)
        det.process(t, _frame()); t += 0.1
    # 突然大白块(占画面 ~1/4)→ 前景占比远超 1%
    s = det.process(t, _frame(block=(0, 180, 0, 320), val=255))
    assert s.moving, s.score
    assert s.score > 0.05, s.score


def test_score_is_foreground_ratio_range():
    det = MotionDetector(MotionConfig(warmup_s=0.0))
    det.process(0.0, _frame())                # 建背景
    s = det.process(0.1, _frame(block=(0, 360, 0, 640), val=255))  # 全屏变白
    assert 0.0 <= s.score <= 1.0
    assert s.score > 0.9, s.score             # 几乎全前景


def test_reset_rebuilds_background():
    det = MotionDetector(MotionConfig(warmup_s=0.0))
    det.process(0.0, _frame())
    det.reset()
    s = det.process(1.0, _frame())            # reset 后首帧应重新建背景
    assert s.warming and not s.moving


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

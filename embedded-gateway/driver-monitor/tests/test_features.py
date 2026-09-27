#!/usr/bin/env python3
"""特征提取单测(纯标准库,Mac 上跑)。用构造的几何点验证 EAR/MAR/头姿换算正确。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from vision.features import (eye_aspect_ratio, mouth_aspect_ratio,   # noqa: E402
                             both_eyes_ear, head_pose_2d)


def _eye(open_h):
    """构造一只眼的 6 点:水平宽 1.0,上下睑各 open_h/2 → EAR = open_h。"""
    return [(0.0, 0.0),               # p1 左角
            (0.3, -open_h / 2), (0.7, -open_h / 2),   # p2,p3 上睑
            (1.0, 0.0),               # p4 右角
            (0.7, open_h / 2), (0.3, open_h / 2)]     # p5,p6 下睑


def test_ear_open_vs_closed():
    open_ear = eye_aspect_ratio(*_eye(0.30))
    closed_ear = eye_aspect_ratio(*_eye(0.06))
    assert open_ear > 0.25, open_ear
    assert closed_ear < 0.12, closed_ear
    assert open_ear > closed_ear


def test_ear_degenerate_zero_width():
    p = (0.0, 0.0)
    assert eye_aspect_ratio(p, p, p, p, p, p) == 0.0


def test_both_eyes_average_and_insufficient_points():
    avg = both_eyes_ear(_eye(0.30), _eye(0.10))
    e_open = eye_aspect_ratio(*_eye(0.30))
    e_clos = eye_aspect_ratio(*_eye(0.10))
    assert abs(avg - (e_open + e_clos) / 2) < 1e-9
    assert both_eyes_ear(_eye(0.3), [(0, 0)] * 3) is None     # 点不够 → None


def test_mar_closed_vs_yawn():
    closed = mouth_aspect_ratio((0, 0), (1.0, 0), (0.5, -0.02), (0.5, 0.02))   # 几乎闭
    yawn = mouth_aspect_ratio((0, 0), (1.0, 0), (0.5, -0.4), (0.5, 0.4))       # 大张
    assert closed < 0.1, closed
    assert yawn > 0.6, yawn


def test_head_pose_center_is_near_zero():
    yaw, pitch = head_pose_2d(nose=(0.0, 0.5), left_eye_c=(-1.0, 0.0),
                              right_eye_c=(1.0, 0.0), mouth_c=(0.0, 1.0))
    assert abs(yaw) < 5, yaw            # 鼻子居中 → yaw≈0
    assert abs(pitch) < 5, pitch        # 鼻尖在眼-嘴中点 → pitch≈0


def test_head_pose_turned_right_positive_yaw():
    # 鼻子偏向右眼 → 正 yaw
    yaw, _ = head_pose_2d(nose=(0.6, 0.5), left_eye_c=(-1.0, 0.0),
                          right_eye_c=(1.0, 0.0), mouth_c=(0.0, 1.0))
    assert yaw > 20, yaw


def test_head_pose_down_positive_pitch():
    # 鼻尖明显下压(接近嘴)→ 正 pitch(低头)
    _, pitch = head_pose_2d(nose=(0.0, 0.9), left_eye_c=(-1.0, 0.0),
                            right_eye_c=(1.0, 0.0), mouth_c=(0.0, 1.0))
    assert pitch > 15, pitch


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

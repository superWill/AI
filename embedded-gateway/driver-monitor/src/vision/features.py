#!/usr/bin/env python3
"""人脸关键点 → 疲劳特征(EAR / MAR / 近似头姿)。纯数学,零第三方依赖,可单测。

这层把"模型吐的关键点坐标"换算成状态机要的标量特征:
  - EAR  眼睛纵横比(Soukupová & Čech):越低越闭眼。
  - MAR  嘴巴纵横比:越高越张嘴(打哈欠)。
  - 头姿  2D 近似 yaw/pitch(看别处/低头)——粗略信号。

**与具体模型解耦**:函数只吃显式点坐标 (x,y);从 68/98/468 点模型到这几个点的映射由
调用方(landmark index spec)负责,不写死在这里。

注意:精确头姿应在板子上用 cv2.solvePnP + 3D 人脸模型;这里的 2D 近似只用于
"是否明显偏离"这种粗判,已在函数里标注。
"""
from __future__ import annotations

import math
from dataclasses import dataclass

Point = tuple[float, float]


def dist(a: Point, b: Point) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def eye_aspect_ratio(p1: Point, p2: Point, p3: Point, p4: Point, p5: Point, p6: Point) -> float:
    """EAR = (|p2-p6| + |p3-p5|) / (2·|p1-p4|)。
    p1,p4 为眼角(水平),p2,p3 上眼睑,p5,p6 下眼睑(dlib 6 点约定)。
    睁眼约 0.25~0.35,闭眼趋近 0。水平间距为 0 时返回 0(退化)。"""
    horiz = dist(p1, p4)
    if horiz <= 1e-6:
        return 0.0
    return (dist(p2, p6) + dist(p3, p5)) / (2.0 * horiz)


def mouth_aspect_ratio(left: Point, right: Point, top: Point, bottom: Point) -> float:
    """MAR = 竖直开口 / 水平嘴宽。闭嘴接近 0,打哈欠时显著增大(>0.6)。
    left/right 为嘴角,top/bottom 为上下唇中点。"""
    width = dist(left, right)
    if width <= 1e-6:
        return 0.0
    return dist(top, bottom) / width


def both_eyes_ear(left_eye: list[Point], right_eye: list[Point]) -> float | None:
    """左右眼各 6 点,取两眼 EAR 均值;任一不足 6 点返回 None。"""
    if len(left_eye) < 6 or len(right_eye) < 6:
        return None
    le = eye_aspect_ratio(*left_eye[:6])
    re = eye_aspect_ratio(*right_eye[:6])
    return (le + re) / 2.0


def head_pose_2d(nose: Point, left_eye_c: Point, right_eye_c: Point,
                 mouth_c: Point) -> tuple[float, float]:
    """**2D 近似** yaw/pitch(度),仅供"是否明显偏离"粗判,非精确姿态。
    yaw:鼻子在两眼水平中点的左右偏移 / 两眼间距 → 映射到角度(扭头时鼻子偏向一侧)。
    pitch:鼻子相对"眼线→嘴"竖直区间的位置 → 偏离中位映射到角度(低头时鼻尖下压比例变化)。
    返回 (yaw_deg, pitch_deg);右转为正 yaw,低头为正 pitch。"""
    eye_mid_x = (left_eye_c[0] + right_eye_c[0]) / 2.0
    eye_dist = dist(left_eye_c, right_eye_c)
    if eye_dist <= 1e-6:
        return 0.0, 0.0
    # yaw:鼻子横向偏离两眼中点的比例 → ±60° 量程的线性近似
    yaw = max(-1.0, min(1.0, (nose[0] - eye_mid_x) / (eye_dist * 0.5))) * 60.0
    # pitch:鼻尖在 (眼线 y → 嘴 y) 区间内的相对位置,0.5 为中性
    eye_mid_y = (left_eye_c[1] + right_eye_c[1]) / 2.0
    span = mouth_c[1] - eye_mid_y
    if abs(span) <= 1e-6:
        return yaw, 0.0
    rel = (nose[1] - eye_mid_y) / span            # 鼻尖偏下 → rel 偏大 → 低头
    pitch = max(-1.0, min(1.0, (rel - 0.5) / 0.5)) * 45.0
    return yaw, pitch


@dataclass
class LandmarkSpec:
    """模型关键点索引 → 本层所需点的映射(各模型不同,配置化)。
    索引指向一个 [(x,y), ...] 关键点数组。"""
    left_eye: list[int]      # 6 个:p1..p6
    right_eye: list[int]     # 6 个
    mouth_corners: tuple[int, int]   # (左角, 右角)
    mouth_vert: tuple[int, int]      # (上唇中, 下唇中)
    nose_tip: int
    left_eye_center: int
    right_eye_center: int
    mouth_center: int

    def pick(self, lms: list[Point], idx) -> Point:
        return lms[idx]


def features_from_landmarks(lms: list[Point], spec: LandmarkSpec) -> dict:
    """一组关键点 + 索引规格 → {ear, mar, yaw, pitch}。点不够时对应项为 None。"""
    out: dict = {"ear": None, "mar": None, "yaw": None, "pitch": None}
    n = len(lms)
    need = max(spec.left_eye + spec.right_eye + list(spec.mouth_corners)
               + list(spec.mouth_vert)
               + [spec.nose_tip, spec.left_eye_center, spec.right_eye_center, spec.mouth_center])
    if n <= need:
        return out
    out["ear"] = both_eyes_ear([lms[i] for i in spec.left_eye],
                               [lms[i] for i in spec.right_eye])
    out["mar"] = mouth_aspect_ratio(lms[spec.mouth_corners[0]], lms[spec.mouth_corners[1]],
                                    lms[spec.mouth_vert[0]], lms[spec.mouth_vert[1]])
    yaw, pitch = head_pose_2d(lms[spec.nose_tip], lms[spec.left_eye_center],
                              lms[spec.right_eye_center], lms[spec.mouth_center])
    out["yaw"], out["pitch"] = yaw, pitch
    return out

#!/usr/bin/env python3
"""PFLD98(WFLW)在 RKNPU 上推理 → 98 关键点 → 真 EAR/MAR。

WFLW98 索引(对照 yakhyo/face-landmark-detection 的 TRACKED_POINTS / 3D 模型点 / Mirror98.txt):
  轮廓 0-32 · 左眉 33-41 · 右眉 42-50 · 鼻 51-59 · 左眼 60-67 · 右眼 68-75 ·
  外唇 76-87 · 内唇 88-95 · 左瞳 96 · 右瞳 97

EAR(每眼 6 点,Soukupová-Čech):
  左眼:角 60(外)/64(内),上睑 61,63,下睑 67,65
  右眼:角 68(内)/72(外),上睑 69,71,下睑 75,73
MAR(内唇):角 88/92,上 89,91,下 95,93

输入:112x112 RGB 人脸 ROI(已 resize)。模型 rknn 建时 mean0/std255 → 喂 uint8 RGB。
输出关键点为归一化 [0,1] → ×112 得 ROI 内像素坐标(EAR/MAR 是比值,scale 无关)。
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from rknnlite.api import RKNNLite

from vision.features import dist, eye_aspect_ratio

# WFLW98 关键点分组
LEFT_EYE = [60, 61, 62, 63, 64, 65, 66, 67]
RIGHT_EYE = [68, 69, 70, 71, 72, 73, 74, 75]
INNER_LIP = [88, 89, 90, 91, 92, 93, 94, 95]
# solvePnP 14 点(repo TRACKED_POINTS;真 PnP 需 cv2,板上缺 → 头姿暂留 2D 近似)
TRACKED_POINTS = [33, 38, 50, 46, 60, 64, 68, 72, 55, 59, 76, 82, 85, 16]


class PFLDLandmarkRKNN:
    """PFLD98 推理器。infer(face112) → (98,2) ROI 内像素坐标。"""

    def __init__(self, model_path: str, *, size: int = 112,
                 core_mask=RKNNLite.NPU_CORE_AUTO):
        self.size = size
        self._rknn = RKNNLite()
        if self._rknn.load_rknn(model_path) != 0:
            raise RuntimeError(f"load_rknn failed: {model_path}")
        if self._rknn.init_runtime(core_mask=core_mask) != 0:
            raise RuntimeError("init_runtime failed")

    def infer(self, face_rgb_112: np.ndarray) -> np.ndarray:
        if face_rgb_112.shape[0] != self.size or face_rgb_112.shape[1] != self.size:
            raise ValueError(f"期望 {self.size}x{self.size},收到 {face_rgb_112.shape[:2]}")
        inp = np.ascontiguousarray(face_rgb_112[np.newaxis, ...])
        outs = self._rknn.inference(inputs=[inp])
        lm = next(o for o in outs if o.reshape(-1).shape[0] == 196).reshape(98, 2)
        if lm.max() <= 2.0:                      # 归一化 → ROI 像素
            lm = lm * self.size
        return lm

    def release(self) -> None:
        self._rknn.release()


def _ear_6(lm: np.ndarray, idx) -> float:
    """idx 为 8 点眼序 [外角,上1,上2,内角?...] 实际传 (外角,上a,上b,内角,下a,下b) 6 点。"""
    p = [tuple(lm[i]) for i in idx]
    return eye_aspect_ratio(*p)


def ear_left(lm: np.ndarray) -> float:
    # p1=外角60 p2=上睑61 p3=上睑63 p4=内角64 p5=下睑65 p6=下睑67
    return eye_aspect_ratio(tuple(lm[60]), tuple(lm[61]), tuple(lm[63]),
                            tuple(lm[64]), tuple(lm[65]), tuple(lm[67]))


def ear_right(lm: np.ndarray) -> float:
    # p1=内角68 p2=上睑69 p3=上睑71 p4=外角72 p5=下睑73 p6=下睑75
    return eye_aspect_ratio(tuple(lm[68]), tuple(lm[69]), tuple(lm[71]),
                            tuple(lm[72]), tuple(lm[73]), tuple(lm[75]))


def ear_both(lm: np.ndarray) -> float:
    return (ear_left(lm) + ear_right(lm)) / 2.0


def mar(lm: np.ndarray) -> float:
    """内唇 MAR = (|89-95|+|91-93|) / (2·|88-92|)。闭嘴 ~0,张嘴/哈欠显著增大。"""
    width = dist(tuple(lm[88]), tuple(lm[92]))
    if width <= 1e-6:
        return 0.0
    return (dist(tuple(lm[89]), tuple(lm[95])) + dist(tuple(lm[91]), tuple(lm[93]))) / (2.0 * width)


def features_from_pfld(lm: np.ndarray) -> dict:
    """98 点 → {ear, mar}(纯数学,板上可跑)。头姿(solvePnP)需 cv2,另算。"""
    return {"ear": ear_both(lm), "mar": mar(lm)}

#!/usr/bin/env python3
"""RetinaFace(mobilenet)在 RKNPU 上的推理 + 后处理 → 人脸框 + 5 关键点。

板子(BL412B/RK3568)用 `rknnlite` 跑量化后的 RetinaFace_mobile320.rknn。后处理(PriorBox/
box_decode/decode_landm/NMS)照搬 airockchip/rknn_model_zoo 的 RetinaFace 示例,纯 numpy,
无 cv2 依赖。

**关键点顺序(RetinaFace 5 点约定)**:[左眼, 右眼, 鼻尖, 左嘴角, 右嘴角]。
本层只产出几何点;EAR/MAR(需眼睑/唇缘稠密点)5 点给不了 → 上层只取头姿。

输入约定:**已 letterbox 到 model_size 的 RGB uint8**(由 GStreamer videoscale add-borders 出),
故后处理直接在 model_size 坐标系内工作,不再做 letterbox 反算(疲劳特征是比值/相对量,scale 无关)。
"""
from __future__ import annotations

from math import ceil
from itertools import product
from typing import Optional

import numpy as np

from rknnlite.api import RKNNLite

# RetinaFace 5 点在 landmarks 向量(长度 10)中的下标
LM_LEFT_EYE = 0
LM_RIGHT_EYE = 1
LM_NOSE = 2
LM_MOUTH_L = 3
LM_MOUTH_R = 4


def prior_box(image_size) -> np.ndarray:
    """生成 anchor 先验框(中心 + 宽高,归一化)。支持 (320,320)/(640,640)。"""
    min_sizes = [[16, 32], [64, 128], [256, 512]]
    steps = [8, 16, 32]
    feature_maps = [[ceil(image_size[0] / s), ceil(image_size[1] / s)] for s in steps]
    anchors = []
    for k, f in enumerate(feature_maps):
        for i, j in product(range(f[0]), range(f[1])):
            for min_size in min_sizes[k]:
                s_kx = min_size / image_size[1]
                s_ky = min_size / image_size[0]
                cx = (j + 0.5) * steps[k] / image_size[1]
                cy = (i + 0.5) * steps[k] / image_size[0]
                anchors += [cx, cy, s_kx, s_ky]
    return np.array(anchors, dtype=np.float32).reshape(-1, 4)


def _box_decode(loc: np.ndarray, priors: np.ndarray) -> np.ndarray:
    variances = [0.1, 0.2]
    boxes = np.concatenate((
        priors[:, :2] + loc[:, :2] * variances[0] * priors[:, 2:],
        priors[:, 2:] * np.exp(loc[:, 2:] * variances[1])), axis=1)
    boxes[:, :2] -= boxes[:, 2:] / 2
    boxes[:, 2:] += boxes[:, :2]
    return boxes


def _decode_landm(pre: np.ndarray, priors: np.ndarray) -> np.ndarray:
    v = 0.1
    return np.concatenate([
        priors[:, :2] + pre[:, 2 * i:2 * i + 2] * v * priors[:, 2:]
        for i in range(5)
    ], axis=1)


def _nms(dets: np.ndarray, thresh: float) -> list:
    x1, y1, x2, y2, scores = dets[:, 0], dets[:, 1], dets[:, 2], dets[:, 3], dets[:, 4]
    areas = (x2 - x1 + 1) * (y2 - y1 + 1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h
        ovr = inter / (areas[i] + areas[order[1:]] - inter)
        order = order[np.where(ovr <= thresh)[0] + 1]
    return keep


class RetinaFaceRKNN:
    """单脸优先的 RetinaFace 推理器。`infer(rgb)` 返回最高分人脸或 None。"""

    def __init__(self, model_path: str, *, model_size=(320, 320),
                 conf_thresh: float = 0.5, nms_thresh: float = 0.4,
                 core_mask=RKNNLite.NPU_CORE_AUTO):
        self.model_size = model_size
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh
        self._priors = prior_box(model_size)
        self._scale_box = np.array([model_size[1], model_size[0]] * 2, dtype=np.float32)
        self._scale_lm = np.array([model_size[1], model_size[0]] * 5, dtype=np.float32)

        self._rknn = RKNNLite()
        if self._rknn.load_rknn(model_path) != 0:
            raise RuntimeError(f"load_rknn failed: {model_path}")
        if self._rknn.init_runtime(core_mask=core_mask) != 0:
            raise RuntimeError("init_runtime failed")

    def infer(self, rgb: np.ndarray) -> Optional[dict]:
        """rgb: model_size 的 letterboxed RGB uint8 (H,W,3)。返回最优脸或 None。
        返回 dict:{score, box[x1,y1,x2,y2], landmarks: np.ndarray(5,2)} 坐标在 model_size 内。"""
        h, w = self.model_size
        if rgb.shape[0] != h or rgb.shape[1] != w:
            raise ValueError(f"期望 {self.model_size} 输入,收到 {rgb.shape[:2]}")
        # 该 rknnlite(2.0.0b0)对 static_shape 模型要 4 维 NHWC
        inp = np.ascontiguousarray(rgb[np.newaxis, ...])
        outputs = self._rknn.inference(inputs=[inp])
        if not outputs or len(outputs) < 3:
            return None
        # 不假设输出顺序:按元素数识别 conf(2N)/loc(4N)/landms(10N)。
        # 三者 N 相同 → 总元素数 2N < 4N < 10N,排序即得。
        by_size = sorted(outputs, key=lambda a: a.size)
        conf = by_size[0].reshape(-1, 2)
        loc = by_size[1].reshape(-1, 4)
        landms = by_size[2].reshape(-1, 10)

        scores = conf[:, 1]
        keep0 = scores > self.conf_thresh
        if not keep0.any():
            return None
        boxes = _box_decode(loc[keep0], self._priors[keep0]) * self._scale_box
        lms = _decode_landm(landms[keep0], self._priors[keep0]) * self._scale_lm
        scores = scores[keep0]

        order = scores.argsort()[::-1]
        boxes, lms, scores = boxes[order], lms[order], scores[order]
        dets = np.hstack((boxes, scores[:, None])).astype(np.float32)
        keep = _nms(dets, self.nms_thresh)
        if not keep:
            return None
        i = keep[0]                       # 最高分人脸(车内单驾驶员场景取一张)
        lm = lms[i].reshape(5, 2)
        return {"score": float(scores[i]), "box": boxes[i].tolist(), "landmarks": lm}

    def release(self) -> None:
        self._rknn.release()


def head_pose_points(lm: np.ndarray):
    """从 5 关键点取 head_pose_2d 需要的 (nose, left_eye, right_eye, mouth_center)。"""
    nose = (float(lm[LM_NOSE][0]), float(lm[LM_NOSE][1]))
    le = (float(lm[LM_LEFT_EYE][0]), float(lm[LM_LEFT_EYE][1]))
    re = (float(lm[LM_RIGHT_EYE][0]), float(lm[LM_RIGHT_EYE][1]))
    mc = ((float(lm[LM_MOUTH_L][0]) + float(lm[LM_MOUTH_R][0])) / 2.0,
          (float(lm[LM_MOUTH_L][1]) + float(lm[LM_MOUTH_R][1])) / 2.0)
    return nose, le, re, mc

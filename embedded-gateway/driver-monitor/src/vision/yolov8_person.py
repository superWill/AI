#!/usr/bin/env python3
"""yolov8n 在 RKNPU 上的推理 + 后处理 → 只出人体框(P1b,替代 person_detector.py 的 Mock)。

板子(BL412B/RK3568)用 `rknnlite` 跑量化后的 yolov8n rk3568 rknn(**待转换,还没有 .rknn
文件** —— rknn_model_zoo 只发 onnx,.rknn 要本地跑 rknn-toolkit2 量化转出来)。后处理(DFL
box 解码 + NMS)照搬 airockchip/rknn_model_zoo 的 yolov8 python demo,把 torch 换成纯
numpy(板上不装 torch),并且只取 COCO class 0(person)这一路,不算全 80 类。

**坐标约定**:`detect()` 吃**原始整帧** RGB(不要求调用方先 letterbox),内部自己
letterbox 到 model_size 再喂模型,输出的 PersonBox 坐标已经反算回原图像素坐标系
——跟 `PersonDetector` 抽象接口的约定一致(下游 ROI mask 按原图坐标算 contains)。

输出格式说明(yolov8n rknn_model_zoo 优化导出,defualt_branch=3,每 branch 3 个 tensor):
  [box(1,64,H,W), class_conf(1,80,H,W), score_sum(1,1,H,W)(忽略)] × 3 个 stride(8/16/32)。
box 用 DFL(Distribution Focal Loss)解码:64 通道 = 4 边 × 16 bins softmax 期望。
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from util.imgproc import letterbox
from vision.person_detector import PersonBox, PersonDetector

PERSON_CLASS_ID = 0        # COCO id 0 = "person",且是 80 类里的第一个,channel 0 直接就是
DFL_BINS = 16               # DFL 每边 bin 数(yolov8n 默认)
STRIDES = (8, 16, 32)


def _softmax(x: np.ndarray, axis: int) -> np.ndarray:
    x = x - x.max(axis=axis, keepdims=True)
    e = np.exp(x)
    return e / e.sum(axis=axis, keepdims=True)


def _dfl_decode(position: np.ndarray) -> np.ndarray:
    """position: (1, 4*DFL_BINS, H, W) → (1, 4, H, W) 每边期望值(纯 numpy,替代参考实现的 torch)。"""
    n, c, h, w = position.shape
    y = position.reshape(n, 4, DFL_BINS, h, w)
    y = _softmax(y, axis=2)
    bins = np.arange(DFL_BINS, dtype=np.float32).reshape(1, 1, DFL_BINS, 1, 1)
    return (y * bins).sum(axis=2)


def _box_process(position: np.ndarray, stride: int, model_size) -> np.ndarray:
    """position: (1,64,H,W) 单 branch box 输出 → (1,4,H,W) xyxy,单位:model_size 像素。"""
    grid_h, grid_w = position.shape[2:4]
    col, row = np.meshgrid(np.arange(grid_w), np.arange(grid_h))
    col = col.reshape(1, 1, grid_h, grid_w).astype(np.float32)
    row = row.reshape(1, 1, grid_h, grid_w).astype(np.float32)
    grid = np.concatenate((col, row), axis=1)

    dist = _dfl_decode(position)
    xy1 = grid + 0.5 - dist[:, 0:2]
    xy2 = grid + 0.5 + dist[:, 2:4]
    return np.concatenate((xy1 * stride, xy2 * stride), axis=1)


def _sp_flatten(a: np.ndarray) -> np.ndarray:
    ch = a.shape[1]
    return a.transpose(0, 2, 3, 1).reshape(-1, ch)


def _nms(boxes: np.ndarray, scores: np.ndarray, thresh: float) -> list:
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = np.maximum(0.0, x2 - x1) * np.maximum(0.0, y2 - y1)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)
        xx1 = np.maximum(x1[i], x1[order[1:]]); yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]]); yy2 = np.minimum(y2[i], y2[order[1:]])
        inter = np.maximum(0.0, xx2 - xx1) * np.maximum(0.0, yy2 - yy1)
        ovr = inter / (areas[i] + areas[order[1:]] - inter + 1e-9)
        order = order[1:][ovr <= thresh]
    return keep


def decode_person_boxes(outputs: list, model_size, conf_thresh: float, nms_thresh: float) -> np.ndarray:
    """outputs:9 个 rknn 输出张量(顺序不保证,按 shape 归位)。返回 (N,5) xyxy+score,
    model_size 像素坐标系,已按 person 类过滤 + NMS。纯函数,不需要 RKNNLite,单测直接调。"""
    by_branch = sorted(outputs, key=lambda a: a.shape[2] * a.shape[3], reverse=True)
    boxes_all, scores_all = [], []
    for i, stride in enumerate(STRIDES):
        box_raw, cls_raw = by_branch[3 * i], by_branch[3 * i + 1]   # score_sum(第3个)不用
        boxes_all.append(_sp_flatten(_box_process(box_raw, stride, model_size)))
        scores_all.append(_sp_flatten(cls_raw)[:, PERSON_CLASS_ID])
    boxes = np.concatenate(boxes_all, axis=0)
    scores = np.concatenate(scores_all, axis=0)

    keep0 = scores >= conf_thresh
    if not keep0.any():
        return np.zeros((0, 5), dtype=np.float32)
    boxes, scores = boxes[keep0], scores[keep0]
    keep = _nms(boxes, scores, nms_thresh)
    if not keep:
        return np.zeros((0, 5), dtype=np.float32)
    return np.hstack((boxes[keep], scores[keep, None])).astype(np.float32)


class Yolov8nPersonDetector(PersonDetector):
    """真 RKNN 人体检测后端(P1b)。吃原始整帧 RGB,吐原图坐标系的 PersonBox。"""

    def __init__(self, model_path: str, model_size: int = 640,
                 conf_thresh: float = 0.25, nms_thresh: float = 0.45, core_mask=None):
        from rknnlite.api import RKNNLite   # 懒加载:只在真用板子后端时才需要 rknnlite(板专属包)
        if core_mask is None:
            core_mask = RKNNLite.NPU_CORE_AUTO   # 传 None 会被当成"显式设置",rk3568 单核不支持 core_mask,报错;NPU_CORE_AUTO 是唯一验证过能用的值(retinaface.py 同款)
        self.model_size = (model_size, model_size)
        self.conf_thresh = conf_thresh
        self.nms_thresh = nms_thresh

        self._rknn = RKNNLite()
        if self._rknn.load_rknn(model_path) != 0:
            raise RuntimeError(f"load_rknn failed: {model_path}")
        if self._rknn.init_runtime(core_mask=core_mask) != 0:
            raise RuntimeError("init_runtime failed")

    def detect(self, rgb: np.ndarray) -> list:
        lb, scale, padx, pady = letterbox(rgb, self.model_size[0])
        inp = np.ascontiguousarray(lb[np.newaxis, ...])
        outputs = self._rknn.inference(inputs=[inp])
        if not outputs or len(outputs) < 9:
            return []
        dets = decode_person_boxes(outputs, self.model_size, self.conf_thresh, self.nms_thresh)
        result = []
        for x1, y1, x2, y2, score in dets:
            # letterbox 反算:原图 = (letterbox 坐标 - pad) / scale
            result.append(PersonBox(
                x1=(x1 - padx) / scale, y1=(y1 - pady) / scale,
                x2=(x2 - padx) / scale, y2=(y2 - pady) / scale,
                score=float(score)))
        return result

    def release(self) -> None:
        self._rknn.release()

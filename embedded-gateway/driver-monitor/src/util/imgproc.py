#!/usr/bin/env python3
"""纯 numpy 图像处理 —— 板上无 cv2/PIL,人脸 ROI 裁剪 + resize 自己实现。"""
from __future__ import annotations

from typing import Tuple

import numpy as np


def crop_with_margin(img: np.ndarray, box, margin: float = 0.2) -> Tuple[np.ndarray, int, int, float, float]:
    """按 box[x1,y1,x2,y2] 扩 margin 比例裁人脸方形 ROI(便于 PFLD 对齐)。
    返回 (crop, ox, oy, sx, sy):crop 起点(ox,oy)及到原图的缩放(此处恒等,缩放在 resize 阶段)。"""
    h, w = img.shape[:2]
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    cx, cy = x1 + bw / 2.0, y1 + bh / 2.0
    side = max(bw, bh) * (1.0 + margin)
    nx1 = int(max(0, cx - side / 2)); ny1 = int(max(0, cy - side / 2))
    nx2 = int(min(w, cx + side / 2)); ny2 = int(min(h, cy + side / 2))
    return img[ny1:ny2, nx1:nx2], nx1, ny1, 1.0, 1.0


def letterbox(img: np.ndarray, size: int, pad_val: int = 114):
    """等比缩放到 size×size 并补边(letterbox)。返回 (out, scale, padx, pady),
    可用 (x_orig = (x_lb - padx)/scale) 把 letterbox 内坐标映射回原图。"""
    h, w = img.shape[:2]
    scale = size / max(h, w)
    nh, nw = int(round(h * scale)), int(round(w * scale))
    resized = resize_bilinear(img, nh, nw)
    out = np.full((size, size, 3), pad_val, np.uint8)
    padx = (size - nw) // 2
    pady = (size - nh) // 2
    out[pady:pady + nh, padx:padx + nw] = resized
    return out, scale, padx, pady


def resize_bilinear(img: np.ndarray, out_h: int, out_w: int) -> np.ndarray:
    """双线性 resize(纯 numpy,向量化)。img:(H,W,3) uint8 → (out_h,out_w,3) uint8。"""
    h, w = img.shape[:2]
    if h == out_h and w == out_w:
        return img.astype(np.uint8)
    # 目标像素中心映射回源坐标(align_corners=False 约定)
    ys = (np.arange(out_h) + 0.5) * (h / out_h) - 0.5
    xs = (np.arange(out_w) + 0.5) * (w / out_w) - 0.5
    ys = np.clip(ys, 0, h - 1); xs = np.clip(xs, 0, w - 1)
    y0 = np.floor(ys).astype(np.int32); x0 = np.floor(xs).astype(np.int32)
    y1 = np.minimum(y0 + 1, h - 1); x1 = np.minimum(x0 + 1, w - 1)
    wy = (ys - y0)[:, None, None]; wx = (xs - x0)[None, :, None]
    img = img.astype(np.float32)
    Ia = img[y0][:, x0]; Ib = img[y0][:, x1]
    Ic = img[y1][:, x0]; Id = img[y1][:, x1]
    top = Ia * (1 - wx) + Ib * wx
    bot = Ic * (1 - wx) + Id * wx
    out = top * (1 - wy) + bot * wy
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)

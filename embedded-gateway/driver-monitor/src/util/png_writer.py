#!/usr/bin/env python3
"""纯标准库 PNG 编码 + numpy 画框/点 —— BL412B 上无 cv2/PIL/ffmpeg,用它存证截图。

PNG 用 zlib(标准库)即可编码,产物任意看图器可开。画标注靠直接改 numpy 像素,无第三方依赖。
"""
from __future__ import annotations

import struct
import zlib
from typing import Sequence, Tuple

import numpy as np

Color = Tuple[int, int, int]


def write_png(path: str, rgb: np.ndarray) -> None:
    """rgb: (H,W,3) uint8 → 8-bit RGB PNG。纯 zlib,无依赖。"""
    if rgb.dtype != np.uint8:
        rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    h, w, _ = rgb.shape
    # 每行前置 1 字节 filter(0=None),再接 RGB 原始字节
    filtered = np.hstack([np.zeros((h, 1), np.uint8), rgb.reshape(h, w * 3)])
    idat = zlib.compress(filtered.tobytes(), 6)

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)   # 8bit, color type 2 = RGB
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


def draw_box(rgb: np.ndarray, x1: int, y1: int, x2: int, y2: int,
             color: Color = (0, 255, 0), thickness: int = 2) -> None:
    """矩形框(原地)。坐标越界自动夹取。"""
    h, w, _ = rgb.shape
    x1, x2 = sorted((max(0, min(w - 1, int(x1))), max(0, min(w - 1, int(x2)))))
    y1, y2 = sorted((max(0, min(h - 1, int(y1))), max(0, min(h - 1, int(y2)))))
    t = max(1, thickness)
    rgb[y1:y1 + t, x1:x2 + 1] = color
    rgb[max(y1, y2 - t + 1):y2 + 1, x1:x2 + 1] = color
    rgb[y1:y2 + 1, x1:x1 + t] = color
    rgb[y1:y2 + 1, max(x1, x2 - t + 1):x2 + 1] = color


def draw_points(rgb: np.ndarray, pts: Sequence[Sequence[float]],
                color: Color = (255, 0, 0), radius: int = 2) -> None:
    """在每个 (x,y) 画实心小方点(原地)。"""
    h, w, _ = rgb.shape
    r = max(0, radius)
    for p in pts:
        x, y = int(p[0]), int(p[1])
        rgb[max(0, y - r):min(h, y + r + 1), max(0, x - r):min(w, x + r + 1)] = color


def draw_border(rgb: np.ndarray, color: Color, thickness: int = 6) -> None:
    """整幅边框(严重度色条:alarm 红 / warning 橙)。"""
    t = max(1, thickness)
    rgb[:t, :] = color
    rgb[-t:, :] = color
    rgb[:, :t] = color
    rgb[:, -t:] = color

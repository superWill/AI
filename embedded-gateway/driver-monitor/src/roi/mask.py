#!/usr/bin/env python3
"""每摄 ROI 掩膜 —— 过滤落在关注区外的人体框 / 运动,压掉盲区与固定干扰源。

换热站/消防站现场:蒸汽出口、指示灯、热管往往集中在画面固定区域(ADR-0001 强干扰背景)。
给每摄配一个多边形 ROI(只保留门口/通道等真正关心的区域),区外的框/运动一律不计,
是压误报最直接的一招。

- 多边形点在内判定:射线法(纯 stdlib)。**空多边形 = 全帧**(ROI 关闭,单摄免配即用)。
- 人体框过滤:默认按框中心是否落在 ROI 内。
- 运动 ROI:`to_bitmap(w,h)` 出降采样布尔掩膜,喂给 MotionDetector 只在区内数前景(可选,需 numpy)。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RoiMask:
    """一路摄像头的关注区。polygon 为 [(x,y), ...] 像素坐标;空 = 全帧。"""
    polygon: list[tuple[float, float]] = field(default_factory=list)

    def __post_init__(self):
        if self.polygon and len(self.polygon) < 3:
            raise ValueError(f"ROI 多边形至少 3 个点,得到 {len(self.polygon)}")

    @property
    def enabled(self) -> bool:
        return bool(self.polygon)

    def contains_point(self, x: float, y: float) -> bool:
        """点是否在多边形内(射线法)。空多边形 → 恒 True(全帧)。"""
        poly = self.polygon
        if not poly:
            return True
        inside = False
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside

    def box_in_roi(self, box) -> bool:
        """人体框是否算「在 ROI 内」——按框中心判定。"""
        cx, cy = box.center
        return self.contains_point(cx, cy)

    def filter_boxes(self, boxes: list) -> list:
        """只保留中心落在 ROI 内的框。空多边形 → 原样返回。"""
        if not self.polygon:
            return list(boxes)
        return [b for b in boxes if self.box_in_roi(b)]

    def to_bitmap(self, w: int, h: int):
        """出 (h,w) 布尔掩膜(True=区内),供运动检测按区数前景。需 numpy。
        空多边形 → 全 True。像素中心判定。"""
        import numpy as np
        if not self.polygon:
            return np.ones((h, w), dtype=bool)
        ys = np.arange(h) + 0.5
        xs = np.arange(w) + 0.5
        mask = np.zeros((h, w), dtype=bool)
        poly = self.polygon
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            cond_y = (yi > ys) != (yj > ys)                    # (h,)
            # 每行的交点 x 阈值(cond_y 为真处才有意义)
            with np.errstate(divide="ignore", invalid="ignore"):
                xint = (xj - xi) * (ys - yi) / (yj - yi) + xi   # (h,)
            row_hit = cond_y[:, None] & (xs[None, :] < xint[:, None])
            mask ^= row_hit
            j = i
        return mask

    @classmethod
    def from_dict(cls, d: dict) -> "RoiMask":
        pts = [(float(p[0]), float(p[1])) for p in (d or {}).get("polygon", [])]
        return cls(polygon=pts)

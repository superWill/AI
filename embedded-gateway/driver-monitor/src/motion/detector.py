#!/usr/bin/env python3
"""滑动平均背景差 运动检测 —— 单摄换热站/消防站安防的 P0 视觉前端。

每帧:降采样 ~320×180 → 灰度 → 滑动平均背景 `bg = α·gray + (1-α)·bg` → `|gray-bg|>25`
前景掩码 → 前景占比 > 1% 判 `moving`。输出的 `moving/score` 喂 `episode.EpisodeStateMachine`。

设计(对照 ADR-0001):
- **机器只产事实**:本层只回答「画面在动吗」,**不判断人/入侵/火**。人体确认(NPU)是 P1。
- **冷启动只喂背景不判决**:开机头 `warmup_s` 秒背景未收敛,强制 `moving=False`(仍更新 bg),
  避免把「背景刚建立」误当运动。
- **纯 numpy**:板上无 cv2/PIL/ffmpeg;降采样用 stride 跳采样(比 bilinear 便宜,运动检测足够)。
- **确定性**:ts 由调用方给(接 gst_source.read() 的单调 ts),不读真实时钟 → 可重放、可测。

已知限制(ADR-0001 ④,须显式记录):**单摄有覆盖盲区——「无 motion ≠ 无人/无入侵者」。**
本检测器只覆盖单摄可见区域;盲区内的活动不会产生任何事件,不得据「无告警」推断「无人」。
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# 灰度 luma 权重(Rec.601),与 features/imgproc 侧口径一致。
_LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


@dataclass
class MotionConfig:
    """运动检测阈值,带版本号(仿 DrowsinessConfig,配置化/版本化)。"""
    version: str = "motion-detector-v1"
    down_w: int = 320                 # 降采样目标宽(stride 跳采样,近似)
    down_h: int = 180                 # 降采样目标高
    alpha: float = 0.02               # 背景滑动平均学习率(越小背景越"稳/慢")
    diff_thresh: float = 25.0         # 灰度差 > 此值判前景像素(0..255)
    fg_ratio_thresh: float = 0.01     # 前景占比 > 此值判 moving(1%)
    warmup_s: float = 3.0             # 冷启动:开机头几秒只喂背景不判决

    @classmethod
    def from_dict(cls, d: dict) -> "MotionConfig":
        known = {f for f in cls.__dataclass_fields__}          # type: ignore[attr-defined]
        return cls(**{k: v for k, v in (d or {}).items() if k in known})


@dataclass
class MotionSample:
    """一帧运动观测。喂 episode.EpisodeStateMachine.update(ts, moving, score)。"""
    ts: float
    moving: bool
    score: float          # 前景占比 0..1
    warming: bool         # True = 冷启动预热期,moving 已被强制 False


class MotionDetector:
    """滑动平均背景差。喂 (ts, HxWx3 uint8 RGB),吐 MotionSample。线性、无状态泄漏。"""

    def __init__(self, config: MotionConfig | None = None):
        self.cfg = config or MotionConfig()
        self._bg: np.ndarray | None = None     # float32 灰度背景累加器(降采样尺寸)
        self._first_ts: float | None = None     # 首帧 ts,判 warmup

    def process(self, ts: float, frame_rgb: np.ndarray) -> MotionSample:
        cfg = self.cfg
        gray = self._to_gray_small(frame_rgb)

        if self._bg is None:                    # 首帧:背景 = 当前帧,不判决
            self._bg = gray.copy()
            self._first_ts = ts
            return MotionSample(ts, moving=False, score=0.0, warming=True)

        # 前景占比(用**旧背景**比,再更新背景,避免把当前帧学进去后自己减自己)
        diff = np.abs(gray - self._bg)
        score = float(np.count_nonzero(diff > cfg.diff_thresh)) / diff.size

        # 滑动平均更新背景(每帧都更,含 warmup 期 → 让背景收敛)
        self._bg += cfg.alpha * (gray - self._bg)

        warming = (self._first_ts is not None
                   and ts - self._first_ts < cfg.warmup_s)
        moving = (not warming) and (score > cfg.fg_ratio_thresh)
        return MotionSample(ts, moving=moving, score=score, warming=warming)

    # ---- 内部 ----
    def _to_gray_small(self, frame_rgb: np.ndarray) -> np.ndarray:
        """降采样(stride 跳采样)→ 灰度 float32。返回 (down_h, down_w) 近似尺寸。"""
        h, w = frame_rgb.shape[:2]
        sy = max(1, h // self.cfg.down_h)
        sx = max(1, w // self.cfg.down_w)
        small = frame_rgb[::sy, ::sx]                       # (h', w', 3) uint8
        return small.astype(np.float32) @ _LUMA             # (h', w') float32

    def reset(self) -> None:
        """断流/重连后重建背景(仿 gst_source.restart 的语义)。"""
        self._bg = None
        self._first_ts = None

#!/usr/bin/env python3
"""关键帧节流 —— 纯逻辑,零依赖。事件期间决定「何时该截一帧」,不碰 gst/numpy/网络。

语义(「事件代表帧节流上传」):
- 事件首次出现 → 立即出 first_frame(seq 0,**不节流**,保证事件起点可见,呼应
  edge-video 文档「第一帧必须在首次命中时立即复制」)。
- 事件持续期间 → 每 `min_interval_s` 秒最多再出 1 帧(代表帧)。
- 每事件封顶 `max_frames_per_event`(含 first_frame),防长事件把 OSS/磁盘打爆。
- 本模块只出「截帧决策」;真正的帧编码 + OSS 上传由调用方做(见 uplink/oss_media.py)。

与 envelope 对接:first_frame 的 OSS URL → EventEnvelope.thumbnail_ref;
后续代表帧 URL → 收进 evidence_ref["frames"](由调用方组装)。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KeyframeConfig:
    min_interval_s: float = 5.0          # 代表帧最小间隔(节流)
    max_frames_per_event: int = 6        # 含 first_frame 的每事件上限


@dataclass(frozen=True)
class Capture:
    """一次截帧决策。name 直接用作 OSS object 名(first_frame / frame-001 …)。"""
    event_id: str
    seq: int                 # 0 = first_frame
    name: str
    is_first: bool


@dataclass
class _EvState:
    count: int = 0
    last_ts: float = -1e18


class KeyframeThrottle:
    """按事件维护截帧节奏。注入时钟(now)即可完全单测,无 I/O。"""

    def __init__(self, config: KeyframeConfig | None = None):
        self.cfg = config or KeyframeConfig()
        self._state: dict[str, _EvState] = {}

    def offer(self, event_id: str, now: float) -> Capture | None:
        """事件期间每有一帧可用就调一次。返回截帧决策,或 None(本帧跳过)。"""
        st = self._state.get(event_id)
        if st is None:
            # 首帧:立即 first_frame,不受 min_interval 约束
            self._state[event_id] = _EvState(count=1, last_ts=now)
            return Capture(event_id, 0, "first_frame", True)
        if st.count >= self.cfg.max_frames_per_event:
            return None                                   # 已达每事件上限
        if now - st.last_ts < self.cfg.min_interval_s:
            return None                                   # 节流:间隔未到
        seq = st.count
        st.count += 1
        st.last_ts = now
        return Capture(event_id, seq, f"frame-{seq:03d}", False)

    def close(self, event_id: str) -> None:
        """事件结束释放状态(event_id 稳定不复用;仅防长期运行内存泄漏)。"""
        self._state.pop(event_id, None)

    def active_events(self) -> int:
        return len(self._state)

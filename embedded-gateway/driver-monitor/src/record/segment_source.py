#!/usr/bin/env python3
"""录像段来源接口 + 离线 Fake —— 纯逻辑,把 splitmuxsink 隔在硬件外。真实现留 P2b。

板上录像用 GStreamer `splitmuxsink`/`mp4mux` 把连续流切成定长 .mp4 段(ADR-0001 ④验证门)。
本层只定义「一段录像」的事实与取段接口;真 splitmuxsink(gi/GStreamer)是 P2b。

- `SegmentRecord`:一段定长录像的元数据(id/起止时间/落盘路径/字节/是否含编码缺口)。
- `SegmentSource`:`poll(now)` 取已完成的新段;真/假后端同接口。
- `FakeSegmentSource`:合成时钟按 `now` 吐定长假段,可注入 `has_gap` 缺口,离线测/联调用。
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class SegmentRecord:
    """一段定长录像。has_gap=True 表示段内/段前有编码不连续(丢帧/解码缺口)。"""
    seg_id: int
    start_ts: float
    end_ts: float
    path: str
    bytes: int
    has_gap: bool = False

    def overlaps(self, lo: float, hi: float, eps: float = 1e-6) -> bool:
        """本段时间是否与 [lo, hi] 有交叠。"""
        return self.start_ts < hi - eps and self.end_ts > lo + eps


class SegmentSource(abc.ABC):
    """录像段来源。poll(now) 返回「截至 now 已完成、且尚未取走」的段(按时间序)。"""

    @abc.abstractmethod
    def poll(self, now: float) -> list[SegmentRecord]:
        ...


class FakeSegmentSource(SegmentSource):
    """合成时钟录像段源:每 seg_dur 秒产出一段;gap_at 里的 seg_id 标 has_gap。"""

    def __init__(self, seg_dur: float = 1.0, seg_bytes: int = 100, t0: float = 0.0,
                 gap_at: set[int] | None = None, path_prefix: str = "/rec/seg"):
        self.seg_dur = seg_dur
        self.seg_bytes = seg_bytes
        self._next_id = 0
        self._next_start = t0
        self._gap_at = set(gap_at or [])
        self._prefix = path_prefix

    def poll(self, now: float) -> list[SegmentRecord]:
        out: list[SegmentRecord] = []
        while self._next_start + self.seg_dur <= now + 1e-9:
            sid = self._next_id
            seg = SegmentRecord(
                seg_id=sid,
                start_ts=round(self._next_start, 3),
                end_ts=round(self._next_start + self.seg_dur, 3),
                path=f"{self._prefix}-{sid:06d}.mp4",
                bytes=self.seg_bytes,
                has_gap=(sid in self._gap_at),
            )
            out.append(seg)
            self._next_id += 1
            self._next_start = round(self._next_start + self.seg_dur, 3)
        return out

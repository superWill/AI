#!/usr/bin/env python3
"""工单/巡检窗缓存 —— 纯逻辑。带版本 + 有效期。ADR-0001 ⑥。

platform 是工单/巡检窗**权威源**,RK3506 缓存(离线自治)。缓存带 `version + as_of_ts`;
断网且缓存过期 → 分类器据此降级(见 classify.py)。**高安防场景 TTL 要短**。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkOrderWindow:
    """一个预期出现窗。**不证明身份**,只表示「此时段有工单/巡检」。"""
    window_id: str
    start_ts: float
    end_ts: float

    def covers(self, ts: float) -> bool:
        return self.start_ts <= ts <= self.end_ts


class WorkOrderCache:
    """缓存快照持有者。update() 整体替换为新版本快照。"""

    def __init__(self, ttl_s: float = 3600.0):
        self.ttl_s = ttl_s
        self._version: str | None = None
        self._as_of_ts: float | None = None
        self._windows: list[WorkOrderWindow] = []

    def update(self, version: str, as_of_ts: float,
               windows: list[WorkOrderWindow]) -> None:
        self._version = version
        self._as_of_ts = as_of_ts
        self._windows = list(windows)

    def status(self, now: float) -> str:
        """empty(从未下发)| expired(超 TTL)| fresh。"""
        if self._version is None or self._as_of_ts is None:
            return "empty"
        if now - self._as_of_ts > self.ttl_s:
            return "expired"
        return "fresh"

    def covering(self, ts: float) -> WorkOrderWindow | None:
        for w in self._windows:
            if w.covers(ts):
                return w
        return None

    @property
    def version(self) -> str | None:
        return self._version

    @property
    def as_of_ts(self) -> float | None:
        return self._as_of_ts

#!/usr/bin/env python3
"""通知升级状态机 —— 纯逻辑,ts 注入、确定性。ADR-0001 ②。

可通知事件(person_observation / suspected_intrusion / 健康告警)推值班岗 + **要求 ack**;
超时未 ack → 升**通知等级**(更多人 / 更响)。

不变量(硬约束,写进测试):
  - **升级只升通知等级(谁被 ping、多响),永不升事件分类、永不升火警等级。**
  - 真火响应由认证链自主联动,**不在人工 ack 关键路径上**(此状态机只管通知,不碰火警链)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class EscalateConfig:
    # 各级停留超时(秒):L1 无 ack 超 timeouts[0] → L2,再超 timeouts[1] → L3 …
    timeouts: tuple = (60.0, 180.0)
    max_level: int = 3


@dataclass
class _Track:
    event_id: str
    level: int
    since: float
    acked: bool = False


class NotificationEscalator:
    def __init__(self, config: EscalateConfig | None = None):
        self.cfg = config or EscalateConfig()
        self._tracks: dict[str, _Track] = {}

    def notify(self, event_id: str, now: float) -> dict:
        """登记一个待 ack 的通知,起始 L1。返回通知动作事件。"""
        self._tracks[event_id] = _Track(event_id, level=1, since=now)
        return self._event(event_id, 1, "notify", now)

    def ack(self, event_id: str, now: float) -> dict | None:
        t = self._tracks.get(event_id)
        if t is None or t.acked:
            return None
        t.acked = True
        return self._event(event_id, t.level, "resolved", now)

    def tick(self, now: float) -> list[dict]:
        """超时未 ack → 升一级(直到 max_level)。返回本次升级动作。"""
        out = []
        for t in self._tracks.values():
            if t.acked or t.level >= self.cfg.max_level:
                continue
            idx = t.level - 1
            if idx < len(self.cfg.timeouts) and now - t.since >= self.cfg.timeouts[idx]:
                t.level += 1
                t.since = now
                out.append(self._event(t.event_id, t.level, "escalate", now))
        return out

    def _event(self, event_id: str, level: int, action: str, now: float) -> dict:
        # 只带通知等级 + 动作;**没有事件分类字段** → 结构上无法升级分类/火警
        return {
            "type": "notification",
            "event_id": event_id,
            "notify_level": level,
            "action": action,               # notify | escalate | resolved
            "ts": round(now, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def level_of(self, event_id: str) -> int | None:
        t = self._tracks.get(event_id)
        return t.level if t else None

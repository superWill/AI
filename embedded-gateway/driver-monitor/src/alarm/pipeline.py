#!/usr/bin/env python3
"""报警抓拍编排 —— 纯逻辑,把三件事串起来:收报警 → 抓快照 → 入板子侧 spool(ship 到代理→OSS)。

RK3506 产品侧主链。注入 alarm_source / snapshot / spool(MediaOutbox),可完全离线单测。
- event_id 确定性:`alarm-{source_id}-{int(occurred_at)}` —— 同源同秒幂等,不用随机。
- 快照抓失败(相机离线)→ 不入队,发 alarm_snapshot_failed 健康告警(不静默)。
- 用 kind="first_frame" 入队 → 拿 MediaOutbox 最高优先 + 永不淘汰(报警证据不能丢)。
"""
from __future__ import annotations

from uplink.oss_media import event_media_key


class AlarmSnapshotPipeline:
    def __init__(self, alarm_source, snapshot, spool, *,
                 prefix: str = "driver-monitor", on_captured=None):
        """alarm_source: poll(now)->[AlarmEvent];snapshot: grab()->bytes|None;
        spool: MediaOutbox(enqueue/pump);on_captured(event_id,key,size):抓拍成功回调。"""
        self.alarm_source = alarm_source
        self.snapshot = snapshot
        self.spool = spool
        self.prefix = prefix
        self._on_captured = on_captured

    def tick(self, now: float) -> list[dict]:
        """驱动一拍:处理新报警。返回健康信号(抓图失败/spool 容量等)。上层另调 spool.pump(now)。"""
        health: list[dict] = []
        for ev in self.alarm_source.poll(now):
            event_id = f"alarm-{ev.source_id}-{int(ev.occurred_at)}"
            key = event_media_key(self.prefix, event_id, "snapshot", ext="jpg")
            jpeg = self.snapshot.grab()
            if jpeg is None:
                health.append(self._health("alarm_snapshot_failed",
                                           f"{event_id} 抓图失败(相机离线?)", now))
                continue
            health += self.spool.enqueue(
                key, jpeg, "first_frame", occurred_at=ev.occurred_at, now=now,
                content_type="image/jpeg", ref=event_id)
            if self._on_captured is not None:
                self._on_captured(event_id, key, len(jpeg))
        return health

    def _health(self, status: str, detail: str, ts: float) -> dict:
        return {"type": "alarm_health", "status": status, "detail": detail, "ts": round(ts, 3)}

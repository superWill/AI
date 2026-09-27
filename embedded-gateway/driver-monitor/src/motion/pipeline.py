#!/usr/bin/env python3
"""单摄运动管线 —— 把 detector + episode 粘成「一路摄像头」的处理单元 + 相机健康态。

一路摄像头 = 一个 MotionPipeline(**独立的背景模型 + 独立的 episode 状态机**)。
多摄就是多个 MotionPipeline 并行(见 scripts/run_motion_live.py 的按摄像头起线程)。
每个摄像头场景不同,背景模型**绝不能共享**——共享会把 A 摄的背景当 B 摄的,满屏误报。

职责:
  - 每帧:detector → episode,并把 `cam_id` 打进每条事件(多摄下辨明哪路)。
  - **相机健康**:停流超过 stale_after_s → 发 `camera_health(status=stale)`,**强制收尾**当前
    episode(force_close,避免 ACTIVE 永远挂着;ADR-0001:诚实降级、禁止无声丢失),并即刻
    reset detector(下次出帧从新背景起,不拿旧背景误报)。恢复出帧 → 发 `camera_health(status=online)`。
  - **纯粘合、鸭子类型**:只调 detector.process/reset、episode.update/force_close,不 import
    numpy/gst → 相机健康与 cam_id 逻辑可脱硬件单测(注入 fake detector)。
"""
from __future__ import annotations


class MotionPipeline:
    """一路摄像头的处理单元。detector/episode 由外部注入(各摄独立实例)。"""

    def __init__(self, cam_id: str, detector, episode, *, stale_after_s: float = 2.0):
        self.cam_id = cam_id
        self.detector = detector
        self.episode = episode
        self.stale_after_s = stale_after_s
        self._last_frame_ts: float | None = None
        self._started_ts: float | None = None
        self._online: bool = True

    def mark_started(self, ts: float) -> None:
        """记录起跑时刻:用于「开机后一直没出帧」也能判 stale(否则死摄不告警)。"""
        self._started_ts = ts

    def process_frame(self, ts: float, frame) -> list[dict]:
        """喂一帧 → 运动检测 + episode 更新。返回本帧事件(含 cam_id)。"""
        events: list[dict] = []
        if not self._online:                     # 停流后又出帧 → 恢复
            events.append(self._health(ts, "online"))
            self._online = True
        self._last_frame_ts = ts

        sample = self.detector.process(ts, frame)
        for ev in self.episode.update(sample.ts, sample.moving, sample.score):
            ev["cam_id"] = self.cam_id
            events.append(ev)
        return events

    def tick_no_frame(self, now: float) -> list[dict]:
        """无新帧时由上层定时调用:停流超阈 → camera_health(stale) + 强制收尾 episode。"""
        if not self._online:
            return []                            # 已 stale,不刷屏
        ref = self._last_frame_ts if self._last_frame_ts is not None else self._started_ts
        if ref is None or now - ref < self.stale_after_s:
            return []
        self._online = False
        events = [self._health(now, "stale")]
        forced = self.episode.force_close(now, "camera_fault")
        if forced is not None:
            forced["cam_id"] = self.cam_id
            events.append(forced)
        self.detector.reset()                    # 恢复后从新背景起,不拿旧背景误报
        return events

    def _health(self, ts: float, status: str) -> dict:
        return {"type": "camera_health", "cam_id": self.cam_id,
                "status": status, "ts": round(ts, 3)}

    @property
    def online(self) -> bool:
        return self._online

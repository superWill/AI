#!/usr/bin/env python3
"""运动门控 + 人体确认 升级状态机 —— 纯逻辑,零第三方依赖,可单测/重放。

把 P0 的 motion episode(「画面在动」)升级为 person_observation(「确认有人出现」):
  - **运动门控**:只有 motion episode ACTIVE 时才喂人体检测(NPU 只在有动静时跑,省电)。
  - **时间持久性**:最近 K 帧里 person-in-ROI ≥ M 帧才确认,滤掉单帧误检/闪烁。
  - **升级**:motion OPEN 只是「暂定」;确认到人才发 `person_observation` OPEN(触发告警);
    motion 闭合但从未确认到人(如蒸汽)→ **不产任何事件**。

不变量(ADR-0001 ⑥,写进测试):
  - 视觉只到 `person_observation`(事实),**永不**产 intrusion/confirmed_intrusion。
  - **不确定只升通知优先级,不改事件分类**:没达 M 阈值就是「没确认到人」,绝不发「疑似有人」
    这种冒充分类的中间态。
  - OPEN 进场即发(确认即触发),CLOSE 发**同 event_id** 的幂等更新。
  - 时间显式传入 → 确定性、可重放。
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone


class ConfirmState:
    IDLE = "idle"                      # 无运动门控 / 门控关闭
    MOTION_TENTATIVE = "motion_tentative"   # motion 活跃,尚未确认到人(暂定)
    PERSON_CONFIRMED = "person_confirmed"   # 已确认到人,person_observation OPEN 中


@dataclass
class ConfirmConfig:
    version: str = "person-confirm-v1"
    k_window: int = 5                  # 持久性滑窗帧数
    m_confirm: int = 3                 # 窗内 ≥ 此数帧见人 → 确认
    person_exit_frames: int = 15       # 确认后连续缺席此帧数 → CLOSE(person_left)

    @classmethod
    def from_dict(cls, d: dict) -> "ConfirmConfig":
        known = {f for f in cls.__dataclass_fields__}          # type: ignore[attr-defined]
        return cls(**{k: v for k, v in (d or {}).items() if k in known})


class PersonConfirmer:
    """喂 (ts, motion_active, person_boxes),吐 person_observation 的 OPEN/CLOSE 事件。

    person_boxes 应为**已过 ROI 过滤**的框(上层用 RoiMask.filter_boxes)。
    update() 返回本帧发出的事件列表(通常空)。
    """

    def __init__(self, config: ConfirmConfig | None = None):
        self.cfg = config or ConfirmConfig()
        self._state = ConfirmState.IDLE
        self._window: deque[bool] = deque(maxlen=self.cfg.k_window)
        self._first_person_ts: float | None = None   # 本次暂定期首次见人(诚实起点)
        self._last_person_ts: float | None = None     # 最近见人时刻(→ ts_end)
        self._peak_conf: float = 0.0
        self._person_frames: int = 0                  # 本次观测累计见人帧数
        self._absent: int = 0                         # 确认后连续缺席帧数
        self._seq: int = 0
        self._event_id: str | None = None

    def update(self, ts: float, motion_active: bool, person_boxes,
               motion_event_id: str | None = None) -> list[dict]:
        present = bool(person_boxes)
        best = max((b.score for b in person_boxes), default=0.0)

        if self._state == ConfirmState.IDLE:
            if not motion_active:
                return []
            self._enter_tentative()
            return self._tentative(ts, motion_active, present, best, motion_event_id)

        if self._state == ConfirmState.MOTION_TENTATIVE:
            return self._tentative(ts, motion_active, present, best, motion_event_id)

        return self._confirmed(ts, motion_active, present, best, motion_event_id)

    # ---- 暂定期:累计持久性,够 M 就确认 ----
    def _tentative(self, ts, motion_active, present, best, motion_ref) -> list[dict]:
        if not motion_active:                     # motion 闭合但没确认到人 → 丢弃,不上报
            self._reset()
            return []
        self._window.append(present)
        if present:
            if self._first_person_ts is None:
                self._first_person_ts = ts
            self._last_person_ts = ts
            self._person_frames += 1
        if best > self._peak_conf:
            self._peak_conf = best
        if sum(self._window) >= self.cfg.m_confirm:
            return [self._open(motion_ref)]
        return []

    # ---- 确认期:跟踪缺席,人走或 motion 闭合则 CLOSE ----
    def _confirmed(self, ts, motion_active, present, best, motion_ref) -> list[dict]:
        if not motion_active:                     # 门控信封消失 → 收尾
            return [self._close("motion_closed", motion_ref)]
        if present:
            self._absent = 0
            self._last_person_ts = ts
            self._person_frames += 1
            if best > self._peak_conf:
                self._peak_conf = best
            return []
        # 缺席累计
        self._absent += 1
        if self._absent >= self.cfg.person_exit_frames:
            ev = self._close("person_left", motion_ref)
            # motion 还活着 → 回暂定,允许同一 motion 内二次进人开新观测
            if motion_active:
                self._enter_tentative()       # 置 MOTION_TENTATIVE + 清窗口
            return [ev]
        return []

    def force_close(self, ts: float, reason: str = "shutdown",
                    motion_event_id: str | None = None) -> dict | None:
        """相机故障/关机强制收尾:仅 PERSON_CONFIRMED 有 CLOSE,其余 None(暂定期无已确认观测)。"""
        if self._state != ConfirmState.PERSON_CONFIRMED:
            return None
        return self._close(reason, motion_event_id)

    # ---- 事件构造 ----
    def _open(self, motion_ref) -> dict:
        self._seq += 1
        self._event_id = f"po-{self._seq:06d}"
        self._state = ConfirmState.PERSON_CONFIRMED
        self._absent = 0
        start = self._first_person_ts if self._first_person_ts is not None else 0.0
        ev = {
            "type": "person_observation",
            "event_kind": "open",
            "event_id": self._event_id,
            "ts_start": round(start, 3),
            "confidence": round(self._peak_conf, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if motion_ref is not None:
            ev["motion_ref"] = motion_ref
        return ev

    def _close(self, closed_by: str, motion_ref) -> dict:
        start = self._first_person_ts if self._first_person_ts is not None else 0.0
        end = self._last_person_ts if self._last_person_ts is not None else start
        ev = {
            "type": "person_observation",
            "event_kind": "close",
            "event_id": self._event_id,
            "ts_start": round(start, 3),
            "ts_end": round(end, 3),
            "duration_s": round(end - start, 3),
            "peak_confidence": round(self._peak_conf, 3),
            "person_frames": self._person_frames,
            "closed_by": closed_by,           # person_left | motion_closed | shutdown
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if motion_ref is not None:
            ev["motion_ref"] = motion_ref
        self._reset()
        return ev

    # ---- 状态维护 ----
    def _enter_tentative(self) -> None:
        self._state = ConfirmState.MOTION_TENTATIVE
        self._window.clear()
        self._first_person_ts = None
        self._last_person_ts = None
        self._peak_conf = 0.0
        self._person_frames = 0
        self._absent = 0

    def _reset(self) -> None:
        self._state = ConfirmState.IDLE
        self._window.clear()
        self._first_person_ts = None
        self._last_person_ts = None
        self._peak_conf = 0.0
        self._person_frames = 0
        self._absent = 0
        self._event_id = None

    # ---- 只读 ----
    @property
    def state(self) -> str:
        return self._state

    @property
    def confirmed(self) -> bool:
        return self._state == ConfirmState.PERSON_CONFIRMED

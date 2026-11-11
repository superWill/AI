#!/usr/bin/env python3
"""Motion episode 迟滞状态机 —— 纯逻辑,零第三方依赖,Mac/板子都能跑、可单测。

输入:每帧的运动观测 (ts, moving: bool, score: float),由 `detector.MotionDetector` 产出。
输出:一次「运动 episode」的 OPEN / CLOSE 事件(dict),供上层落地(存证/日志/上行)。

设计原则(对照 ADR-0001):
- **机器只产事实**:本层只产 `motion_episode`(检测到运动这一事实),
  **不产** `person_present` 长状态、**不产** `intrusion`。人体确认(NPU)是 P1,
  届时把 `type` 升为 `person_observation`,event_id 幂等更新的骨架此处已就位。
- **迟滞去抖**:连续 N_enter 帧 moving 才进 ACTIVE(滤单帧抖动);连续 N_exit 帧
  quiet 才离场(滤运动间隙),避免一次连续活动被切成多段。
- **进场即告警**(ADR-0001 ⑥):START 立即发 OPEN,不等离场;END 发**同 event_id**
  的 CLOSE 更新(补时长/峰值)。靠 open 触发,不靠 close,否则进场不告警、离场才告警。
- **时间显式传入**:ts 由调用方给(单调时钟或 epoch,只要单调递增)→ 状态机确定、
  可重放、可单测,不读真实时钟。
- **诚实的时间边界**:ts_start = 运动**真正开始**时刻(qualifying run 的首帧),
  ts_end = 运动**真正停止**时刻(最后一帧 moving),不含末尾 N_exit 帧的静默尾巴。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


class EpisodeState:
    IDLE = "idle"
    ACTIVE = "active"


@dataclass
class EpisodeConfig:
    """迟滞阈值,带版本号(仿 DrowsinessConfig,便于配置化/版本化)。"""
    version: str = "motion-episode-v1"
    n_enter: int = 4        # 连续 moving 帧数达此值 → 进 ACTIVE 并发 OPEN
    n_exit: int = 30        # 连续 quiet 帧数达此值 → 离 ACTIVE 并发 CLOSE

    @classmethod
    def from_dict(cls, d: dict) -> "EpisodeConfig":
        known = {f for f in cls.__dataclass_fields__}          # type: ignore[attr-defined]
        return cls(**{k: v for k, v in (d or {}).items() if k in known})


class EpisodeStateMachine:
    """喂 (ts, moving, score),吐 motion_episode 的 OPEN/CLOSE 事件。

    update() 返回**本帧发出的事件列表**(通常空;偶发一条 open 或 close)。
    一次进场→离场是一个 episode,open/close 共享稳定 event_id(P1 幂等更新的雏形)。
    """

    def __init__(self, config: EpisodeConfig | None = None):
        self.cfg = config or EpisodeConfig()
        self._state: str = EpisodeState.IDLE
        self._enter_run: int = 0                 # IDLE 期:当前连续 moving 计数
        self._exit_run: int = 0                  # ACTIVE 期:当前连续 quiet 计数
        self._onset_ts: float | None = None      # 当前 moving run 的起点(运动真正开始)
        self._last_moving_ts: float | None = None  # ACTIVE 期:最后一次 moving 的 ts(运动真正停止)
        self._peak_motion: float = 0.0           # ACTIVE 期:motion score 峰值
        self._moving_frames: int = 0             # ACTIVE 期:moving 帧计数(诊断用)
        self._seq: int = 0                       # episode 序号 → 确定性 event_id
        self._event_id: str | None = None        # 当前 open 着的 episode 的 id

    # ---- 对外:喂一帧 ----
    def update(self, ts: float, moving: bool, score: float = 0.0) -> list[dict]:
        if self._state == EpisodeState.IDLE:
            return self._update_idle(ts, moving, score)
        return self._update_active(ts, moving, score)

    def _update_idle(self, ts: float, moving: bool, score: float) -> list[dict]:
        if moving:
            if self._enter_run == 0:
                self._onset_ts = ts              # 运动 run 起点
            self._enter_run += 1
            # 进场窗口内的帧也算 episode 的一部分(ts_start=onset、moving_frames 含它们),
            # 峰值须一并计入,否则最强的一帧(常在进场瞬间)会被丢掉。
            if score > self._peak_motion:
                self._peak_motion = score
            if self._enter_run >= self.cfg.n_enter:
                return [self._open(ts, score)]
        else:
            self._enter_run = 0                  # 中断即清零(要求连续)
            self._onset_ts = None
            self._peak_motion = 0.0              # run 断了,峰值随之清零
        return []

    def _update_active(self, ts: float, moving: bool, score: float) -> list[dict]:
        if moving:
            self._exit_run = 0                   # 运动继续,重置离场计数
            self._last_moving_ts = ts
            self._moving_frames += 1
            if score > self._peak_motion:
                self._peak_motion = score
        else:
            self._exit_run += 1
            if self._exit_run >= self.cfg.n_exit:
                return [self._close()]
        return []

    # ---- 事件构造 ----
    def _open(self, ts: float, score: float) -> dict:
        self._seq += 1
        self._event_id = f"ep-{self._seq:06d}"
        self._state = EpisodeState.ACTIVE
        self._exit_run = 0
        self._last_moving_ts = ts
        if score > self._peak_motion:            # 含进场窗口累计的峰值
            self._peak_motion = score
        self._moving_frames = self._enter_run    # 进场前已累计的 moving 帧
        start = self._onset_ts if self._onset_ts is not None else ts
        return {
            "type": "motion_episode",
            "event_kind": "open",
            "event_id": self._event_id,
            "ts_start": round(start, 3),
            "motion_score": round(score, 4),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def force_close(self, ts: float, reason: str = "camera_fault") -> dict | None:
        """强制收尾当前 episode(相机停流/故障时用):ACTIVE → 发 CLOSE,否则 None。

        没有帧就没有 quiet 帧,ACTIVE 会永远挂着;相机故障时必须诚实收尾——
        既不静默丢弃、也不留悬空 OPEN(ADR-0001:诚实降级、禁止无声丢失)。
        ts_end 仍取**最后一帧可见运动**(故障后画面盲,真实结束时刻不可知),
        `closed_by=camera_fault` 标注此 CLOSE 是被故障截断的,时长可能偏短。
        """
        if self._state != EpisodeState.ACTIVE:
            return None
        return self._close(closed_by=reason)

    def _close(self, closed_by: str = "quiet_timeout") -> dict:
        start = self._onset_ts if self._onset_ts is not None else 0.0
        end = self._last_moving_ts if self._last_moving_ts is not None else start
        ev = {
            "type": "motion_episode",
            "event_kind": "close",
            "event_id": self._event_id,       # 同 open 的 id → 幂等更新
            "ts_start": round(start, 3),
            "ts_end": round(end, 3),
            "duration_s": round(end - start, 3),
            "peak_motion": round(self._peak_motion, 4),
            "moving_frames": self._moving_frames,
            "closed_by": closed_by,           # quiet_timeout | camera_fault | shutdown
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # 回 IDLE,清 run 态
        self._state = EpisodeState.IDLE
        self._enter_run = 0
        self._exit_run = 0
        self._onset_ts = None
        self._last_moving_ts = None
        self._peak_motion = 0.0
        self._moving_frames = 0
        self._event_id = None
        return ev

    # ---- 只读 ----
    @property
    def state(self) -> str:
        return self._state

    @property
    def active(self) -> bool:
        return self._state == EpisodeState.ACTIVE

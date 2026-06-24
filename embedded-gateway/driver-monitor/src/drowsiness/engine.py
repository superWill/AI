#!/usr/bin/env python3
"""疲劳驾驶状态机引擎 —— 纯逻辑,零第三方依赖,Mac/板子都能跑、可单测。

输入:每帧的脸部观测(EAR/MAR/头姿/是否有脸/推理是否成功)+ 外部健康(摄像头在线/模型正常)。
输出:状态机结果(状态 + 原因 + 置信度 + 事件 JSON),供 event-adapter 落地(蜂鸣/HMI/日志/MQTT)。

设计原则(对照 handoff §4):
- **不以单帧阈值直接报警**:特征先进时间窗(PERCLOS/连续闭眼/打哈欠计数/偏头时长)再进状态机。
- **故障态独立**:摄像头离线、丢脸、模型异常、时间戳倒退 → 独立故障状态,**绝不解释成"驾驶员正常"**。
- **阈值配置化 + 版本化**:全部来自 DrowsinessConfig,不散落为代码常量。
- 时间显式传入(now/ts),不读真实时钟 → 状态机确定、可重放、可单测。
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


# ===========================================================================
# 状态与配置
# ===========================================================================
class State:
    NORMAL = "normal"
    SUSPECTED = "suspected"
    WARNING = "warning"
    ALARM = "alarm"
    NO_FACE = "no_face"            # 持续丢脸(驾驶员离位/严重遮挡)——不是 normal
    CAMERA_FAULT = "camera_fault"  # 摄像头离线/帧停滞
    MODEL_FAULT = "model_fault"    # 推理失败/时间戳倒退


# 故障态优先级高于一切疲劳判定;数值越大越优先
_FAULT_RANK = {State.MODEL_FAULT: 3, State.CAMERA_FAULT: 3,
               State.NO_FACE: 2}


@dataclass
class DrowsinessConfig:
    """全部阈值与时间窗,带版本号。从 config/thresholds.json 加载。"""
    version: str = "thresholds-v1"
    model_version: str = "unset"

    # 眼睛:EAR 越低越闭
    ear_closed_thresh: float = 0.18
    eye_closed_alarm_s: float = 2.0        # 连续闭眼(微睡)→ alarm

    # PERCLOS:窗口内闭眼时间占比
    perclos_window_s: float = 60.0
    perclos_min_span_s: float = 15.0       # 样本覆盖不足此跨度时,PERCLOS 不参与状态升级(预热,防开机/短闭眼误报)
    perclos_warn: float = 0.15
    perclos_alarm: float = 0.30

    # 嘴:MAR 越高越张(打哈欠)
    mar_yawn_thresh: float = 0.6
    yawn_min_s: float = 0.4                # 张嘴持续超过此值才算一次哈欠
    yawn_window_s: float = 120.0
    yawn_count_warn: int = 3

    # 头姿:低头/扭头看别处
    head_down_pitch: float = 20.0          # pitch 低头超过此度数
    head_away_yaw: float = 35.0            # yaw 扭头超过此度数
    head_off_alarm_s: float = 3.0          # 持续偏离驾驶视线超过此值

    # 故障判定
    face_lost_grace_s: float = 2.0         # 丢脸超过此值 → NO_FACE
    stale_frame_s: float = 2.0             # 无新帧超过此值 → CAMERA_FAULT

    @classmethod
    def from_dict(cls, d: dict) -> "DrowsinessConfig":
        known = {f for f in cls.__dataclass_fields__}          # type: ignore[attr-defined]
        return cls(**{k: v for k, v in (d or {}).items() if k in known})


@dataclass
class FrameObservation:
    """一帧处理后的观测。值为 None 表示该项不可用(如丢脸时 EAR 无意义)。"""
    ts: float                              # 帧时间戳(秒,单调或 epoch 均可,只要单调递增)
    face_present: bool
    infer_ok: bool = True                  # 推理是否产出有效关键点(模型健康)
    ear: float | None = None
    mar: float | None = None
    yaw: float | None = None               # 头部偏航(左右扭头),度
    pitch: float | None = None             # 头部俯仰(低头),度
    confidence: float | None = None        # 关键点/检测置信度 0..1


@dataclass
class StateResult:
    state: str
    reason: list[str] = field(default_factory=list)
    confidence: float = 0.0
    camera_status: str = "online"
    perclos: float | None = None
    eye_closed_s: float = 0.0
    model_version: str = "unset"
    ts: float = 0.0

    def to_event(self) -> dict:
        """handoff §4 的事件 JSON。"""
        return {
            "type": "driver_monitor_event",
            "state": self.state,
            "reason": self.reason,
            "confidence": round(self.confidence, 3),
            "camera_status": self.camera_status,
            "model_version": self.model_version,
            "perclos": (None if self.perclos is None else round(self.perclos, 3)),
            "eye_closed_s": round(self.eye_closed_s, 2),
            "timestamp": datetime.fromtimestamp(self.ts, tz=timezone.utc).isoformat(),
        }


# ===========================================================================
# 引擎
# ===========================================================================
class DrowsinessEngine:
    """喂帧观测,吐状态。维护时间窗与连续计时,确定性、可重放。"""

    def __init__(self, config: DrowsinessConfig | None = None):
        self.cfg = config or DrowsinessConfig()
        self._eye_samples: deque[tuple[float, bool]] = deque()   # (ts, eyes_closed) 供 PERCLOS
        self._eye_closed_since: float | None = None              # 当前连续闭眼起点
        self._face_lost_since: float | None = None               # 当前连续丢脸起点
        self._head_off_since: float | None = None                # 当前连续偏头起点
        self._yawn_events: deque[float] = deque()                # 哈欠完成时刻
        self._mouth_open_since: float | None = None              # 当前张嘴起点
        self._last_ts: float | None = None
        self._state: str = State.NORMAL

    # ---- 对外:喂一帧 ----
    def update(self, obs: FrameObservation, *, camera_online: bool = True,
               model_ok: bool = True, now: float | None = None) -> StateResult:
        cfg = self.cfg
        now = obs.ts if now is None else now

        # 1) 时间戳倒退 → 模型/链路异常,不能当正常
        if self._last_ts is not None and obs.ts < self._last_ts - 1e-6:
            return self._fault(State.MODEL_FAULT, ["timestamp_regression"], now)
        self._last_ts = obs.ts

        # 2) 外部健康:摄像头 / 模型
        if not camera_online:
            return self._fault(State.CAMERA_FAULT, ["camera_offline"], now)
        if not model_ok or not obs.infer_ok:
            return self._fault(State.MODEL_FAULT, ["inference_failed"], now)

        # 3) 丢脸宽限:短暂丢脸不报,持续超过 grace → NO_FACE
        if not obs.face_present:
            if self._face_lost_since is None:
                self._face_lost_since = obs.ts
            if obs.ts - self._face_lost_since >= cfg.face_lost_grace_s:
                self._eye_closed_since = None        # 丢脸期间不累计闭眼
                self._head_off_since = None
                return self._fault(State.NO_FACE, ["face_lost"], now)
            # 宽限期内:保持上一个非故障态,不推进疲劳判定
            return StateResult(self._state, ["face_lost_grace"], 0.3,
                               "online", self._perclos(obs.ts), self._eye_closed_dur(obs.ts),
                               cfg.model_version, obs.ts)
        self._face_lost_since = None

        # 4) 有脸:更新时间窗特征
        eyes_closed = obs.ear is not None and obs.ear < cfg.ear_closed_thresh
        self._push_eye(obs.ts, eyes_closed)
        self._track_eye_closure(obs.ts, eyes_closed)
        self._track_yawn(obs.ts, obs.mar)
        self._track_head(obs.ts, obs.yaw, obs.pitch)

        # 5) 判定(故障态在上面已早返回;这里只判疲劳分级)
        return self._classify(obs, now)

    # ---- 疲劳分级 ----
    def _classify(self, obs: FrameObservation, now: float) -> StateResult:
        cfg = self.cfg
        reasons: list[str] = []
        perclos = self._perclos(obs.ts)
        # PERCLOS 预热:样本覆盖跨度不足时不参与升级(只报数值),短闭眼交给微睡逻辑
        perclos_ready = self._perclos_span() >= min(cfg.perclos_min_span_s,
                                                    cfg.perclos_window_s * 0.9)
        eye_dur = self._eye_closed_dur(obs.ts)
        head_off = (0.0 if self._head_off_since is None else obs.ts - self._head_off_since)
        yawns = self._yawn_count(obs.ts)

        # ALARM:微睡(连续闭眼) / PERCLOS 高 / 长时间偏离视线
        alarm = False
        if eye_dur >= cfg.eye_closed_alarm_s:
            alarm = True; reasons.append("microsleep_eyes_closed")
        if perclos_ready and perclos >= cfg.perclos_alarm:
            alarm = True; reasons.append("high_perclos")
        if head_off >= cfg.head_off_alarm_s:
            alarm = True; reasons.append("head_off_road")
        if alarm:
            return self._set(State.ALARM, reasons, 0.9, perclos, eye_dur, obs.ts)

        # WARNING:PERCLOS 偏高 / 哈欠频繁 / 持续偏头
        warn = False
        if perclos_ready and perclos >= cfg.perclos_warn:
            warn = True; reasons.append("elevated_perclos")
        if yawns >= cfg.yawn_count_warn:
            warn = True; reasons.append("frequent_yawning")
        if head_off >= cfg.head_off_alarm_s * 0.5:
            warn = True; reasons.append("head_drift")
        if warn:
            return self._set(State.WARNING, reasons, 0.75, perclos, eye_dur, obs.ts)

        # SUSPECTED:瞬时闭眼 / 单次哈欠在进行
        susp = False
        if eye_dur > 0.3:
            susp = True; reasons.append("eyes_closing")
        if self._mouth_open_since is not None and obs.ts - self._mouth_open_since >= cfg.yawn_min_s:
            susp = True; reasons.append("yawning")
        if susp:
            return self._set(State.SUSPECTED, reasons, 0.5, perclos, eye_dur, obs.ts)

        return self._set(State.NORMAL, [], 0.95, perclos, eye_dur, obs.ts)

    # ---- 时间窗维护 ----
    def _push_eye(self, ts: float, closed: bool) -> None:
        self._eye_samples.append((ts, closed))
        cutoff = ts - self.cfg.perclos_window_s
        while self._eye_samples and self._eye_samples[0][0] < cutoff:
            self._eye_samples.popleft()

    def _perclos(self, ts: float) -> float:
        """窗口内闭眼时间占比(按相邻样本时间间隔加权)。"""
        s = self._eye_samples
        if len(s) < 2:
            return 0.0
        closed_t = total_t = 0.0
        for i in range(1, len(s)):
            dt = s[i][0] - s[i - 1][0]
            if dt <= 0:
                continue
            total_t += dt
            if s[i - 1][1]:                  # 区间起点闭眼则计入
                closed_t += dt
        return (closed_t / total_t) if total_t > 0 else 0.0

    def _perclos_span(self) -> float:
        """当前 PERCLOS 样本在窗口内覆盖的时间跨度。"""
        s = self._eye_samples
        return (s[-1][0] - s[0][0]) if len(s) >= 2 else 0.0

    def _track_eye_closure(self, ts: float, closed: bool) -> None:
        if closed:
            if self._eye_closed_since is None:
                self._eye_closed_since = ts
        else:
            self._eye_closed_since = None

    def _eye_closed_dur(self, ts: float) -> float:
        return 0.0 if self._eye_closed_since is None else ts - self._eye_closed_since

    def _track_yawn(self, ts: float, mar: float | None) -> None:
        cfg = self.cfg
        open_now = mar is not None and mar >= cfg.mar_yawn_thresh
        if open_now:
            if self._mouth_open_since is None:
                self._mouth_open_since = ts
        else:
            # 张嘴结束:若持续够久,记一次哈欠
            if self._mouth_open_since is not None and ts - self._mouth_open_since >= cfg.yawn_min_s:
                self._yawn_events.append(ts)
            self._mouth_open_since = None
        cutoff = ts - cfg.yawn_window_s
        while self._yawn_events and self._yawn_events[0] < cutoff:
            self._yawn_events.popleft()

    def _yawn_count(self, ts: float) -> int:
        cutoff = ts - self.cfg.yawn_window_s
        return sum(1 for t in self._yawn_events if t >= cutoff)

    def _track_head(self, ts: float, yaw: float | None, pitch: float | None) -> None:
        cfg = self.cfg
        off = ((yaw is not None and abs(yaw) >= cfg.head_away_yaw) or
               (pitch is not None and pitch >= cfg.head_down_pitch))
        if off:
            if self._head_off_since is None:
                self._head_off_since = ts
        else:
            self._head_off_since = None

    # ---- 结果构造 ----
    def _set(self, state, reasons, conf, perclos, eye_dur, ts) -> StateResult:
        self._state = state
        return StateResult(state, reasons, conf, "online", perclos, eye_dur,
                           self.cfg.model_version, ts)

    def _fault(self, state, reasons, now) -> StateResult:
        self._state = state
        cam = "offline" if state == State.CAMERA_FAULT else "online"
        return StateResult(state, reasons, 0.0, cam, None, 0.0, self.cfg.model_version, now)

    def tick_no_frame(self, now: float, *, camera_online: bool = True) -> StateResult | None:
        """无新帧时由上层定时调用:帧停滞超过 stale_frame_s → CAMERA_FAULT。"""
        if not camera_online:
            return self._fault(State.CAMERA_FAULT, ["camera_offline"], now)
        if self._last_ts is not None and now - self._last_ts >= self.cfg.stale_frame_s:
            return self._fault(State.CAMERA_FAULT, ["frame_stale"], now)
        return None

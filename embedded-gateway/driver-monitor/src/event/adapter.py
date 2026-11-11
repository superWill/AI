#!/usr/bin/env python3
"""事件适配器 —— 把状态机结果落地成事件(去抖 + 周期重报),扇出到可插拔 sink。

职责(handoff §3 的 event-adapter):
  - **去抖**:新状态需稳定 min_dwell_s 才出事件,过滤 1~2 帧抖动(状态机已平滑,这里再兜一层)。
  - **周期重报**:alarm/warning 持续时按 realert_interval_s 重发,让蜂鸣/通知持续,而不是只在切入时响一次。
  - **扇出**:写本地 JSONL 日志 + 任意 sink(MQTT 发布、蜂鸣 GPIO、HMI…)。sink 用回调注入 → 不依赖具体库,可单测。
  - **不把连续视频帧塞进 MQTT**:只发状态/事件 JSON(handoff 红线)。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


@dataclass
class EventAdapterConfig:
    min_dwell_s: float = 0.5                 # 新状态稳定多久才出事件(去抖)
    realert_interval_s: float = 5.0          # 活跃告警重报间隔
    realert_states: tuple = ("alarm", "warning")   # 哪些状态需要周期重报


class Sink:
    """事件接收口。子类实现 emit(event: dict)。"""
    def emit(self, event: dict) -> None:        # pragma: no cover - 接口
        raise NotImplementedError


class CallableSink(Sink):
    """把任意函数包成 sink —— MQTT 发布/蜂鸣/测试注入都走它。"""
    def __init__(self, fn):
        self._fn = fn

    def emit(self, event: dict) -> None:
        self._fn(event)


class JsonlLogSink(Sink):
    """本地事件日志,一行一个 JSON(便于追溯;视频不进这里)。"""
    def __init__(self, path: str):
        self.path = path
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)

    def emit(self, event: dict) -> None:
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")


class EventAdapter:
    """喂 StateResult(或其 to_event() 的 dict),按策略出事件并扇出。"""

    def __init__(self, sinks: list[Sink] | None = None,
                 config: EventAdapterConfig | None = None):
        self.cfg = config or EventAdapterConfig()
        self.sinks = sinks or []
        self._emitted_state: str | None = None   # 上一个已发出的状态
        self._pending: str | None = None          # 正在去抖观察的新状态
        self._pending_since: float = 0.0
        self._last_emit_ts: float = 0.0

    def on_result(self, result, now: float | None = None) -> dict | None:
        """result:有 .state 和 .to_event() 的对象(engine.StateResult)。
        返回本次发出的事件 dict;未发出返回 None。"""
        state = result.state
        now = getattr(result, "ts", 0.0) if now is None else now
        cfg = self.cfg

        if state != self._emitted_state:
            # 新状态:进入/刷新去抖观察
            if state != self._pending:
                self._pending = state
                self._pending_since = now
            if now - self._pending_since >= cfg.min_dwell_s:
                return self._emit(result, now, "transition")
            return None                            # 去抖期内,不发

        # 与已发出状态相同:活跃告警按间隔重报
        self._pending = None
        if state in cfg.realert_states and now - self._last_emit_ts >= cfg.realert_interval_s:
            return self._emit(result, now, "realert")
        return None

    def _emit(self, result, now: float, kind: str) -> dict:
        self._emitted_state = result.state
        self._pending = None
        self._last_emit_ts = now
        event = result.to_event()
        event["event_kind"] = kind                 # transition | realert
        for s in self.sinks:
            try:
                s.emit(event)
            except Exception as exc:               # 单个 sink 失败不拖垮其它(handoff:进程隔离)
                print(f"[event] sink {type(s).__name__} 失败: {exc}", flush=True)
        return event

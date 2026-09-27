#!/usr/bin/env python3
"""事件适配器单测:去抖、周期重报、扇出、本地日志、sink 失败隔离(纯标准库)。"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from event.adapter import (EventAdapter, EventAdapterConfig,          # noqa: E402
                           CallableSink, JsonlLogSink)
from drowsiness.engine import StateResult                            # noqa: E402


def _res(state, ts):
    return StateResult(state=state, reason=[state], confidence=0.9,
                       camera_status="online", model_version="t", ts=ts)


def _adapter(rec, **cfg):
    return EventAdapter(sinks=[CallableSink(rec.append)],
                        config=EventAdapterConfig(**cfg))


def test_transition_emits_after_dwell():
    rec = []
    a = _adapter(rec, min_dwell_s=0.5)
    assert a.on_result(_res("warning", 0.0)) is None      # 刚切入,去抖中
    assert a.on_result(_res("warning", 0.3)) is None
    ev = a.on_result(_res("warning", 0.6))                 # 稳定 >0.5s → 发
    assert ev is not None and ev["state"] == "warning" and ev["event_kind"] == "transition"
    assert len(rec) == 1


def test_flap_suppressed():
    """瞬时切到 warning 又回 normal,没稳定到 dwell → 不发。"""
    rec = []
    a = _adapter(rec, min_dwell_s=0.5)
    a.on_result(_res("normal", 0.0))
    a.on_result(_res("warning", 0.1))       # 抖一下
    a.on_result(_res("normal", 0.2))        # 又回去
    assert rec == []                         # 没有任何事件发出


def test_realert_for_active_alarm():
    rec = []
    a = _adapter(rec, min_dwell_s=0.0, realert_interval_s=5.0, realert_states=("alarm",))
    assert a.on_result(_res("alarm", 0.0)) is not None     # 切入即发(dwell=0)
    assert a.on_result(_res("alarm", 2.0)) is None         # 未到重报间隔
    assert a.on_result(_res("alarm", 5.1)) is not None     # 到间隔 → 重报
    assert [e["event_kind"] for e in rec] == ["transition", "realert"]


def test_normal_does_not_realert():
    rec = []
    a = _adapter(rec, min_dwell_s=0.0, realert_states=("alarm", "warning"))
    a.on_result(_res("normal", 0.0))         # 首次进 normal 发一次 transition
    a.on_result(_res("normal", 100.0))       # normal 不在 realert_states → 不重报
    assert len(rec) == 1


def test_jsonl_log_written():
    rec = []
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "events.jsonl")
        a = EventAdapter(sinks=[JsonlLogSink(path), CallableSink(rec.append)],
                         config=EventAdapterConfig(min_dwell_s=0.0))
        a.on_result(_res("alarm", 1.0))
        lines = open(path, encoding="utf-8").read().strip().splitlines()
        assert len(lines) == 1
        ev = json.loads(lines[0])
        assert ev["state"] == "alarm" and ev["type"] == "driver_monitor_event"


def test_sink_failure_isolated():
    """一个 sink 抛异常,不影响其它 sink 收到事件。"""
    rec = []

    def boom(_):
        raise RuntimeError("mqtt down")
    a = EventAdapter(sinks=[CallableSink(boom), CallableSink(rec.append)],
                     config=EventAdapterConfig(min_dwell_s=0.0))
    ev = a.on_result(_res("warning", 0.0))
    assert ev is not None and len(rec) == 1        # 第二个 sink 仍收到


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

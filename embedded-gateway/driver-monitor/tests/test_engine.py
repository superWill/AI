#!/usr/bin/env python3
"""疲劳状态机单测(纯标准库,python3 tests/test_engine.py 即可跑,Mac 上无需板子)。

重点验证 handoff §4 的硬约束:
  - 不单帧报警:特征进时间窗。
  - 故障态独立、优先,绝不被解释成"正常"。
  - 微睡/PERCLOS/哈欠/偏头各自能触发对应状态。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from drowsiness.engine import (DrowsinessEngine, DrowsinessConfig,   # noqa: E402
                               FrameObservation, State)


def _eng(**over):
    cfg = DrowsinessConfig(model_version="test-v1", **over)
    return DrowsinessEngine(cfg)


def _frame(ts, ear=0.30, mar=0.2, yaw=0.0, pitch=0.0, face=True, infer=True):
    return FrameObservation(ts=ts, face_present=face, infer_ok=infer,
                            ear=ear, mar=mar, yaw=yaw, pitch=pitch, confidence=0.9)


def _run(eng, frames, **kw):
    r = None
    for f in frames:
        r = eng.update(f, **kw)
    return r


def test_open_eyes_normal():
    eng = _eng()
    r = _run(eng, [_frame(t * 0.1, ear=0.30) for t in range(50)])
    assert r.state == State.NORMAL, r.state
    assert r.perclos == 0.0


def test_microsleep_continuous_closure_alarm():
    """连续闭眼 ≥ eye_closed_alarm_s(2s)→ alarm;不到则不报。"""
    eng = _eng(eye_closed_alarm_s=2.0)
    # 1.5s 闭眼:还不到微睡门
    r = _run(eng, [_frame(t * 0.1, ear=0.10) for t in range(15)])
    assert r.state in (State.SUSPECTED,), r.state
    # 继续闭到 >2s
    r = _run(eng, [_frame(1.5 + t * 0.1, ear=0.10) for t in range(10)])
    assert r.state == State.ALARM, r.state
    assert "microsleep_eyes_closed" in r.reason


def test_perclos_warning_then_alarm():
    """窗口内闭眼占比升高 → warning → alarm。"""
    eng = _eng(perclos_window_s=10.0, perclos_warn=0.15, perclos_alarm=0.30,
               eye_closed_alarm_s=99)  # 排除微睡干扰,只看 PERCLOS
    # 交替:30% 帧闭眼 → 应进 warning/alarm 区间
    frames = []
    for t in range(100):
        closed = (t % 10) < 3            # 30% 闭眼
        frames.append(_frame(t * 0.1, ear=0.10 if closed else 0.30))
    r = _run(eng, frames)
    assert r.perclos >= 0.25, r.perclos
    assert r.state in (State.WARNING, State.ALARM), r.state


def test_frequent_yawning_warning():
    eng = _eng(yawn_window_s=120, yawn_count_warn=3, mar_yawn_thresh=0.6,
               yawn_min_s=0.4, eye_closed_alarm_s=99)
    t = 0.0
    frames = []
    for _ in range(4):                   # 4 次哈欠
        for _ in range(8):               # 张嘴 0.8s
            frames.append(_frame(t, mar=0.8)); t += 0.1
        for _ in range(12):              # 闭嘴 1.2s
            frames.append(_frame(t, mar=0.2)); t += 0.1
    r = _run(eng, frames)
    assert "frequent_yawning" in r.reason, r.reason
    assert r.state == State.WARNING, r.state


def test_head_off_road_alarm():
    eng = _eng(head_away_yaw=35, head_off_alarm_s=3.0, eye_closed_alarm_s=99)
    r = _run(eng, [_frame(t * 0.1, yaw=50.0) for t in range(40)])  # 持续扭头 4s
    assert r.state == State.ALARM and "head_off_road" in r.reason, (r.state, r.reason)


# ---- 故障态:必须独立、优先,绝不当 normal ----
def test_camera_offline_is_fault_not_normal():
    eng = _eng()
    r = eng.update(_frame(1.0, ear=0.30), camera_online=False)
    assert r.state == State.CAMERA_FAULT and r.camera_status == "offline"


def test_model_failure_is_fault_even_with_closed_eyes():
    """推理失败时即使"看起来闭眼"也不能判疲劳,而是 model_fault。"""
    eng = _eng()
    r = eng.update(_frame(1.0, ear=0.05, infer=False))
    assert r.state == State.MODEL_FAULT, r.state


def test_timestamp_regression_is_model_fault():
    eng = _eng()
    eng.update(_frame(5.0))
    r = eng.update(_frame(3.0))          # 时间戳倒退
    assert r.state == State.MODEL_FAULT and "timestamp_regression" in r.reason


def test_face_lost_grace_then_no_face():
    eng = _eng(face_lost_grace_s=2.0)
    eng.update(_frame(0.0))
    # 丢脸 1s:宽限内,不报 NO_FACE
    r = _run(eng, [_frame(0.1 + t * 0.1, face=False) for t in range(10)])
    assert r.state != State.NO_FACE, r.state
    # 丢脸超过 2s → NO_FACE
    r = _run(eng, [_frame(1.2 + t * 0.1, face=False) for t in range(15)])
    assert r.state == State.NO_FACE and "face_lost" in r.reason


def test_frame_stale_via_tick():
    eng = _eng(stale_frame_s=2.0)
    eng.update(_frame(10.0))
    assert eng.tick_no_frame(now=11.0) is None          # 1s 内不报
    r = eng.tick_no_frame(now=12.5)                       # >2s 停滞
    assert r is not None and r.state == State.CAMERA_FAULT and "frame_stale" in r.reason


def test_event_json_shape():
    eng = _eng()
    r = eng.update(_frame(1.0, ear=0.30))
    ev = r.to_event()
    for k in ("type", "state", "reason", "confidence", "camera_status",
              "model_version", "timestamp"):
        assert k in ev, k
    assert ev["type"] == "driver_monitor_event"
    assert ev["model_version"] == "test-v1"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

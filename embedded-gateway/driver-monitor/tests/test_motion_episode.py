#!/usr/bin/env python3
"""Motion episode 迟滞状态机单测(纯标准库,python3 tests/test_motion_episode.py 即可跑)。

验证 ADR-0001 的硬约束:
  - 进场即发 OPEN(靠 open 触发,不靠 close);离场发同 event_id 的 CLOSE。
  - 迟滞:不够 N_enter 不 OPEN;不够 N_exit 不 CLOSE(过滤抖动/运动间隙)。
  - 时间诚实:ts_start = 运动真正开始,ts_end = 运动真正停止(不含静默尾巴)。
  - 只产 motion_episode 事实,不产 person/intrusion。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from motion.episode import (EpisodeStateMachine, EpisodeConfig,   # noqa: E402
                            EpisodeState)


def _sm(**over):
    return EpisodeStateMachine(EpisodeConfig(**over))


def _feed(sm, seq, dt=0.1, t0=0.0, score=0.5):
    """seq: 可迭代的 bool(moving)。返回所有发出的事件。"""
    events = []
    t = t0
    for moving in seq:
        events += sm.update(t, bool(moving), score if moving else 0.0)
        t = round(t + dt, 6)
    return events


def test_open_after_n_enter_not_before():
    sm = _sm(n_enter=4, n_exit=30)
    # 3 帧 moving:还不够,不 OPEN
    ev = _feed(sm, [1, 1, 1])
    assert ev == [], ev
    assert sm.state == EpisodeState.IDLE
    # 第 4 帧:OPEN
    ev = _feed(sm, [1], t0=0.3)
    assert len(ev) == 1 and ev[0]["event_kind"] == "open", ev
    assert sm.state == EpisodeState.ACTIVE


def test_open_ts_start_is_motion_onset_not_nth_frame():
    """ts_start 应为运动真正开始(首帧),不是达阈值的第 N 帧。"""
    sm = _sm(n_enter=4)
    ev = _feed(sm, [1, 1, 1, 1], dt=0.1, t0=0.0)
    assert ev[0]["ts_start"] == 0.0, ev[0]["ts_start"]   # 首帧,非 0.3


def test_intermittent_moving_resets_enter_run():
    """要求连续:moving 被 quiet 打断则重新计数,不误 OPEN。"""
    sm = _sm(n_enter=4)
    ev = _feed(sm, [1, 1, 0, 1, 1, 1])   # 最长连续 run = 3 < 4
    assert ev == [], ev
    assert sm.state == EpisodeState.IDLE


def test_close_after_n_exit_not_before():
    sm = _sm(n_enter=4, n_exit=30)
    _feed(sm, [1, 1, 1, 1])                        # OPEN
    # 29 帧 quiet:还不够 CLOSE
    ev = _feed(sm, [0] * 29, t0=0.4)
    assert ev == [], ev
    assert sm.state == EpisodeState.ACTIVE
    # 第 30 帧 quiet:CLOSE
    ev = _feed(sm, [0], t0=0.4 + 29 * 0.1)
    assert len(ev) == 1 and ev[0]["event_kind"] == "close", ev
    assert sm.state == EpisodeState.IDLE


def test_quiet_gap_shorter_than_n_exit_does_not_split_episode():
    """运动中的短暂静默(< N_exit)不切断 episode;整段仍是一个 episode。"""
    sm = _sm(n_enter=4, n_exit=30)
    events = []
    events += _feed(sm, [1, 1, 1, 1])              # OPEN
    events += _feed(sm, [0] * 10, t0=0.4)          # 10 帧静默(< 30),不 CLOSE
    events += _feed(sm, [1, 1, 1], t0=1.4)         # 恢复运动
    events += _feed(sm, [0] * 30, t0=1.7)          # 30 帧静默 → CLOSE
    kinds = [e["event_kind"] for e in events]
    assert kinds == ["open", "close"], kinds       # 只一对,没被切成两段


def test_close_ts_end_is_last_moving_not_close_frame():
    """ts_end = 运动真正停止(最后一帧 moving),不含末尾 N_exit 静默尾巴。"""
    sm = _sm(n_enter=4, n_exit=30)
    _feed(sm, [1, 1, 1, 1], dt=0.1, t0=0.0)        # moving 到 t=0.3
    ev = _feed(sm, [0] * 30, dt=0.1, t0=0.4)       # 静默从 0.4 起,CLOSE 在 t≈3.3
    close = ev[0]
    assert close["ts_end"] == 0.3, close["ts_end"] # 最后一帧 moving 是 0.3
    assert close["ts_start"] == 0.0
    assert abs(close["duration_s"] - 0.3) < 1e-6, close["duration_s"]


def test_peak_motion_tracked_over_episode():
    sm = _sm(n_enter=4, n_exit=3)
    events = []
    t = 0.0
    for sc in [0.2, 0.3, 0.4, 0.9, 0.5]:           # 峰值 0.9(在 ACTIVE 期)
        events += sm.update(t, True, sc); t += 0.1
    events += _feed(sm, [0, 0, 0], t0=t)           # CLOSE
    close = [e for e in events if e["event_kind"] == "close"][0]
    assert close["peak_motion"] == 0.9, close["peak_motion"]


def test_peak_includes_enter_window_frames():
    """峰值出现在进场窗口(前 N_enter 帧)时,不得被丢——ts_start/moving_frames 都算它们。"""
    sm = _sm(n_enter=4, n_exit=3)
    events = []
    t = 0.0
    for sc in [0.2, 0.9, 0.4, 0.5, 0.3]:           # 峰值 0.9 在第 2 帧(进场窗口内)
        events += sm.update(t, True, sc); t += 0.1
    events += _feed(sm, [0, 0, 0], t0=t)           # CLOSE
    close = [e for e in events if e["event_kind"] == "close"][0]
    assert close["peak_motion"] == 0.9, close["peak_motion"]


def test_peak_resets_when_enter_run_interrupted():
    """进场窗口被 quiet 打断后,残留的高分不得泄漏进下一段/下一 episode 的峰值。"""
    sm = _sm(n_enter=4, n_exit=3)
    events = []
    t = 0.0
    # 先来 2 帧高分 moving,再 quiet 打断(run 作废)
    for sc in [0.9, 0.8]:
        events += sm.update(t, True, sc); t += 0.1
    events += sm.update(t, False, 0.0); t += 0.1
    # 重新一段全低分 moving → OPEN,再 CLOSE
    for sc in [0.1, 0.1, 0.1, 0.1]:
        events += sm.update(t, True, sc); t += 0.1
    events += _feed(sm, [0, 0, 0], t0=t)
    close = [e for e in events if e["event_kind"] == "close"][0]
    assert close["peak_motion"] == 0.1, close["peak_motion"]


def test_open_and_close_share_event_id():
    sm = _sm(n_enter=4, n_exit=3)
    events = _feed(sm, [1, 1, 1, 1] + [0, 0, 0])
    opens = [e for e in events if e["event_kind"] == "open"]
    closes = [e for e in events if e["event_kind"] == "close"]
    assert opens[0]["event_id"] == closes[0]["event_id"]


def test_second_episode_gets_new_event_id():
    sm = _sm(n_enter=4, n_exit=3)
    ev1 = _feed(sm, [1, 1, 1, 1] + [0, 0, 0])
    ev2 = _feed(sm, [1, 1, 1, 1] + [0, 0, 0], t0=1.0)
    id1 = ev1[0]["event_id"]
    id2 = ev2[0]["event_id"]
    assert id1 != id2, (id1, id2)
    assert id1 == "ep-000001" and id2 == "ep-000002", (id1, id2)


def test_event_is_motion_episode_not_person_or_intrusion():
    """ADR-0001:P0 只产 motion_episode 事实,不产 person_present/intrusion。"""
    sm = _sm(n_enter=4, n_exit=3)
    events = _feed(sm, [1, 1, 1, 1] + [0, 0, 0])
    for e in events:
        assert e["type"] == "motion_episode", e["type"]
        assert "person" not in e["type"] and "intrusion" not in e["type"]


def test_open_event_shape():
    sm = _sm(n_enter=4)
    ev = _feed(sm, [1, 1, 1, 1])[0]
    for k in ("type", "event_kind", "event_id", "ts_start", "motion_score", "timestamp"):
        assert k in ev, k


def test_close_event_shape():
    sm = _sm(n_enter=4, n_exit=3)
    ev = [e for e in _feed(sm, [1, 1, 1, 1] + [0, 0, 0]) if e["event_kind"] == "close"][0]
    for k in ("type", "event_kind", "event_id", "ts_start", "ts_end",
              "duration_s", "peak_motion", "moving_frames", "closed_by", "timestamp"):
        assert k in ev, k
    assert ev["closed_by"] == "quiet_timeout", ev["closed_by"]


def test_force_close_active_episode_emits_camera_fault_close():
    """相机停流强制收尾:ACTIVE → 发 CLOSE(closed_by=camera_fault),ts_end=最后 moving。"""
    sm = _sm(n_enter=4, n_exit=30)
    _feed(sm, [1, 1, 1, 1], dt=0.1, t0=0.0)        # OPEN,最后 moving 在 t=0.3
    assert sm.active
    ev = sm.force_close(5.0, "camera_fault")       # 5s 后相机死
    assert ev is not None
    assert ev["event_kind"] == "close"
    assert ev["closed_by"] == "camera_fault"
    assert ev["ts_end"] == 0.3, ev["ts_end"]       # 诚实:最后可见运动,不是故障时刻
    assert sm.state == EpisodeState.IDLE           # 不留悬空 OPEN


def test_force_close_when_idle_is_noop():
    sm = _sm(n_enter=4, n_exit=3)
    assert sm.force_close(1.0) is None             # IDLE 无可收尾
    _feed(sm, [1, 1, 1, 1] + [0, 0, 0])            # 走完一个 episode → 回 IDLE
    assert sm.force_close(9.0) is None


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

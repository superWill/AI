#!/usr/bin/env python3
"""MotionPipeline 粘合层单测(纯标准库,注入 fake detector → 免 numpy/硬件)。

验证多摄/相机健康的硬约束:
  - 每条事件都打上正确 cam_id。
  - 各摄独立的 detector+episode:一路故障不影响另一路。
  - 停流 → camera_health(stale) + 强制收尾 ACTIVE episode(不留悬空 OPEN,不静默丢)。
  - 恢复出帧 → camera_health(online);stale 只报一次不刷屏。
  - 死摄(开机就无帧)也能凭 started_ts 判 stale。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from motion.episode import EpisodeStateMachine, EpisodeConfig    # noqa: E402
from motion.pipeline import MotionPipeline                        # noqa: E402


class _Sample:
    def __init__(self, ts, moving, score):
        self.ts, self.moving, self.score = ts, moving, score


class FakeDetector:
    """按脚本吐 moving/score,不碰像素。process 忽略 frame。"""
    def __init__(self):
        self.reset_count = 0

    def process(self, ts, frame):
        moving, score = frame        # 测试里把 (moving, score) 当 frame 传进来
        return _Sample(ts, moving, score)

    def reset(self):
        self.reset_count += 1


def _pipe(cam_id="cam0", n_enter=4, n_exit=30, stale=2.0):
    det = FakeDetector()
    ep = EpisodeStateMachine(EpisodeConfig(n_enter=n_enter, n_exit=n_exit))
    return MotionPipeline(cam_id, det, ep, stale_after_s=stale), det


def _drive(pipe, seq, dt=0.1, t0=0.0):
    """seq: [(moving, score), ...] → 逐帧 process。返回全部事件。"""
    events, t = [], t0
    for moving, score in seq:
        events += pipe.process_frame(round(t, 6), (moving, score))
        t += dt
    return events


def test_events_tagged_with_cam_id():
    pipe, _ = _pipe("front", n_enter=4, n_exit=3)
    events = _drive(pipe, [(True, 0.5)] * 4 + [(False, 0.0)] * 3)
    assert events, "应有 open+close"
    for ev in events:
        assert ev["cam_id"] == "front", ev


def test_open_close_roundtrip_through_pipeline():
    pipe, _ = _pipe(n_enter=4, n_exit=3)
    events = _drive(pipe, [(True, 0.5)] * 4 + [(False, 0.0)] * 3)
    kinds = [e["event_kind"] for e in events if e["type"] == "motion_episode"]
    assert kinds == ["open", "close"], kinds


def test_stale_emits_health_and_force_closes_active_episode():
    pipe, det = _pipe("yard", n_enter=4, n_exit=30, stale=2.0)
    _drive(pipe, [(True, 0.5)] * 4, t0=0.0)         # OPEN(最后帧 t=0.3)
    assert pipe.episode.active
    # 5s 后无帧 → stale
    evs = pipe.tick_no_frame(5.0)
    types = [(e["type"], e.get("status") or e.get("closed_by")) for e in evs]
    assert ("camera_health", "stale") in types
    assert ("motion_episode", "camera_fault") in types
    assert all(e["cam_id"] == "yard" for e in evs)
    assert not pipe.episode.active                  # 不留悬空 OPEN
    assert det.reset_count == 1                     # 背景将重建
    assert not pipe.online


def test_stale_reported_only_once():
    pipe, _ = _pipe(stale=2.0)
    _drive(pipe, [(True, 0.5)], t0=0.0)             # 有过一帧
    assert pipe.tick_no_frame(5.0)                  # 首次 stale
    assert pipe.tick_no_frame(6.0) == []            # 不刷屏
    assert pipe.tick_no_frame(9.0) == []


def test_recovery_emits_online_then_processes():
    pipe, det = _pipe(n_enter=4, n_exit=3, stale=2.0)
    _drive(pipe, [(True, 0.5)], t0=0.0)
    pipe.tick_no_frame(5.0)                          # stale
    assert not pipe.online
    evs = pipe.process_frame(6.0, (False, 0.0))      # 恢复出帧
    assert evs[0]["type"] == "camera_health" and evs[0]["status"] == "online"
    assert pipe.online


def test_dead_camera_from_start_goes_stale_via_started_ts():
    pipe, _ = _pipe(stale=2.0)
    pipe.mark_started(100.0)                          # 起跑,但一帧没来
    assert pipe.tick_no_frame(101.0) == []           # 1s 内不报
    evs = pipe.tick_no_frame(102.5)                  # >2s → stale
    assert any(e["type"] == "camera_health" and e["status"] == "stale" for e in evs)


def test_two_cameras_are_independent():
    """两路各自 detector+episode:A 路故障不影响 B 路正常出 episode。"""
    a, _ = _pipe("A", n_enter=4, n_exit=3, stale=2.0)
    b, _ = _pipe("B", n_enter=4, n_exit=3, stale=2.0)
    _drive(a, [(True, 0.5)] * 4, t0=0.0)             # A OPEN
    a_fault = a.tick_no_frame(5.0)                    # A 停流 → 强制收尾
    # B 独立跑完一个完整 episode
    b_events = _drive(b, [(True, 0.7)] * 4 + [(False, 0.0)] * 3, t0=0.0)
    assert any(e["cam_id"] == "A" for e in a_fault)
    b_ep = [e for e in b_events if e["type"] == "motion_episode"]
    assert [e["event_kind"] for e in b_ep] == ["open", "close"]
    assert all(e["cam_id"] == "B" for e in b_ep)
    # A 的事件里绝不该冒出 B 的 cam_id,反之亦然
    assert all(e["cam_id"] == "A" for e in a_fault)


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

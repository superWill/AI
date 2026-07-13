#!/usr/bin/env python3
"""报警抓拍编排单测(纯标准库,注入 fake 源/快照/上传器)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.pipeline import AlarmSnapshotPipeline                # noqa: E402
from alarm.alarm_source import FakeAlarmSource                  # noqa: E402
from alarm.snapshot import FakeSnapshotGrabber                  # noqa: E402
from uplink.media_outbox import MediaOutbox, MediaOutboxState   # noqa: E402
from uplink.oss_media import FakeMediaUploader, event_media_key  # noqa: E402


def _setup(snapshot_online=True):
    alarm = FakeAlarmSource("smoke-1")
    snap = FakeSnapshotGrabber(jpeg=b"\xff\xd8\xffIMG", online=snapshot_online)
    up = FakeMediaUploader()
    spool = MediaOutbox(up)
    captured = []
    pipe = AlarmSnapshotPipeline(alarm, snap, spool, prefix="dm",
                                 on_captured=lambda e, k, s: captured.append((e, k, s)))
    return alarm, snap, up, spool, pipe, captured


def test_alarm_grabs_snapshot_and_enqueues():
    alarm, snap, up, spool, pipe, captured = _setup()
    pipe.tick(now=0.0)                                    # 无报警 → 无事
    assert spool.pending_count == 0
    alarm.fire(now=100.0)
    pipe.tick(now=100.0)                                  # 报警 → 抓图 → 入队
    key = event_media_key("dm", "alarm-smoke-1-100", "snapshot", ext="jpg")
    assert spool.pending_count == 1 and spool.state_of(key) == MediaOutboxState.QUEUED
    assert captured == [("alarm-smoke-1-100", key, 6)]   # on_captured 触发(6=len jpeg)
    spool.pump(now=100.0)                                 # ship → (假)OSS
    assert up.get(key) == b"\xff\xd8\xffIMG"


def test_alarm_high_priority_never_dropped():
    # 报警快照以 first_frame 入队 → 最高优先 + 永不淘汰
    alarm, snap, up, spool, pipe, _ = _setup()
    alarm.fire(now=1.0)
    pipe.tick(now=1.0)
    key = event_media_key("dm", "alarm-smoke-1-1", "snapshot", ext="jpg")
    # first_frame 类不受 cappable_cap 影响,恒在队
    assert spool.state_of(key) == MediaOutboxState.QUEUED


def test_snapshot_failed_not_enqueued_and_alerts():
    alarm, snap, up, spool, pipe, captured = _setup(snapshot_online=False)  # 相机离线
    alarm.fire(now=50.0)
    health = pipe.tick(now=50.0)
    assert spool.pending_count == 0 and captured == []   # 抓图失败 → 不入队
    assert any(h["status"] == "alarm_snapshot_failed" for h in health)  # 发告警,不静默


def test_event_id_idempotent_same_source_same_second():
    alarm, snap, up, spool, pipe, _ = _setup()
    alarm.fire(now=200.4)
    alarm.fire(now=200.7)                                 # 同源同秒
    pipe.tick(now=200.7)
    assert spool.pending_count == 1                       # 同 event_id/key → 幂等,只一条


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

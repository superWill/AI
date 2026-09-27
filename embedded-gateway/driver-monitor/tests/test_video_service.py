#!/usr/bin/env python3
"""视频工具服务单测(纯标准库,注入 fake grabber/uploader/analyzer,零网络)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.snapshot import FakeSnapshotGrabber                 # noqa: E402
from uplink.media_outbox import MediaOutbox, MediaOutboxState  # noqa: E402
from uplink.oss_media import FakeMediaUploader                 # noqa: E402
from video.analyze import StubVisionAnalyzer                   # noqa: E402
from video.service import VideoToolService                     # noqa: E402

JPEG = b"\xff\xd8\xff\xe0" + b"scene" * 40


def _svc(cam_online=True, up_online=True):
    grab = FakeSnapshotGrabber(jpeg=JPEG, online=cam_online)
    up = FakeMediaUploader(online=up_online)
    outbox = MediaOutbox(up)
    svc = VideoToolService(grab, outbox, StubVisionAnalyzer(), up.object_url,
                           go2rtc_base="http://lobster:1984/", default_cam="cam",
                           prefix="dm", clock=lambda: 1000.0)
    return svc, grab, up, outbox


def test_snapshot_grabs_enqueues_ships_and_returns_url():
    svc, grab, up, outbox = _svc()
    status, body = svc.snapshot(now=1000.0)
    assert status == 200 and body["ok"]
    assert body["key"] == "dm/events/snap-cam-1000/snapshot.jpg"
    assert body["url"] == up.object_url(body["key"])          # 预算 URL 即最终 URL
    assert body["bytes"] == len(JPEG)
    # snapshot 内部 pump 了一次 → 已 ship 到(假)OSS
    assert up._objects[body["key"]] == JPEG
    assert body["state"] == MediaOutboxState.UPLOADED


def test_snapshot_camera_offline_503_not_enqueued():
    svc, grab, up, outbox = _svc(cam_online=False)
    status, body = svc.snapshot(now=1000.0)
    assert status == 503 and not body["ok"] and body["error"] == "snapshot_failed"
    assert outbox.pending_count == 0                           # 抓图失败不入队


def test_snapshot_agent_offline_queues_for_retry():
    svc, grab, up, outbox = _svc(up_online=False)              # agent/OSS 下线
    status, body = svc.snapshot(now=1000.0)
    assert status == 200 and body["ok"]                        # 抓到了,先返预算 URL
    assert body["state"] == MediaOutboxState.QUEUED            # 没 ship 出去,留队
    assert outbox.pending_count == 1
    up.set_online(True)                                        # agent 上线
    outbox.pump(1031.0)                                         # 过 resend_after_s(30s)才重试
    assert outbox.state_of(body["key"]) == MediaOutboxState.UPLOADED   # 补传


def test_snapshot_alarm_kind_first_frame():
    svc, grab, up, outbox = _svc(up_online=False)
    status, body = svc.snapshot(event_id="alarm-smoke-1-1000", kind="first_frame", now=1000.0)
    assert body["kind"] == "first_frame"                      # 报警证据:最高优先+永不淘汰
    assert body["key"] == "dm/events/alarm-smoke-1-1000/snapshot.jpg"


def test_live_returns_go2rtc_urls():
    svc, *_ = _svc()
    status, body = svc.live(cam="cam")
    assert status == 200 and body["ok"]
    assert body["urls"]["html"] == "http://lobster:1984/stream.html?src=cam"
    assert body["urls"]["hls"] == "http://lobster:1984/api/stream.m3u8?src=cam"
    assert body["urls"]["mp4"] == "http://lobster:1984/api/stream.mp4?src=cam"


def test_analyze_stub_not_implemented():
    svc, *_ = _svc()
    status, body = svc.analyze(cam="cam")
    assert status == 200 and body["ok"]
    assert body["result"]["status"] == "not_implemented"      # 留桩明确,不假装有结果
    assert body["result"]["model"] == "stub"
    assert body["result"]["detections"] == []


def test_analyze_camera_offline_503():
    svc, *_ = _svc(cam_online=False)
    status, body = svc.analyze(cam="cam")
    assert status == 503 and not body["ok"]


def test_health_camera_ok_and_offline():
    svc, grab, up, outbox = _svc()
    status, body = svc.health(now=1000.0)
    assert status == 200 and body["camera_ok"] and body["analyzer"] == "stub"
    assert body["snapshot_bytes"] == len(JPEG)
    grab.online = False
    status, body = svc.health(now=1000.0)
    assert status == 503 and not body["camera_ok"]            # 相机离线 → 503,不静默


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

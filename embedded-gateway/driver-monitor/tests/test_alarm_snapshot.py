#!/usr/bin/env python3
"""快照抓取器单测(纯标准库,不发网络)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.snapshot import (                                    # noqa: E402
    HttpSnapshotGrabber, FakeSnapshotGrabber, SnapshotConfig, _is_jpeg)


def test_jpeg_magic_validation():
    assert _is_jpeg(b"\xff\xd8\xff\xe0rest")
    assert not _is_jpeg(b"<html>not a jpeg")
    assert not _is_jpeg(b"")


def test_fake_grabber_online_offline():
    g = FakeSnapshotGrabber(jpeg=b"\xff\xd8\xffXY")
    assert g.grab() == b"\xff\xd8\xffXY" and g.grab_count == 1
    g.online = False
    assert g.grab() is None


def test_http_build_request_url_and_basic_auth():
    g = HttpSnapshotGrabber(SnapshotConfig(
        url="http://192.168.1.217/webcapture.jpg?command=snap&channel=0",
        username="admin", password=""))
    host, port, path, headers, secure = g._build_request()
    assert host == "192.168.1.217" and port == 80 and secure is False
    assert path == "/webcapture.jpg?command=snap&channel=0"
    # Basic base64("admin:")
    import base64
    assert headers["Authorization"] == "Basic " + base64.b64encode(b"admin:").decode()


def test_http_build_request_https_default_port():
    g = HttpSnapshotGrabber(SnapshotConfig(url="https://cam.local/snap.jpg"))
    host, port, path, headers, secure = g._build_request()
    assert host == "cam.local" and port == 443 and secure is True
    assert "Authorization" not in headers                 # 无凭证不加头


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

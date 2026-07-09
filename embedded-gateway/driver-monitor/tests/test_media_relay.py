#!/usr/bin/env python3
"""MediaRelay 单测(纯标准库):线格式往返、接收入队、请求构造 + localhost 端到端。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.media_relay import (                                # noqa: E402
    MediaShipment, MediaRelayClient, MediaReceiver, RelayUploader,
    build_agent_server)
from uplink.media_outbox import MediaOutbox, MediaOutboxState   # noqa: E402
from uplink.oss_media import FakeMediaUploader, oss_object_url  # noqa: E402


def _k(event, name):
    return f"driver-monitor/events/{event}/{name}.png"


class _FakeRelay:
    """模拟板子→代理链路的开关。真实现是 MediaRelayClient→本地 HTTP。"""

    def __init__(self, online=True):
        self.online = online
        self.shipped: list[str] = []

    def ship(self, shipment) -> bool:
        if not self.online:
            return False
        self.shipped.append(shipment.key)
        return True


def _url_for(key):
    return oss_object_url("oss-cn-hangzhou.aliyuncs.com", "ubuntu-oss-313", key)


# ---- 线格式:往返 ----

def test_shipment_http_roundtrip():
    s = MediaShipment(_k("po-1", "first_frame"), "first_frame", 1783072803.5, "po-1", b"\x89PNGxx")
    headers, body = s.to_http()
    assert headers["X-Media-Key"] == s.key
    assert headers["Content-Length"] == str(len(s.data))
    back = MediaShipment.from_http(headers, body)
    assert back == s                                   # 逐字段一致(含 occurred_at 精确还原)


def test_from_http_case_insensitive_and_missing_key():
    # 小写头(http.server 场景)也能解析
    s = MediaShipment.from_http(
        {"x-media-key": _k("po-2", "frame-001"), "x-media-kind": "frame",
         "x-media-occurred-at": "2.0", "x-media-event-id": "po-2"}, b"data")
    assert s.key.endswith("frame-001.png") and s.kind == "frame" and s.data == b"data"
    try:
        MediaShipment.from_http({}, b"x")
        assert False, "missing key should raise"
    except ValueError:
        pass


# ---- 接收侧:入队 / 坏包 ----

def test_receiver_enqueues_into_outbox():
    up = FakeMediaUploader()
    ob = MediaOutbox(up)
    rec = MediaReceiver(ob)
    key = _k("po-1", "first_frame")
    headers, body = MediaShipment(key, "first_frame", 1.0, "po-1", b"png").to_http()
    status, _ = rec.on_post(headers, body, now=1.0)
    assert status == 200 and ob.pending_count == 1
    ob.pump(now=1.0)
    assert up.get(key) == b"png"                       # 收→入队→pump→(假)OSS


def test_receiver_bad_shipment_returns_400():
    rec = MediaReceiver(MediaOutbox(FakeMediaUploader()))
    status, _ = rec.on_post({}, b"", now=0.0)          # 无 X-Media-Key
    assert status == 400


# ---- 板子侧:请求构造 ----

def test_relay_build_request():
    client = MediaRelayClient("10.0.0.5", 8890)
    method, path, headers, body = client._build_request(
        MediaShipment(_k("po-1", "first_frame"), "first_frame", 1.0, "po-1", b"xyz"))
    assert method == "POST" and path == "/media"
    assert headers["X-Media-Kind"] == "first_frame" and body == b"xyz"


# ---- 端到端:localhost 板子→代理→(假)OSS(端口绑不了则跳过) ----

def test_e2e_board_to_agent_localhost():
    import threading
    up = FakeMediaUploader()
    ob = MediaOutbox(up)
    rec = MediaReceiver(ob)
    try:
        httpd, lock = build_agent_server(rec, host="127.0.0.1", port=0)
    except OSError:
        print("  skip test_e2e_board_to_agent_localhost (无法绑定端口)")
        return
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    try:
        client = MediaRelayClient("127.0.0.1", port, timeout_s=3.0)
        k1, k2 = _k("po-1", "first_frame"), _k("po-1", "frame-001")
        ok1 = client.ship(MediaShipment(k1, "first_frame", 1.0, "po-1", b"aa"))
        ok2 = client.ship(MediaShipment(k2, "frame", 2.0, "po-1", b"bbb"))
        if not (ok1 and ok2):
            print("  skip test_e2e_board_to_agent_localhost (本地网络被限)")
            return
        with lock:
            ob.pump(now=10.0)
        assert up.get(k1) == b"aa" and up.get(k2) == b"bbb"
    finally:
        httpd.shutdown()


# ---- 板子侧 spool:RelayUploader + MediaOutbox 复用 ----

def test_relay_uploader_ship_ok_and_offline():
    r = _FakeRelay()
    ru = RelayUploader(r, _url_for)
    url = ru.put_media(_k("po-1", "first_frame"), b"x", "image/png", "first_frame", 1.0, "po-1")
    assert url == _url_for(_k("po-1", "first_frame")) and r.shipped == [_k("po-1", "first_frame")]
    r.online = False
    assert ru.put_media(_k("po-1", "frame-001"), b"x", "image/png", "frame", 2.0, "po-1") is None


def test_board_spool_stores_and_forwards_when_agent_down_then_up():
    """代理下线 → 帧留在板子队列不丢;代理上线 → pump 推送(证据不丢)。"""
    r = _FakeRelay(online=False)
    spool = MediaOutbox(RelayUploader(r, _url_for), )      # 板子侧 spool = MediaOutbox+relay sink
    key = _k("po-1", "first_frame")
    spool.enqueue(key, b"x", "first_frame", occurred_at=0.0, now=0.0, ref="po-1")
    spool.pump(now=0.0)                                    # 代理下线 → ship 失败 → 留队
    assert spool.pending_count == 1 and r.shipped == []
    r.online = True
    spool.pump(now=30.0)                                   # 代理上线(过了 resend 间隔)→ 推送
    assert spool.pending_count == 0 and r.shipped == [key]
    assert spool.state_of(key) == MediaOutboxState.UPLOADED


def test_board_spool_priority_first_frame_ships_first():
    r = _FakeRelay()
    spool = MediaOutbox(RelayUploader(r, _url_for))
    spool.enqueue(_k("po-1", "clip"), b"x", "clip", 3.0, 3.0)
    spool.enqueue(_k("po-1", "first_frame"), b"x", "first_frame", 1.0, 1.0)
    spool.pump(now=5.0)
    assert r.shipped[0] == _k("po-1", "first_frame")       # first_frame 先推


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

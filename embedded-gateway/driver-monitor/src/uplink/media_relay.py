#!/usr/bin/env python3
"""板子→代理 的媒体证据 hop —— 采集机(无外网)把关键帧经本地网络推给有网代理,代理跑 MediaOutbox 传 OSS。

为什么分这一跳:采集板对公网无路由(安全气隙/物理隔离),egress 必须发生在够得着公网的节点。
链路:
  板子截帧 → MediaRelayClient.ship() ──本地 HTTP──▶ 代理 MediaReceiver.on_post()
          → MediaOutbox.enqueue() ──公网──▶ OSS(代理侧持凭证)

- 线格式 MediaShipment:元数据走 HTTP 头(X-Media-*),PNG 字节走 body(不 base64,省带宽)。
- 板子侧 ship() 离线容忍:代理不可达返回 False,由板子侧留存重试(spool 为后续项;可复用
  MediaOutbox 包一层做板→代理的存储转发)。
- key 确定性:板子能预算最终 OSS URL,无需等上传完成即可回填 envelope.thumbnail_ref。
- 纯标准库;解析/入队/请求构造均抽成纯函数,可离线单测;serve/pump 为薄 glue。
"""
from __future__ import annotations

from dataclasses import dataclass


def _ci_get(headers, name: str, default=None):
    """大小写不敏感取 header,兼容普通 dict 与 http.server 的 Message。"""
    v = headers.get(name)
    if v is not None:
        return v
    if hasattr(headers, "items"):
        low = name.lower()
        for k, val in headers.items():
            if k.lower() == low:
                return val
    return default


@dataclass(frozen=True)
class MediaShipment:
    """板子发给代理的一份证据:元数据 + PNG 字节。"""
    key: str
    kind: str
    occurred_at: float
    event_id: str
    data: bytes
    content_type: str = "image/png"

    def to_http(self) -> tuple[dict, bytes]:
        headers = {
            "X-Media-Key": self.key,
            "X-Media-Kind": self.kind,
            "X-Media-Occurred-At": repr(self.occurred_at),
            "X-Media-Event-Id": self.event_id,
            "Content-Type": self.content_type,
            "Content-Length": str(len(self.data)),
        }
        return headers, self.data

    @classmethod
    def from_http(cls, headers, body: bytes) -> "MediaShipment":
        key = _ci_get(headers, "X-Media-Key")
        if not key:
            raise ValueError("missing X-Media-Key")
        return cls(
            key=key,
            kind=_ci_get(headers, "X-Media-Kind", "frame"),
            occurred_at=float(_ci_get(headers, "X-Media-Occurred-At", "0") or 0.0),
            event_id=_ci_get(headers, "X-Media-Event-Id", "") or "",
            data=body,
            content_type=_ci_get(headers, "Content-Type", "image/png"),
        )


class MediaRelayClient:
    """板子侧:把一份证据 POST 给代理。ship() 返回是否已交给代理(离线返回 False,留给上层重试)。"""

    def __init__(self, host: str, port: int, *, path: str = "/media",
                 secure: bool = False, timeout_s: float = 5.0):
        self.host = host
        self.port = port
        self.path = path
        self.secure = secure
        self.timeout_s = timeout_s

    def _build_request(self, shipment: MediaShipment) -> tuple[str, str, dict, bytes]:
        headers, body = shipment.to_http()
        return "POST", self.path, headers, body

    def ship(self, shipment: MediaShipment) -> bool:
        import http.client
        _, path, headers, body = self._build_request(shipment)
        try:
            conn = (http.client.HTTPSConnection if self.secure
                    else http.client.HTTPConnection)(
                self.host, self.port, timeout=self.timeout_s)
            try:
                conn.request("POST", path, body=body, headers=headers)
                resp = conn.getresponse()
                resp.read()
                return 200 <= resp.status < 300
            finally:
                conn.close()
        except OSError:
            return False                                # 代理不可达 → 板子侧留存重试


class RelayUploader:
    """把 MediaRelayClient 适配成 MediaOutbox 的 sink —— 让"板子侧 spool"直接复用 MediaOutbox。

    板子:MediaOutbox(RelayUploader(...)).enqueue() → pump 时 put_media() 经 relay 推代理:
      ship 成功 → 返回板子预算的确定性 OSS URL(on_uploaded 据此回填 thumbnail_ref);
      代理不可达 → None → MediaOutbox 留队重试(板子侧存储转发,证据不丢)。
    url_for:key→最终 OSS URL 的函数(非秘密,endpoint+bucket 即可算,见 oss_media.oss_object_url)。
    """

    def __init__(self, relay: MediaRelayClient, url_for):
        self.relay = relay
        self._url_for = url_for

    def object_url(self, key: str) -> str:
        return self._url_for(key)

    def put_media(self, key: str, data: bytes, content_type: str,
                  kind: str, occurred_at: float, ref) -> str | None:
        ok = self.relay.ship(MediaShipment(
            key, kind, occurred_at, ref or "", data, content_type))
        return self._url_for(key) if ok else None


class MediaReceiver:
    """代理侧:收下 POST 的证据,入 MediaOutbox(由 pump 循环异步传 OSS)。"""

    def __init__(self, outbox, *, path: str = "/media"):
        self.outbox = outbox
        self.path = path

    def on_post(self, headers, body: bytes, now: float) -> tuple[int, list]:
        try:
            s = MediaShipment.from_http(headers, body)
        except (ValueError, TypeError):
            return 400, []
        health = self.outbox.enqueue(
            s.key, s.data, s.kind, occurred_at=s.occurred_at, now=now,
            content_type=s.content_type, ref=s.event_id)
        return 200, health


# ---- 薄 glue(非单测;demo/部署用) ----

def build_agent_server(receiver: MediaReceiver, host: str = "0.0.0.0",
                       port: int = 8890, *, lock=None, clock=None):
    """建代理 HTTP 服务(收证据入队)。返回 (httpd, lock);调用方另起 pump 线程。"""
    import http.server
    import threading
    import time
    lock = lock or threading.Lock()
    clock = clock or time.time

    class _H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path.split("?", 1)[0] != receiver.path:
                self.send_response(404)
                self.end_headers()
                return
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length)
            with lock:
                status, _ = receiver.on_post(self.headers, body, clock())
            self.send_response(status)
            self.end_headers()

        def log_message(self, *a):                      # 静音访问日志
            pass

    httpd = http.server.ThreadingHTTPServer((host, port), _H)
    return httpd, lock


def run_pump_loop(outbox, lock, *, clock=None, interval_s: float = 2.0, stop=None) -> None:
    """代理侧 pump 循环:定期把队列里的证据推 OSS。与收包共用锁(MediaOutbox 非线程安全)。"""
    import time
    clock = clock or time.time
    while stop is None or not stop.is_set():
        time.sleep(interval_s)
        with lock:
            outbox.pump(clock())

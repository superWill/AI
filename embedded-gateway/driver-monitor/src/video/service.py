#!/usr/bin/env python3
"""BL410(RK3568)视频工具服务 —— 把"视频"整块收到这块板,对外一个纯标准库 HTTP API。

架构:RK3506 只做控制/热能;所有视频(拉流/抓帧/直播/看懂)统一在 RK3568。
本服务把视频暴露成 agent/值守可调的工具,RK3506 或平台按需 HTTP 调:
  POST /snapshot  抓相机帧 → MediaOutbox(RelayUploader→lobster agent→OSS) → 返预算 URL+key
  GET  /live      返 go2rtc 直播 URL(html/hls/mp4/webrtc)——go2rtc 已在本板,passthrough 不转码
  POST /analyze   抓帧 → VisionAnalyzer(RKNN;当前留桩)→ 结构化视觉结论
  GET  /health    相机/积压/analyzer 自检,不静默

板子无外网:OSS egress 仍走 agent 一跳(board→lobster media_agent→OSS,已固化)。抓帧走
雄迈 webcapture.jpg(不解码,RK3568 也不用 MPP 出静态图)。纯标准库 py3.8;handler 抽成纯方法
(注入 grabber/outbox/analyzer),可离线单测;HTTP/pump 为薄 glue。
"""
from __future__ import annotations

import json

from uplink.oss_media import event_media_key


class VideoToolService:
    """视频工具:四个纯 handler,各返回 (status:int, body:dict)。注入依赖,零 I/O 于构造。"""

    def __init__(self, grabber, outbox, analyzer, url_for, *,
                 go2rtc_base: str, default_cam: str = "cam",
                 prefix: str = "driver-monitor", clock=None):
        import time
        self.grabber = grabber                       # SnapshotSource:grab()->bytes|None
        self.outbox = outbox                         # MediaOutbox(RelayUploader sink)
        self.analyzer = analyzer                     # VisionAnalyzer
        self._url_for = url_for                      # key -> 最终 OSS URL(预算,非秘密)
        self.go2rtc_base = go2rtc_base.rstrip("/")
        self.default_cam = default_cam
        self.prefix = prefix
        self._clock = clock or time.time

    # ---- POST /snapshot:抓帧 → 入队 ship → 返预算 URL ----
    def snapshot(self, *, event_id=None, cam=None, kind="frame", now=None):
        cam = cam or self.default_cam
        now = self._clock() if now is None else now
        jpeg = self.grabber.grab()
        if jpeg is None:                             # 相机不可达 → 不静默,报 503
            return 503, {"ok": False, "error": "snapshot_failed",
                         "detail": "相机不可达或返回非JPEG", "cam": cam}
        event_id = event_id or f"snap-{cam}-{int(now)}"
        kind = kind if kind in ("frame", "first_frame") else "frame"
        key = event_media_key(self.prefix, event_id, "snapshot", ext="jpg")
        self.outbox.enqueue(key, jpeg, kind, occurred_at=now, now=now,
                            content_type="image/jpeg", ref=event_id)
        self.outbox.pump(now)                        # 尽力即时 ship;失败留队重试(存储转发)
        return 200, {"ok": True, "cam": cam, "event_id": event_id, "key": key,
                     "url": self._url_for(key), "bytes": len(jpeg),
                     "kind": kind, "state": self.outbox.state_of(key)}

    # ---- GET /live:返 go2rtc 直播 URL(按需连,没人看不推流) ----
    def live(self, *, cam=None):
        cam = cam or self.default_cam
        b = self.go2rtc_base
        return 200, {"ok": True, "cam": cam, "urls": {
            "html": f"{b}/stream.html?src={cam}",     # 浏览器自适应(安卓 MSE)
            "hls": f"{b}/api/stream.m3u8?src={cam}",   # iOS Safari 原生
            "mp4": f"{b}/api/stream.mp4?src={cam}",    # 兜底
            "webrtc": f"{b}/api/ws?src={cam}",         # 低延迟(同网可用)
        }}

    # ---- POST /analyze:抓帧 → 视觉推理(RKNN 留桩) ----
    def analyze(self, *, cam=None, now=None):
        cam = cam or self.default_cam
        jpeg = self.grabber.grab()
        if jpeg is None:
            return 503, {"ok": False, "error": "snapshot_failed", "cam": cam}
        result = self.analyzer.analyze(jpeg, ref=cam)
        return 200, {"ok": True, "cam": cam, "bytes": len(jpeg),
                     "result": result.to_dict()}

    # ---- GET /health:相机/积压/analyzer 自检(相机不可达 → 503) ----
    def health(self, *, now=None):
        now = self._clock() if now is None else now
        jpeg = self.grabber.grab()                   # 真探一次:相机可达是关键健康信号
        cam_ok = jpeg is not None
        return (200 if cam_ok else 503), {
            "ok": cam_ok, "camera_ok": cam_ok,
            "snapshot_bytes": len(jpeg) if jpeg else 0,
            "outbox_pending": self.outbox.pending_count,
            "analyzer": self.analyzer.model,
            "go2rtc_base": self.go2rtc_base,
            "ts": round(now, 3),
        }


# ---- 薄 glue(非单测;部署用) ----

def build_http_server(service: VideoToolService, host: str = "0.0.0.0",
                      port: int = 8891, *, lock=None, clock=None):
    """建视频工具 HTTP 服务。outbox 非线程安全 → handler 与 pump 共用 lock。返回 (httpd, lock)。"""
    import http.server
    import threading
    import time
    import urllib.parse
    lock = lock or threading.Lock()
    clock = clock or time.time

    class _H(http.server.BaseHTTPRequestHandler):
        def _dispatch(self, method: str) -> None:
            parsed = urllib.parse.urlsplit(self.path)
            path = parsed.path.rstrip("/") or "/"
            q = {k: v[0] for k, v in urllib.parse.parse_qs(parsed.query).items()}
            now = clock()
            with lock:
                if method == "GET" and path == "/live":
                    status, body = service.live(cam=q.get("cam"))
                elif method == "GET" and path == "/health":
                    status, body = service.health(now=now)
                elif method == "POST" and path == "/snapshot":
                    status, body = service.snapshot(
                        event_id=q.get("event_id"), cam=q.get("cam"),
                        kind=q.get("kind", "frame"), now=now)
                elif method == "POST" and path == "/analyze":
                    status, body = service.analyze(cam=q.get("cam"), now=now)
                else:
                    status, body = 404, {"ok": False, "error": "not_found", "path": path}
            payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            self._dispatch("GET")

        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)               # 参数走 query,body 排空即可
            self._dispatch("POST")

        def log_message(self, *a):                    # 静音访问日志
            pass

    httpd = http.server.ThreadingHTTPServer((host, port), _H)
    return httpd, lock


def run_pump_loop(outbox, lock, *, clock=None, interval_s: float = 2.0, stop=None) -> None:
    """后台 pump:定期把队列里的帧推向 agent(→OSS)。与 handler 共用锁(outbox 非线程安全)。"""
    import time
    clock = clock or time.time
    while stop is None or not stop.is_set():
        time.sleep(interval_s)
        with lock:
            outbox.pump(clock())

#!/usr/bin/env python3
"""摄像头快照抓取 —— 从相机 HTTP JPEG 接口 GET 一张图，不解码（RK3506 无 VPU 也能用）。

雄迈 .217 实测接口：`http://<ip>/webcapture.jpg?command=snap&channel=0`（HTTP Basic admin:）。
RK3506 报警时调 grab() 拿 JPEG 字节，直接 ship 上云，全程不解视频。
- 离线容忍：网络/相机不可达返回 None（上层不入队、发健康告警）。
- 校验 JPEG 魔数（ffd8ff），非图片返回 None（防把错误页当图上传）。
- 纯标准库；FakeSnapshotGrabber 供离线单测/无相机联调。
"""
from __future__ import annotations

import abc
import base64
from dataclasses import dataclass


class SnapshotSource(abc.ABC):
    @abc.abstractmethod
    def grab(self) -> bytes | None:
        """抓一张 JPEG。成功返回字节；失败/离线返回 None。"""


@dataclass
class SnapshotConfig:
    url: str                       # 完整快照 URL(含 query),如 http://ip/webcapture.jpg?command=snap&channel=0
    username: str = ""
    password: str = ""
    timeout_s: float = 6.0


def _is_jpeg(data: bytes) -> bool:
    return len(data) >= 3 and data[:3] == b"\xff\xd8\xff"


class HttpSnapshotGrabber(SnapshotSource):
    def __init__(self, config: SnapshotConfig):
        self.c = config

    def _build_request(self):
        """解析 URL + 组 Basic Auth 头。抽出供单测,不发网络。返回 (host,port,path,headers,secure)。"""
        import urllib.parse
        u = urllib.parse.urlsplit(self.c.url)
        secure = u.scheme == "https"
        port = u.port or (443 if secure else 80)
        path = u.path + (("?" + u.query) if u.query else "")
        headers = {"Host": u.hostname or ""}
        if self.c.username or self.c.password:
            token = base64.b64encode(f"{self.c.username}:{self.c.password}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        return u.hostname, port, path or "/", headers, secure

    def grab(self) -> bytes | None:
        import http.client
        host, port, path, headers, secure = self._build_request()
        try:
            conn = (http.client.HTTPSConnection if secure
                    else http.client.HTTPConnection)(host, port, timeout=self.c.timeout_s)
            try:
                conn.request("GET", path, headers=headers)
                resp = conn.getresponse()
                body = resp.read()
                if 200 <= resp.status < 300 and _is_jpeg(body):
                    return body
                return None                        # 4xx/5xx 或非 JPEG(错误页) → 视为抓图失败
            finally:
                conn.close()
        except OSError:
            return None                            # 断网/超时/相机离线


class FakeSnapshotGrabber(SnapshotSource):
    """离线桩:返回固定 JPEG 字节;online=False 模拟相机不可达。"""

    def __init__(self, jpeg: bytes = b"\xff\xd8\xff\xe0canned-jpeg", online: bool = True):
        self.jpeg = jpeg
        self.online = online
        self.grab_count = 0

    def grab(self) -> bytes | None:
        self.grab_count += 1
        return self.jpeg if self.online else None

#!/usr/bin/env python3
"""RTSP H.264/265 取流 → MPP 硬解 → numpy 帧。BL412B(RK3568J)专用,零 OpenCV/ffmpeg 依赖。

板子上**没有 ffmpeg/opencv**,但 GStreamer 1.18 带 `mppvideodec`(Rockchip 硬解)。本模块用
`rtspsrc ! depay ! parse ! mppvideodec ! videoconvert ! appsink` 把 H.265 解到内存,经 appsink
逐帧 pull 成 numpy(H,W,3) RGB,喂给 vision-worker。

设计:
- **解码与上层解耦**:`read()` 返回 (ts, frame) 或 None(超时/暂无帧);上层自己决定怎么用。
- **单调时间戳**:用 `time.monotonic()` 打帧到达时刻(供状态机时间窗),不依赖流内 PTS。
- **断流自愈**:pipeline 出错/EOS → 标记 stale,`read()` 返回 None;上层据此进 CAMERA_FAULT,
  并可调 `restart()` 重连。GStreamer 内部对 rtspsrc 也会做重连尝试。
- **不打印密码**:URL 里的密码只存在对象内,日志一律打码。
"""
from __future__ import annotations

import re
import threading
import time
from typing import Optional, Tuple

import numpy as np

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib  # noqa: E402

Gst.init(None)

Frame = Tuple[float, "np.ndarray"]   # (monotonic_ts, HxWx3 uint8 RGB)


def redact(url: str) -> str:
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", url)


class GstRtspSource:
    """单路 RTSP H.265 → RGB numpy 帧源。线程安全的最新帧获取。"""

    def __init__(self, url: str, *, codec: str = "h265", latency_ms: int = 200,
                 width: Optional[int] = None, height: Optional[int] = None,
                 drop: bool = True):
        self.url = url
        self.codec = codec
        self.latency_ms = latency_ms
        self.req_w = width
        self.req_h = height
        self.drop = drop

        self._pipeline: Optional[Gst.Pipeline] = None
        self._appsink: Optional[Gst.Element] = None
        self._loop_thread: Optional[threading.Thread] = None
        self._glib_loop: Optional[GLib.MainLoop] = None

        self._lock = threading.Lock()
        self._latest: Optional[Frame] = None
        self._width = width or 0
        self._height = height or 0
        self._frame_count = 0
        self._error: Optional[str] = None
        self._eos = False

    # ---- pipeline 构造 ----
    def _build_desc(self) -> str:
        depay = "rtph265depay" if self.codec == "h265" else "rtph264depay"
        parse = "h265parse" if self.codec == "h265" else "h264parse"
        # 可选缩放:videoscale 在 videoconvert 后,降到模型输入尺寸,省 CPU/带宽。
        # add-borders=true → letterbox(保持长宽比、补边),直接喂检测模型,免去板上 numpy resize。
        scale = ""
        caps = "video/x-raw,format=RGB"
        if self.req_w and self.req_h:
            scale = "videoscale add-borders=true ! "
            caps = f"video/x-raw,format=RGB,width={self.req_w},height={self.req_h}"
        return (
            f"rtspsrc location=\"{self.url}\" protocols=tcp latency={self.latency_ms} "
            f"name=src ! {depay} ! {parse} ! mppvideodec ! videoconvert ! {scale}"
            f"{caps} ! appsink name=sink emit-signals=true sync=false "
            f"max-buffers=2 drop={'true' if self.drop else 'false'}"
        )

    def start(self) -> None:
        if self._pipeline is not None:
            return
        self._pipeline = Gst.parse_launch(self._build_desc())
        self._appsink = self._pipeline.get_by_name("sink")
        self._appsink.connect("new-sample", self._on_sample)

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._on_bus)

        self._glib_loop = GLib.MainLoop()
        self._loop_thread = threading.Thread(target=self._glib_loop.run, daemon=True)
        self._loop_thread.start()
        self._pipeline.set_state(Gst.State.PLAYING)

    def _on_sample(self, sink) -> int:
        sample = sink.emit("pull-sample")
        if sample is None:
            return Gst.FlowReturn.OK
        buf = sample.get_buffer()
        caps = sample.get_caps().get_structure(0)
        w = caps.get_value("width")
        h = caps.get_value("height")
        ok, mapinfo = buf.map(Gst.MapFlags.READ)
        if not ok:
            return Gst.FlowReturn.OK
        try:
            # RGB packed:每像素 3 字节。GStreamer 行对齐通常按 4 字节,RGB 24bpp 一般无 padding,
            # 但保险起见按 buffer 实际大小判定是否有 stride padding。
            expected = w * h * 3
            if mapinfo.size >= expected:
                arr = np.frombuffer(mapinfo.data[:expected], dtype=np.uint8).reshape(h, w, 3)
                frame = arr.copy()   # 脱离 mapinfo 生命周期
                with self._lock:
                    self._latest = (time.monotonic(), frame)
                    self._width, self._height = w, h
                    self._frame_count += 1
        finally:
            buf.unmap(mapinfo)
        return Gst.FlowReturn.OK

    def _on_bus(self, bus, message) -> None:
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, dbg = message.parse_error()
            with self._lock:
                self._error = f"{err.message}"
        elif t == Gst.MessageType.EOS:
            with self._lock:
                self._eos = True

    # ---- 对外 ----
    def read(self, *, timeout_s: float = 1.0, min_ts: float = 0.0) -> Optional[Frame]:
        """取最新帧。等到有一帧比 min_ts 更新或超时。无新帧返回 None。"""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            with self._lock:
                f = self._latest
                if f is not None and f[0] > min_ts:
                    return f
            time.sleep(0.005)
        return None

    @property
    def size(self) -> Tuple[int, int]:
        with self._lock:
            return self._width, self._height

    @property
    def frame_count(self) -> int:
        with self._lock:
            return self._frame_count

    @property
    def error(self) -> Optional[str]:
        with self._lock:
            return self._error or ("eos" if self._eos else None)

    def stop(self) -> None:
        if self._pipeline is not None:
            self._pipeline.set_state(Gst.State.NULL)
            self._pipeline = None
        if self._glib_loop is not None:
            self._glib_loop.quit()
            self._glib_loop = None

    def restart(self) -> None:
        self.stop()
        with self._lock:
            self._latest = None
            self._error = None
            self._eos = False
        self.start()

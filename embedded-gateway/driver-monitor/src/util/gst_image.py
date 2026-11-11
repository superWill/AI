#!/usr/bin/env python3
"""用 GStreamer 解码静态图片(jpeg/png)→ RGB numpy。板上无 cv2/PIL,调试/验证用。"""
from __future__ import annotations

import numpy as np

import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst  # noqa: E402

Gst.init(None)


def load_image_rgb(path: str, timeout_s: float = 5.0):
    """filesrc ! decodebin ! videoconvert ! RGB ! appsink,拉一帧返回 (H,W,3) uint8。"""
    desc = (f'filesrc location="{path}" ! decodebin ! videoconvert ! '
            f'video/x-raw,format=RGB ! appsink name=s sync=false max-buffers=1')
    pipe = Gst.parse_launch(desc)
    sink = pipe.get_by_name("s")
    pipe.set_state(Gst.State.PLAYING)
    try:
        sample = sink.emit("try-pull-sample", int(timeout_s * Gst.SECOND))
        if sample is None:
            return None
        buf = sample.get_buffer()
        caps = sample.get_caps().get_structure(0)
        w = caps.get_value("width"); h = caps.get_value("height")
        ok, mi = buf.map(Gst.MapFlags.READ)
        if not ok:
            return None
        try:
            arr = np.frombuffer(mi.data[:w * h * 3], dtype=np.uint8).reshape(h, w, 3).copy()
        finally:
            buf.unmap(mi)
        return arr
    finally:
        pipe.set_state(Gst.State.NULL)

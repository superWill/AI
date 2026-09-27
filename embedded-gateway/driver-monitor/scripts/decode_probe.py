#!/usr/bin/env python3
"""P1 解码取证 —— 在 BL412B 上跑:用 GStreamer MPP 硬解真实 RTSP 流,验证解码链路、
量真实分辨率/帧率,并可存一帧做肉眼核对。替代 ffprobe(板子无 ffmpeg)。

  export CAM_RTSP='rtsp://admin:@192.168.1.217:554/user=admin&password=&channel=1&stream=0.sdp'
  python3 scripts/decode_probe.py --seconds 5 --save /tmp/frame.npy
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from camera.gst_source import GstRtspSource, redact   # noqa: E402

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"))
    ap.add_argument("--codec", default="h265", choices=["h264", "h265"])
    ap.add_argument("--seconds", type=float, default=5.0)
    ap.add_argument("--save", default="", help="把最后一帧存成 .npy(肉眼/离线核对)")
    args = ap.parse_args()
    if not args.url:
        print("缺 RTSP URL:--url 或 export CAM_RTSP=...", file=sys.stderr)
        return 2

    print(f"[decode] {redact(args.url)} codec={args.codec} 测 {args.seconds}s …", flush=True)
    src = GstRtspSource(args.url, codec=args.codec)
    t0 = time.monotonic()
    src.start()

    # 等首帧
    first = src.read(timeout_s=10.0)
    if first is None:
        print(f"[decode] 10s 内无帧。error={src.error}", file=sys.stderr)
        src.stop()
        return 1
    first_latency = time.monotonic() - t0
    w, h = src.size
    print(f"[decode] 首帧 {w}x{h} dtype={first[1].dtype} 用时 {first_latency:.2f}s", flush=True)

    # 计实测 fps
    start_n = src.frame_count
    end = time.monotonic() + args.seconds
    last_frame = first[1]
    last_ts = first[0]
    while time.monotonic() < end:
        f = src.read(timeout_s=1.0, min_ts=last_ts)
        if f is not None:
            last_ts, last_frame = f
        if src.error:
            print(f"[decode] 流错误: {src.error}", file=sys.stderr)
            break
    n = src.frame_count - start_n
    fps = n / args.seconds
    print(f"[decode] {args.seconds}s 收 {n} 帧 → ~{fps:.1f} fps  尺寸 {src.size}", flush=True)

    if args.save:
        np.save(args.save, last_frame)
        # 同时存一个均值,便于判断不是全黑/全白
        print(f"[decode] 存帧 → {args.save}  mean={last_frame.mean():.1f} "
              f"min={last_frame.min()} max={last_frame.max()}", flush=True)

    src.stop()
    return 0 if n > 0 else 1


if __name__ == "__main__":
    sys.exit(main())

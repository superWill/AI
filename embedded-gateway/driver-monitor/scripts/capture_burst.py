#!/usr/bin/env python3
"""连续采一段 RTSP 帧序列存 PNG —— 给 #8 当 EAR 标定/关键点验证素材(睁眼/闭眼)。
板上无 cv2/PIL,用纯 stdlib PNG 编码。每帧文件名带相对秒,便于事后按「前睁后闭」切分。

  export CAM_RTSP='rtsp://admin:@192.168.1.217:554/...stream=1.sdp'
  python3 scripts/capture_burst.py --dir /tmp/cal --seconds 30 --interval 0.5
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camera.gst_source import GstRtspSource, redact          # noqa: E402
from util.png_writer import write_png                        # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"))
    ap.add_argument("--codec", default="h265", choices=["h264", "h265"])
    ap.add_argument("--dir", default="/tmp/cal")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--interval", type=float, default=0.5)
    args = ap.parse_args()
    if not args.url:
        print("缺 RTSP URL", file=sys.stderr)
        return 2
    os.makedirs(args.dir, exist_ok=True)

    print(f"[cap] {redact(args.url)} → {args.dir}  {args.seconds}s @ {1/args.interval:.0f}fps", flush=True)
    s = GstRtspSource(args.url, codec=args.codec)
    s.start()
    if s.read(timeout_s=12.0) is None:
        print(f"[cap] 无帧: {s.error}", file=sys.stderr); s.stop(); return 1

    t0 = time.monotonic()
    n = 0
    last_ts = 0.0
    half = args.seconds / 2.0
    announced = False
    while time.monotonic() - t0 < args.seconds:
        rel = time.monotonic() - t0
        if rel >= half and not announced:
            print(f"  >>> {rel:.0f}s:现在请【闭眼】<<<", flush=True); announced = True
        f = s.read(timeout_s=1.0, min_ts=last_ts)
        if f is None:
            continue
        last_ts, frame = f
        phase = "open" if rel < half else "closed"
        path = os.path.join(args.dir, f"f_{rel:05.1f}s_{phase}.png")
        write_png(path, frame)
        n += 1
        time.sleep(args.interval)
    s.stop()
    print(f"[cap] 完成:{n} 帧存于 {args.dir}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

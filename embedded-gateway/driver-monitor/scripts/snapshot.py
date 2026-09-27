#!/usr/bin/env python3
"""抓一帧 RTSP → 标注 → 存 PNG。板上无 cv2/PIL,用纯 stdlib 编码器。
用于验证存证截图链,也可当采图工具。

  export CAM_RTSP='rtsp://admin:@192.168.1.217:554/user=admin&password=&channel=1&stream=1.sdp'
  python3 scripts/snapshot.py --out /tmp/cam.png
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camera.gst_source import GstRtspSource, redact          # noqa: E402
from util.png_writer import write_png, draw_box, draw_border  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"))
    ap.add_argument("--codec", default="h265", choices=["h264", "h265"])
    ap.add_argument("--out", default="/tmp/cam.png")
    ap.add_argument("--timeout", type=float, default=12.0)
    ap.add_argument("--annotate", action="store_true", help="画中央框+红边(模拟存证标注)")
    args = ap.parse_args()
    if not args.url:
        print("缺 RTSP URL:--url 或 export CAM_RTSP=...", file=sys.stderr)
        return 2

    print(f"[snap] {redact(args.url)} …", flush=True)
    s = GstRtspSource(args.url, codec=args.codec)
    s.start()
    f = s.read(timeout_s=args.timeout)
    if f is None:
        print(f"[snap] 无帧: {s.error}", file=sys.stderr)
        s.stop()
        return 1
    ts, frame = f
    h, w = frame.shape[:2]
    print(f"[snap] 帧 {w}x{h} mean={frame.mean():.1f}", flush=True)
    if args.annotate:
        draw_box(frame, w // 4, h // 4, w * 3 // 4, h * 3 // 4, (0, 255, 0), 3)
        draw_border(frame, (220, 0, 0), 6)
    write_png(args.out, frame)
    s.stop()
    print(f"[snap] 存 {args.out} ({os.path.getsize(args.out)} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

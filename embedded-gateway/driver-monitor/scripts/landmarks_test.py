#!/usr/bin/env python3
"""#8 验证:真帧 → RetinaFace → PFLD98 → EAR/MAR,叠 98 点存 PNG。
自带模型自验,不需要谁出镜。

  export CAM_RTSP='rtsp://admin:@192.168.1.217:554/...stream=1.sdp'
  python3 scripts/landmarks_test.py --retina models/RetinaFace_mobile320.rknn \
      --pfld models/pfld_landmark_rk3568.rknn --out /tmp/lm.png
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np                                          # noqa: E402
from camera.gst_source import GstRtspSource, redact         # noqa: E402
from vision.pipeline import FacePipeline                    # noqa: E402
from vision.pfld import LEFT_EYE, RIGHT_EYE, INNER_LIP      # noqa: E402
from util.png_writer import write_png, draw_box, draw_points  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"))
    ap.add_argument("--codec", default="h265")
    ap.add_argument("--retina", default="models/RetinaFace_mobile320.rknn")
    ap.add_argument("--pfld", default="models/pfld_landmark_rk3568.rknn")
    ap.add_argument("--out", default="/tmp/lm.png")
    ap.add_argument("--image", default="", help="用本地 .npy 帧替代取流(调试)")
    ap.add_argument("--jpeg", default="", help="用 jpeg/png 文件替代取流(GStreamer 解码)")
    args = ap.parse_args()

    if args.jpeg:
        from util.gst_image import load_image_rgb
        frame = load_image_rgb(args.jpeg)
        if frame is None:
            print(f"[lm] 解码失败 {args.jpeg}", file=sys.stderr); return 1
    elif args.image:
        frame = np.load(args.image)
    else:
        if not args.url:
            print("缺 CAM_RTSP", file=sys.stderr); return 2
        s = GstRtspSource(args.url, codec=args.codec); s.start()
        f = s.read(timeout_s=12.0)
        if f is None:
            print(f"无帧 {s.error}", file=sys.stderr); s.stop(); return 1
        _, frame = f; s.stop()
    print(f"[lm] frame {frame.shape}", flush=True)

    pipe = FacePipeline(args.retina, args.pfld)
    r = pipe.process(frame)
    pipe.release()
    if r is None:
        print("[lm] 未检出人脸", flush=True)
        write_png(args.out, frame)
        return 1

    bx = r["box"]; lm = r["landmarks98"]
    print(f"[lm] 人脸 score={r['score']:.2f} box=({bx[0]:.0f},{bx[1]:.0f},{bx[2]:.0f},{bx[3]:.0f})", flush=True)
    print(f"[lm] EAR={r['ear']:.3f}  MAR={r['mar']:.3f}  (睁眼 EAR~0.25-0.35, 闭眼<0.18)", flush=True)

    # 叠图:框 + 全 98 点(白) + 眼(绿) + 内唇(红),便于肉眼核对索引对不对
    draw_box(frame, bx[0], bx[1], bx[2], bx[3], (0, 255, 0), 2)
    draw_points(frame, lm, (255, 255, 255), 1)
    draw_points(frame, lm[LEFT_EYE + RIGHT_EYE], (0, 255, 0), 2)
    draw_points(frame, lm[INNER_LIP], (255, 0, 0), 2)
    write_png(args.out, frame)
    print(f"[lm] 存 {args.out} ({os.path.getsize(args.out)} bytes)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

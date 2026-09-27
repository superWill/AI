#!/usr/bin/env python3
"""整链实时跑通 —— BL412B 上:摄像头 RTSP → MPP 硬解 → RetinaFace(NPU)→ 头姿特征 →
疲劳状态机 → 事件落地。这是 driver-monitor 的端到端入口。

Path A(RetinaFace 5 点):只产出头姿(看别处/低头)信号驱动状态机;EAR/MAR 需稠密关键点,
后续换稠密模型再补(见 README 阶段进度)。本脚本证明 **整条链路在板上闭环**。

  export CAM_RTSP='rtsp://admin:@192.168.1.217:554/user=admin&password=&channel=1&stream=1.sdp'
  python3 scripts/run_live.py --model models/RetinaFace_mobile320.rknn --seconds 30
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np   # noqa: E402

from datetime import datetime                                # noqa: E402

from camera.gst_source import GstRtspSource, redact          # noqa: E402
from vision.retinaface import RetinaFaceRKNN, head_pose_points  # noqa: E402
from vision.features import head_pose_2d                      # noqa: E402
from drowsiness.engine import (DrowsinessEngine, DrowsinessConfig,  # noqa: E402
                               FrameObservation, State)
from event.adapter import EventAdapter, CallableSink, JsonlLogSink  # noqa: E402
from util.png_writer import write_png, draw_box, draw_points, draw_border  # noqa: E402

# 疲劳事件存证:状态 → 边框色(BGR? 不,RGB)
_EVIDENCE_STATES = {State.ALARM: (220, 0, 0), State.WARNING: (255, 140, 0)}


def save_evidence(evidence_dir, frame, face, ev) -> str:
    """把触发疲劳事件的当前帧标注后存成 PNG(板上无 cv2/PIL,用纯 stdlib 编码器)。"""
    img = frame.copy()
    if face is not None:
        bx = face.get("box")
        if bx:
            draw_box(img, bx[0], bx[1], bx[2], bx[3], (0, 255, 0), 2)
        lm = face.get("landmarks")
        if lm is not None:
            draw_points(img, lm, (255, 0, 0), 2)
    draw_border(img, _EVIDENCE_STATES.get(ev["state"], (255, 255, 0)), 6)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"evt_{stamp}_{ev['state']}_{ev.get('event_kind','')}.png"
    path = os.path.join(evidence_dir, name)
    write_png(path, img)
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"))
    ap.add_argument("--codec", default="h265", choices=["h264", "h265"])
    ap.add_argument("--model", required=True, help="RetinaFace .rknn 路径")
    ap.add_argument("--size", type=int, default=320, help="模型输入边长(letterbox 方形)")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--events-log", default="", help="事件 JSONL 落盘路径(可选)")
    ap.add_argument("--evidence-dir", default="", help="疲劳事件存证截图目录(空=不存)")
    ap.add_argument("--verbose", action="store_true", help="每帧打印特征(调试)")
    args = ap.parse_args()
    if args.evidence_dir:
        os.makedirs(args.evidence_dir, exist_ok=True)
    if not args.url:
        print("缺 RTSP URL:--url 或 export CAM_RTSP=...", file=sys.stderr)
        return 2

    print(f"[run] 模型 {args.model}", flush=True)
    det = RetinaFaceRKNN(args.model, model_size=(args.size, args.size))
    engine = DrowsinessEngine(DrowsinessConfig(model_version="retinaface_mobile320"))

    def _print_event(ev: dict) -> None:
        print(f"[event:{ev.get('event_kind')}] {ev['state']} reason={ev['reason']} "
              f"perclos={ev['perclos']} eye_closed_s={ev['eye_closed_s']}", flush=True)

    sinks = [CallableSink(_print_event)]
    if args.events_log:
        sinks.append(JsonlLogSink(args.events_log))
    adapter = EventAdapter(sinks=sinks)

    print(f"[run] 取流 {redact(args.url)} → letterbox {args.size}x{args.size}", flush=True)
    src = GstRtspSource(args.url, codec=args.codec, width=args.size, height=args.size)
    src.start()
    if src.read(timeout_s=10.0) is None:
        print(f"[run] 10s 无帧,放弃。error={src.error}", file=sys.stderr)
        src.stop(); return 1

    last_state = None
    last_ts = 0.0
    n_frames = n_faces = 0
    t_end = time.monotonic() + args.seconds
    try:
        while time.monotonic() < t_end:
            f = src.read(timeout_s=1.0, min_ts=last_ts)
            if f is None:
                # 无新帧:让状态机判摄像头停滞;有流错误则尝试重连(自愈)
                now = time.monotonic()
                res = engine.tick_no_frame(now, camera_online=(src.error is None))
                if res is not None:
                    adapter.on_result(res, now=now)
                if src.error is not None:
                    print(f"[stream] 错误 {src.error} → 重连", flush=True)
                    src.restart()
                    time.sleep(0.5)
                continue
            ts, frame = f
            last_ts = ts
            n_frames += 1

            # 推理异常必须收敛成 MODEL_FAULT,绝不能让整进程崩退
            try:
                face = det.infer(frame)
            except Exception as exc:                  # noqa: BLE001
                print(f"[infer] 异常 → MODEL_FAULT: {exc}", flush=True)
                res = engine.update(FrameObservation(ts=ts, face_present=False, infer_ok=False),
                                    now=ts)
                adapter.on_result(res, now=ts)
                if res.state != last_state:
                    print(f"[state] {last_state} → {res.state}", flush=True)
                    last_state = res.state
                continue
            if face is None:
                obs = FrameObservation(ts=ts, face_present=False)
            else:
                n_faces += 1
                nose, le, re, mc = head_pose_points(face["landmarks"])
                yaw, pitch = head_pose_2d(nose, le, re, mc)
                obs = FrameObservation(ts=ts, face_present=True, infer_ok=True,
                                       ear=None, mar=None, yaw=yaw, pitch=pitch,
                                       confidence=face["score"])
                if args.verbose:
                    print(f"  face score={face['score']:.2f} yaw={yaw:+.0f} pitch={pitch:+.0f}",
                          flush=True)
            res = engine.update(obs, now=ts)
            ev = adapter.on_result(res, now=ts)   # 去抖/重报/扇出由 adapter 负责;返回已发事件或 None
            # 疲劳事件(发出时)存证截图——复用 adapter 去抖/重报,不会逐帧刷盘
            if ev is not None and args.evidence_dir and ev["state"] in _EVIDENCE_STATES:
                p = save_evidence(args.evidence_dir, frame, face, ev)
                print(f"[evidence] {ev['state']} → 截图 {p}", flush=True)
            if res.state != last_state:
                print(f"[state] {last_state} → {res.state}", flush=True)
                last_state = res.state
    finally:
        src.stop()
        det.release()

    dur = args.seconds
    print(f"\n[run] 结束:{n_frames} 帧 / {n_faces} 帧有脸 / ~{n_frames/dur:.1f} fps "
          f"/ 检出率 {(100*n_faces/max(1,n_frames)):.0f}%", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

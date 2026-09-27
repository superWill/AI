#!/usr/bin/env python3
"""视觉安防 P0 实机入口 —— 摄像头 RTSP → MPP 硬解 → 运动检测 → episode → 事件/存证。

不需要模型 / 不用 NPU(P0 只做运动检测;人体确认是 P1)。一台 BL412 上:
  - 单摄:  export CAM_RTSP='rtsp://admin:@192.168.1.217:554/...'; python3 scripts/run_motion_live.py --seconds 60
  - 多摄:  python3 scripts/run_motion_live.py --cam front=rtsp://... --cam yard=rtsp://... --seconds 120

每路摄像头一根线程,**各自独立的背景模型 + episode 状态机**(场景不同,背景不能共享)。
一路 crash/停流不拖垮其它路(线程隔离 + 相机健康告警)。OPEN 事件存证 PNG(进场画面),
CLOSE/相机健康只落 JSONL(离场是空场,截图无意义)。

依赖 numpy(板上 apt install python3-numpy)。密码只走环境变量/参数,不写盘、日志打码。
"""
from __future__ import annotations

import argparse
import os
import sys
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camera.gst_source import GstRtspSource, redact              # noqa: E402
from motion.detector import MotionDetector, MotionConfig         # noqa: E402
from motion.episode import EpisodeStateMachine, EpisodeConfig    # noqa: E402
from motion.pipeline import MotionPipeline                       # noqa: E402
from event.adapter import JsonlLogSink                           # noqa: E402
from util.png_writer import write_png, draw_border               # noqa: E402


def _parse_cams(args) -> list[tuple[str, str]]:
    """归一化成 [(cam_id, url), ...]。--cam id=url 可重复;--url 为单摄兜底(id=cam0)。"""
    cams: list[tuple[str, str]] = []
    for spec in (args.cam or []):
        if "=" not in spec:
            raise SystemExit(f"--cam 需 id=url 形式,得到:{spec}")
        cid, url = spec.split("=", 1)
        cams.append((cid.strip(), url.strip()))
    if args.url:
        cams.append(("cam0", args.url))
    if not cams:
        raise SystemExit("未指定摄像头:用 --cam id=url(可多次)或 --url / CAM_RTSP")
    return cams


class Fanout:
    """线程安全事件扇出:控制台 + JSONL。多线程写不交错。"""
    def __init__(self, jsonl_path: str | None):
        self._lock = threading.Lock()
        self._sink = JsonlLogSink(jsonl_path) if jsonl_path else None

    def emit(self, ev: dict) -> None:
        with self._lock:
            self._print(ev)
            if self._sink:
                self._sink.emit(ev)

    def _print(self, ev: dict) -> None:
        cam = ev.get("cam_id", "?")
        t = ev.get("type")
        if t == "motion_episode" and ev["event_kind"] == "open":
            print(f"[{cam}] >>> OPEN  {ev['event_id']} ts_start={ev['ts_start']} "
                  f"motion={ev['motion_score']}")
        elif t == "motion_episode":
            print(f"[{cam}] <<< CLOSE {ev['event_id']} dur={ev['duration_s']}s "
                  f"peak={ev['peak_motion']} by={ev['closed_by']}")
        elif t == "camera_health":
            print(f"[{cam}] ~~~ CAMERA {ev['status'].upper()} @ ts={ev['ts']}")


def _worker(cam_id: str, url: str, codec: str, seconds: float,
            fan: Fanout, evidence_dir: str | None, cfg: MotionConfig,
            ep_cfg: EpisodeConfig, stop: threading.Event) -> None:
    src = GstRtspSource(url, codec=codec)
    pipe = MotionPipeline(cam_id, MotionDetector(cfg),
                          EpisodeStateMachine(ep_cfg), stale_after_s=2.0)
    print(f"[{cam_id}] 启动:{redact(url)} ({codec})")
    src.start()
    start = time.monotonic()
    pipe.mark_started(start)
    last_ts = 0.0
    last_restart = -1e9                          # 上次重连时刻(退避用;-inf → 首次立即)
    reconnect_backoff_s = 5.0
    try:
        while not stop.is_set() and time.monotonic() - start < seconds:
            f = src.read(timeout_s=0.5, min_ts=last_ts)
            now = time.monotonic()
            if f is None:                        # 无新帧:判停流 + 重连
                for ev in pipe.tick_no_frame(now):
                    fan.emit(ev)
                # 重连触发:①显式流错误(ERROR/EOS);②静默停流——TCP 连接还在但不再出帧,
                #   GStreamer 不一定立刻报 ERROR,src.error 仍为假,只能靠 stale 判(pipe.online=False)。
                #   带退避,避免每 0.5s 猛拉重连拖累 RK3568。
                if (src.error or not pipe.online) and now - last_restart >= reconnect_backoff_s:
                    print(f"[{cam_id}] 重连({src.error or 'silent_stall'})…")
                    src.restart()
                    last_restart = now
                continue
            ts, frame = f
            last_ts = ts
            for ev in pipe.process_frame(ts, frame):
                fan.emit(ev)
                if evidence_dir and ev.get("type") == "motion_episode" \
                        and ev["event_kind"] == "open":
                    _save_evidence(evidence_dir, cam_id, frame, ev)
    finally:
        # 收尾时若还有 ACTIVE episode,强制收尾——不留悬空 OPEN(和相机故障同理)
        forced = pipe.episode.force_close(time.monotonic(), "shutdown")
        if forced is not None:
            forced["cam_id"] = cam_id
            fan.emit(forced)
        src.stop()
        print(f"[{cam_id}] 停止(收到 {src.frame_count} 帧)")


def _save_evidence(evidence_dir: str, cam_id: str, frame, ev: dict) -> None:
    shot = frame.copy()
    draw_border(shot, (255, 0, 0), 6)            # 进场:红框
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    name = f"{cam_id}_{stamp}_{ev['event_id']}_open.png"
    write_png(os.path.join(evidence_dir, name), shot)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cam", action="append", help="摄像头 id=url(可多次)")
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"), help="单摄 RTSP(兜底)")
    ap.add_argument("--codec", default="h265", choices=["h264", "h265"])
    ap.add_argument("--seconds", type=float, default=60.0)
    ap.add_argument("--evidence", help="OPEN 存证 PNG 目录")
    ap.add_argument("--alpha", type=float, default=0.02, help="背景学习率")
    ap.add_argument("--diff", type=float, default=25.0, help="前景灰度差阈值")
    ap.add_argument("--fg-ratio", type=float, default=0.01, help="判 moving 的前景占比")
    ap.add_argument("--warmup", type=float, default=3.0, help="冷启动预热秒数")
    ap.add_argument("--n-enter", type=int, default=4)
    ap.add_argument("--n-exit", type=int, default=30)
    args = ap.parse_args()

    cams = _parse_cams(args)
    if args.evidence:
        os.makedirs(args.evidence, exist_ok=True)
    fan = Fanout(os.path.join(args.evidence, "events.jsonl") if args.evidence else None)
    cfg = MotionConfig(alpha=args.alpha, diff_thresh=args.diff,
                       fg_ratio_thresh=args.fg_ratio, warmup_s=args.warmup)
    ep_cfg = EpisodeConfig(n_enter=args.n_enter, n_exit=args.n_exit)

    print(f"视觉安防 P0 运动检测:{len(cams)} 路摄像头 × {args.seconds}s  "
          f"(alpha={cfg.alpha} diff={cfg.diff_thresh} fg>{cfg.fg_ratio_thresh} "
          f"N_enter={ep_cfg.n_enter} N_exit={ep_cfg.n_exit})\n")

    stop = threading.Event()
    threads = [threading.Thread(target=_worker, name=cid,
                                args=(cid, url, args.codec, args.seconds, fan,
                                      args.evidence, cfg, ep_cfg, stop), daemon=True)
               for cid, url in cams]
    for t in threads:
        t.start()
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print("\n中断,收尾…")
        stop.set()
        for t in threads:
            t.join(timeout=3.0)
    print("\n完成。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

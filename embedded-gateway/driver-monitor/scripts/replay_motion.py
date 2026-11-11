#!/usr/bin/env python3
"""离线回放/联调 —— 合成帧序列喂 MotionDetector + EpisodeStateMachine,验 OPEN/CLOSE 时序。

不上板子、不接摄像头:自造「黑底移动白块」帧序列,复现一次进场→活动→离场,
观察 episode 的 OPEN/CLOSE 时间线与迟滞行为。OPEN/CLOSE 帧用 png_writer 存证。

需 numpy → 用带 numpy 的解释器跑,如:
  python3.10 scripts/replay_motion.py
  python3.10 scripts/replay_motion.py --evidence /tmp/motion-evidence

合成剧本(默认 15fps):
  0-2s    冷启动 + 空场(黑底,warmup 不判决)
  2-6s    白块从左向右横穿画面(moving)
  6-12s   白块离场,空场;背景差有 ~1.5s「余像」(bg 以 α=0.02 慢慢忘掉白块),
          余像散尽后连续 quiet ≥ N_exit 帧 → CLOSE
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from motion.detector import MotionDetector, MotionConfig     # noqa: E402
from motion.episode import EpisodeStateMachine, EpisodeConfig  # noqa: E402
from util.png_writer import write_png, draw_border            # noqa: E402


def synth_frames(fps: int = 15, h: int = 360, w: int = 640):
    """生成 (ts, frame) 序列:空场 → 白块横穿 → 空场。"""
    dt = 1.0 / fps
    t = 0.0
    n = int(12 * fps)
    bw, bh = 80, 120                                   # 白块尺寸
    for i in range(n):
        img = np.zeros((h, w, 3), np.uint8)
        if 2.0 <= t < 6.0:                             # 白块横穿(2s→6s)
            frac = (t - 2.0) / 4.0
            x0 = int(frac * (w - bw))
            y0 = (h - bh) // 2
            img[y0:y0 + bh, x0:x0 + bw] = 255
        yield round(t, 3), img
        t += dt


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fps", type=int, default=15)
    ap.add_argument("--evidence", help="OPEN/CLOSE 存证 PNG 输出目录(默认不存)")
    args = ap.parse_args()

    det = MotionDetector(MotionConfig(warmup_s=2.0))
    sm = EpisodeStateMachine(EpisodeConfig(n_enter=4, n_exit=30))

    if args.evidence:
        os.makedirs(args.evidence, exist_ok=True)

    events: list[dict] = []
    frames = list(synth_frames(args.fps))
    print(f"回放 {len(frames)} 帧(合成:空场→白块横穿→空场)@ {args.fps}fps\n")

    last_moving = None
    for ts, img in frames:
        s = det.process(ts, img)
        if s.moving != last_moving:                    # moving 翻转才打印,免刷屏
            tag = "warming" if s.warming else ("MOVING" if s.moving else "quiet")
            print(f"  t={ts:6.2f}s  motion={s.score:6.3f}  {tag}")
            last_moving = s.moving
        for ev in sm.update(ts, s.moving, s.score):
            events.append(ev)
            k = ev["event_kind"]
            if k == "open":
                print(f"  t={ts:6.2f}s  >>> OPEN  {ev['event_id']}  ts_start={ev['ts_start']}")
            else:
                print(f"  t={ts:6.2f}s  <<< CLOSE {ev['event_id']}  "
                      f"dur={ev['duration_s']}s peak={ev['peak_motion']} "
                      f"end={ev['ts_end']}")
            if args.evidence:
                shot = img.copy()
                draw_border(shot, (255, 0, 0) if k == "open" else (0, 200, 0))
                p = os.path.join(args.evidence, f"{ev['event_id']}-{k}.png")
                write_png(p, shot)
                print(f"           存证 → {p}")

    # 结论校验:剧本应恰好一对 OPEN/CLOSE,时序合理
    opens = [e for e in events if e["event_kind"] == "open"]
    closes = [e for e in events if e["event_kind"] == "close"]
    ok = (len(opens) == 1 and len(closes) == 1
          and opens[0]["event_id"] == closes[0]["event_id"]
          and 2.0 <= opens[0]["ts_start"] <= 3.0        # 白块 2s 入场,4 帧内 OPEN
          and 6.0 <= closes[0]["ts_end"] <= 8.5         # 运动 6s 停 + ~1.5s 背景余像
          and closes[0]["duration_s"] > 3.0)            # 覆盖大部分横穿时长
    print(f"\n发出事件 {len(events)} 条(open={len(opens)} close={len(closes)})")
    print(f"剧本结论:{'✅ 一次完整 episode(OPEN→CLOSE)时序正确' if ok else '⚠️ 时序异常,检查阈值/剧本'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

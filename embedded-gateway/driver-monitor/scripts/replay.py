#!/usr/bin/env python3
"""离线回放/联调 —— 把特征轨迹喂进 状态机 + 事件适配器,打印状态时间线与事件。

用途:
  - 不上板子就能调阈值、看状态机在一段"疲劳剧本"下的反应。
  - 也能回放真实录制的特征轨迹(JSON)做回归。

用法:
  python3 scripts/replay.py                       # 跑内置合成剧本(清醒→困倦→微睡→恢复)
  python3 scripts/replay.py --trace trace.json    # 回放真实特征轨迹
  python3 scripts/replay.py --config config/thresholds.example.json --events

轨迹 JSON 格式:[{ "ts":0.0,"face_present":true,"ear":0.30,"mar":0.2,"yaw":0,"pitch":0 }, ...]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from drowsiness.engine import (DrowsinessEngine, DrowsinessConfig,   # noqa: E402
                               FrameObservation)
from event.adapter import EventAdapter, EventAdapterConfig, CallableSink   # noqa: E402


def synthetic_trace(fps: int = 15) -> list[dict]:
    """合成剧本(秒):
      0-20  清醒(EAR~0.30,偶尔正常眨眼)
      20-50 困倦(EAR 下滑、PERCLOS 上升、打几个哈欠)
      50-54 微睡(连续闭眼 4s)
      54-70 恢复清醒
    """
    dt = 1.0 / fps
    frames: list[dict] = []
    t = 0.0
    n = int(70 * fps)
    for i in range(n):
        face = True
        ear, mar, yaw, pitch = 0.30, 0.20, 0.0, 0.0
        if t < 20:                          # 清醒:每 ~3s 眨一次眼(2 帧)
            if int(t / 3) != int((t - dt) / 3):
                ear = 0.10
        elif t < 50:                        # 困倦:EAR 整体下移 + 更频繁半闭 + 3 个哈欠
            ear = 0.22
            if (i % int(fps * 1.5)) < int(fps * 0.6):   # 40% 时间半闭
                ear = 0.12
            if 25 <= t < 26 or 33 <= t < 34 or 41 <= t < 42:   # 哈欠
                mar = 0.8
        elif t < 54:                        # 微睡:连续闭眼
            ear = 0.07
        else:                               # 恢复
            ear = 0.30
        frames.append({"ts": round(t, 3), "face_present": face,
                       "ear": round(ear, 3), "mar": mar, "yaw": yaw, "pitch": pitch})
        t += dt
    return frames


def load_config(path: str | None) -> DrowsinessConfig:
    if path and os.path.exists(path):
        return DrowsinessConfig.from_dict(json.load(open(path, encoding="utf-8")))
    return DrowsinessConfig()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trace", help="特征轨迹 JSON(默认用内置合成剧本)")
    ap.add_argument("--config", help="阈值配置 JSON")
    ap.add_argument("--events", action="store_true", help="同时打印 event-adapter 发出的事件")
    ap.add_argument("--fps", type=int, default=15)
    args = ap.parse_args()

    frames = (json.load(open(args.trace, encoding="utf-8")) if args.trace
              else synthetic_trace(args.fps))
    eng = DrowsinessEngine(load_config(args.config))
    events: list[dict] = []
    adapter = EventAdapter(sinks=[CallableSink(events.append)],
                           config=EventAdapterConfig(min_dwell_s=0.3, realert_interval_s=5.0))

    print(f"回放 {len(frames)} 帧"
          + (f"(轨迹 {args.trace})" if args.trace else "(合成剧本)"))
    prev = None
    counts: dict[str, int] = {}
    for fr in frames:
        obs = FrameObservation(ts=fr["ts"], face_present=fr.get("face_present", True),
                               infer_ok=fr.get("infer_ok", True),
                               ear=fr.get("ear"), mar=fr.get("mar"),
                               yaw=fr.get("yaw"), pitch=fr.get("pitch"))
        r = eng.update(obs)
        adapter.on_result(r)
        counts[r.state] = counts.get(r.state, 0) + 1
        if r.state != prev:                 # 状态切换才打印,免刷屏
            pc = "" if r.perclos is None else f" perclos={r.perclos:.2f}"
            print(f"  t={fr['ts']:6.2f}s  {prev or '—':>11} → {r.state:<11}"
                  f"  {','.join(r.reason)}{pc}")
            prev = r.state

    print("\n状态占比(帧):", {k: counts[k] for k in sorted(counts)})
    if args.events:
        print(f"\n发出事件 {len(events)} 条:")
        for e in events:
            print(f"  [{e['event_kind']:10}] {e['state']:<9} {','.join(e['reason'])}  @{e['timestamp']}")
    # 验证剧本确实走到过 alarm 又恢复
    reached_alarm = "alarm" in counts
    print(f"\n剧本结论:{'✅ 触发过 alarm 并能恢复' if reached_alarm else '⚠️ 未触发 alarm(检查阈值)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""P1 摄像头 RTSP 探测 —— 在 BL412B 上跑,记录 codec/分辨率/fps/码率/连接耗时。

只用 ffprobe(系统装 ffmpeg 即可),纯标准库包装。**密码从环境变量取,不写进代码/日志。**

用法:
  export CAM_RTSP='rtsp://admin:PASSWORD@192.168.1.110:554/0'   # 或用 --url
  python3 scripts/rtsp_probe.py                                  # 探测主码流
  python3 scripts/rtsp_probe.py --url "$CAM_RTSP" --json
  python3 scripts/rtsp_probe.py --soak 1800                      # 连续拉流 30 分钟,记断流/重连

注:打印时会把 URL 里的密码打码,避免落进终端/日志。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time


def redact(url: str) -> str:
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", url)


def ffprobe(url: str, timeout: int = 15) -> dict:
    """返回首个视频流的 codec/宽高/帧率/码率 + 连接耗时;失败返回 {'ok': False, 'error': ...}。"""
    t0 = time.time()
    cmd = ["ffprobe", "-v", "error", "-rtsp_transport", "tcp",
           "-select_streams", "v:0", "-show_streams", "-show_format",
           "-of", "json", url]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        return {"ok": False, "error": "ffprobe 未安装(apt install ffmpeg)"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "ffprobe 超时", "connect_s": round(time.time() - t0, 2)}
    connect_s = round(time.time() - t0, 2)
    if p.returncode != 0:
        return {"ok": False, "error": (p.stderr or "ffprobe 失败").strip(), "connect_s": connect_s}
    data = json.loads(p.stdout or "{}")
    st = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), {})
    fr = st.get("avg_frame_rate") or st.get("r_frame_rate") or "0/0"
    try:
        num, den = fr.split("/")
        fps = round(int(num) / int(den), 2) if int(den) else 0.0
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    return {"ok": True, "connect_s": connect_s,
            "codec": st.get("codec_name"),
            "width": st.get("width"), "height": st.get("height"),
            "fps": fps,
            "bit_rate": st.get("bit_rate") or data.get("format", {}).get("bit_rate")}


def soak(url: str, seconds: int) -> dict:
    """连续探测,统计断流/重连。每 ~10s 探一次。"""
    end = time.time() + seconds
    probes = ok = fail = 0
    first_fail_streak = max_fail_streak = streak = 0
    print(f"[soak] {seconds}s 连续探测 {redact(url)} …", flush=True)
    while time.time() < end:
        r = ffprobe(url)
        probes += 1
        if r.get("ok"):
            ok += 1; streak = 0
        else:
            fail += 1; streak += 1
            max_fail_streak = max(max_fail_streak, streak)
            if first_fail_streak == 0:
                first_fail_streak = probes
            print(f"  [{probes}] 失败: {r.get('error')}", flush=True)
        time.sleep(10)
    return {"duration_s": seconds, "probes": probes, "ok": ok, "fail": fail,
            "max_consecutive_fail": max_fail_streak}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=os.environ.get("CAM_RTSP"),
                    help="RTSP URL(默认取环境变量 CAM_RTSP)")
    ap.add_argument("--soak", type=int, default=0, help="连续拉流秒数(P1 建议 1800)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if not args.url:
        print("缺 RTSP URL:--url 或 export CAM_RTSP=...", file=sys.stderr)
        return 2

    if args.soak:
        res = soak(args.url, args.soak)
    else:
        res = ffprobe(args.url)
    res["url"] = redact(args.url)        # 打码后才输出

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        if res.get("ok") is False:
            print(f"探测失败: {res.get('error')}  (连接 {res.get('connect_s')}s)")
        elif "probes" in res:
            print(f"soak {res['duration_s']}s: 探测{res['probes']} 成功{res['ok']} "
                  f"失败{res['fail']} 最长连续失败{res['max_consecutive_fail']}")
        else:
            print(f"OK  {res['codec']} {res['width']}x{res['height']} @{res['fps']}fps "
                  f"码率{res.get('bit_rate')}  连接{res['connect_s']}s")
    return 0 if res.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())

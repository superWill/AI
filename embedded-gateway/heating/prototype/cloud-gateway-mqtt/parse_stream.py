#!/usr/bin/env python3
"""平台/云侧：解析网关 MQTT 上行数据的示例（纯标准库，无需 paho）。

用法：靠 mosquitto_sub 收，本脚本只负责解析 stdin：
    mosquitto_sub -h 192.168.1.230 -t 'station/#' -v | python3 parse_stream.py

演示解析的四个要点：
  ① ts(Unix ms) → 本地时间      ② seq 单调 → 丢帧/补传检测
  ③ replay:true → 补传帧识别     ④ q 质量码 → 非 good 高亮
"""

from __future__ import annotations   # 让注解不被求值，兼容 BL412B 的 Python 3.8

import json
import sys
import time

last_seq: dict[str, int] = {}      # device_id -> 上一个非补传 seq

# 展开时重点看的几个点（按需改）
WATCH = ("pri_supply_temp", "sec_supply_temp", "outdoor_temp")


def ts_local(ms: int) -> str:
    """采样时刻(Unix ms) → 本地 HH:MM:SS。注意是采样时刻，不是收到时刻。"""
    return time.strftime("%H:%M:%S", time.localtime(ms / 1000))


def on_telemetry(dev: str, p: dict):
    seq = p.get("seq")
    replay = bool(p.get("replay"))
    pts = p.get("points", {})

    # ② seq 连续性（补传帧不参与判断）
    gap = ""
    prev = last_seq.get(dev)
    if prev is not None and not replay and seq != prev + 1:
        gap = f"  ⚠️丢帧 {prev}->{seq}"
    if not replay:
        last_seq[dev] = seq

    # ④ 质量码：挑出非 good 的点
    bad = [k for k, v in pts.items() if v.get("q") != "good"]

    tag = "↩补传" if replay else "遥测"
    line = (f"[{ts_local(p['ts'])}] {dev} {tag} seq={seq} "
            f"sync={p.get('clock_sync')} 点数={len(pts)}")
    if bad:
        line += f"  ⚠️非good:{bad}"
    line += gap
    print(line)

    # ③ 先看 q 再用 v —— 展开关注点
    for k in WATCH:
        if k in pts:
            v, q = pts[k].get("v"), pts[k].get("q")
            flag = "" if q == "good" else "  ←按质量码降权/剔除"
            print(f"        {k:18}= {v:>8}  ({q}){flag}")


def on_heartbeat(dev: str, p: dict):
    print(f"[{ts_local(p['ts'])}] {dev} 心跳 online={p.get('online')} "
          f"buffer={p.get('buffer')}")


def on_reply(dev: str, p: dict):
    extra = f" reason={p['reason']}" if p.get("reason") else ""
    print(f"[{ts_local(p['ts'])}] {dev} 回传 cmd={p.get('command_id')} "
          f"status={p.get('status')}{extra}")


def on_alarm(dev: str, p: dict):
    print(f"[{ts_local(p['ts'])}] {dev} 🚨报警 {p.get('alarm_id')}: {p.get('message')}")


HANDLERS = {
    "telemetry": on_telemetry,
    "heartbeat": on_heartbeat,
    "command_reply": on_reply,
    "alarm": on_alarm,
}


def main():
    # mosquitto_sub -v 每行格式： "<topic> <json_payload>"
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        topic, _, payload = line.partition(" ")     # JSON 里有空格，只切第一个
        parts = topic.split("/")                     # station/{dev}/{type}
        if len(parts) < 3:
            continue
        dev, mtype = parts[1], parts[2]
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue
        handler = HANDLERS.get(mtype)
        if handler:
            handler(dev, data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

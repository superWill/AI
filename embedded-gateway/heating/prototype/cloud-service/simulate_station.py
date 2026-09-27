#!/usr/bin/env python3
"""多站点遥测模拟器：在测试机上造数据，不用等真实网关，先把 Grafana 点亮。

按数据契约 §3 发 station/{id}/telemetry（带 ts/seq/points{v,q}）+ 周期 heartbeat，
偶发 alarm。可一次起 N 个站，验证入库/聚合/看板和大致吞吐。

依赖： pip install paho-mqtt
示例：
  python3 simulate_station.py --stations 10 --interval 5 --host 127.0.0.1
  python3 simulate_station.py --stations 1  --host <ECS公网IP> -u user -P pass
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time

import paho.mqtt.client as mqtt

# 点表取自数据契约 §3 的样例（基准值, 波动幅度）
BASE = {
    "pri_supply_temp":   (78.0, 3.0),
    "pri_return_temp":   (45.0, 2.0),
    "pri_flow":          (32.0, 4.0),
    "pri_valve_feedback": (60.0, 8.0),
    "sec_supply_temp":   (52.0, 2.0),
    "sec_return_temp":   (42.0, 1.5),
    "sec_flow":          (88.0, 6.0),
    "circ_pump_freq_fb": (38.0, 3.0),
    "refill_pressure":   (0.32, 0.05),
    "outdoor_temp":      (-3.0, 4.0),
}


def make_points(phase: float) -> dict:
    pts = {}
    for k, (base, amp) in BASE.items():
        # 正弦慢漂 + 噪声，像真实工况
        v = base + amp * math.sin(phase) * 0.4 + random.uniform(-amp, amp) * 0.3
        q = "good" if random.random() > 0.02 else random.choice(["stale", "bad"])
        pts[k] = {"v": round(v, 2), "q": q}
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("-u", "--username", default="")
    ap.add_argument("-P", "--password", default="")
    ap.add_argument("--stations", type=int, default=3, help="模拟站点数")
    ap.add_argument("--interval", type=float, default=5.0, help="遥测周期秒")
    args = ap.parse_args()

    client = mqtt.Client(client_id="sim-%d" % random.randint(1000, 9999))
    if args.username:
        client.username_pw_set(args.username, args.password)
    client.connect(args.host, args.port, 60)
    client.loop_start()

    ids = ["stn-%03d" % i for i in range(1, args.stations + 1)]
    seq = {d: random.randint(1, 100) for d in ids}
    # 累计量与设备状态（每站独立）
    heat = {d: round(random.uniform(1000, 5000), 2) for d in ids}    # heat_total 基数 GJ
    refill = {d: round(random.uniform(100, 500), 2) for d in ids}    # refill_total 基数 m3
    pump_on = {d: True for d in ids}
    print("simulating %d station(s) -> %s:%d every %.1fs (Ctrl-C 停止)"
          % (len(ids), args.host, args.port, args.interval))
    tick = 0
    try:
        while True:
            now_ms = int(time.time() * 1000)
            for d in ids:
                seq[d] += 1
                pts = make_points(tick * 0.1)
                # 循环泵偶发启停 → 发 event + 改写泵频
                if random.random() < 0.02:
                    new_on = not pump_on[d]
                    client.publish("station/%s/event" % d, json.dumps(
                        {"device_id": d, "ts": now_ms, "equip": "circ_pump",
                         "from_state": "running" if pump_on[d] else "stopped",
                         "to_state": "running" if new_on else "stopped"}), qos=1)
                    pump_on[d] = new_on
                if not pump_on[d]:
                    pts["circ_pump_freq_fb"] = {"v": 0.0, "q": "good"}
                # 累计量：仅运行时增长（差分口径的源）
                if pump_on[d]:
                    heat[d] = round(heat[d] + random.uniform(0.02, 0.06), 3)
                    refill[d] = round(refill[d] + random.uniform(0.0, 0.01), 3)
                pts["heat_total"] = {"v": heat[d], "q": "good"}
                pts["refill_total"] = {"v": refill[d], "q": "good"}
                frame = {"device_id": d, "ts": now_ms, "clock_sync": "synced",
                         "seq": seq[d], "points": pts}
                client.publish("station/%s/telemetry" % d, json.dumps(frame), qos=1)
                if tick % 12 == 0:  # 每 12 帧发一次心跳
                    client.publish("station/%s/heartbeat" % d, json.dumps(
                        {"device_id": d, "ts": now_ms, "online": True, "buffer": 0}), qos=1)
                if random.random() < 0.01:  # 偶发报警
                    client.publish("station/%s/alarm" % d, json.dumps(
                        {"device_id": d, "ts": now_ms, "alarm_id": "SIM_OVERTEMP",
                         "message": "二次供温瞬时越限(模拟)"}), qos=1)
            tick += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nstopped")
        client.loop_stop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""三层网关骨架(纯标准库)——把今天学的全拼起来:

   采集层(Modbus 轮询,超时/退避/隔离) ─push→ 队列(时间戳+质量码) ─pull→ 上传层(打印=占位上云)

设计要点(对应 docs/architecture/gateway-reliability-and-performance.md):
  - 所有 I/O 带超时,绝不死等;坏设备连续超时→标记离线→降频(退避),不拖累整轮。
  - 采集与上传解耦:两个线程 + 队列,网络/上传慢不卡采集。
  - 每个点带质量码(good/bad),上层据此判断能不能用。
真接 MQTT:把 uploader 里的 print 换成 cloud-gateway-mqtt/gateway_mqtt.py 的 publish 即可。

用法(板子上):
  python3 gateway.py /dev/ttyS1 gateway_config.json
"""
import json
import os
import select
import struct
import sys
import termios
import threading
import time

BAUDS = {9600: termios.B9600, 19200: termios.B19200, 38400: termios.B38400,
         57600: termios.B57600, 115200: termios.B115200}


def crc16(data):
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return struct.pack("<H", crc)


def open_serial(dev, baud):
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
    a = termios.tcgetattr(fd)
    a[0] = a[1] = a[3] = 0
    a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
    a[4] = a[5] = BAUDS[baud]
    a[6][termios.VMIN] = 0; a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd


def read_frame(fd, timeout, gap=0.03):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], max(0, deadline - time.time()))
        if not r:
            continue
        buf = os.read(fd, 256)
        if not buf:
            continue
        while True:
            r2, _, _ = select.select([fd], [], [], gap)
            if r2:
                buf += os.read(fd, 256)
            else:
                return buf
    return b""


def read_holding(fd, addr, start, count, timeout):
    """主站读保持寄存器。返回 (regs列表, None) 或 (None, 错误原因)。"""
    body = struct.pack(">BBHH", addr, 0x03, start, count)
    termios.tcflush(fd, termios.TCIOFLUSH)
    os.write(fd, body + crc16(body))
    resp = read_frame(fd, timeout)
    if not resp:
        return None, "timeout"
    if crc16(resp[:-2]) != resp[-2:]:
        return None, "crc_error"
    if resp[1] & 0x80:
        return None, "exception_%d" % (resp[2] if len(resp) > 2 else 0)
    n = resp[2]
    return [struct.unpack(">H", resp[3 + i:5 + i])[0] for i in range(0, n, 2)], None


def clock_synced():
    """没 RTC 的板子重启后时间会乱(常识 §11)。年份 < 2020 视为没校时,时间戳不可信。"""
    return time.gmtime().tm_year >= 2020


# ---------- 采集层 ----------

def poller(fd, cfg, state, lock, stop):
    """轮询所有设备;坏设备退避;把每台最新状态(含离线)写进共享 state。"""
    devs = cfg["devices"]
    timeout = cfg.get("timeout_s", 1.0)
    offline_after = cfg.get("offline_after", 3)
    interval = cfg.get("poll_interval_s", 3)
    fail = {d["addr"]: 0 for d in devs}
    nextpoll = {d["addr"]: 0 for d in devs}
    while not stop.is_set():
        now = time.time()
        for d in devs:
            a = d["addr"]
            if now < nextpoll[a]:
                continue
            regs, err = read_holding(fd, a, d["start"], d["count"], timeout)
            ts = int(time.time() * 1000)
            if err:
                fail[a] += 1
                offline = fail[a] >= offline_after
                # 退避:连续失败越多,下次越晚再试(最多 30s),不拖累整轮
                backoff = min(30, interval * (2 ** min(fail[a], 4))) if offline else interval
                nextpoll[a] = now + backoff
                sample = {"addr": a, "name": d["name"], "ts": ts, "ok": False,
                          "health": "离线" if offline else "异常(%s)×%d" % (err, fail[a]),
                          "points": {p["id"]: {"v": None, "q": "bad"} for p in d["points"]}}
            else:
                fail[a] = 0
                nextpoll[a] = now + interval
                pts = {p["id"]: {"v": round(regs[p["reg"] - d["start"]] * p.get("scale", 1), 3),
                                 "u": p.get("unit", ""), "q": "good"} for p in d["points"]}
                sample = {"addr": a, "name": d["name"], "ts": ts, "ok": True,
                          "health": "在线", "points": pts}
            with lock:
                state[a] = sample
        time.sleep(0.2)


# ---------- 上传层(占位:打印 = 上云) ----------

def uploader(cfg, state, lock, stop):
    dev_id = cfg.get("device_id", "gw-01")
    up_interval = cfg.get("upload_interval_s", 10)
    seq = 0
    while not stop.is_set():
        time.sleep(up_interval)
        with lock:
            snap = list(state.values())                  # 全设备快照:离线的也在,不会凭空消失
        if not snap:
            continue
        seq += 1
        telemetry = {"device_id": dev_id, "ts": int(time.time() * 1000),
                     "clock_sync": "synced" if clock_synced() else "unsynced", "seq": seq,
                     "devices": [{"addr": s["addr"], "name": s["name"], "ok": s["ok"],
                                  "points": s["points"]} for s in snap]}
        # ↓↓↓ 真上线:把这行 print 换成 gateway_mqtt.py 的 publish(telemetry) ↓↓↓
        print("[上传→云] " + json.dumps(telemetry, ensure_ascii=False), flush=True)
        print("[健康] " + "  ".join("%d:%s" % (s["addr"], s["health"]) for s in snap)
              + ("  ⚠️时间未校准" if not clock_synced() else ""), flush=True)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    dev, cfg = sys.argv[1], json.load(open(sys.argv[2]))
    fd = open_serial(dev, cfg.get("baud", 9600))
    state, lock = {}, threading.Lock()                   # 共享最新状态(采集写,上传读)
    stop = threading.Event()
    print("网关启动:口=%s 设备数=%d 轮询=%ds 上传=%ds  时钟=%s。Ctrl-C 退出。"
          % (dev, len(cfg["devices"]), cfg.get("poll_interval_s", 3),
             cfg.get("upload_interval_s", 10),
             "已校准" if clock_synced() else "未校准(时间戳不可信)"), flush=True)
    tp = threading.Thread(target=poller, args=(fd, cfg, state, lock, stop), daemon=True)
    tu = threading.Thread(target=uploader, args=(cfg, state, lock, stop), daemon=True)
    tp.start(); tu.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()
        print("\n网关退出。")


if __name__ == "__main__":
    main()

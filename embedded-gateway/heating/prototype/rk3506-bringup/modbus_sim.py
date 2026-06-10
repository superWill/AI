#!/usr/bin/env python3
"""配置驱动的 Modbus RTU 从站模拟器(纯标准库)——网关的"陪练设备"。

一个串口上模拟多台从站(多 drop),寄存器表 + 故障从 JSON 读,真表没到也能开发网关。
故障注入(fault):
  none      正常应答
  offline   不应答(模拟掉线 → 测网关超时/退避)
  bad_crc   应答但 CRC 故意算错(测网关丢帧)
  exception 回 Modbus 异常码 2(测网关认异常)

用法(104 上,USB-TTL 当线):
  python3 modbus_sim.py /dev/ttyUSB0 sim_config.json
"""
import json
import math
import os
import select
import struct
import sys
import termios
import time

BAUDS = {9600: termios.B9600, 19200: termios.B19200, 38400: termios.B38400,
         57600: termios.B57600, 115200: termios.B115200}


def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return struct.pack("<H", crc)


def hx(b): return " ".join("%02X" % x for x in b)


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


def _read_exact(fd, n, deadline):
    b = b""
    while len(b) < n and time.time() < deadline:
        r, _, _ = select.select([fd], [], [], max(0, deadline - time.time()))
        if r:
            c = os.read(fd, n - len(b))
            if c:
                b += c
    return b


def read_frame(fd, timeout=5.0):
    """按 Modbus 帧长精确分帧(不靠时间间隔,彻底避免请求粘连)。
    先读 addr+func,再按功能码读固定长度的剩余字节。"""
    deadline = time.time() + timeout
    head = _read_exact(fd, 2, deadline)          # 从站地址 + 功能码
    if len(head) < 2:
        return b""
    func = head[1] & 0x7F
    if func in (0x03, 0x04, 0x05, 0x06):
        body = _read_exact(fd, 6, deadline)      # 起始2 + 数量/值2 + CRC2 = 共8字节
    elif func == 0x10:                           # 写多个:变长
        pre = _read_exact(fd, 5, deadline)       # 起始2 数量2 字节数1
        nb = pre[4] if len(pre) >= 5 else 0
        body = pre + _read_exact(fd, nb + 2, deadline)
    else:
        body = _read_exact(fd, 6, deadline)      # 未知:按 8 字节尽力读
    return head + body


def reg_value(spec, t0):
    """寄存器当前值:base 固定;给了 swing/period 就按正弦在 base±swing 间慢变(模拟真实波动)。"""
    base = spec.get("base", 0)
    swing = spec.get("swing", 0)
    if not swing:
        return base & 0xFFFF
    period = spec.get("period_s", 60)
    v = base + swing * 0.5 * (1 + math.sin(2 * math.pi * (time.time() - t0) / period))
    return int(round(v)) & 0xFFFF


def build_read_resp(addr, regs):
    vals = b"".join(struct.pack(">H", v) for v in regs)
    body = struct.pack(">BBB", addr, 0x03, len(vals)) + vals
    return body + crc16(body)


def exc_resp(addr, func, code):
    body = struct.pack(">BBB", addr, func | 0x80, code)
    return body + crc16(body)


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    dev, cfg_path = sys.argv[1], sys.argv[2]
    cfg = json.load(open(cfg_path))
    baud = cfg.get("baud", 9600)
    slaves = {s["addr"]: s for s in cfg["slaves"]}
    fd = open_serial(dev, baud)
    t0 = time.time()
    print("模拟器在 %s @ %d,从站: %s。Ctrl-C 退出。"
          % (dev, baud, ", ".join("%d(%s,%s)" % (s["addr"], s.get("name", "?"),
             s.get("fault", "none")) for s in cfg["slaves"])), flush=True)
    try:
        while True:
            frame = read_frame(fd)
            if len(frame) < 4:
                continue
            addr, func = frame[0], frame[1]
            s = slaves.get(addr)
            resp, note = None, ""                       # 默认不应答
            if s is None:
                note = "未知地址,不应答"                  # 总线上没这台
            elif crc16(frame[:-2]) != frame[-2:]:
                note = "请求CRC错,丢弃不应答"
            elif s.get("fault") == "offline":
                note = "[故障:offline] 不应答"
            elif func == 0x06:                          # 写单个寄存器(控制!)
                reg, val = struct.unpack(">HH", frame[2:6])
                s.setdefault("registers", {})[str(reg)] = {"base": val}   # 存下被控值
                resp = frame[:6] + crc16(frame[:6])     # 0x06 原样回 addr/reg/val
                note = "[写] 寄存器%d=%d" % (reg, val)
            elif func != 0x03:
                resp, note = exc_resp(addr, func, 1), "非0x03→异常码1"
            else:
                start, count = struct.unpack(">HH", frame[2:6])
                regs = s.get("registers", {})
                if any(str(start + i) not in regs for i in range(count)):
                    resp, note = exc_resp(addr, func, 2), "越界→异常码2"
                elif s.get("fault") == "exception":
                    resp, note = exc_resp(addr, func, 2), "[故障:exception]→异常码2"
                else:
                    vals = [reg_value(regs[str(start + i)], t0) for i in range(count)]
                    resp = build_read_resp(addr, vals)
                    if s.get("fault") == "bad_crc":
                        resp = resp[:-2] + bytes([resp[-2] ^ 0xFF, resp[-1]])
                        note = "[故障:bad_crc] CRC故意错"
                    else:
                        note = "正常应答 %s" % vals
            if "正常应答" not in note:                  # 只打异常/写/离线,正常读不刷日志(否则 I/O 拖慢→请求粘连)
                print("收 %s  →  %s" % (hx(frame), note), flush=True)
            if resp:
                os.write(fd, resp)
    except KeyboardInterrupt:
        print("\n模拟器退出。")


if __name__ == "__main__":
    main()

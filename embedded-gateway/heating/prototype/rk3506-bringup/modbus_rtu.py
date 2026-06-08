#!/usr/bin/env python3
"""真实串口 Modbus RTU:主站 / 从站(纯标准库,无需 pymodbus)。

跟 modbus_demo.py 的区别:不再用虚拟串口,而是跑在板子真实 UART 上,数据真的过线。
这一层是 RS485 的电气换成了板载 3.3V TTL —— 帧/功能码/CRC 完全一样,
真接 RS485 表时只是中间多一个 RS485 收发器,这套代码一行不用改。

接线(HD-RK3506-IOT 40Pin,板载 TTL,同板共地不用单接 GND):
    ttyS1_TX(pin 8)  ──►  ttyS2_RX(pin 12)
    ttyS2_TX(pin 11) ──►  ttyS1_RX(pin 10)

用法(板子上,开两个终端 / 或后台跑从站):
    python3 modbus_rtu.py slave  /dev/ttyS2 1        # 从站:模拟温湿度表,常驻应答
    python3 modbus_rtu.py master /dev/ttyS1 1        # 主站:轮询读温湿度(像真网关)
    末尾可加波特率,默认 9600:  ... /dev/ttyS1 1 115200
"""
import os
import select
import struct
import sys
import termios
import time

BAUDS = {9600: termios.B9600, 19200: termios.B19200,
         38400: termios.B38400, 57600: termios.B57600, 115200: termios.B115200}


def crc16(data: bytes) -> bytes:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return struct.pack("<H", crc)


def hx(b: bytes) -> str:
    return " ".join("%02X" % x for x in b)


def open_serial(dev, baud):
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
    a = termios.tcgetattr(fd)
    a[0] = 0; a[1] = 0
    a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
    a[3] = 0
    a[4] = a[5] = BAUDS[baud]
    a[6][termios.VMIN] = 0
    a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd


def read_frame(fd, timeout, gap=0.03):
    """读一帧:等到有数据,再读到"帧间静默(gap 内无新字节)"为止。RTU 就是靠静默分帧。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], deadline - time.time())
        if not r:
            continue
        buf = os.read(fd, 256)
        if not buf:
            continue
        while True:                                  # 收到首段后,持续读到出现 gap 静默
            r2, _, _ = select.select([fd], [], [], gap)
            if r2:
                buf += os.read(fd, 256)
            else:
                return buf
    return b""


# ---------- 主站 ----------

def build_read_holding(slave, start, count):
    body = struct.pack(">BBHH", slave, 0x03, start, count)
    return body + crc16(body)


def parse_response(frame):
    if len(frame) < 5:
        raise ValueError("帧太短/无响应")
    if crc16(frame[:-2]) != frame[-2:]:
        raise ValueError("CRC 校验失败")
    if frame[1] & 0x80:
        names = {1: "非法功能码", 2: "非法寄存器地址", 3: "非法数据值", 4: "从站故障"}
        raise ValueError("异常码 %d(%s)" % (frame[2], names.get(frame[2], "?")))
    n = frame[2]
    return [struct.unpack(">H", frame[3 + i:5 + i])[0] for i in range(0, n, 2)]


def run_master(dev, addr, baud):
    fd = open_serial(dev, baud)
    print("主站在 %s @ %d,轮询从站 %d(每 2 秒)。Ctrl-C 退出。" % (dev, baud, addr))
    ok = miss = 0
    try:
        while True:
            req = build_read_holding(addr, 0, 2)
            termios.tcflush(fd, termios.TCIOFLUSH)
            os.write(fd, req)
            resp = read_frame(fd, timeout=1.0)
            try:
                regs = parse_response(resp)
                ok += 1
                print("[OK %d] 发:%s  收:%s  → 温度=%.1f℃ 湿度=%.1f%%RH"
                      % (ok, hx(req), hx(resp), regs[0] / 10, regs[1] / 10))
            except ValueError as e:
                miss += 1
                print("[超时/错 %d] 发:%s  收:%s  (%s)"
                      % (miss, hx(req), hx(resp) if resp else "(无)", e))
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n主站退出。成功 %d 次,失败 %d 次。" % (ok, miss))


# ---------- 从站 ----------

def run_slave(dev, addr, baud):
    fd = open_serial(dev, baud)
    regs = {0: 235, 1: 486, 2: 1}                    # 23.5℃, 48.6%RH, 状态正常
    print("从站在 %s @ %d,地址 %d,模拟温湿度表,常驻应答。Ctrl-C 退出。" % (dev, baud, addr))
    t0 = time.time()
    try:
        while True:
            frame = read_frame(fd, timeout=5.0)
            if not frame:
                continue
            regs[0] = 235 + int((time.time() - t0) % 30) // 3   # 让温度慢慢变,像真表
            resp = handle(frame, addr, regs)
            tag = "应答" if resp else "(丢弃:CRC错/非本机)"
            print("收:%s  %s%s" % (hx(frame), tag, "  发:" + hx(resp) if resp else ""))
            if resp:
                os.write(fd, resp)
    except KeyboardInterrupt:
        print("\n从站退出。")


def handle(frame, addr, regs):
    if len(frame) < 4 or crc16(frame[:-2]) != frame[-2:]:
        return None
    slave, func = frame[0], frame[1]
    if slave != addr:
        return None
    if func != 0x03:
        body = struct.pack(">BBB", addr, func | 0x80, 1)         # 非法功能码
        return body + crc16(body)
    start, count = struct.unpack(">HH", frame[2:6])
    if any((start + i) not in regs for i in range(count)):
        body = struct.pack(">BBB", addr, func | 0x80, 2)         # 非法地址
        return body + crc16(body)
    vals = b"".join(struct.pack(">H", regs[start + i]) for i in range(count))
    body = struct.pack(">BBB", slave, func, len(vals)) + vals
    return body + crc16(body)


def main():
    if len(sys.argv) < 4 or sys.argv[1] not in ("slave", "master"):
        print(__doc__); sys.exit(2)
    role, dev, addr = sys.argv[1], sys.argv[2], int(sys.argv[3])
    baud = int(sys.argv[4]) if len(sys.argv) > 4 else 9600
    (run_slave if role == "slave" else run_master)(dev, addr, baud)


if __name__ == "__main__":
    main()

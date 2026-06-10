#!/usr/bin/env python3
"""104 现场陪练:扩展版 Modbus RTU 多从站模拟器(纯标准库)。

比 rk3506-bringup/modbus_sim.py 多两件事,专门陪 rk3506-app 跑:
  1) 支持写寄存器(0x06 单个 / 0x10 多个)—— 网关下发设定值能写进来。
  2) setpoint/feedback 寄存器 —— 写入设定值后,反馈寄存器朝它收敛,
     于是"平台下发→写回→反馈变化"的控制闭环在真 Modbus 链路上也看得到。

寄存器类型(sim_104_config.json 里 registers 的 value):
  {"base":N,"swing":S,"period_s":P}        正弦慢变(传感器)
  {"fixed":N}                              常量(开关量/状态)
  {"setpoint":N}                           保存最近写入值(可写,init=N)
  {"feedback":"<reg>","init":N,"rate":R}   每拍朝寄存器<reg>的值收敛(执行器反馈)

故障注入 fault: none/offline/bad_crc/exception(同 bringup 版)。

用法(104 上,USB-TTL 当线):
  python3 sim_104.py /dev/ttyUSB0 sim_104_config.json
"""
import json
import math
import os
import select
import struct
import sys
import termios
import threading
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


def hx(b):
    return " ".join("%02X" % x for x in b)


def open_serial(dev, baud):
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
    a = termios.tcgetattr(fd)
    a[0] = a[1] = a[3] = 0
    a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
    a[4] = a[5] = BAUDS[baud]
    a[6][termios.VMIN] = 0
    a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd


def read_frame(fd, timeout=5.0, gap=0.03):
    deadline = time.time() + timeout
    while time.time() < deadline:
        r, _, _ = select.select([fd], [], [], deadline - time.time())
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


class Bank:
    """一台从站的寄存器组:保存 setpoint/feedback 的运行时值,oscillate/fixed 现算。"""

    def __init__(self, spec: dict):
        self.spec = spec
        self.t0 = time.time()
        self.cur = {}                       # reg(int) -> 运行时整数值(setpoint/feedback)
        for reg, s in spec.items():
            if "setpoint" in s:
                self.cur[int(reg)] = int(s["setpoint"]) & 0xFFFF
            elif "feedback" in s:
                self.cur[int(reg)] = int(s.get("init", 0)) & 0xFFFF

    def tick(self):
        """反馈寄存器朝其 setpoint 收敛一步(一阶滞后)。"""
        for reg, s in self.spec.items():
            if "feedback" in s:
                r = int(reg)
                target = self.cur.get(int(s["feedback"]), self.cur[r])
                rate = s.get("rate", 0.25)
                self.cur[r] = int(round(self.cur[r] + (target - self.cur[r]) * rate)) & 0xFFFF

    def read(self, reg: int):
        s = self.spec.get(str(reg))
        if s is None:
            return None
        if "fixed" in s:
            return int(s["fixed"]) & 0xFFFF
        if "setpoint" in s or "feedback" in s:
            return self.cur[reg]
        base = s.get("base", 0)
        swing = s.get("swing", 0)
        if not swing:
            return int(base) & 0xFFFF
        period = s.get("period_s", 60)
        v = base + swing * 0.5 * (1 + math.sin(2 * math.pi * (time.time() - self.t0) / period))
        return int(round(v)) & 0xFFFF

    def write(self, reg: int, value: int) -> bool:
        s = self.spec.get(str(reg))
        if s is None:
            return False                    # 不存在的寄存器不接受写
        # 只允许写 setpoint(执行器指令);传感器/反馈寄存器拒写
        if "setpoint" not in s:
            return False
        self.cur[reg] = int(value) & 0xFFFF
        return True


def build_read_resp(addr, regs):
    vals = b"".join(struct.pack(">H", v) for v in regs)
    body = struct.pack(">BBB", addr, 0x03, len(vals)) + vals
    return body + crc16(body)


def exc_resp(addr, func, code):
    body = struct.pack(">BBB", addr, func | 0x80, code)
    return body + crc16(body)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    dev, cfg_path = sys.argv[1], sys.argv[2]
    cfg = json.load(open(cfg_path))
    baud = cfg.get("baud", 9600)
    slaves = {s["addr"]: s for s in cfg["slaves"]}
    banks = {s["addr"]: Bank(s.get("registers", {})) for s in cfg["slaves"]}
    fd = open_serial(dev, baud)

    # 收敛后台拍:让反馈寄存器持续朝设定值靠拢
    stop = threading.Event()

    def ticker():
        while not stop.is_set():
            for b in banks.values():
                b.tick()
            stop.wait(0.5)
    threading.Thread(target=ticker, daemon=True).start()

    print("104 模拟器 @ %s %d,从站: %s。Ctrl-C 退出。"
          % (dev, baud, ", ".join("%d(%s,%s)" % (s["addr"], s.get("name", "?"),
             s.get("fault", "none")) for s in cfg["slaves"])), flush=True)
    try:
        while True:
            frame = read_frame(fd)
            if len(frame) < 4:
                continue
            addr, func = frame[0], frame[1]
            s = slaves.get(addr)
            resp, note = None, ""
            if s is None:
                note = "未知地址,不应答"
            elif crc16(frame[:-2]) != frame[-2:]:
                note = "请求CRC错,丢弃"
            elif s.get("fault") == "offline":
                note = "[故障:offline] 不应答"
            elif func == 0x03:                       # 读保持寄存器
                start, count = struct.unpack(">HH", frame[2:6])
                bank = banks[addr]
                vals = [bank.read(start + i) for i in range(count)]
                if any(v is None for v in vals):
                    resp, note = exc_resp(addr, func, 2), "读越界→异常码2"
                elif s.get("fault") == "exception":
                    resp, note = exc_resp(addr, func, 2), "[故障:exception]→异常码2"
                else:
                    resp = build_read_resp(addr, vals)
                    if s.get("fault") == "bad_crc":
                        resp = resp[:-2] + bytes([resp[-2] ^ 0xFF, resp[-1]])
                        note = "[故障:bad_crc] CRC故意错"
                    else:
                        note = "读 %s" % vals
            elif func == 0x06:                       # 写单个寄存器
                reg, value = struct.unpack(">HH", frame[2:6])
                if banks[addr].write(reg, value):
                    resp, note = frame[:6] + crc16(frame[:6]), "写 reg%d=%d ✓" % (reg, value)
                else:
                    resp, note = exc_resp(addr, func, 2), "reg%d 不可写→异常码2" % reg
            elif func == 0x10:                       # 写多个寄存器
                start, count = struct.unpack(">HH", frame[2:6])
                nbytes = frame[6]
                ok = True
                for i in range(count):
                    v = struct.unpack(">H", frame[7 + i * 2:9 + i * 2])[0]
                    ok = banks[addr].write(start + i, v) and ok
                if ok:
                    body = frame[:6]
                    resp, note = body + crc16(body), "写%d个 from reg%d ✓" % (count, start)
                else:
                    resp, note = exc_resp(addr, func, 2), "部分不可写→异常码2"
            else:
                resp, note = exc_resp(addr, func, 1), "功能码%d不支持→异常码1" % func
            print("收 %s  →  %s" % (hx(frame), note), flush=True)
            if resp:
                os.write(fd, resp)
    except KeyboardInterrupt:
        stop.set()
        print("\n模拟器退出。")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""开外部串口路径当 Modbus RTU 从站(闭环 L3):FC03 读、FC06 写并更新寄存器表。
用法: modbus_slave_on.py <dev> <config.json>   config: {"regs":{"1":[...]}}"""
import os, sys, struct, termios, select, json
def crc16(d):
    c = 0xFFFF
    for b in d:
        c ^= b
        for _ in range(8): c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return struct.pack("<H", c)
dev = sys.argv[1]
cfg = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
REGS = {int(k): v for k, v in cfg.get("regs", {"1": [0] * 40}).items()}
fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
a = termios.tcgetattr(fd); a[0] = a[1] = a[3] = 0
a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
a[4] = a[5] = termios.B9600; a[6][termios.VMIN] = 0; a[6][termios.VTIME] = 0
termios.tcsetattr(fd, termios.TCSANOW, a); termios.tcflush(fd, termios.TCIOFLUSH)
sys.stderr.write("slave_on %s\n" % dev); sys.stderr.flush()
buf = b""
while True:
    r, _, _ = select.select([fd], [], [], 120)
    if not r: break
    buf += os.read(fd, 256)
    while len(buf) >= 8:
        f = buf[:8]; buf = buf[8:]
        if crc16(f[:-2]) != f[-2:]: continue
        addr, fc, start, count = struct.unpack(">BBHH", f[:6])
        if fc == 0x03 and addr in REGS:
            vals = REGS[addr][start:start + count]
            body = struct.pack(">BBB", addr, 0x03, count * 2) + b"".join(struct.pack(">H", v & 0xFFFF) for v in vals)
            os.write(fd, body + crc16(body))
        elif fc == 0x06 and addr in REGS:
            reg, val = start, count
            while len(REGS[addr]) <= reg: REGS[addr].append(0)
            REGS[addr][reg] = val
            os.write(fd, f)

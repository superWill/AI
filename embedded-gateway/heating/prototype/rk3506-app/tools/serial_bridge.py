#!/usr/bin/env python3
"""测试用:创建两个互联的虚拟串口(pty),把一端的字节转发到另一端。
用于在 Mac 上把 sim_104.py 和 app.py(--source modbus)接起来,无需真硬件。
打印两个串口路径(第一行=A 给模拟器,第二行=B 给网关)。"""
import os, pty, select, sys, tty
mA, sA = pty.openpty(); mB, sB = pty.openpty()
for f in (sA, sB, mA, mB):
    tty.setraw(f)
open(sys.argv[1], "w").write(os.ttyname(sA) + "\n" + os.ttyname(sB) + "\n") if len(sys.argv) > 1 else None
print(os.ttyname(sA), flush=True); print(os.ttyname(sB), flush=True)
while True:
    r, _, _ = select.select([mA, mB], [], [])
    if mA in r:
        os.write(mB, os.read(mA, 4096))
    if mB in r:
        os.write(mA, os.read(mB, 4096))

#!/usr/bin/env python3
"""双端 pty 桥(null-modem):造两个 /dev/pts(A 给从站、B 给网关),两 master 间互转字节。
保持四个 fd 都开着(只读 master),从站/网关各开 A/B 路径。"""
import os, tty, select, sys
mA, sA = os.openpty(); mB, sB = os.openpty()
for fd in (mA, sA, mB, sB): tty.setraw(fd)
open("/tmp/pty_a", "w").write(os.ttyname(sA))
open("/tmp/pty_b", "w").write(os.ttyname(sB))
sys.stderr.write("A=%s B=%s\n" % (os.ttyname(sA), os.ttyname(sB))); sys.stderr.flush()
try:
    while True:
        r, _, _ = select.select([mA, mB], [], [], 120)
        if not r: break
        for fd in r:
            data = os.read(fd, 512)
            if data: os.write(mB if fd == mA else mA, data)
except (OSError, KeyboardInterrupt):
    pass

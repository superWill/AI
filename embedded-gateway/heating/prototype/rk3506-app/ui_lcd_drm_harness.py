#!/usr/bin/env python3
"""增量C 对拍:Go DRM ioctl 缓冲 == drm_hmi_v4.py 的 struct.pack(逐字节)。

  python3 ui_lcd_drm_harness.py [gatewayc_host_bin]
"""
import struct
import subprocess
import sys

W, H, CRTC = 800, 480, 72
MODE = struct.pack("<IHHHHHHHHHHIII32s", 30000, 800, 806, 811, 816, 0,
                   480, 485, 493, 503, 0, 73, 0x0A, 0x48, b"800x480")
exp = {
    "mode": MODE.hex(),
    "create_dumb": struct.pack("<IIIIIIQ", H, W, 32, 0, 0, 0, 0).hex(),
    "addfb": struct.pack("<IIIIIII", 0, W, H, 3200, 32, 24, 7).hex(),
    "map_dumb": struct.pack("<IIQ", 7, 0, 0).hex(),
    "setcrtc": (struct.pack("<QIIIIIII", 0, 1, CRTC, 42, 0, 0, 0, 1) + MODE).hex(),
}

binp = sys.argv[1] if len(sys.argv) > 1 else "./gateway-go/gatewayc-host"
out = subprocess.run([binp, "lcddrmpack"], capture_output=True, text=True).stdout
got = dict(l.split("\t") for l in out.splitlines() if "\t" in l)

ok = True
for k in ("mode", "create_dumb", "addfb", "map_dumb", "setcrtc"):
    m = exp[k] == got.get(k)
    ok &= m
    if m:
        print("%-12s 逐字节一致 ✅ (%d 字节)" % (k, len(exp[k]) // 2))
    else:
        print("%-12s ❌\n  py=%s\n  go=%s" % (k, exp[k], got.get(k)))
print("=> 增量C DRM ioctl 缓冲对拍 %s" % ("全部一致 ✅" if ok else "存在差异 ❌"))
sys.exit(0 if ok else 1)

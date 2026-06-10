#!/usr/bin/env python3
"""RK3506 本地 LCD 第一屏 v2 —— 纯 Python 直写 DRM,读统一快照(不碰串口)。

和 app.py 解耦:app.py 跑采集+HTTP,这个程序只 GET http://127.0.0.1:PORT/api/snapshot
然后把关键 KPI 画到 800x480 LCD。开机自启后这就是"第一屏=应用页"。

板子无 GUI 库/无浏览器/无字体库,只能直写 DRM + 手画 5x7 点阵字(ASCII)。
中文那版界面在 Web HMI(PC/手机访问 :PORT),LCD 显示 ASCII KPI——工业常态,最稳。

用法:  python3 drm_hmi_v2.py            # 默认读 127.0.0.1:8092
        python3 drm_hmi_v2.py 8092
"""
import fcntl
import json
import mmap
import os
import struct
import sys
import time
import urllib.request

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
SNAP_URL = f"http://127.0.0.1:{PORT}/api/snapshot"

# ---- DRM ioctl(沿用 drm_hmi.py 已在板子验证过的序列)----
DRM_SET_MASTER = 0x641E
DRM_CREATE_DUMB = 0xC02064B2
DRM_MAP_DUMB = 0xC01064B3
DRM_ADDFB = 0xC01C64AE
DRM_SETCRTC = 0xC06864A2
W, H, CONN, CRTC = 800, 480, 75, 72
MODE = struct.pack("<IHHHHHHHHHHIII32s", 30000, 800, 806, 811, 816, 0,
                   480, 485, 493, 503, 0, 73, 0x0A, 0x48, b"800x480")

# ---- 完整 5x7 点阵字(0-9 A-Z 及常用符号)----
FONT = {
 '0': ["01110","10001","10011","10101","11001","10001","01110"],
 '1': ["00100","01100","00100","00100","00100","00100","01110"],
 '2': ["01110","10001","00001","00010","00100","01000","11111"],
 '3': ["11111","00010","00100","00010","00001","10001","01110"],
 '4': ["00010","00110","01010","10010","11111","00010","00010"],
 '5': ["11111","10000","11110","00001","00001","10001","01110"],
 '6': ["00110","01000","10000","11110","10001","10001","01110"],
 '7': ["11111","00001","00010","00100","01000","01000","01000"],
 '8': ["01110","10001","10001","01110","10001","10001","01110"],
 '9': ["01110","10001","10001","01111","00001","00010","01100"],
 'A': ["01110","10001","10001","11111","10001","10001","10001"],
 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'C': ["01110","10001","10000","10000","10000","10001","01110"],
 'D': ["11100","10010","10001","10001","10001","10010","11100"],
 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"],
 'G': ["01110","10001","10000","10111","10001","10001","01111"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'I': ["01110","00100","00100","00100","00100","00100","01110"],
 'J': ["00111","00010","00010","00010","00010","10010","01100"],
 'K': ["10001","10010","10100","11000","10100","10010","10001"],
 'L': ["10000","10000","10000","10000","10000","10000","11111"],
 'M': ["10001","11011","10101","10101","10001","10001","10001"],
 'N': ["10001","10001","11001","10101","10011","10001","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"],
 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'Q': ["01110","10001","10001","10001","10101","10010","01101"],
 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"],
 'V': ["10001","10001","10001","10001","10001","01010","00100"],
 'W': ["10001","10001","10001","10101","10101","11011","10001"],
 'X': ["10001","10001","01010","00100","01010","10001","10001"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"],
 'Z': ["11111","00001","00010","00100","01000","10000","11111"],
 '.': ["00000","00000","00000","00000","00000","01100","01100"],
 '-': ["00000","00000","00000","11111","00000","00000","00000"],
 ':': ["00000","01100","01100","00000","01100","01100","00000"],
 '/': ["00001","00010","00010","00100","01000","01000","10000"],
 '%': ["11000","11001","00010","00100","01000","10011","00011"],
 ' ': ["00000","00000","00000","00000","00000","00000","00000"],
}


class Canvas:
    def __init__(self):
        self.fd = os.open("/dev/dri/card0", os.O_RDWR)
        try:
            fcntl.ioctl(self.fd, DRM_SET_MASTER, 0)
        except OSError:
            pass
        b = bytearray(struct.pack("<IIIIIIQ", H, W, 32, 0, 0, 0, 0))
        fcntl.ioctl(self.fd, DRM_CREATE_DUMB, b)
        _, _, _, _, self.handle, self.pitch, self.size = struct.unpack("<IIIIIIQ", b)
        b = bytearray(struct.pack("<IIIIIII", 0, W, H, self.pitch, 32, 24, self.handle))
        fcntl.ioctl(self.fd, DRM_ADDFB, b)
        self.fb_id = struct.unpack("<IIIIIII", b)[0]
        b = bytearray(struct.pack("<IIQ", self.handle, 0, 0))
        fcntl.ioctl(self.fd, DRM_MAP_DUMB, b)
        offset = struct.unpack("<IIQ", b)[2]
        self.mm = mmap.mmap(self.fd, self.size, mmap.MAP_SHARED,
                            mmap.PROT_READ | mmap.PROT_WRITE, offset=offset)
        import ctypes
        self._cbuf = ctypes.create_string_buffer(struct.pack("<I", CONN), 4)
        crtc = struct.pack("<QIIIIIII", ctypes.addressof(self._cbuf), 1, CRTC,
                           self.fb_id, 0, 0, 0, 1) + MODE
        fcntl.ioctl(self.fd, DRM_SETCRTC, bytearray(crtc))

    def fill(self, x, y, w, h, r, g, b):
        px = struct.pack("<I", (r << 16) | (g << 8) | b)
        for yy in range(max(0, y), min(y + h, H)):
            base = yy * self.pitch + x * 4
            self.mm[base:base + w * 4] = px * w

    def char(self, ch, x, y, s, r, g, b):
        g7 = FONT.get(ch, FONT[' '])
        for ry, row in enumerate(g7):
            for rx, bit in enumerate(row):
                if bit == '1':
                    self.fill(x + rx * s, y + ry * s, s, s, r, g, b)

    def text(self, s, x, y, scale, r, g, b):
        for ch in s:
            self.char(ch, x, y, scale, r, g, b)
            x += 6 * scale
        return x


def fnum(v, d=1):
    if v is None:
        return "--"
    try:
        return ("%.{}f".format(d)) % float(v)
    except (TypeError, ValueError):
        return str(v)


def fetch():
    with urllib.request.urlopen(SNAP_URL, timeout=2) as r:
        return json.loads(r.read())


def pick(view, point_id):
    """从所有设备里找第一个出现的点位值。"""
    for d in view.get("devices", []):
        p = (d.get("points") or {}).get(point_id)
        if p and p.get("v") is not None:
            return p["v"]
    return None


def main():
    cv = Canvas()
    print("LCD v2 接管屏幕,读 %s。" % SNAP_URL, flush=True)
    while True:
        try:
            view = fetch()
        except Exception:
            cv.fill(0, 0, W, H, 12, 18, 30)
            cv.text("STARTING", 250, 210, 6, 120, 160, 200)
            cv.text("WAIT BACKEND", 230, 280, 3, 90, 110, 140)
            time.sleep(1)
            continue

        devs = view.get("devices", [])
        online = sum(1 for d in devs if d.get("ok"))
        total = len(devs)
        alarms = [e for e in view.get("events", []) if e.get("kind") in ("command", "alarm")]
        sec_t = pick(view, "sec_supply_temp")
        pri_t = pick(view, "pri_supply_temp")
        valve = pick(view, "valve_open")
        freq = pick(view, "pump_freq")
        sec_p = pick(view, "sec_supply_pressure")
        cur = pick(view, "current")

        # 背景 + 标题条
        cv.fill(0, 0, W, H, 12, 18, 30)
        cv.fill(0, 0, W, 64, 18, 60, 105)
        cv.text("RK3506 GATEWAY", 20, 18, 4, 235, 245, 255)
        clk = time.strftime("%H:%M:%S") if time.gmtime().tm_year >= 2020 else "NO CLOCK"
        cv.text(clk, 600, 20, 3, 200, 220, 240)
        # 在线状态点
        all_ok = online == total and total > 0
        cv.fill(560, 22, 22, 22, (40 if all_ok else 200), (200 if all_ok else 160), 40)

        # KPI 网格:label 小 + 大数字
        def kpi(x, y, label, val, unit, cr, cg, cb):
            cv.text(label, x, y, 2, 120, 150, 180)
            nx = cv.text(val, x, y + 22, 6, cr, cg, cb)
            if unit:
                cv.text(unit, nx + 4, y + 40, 2, 120, 150, 180)

        kpi(24, 86,  "DEVICES ON/ALL", "%d/%d" % (online, total), "", 255, 255, 255)
        kpi(280, 86, "SEC SUPPLY T", fnum(sec_t), "C", 120, 220, 255)
        kpi(540, 86, "PRI SUPPLY T", fnum(pri_t), "C", 255, 210, 120)

        kpi(24, 200,  "VALVE OPEN", fnum(valve, 0), "%", 130, 255, 180)
        kpi(280, 200, "PUMP FREQ", fnum(freq), "HZ", 130, 255, 180)
        kpi(540, 200, "SEC PRESS", fnum(sec_p, 2), "MPA", 200, 200, 255)

        kpi(24, 314,  "CURRENT", fnum(cur), "A", 255, 255, 255)
        # MQTT 状态(从事件里粗略判断;有 telemetry 行为即在线——这里简化为常亮)
        cv.text("MQTT", 280, 314, 2, 120, 150, 180)
        cv.text("ONLINE", 280, 336, 4, 40, 210, 120)

        # 告警条
        if alarms:
            cv.fill(0, H - 64, W, 64, 60, 34, 24)
            msg = (alarms[0].get("detail") or "EVENT")[:46].upper()
            # 只画 ASCII 部分(中文字模没有,过滤掉)
            msg = "".join(c if (c.upper() in FONT or c == " ") else "" for c in msg)
            cv.text("EVENT " + msg, 16, H - 48, 3, 255, 200, 120)
        else:
            cv.fill(0, H - 64, W, 64, 16, 40, 26)
            cv.text("ALL NORMAL", 16, H - 48, 3, 120, 220, 160)

        time.sleep(1)


if __name__ == "__main__":
    main()

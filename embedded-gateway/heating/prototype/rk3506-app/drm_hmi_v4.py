#!/usr/bin/env python3
"""RK3506 本地第一屏 v4 —— edge-os 风格图形仪表盘 + 触摸控制。

在 v3 基础上加:读 Goodix 触摸屏(/dev/input/event0),点 −/+ 按钮下发设定值。
触摸坐标 0..799/0..479,与屏幕 1:1(已 ioctl 实测)。控制走本机 /api/command(安全校验)。

用法:  python3 drm_hmi_v4.py [port]
"""
import fcntl
import json
import mmap
import os
import struct
import sys
import threading
import time
import urllib.request

import dashboard

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
BASE = "http://127.0.0.1:%d" % PORT
TOUCH_DEV = "/dev/input/event0"

DRM_SET_MASTER = 0x641E
DRM_CREATE_DUMB = 0xC02064B2
DRM_MAP_DUMB = 0xC01064B3
DRM_ADDFB = 0xC01C64AE
DRM_SETCRTC = 0xC06864A2
W, H, CONN, CRTC = 800, 480, 75, 72
MODE = struct.pack("<IHHHHHHHHHHIII32s", 30000, 800, 806, 811, 816, 0,
                   480, 485, 493, 503, 0, 73, 0x0A, 0x48, b"800x480")


class Screen:
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

    def blit_rgb(self, rgb):
        out = bytearray(W * H * 4)
        out[0::4] = rgb[2::3]
        out[1::4] = rgb[1::3]
        out[2::4] = rgb[0::3]
        if self.pitch == W * 4:
            self.mm[0:W * H * 4] = out
        else:
            for y in range(H):
                self.mm[y * self.pitch:y * self.pitch + W * 4] = out[y * W * 4:(y + 1) * W * 4]


class Touch(threading.Thread):
    """读 Goodix 触摸屏,松手即一次 tap,回调 on_tap(x, y)。"""
    EVFMT, SZ = "<IIHHi", 16
    EV_KEY, EV_ABS, BTN_TOUCH = 1, 3, 0x14A

    def __init__(self, on_tap):
        super().__init__(daemon=True)
        self.on_tap = on_tap

    def run(self):
        try:
            fd = os.open(TOUCH_DEV, os.O_RDONLY)
        except OSError as exc:
            print("[touch] 打不开 %s: %s" % (TOUCH_DEV, exc), flush=True)
            return
        x = y = 0
        while True:
            data = os.read(fd, self.SZ)
            if len(data) < self.SZ:
                continue
            _, _, typ, code, val = struct.unpack(self.EVFMT, data)
            if typ == self.EV_ABS:
                if code in (0x00, 0x35):
                    x = val
                elif code in (0x01, 0x36):
                    y = val
            elif typ == self.EV_KEY and code == self.BTN_TOUCH and val == 0:
                try:
                    self.on_tap(x, y)
                except Exception as exc:
                    print("[touch] on_tap err:", exc, flush=True)


def fetch():
    with urllib.request.urlopen(BASE + "/api/snapshot", timeout=2) as r:
        return json.loads(r.read())


def post_cmd(point_id, value):
    body = json.dumps({"point_id": point_id, "value": value}).encode()
    req = urllib.request.Request(BASE + "/api/command", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return json.loads(r.read())
    except Exception as exc:
        print("[ctl] post err:", exc, flush=True)
        return {"ok": False}


def main():
    scr = Screen()
    targets = {}
    state = {"buttons": [], "view": {"devices": []}, "page": "overview"}
    dirty = threading.Event()

    def on_tap(x, y):
        for b in state["buttons"]:
            bx, by, bw, bh = b["rect"]
            if bx - 8 <= x <= bx + bw + 8 and by - 8 <= y <= by + bh + 8:
                if "nav" in b:                       # 侧栏导航:切页
                    state["page"] = b["nav"]
                    print("[nav] → %s" % b["nav"], flush=True)
                    dirty.set()
                    return
                base = targets.get(b["fb"])
                if base is None:
                    cur = dashboard.pick(state["view"], b["fb"])
                    base = round(cur) if cur is not None else b["lo"]
                new = max(b["lo"], min(b["hi"], base + b["delta"]))
                targets[b["fb"]] = new
                print("[ctl] tap → %s = %s" % (b["sp"], new), flush=True)
                post_cmd(b["sp"], new)
                dirty.set()
                return

    Touch(on_tap).start()
    print("LCD v4(触摸仪表盘)接管屏幕,读 %s/api/snapshot。" % BASE, flush=True)
    while True:
        try:
            state["view"] = fetch()
        except Exception:
            state["view"] = {"devices": [], "events": [{"detail": "正在连接后端…"}]}
        clock = time.strftime("%H:%M:%S") if time.gmtime().tm_year >= 2020 else "--:--:--"
        fb, buttons = dashboard.render(state["view"], clock=clock, targets=targets,
                                       page=state["page"])
        state["buttons"] = buttons
        scr.blit_rgb(fb.buf)
        dirty.wait(1.0)          # 1Hz 刷新,触摸即时重绘
        dirty.clear()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""RK3506 本地第一屏 v3 —— edge-os 风格图形仪表盘,直写 DRM。

读 /api/snapshot,用 dashboard.render() 画一帧 800x480 RGB,blit 到 DRM。
DRM 初始化沿用已在板验证的 drm_hmi_v2 序列;中文用 cjk_font 点阵,无需字体库/浏览器。

用法:  python3 drm_hmi_v3.py [port]   # 默认读 127.0.0.1:8092
"""
import fcntl
import json
import mmap
import os
import struct
import sys
import time
import urllib.request

import dashboard

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
SNAP_URL = "http://127.0.0.1:%d/api/snapshot" % PORT

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
        """RGB(W*H*3) → DRM 32bpp(BGRX)。用扩展切片做整块转换,C 速度。"""
        out = bytearray(W * H * 4)
        out[0::4] = rgb[2::3]   # B
        out[1::4] = rgb[1::3]   # G
        out[2::4] = rgb[0::3]   # R
        if self.pitch == W * 4:
            self.mm[0:W * H * 4] = out
        else:
            for y in range(H):
                self.mm[y * self.pitch:y * self.pitch + W * 4] = out[y * W * 4:(y + 1) * W * 4]


def fetch():
    with urllib.request.urlopen(SNAP_URL, timeout=2) as r:
        return json.loads(r.read())


def main():
    scr = Screen()
    print("LCD v3(图形仪表盘)接管屏幕,读 %s。" % SNAP_URL, flush=True)
    while True:
        try:
            view = fetch()
        except Exception:
            view = {"devices": [], "events": [{"detail": "正在连接后端…"}]}
        clock = time.strftime("%H:%M:%S") if time.gmtime().tm_year >= 2020 else "--:--:--"
        fb = dashboard.render(view, clock=clock)
        scr.blit_rgb(fb.buf)
        time.sleep(1)


if __name__ == "__main__":
    main()

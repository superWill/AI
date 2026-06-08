#!/usr/bin/env python3
"""RK3506 本地 HMI —— 纯 Python 直写 DRM 显存,在 800x480 LCD 上画实时仪表盘。

这块 buildroot 板没有 /dev/fb0、没浏览器、没 GUI 库、没编译器,只有 DRM(/dev/dri/card0)
和 libdrm。于是直接用 ioctl 创建 dumb buffer + 设模式 + 手写位图字体画大字。
数据来源:作 Modbus 主站从 ttyS1 读(和 gateway 一样),显示温度/湿度/电压。

先停掉厂家 demo 释放屏幕:  kill lv_demo
然后:  python3 drm_hmi.py /dev/ttyS1
"""
import fcntl
import mmap
import os
import select
import struct
import sys
import termios
import time

# ---- DRM ioctl(type 'd'=0x64;号和结构体大小按内核固定值算出) ----
DRM_SET_MASTER = 0x641E
DRM_CREATE_DUMB = 0xC02064B2
DRM_MAP_DUMB = 0xC01064B3
DRM_ADDFB = 0xC01C64AE
DRM_SETCRTC = 0xC06864A2

W, H, CONN, CRTC = 800, 480, 75, 72
# 800x480 模式时序(取自 modetest):clock(kHz) h:800/806/811/816 v:480/485/493/503
MODE = struct.pack("<IHHHHHHHHHHIII32s", 30000, 800, 806, 811, 816, 0,
                   480, 485, 493, 503, 0, 73, 0x0A, 0x48, b"800x480")

# ---- 5x7 位图字体(只编需要的字符)----
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
 '.': ["00000","00000","00000","00000","00000","01100","01100"],
 '-': ["00000","00000","00000","11111","00000","00000","00000"],
 '%': ["11000","11001","00010","00100","01000","10011","00011"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'V': ["10001","10001","10001","10001","10001","01010","00100"],
 'C': ["01110","10001","10000","10000","10000","10001","01110"],
 ' ': ["00000","00000","00000","00000","00000","00000","00000"],
}

# ---- Modbus 主站(纯标准库,和 gateway 一致)----
BAUD9600 = termios.B9600


def crc16(d):
    c = 0xFFFF
    for b in d:
        c ^= b
        for _ in range(8):
            c = (c >> 1) ^ 0xA001 if c & 1 else c >> 1
    return struct.pack("<H", c)


def open_serial(dev):
    fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
    a = termios.tcgetattr(fd)
    a[0] = a[1] = a[3] = 0
    a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
    a[4] = a[5] = BAUD9600
    a[6][termios.VMIN] = 0; a[6][termios.VTIME] = 0
    termios.tcsetattr(fd, termios.TCSANOW, a)
    termios.tcflush(fd, termios.TCIOFLUSH)
    return fd


def read_holding(fd, addr, start, count, timeout=0.6):
    body = struct.pack(">BBHH", addr, 0x03, start, count)
    termios.tcflush(fd, termios.TCIOFLUSH)
    os.write(fd, body + crc16(body))
    buf, dl = b"", time.time() + timeout
    while time.time() < dl:
        r, _, _ = select.select([fd], [], [], dl - time.time())
        if not r:
            continue
        buf += os.read(fd, 256)
        time.sleep(0.03)
        r2, _, _ = select.select([fd], [], [], 0)
        if r2:
            buf += os.read(fd, 256)
        break
    if len(buf) < 5 or crc16(buf[:-2]) != buf[-2:] or buf[1] & 0x80:
        return None
    n = buf[2]
    return [struct.unpack(">H", buf[3 + i:5 + i])[0] for i in range(0, n, 2)]


# ---- DRM 画布 ----
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
        self._cbuf = ctypes.create_string_buffer(struct.pack("<I", CONN), 4)  # 连接器数组,保活
        crtc = struct.pack("<QIIIIIII", ctypes.addressof(self._cbuf), 1, CRTC,
                           self.fb_id, 0, 0, 0, 1) + MODE
        fcntl.ioctl(self.fd, DRM_SETCRTC, bytearray(crtc))

    def fill(self, x, y, w, h, r, g, b):
        px = struct.pack("<I", (r << 16) | (g << 8) | b)
        for yy in range(y, min(y + h, H)):
            base = yy * self.pitch + x * 4
            self.mm[base:base + w * 4] = px * w

    def char(self, ch, x, y, s, r, g, b):
        g7 = FONT.get(ch, FONT[' '])
        px = struct.pack("<I", (r << 16) | (g << 8) | b)
        for ry, row in enumerate(g7):
            for rx, bit in enumerate(row):
                if bit == '1':
                    self.fill(x + rx * s, y + ry * s, s, s, r, g, b)

    def text(self, s, x, y, scale, r, g, b):
        for ch in s:
            self.char(ch, x, y, scale, r, g, b)
            x += 6 * scale
        return x


def fmt(v, w=5):
    return ("---" if v is None else "%.1f" % v).rjust(w)


def main():
    dev = sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyS1"
    ser = open_serial(dev)
    cv = Canvas()
    print("HMI 已接管屏幕,开始绘制。Ctrl-C 退出。", flush=True)
    try:
        while True:
            th = read_holding(ser, 1, 0, 2)          # 热表:温度/湿度
            volt = read_holding(ser, 2, 0, 1)        # 电表:电压
            t = th[0] / 10 if th else None
            h = th[1] / 10 if th else None
            u = volt[0] / 10 if volt else None
            # 背景 + 标题条
            cv.fill(0, 0, W, H, 12, 18, 30)
            cv.fill(0, 0, W, 70, 20, 70, 120)
            cv.text("RK3506 GW", 24, 18, 5, 235, 245, 255)
            # 三行大数字
            cv.text("T", 30, 110, 7, 120, 220, 255)
            cv.text(fmt(t), 150, 110, 7, 255, 255, 255)
            cv.text("C", 560, 110, 7, 120, 220, 255)
            cv.text("H", 30, 230, 7, 120, 255, 180)
            cv.text(fmt(h), 150, 230, 7, 255, 255, 255)
            cv.text("%", 560, 230, 7, 120, 255, 180)
            cv.text("V", 30, 350, 7, 255, 210, 120)
            cv.text(fmt(u), 130, 350, 7, 255, 255, 255)
            cv.text("V", 600, 350, 7, 255, 210, 120)
            # 在线状态点:绿=有数据,红=无
            cv.fill(740, 26, 30, 30, (40 if th else 200), (200 if th else 40), 40)
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nHMI 退出。")


if __name__ == "__main__":
    main()

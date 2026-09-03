#!/usr/bin/env python3
"""增量A 对拍:Go fb == Python dashboard.FB(同场景逐像素)。

  python3 ui_lcd_harness.py <go_raw.rgb>
"""
import sys
import dashboard as D

f = D.FB(800, 480)
f.clear((15, 23, 42))
f.round_rect(10, 10, 120, 70, (30, 41, 59), 8, (56, 189, 248))
f.text("温度 52.3℃ ABC", 20, 90, 2, (226, 232, 240))
f.ring(200, 200, 40, 28, 0.6, (34, 197, 94), 270, 135)
f.text("二次供水温度 急停 缺水 反馈", 20, 140, 1, (148, 163, 184))
f.text_right("7/8 在线", 790, 20, 1, (245, 158, 11))
py = bytes(f.buf)
go = open(sys.argv[1], "rb").read()

print("py %d 字节, go %d 字节" % (len(py), len(go)))
if py == go:
    print("=> 增量A FB+字库逐像素一致 ✅")
    sys.exit(0)
diff = sum(1 for a, b in zip(py, go) if a != b)
print("不一致字节: %d / %d (%.3f%%)" % (diff, len(py), 100.0 * diff / len(py)))
for i, (a, b) in enumerate(zip(py, go)):
    if a != b:
        px = i // 3
        print("首差 像素 (%d,%d) py=%s go=%s" % (px % 800, px // 800, py[i:i + 3].hex(), go[i:i + 3].hex()))
        break
sys.exit(1)

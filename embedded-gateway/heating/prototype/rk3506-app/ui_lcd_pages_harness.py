#!/usr/bin/env python3
"""增量B 对拍:Go lcdRender == Python dashboard.render(5 页逐像素)。

  python3 ui_lcd_pages_harness.py [gatewayc_host_bin]

向 Go 场景注入 _porder(= Python dict 插入序),消除 Go map 遍历随机性。
"""
import json
import os
import subprocess
import sys
import tempfile

import dashboard as D

GATEWAYC = sys.argv[1] if len(sys.argv) > 1 else "./gateway-go/gatewayc-host"
CLOCK = "14:32:07"
TARGETS = {"valve_open": 70, "pump_freq": 40}
PAGES = ["overview", "monitor", "nodes", "control", "settings"]

D.configure_display(None)
view = D._sample_view()


def with_order(v):
    v2 = json.loads(json.dumps(v))
    for d in v2["devices"]:
        d["_porder"] = list((d.get("points") or {}).keys())
    return v2


tmp = tempfile.mkdtemp()
allok = True
for page in PAGES:
    scene = {"view": with_order(view), "clock": CLOCK, "targets": TARGETS,
             "page": page, "display_model": None}
    sp = os.path.join(tmp, "scene.json")
    rp = os.path.join(tmp, "go_%s.rgb" % page)
    with open(sp, "w") as fh:
        json.dump(scene, fh)
    r = subprocess.run([GATEWAYC, "lcdrender", sp, rp], capture_output=True, text=True)
    if r.returncode != 0:
        print("page %-9s GO 渲染失败: %s" % (page, r.stderr.strip()))
        allok = False
        continue
    go = open(rp, "rb").read()
    fb, _ = D.render(view, clock=CLOCK, targets=dict(TARGETS), page=page)
    py = bytes(fb.buf)
    if py == go:
        print("page %-9s 逐像素一致 ✅ (%d 字节)" % (page, len(py)))
        continue
    allok = False
    diff = sum(1 for a, b in zip(py, go) if a != b)
    print("page %-9s 不一致 %d/%d (%.3f%%)" % (page, diff, len(py), 100.0 * diff / len(py)))
    for i, (a, b) in enumerate(zip(py, go)):
        if a != b:
            px = i // 3
            print("  首差像素(%d,%d) py=%s go=%s" %
                  (px % 800, px // 800, py[i:i + 3].hex(), go[i:i + 3].hex()))
            break

print("=> 增量B 5 页对拍 %s" % ("全部一致 ✅" if allok else "存在差异 ❌"))
sys.exit(0 if allok else 1)

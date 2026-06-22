#!/usr/bin/env python3
"""edge-os 风格本地仪表盘(多页 + 触摸导航,纯标准库)。

把统一点表快照画成 800x480 RGB 帧。侧栏可点导航:总览/监控/设备/控制/设置。
- 板子:drm_hmi_v4.py 调 render(page=...) blit 到 DRM,读触摸切页/控制。
- 开发:本文件 __main__ 把每页渲染成 PNG 预览。
中文用 GNU Unifont 子集(cjk_font.py)。render 返回 (fb, buttons);
buttons 元素含 "rect";导航键含 "nav"=页面id,控制键含 "sp"/"delta"。
"""
import math
import struct
import zlib

try:
    from cjk_font import GLYPHS
except ImportError:
    GLYPHS = {}

W, H = 800, 480
BG = (15, 23, 42)
SIDEBAR = (12, 18, 33)
CARD = (30, 41, 59)
CARD2 = (23, 33, 52)
LINE = (51, 65, 85)
INK = (226, 232, 240)
MUTED = (148, 163, 184)
BLUE = (56, 189, 248)
BLUE2 = (37, 99, 235)
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
TRACK = (40, 52, 74)

NAV = [("overview", "总览"), ("monitor", "监控"), ("nodes", "设备"),
       ("control", "控制"), ("settings", "设置")]
PAGE_TITLE = {"overview": "总览", "monitor": "数据监控", "nodes": "设备管理",
              "control": "就地控制", "settings": "系统设置"}

CONTROLS = [
    ("二次供温", "sec_supply_temp", "sec_supply_temp_sp", 20, 75, 2, "℃", BLUE),
    ("阀位开度", "valve_open", "valve_open_sp", 0, 100, 5, "%", GREEN),
    ("循环泵频率", "pump_freq", "pump_freq_sp", 0, 50, 2, "Hz", AMBER),
]

# 编译产物 display_model 驱动的卡片(监控页用)。空=回退到平铺点表。
# 由 configure_display() 从 display_model.json 派生;page/card 模型在本地 HMI 才真正发挥。
DISPLAY_CARDS = []


def configure_display(display_model):
    """从 display_model.json 派生监控页卡片:按 (页序, card priority) 排序,
    每卡片含标题与点位列表。无 display_model 则清空,监控页回退平铺点表。"""
    DISPLAY_CARDS.clear()
    if not display_model:
        return
    items = []
    for pi, page in enumerate(display_model.get("pages", [])):
        for card in page.get("cards", []):
            # 优先用人类可读 label,缺省回退 card id
            title = card.get("label") or card.get("card", "")
            fields = [(f["point_id"], f.get("label") or f["point_id"])
                      for f in card.get("fields", []) if f.get("point_id")]
            items.append(((pi, card.get("priority", 50)), title, fields))
    items.sort(key=lambda t: t[0])
    for _, title, fields in items:
        DISPLAY_CARDS.append({"title": title, "fields": fields})


class FB:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.buf = bytearray(w * h * 3)

    def clear(self, c):
        row = bytes(c) * self.w
        for y in range(self.h):
            self.buf[y * self.w * 3:(y + 1) * self.w * 3] = row

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + (x1 - x0) * 3] = row

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def round_rect(self, x, y, w, h, c, r=8, border=None):
        self.rect(x + r, y, w - 2 * r, h, c)
        self.rect(x, y + r, w, h - 2 * r, c)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        self.px(cx + dx, cy + dy, c)
        if border:
            self.hline(x + r, x + w - r, y, border)
            self.hline(x + r, x + w - r, y + h - 1, border)
            self.vline(y + r, y + h - r, x, border)
            self.vline(y + r, y + h - r, x + w - 1, border)

    def hline(self, x0, x1, y, c):
        self.rect(x0, y, x1 - x0, 1, c)

    def vline(self, y0, y1, x, c):
        self.rect(x, y0, 1, y1 - y0, c)

    def ring(self, cx, cy, r_out, r_in, value_frac, vcolor, sweep=270, start=135):
        value_frac = max(0.0, min(1.0, value_frac))
        ro2, ri2 = r_out * r_out, r_in * r_in
        for y in range(cy - r_out, cy + r_out + 1):
            for x in range(cx - r_out, cx + r_out + 1):
                dx, dy = x - cx, y - cy
                d2 = dx * dx + dy * dy
                if not (ri2 <= d2 <= ro2):
                    continue
                ang = (math.degrees(math.atan2(dy, dx)) + 360) % 360
                rel = (ang - start + 360) % 360
                if rel <= sweep:
                    self.px(x, y, vcolor if rel <= sweep * value_frac else TRACK)

    def char(self, ch, x, y, scale, c):
        bm = GLYPHS.get(ch)
        if bm is None:
            return 8 * scale
        gw = 16 if len(bm) == 64 else 8
        bpr = gw // 8
        for ry in range(16):
            val = int(bm[ry * bpr * 2:(ry + 1) * bpr * 2], 16)
            for rx in range(gw):
                if val & (1 << (gw - 1 - rx)):
                    self.rect(x + rx * scale, y + ry * scale, scale, scale, c)
        return gw * scale

    def text(self, s, x, y, scale, c):
        for ch in s:
            x += self.char(ch, x, y, scale, c) + (1 if scale <= 1 else scale)
        return x

    def text_w(self, s, scale):
        w = 0
        for ch in s:
            bm = GLYPHS.get(ch)
            gw = (16 if (bm and len(bm) == 64) else 8)
            w += gw * scale + (1 if scale <= 1 else scale)
        return w

    def text_center(self, s, cx, y, scale, c):
        self.text(s, cx - self.text_w(s, scale) // 2, y, scale, c)

    def text_right(self, s, rx, y, scale, c):
        self.text(s, rx - self.text_w(s, scale), y, scale, c)

    def to_png(self, path):
        raw = bytearray()
        for y in range(self.h):
            raw.append(0)
            raw.extend(self.buf[y * self.w * 3:(y + 1) * self.w * 3])
        def chunk(typ, data):
            return (struct.pack(">I", len(data)) + typ + data
                    + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0))
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        open(path, "wb").write(png)


def fnum(v, d=1):
    if v is None:
        return "--"
    try:
        return ("%.{}f".format(d)) % float(v)
    except (TypeError, ValueError):
        return str(v)


def pick(view, pid):
    for d in view.get("devices", []):
        p = (d.get("points") or {}).get(pid)
        if p and p.get("v") is not None:
            return p["v"]
    return None


def all_points(view):
    out = []
    for d in view.get("devices", []):
        for pid, p in (d.get("points") or {}).items():
            out.append((d.get("name", ""), pid, p.get("v"), p.get("u", ""), p.get("q", "")))
    return out


def point_of(view, pid):
    for d in view.get("devices", []):
        p = (d.get("points") or {}).get(pid)
        if p is not None:
            return p
    return None


# ---- 侧栏(可点导航) ----
def draw_sidebar(fb, page, buttons):
    fb.rect(0, 0, 76, H, SIDEBAR)
    fb.round_rect(20, 12, 36, 32, BLUE2, r=8)
    fb.text_center("N", 38, 18, 2, (255, 255, 255))
    for i, (pid, label) in enumerate(NAV):
        y = 66 + i * 78
        active = (pid == page)
        fb.round_rect(8, y, 60, 68, (19, 35, 58) if active else SIDEBAR, r=10,
                      border=BLUE if active else None)
        fb.round_rect(26, y + 8, 24, 24, BLUE2 if active else CARD2, r=6,
                      border=None if active else LINE)
        fb.rect(32, y + 14, 12, 3, (255, 255, 255) if active else MUTED)
        fb.rect(32, y + 19, 12, 3, (255, 255, 255) if active else MUTED)
        fb.text_center(label, 38, y + 40, 1, INK if active else MUTED)
        buttons.append({"rect": (4, y, 68, 72), "nav": pid})


def draw_header(fb, view, clock, title):
    fb.rect(76, 0, W - 76, 52, CARD2)
    fb.hline(76, W, 52, LINE)
    fb.text(title, 92, 16, 2, INK)
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    total = len(devs)
    clk_w = fb.text_w(clock, 1)
    fb.text(clock, W - clk_w - 14, 18, 1, MUTED)
    pc = GREEN if (online == total and total) else AMBER
    pl = "在线 %d/%d" % (online, total)
    pw = fb.text_w(pl, 1) + 34
    px = W - clk_w - 14 - pw - 14
    fb.round_rect(px, 14, pw, 24, (20, 45, 30) if pc == GREEN else (50, 38, 16), r=12)
    fb.rect(px + 12, 23, 7, 7, pc)
    fb.text(pl, px + 24, 17, 1, pc)


def _kpi_row(fb, view):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    total = len(devs)
    pts = sum(len(d.get("points") or {}) for d in devs)
    cx0, cy0, cw, ch, gap = 88, 64, 168, 76, 12
    kpis = [("接入设备", str(total), "台", BLUE),
            ("在线", "%d/%d" % (online, total), "", GREEN if online == total else AMBER),
            ("采集点位", str(pts), "点", BLUE),
            ("上行 MQTT", "在线", "", GREEN)]
    for i, (label, val, unit, col) in enumerate(kpis):
        x = cx0 + i * (cw + gap)
        fb.round_rect(x, cy0, cw, ch, CARD, r=10, border=LINE)
        fb.text(label, x + 14, cy0 + 10, 1, MUTED)
        vx = fb.text(val, x + 14, cy0 + 32, 3, col)
        if unit:
            fb.text(unit, vx + 6, cy0 + 46, 1, MUTED)


def _device_list(fb, view, x, y, w, h):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    fb.round_rect(x, y, w, h, CARD, r=10, border=LINE)
    fb.text("接入设备", x + 14, y + 12, 1, MUTED)
    fb.text_right("%d/%d 在线" % (online, len(devs)), x + w - 14, y + 12, 1, MUTED)
    ry = y + 36
    for d in devs[: (h - 40) // 28]:
        ok = d.get("ok")
        fb.rect(x + 16, ry + 7, 8, 8, GREEN if ok else RED)
        fb.text(d.get("name", "")[:9], x + 32, ry + 2, 1, INK)
        first = next((("%s %s" % (fnum(p["v"]), p.get("u", "")))
                      for p in (d.get("points") or {}).values() if p.get("v") is not None), "--")
        fb.text_right(first, x + w - 14, ry + 2, 1, INK if ok else MUTED)
        fb.hline(x + 14, x + w - 14, ry + 26, (37, 47, 66))
        ry += 28


def _status_bar(fb, view):
    by = 424
    events = view.get("events", [])
    msg = events[0].get("detail") if events else None
    if msg:
        fb.round_rect(88, by, W - 88 - 12, 44, CARD2, r=10)
        fb.rect(104, by + 17, 8, 8, AMBER)
        fb.text(("事件 " + msg)[:42], 124, by + 13, 1, INK)
    else:
        fb.round_rect(88, by, W - 88 - 12, 44, CARD2, r=10)
        fb.rect(104, by + 17, 8, 8, GREEN)
        fb.text("系统正常 · 采集与上行运行中", 124, by + 13, 1, GREEN)


# ---- 各页面 ----
def page_overview(fb, view, targets, buttons):
    _kpi_row(fb, view)
    gx0, gy = 88, 152
    fb.round_rect(gx0, gy, 332, 252, CARD, r=10, border=LINE)
    fb.text("关键运行参数", gx0 + 16, gy + 12, 1, MUTED)
    gauges = [("二次供温", pick(view, "sec_supply_temp"), 0, 80, "℃", BLUE),
              ("阀位开度", pick(view, "valve_open"), 0, 100, "%", GREEN),
              ("泵频率", pick(view, "pump_freq"), 0, 50, "Hz", AMBER)]
    for (label, val, lo, hi, unit, col), cxp in zip(gauges, (gx0 + 70, gx0 + 166, gx0 + 262)):
        frac = 0 if val is None else (float(val) - lo) / (hi - lo)
        fb.ring(cxp, gy + 120, 44, 33, frac, col)
        fb.text_center(fnum(val, 0 if unit == "%" else 1), cxp, gy + 108, 2, INK)
        fb.text_center(unit, cxp, gy + 128, 1, MUTED)
        fb.text_center(label, cxp, gy + 178, 1, MUTED)
    _device_list(fb, view, 432, gy, W - 432 - 12, 252)
    _status_bar(fb, view)


def _qcolor(q):
    return GREEN if q in ("good", "") else (AMBER if q in ("stale", "est") else RED)


def page_monitor(fb, view, targets, buttons):
    if DISPLAY_CARDS:
        return _page_monitor_cards(fb, view)
    pts = all_points(view)
    fb.round_rect(88, 64, W - 88 - 12, 400, CARD, r=10, border=LINE)
    fb.text("采集点表 · 共 %d 点" % len(pts), 104, 76, 1, MUTED)
    col_w = (W - 88 - 12 - 24) // 2
    per = 13
    for idx, (dn, pid, v, u, q) in enumerate(pts[: per * 2]):
        col = idx // per
        row = idx % per
        x = 104 + col * (col_w + 8)
        ry = 102 + row * 27
        fb.rect(x, ry + 5, 7, 7, _qcolor(q))
        fb.text(pid[:16], x + 14, ry, 1, INK)
        fb.text_right("%s %s" % (fnum(v), u), x + col_w - 6, ry, 1,
                      INK if q in ("good", "") else MUTED)
        fb.hline(x, x + col_w - 6, ry + 22, (34, 44, 62))


def _page_monitor_cards(fb, view):
    """display_model 驱动:按卡片分组渲染,2 列流式排布,超出可视高度的卡片截断。"""
    col_w = (W - 88 - 12 - 12) // 2
    colx = [88, 88 + col_w + 12]
    coly = [64, 64]
    for c in DISPLAY_CARDS:
        fields = c["fields"][:6]
        ch = 30 + len(fields) * 22 + 8
        ci = 0 if coly[0] <= coly[1] else 1
        x, y = colx[ci], coly[ci]
        if y + ch > 466:
            continue
        fb.round_rect(x, y, col_w, ch, CARD, r=10, border=LINE)
        fb.text(c["title"][:14], x + 14, y + 8, 1, MUTED)
        ry = y + 30
        for pid, label in fields:
            p = point_of(view, pid) or {}
            q = p.get("q", "")
            fb.rect(x + 14, ry + 5, 7, 7, _qcolor(q))
            fb.text(label[:10], x + 24, ry, 1, INK)
            fb.text_right("%s %s" % (fnum(p.get("v")), p.get("u", "")), x + col_w - 14, ry, 1,
                          INK if q in ("good", "") else MUTED)
            ry += 22
        coly[ci] = y + ch + 12


def page_nodes(fb, view, targets, buttons):
    devs = view.get("devices", [])
    cw, chh, gap = (W - 88 - 12 - 12) // 2, 92, 12
    for i, d in enumerate(devs[:8]):
        col, row = i % 2, i // 2
        x = 88 + col * (cw + gap)
        y = 64 + row * (chh + gap)
        ok = d.get("ok")
        fb.round_rect(x, y, cw, chh, CARD, r=10, border=LINE)
        fb.rect(x + 16, y + 18, 10, 10, GREEN if ok else RED)
        fb.text(d.get("name", "")[:12], x + 32, y + 12, 1, INK)
        sc = GREEN if ok else RED
        st = "在线" if ok else "离线"
        fb.round_rect(x + cw - 64, y + 12, 50, 22, (20, 45, 30) if ok else (50, 24, 24), r=11)
        fb.text_center(st, x + cw - 39, y + 15, 1, sc)
        fb.text("类型 %s" % d.get("type", "-"), x + 16, y + 40, 1, MUTED)
        fb.text("地址 %s · 点位 %d" % (d.get("addr", "-"), len(d.get("points") or {})),
                x + 16, y + 62, 1, MUTED)


def page_control(fb, view, targets, buttons):
    fb.round_rect(88, 64, W - 88 - 12, 400, CARD, r=10, border=LINE)
    fb.text("就地控制 · 点 −/+ 下发设定值(安全校验)", 104, 78, 1, MUTED)
    for i, (label, fbid, spid, lo, hi, step, unit, col) in enumerate(CONTROLS):
        ry = 116 + i * 106
        cur = pick(view, fbid)
        tgt = targets.get(fbid)
        if tgt is None:
            tgt = round(cur) if cur is not None else lo
        fb.text(label, 116, ry, 2, INK)
        frac = 0 if cur is None else max(0.0, min(1.0, (float(cur) - lo) / (hi - lo)))
        fb.rect(116, ry + 40, 300, 12, TRACK)
        fb.rect(116, ry + 40, int(300 * frac), 12, col)
        fb.text("当前 %s%s" % (fnum(cur, 0 if unit == "%" else 1), unit), 116, ry + 60, 1, MUTED)
        bm = (470, ry, 70, 70)
        bp = (650, ry, 70, 70)
        fb.round_rect(*bm, CARD2, r=12, border=LINE)
        fb.text_center("-", bm[0] + 35, ry + 12, 3, MUTED)
        fb.round_rect(*bp, (18, 38, 26) if col == GREEN else CARD2, r=12, border=col)
        fb.text_center("+", bp[0] + 35, ry + 12, 3, col)
        fb.text_center(fnum(tgt, 0), 595, ry + 10, 3, INK)
        fb.text_center("设定 " + unit, 595, ry + 58, 1, MUTED)
        buttons.append({"rect": bm, "fb": fbid, "sp": spid, "delta": -step, "lo": lo, "hi": hi})
        buttons.append({"rect": bp, "fb": fbid, "sp": spid, "delta": step, "lo": lo, "hi": hi})


def page_settings(fb, view, targets, buttons):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    pts = sum(len(d.get("points") or {}) for d in devs)
    fb.round_rect(88, 64, W - 88 - 12, 400, CARD, r=10, border=LINE)
    fb.text("系统信息", 104, 78, 1, MUTED)
    rows = [("设备 ID", str(view.get("device_id", "rk3506-gw-01"))),
            ("接入设备", "%d 台(在线 %d)" % (len(devs), online)),
            ("采集点位", "%d 点" % pts),
            ("上行链路", "MQTT 在线"),
            ("本机地址", "192.168.1.10 : 8092"),
            ("应用版本", "nexus-edge gateway v1"),
            ("运行平台", "RK3506 · Buildroot · DRM")]
    for i, (k, v) in enumerate(rows):
        ry = 112 + i * 44
        fb.text(k, 116, ry, 1, MUTED)
        fb.text(v, 320, ry, 1, INK)
        fb.hline(104, W - 24, ry + 28, (34, 44, 62))


PAGES = {"overview": page_overview, "monitor": page_monitor, "nodes": page_nodes,
         "control": page_control, "settings": page_settings}


def render(view, clock="--:--:--", targets=None, page="overview"):
    targets = targets or {}
    buttons = []
    fb = FB()
    fb.clear(BG)
    if page not in PAGES:
        page = "overview"
    draw_sidebar(fb, page, buttons)
    draw_header(fb, view, clock, PAGE_TITLE[page])
    PAGES[page](fb, view, targets, buttons)
    return fb, buttons


def _sample_view():
    def dev(addr, name, typ, pts, ok=True):
        return {"addr": addr, "name": name, "type": typ, "ok": ok, "health": "在线",
                "points": {k: {"v": v, "u": u, "q": "good"} for k, v, u in pts}}
    return {"device_id": "rk3506-gw-01", "devices": [
        dev(1, "1号换热机组", "换热机组", [("pri_supply_temp", 72.3, "℃"), ("sec_supply_temp", 52.3, "℃"),
            ("valve_open", 68, "%"), ("sec_supply_pressure", 0.31, "MPa")]),
        dev(2, "二次侧循环泵", "循环泵", [("pump_run", 1, ""), ("pump_freq", 38.5, "Hz"), ("pump_current", 11.2, "A")]),
        dev(3, "一次侧电动调节阀", "电动调节阀", [("valve_open", 67, "%")]),
        dev(4, "压力模块", "压力传感器", [("sec_supply_pressure", 0.31, "MPa"), ("sec_return_pressure", 0.22, "MPa")]),
        dev(5, "安全IO板", "安全IO", [("estop", 0, ""), ("water_low", 0, "")]),
        dev(6, "热表#6", "热表", [("supply_temp", 71.2, "℃"), ("flow", 35, "m³/h"), ("heat_power", 820, "kW")]),
        dev(7, "电表#7", "电表", [("voltage", 381, "V"), ("current", 12.1, "A")]),
        dev(8, "坏表#8", "热表", [("supply_temp", None, "℃")], ok=False),
    ], "events": []}


if __name__ == "__main__":
    import sys
    page = sys.argv[1] if len(sys.argv) > 1 else "overview"
    fb, buttons = render(_sample_view(), clock="14:32:07",
                         targets={"valve_open": 70, "pump_freq": 40}, page=page)
    out = "/tmp/dash_%s.png" % page
    fb.to_png(out)
    print("rendered", page, "->", out, "buttons:", len(buttons))

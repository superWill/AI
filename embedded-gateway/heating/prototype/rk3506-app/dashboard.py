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
BG = (244, 248, 255)
SIDEBAR = (255, 255, 255)
CARD = (255, 255, 255)
CARD2 = (247, 250, 255)
LINE = (221, 230, 242)
INK = (22, 34, 56)
MUTED = (112, 130, 157)
BLUE = (47, 128, 237)
BLUE2 = (37, 99, 235)
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
RED = (239, 68, 68)
TRACK = (229, 236, 247)
PALE_BLUE = (235, 244, 255)
PALE_GREEN = (232, 249, 241)
PALE_AMBER = (255, 246, 230)
SHADOW = (232, 238, 248)

THEMES = {
    "light": {
        "BG": (244, 248, 255), "SIDEBAR": (255, 255, 255),
        "CARD": (255, 255, 255), "CARD2": (247, 250, 255),
        "LINE": (221, 230, 242), "INK": (22, 34, 56),
        "MUTED": (112, 130, 157), "TRACK": (229, 236, 247),
        "PALE_BLUE": (235, 244, 255), "PALE_GREEN": (232, 249, 241),
        "PALE_AMBER": (255, 246, 230), "SHADOW": (232, 238, 248),
    },
    "dark": {
        "BG": (15, 23, 42), "SIDEBAR": (17, 24, 39),
        "CARD": (30, 41, 59), "CARD2": (37, 50, 70),
        "LINE": (55, 65, 81), "INK": (241, 245, 249),
        "MUTED": (156, 163, 175), "TRACK": (55, 65, 81),
        "PALE_BLUE": (30, 58, 95), "PALE_GREEN": (26, 67, 55),
        "PALE_AMBER": (78, 55, 25), "SHADOW": (12, 18, 32),
    },
}

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
_GLYPH_RUNS = {}


def apply_theme(theme):
    """Apply a process-wide palette before rendering a frame."""
    name = theme if theme in THEMES else "light"
    globals().update(THEMES[name])
    return name


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
        # Draw rounded corners as horizontal spans. The previous implementation
        # visited every corner pixel in Python and allocated bytes for each one,
        # which cost hundreds of milliseconds on RK3506.
        r = max(0, min(r, w // 2, h // 2))
        if not r:
            self.rect(x, y, w, h, c)
            return
        self.rect(x, y + r, w, h - 2 * r, c)
        rr = r * r
        for dy in range(r):
            cy = r - dy
            inset = r - int(math.sqrt(max(0, rr - cy * cy)))
            span = w - inset * 2
            self.rect(x + inset, y + dy, span, 1, c)
            self.rect(x + inset, y + h - 1 - dy, span, 1, c)
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
        cached = _GLYPH_RUNS.get(ch)
        if cached is None:
            gw = 16 if len(bm) == 64 else 8
            bpr = gw // 8
            rows = []
            for ry in range(16):
                val = int(bm[ry * bpr * 2:(ry + 1) * bpr * 2], 16)
                runs = []
                rx = 0
                while rx < gw:
                    if not (val & (1 << (gw - 1 - rx))):
                        rx += 1
                        continue
                    start = rx
                    while rx < gw and val & (1 << (gw - 1 - rx)):
                        rx += 1
                    runs.append((start, rx))
                rows.append(tuple(runs))
            cached = (gw, tuple(rows))
            _GLYPH_RUNS[ch] = cached
        gw, rows = cached
        for ry, runs in enumerate(rows):
            for start, end in runs:
                self.rect(x + start * scale, y + ry * scale,
                          (end - start) * scale, scale, c)
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


def panel(fb, x, y, w, h, r=12, border=True):
    """Reference-inspired white card with a restrained one-pixel shadow."""
    fb.round_rect(x + 2, y + 3, w, h, SHADOW, r=r)
    fb.round_rect(x, y, w, h, CARD, r=r, border=LINE if border else None)


# ---- 顶栏与底部导航(适配 800x480 触摸屏) ----
def draw_nav(fb, page, buttons):
    y = 442
    fb.rect(0, y, W, H - y, CARD)
    fb.hline(0, W, y, LINE)
    cell = 104
    x0 = (W - cell * len(NAV)) // 2
    for i, (pid, label) in enumerate(NAV):
        x = x0 + i * cell
        active = pid == page
        if active:
            fb.round_rect(x + 7, y + 5, cell - 14, 28, PALE_BLUE, r=14)
            fb.rect(x + 17, y + 16, 6, 6, BLUE)
        fb.text_center(label, x + cell // 2 + (5 if active else 0), y + 10, 1,
                       BLUE if active else MUTED)
        buttons.append({"rect": (x, y, cell, H - y), "nav": pid})


def draw_header(fb, view, clock, title):
    fb.rect(0, 0, W, 54, CARD)
    fb.hline(0, W, 53, LINE)
    # Compact EdgeAgent mark + product lockup. The mark is UI chrome, not a mascot asset.
    fb.round_rect(16, 11, 32, 32, BLUE2, r=8)
    fb.text_center("E", 32, 17, 2, (255, 255, 255))
    fb.text("EdgeAgent", 58, 12, 1, INK)
    fb.text("ONE", 58, 29, 1, BLUE)
    fb.vline(12, 42, 142, LINE)
    fb.text(title, 158, 18, 1, INK)
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    total = len(devs)
    clk_w = fb.text_w(clock, 1)
    fb.text(clock, W - clk_w - 18, 19, 1, MUTED)
    pc = GREEN if (online == total and total) else AMBER
    pl = "系统正常" if pc == GREEN else "设备 %d/%d" % (online, total)
    pw = fb.text_w(pl, 1) + 34
    px = W - clk_w - 18 - pw - 20
    fb.round_rect(px, 14, pw, 25, PALE_GREEN if pc == GREEN else PALE_AMBER, r=12)
    fb.rect(px + 12, 23, 7, 7, pc)
    fb.text(pl, px + 24, 17, 1, pc)


def _kpi_row(fb, view):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    total = len(devs)
    cx0, cy0, cw, ch, gap = 16, 132, 132, 104, 8
    kpis = [("二次供温", fnum(pick(view, "sec_supply_temp")), "℃", BLUE),
            ("供水压力", fnum(pick(view, "sec_supply_pressure"), 2), "MPa", BLUE),
            ("循环泵频率", fnum(pick(view, "pump_freq")), "Hz", GREEN),
            ("在线设备", "%d/%d" % (online, total), "", GREEN if online == total else AMBER)]
    for i, (label, val, unit, col) in enumerate(kpis):
        x = cx0 + i * (cw + gap)
        panel(fb, x, cy0, cw, ch)
        fb.round_rect(x + 12, cy0 + 10, 24, 24,
                      PALE_GREEN if col == GREEN else (PALE_AMBER if col == AMBER else PALE_BLUE), r=8)
        fb.rect(x + 20, cy0 + 18, 8, 8, col)
        fb.text(label, x + 44, cy0 + 14, 1, MUTED)
        vx = fb.text(val, x + 14, cy0 + 43, 2, INK)
        if unit:
            fb.text(unit, vx + 5, cy0 + 52, 1, MUTED)
        # Tiny bar sparkline, kept data-neutral because the snapshot has no history series.
        bars = (5, 9, 7, 13, 8, 16, 11, 18, 13, 20, 14, 17)
        for bi, bh in enumerate(bars):
            fb.round_rect(x + 14 + bi * 8, cy0 + 91 - bh, 4, bh, col, r=2)


def _device_list(fb, view, x, y, w, h):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    panel(fb, x, y, w, h)
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
        fb.hline(x + 14, x + w - 14, ry + 26, LINE)
        ry += 28


def _status_bar(fb, view):
    by = 394
    events = view.get("events", [])
    msg = events[0].get("detail") if events else None
    if msg:
        fb.round_rect(16, by, 552, 36, CARD, r=10, border=LINE)
        fb.rect(28, by + 14, 8, 8, AMBER)
        fb.text(("事件 " + msg)[:38], 40, by + 10, 1, INK)
    else:
        fb.round_rect(16, by, 552, 36, CARD, r=10, border=LINE)
        fb.rect(28, by + 14, 8, 8, GREEN)
        fb.text("系统正常 · 本机采集与设备监控运行中", 46, by + 9, 1, GREEN)


# ---- 各页面 ----
def page_overview(fb, view, targets, buttons):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    fb.text("换热网关", 18, 70, 2, INK)
    fb.text("换热系统", 18, 104, 1, MUTED)
    fb.text("运行正常" if online == len(devs) else "设备异常", 118, 104, 1,
            GREEN if online == len(devs) else AMBER)
    _kpi_row(fb, view)
    # Device summary cards echo the product cards in the reference without fake product imagery.
    cards = [("换热机组", "供温 %s℃" % fnum(pick(view, "sec_supply_temp")), BLUE),
             ("循环水泵", "频率 %sHz" % fnum(pick(view, "pump_freq")), GREEN),
             ("调节阀", "开度 %s%%" % fnum(pick(view, "valve_open"), 0), AMBER)]
    for i, (name, detail, col) in enumerate(cards):
        x, y, w, h = 16 + i * 184, 248, 176, 134
        panel(fb, x, y, w, h)
        fb.text(name, x + 14, y + 12, 1, INK)
        fb.rect(x + w - 26, y + 17, 7, 7, GREEN)
        fb.text("运行正常", x + 14, y + 37, 1, GREEN)
        fb.round_rect(x + 14, y + 62, 48, 48,
                      PALE_GREEN if col == GREEN else (PALE_AMBER if col == AMBER else PALE_BLUE), r=12)
        fb.ring(x + 38, y + 86, 15, 10, .72, col, sweep=300, start=120)
        fb.text(detail, x + 72, y + 79, 1, MUTED)

    # Local duty rail: the cloud-agent metaphor is translated into observable local services.
    x, y, w, h = 584, 66, 200, 364
    panel(fb, x, y, w, h, r=14)
    fb.text("本机监控中", x + 16, y + 16, 2, INK)
    fb.text("离线可运行 · 就地监控", x + 16, y + 50, 1, MUTED)
    fb.hline(x + 14, x + w - 14, y + 76, LINE)
    duties = [("数据采集", "读取设备点位", GREEN),
              ("设备运行", "%d/%d 在线" % (online, len(devs)), BLUE),
              ("本机控制", "安全校验下发", BLUE),
              ("云端上行", "本机运行正常", MUTED)]
    for i, (name, desc, col) in enumerate(duties):
        ry = y + 92 + i * 64
        fb.ring(x + 24, ry + 10, 9, 6, 1 if col != MUTED else .35, col, sweep=360, start=0)
        if i < len(duties) - 1:
            fb.vline(ry + 20, ry + 58, x + 24, LINE)
        fb.text(name, x + 44, ry, 1, col if col != MUTED else INK)
        fb.text(desc, x + 44, ry + 23, 1, MUTED)
    _status_bar(fb, view)


def _qcolor(q):
    return GREEN if q in ("good", "") else (AMBER if q in ("stale", "est") else RED)


def page_monitor(fb, view, targets, buttons):
    if DISPLAY_CARDS:
        return _page_monitor_cards(fb, view)
    pts = all_points(view)
    panel(fb, 16, 66, 768, 364, r=14)
    fb.text("采集点表 · 共 %d 点" % len(pts), 34, 82, 1, MUTED)
    col_w = 356
    per = 11
    for idx, (dn, pid, v, u, q) in enumerate(pts[: per * 2]):
        col = idx // per
        row = idx % per
        x = 34 + col * (col_w + 22)
        ry = 110 + row * 27
        fb.rect(x, ry + 5, 7, 7, _qcolor(q))
        fb.text(pid[:16], x + 14, ry, 1, INK)
        fb.text_right("%s %s" % (fnum(v), u), x + col_w - 6, ry, 1,
                      INK if q in ("good", "") else MUTED)
        fb.hline(x, x + col_w - 6, ry + 22, LINE)


def _page_monitor_cards(fb, view):
    """display_model 驱动:按卡片分组渲染,2 列流式排布,超出可视高度的卡片截断。"""
    col_w = 378
    colx = [16, 406]
    coly = [66, 66]
    for c in DISPLAY_CARDS:
        fields = c["fields"][:6]
        ch = 30 + len(fields) * 22 + 8
        ci = 0 if coly[0] <= coly[1] else 1
        x, y = colx[ci], coly[ci]
        if y + ch > 430:
            continue
        panel(fb, x, y, col_w, ch)
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
    fb.text("运行 %d 台" % len(devs), 24, 76, 1, MUTED)
    cw, chh, gap = 376, 72, 8
    for i, d in enumerate(devs[:8]):
        col, row = i % 2, i // 2
        x = 16 + col * (cw + 16)
        y = 108 + row * (chh + gap)
        ok = d.get("ok")
        panel(fb, x, y, cw, chh)
        fb.rect(x + 16, y + 18, 10, 10, GREEN if ok else RED)
        fb.text(d.get("name", "")[:12], x + 32, y + 12, 1, INK)
        sc = GREEN if ok else RED
        st = "在线" if ok else "离线"
        badge = PALE_GREEN if ok else (255, 238, 238)
        fb.round_rect(x + cw - 64, y + 12, 50, 22, badge, r=11)
        fb.text_center(st, x + cw - 39, y + 15, 1, sc)
        fb.text("类型 %s" % d.get("type", "-"), x + 16, y + 36, 1, MUTED)
        fb.text("地址 %s · 点位 %d" % (d.get("addr", "-"), len(d.get("points") or {})),
                x + 16, y + 56, 1, MUTED)


def page_control(fb, view, targets, buttons):
    panel(fb, 16, 66, 768, 364, r=14)
    fb.text("就地控制 · 点 −/+ 下发设定值(安全校验)", 34, 82, 1, MUTED)
    for i, (label, fbid, spid, lo, hi, step, unit, col) in enumerate(CONTROLS):
        ry = 112 + i * 100
        cur = pick(view, fbid)
        tgt = targets.get(fbid)
        if tgt is None:
            tgt = round(cur) if cur is not None else lo
        fb.text(label, 38, ry, 2, INK)
        frac = 0 if cur is None else max(0.0, min(1.0, (float(cur) - lo) / (hi - lo)))
        fb.round_rect(38, ry + 40, 320, 10, TRACK, r=5)
        fb.round_rect(38, ry + 40, int(320 * frac), 10, col, r=5)
        fb.text("当前 %s%s" % (fnum(cur, 0 if unit == "%" else 1), unit), 38, ry + 60, 1, MUTED)
        bm = (480, ry, 64, 64)
        bp = (690, ry, 64, 64)
        fb.round_rect(*bm, CARD2, r=12, border=LINE)
        fb.text_center("-", bm[0] + 35, ry + 12, 3, MUTED)
        fb.round_rect(*bp, PALE_GREEN if col == GREEN else CARD2, r=12, border=col)
        fb.text_center("+", bp[0] + 35, ry + 12, 3, col)
        fb.text_center(fnum(tgt, 0), 617, ry + 10, 3, INK)
        fb.text_center("设定 " + unit, 617, ry + 52, 1, MUTED)
        buttons.append({"rect": bm, "fb": fbid, "sp": spid, "delta": -step, "lo": lo, "hi": hi})
        buttons.append({"rect": bp, "fb": fbid, "sp": spid, "delta": step, "lo": lo, "hi": hi})


def page_settings(fb, view, targets, buttons):
    devs = view.get("devices", [])
    online = sum(1 for d in devs if d.get("ok"))
    pts = sum(len(d.get("points") or {}) for d in devs)
    settings = view.get("local_settings") or {}
    brightness = max(10, min(100, int(settings.get("brightness", 80))))
    theme = settings.get("theme", "light")
    panel(fb, 16, 66, 768, 364, r=14)
    fb.text("画面调节", 34, 82, 1, MUTED)

    fb.round_rect(34, 108, 716, 76, CARD2, r=12, border=LINE)
    fb.text("明度", 52, 126, 2, INK)
    fb.text("10% - 100%", 52, 154, 1, MUTED)
    minus = (466, 120, 68, 48)
    plus = (664, 120, 68, 48)
    fb.round_rect(*minus, CARD, r=10, border=LINE)
    fb.text_center("-", minus[0] + minus[2] // 2, 128, 2, MUTED)
    fb.text_center("%d%%" % brightness, 599, 128, 2, INK)
    fb.round_rect(*plus, PALE_BLUE, r=10, border=BLUE)
    fb.text_center("+", plus[0] + plus[2] // 2, 128, 2, BLUE)
    buttons.append({"rect": minus, "action": "brightness_change", "delta": -10})
    buttons.append({"rect": plus, "action": "brightness_change", "delta": 10})

    fb.round_rect(34, 198, 716, 76, CARD2, r=12, border=LINE)
    fb.text("风格", 52, 218, 2, INK)
    fb.text("LIGHT / DARK", 52, 248, 1, MUTED)
    light = (466, 212, 120, 48)
    dark = (612, 212, 120, 48)
    for rect, value, label in ((light, "light", "LIGHT"), (dark, "dark", "DARK")):
        active = theme == value
        fb.round_rect(*rect, PALE_BLUE if active else CARD, r=10,
                      border=BLUE if active else LINE)
        fb.text_center(label, rect[0] + rect[2] // 2, 228, 1,
                       BLUE if active else MUTED)
        buttons.append({"rect": rect, "action": "theme_set", "theme": value})

    fb.text("系统信息", 34, 294, 1, MUTED)
    rows = [
        ("设备", "%d 台 · 在线 %d" % (len(devs), online)),
        ("点位", "%d 点" % pts),
        ("平台", "RK3506 · Buildroot · DRM"),
    ]
    for i, (key, value) in enumerate(rows):
        ry = 320 + i * 32
        fb.text(key, 52, ry, 1, MUTED)
        fb.text(value, 220, ry, 1, INK)
        if i < len(rows) - 1:
            fb.hline(44, W - 44, ry + 22, LINE)


PAGES = {"overview": page_overview, "monitor": page_monitor, "nodes": page_nodes,
         "control": page_control, "settings": page_settings}


def render(view, clock="--:--:--", targets=None, page="overview"):
    targets = targets or {}
    buttons = []
    fb = FB()
    fb.clear(BG)
    if page not in PAGES:
        page = "overview"
    draw_header(fb, view, clock, PAGE_TITLE[page])
    PAGES[page](fb, view, targets, buttons)
    draw_nav(fb, page, buttons)
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

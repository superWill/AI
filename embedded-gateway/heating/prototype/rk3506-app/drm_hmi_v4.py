#!/usr/bin/env python3
"""RK3506 本地第一屏 v4 —— edge-os 风格图形仪表盘 + 触摸控制。

在 v3 基础上加:读 Goodix 触摸屏(/dev/input/event0),点 −/+ 按钮下发设定值。
触摸坐标 0..799/0..479,与屏幕 1:1(已 ioctl 实测)。控制走本机 /api/command(安全校验)。

用法:  python3 drm_hmi_v4.py [port] [--products build]
       --products 给定时,监控页按编译产物 display_model.json 分组(否则平铺点表)。
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

def _arg(flag):
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
PORT = int(_pos[0]) if _pos else 8092
PRODUCTS = _arg("--products")
BASE = "http://127.0.0.1:%d" % PORT
CONFIG_BASE = "http://127.0.0.1:8092"
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
        self.lock = threading.Lock()
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

    @staticmethod
    def prepare_rgb(rgb):
        """Convert packed RGB888 once so cached pages can be shown by one mmap copy."""
        out = bytearray(W * H * 4)
        out[0::4] = rgb[2::3]
        out[1::4] = rgb[1::3]
        out[2::4] = rgb[0::3]
        return bytes(out)

    def blit_frame(self, frame):
        with self.lock:
            if self.pitch == W * 4:
                self.mm[0:W * H * 4] = frame
            else:
                for y in range(H):
                    self.mm[y * self.pitch:y * self.pitch + W * 4] = frame[y * W * 4:(y + 1) * W * 4]

    def blit_rgb(self, rgb):
        self.blit_frame(self.prepare_rgb(rgb))


class FrameCache:
    """Thread-safe prepared DRM frames and matching touch regions by page."""
    def __init__(self):
        self.lock = threading.Lock()
        self.pages = {}

    def put(self, page, frame, buttons):
        with self.lock:
            self.pages[page] = (frame, tuple(buttons))

    def get(self, page):
        with self.lock:
            return self.pages.get(page)

    def invalidate(self, *pages):
        with self.lock:
            for page in pages:
                self.pages.pop(page, None)


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


def fetch_device_config():
    with urllib.request.urlopen(CONFIG_BASE + "/api/local/device-config", timeout=2) as r:
        return json.loads(r.read()).get("nodes", [])


def save_device_config(nodes):
    body = json.dumps(nodes).encode()
    req = urllib.request.Request(CONFIG_BASE + "/api/local/device-config", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=3) as r:
            return json.loads(r.read())
    except Exception as exc:
        print("[config] save err:", exc, flush=True)
        return {"ok": False, "error": str(exc)}


DEVICE_TYPES = [("other", "设备"), ("pump_vfd", "水泵"),
                ("temp_humidity_sensor", "温度传感器"),
                ("pressure_sensor", "压力传感器"), ("heat_meter", "热量表"),
                ("energy_meter", "电能表"), ("io_module", "IO 模块")]
SERIAL_PORTS = ["/dev/ttyS1", "/dev/ttyS2", "/dev/ttyS3", "/dev/ttyS4"]
BAUDS = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
PARITIES = ["none", "even", "odd"]
POLL_INTERVALS = [250, 500, 1000, 2000, 5000, 10000]


def new_device_form():
    return {"deviceType": "other", "deviceTypeLabel": "设备",
            "serialPort": "/dev/ttyS1", "baudRate": 9600, "dataBits": 8,
            "stopBits": 1, "parity": "none", "slaveId": 1, "pollInterval": 1000}


def main():
    if PRODUCTS:
        dm_path = os.path.join(PRODUCTS, "display_model.json")
        if os.path.exists(dm_path):
            dashboard.configure_display(json.load(open(dm_path, encoding="utf-8")))
            print("[显示] 监控页按 %s 分组(%d 卡片)" % (dm_path, len(dashboard.DISPLAY_CARDS)),
                  flush=True)
    scr = Screen()
    targets = {}
    state = {"buttons": [], "view": {"devices": []}, "page": "overview",
             "configured_nodes": [], "config_slot": 0, "device_form": new_device_form(),
             "config_message": ""}
    try:
        state["configured_nodes"] = fetch_device_config()
    except Exception as exc:
        print("[config] 初始读取失败:", exc, flush=True)
    dirty = threading.Event()
    frame_cache = FrameCache()

    def load_config_slot(slot):
        nodes = state["configured_nodes"]
        state["config_slot"] = slot % (len(nodes) + 1)
        if state["config_slot"] == 0:
            state["device_form"] = new_device_form()
            return
        node = dict(nodes[state["config_slot"] - 1])
        label = next((label for value, label in DEVICE_TYPES if value == node.get("deviceType")), "设备")
        node["deviceTypeLabel"] = label
        state["device_form"] = node

    def cycle_value(field, values, delta):
        form = state["device_form"]
        current = form.get(field)
        try:
            index = values.index(current)
        except ValueError:
            index = 0
        form[field] = values[(index + delta) % len(values)]

    def on_tap(x, y):
        for b in state["buttons"]:
            bx, by, bw, bh = b["rect"]
            if bx - 8 <= x <= bx + bw + 8 and by - 8 <= y <= by + bh + 8:
                if "nav" in b:                       # 侧栏导航:切页
                    state["page"] = b["nav"]
                    print("[nav] → %s" % b["nav"], flush=True)
                    cached = frame_cache.get(b["nav"])
                    if cached is not None:
                        frame, cached_buttons = cached
                        state["buttons"] = cached_buttons
                        scr.blit_frame(frame)
                    dirty.set()
                    return
                action = b.get("action")
                if action in ("open_device_add", "open_device_config"):
                    try:
                        state["configured_nodes"] = fetch_device_config()
                    except Exception:
                        state["configured_nodes"] = []
                    state["config_message"] = ""
                    load_config_slot(0 if action == "open_device_add" else
                                     (1 if state["configured_nodes"] else 0))
                    state["page"] = "device_config"; dirty.set(); return
                if action == "config_back":
                    state["page"] = "nodes"; dirty.set(); return
                if action == "config_change":
                    field, delta = b["field"], b["delta"]
                    if field == "record":
                        load_config_slot(state["config_slot"] + delta)
                    elif field == "deviceType":
                        values = [v for v, _ in DEVICE_TYPES]; cycle_value(field, values, delta)
                        state["device_form"]["deviceTypeLabel"] = next(
                            label for value, label in DEVICE_TYPES
                            if value == state["device_form"]["deviceType"])
                    elif field == "serialPort": cycle_value(field, SERIAL_PORTS, delta)
                    elif field == "baudRate": cycle_value(field, BAUDS, delta)
                    elif field == "parity": cycle_value(field, PARITIES, delta)
                    elif field == "pollInterval": cycle_value(field, POLL_INTERVALS, delta)
                    elif field == "slaveId":
                        state["device_form"][field] = ((int(state["device_form"].get(field, 1)) - 1 + delta) % 247) + 1
                    state["config_message"] = ""; dirty.set(); return
                if action == "config_save":
                    adding = state["config_slot"] == 0
                    form = dict(state["device_form"]); form.pop("deviceTypeLabel", None)
                    form.update({"type": "Southbound", "driver": "Modbus RTU", "transport": "RTU",
                                 "endpoint": form["serialPort"], "byteOrder": "ABCD"})
                    label = next(label for value, label in DEVICE_TYPES if value == form["deviceType"])
                    form["name"] = "%s %s" % (label, form["slaveId"])
                    nodes = list(state["configured_nodes"])
                    if state["config_slot"]:
                        form["id"] = nodes[state["config_slot"] - 1]["id"]
                        nodes[state["config_slot"] - 1] = form
                    else:
                        form["id"] = "local-%s-%s" % (os.path.basename(form["serialPort"]), form["slaveId"])
                        nodes.append(form)
                    result = save_device_config(nodes)
                    if result.get("ok"):
                        state["configured_nodes"] = result.get("nodes", nodes)
                        state["config_slot"] = next(i + 1 for i, n in enumerate(state["configured_nodes"])
                                                    if n["id"] == form["id"])
                        state["config_message"] = "设备已接入" if adding else "配置正常"
                        frame_cache.invalidate("nodes", "device_config")
                    else:
                        state["config_message"] = "配置异常"
                    dirty.set(); return
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
    warm_pages = [pid for pid, _ in dashboard.NAV if pid != "overview"]
    while True:
        try:
            state["view"] = fetch()
        except Exception:
            state["view"] = {"devices": [], "events": [{"detail": "正在连接后端…"}]}
        state["view"]["configured_nodes"] = state["configured_nodes"]
        clock = time.strftime("%H:%M:%S") if time.gmtime().tm_year >= 2020 else "--:--:--"
        render_page = state["page"]
        fb, buttons = dashboard.render(state["view"], clock=clock, targets=targets,
                                       page=render_page, device_form=state["device_form"],
                                       config_slot=state["config_slot"],
                                       config_message=state["config_message"])
        frame = scr.prepare_rgb(fb.buf)
        frame_cache.put(render_page, frame, buttons)
        # A tap may have changed page while the slow render was running. Never
        # let that completed old frame overwrite the newly selected cached page.
        if state["page"] == render_page:
            state["buttons"] = buttons
            scr.blit_frame(frame)

        # Warm one not-yet-visited navigation page after each active render.
        # This costs startup CPU but makes subsequent taps a direct mmap copy.
        if warm_pages and state["view"].get("devices"):
            warm_page = warm_pages.pop(0)
            warm_fb, warm_buttons = dashboard.render(
                state["view"], clock=clock, targets=targets, page=warm_page,
                device_form=state["device_form"], config_slot=state["config_slot"],
                config_message=state["config_message"])
            warm_frame = scr.prepare_rgb(warm_fb.buf)
            frame_cache.put(warm_page, warm_frame, warm_buttons)
            if state["page"] == warm_page:
                state["buttons"] = warm_buttons
                scr.blit_frame(warm_frame)
            # Populate all five navigation pages immediately once the backend
            # has real data; do not stretch cache warm-up over several seconds.
            continue
        dirty.wait(1.0)          # 1Hz 刷新,触摸即时重绘
        dirty.clear()


if __name__ == "__main__":
    main()

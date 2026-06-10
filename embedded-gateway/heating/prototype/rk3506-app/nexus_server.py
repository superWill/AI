#!/usr/bin/env python3
"""nexus-edge-os 前端 + Python 后端适配(纯标准库,零依赖)。

把真 edge-os 已构建的前端 dist 装到 RK3506,用 Python 实现它要的契约:
  - REST: /api/login /api/me /api/init /api/tags/write /api/nodes ... (见 services/api.ts)
  - 实时: 自实现的 socket.io(Engine.IO v4 + Socket.IO v5)轮询服务器,
          推 tag-change / node-change / system-metrics 三个事件。
数据来自 app.py 的统一点表快照(sim 或 modbus 源),控制走 app.py 的安全校验。

用法:
  python3 nexus_server.py --config app_config.json --dist nexus-dist --port 8092
"""
from __future__ import annotations

import argparse
import json
import os
import random
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from app import Runtime, SimSource, ModbusSource, Controller   # 复用已验证的内核

HERE = os.path.dirname(os.path.abspath(__file__))

# 我们网关的可控反馈点 → 设定值点(写 tag 时转成下发设定值)
CONTROLLABLE = {"valve_open": "valve_open_sp", "pump_freq": "pump_freq_sp",
                "sec_supply_temp": "sec_supply_temp_sp"}

# 设备类型(中文) → edge-os DeviceType 枚举
DEVTYPE = {"换热机组": "boiler", "循环泵": "pump_vfd", "电动调节阀": "valve_actuator",
           "压力传感器": "pressure_sensor", "安全IO": "io_module", "热表": "heat_meter",
           "电表": "energy_meter", "温度传感器": "temp_humidity_sensor"}


# ===========================================================================
# 快照 → edge-os 的 nodes / tags 模型
# ===========================================================================
def build_nodes_tags(view, endpoint):
    nodes, tags = [], []
    for d in view.get("devices", []):
        addr = d["addr"]
        nid = "node-%s" % addr
        ok = d.get("ok")
        nodes.append({
            "id": nid, "name": d["name"], "type": d.get("type", ""),
            "deviceType": DEVTYPE.get(d.get("type", ""), "other"),
            "driver": "Modbus RTU", "endpoint": endpoint, "slaveId": addr,
            "status": "Running" if ok else "Error",
            "metrics": {"tx": 0, "rx": 0, "errors": 0 if ok else 1},
            "uptime": "-",
        })
        for pid, p in (d.get("points") or {}).items():
            controllable = pid in CONTROLLABLE
            tags.append({
                "id": "tag-%s-%s" % (addr, pid), "nodeId": nid, "name": pid,
                "address": pid, "type": "FLOAT32",
                "access": "RW" if controllable else "R",
                "value": p.get("v") if p.get("v") is not None else 0,
                "timestamp": d.get("ts", int(time.time() * 1000)),
                "unit": p.get("u", ""),
            })
    return nodes, tags


def sys_metrics():
    cpu, mem = 5.0, 30.0
    try:
        with open("/proc/loadavg") as f:
            cpu = min(100.0, float(f.read().split()[0]) * 25)
        mt = ma = 0
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal:"):
                mt = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                ma = int(line.split()[1])
        if mt:
            mem = round((mt - ma) * 100.0 / mt, 1)
    except OSError:
        cpu, mem = round(random.uniform(3, 15), 1), round(random.uniform(28, 45), 1)
    return {"cpu": round(cpu, 1), "memory": mem, "throughput": 0,
            "rx": 0, "tx": 0, "nbRx": 0, "nbTx": 0, "network": []}


# ===========================================================================
# socket.io (Engine.IO v4 + Socket.IO v5) —— 仅 polling 传输,纯标准库
# ===========================================================================
RS = "\x1e"   # EIO4 多包分隔符


def eio_open(sid):
    return "0" + json.dumps({"sid": sid, "upgrades": [], "pingInterval": 25000,
                             "pingTimeout": 20000, "maxPayload": 1000000})


def sio_event(event, data):
    return "42" + json.dumps([event, data], ensure_ascii=False)


class SocketHub:
    def __init__(self):
        self.sessions = {}                  # sid -> {q: deque, ev: Event}
        self.lock = threading.Lock()

    def new_session(self):
        sid = "%016x" % random.getrandbits(64)
        with self.lock:
            self.sessions[sid] = {"q": deque(), "ev": threading.Event()}
        return sid

    def _push(self, sid, packet):
        s = self.sessions.get(sid)
        if s:
            s["q"].append(packet)
            s["ev"].set()

    def broadcast(self, packet):
        with self.lock:
            sids = list(self.sessions)
        for sid in sids:
            self._push(sid, packet)

    def poll(self, sid, timeout=20):
        s = self.sessions.get(sid)
        if s is None:
            return "0" + json.dumps({"sid": self.new_session()})  # 让客户端重握手
        s["ev"].wait(timeout)
        with self.lock:
            packets = list(s["q"]); s["q"].clear(); s["ev"].clear()
        if not packets:
            return "2"                       # ping,维持长轮询
        return RS.join(packets)

    def handle_post(self, sid, body):
        s = self.sessions.get(sid)
        if s is None:
            return
        for pkt in body.split(RS):
            if pkt.startswith("40"):         # Socket.IO CONNECT
                self._push(sid, "40" + json.dumps({"sid": "%016x" % random.getrandbits(64)}))
            elif pkt == "2":                 # client ping → pong
                self._push(sid, "3")
            # "3"(pong)/其它:忽略


# ===========================================================================
# HTTP:静态 dist + REST + /socket.io
# ===========================================================================
def make_handler(runtime, controller, hub, dist_dir, endpoint, tokens):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            if isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False))

        def _authed(self):
            auth = self.headers.get("Authorization", "")
            return auth.startswith("Bearer ") and len(auth) > 8

        # ---- GET ----
        def do_GET(self):
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            if path == "/socket.io/":
                sid = qs.get("sid", [None])[0]
                if not sid:
                    sid = hub.new_session()
                    return self._send(200, eio_open(sid), "text/plain; charset=utf-8")
                return self._send(200, hub.poll(sid), "text/plain; charset=utf-8")
            if path == "/api/me":
                return self._json({"username": "admin", "role": "admin"})
            if path == "/api/init":
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                view = runtime.view()
                nodes, tags = build_nodes_tags(view, endpoint)
                return self._json({"nodes": nodes, "tags": tags, "apps": [], "rules": []})
            if path == "/api/snapshot":          # 给本地 LCD(drm_hmi_v2)用
                return self._json(runtime.view())
            if path == "/api/scada":
                return self._json([])
            if path == "/api/history":
                return self._json([])
            if path.startswith("/api/"):
                return self._json({})
            return self._static(path)

        def _static(self, path):
            rel = path.lstrip("/") or "index.html"
            full = os.path.normpath(os.path.join(dist_dir, rel))
            if not full.startswith(dist_dir) or not os.path.isfile(full):
                full = os.path.join(dist_dir, "index.html")   # SPA 兜底
            if not os.path.isfile(full):
                return self._send(404, "not found", "text/plain")
            ext = full.rsplit(".", 1)[-1].lower()
            ctype = {"html": "text/html", "js": "text/javascript", "css": "text/css",
                     "json": "application/json", "svg": "image/svg+xml",
                     "png": "image/png", "ico": "image/x-icon",
                     "woff2": "font/woff2", "woff": "font/woff"}.get(ext, "application/octet-stream")
            self._send(200, open(full, "rb").read(), ctype + "; charset=utf-8")

        # ---- POST ----
        def do_POST(self):
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            if path == "/socket.io/":
                hub.handle_post(qs.get("sid", [None])[0], raw.decode("utf-8", "replace"))
                return self._send(200, "ok", "text/plain")
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                body = {}
            if path == "/api/login":
                tok = "%032x" % random.getrandbits(128)
                tokens.add(tok)
                return self._json({"token": tok, "user": {"username": body.get("username", "admin")}})
            if path == "/api/command":          # 本地触摸屏控制面板用
                ok, reason = controller.apply(body.get("point_id", ""), body.get("value"), origin="lcd")
                return self._json({"ok": ok, "reason": reason})
            if path == "/api/tags/write":
                ok, reason = self._write_tag(body.get("tagId", ""), body.get("value"))
                return self._json({"ok": ok, "error": reason} if not ok else {"ok": True})
            if path in ("/api/nodes", "/api/tags", "/api/apps", "/api/rules",
                        "/api/scada", "/api/change-password", "/api/restart", "/api/factory-reset"):
                return self._json({"ok": True})
            return self._json({"ok": True})

        def do_DELETE(self):
            return self._json({"ok": True})

        def _write_tag(self, tag_id, value):
            # tag-<addr>-<pid>
            parts = tag_id.split("-", 2)
            if len(parts) != 3:
                return False, "bad tagId"
            pid = parts[2]
            sp = CONTROLLABLE.get(pid)
            if not sp:
                return False, "该点位不可写"
            ok, reason = controller.apply(sp, value, origin="nexus")
            return ok, reason

    return H


# ===========================================================================
# 后台:采集 + 周期广播 socket 事件
# ===========================================================================
def broadcaster(runtime, hub, endpoint, stop):
    while not stop.is_set():
        view = runtime.view()
        nodes, tags = build_nodes_tags(view, endpoint)
        hub.broadcast(sio_event("tag-change", tags))
        hub.broadcast(sio_event("node-change", nodes))
        hub.broadcast(sio_event("system-metrics", sys_metrics()))
        stop.wait(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "app_config.json"))
    ap.add_argument("--dist", default=os.path.join(HERE, "nexus-dist"))
    ap.add_argument("--source", choices=["sim", "modbus"], default=None)
    ap.add_argument("--serial", default=None)
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()

    cfg = json.load(open(args.config))
    kind = args.source or cfg.get("source", "sim")
    if kind == "modbus":
        dev = args.serial or cfg.get("serial", "/dev/ttyS1")
        source = ModbusSource(dev, cfg.get("baud", 9600), cfg["devices"])
        endpoint = dev
        print("[源] modbus %s" % dev, flush=True)
    else:
        source = SimSource(cfg["devices"])
        endpoint = "sim"
        print("[源] sim 内置仿真", flush=True)

    runtime = Runtime(cfg)
    controller = Controller(runtime, source, cfg.get("control_map", {}))
    hub = SocketHub()
    tokens = set()
    stop = threading.Event()

    def collect():
        while not stop.is_set():
            try:
                runtime.update(source.poll())
            except Exception as exc:
                print("[采集] 异常:", exc, flush=True)
            stop.wait(cfg.get("poll_interval_s", 2))
    threading.Thread(target=collect, daemon=True).start()
    threading.Thread(target=broadcaster, args=(runtime, hub, endpoint, stop), daemon=True).start()

    dist = os.path.normpath(args.dist)
    port = args.port or cfg.get("http_port", 8092)
    handler = make_handler(runtime, controller, hub, dist, endpoint, tokens)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print("[nexus] http://0.0.0.0:%d/  dist=%s" % (port, dist), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()

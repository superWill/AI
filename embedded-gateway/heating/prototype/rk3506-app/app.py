#!/usr/bin/env python3
"""RK3506 供热网关应用 —— keystone 后端(纯标准库,零依赖)。

把分散的 demo 收敛成一份运行时:
  数据源(sim 内置仿真 / modbus 真串口) ─► 统一点表快照 + 设备注册表(一份)
       │
       ├─ HTTP :8092  静态 HMI + REST + SSE 实时推送  (本地屏/PC/手机都读这一份)
       ├─ MQTT 上云    周期遥测 + 心跳;订阅 property/set 下发设定值
       └─ 控制闭环      平台下发 → 安全校验 → 写回数据源 → 反馈进快照 → command_reply

数据源是可插拔的:
  - sim    : 板子自己造各种设备/数据(含可控点位),不需要 104,适合开机演示。
  - modbus : 真串口轮询 104 的 modbus_sim.py(现场陪练)。

用法:
  python3 app.py --config app_config.json            # 按配置(默认 sim 源)
  python3 app.py --config app_config.json --source modbus --serial /dev/ttyS1
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import socket
import struct
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))


# ===========================================================================
# 1) 安全校验 —— 平台只能给设定值,绝不越过本地安全分层(README 共性原则)
# ===========================================================================
SAFE_RANGES = {
    "sec_supply_temp_sp": (20.0, 75.0),   # 二次侧供水温度设定
    "valve_open_sp": (0.0, 100.0),        # 阀位设定 %
    "pump_freq_sp": (0.0, 50.0),          # 循环泵频率设定 Hz
}


def safety_check(point_id: str, value) -> tuple[bool, str]:
    rng = SAFE_RANGES.get(point_id)
    if rng is None:
        return False, f"未知或不可远程设定的点位 {point_id}"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return False, f"{point_id} 值非法 {value!r}"
    lo, hi = rng
    if not (lo <= v <= hi):
        return False, f"{point_id}={v} 超出安全限值 [{lo},{hi}]"
    return True, ""


# ===========================================================================
# 2) 数据源:内置仿真(可控) —— 板子自己模拟各种设备/数据
# ===========================================================================
class SimSource:
    """纯内置仿真源:按设备模板生成连续波动数据;控制设定值写进来后,
    反馈量会朝设定值收敛(模拟闭环),HMI 看得到指令→反馈的变化。"""

    def __init__(self, devices_cfg: list[dict]):
        self.t0 = time.time()
        self.devices = devices_cfg
        self.lock = threading.Lock()
        # 可控点位的"当前反馈值"和"设定值",控制闭环用
        self.setpoints = {"valve_open_sp": 45.0, "pump_freq_sp": 32.0,
                          "sec_supply_temp_sp": 50.0}
        self.feedback = {"valve_open": 45.0, "pump_freq": 32.0, "sec_supply_temp": 50.0}

    def _wave(self, base, swing, period):
        return base + swing * 0.5 * math.sin(2 * math.pi * (time.time() - self.t0) / period)

    def write_setpoint(self, point_id, value) -> bool:
        with self.lock:
            if point_id in self.setpoints:
                self.setpoints[point_id] = float(value)
                return True
        return False

    def _converge(self):
        """反馈量朝设定值收敛一步(一阶滞后),模拟执行器响应。"""
        with self.lock:
            for fb, sp in (("valve_open", "valve_open_sp"),
                           ("pump_freq", "pump_freq_sp"),
                           ("sec_supply_temp", "sec_supply_temp_sp")):
                target = self.setpoints[sp]
                self.feedback[fb] += (target - self.feedback[fb]) * 0.25
            return dict(self.feedback)

    def poll(self) -> dict:
        """返回 {addr: sample},sample 同 modbus 源结构,上层不分源。"""
        fb = self._converge()
        out = {}
        for d in self.devices:
            addr = d["addr"]
            faulted = d.get("fault") == "offline"
            ts = int(time.time() * 1000)
            if faulted:
                out[addr] = {"addr": addr, "name": d["name"], "type": d["type"],
                             "ts": ts, "ok": False, "health": "离线",
                             "offline": True, "fails": 0, "next_retry_s": 0,
                             "points": {p["id"]: {"v": None, "u": p.get("unit", ""),
                                                  "q": "offline"} for p in d["points"]}}
                continue
            pts = {}
            for p in d["points"]:
                pid = p["id"]
                if pid in fb:                       # 可控反馈点:用闭环值
                    v = round(fb[pid], 1)
                elif "fixed" in p:
                    v = p["fixed"]
                else:
                    v = round(self._wave(p.get("base", 0), p.get("swing", 0),
                                         p.get("period_s", 60)), p.get("round", 1))
                pts[pid] = {"v": v, "u": p.get("unit", ""), "q": "good"}
            out[addr] = {"addr": addr, "name": d["name"], "type": d["type"],
                         "ts": ts, "ok": True, "health": "在线",
                         "offline": False, "fails": 0, "next_retry_s": 0, "points": pts}
        return out


# ===========================================================================
# 3) 数据源:真串口 Modbus(轮询 104) —— 复用已验证的采集逻辑
# ===========================================================================
class ModbusSource:
    def __init__(self, dev, baud, devices_cfg, timeout=1.0, reliability=None):
        import termios
        self.termios = termios
        bauds = {9600: termios.B9600, 19200: termios.B19200, 38400: termios.B38400,
                 57600: termios.B57600, 115200: termios.B115200}
        self.devices = devices_cfg
        self.timeout = timeout
        # 招2 故障隔离+退避参数(可配,缺省安全值)
        rel = reliability or {}
        self.offline_after = rel.get("offline_after", 3)     # 连续失败 N 次→离线
        self.backoff_base = rel.get("backoff_base_s", 5)     # 退避起始秒
        self.backoff_max = rel.get("backoff_max_s", 30)      # 退避封顶秒
        self.default_retries = rel.get("retries", 1)
        # 每设备运行时健康状态:坏设备不再每轮耗满超时,而是降频探测
        self.dev_state = {d["addr"]: {"fails": 0, "offline": False, "next_due": 0.0,
                                      "backoff_idx": 0, "last_sample": None}
                          for d in self.devices}
        self.lock = threading.Lock()   # 采集线程与控制写共用串口,事务必须串行
        self.fd = os.open(dev, os.O_RDWR | os.O_NOCTTY)
        a = termios.tcgetattr(self.fd)
        a[0] = a[1] = a[3] = 0
        a[2] = termios.CS8 | termios.CLOCAL | termios.CREAD
        a[4] = a[5] = bauds[baud]
        a[6][termios.VMIN] = 0; a[6][termios.VTIME] = 0
        termios.tcsetattr(self.fd, termios.TCSANOW, a)
        termios.tcflush(self.fd, termios.TCIOFLUSH)

    @staticmethod
    def _crc(data):
        crc = 0xFFFF
        for b in data:
            crc ^= b
            for _ in range(8):
                crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
        return struct.pack("<H", crc)

    def _txn(self, body, timeout):
        import select
        with self.lock:                       # 一次请求+应答原子化,防采集与控制写交叉
            self.termios.tcflush(self.fd, self.termios.TCIOFLUSH)
            os.write(self.fd, body + self._crc(body))
            dl, buf = time.time() + timeout, b""
            while time.time() < dl:
                r, _, _ = select.select([self.fd], [], [], max(0, dl - time.time()))
                if not r:
                    continue
                buf += os.read(self.fd, 256)
                time.sleep(0.03)
                r2, _, _ = select.select([self.fd], [], [], 0)
                if r2:
                    buf += os.read(self.fd, 256)
                break
            return buf

    def read_holding(self, addr, start, count, timeout=None, retries=0):
        """招5:timeout/crc 错可重试;exception 是设备明确拒绝(真应答),不重试。"""
        timeout = timeout or self.timeout
        body = struct.pack(">BBHH", addr, 0x03, start, count)
        err = "timeout"
        for _ in range(retries + 1):
            resp = self._txn(body, timeout)
            if not resp:
                err = "timeout"; continue
            if self._crc(resp[:-2]) != resp[-2:]:
                err = "crc_error"; continue
            if resp[1] & 0x80:
                return None, "exception"
            n = resp[2]
            return [struct.unpack(">H", resp[3 + i:5 + i])[0] for i in range(0, n, 2)], None
        return None, err

    def write_register(self, addr, reg, value) -> bool:
        body = struct.pack(">BBHH", addr, 0x06, reg, int(value) & 0xFFFF)
        resp = self._txn(body, self.timeout)
        return bool(resp) and resp[:6] == body  # echo 确认

    def _bad_points(self, d, q):
        return {p["id"]: {"v": None, "u": p.get("unit", ""), "q": q} for p in d["points"]}

    def poll(self) -> dict:
        out = {}
        now = time.monotonic()
        for d in self.devices:
            addr = d["addr"]
            st = self.dev_state[addr]
            # 招2:离线设备退避未到期→本轮不碰总线,复用上次样本,整轮耗时被压住
            if st["offline"] and now < st["next_due"]:
                s = dict(st["last_sample"]) if st["last_sample"] else {
                    "addr": addr, "name": d["name"], "type": d.get("type", ""),
                    "ok": False, "points": self._bad_points(d, "offline")}
                s["offline"] = True
                s["fails"] = st["fails"]
                s["next_retry_s"] = max(0, round(st["next_due"] - now, 1))
                s["health"] = "离线·下次重试 %ss" % s["next_retry_s"]
                out[addr] = s
                continue
            timeout = d.get("timeout_ms", self.timeout * 1000) / 1000.0
            retries = d.get("retries", self.default_retries)
            regs, err = self.read_holding(addr, d["start"], d["count"], timeout, retries)
            ts = int(time.time() * 1000)
            if err:
                st["fails"] += 1
                if st["fails"] >= self.offline_after and not st["offline"]:
                    st["offline"] = True
                if st["offline"]:                       # 进入/维持离线:几何退避降频
                    backoff = min(self.backoff_base * (2 ** st["backoff_idx"]), self.backoff_max)
                    st["next_due"] = now + backoff
                    st["backoff_idx"] += 1
                    health = "离线·下次重试 %ss" % round(backoff, 1)
                    q = "offline"
                else:
                    health = "异常(%s)×%d" % (err, st["fails"])
                    q = "bad"
                sample = {"addr": addr, "name": d["name"], "type": d.get("type", ""),
                          "ts": ts, "ok": False, "health": health,
                          "fails": st["fails"], "offline": st["offline"],
                          "next_retry_s": max(0, round(st["next_due"] - now, 1)) if st["offline"] else 0,
                          "points": self._bad_points(d, q)}
                st["last_sample"] = sample
                out[addr] = sample
                continue
            # 成功:复位故障状态,恢复每轮轮询
            st["fails"] = 0; st["offline"] = False; st["backoff_idx"] = 0; st["next_due"] = 0.0
            pts = {p["id"]: {"v": round(regs[p["reg"] - d["start"]] * p.get("scale", 1), 3),
                             "u": p.get("unit", ""), "q": "good"} for p in d["points"]}
            sample = {"addr": addr, "name": d["name"], "type": d.get("type", ""),
                      "ts": ts, "ok": True, "health": "在线", "fails": 0,
                      "offline": False, "next_retry_s": 0, "points": pts}
            st["last_sample"] = sample
            out[addr] = sample
        return out

    # 控制写:point_id → (addr,reg,scale) 由 control_map 给出;按 scale 折算成寄存器值
    def write_setpoint(self, point_id, value, control_map) -> bool:
        m = control_map.get(point_id)
        if not m:
            return False
        reg_val = int(round(float(value) / m.get("scale", 1)))
        return self.write_register(m["addr"], m["reg"], reg_val)


# ===========================================================================
# 4) 运行时快照 + 设备注册表(一份,所有出口都读它)
# ===========================================================================
class Runtime:
    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.Lock()
        self.snapshot = {}                  # {addr: sample}
        self.events = deque(maxlen=20)       # 接口/告警事件
        self.commands = deque(maxlen=50)     # 控制指令记录
        self.seq = 0
        self.data_path = os.path.join(HERE, "data", "registry.json")
        self.last_poll_mono = time.monotonic()   # 招4:采集存活时间戳,看门狗据此判活

    def mark_alive(self):
        with self.lock:
            self.last_poll_mono = time.monotonic()

    def collector_age_ms(self):
        with self.lock:
            return int((time.monotonic() - self.last_poll_mono) * 1000)

    def update(self, snap):
        with self.lock:
            self.snapshot = snap

    def get(self):
        with self.lock:
            return dict(self.snapshot)

    def add_event(self, ev):
        ev["time"] = int(time.time() * 1000)
        with self.lock:
            self.events.appendleft(ev)

    def record_command(self, rec):
        with self.lock:
            self.commands.appendleft(rec)

    def telemetry(self):
        with self.lock:
            self.seq += 1
            seq = self.seq
            snap = list(self.snapshot.values())
        return {"device_id": self.cfg.get("device_id", "rk3506-gw-01"),
                "ts": int(time.time() * 1000),
                "clock_sync": "synced" if time.gmtime().tm_year >= 2020 else "unsynced",
                "seq": seq,
                "devices": [{"addr": s["addr"], "name": s["name"], "type": s.get("type", ""),
                             "ok": s["ok"], "points": s["points"]} for s in snap]}

    def view(self):
        """给 HMI 的完整视图。"""
        with self.lock:
            return {"device_id": self.cfg.get("device_id"),
                    "ts": int(time.time() * 1000),
                    "devices": list(self.snapshot.values()),
                    "events": list(self.events),
                    "commands": list(self.commands)[:10]}


# ===========================================================================
# 5) 极简 MQTT 客户端(纯标准库):发布 + 订阅 + keepalive
# ===========================================================================
def _mqtt_len(n):
    out = b""
    while True:
        b = n % 128; n //= 128
        if n:
            b |= 0x80
        out += bytes([b])
        if not n:
            return out


def _read_len(sock):
    mult, val = 1, 0
    while True:
        b = sock.recv(1)
        if not b:
            raise OSError("closed")
        val += (b[0] & 0x7F) * mult
        if not (b[0] & 0x80):
            return val
        mult *= 128


class MqttClient:
    def __init__(self, host, port, client_id, on_message=None,
                 username=None, password=None, keepalive=30):
        self.host, self.port, self.cid = host, port, client_id
        self.user, self.pw, self.keepalive = username, password, keepalive
        self.on_message = on_message
        self.sock = None
        self.subs = []
        self.buf = deque(maxlen=2000)
        self.lock = threading.Lock()

    def _connect(self):
        s = socket.create_connection((self.host, self.port), timeout=5)
        cid = self.cid.encode()
        flags = 0x02
        payload = struct.pack(">H", len(cid)) + cid
        if self.user:
            flags |= 0x80
            u = self.user.encode(); payload += struct.pack(">H", len(u)) + u
            if self.pw:
                flags |= 0x40
                p = self.pw.encode(); payload += struct.pack(">H", len(p)) + p
        var = b"\x00\x04MQTT\x04" + bytes([flags]) + struct.pack(">H", self.keepalive)
        body = var + payload
        s.sendall(b"\x10" + _mqtt_len(len(body)) + body)
        if s.recv(4)[:1] != b"\x20":
            s.close(); raise OSError("CONNACK 失败")
        self.sock = s
        for topic in self.subs:
            self._subscribe(topic)
        threading.Thread(target=self._rx_loop, daemon=True).start()

    def subscribe(self, topic):
        self.subs.append(topic)
        if self.sock:
            self._subscribe(topic)

    def _subscribe(self, topic):
        t = topic.encode()
        body = struct.pack(">H", 1) + struct.pack(">H", len(t)) + t + b"\x00"
        with self.lock:
            self.sock.sendall(b"\x82" + _mqtt_len(len(body)) + body)

    def _rx_loop(self):
        try:
            while self.sock:
                hdr = self.sock.recv(1)
                if not hdr:
                    break
                length = _read_len(self.sock)
                data = b""
                while len(data) < length:
                    chunk = self.sock.recv(length - len(data))
                    if not chunk:
                        break
                    data += chunk
                if (hdr[0] & 0xF0) == 0x30:           # PUBLISH
                    tlen = struct.unpack(">H", data[:2])[0]
                    topic = data[2:2 + tlen].decode("utf-8", "replace")
                    payload = data[2 + tlen:]
                    if self.on_message:
                        try:
                            self.on_message(topic, payload)
                        except Exception as exc:       # 回调出错不能拖垮 rx
                            print("[mqtt] on_message error:", exc, flush=True)
        except OSError:
            pass
        self.sock = None

    def publish(self, topic, obj):
        try:
            if self.sock is None:
                self._connect()
                while self.buf:
                    t, o = self.buf.popleft()
                    o = dict(o); o["replay"] = True
                    self._raw(t, o)
            self._raw(topic, obj)
            return True
        except OSError:
            self.sock = None
            self.buf.append((topic, obj))
            return False

    def _raw(self, topic, obj):
        t = topic.encode(); p = json.dumps(obj, ensure_ascii=False).encode()
        body = struct.pack(">H", len(t)) + t + p
        with self.lock:
            self.sock.sendall(b"\x30" + _mqtt_len(len(body)) + body)

    def ping(self):
        if self.sock:
            try:
                with self.lock:
                    self.sock.sendall(b"\xc0\x00")
            except OSError:
                self.sock = None


# ===========================================================================
# 6) 控制器:下发设定值 → 安全校验 → 写数据源 → 记录 + 回传
# ===========================================================================
class Controller:
    def __init__(self, runtime, source, control_map, mqtt=None, base_topic=""):
        self.rt = runtime
        self.source = source
        self.control_map = control_map
        self.mqtt = mqtt
        self.base = base_topic

    def apply(self, point_id, value, command_id="", origin="local"):
        ok, reason = safety_check(point_id, value)
        if not ok:
            self._record(command_id, point_id, value, "blocked_by_safety", reason, origin)
            return False, reason
        # 写数据源(sim 直接写设定值;modbus 按 control_map 写寄存器)
        if isinstance(self.source, SimSource):
            wrote = self.source.write_setpoint(point_id, value)
        else:
            wrote = self.source.write_setpoint(point_id, value, self.control_map)
        status = "accepted" if wrote else "write_failed"
        self._record(command_id, point_id, value, status, "" if wrote else "源写入失败", origin)
        return wrote, ""

    def _record(self, command_id, point_id, value, status, reason, origin):
        rec = {"command_id": command_id, "point_id": point_id, "value": value,
               "status": status, "reason": reason, "origin": origin,
               "ts": int(time.time() * 1000)}
        self.rt.record_command(rec)
        self.rt.add_event({"kind": "command", "action": status,
                           "detail": f"{point_id} ← {value} ({status}{' '+reason if reason else ''})"})
        if self.mqtt and self.base:
            self.mqtt.publish(f"{self.base}/command_reply", rec)
        print(f"[控制] {point_id} ← {value} : {status} {reason}", flush=True)


# ===========================================================================
# 7) HTTP:静态 HMI + REST + SSE
# ===========================================================================
def make_handler(runtime: Runtime, controller: Controller, html_dir: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):       # 静音默认访问日志
            pass

        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path == "/api/health":
                devs = runtime.view()["devices"]
                offline = [{"addr": d["addr"], "name": d.get("name"),
                            "fails": d.get("fails", 0), "next_retry_s": d.get("next_retry_s", 0)}
                           for d in devs if d.get("offline")]
                return self._json({"ok": True, "ts": int(time.time() * 1000),
                                   "collector_age_ms": runtime.collector_age_ms(),
                                   "devices_total": len(devs),
                                   "devices_offline": len(offline),
                                   "offline": offline})
            if path == "/api/snapshot":
                return self._json(runtime.view())
            if path == "/api/stream":
                return self._sse()
            # 静态文件
            rel = path.lstrip("/") or "index.html"
            full = os.path.normpath(os.path.join(html_dir, rel))
            if not full.startswith(html_dir) or not os.path.isfile(full):
                self.send_error(404); return
            ctype = ("text/html" if full.endswith(".html") else
                     "application/json" if full.endswith(".json") else
                     "text/javascript" if full.endswith(".js") else
                     "text/css" if full.endswith(".css") else "application/octet-stream")
            data = open(full, "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def _sse(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            try:
                while True:
                    payload = json.dumps(runtime.view(), ensure_ascii=False)
                    self.wfile.write(("data: " + payload + "\n\n").encode())
                    self.wfile.flush()
                    time.sleep(1)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_POST(self):
            path = self.path.split("?", 1)[0]
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                return self._json({"error": "bad json"}, 400)
            if path == "/api/command":
                ok, reason = controller.apply(body.get("point_id", ""),
                                              body.get("value"), origin="hmi")
                return self._json({"ok": ok, "reason": reason})
            if path == "/api/event":     # HMI 模拟网线/USB/BLE 事件
                runtime.add_event(body)
                return self._json({"ok": True})
            self.send_error(404)

    return Handler


# ===========================================================================
# 8) 线程:采集、上云、心跳
# ===========================================================================
def collector_loop(source, runtime, interval, stop):
    while not stop.is_set():
        try:
            runtime.update(source.poll())
            runtime.mark_alive()              # 招4:喂"采集存活",看门狗据此判活
        except Exception as exc:
            print("[采集] 异常:", exc, flush=True)
        stop.wait(interval)


def watchdog_loop(runtime, cfg, stop):
    """招4 看门狗:采集新鲜才喂硬件狗;停滞则停喂(硬件超时复位)+ 软件告警。
    off-board 无 /dev/watchdog 时自动退化为只软件存活监控。"""
    rel = cfg.get("reliability", {})
    stale_limit = rel.get("stale_limit_s", max(6, cfg.get("poll_interval_s", 2) * 3))
    wd = cfg.get("watchdog") or {}
    wd_dev, interval = wd.get("device"), wd.get("interval_s", 5)
    fd = None
    if wd_dev and os.path.exists(wd_dev):
        try:
            fd = os.open(wd_dev, os.O_WRONLY)
            print("[看门狗] 硬件看门狗 %s 启用,喂狗周期 %ss" % (wd_dev, interval), flush=True)
        except OSError as exc:
            print("[看门狗] 打开 %s 失败:%s,退化为软件告警" % (wd_dev, exc), flush=True)
    else:
        print("[看门狗] 无硬件狗,软件存活监控:采集停滞 >%ss 告警" % stale_limit, flush=True)
    warned = False
    while not stop.is_set():
        age = runtime.collector_age_ms() / 1000.0
        if age <= stale_limit:
            if warned:
                runtime.add_event({"kind": "watchdog", "action": "recovered",
                                   "detail": "采集恢复 age=%.1fs" % age})
                warned = False
            if fd is not None:
                try:
                    os.write(fd, b"w")        # 仅采集新鲜时喂狗
                except OSError:
                    pass
        elif not warned:                       # 停滞:停喂(硬件复位)+ 记 critical
            print("[看门狗] 采集停滞 age=%.1fs > %ss,停止喂狗" % (age, stale_limit), flush=True)
            runtime.add_event({"kind": "watchdog", "action": "critical",
                               "detail": "采集停滞 %.1fs,看门狗停喂" % age})
            warned = True
        stop.wait(interval)


def uploader_loop(runtime, mqtt, base, t_tele, t_hb, stop):
    next_t = next_h = 0
    while not stop.is_set():
        now = time.monotonic()
        if now >= next_t:
            mqtt.publish(f"{base}/telemetry", runtime.telemetry())
            next_t = now + t_tele
        if now >= next_h:
            mqtt.publish(f"{base}/heartbeat",
                         {"device_id": runtime.cfg.get("device_id"), "online": True,
                          "ts": int(time.time() * 1000)})
            mqtt.ping()
            next_h = now + t_hb
        stop.wait(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "app_config.json"))
    ap.add_argument("--source", choices=["sim", "modbus"], default=None)
    ap.add_argument("--serial", default=None)
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()

    cfg = json.load(open(args.config))
    source_kind = args.source or cfg.get("source", "sim")
    devices = cfg["devices"]

    if source_kind == "modbus":
        dev = args.serial or cfg.get("serial", "/dev/ttyS1")
        source = ModbusSource(dev, cfg.get("baud", 9600), devices,
                              reliability=cfg.get("reliability"))
        print(f"[源] modbus 真串口 {dev}", flush=True)
    else:
        source = SimSource(devices)
        print("[源] sim 内置仿真(板子自造数据)", flush=True)

    runtime = Runtime(cfg)

    mqtt = None
    mcfg = cfg.get("mqtt")
    base = ""
    if mcfg:
        base = f"station/{cfg.get('device_id', 'rk3506-gw-01')}"
        controller_holder = {}

        def on_msg(topic, payload):
            if topic.endswith("/property/set"):
                try:
                    cmd = json.loads(payload)
                except ValueError:
                    return
                pl = cmd.get("payload", cmd)
                for pid, val in pl.items():
                    controller_holder["c"].apply(pid, val,
                                                 cmd.get("command_id", ""), "platform")

        mqtt = MqttClient(mcfg["host"], mcfg.get("port", 1883),
                          cfg.get("device_id", "rk3506-gw-01"), on_message=on_msg,
                          username=mcfg.get("username"), password=mcfg.get("password"))
        mqtt.subscribe(f"{base}/property/set")

    controller = Controller(runtime, source, cfg.get("control_map", {}), mqtt, base)
    if mqtt:
        controller_holder["c"] = controller

    stop = threading.Event()
    threading.Thread(target=collector_loop,
                     args=(source, runtime, cfg.get("poll_interval_s", 2), stop),
                     daemon=True).start()
    threading.Thread(target=watchdog_loop, args=(runtime, cfg, stop),
                     daemon=True).start()
    if mqtt:
        threading.Thread(target=uploader_loop,
                         args=(runtime, mqtt, base, cfg.get("telemetry_interval_s", 10),
                               cfg.get("heartbeat_interval_s", 30), stop),
                         daemon=True).start()

    html_dir = os.path.normpath(cfg.get("html_dir", os.path.join(HERE, "html")))
    port = args.port or cfg.get("http_port", 8092)
    handler = make_handler(runtime, controller, html_dir)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"[HTTP] http://0.0.0.0:{port}/  (HMI + /api/snapshot + /api/stream)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        stop.set()
        print("\n退出。")


if __name__ == "__main__":
    main()

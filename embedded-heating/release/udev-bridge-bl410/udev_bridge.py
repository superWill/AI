#!/usr/bin/env python3
"""udev → SSE event bridge for HMI.

跑在 BL410 上。订阅 udev 事件流（USB / 串口 / 网线），归一化成
HMI 用的 device_event JSON，通过 Server-Sent Events 推给浏览器。

零依赖：只用 Python 标准库 + 子进程调 udevadm。
兼容 Python 3.7+（用 future annotations 把 PEP 585 / 604 语法降级为字符串）。
"""
from __future__ import annotations

import glob
import json
import os
import queue
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8765

# ARPHRD_* constants from <uapi/linux/if_arp.h>
ARPHRD_ETHER = 1
ARPHRD_CAN = 280

_clients: list[queue.Queue] = []
_clients_lock = threading.Lock()


def _read_sysfs(path: str) -> str:
    """读 sysfs 一行；不存在或读不到就返回空串。"""
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def _net_arphrd(net_path: str) -> int:
    """读 /sys/class/net/<iface>/type，区分 ethernet (1) / CAN (280) / 其他。"""
    raw = _read_sysfs(os.path.join(net_path, "type"))
    try:
        return int(raw)
    except ValueError:
        return 0


def _net_carrier_up(net_path: str) -> bool:
    """ethernet 网卡：carrier=1 表示物理链路已建立（网线接好且对端 up）。"""
    return _read_sysfs(os.path.join(net_path, "carrier")) == "1"


def _net_operstate_up(net_path: str) -> bool:
    """通用：operstate=up 表示接口处于工作状态。CAN 一般用这个判断。"""
    return _read_sysfs(os.path.join(net_path, "operstate")) == "up"


def _usb_is_hub(usb_path: str) -> bool:
    """USB Hub 的 bDeviceClass=09，跟"业务 USB 设备"区分开。"""
    return _read_sysfs(os.path.join(usb_path, "bDeviceClass")) == "09"


def _broadcast(event: dict) -> None:
    """把一条事件推给所有当前连着的 SSE 客户端。"""
    line = f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode("utf-8")
    with _clients_lock:
        for q in list(_clients):
            try:
                q.put_nowait(line)
            except queue.Full:
                pass


def _normalize(props: dict) -> dict | None:
    """把 udev 原始属性翻译成 HMI 用的 device_event。
    返回 None 表示这条事件不需要传给 HMI（噪声）。
    """
    action = props.get("ACTION", "")
    subsystem = props.get("SUBSYSTEM", "")
    devtype = props.get("DEVTYPE", "")
    devname = props.get("DEVNAME", "")
    devpath = props.get("DEVPATH", "")
    vendor_id = props.get("ID_VENDOR_ID", "")
    product_id = props.get("ID_MODEL_ID", "")
    model = props.get("ID_MODEL", "") or props.get("ID_VENDOR", "")

    if action not in ("add", "remove", "change"):
        return None

    # USB 串口（CH340 / CP2102 / FTDI / 等）
    if subsystem == "tty" and devname.startswith("/dev/ttyUSB"):
        if action == "change":
            return None  # 串口的 change 事件没业务含义
        return {
            "kind": "serial",
            "action": action,
            "name": devname.split("/")[-1],
            "deviceName": model or "USB Serial",
            "deviceCode": f"{vendor_id}:{product_id}".strip(":"),
            "detail": (
                f"检测到 USB 串口 {devname}，已加入设备列表"
                if action == "add"
                else f"USB 串口 {devname} 已移除，关联设备置为离线"
            ),
        }

    # 网络接口：区分 ethernet 与 CAN，并按 carrier / operstate 判断真实链路
    if subsystem == "net" and devtype == "":
        name = (
            props.get("INTERFACE", "")
            or devname.split("/")[-1]
            or devpath.split("/")[-1]
        )
        if not name or name.startswith(("lo", "docker", "br-", "veth", "virbr")):
            return None

        sysfs_path = f"/sys{devpath}" if devpath.startswith("/") else f"/sys/class/net/{name}"
        arphrd = _net_arphrd(sysfs_path)

        # 只关心 ethernet + CAN，其他（PPP / WWAN / IPIP …）暂时不报
        if arphrd not in (ARPHRD_ETHER, ARPHRD_CAN):
            return None

        is_can = arphrd == ARPHRD_CAN
        kind = "can" if is_can else "ethernet"

        # 判断"在线":
        # - ethernet 看 carrier（网线插上 + 对端 link up 才为 1）
        # - CAN 看 operstate（CAN 没有 carrier 概念）
        is_up = _net_operstate_up(sysfs_path) if is_can else _net_carrier_up(sysfs_path)

        # change 事件按 carrier 翻成 add/remove；HMI 只懂 add/remove
        if action == "change":
            action = "add" if is_up else "remove"
        elif action == "add" and not is_up:
            # 接口存在但链路没起来：snapshot 阶段直接跳过，避免假"在线"
            return None

        return {
            "kind": kind,
            "action": action,
            "name": name,
            "deviceName": ("CAN " if is_can else "网卡 ") + name,
            "deviceCode": name,
            "detail": (
                (f"检测到 CAN 接口 {name} 已激活" if is_can else f"检测到 {name} 网线插入，链路已建立")
                if action == "add"
                else (f"CAN 接口 {name} 已停用" if is_can else f"检测到 {name} 网线断开，关联设备已置为离线")
            ),
        }

    # 通用 USB 设备（手机 / U 盘 / HID）—— 只在没有更具体匹配时报
    if subsystem == "usb" and devtype == "usb_device":
        # 忽略 root hub（Linux Foundation）和板载 USB Hub（bDeviceClass=09）
        if vendor_id == "1d6b":
            return None
        sysfs_path = f"/sys{devpath}" if devpath.startswith("/") else ""
        if sysfs_path and _usb_is_hub(sysfs_path):
            return None
        # USB-to-Ethernet 桥接芯片（CDC ECM/NCM/EEM）已经会通过 net 子系统
        # 单独报告 ethX，这里不要重复算成一台 USB 设备。
        # ID_USB_INTERFACES 形如 ":020600:020201:"，
        # 0206xx = CDC Ethernet Control Model
        # 0902xx = CDC Network Control Model
        usb_interfaces = props.get("ID_USB_INTERFACES", "")
        if ":0206" in usb_interfaces or ":0209" in usb_interfaces:
            return None
        if action == "change":
            return None
        label = model or f"USB {vendor_id}:{product_id}"
        return {
            "kind": "usb",
            "action": action,
            "name": devpath.split("/")[-1] if devpath else "usb",
            "deviceName": label,
            "deviceCode": f"{vendor_id}:{product_id}".strip(":"),
            "detail": (
                f"检测到 USB 设备 {label}"
                if action == "add"
                else f"USB 设备 {label} 已移除"
            ),
        }

    return None


def _udevadm_properties(sysfs_path: str) -> dict:
    """跑 udevadm info -q property 拿一条设备的全部 udev 属性。"""
    try:
        res = subprocess.run(
            ["udevadm", "info", "--query=property", sysfs_path],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return {}
    props: dict[str, str] = {}
    for line in res.stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            props[k.strip()] = v.strip()
    return props


def _snapshot_paths() -> list[str]:
    """枚举当前感兴趣的设备 /sys 路径。"""
    paths: list[str] = []
    # USB 串口
    paths += glob.glob("/sys/class/tty/ttyUSB*")
    paths += glob.glob("/sys/class/tty/ttyACM*")
    # 以太网卡（含 USB 网卡）
    for p in glob.glob("/sys/class/net/*"):
        name = os.path.basename(p)
        if name in ("lo",):
            continue
        if name.startswith(("docker", "br-", "veth", "virbr")):
            continue
        paths.append(p)
    # USB 设备（usb_device 级别，跳过 root hub 由 _normalize 处理）
    for p in glob.glob("/sys/bus/usb/devices/*"):
        if os.path.exists(os.path.join(p, "idVendor")):
            paths.append(p)
    return paths


def _send_snapshot(q: queue.Queue) -> None:
    """SSE 客户端刚连进来时，把当前所有连着的设备以 add 事件回放一次。"""
    for path in _snapshot_paths():
        props = _udevadm_properties(path)
        if not props:
            continue
        # 强制当作 add 事件（已经连着的设备视为刚接入）
        props["ACTION"] = "add"
        ev = _normalize(props)
        if not ev:
            continue
        ev["timestamp"] = time.time()
        ev["snapshot"] = True
        line = f"data: {json.dumps(ev, ensure_ascii=False)}\n\n".encode("utf-8")
        try:
            q.put_nowait(line)
        except queue.Full:
            break


def _udev_reader() -> None:
    """子进程跑 udevadm monitor，逐块解析属性。"""
    proc = subprocess.Popen(
        ["udevadm", "monitor", "--property", "--udev"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        bufsize=1,
    )
    props: dict[str, str] = {}
    in_block = False
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip("\n")
        if line.startswith("UDEV ") or line.startswith("KERNEL "):
            if props:
                ev = _normalize(props)
                if ev:
                    ev["timestamp"] = time.time()
                    _broadcast(ev)
                props = {}
            in_block = True
            continue
        if in_block and line == "":
            if props:
                ev = _normalize(props)
                if ev:
                    ev["timestamp"] = time.time()
                    _broadcast(ev)
                props = {}
            in_block = False
            continue
        if in_block and "=" in line:
            k, _, v = line.partition("=")
            props[k.strip()] = v.strip()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/events":
            self._serve_sse()
        elif self.path == "/health":
            self._serve_health()
        else:
            self.send_error(404, "Not Found")

    def _serve_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        q: queue.Queue = queue.Queue(maxsize=200)
        with _clients_lock:
            _clients.append(q)
        # 客户端刚连上：回放当前所有连着的设备一次（标记 snapshot=true），
        # 让 HMI 即便在 bridge 启动后才连进来也能看到完整设备列表。
        _send_snapshot(q)
        try:
            self.wfile.write(b": connected\n\n")
            self.wfile.flush()
            while True:
                try:
                    chunk = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": hb\n\n")
                    self.wfile.flush()
                    continue
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with _clients_lock:
                if q in _clients:
                    _clients.remove(q)

    def _serve_health(self) -> None:
        with _clients_lock:
            n = len(_clients)
        body = json.dumps({"ok": True, "clients": n}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:  # noqa: ARG002
        # Silence default access log; rely on systemd journal for our own logs.
        pass


def main() -> None:
    threading.Thread(target=_udev_reader, daemon=True).start()
    print(f"udev-bridge ready on 0.0.0.0:{PORT}  ( /events SSE,  /health )")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()


if __name__ == "__main__":
    main()

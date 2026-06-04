#!/usr/bin/env python3
"""嵌入式网关 WiFi 配置（wpa_cli 后端，纯标准库）。

为什么不用 ClawHarbor 那份 network.js：那是 nmcli(NetworkManager) + Node，
跑在 x86 Ubuntu 桌面上；本板是 buildroot/busybox 网关，只有 wpa_supplicant，
没有 NetworkManager、没包管理器。所以照搬它的"接口设计"，换成 wpa_cli 实现。

沿用 ClawHarbor 的 4 函数契约 + 好习惯：
  status() / scan() / connect(ssid, psk) / forget(ssid)
  - 密码绝不进命令行 argv / 配置明文：本地 PBKDF2 算出 PSK 哈希再写入。
  - 有线优先：status 里 eth 在线就报 ethernet。
  - online 与 DNS 分开探，便于定位"连上了但上不了网/DNS挂了"。

用法（板子上 root 跑）：
  python3 wifi.py status
  python3 wifi.py scan
  python3 wifi.py connect <SSID> <密码>     # 连接并写入 /etc/wpa_supplicant.conf(开机自连)
  python3 wifi.py forget <SSID>
  任意命令加 --json 输出机器可读 JSON（给上层网关程序调用）。
"""
import hashlib
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time

IFACE = "wlan0"
CONF = "/etc/wpa_supplicant.conf"          # 持久配置（update_config=1 → save_config 落盘）
CTRL = "/var/run/wpa_supplicant"


def sh(cmd, timeout=15, check=False):
    """跑命令，返回 (rc, stdout)。所有参数走列表，不过 shell。"""
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} -> rc={p.returncode}: {p.stderr.strip()[:200]}")
    return p.returncode, p.stdout


def wpa(*args, timeout=15):
    rc, out = sh(["wpa_cli", "-i", IFACE, *args], timeout=timeout)
    return out.strip()


def _supplicant_procs():
    """读 /proc/*/cmdline 可靠识别 wpa_supplicant 实例（busybox ps 会截断命令行）。
    返回 [(pid, iface, conf), ...]。"""
    procs = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                argv = [a.decode() for a in f.read().split(b"\0") if a]
        except OSError:
            continue
        if not argv or "wpa_supplicant" not in os.path.basename(argv[0]):
            continue
        iface = argv[argv.index("-i") + 1] if "-i" in argv else None
        conf = argv[argv.index("-c") + 1] if "-c" in argv else None
        procs.append((int(pid), iface, conf))
    return procs


def ensure_supplicant():
    """保证 wlan0 上有一个绑定到持久 CONF 的 wpa_supplicant 在跑。
    用别的配置起的实例一律杀掉重启 —— 否则 save_config 不会落到 CONF。"""
    on_conf = False
    for pid, iface, conf in _supplicant_procs():
        if iface != IFACE:
            continue
        if conf == CONF:
            on_conf = True
        else:                                    # 用临时/别的配置起的 → 杀掉
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
    if on_conf:
        return
    time.sleep(1)
    sh(["ip", "link", "set", IFACE, "up"], check=False)
    subprocess.Popen(["wpa_supplicant", "-B", "-i", IFACE, "-c", CONF],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(10):                          # 等控制套接字就绪
        if os.path.exists(f"{CTRL}/{IFACE}"):
            time.sleep(1)
            return
        time.sleep(0.5)


def _psk_hash(ssid, passphrase):
    """WPA-PSK = PBKDF2(HMAC-SHA1, 口令, SSID, 4096, 32B)。明文在本函数内消化掉，
    对外只出 64 位十六进制 —— 命令行和配置里都不会出现明文口令。"""
    if re.fullmatch(r"[0-9a-fA-F]{64}", passphrase):
        return passphrase.lower()                # 已经是 PSK 哈希
    return hashlib.pbkdf2_hmac("sha1", passphrase.encode(), ssid.encode(), 4096, 32).hex()


def _net_id_by_ssid(ssid):
    out = wpa("list_networks")
    for ln in out.splitlines()[1:]:
        f = ln.split("\t")
        if len(f) >= 2 and f[1] == ssid:
            return f[0]
    return None


# ---------- 4 个契约函数 ----------

def scan():
    ensure_supplicant()
    wpa("scan")
    time.sleep(4)
    out = wpa("scan_results")
    nets, seen = [], set()
    for ln in out.splitlines()[1:]:              # bssid freq signal flags ssid
        f = ln.split("\t")
        if len(f) < 5 or not f[4]:
            continue
        ssid = f[4]
        if ssid in seen:                         # 同名多 AP 去重，留信号最强
            continue
        seen.add(ssid)
        flags = f[3].upper()
        sec = ("wpa3" if "SAE" in flags else "wpa2" if "WPA2" in flags
               else "wpa" if "WPA" in flags else "wep" if "WEP" in flags else "open")
        nets.append({"ssid": ssid, "signal_dbm": int(f[2]),
                     "freq_mhz": int(f[1]), "security": sec})
    nets.sort(key=lambda n: n["signal_dbm"], reverse=True)
    return nets


def status():
    # 有线优先：eth0 有 carrier 且有全局 IPv4 → ethernet
    mode, ssid, signal = "offline", None, None
    _, op = sh(["cat", "/sys/class/net/eth0/operstate"], check=False)
    eth_up = op.strip() == "up"
    st = wpa("status")
    kv = dict(l.split("=", 1) for l in st.splitlines() if "=" in l)
    if kv.get("wpa_state") == "COMPLETED" and kv.get("ssid"):
        mode, ssid = "wifi", kv["ssid"]
        sig = wpa("signal_poll")
        m = re.search(r"RSSI=(-?\d+)", sig)
        signal = int(m.group(1)) if m else None
    if eth_up:
        mode = "ethernet"                        # 有线在就以有线为准
    # wlan0 自己的 IP（单独看，别被有线口盖住）
    _, wa = sh(["ip", "-4", "-o", "addr", "show", "dev", IFACE], check=False)
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", wa)
    wlan_ipv4 = m.group(1) if m else None
    # 全局路由 IPv4 + 默认网关
    _, addr = sh(["ip", "-4", "-o", "addr", "show", "scope", "global"], check=False)
    m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", addr)
    ipv4 = m.group(1) if m else None
    _, rt = sh(["ip", "-4", "route", "show", "default"], check=False)
    m = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", rt)
    gw = m.group(1) if m else None
    # online 与 DNS 分开探
    online = sh(["ping", "-c1", "-W2", "223.5.5.5"], check=False)[0] == 0
    try:
        socket.setdefaulttimeout(3)
        socket.getaddrinfo("aliyun.com", 80)
        dns_ok = True
    except OSError:
        dns_ok = False
    if not ipv4:
        mode = "offline"
    return {"mode": mode, "ssid": ssid, "signal_dbm": signal,
            "wlan_ipv4": wlan_ipv4, "ipv4": ipv4, "gateway": gw,
            "online": online, "dns_ok": dns_ok}


def connect(ssid, passphrase):
    ensure_supplicant()
    psk = _psk_hash(ssid, passphrase)
    nid = _net_id_by_ssid(ssid)
    if nid is None:
        nid = wpa("add_network").strip().splitlines()[-1]
    wpa("set_network", nid, "ssid", f'"{ssid}"')
    wpa("set_network", nid, "psk", psk)          # 传哈希，不是明文
    wpa("set_network", nid, "key_mgmt", "WPA-PSK")
    wpa("enable_network", nid)
    wpa("select_network", nid)
    ok = False
    for _ in range(20):
        if dict(l.split("=", 1) for l in wpa("status").splitlines()
                if "=" in l).get("wpa_state") == "COMPLETED":
            ok = True
            break
        time.sleep(1)
    if not ok:
        return {"connected": False, "reason": "关联失败(密码错/信号弱/超时)", **status()}
    sh(["udhcpc", "-i", IFACE, "-n", "-q", "-t", "8"], check=False, timeout=20)
    wpa("save_config")                           # 落盘 → 开机自连
    return {"connected": True, **status()}


def forget(ssid):
    ensure_supplicant()
    nid = _net_id_by_ssid(ssid)
    if nid is None:
        return {"forgotten": False, "reason": "无此 SSID 记录"}
    wpa("remove_network", nid)
    wpa("save_config")
    return {"forgotten": True, "ssid": ssid}


# ---------- CLI ----------

def main():
    args = [a for a in sys.argv[1:] if a != "--json"]
    as_json = "--json" in sys.argv
    cmd = args[0] if args else "status"
    if cmd == "scan":
        res = scan()
    elif cmd == "status":
        res = status()
    elif cmd == "connect" and len(args) >= 3:
        res = connect(args[1], args[2])
    elif cmd == "forget" and len(args) >= 2:
        res = forget(args[1])
    else:
        print(__doc__)
        sys.exit(2)

    if as_json:
        print(json.dumps(res, ensure_ascii=False))
        return
    # 人类可读
    if cmd == "scan":
        print(f"=== 扫到 {len(res)} 个热点 ===")
        for n in res:
            print(f"  {n['signal_dbm']:>4} dBm  {n['security']:<5}  {n['ssid']}")
    elif cmd == "status":
        print(f"上行={res['mode']}  WiFi-SSID={res['ssid']}  信号={res['signal_dbm']}dBm")
        print(f"wlan0-IP={res['wlan_ipv4']}  全局IP={res['ipv4']}  网关={res['gateway']}")
        print(f"外网={'通' if res['online'] else '不通'}  DNS={'通' if res['dns_ok'] else '不通'}")
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

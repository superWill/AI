#!/usr/bin/env python3
"""阶段6 采集可靠性 · 故障注入长跑验证(纯标准库,Mac 上无需真板子)。

链路:serial_bridge(pty 对) ── sim_104(注入 offline/bad_crc) ── app.py(--source modbus)
走的是和真串口完全相同的 Modbus 帧/CRC/超时/重试代码路径。

两段:
  A 集成:故障隔离+退避+恢复——坏设备被降频探测(总线流量骤降),好设备不受影响,
          清除故障后一个退避窗口内自动回在线。
  B 单元:看门狗——采集停滞 > stale_limit 记 critical,恢复后重新喂狗。

用法:python3 tests/reliability_soak.py
"""
import json
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HERE)
PY = sys.executable
PORT = 8097
PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("  ✅ " if ok else "  ❌ ") + name + (("  — " + detail) if detail else ""), flush=True)


def get(path):
    with urllib.request.urlopen("http://127.0.0.1:%d%s" % (PORT, path), timeout=3) as r:
        return json.load(r)


def wait_port(timeout=8):
    end = time.time() + timeout
    while time.time() < end:
        try:
            get("/api/health"); return True
        except Exception:
            time.sleep(0.3)
    return False


def make_sim_config(faults):
    """基于 sim_104_config.json 改写故障:faults={addr: 'offline'|'bad_crc'|'none'}。"""
    cfg = json.load(open(os.path.join(APP_DIR, "sim_104_config.json")))
    for s in cfg["slaves"]:
        if s["addr"] in faults:
            s["fault"] = faults[s["addr"]]
    fd, path = tempfile.mkstemp(suffix=".json", prefix="sim_rel_")
    os.write(fd, json.dumps(cfg, ensure_ascii=False).encode()); os.close(fd)
    return path


def make_app_config():
    """快测用:小退避、短轮询,让离线/退避/恢复在 ~20s 内可见。"""
    cfg = json.load(open(os.path.join(APP_DIR, "app_config.json")))
    cfg["source"] = "modbus"
    cfg["poll_interval_s"] = 1
    cfg.pop("mqtt", None)                       # 测试不连 MQTT
    for d in cfg["devices"]:                    # 每设备短超时:坏设备探测轮也便宜
        d["timeout_ms"] = 250
        d["retries"] = 1
    cfg["reliability"] = {"offline_after": 3, "backoff_base_s": 3,
                          "backoff_max_s": 8, "retries": 1, "stale_limit_s": 4}
    fd, path = tempfile.mkstemp(suffix=".json", prefix="app_rel_")
    os.write(fd, json.dumps(cfg, ensure_ascii=False).encode()); os.close(fd)
    return path


def start_sim(pty_a, sim_cfg):
    return subprocess.Popen([PY, "-u", os.path.join(APP_DIR, "sim_104.py"), pty_a, sim_cfg],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def part_a():
    print("\n[A] 集成:故障隔离 + 退避 + 恢复", flush=True)
    procs = []
    bridge_file = tempfile.mktemp(prefix="bridge_")
    bridge = subprocess.Popen([PY, "-u", os.path.join(APP_DIR, "tools", "serial_bridge.py"), bridge_file],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    procs.append(bridge)
    pty_a = bridge.stdout.readline().strip()      # 给 sim
    pty_b = bridge.stdout.readline().strip()      # 给网关
    if not (pty_a and pty_b):
        check("serial_bridge 起 pty", False, "未拿到 pty 路径"); return procs
    print("  pty: sim=%s gw=%s" % (pty_a, pty_b), flush=True)

    sim_cfg = make_sim_config({8: "offline", 7: "bad_crc"})   # #8 不应答, #7 故意坏CRC
    sim = start_sim(pty_a, sim_cfg); procs.append(sim)
    app_cfg = make_app_config()
    app = subprocess.Popen([PY, "-u", os.path.join(APP_DIR, "app.py"), "--config", app_cfg,
                            "--source", "modbus", "--serial", pty_b, "--port", str(PORT)],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                           cwd=APP_DIR); procs.append(app)
    if not wait_port():
        out = app.stdout.read() if app.stdout else ""
        check("app 启动(modbus)", False, "端口未就绪\n" + out[:800]); return procs
    check("app 启动(modbus)", True)

    # 跑 ~12s 让坏设备走完 offline_after 次并进入退避
    time.sleep(12)
    snap = {d["addr"]: d for d in get("/api/snapshot")["devices"]}
    health = get("/api/health")

    check("坏表#8(offline)被判离线", snap[8]["offline"] is True,
          "health=%s fails=%s" % (snap[8]["health"], snap[8].get("fails")))
    check("坏CRC#7 被判离线", snap[7]["offline"] is True,
          "health=%s fails=%s" % (snap[7]["health"], snap[7].get("fails")))
    good = [a for a in (1, 2, 3, 4, 5, 6) if snap[a]["ok"]]
    check("好设备 1-6 全在线", len(good) == 6, "在线=%s" % good)
    p1 = snap[1]["points"].get("pri_supply_temp", {})
    check("好设备点位质量 good 且有值", p1.get("q") == "good" and p1.get("v") is not None,
          "pri_supply_temp=%s" % p1)
    check("/api/health 报告离线数=2", health["devices_offline"] == 2,
          "offline=%s" % [o["addr"] for o in health["offline"]])

    # 退避证据:统计 sim 收到各地址的请求数,坏设备应远少于好设备
    # (在线设备每轮都点;离线设备一个退避窗口才探一次)
    counts = drain_sim_counts(sim, seconds=10)
    r1, r8 = counts.get(1, 0), counts.get(8, 0)
    check("退避降频:坏#8 被探测次数 << 好#1", r1 >= 5 and r8 * 2 <= r1,
          "10s 内 addr1=%d 次, addr8=%d 次" % (r1, r8))

    # 恢复:重启 sim,#8 故障清除 → 一个退避窗口内回在线
    sim.send_signal(signal.SIGINT); _wait(sim, 2)
    sim_cfg2 = make_sim_config({8: "none", 7: "bad_crc"})
    sim2 = start_sim(pty_a, sim_cfg2); procs.append(sim2)
    recovered = False
    end = time.time() + 12
    while time.time() < end:
        time.sleep(1)
        d8 = {d["addr"]: d for d in get("/api/snapshot")["devices"]}[8]
        if d8["ok"] and not d8["offline"]:
            recovered = True; break
    check("故障清除后 #8 自动恢复在线", recovered)
    return procs


def drain_sim_counts(sim, seconds):
    """统计实时窗口内每个从站被请求的次数(从'收 AA ..'行解析)。
    先清空预热期积压的旧行,再只数 seconds 内的实时流量,否则积压会污染结果。"""
    os.set_blocking(sim.stdout.fileno(), False)
    while sim.stdout.readline():                  # 丢弃积压
        pass
    counts = {}
    end = time.time() + seconds
    while time.time() < end:
        line = sim.stdout.readline()
        if not line:
            time.sleep(0.05); continue
        m = re.match(r"收\s+([0-9A-F]{2})\s", line)
        if m:
            counts[int(m.group(1), 16)] = counts.get(int(m.group(1), 16), 0) + 1
    os.set_blocking(sim.stdout.fileno(), True)
    return counts


def part_b():
    print("\n[B] 单元:看门狗(采集停滞→停喂+critical,恢复→重新喂)", flush=True)
    sys.path.insert(0, APP_DIR)
    import app as appmod
    rt = appmod.Runtime({"poll_interval_s": 1})
    cfg = {"reliability": {"stale_limit_s": 1}, "watchdog": {"device": "", "interval_s": 0.3}}
    import threading
    stop = threading.Event()
    t = threading.Thread(target=appmod.watchdog_loop, args=(rt, cfg, stop), daemon=True)
    rt.mark_alive(); t.start()
    time.sleep(0.6)
    fresh_event = any(e.get("action") == "critical" for e in rt.events)
    check("采集新鲜时不报 critical", not fresh_event)
    time.sleep(2)                                   # 停止 mark_alive,采集"停滞"
    crit = any(e.get("action") == "critical" for e in rt.events)
    check("采集停滞 >stale_limit 记 critical", crit,
          "events=%s" % [e.get("action") for e in rt.events])
    rt.mark_alive(); time.sleep(1)                  # 恢复
    rec = any(e.get("action") == "recovered" for e in rt.events)
    check("采集恢复记 recovered", rec)
    stop.set()


def _wait(p, t):
    try:
        p.wait(t)
    except Exception:
        pass


def kill_all(procs):
    for p in procs:
        if p.poll() is None:
            p.send_signal(signal.SIGINT)
    time.sleep(1)
    for p in procs:
        if p.poll() is None:
            p.kill()


def main():
    procs = []
    try:
        procs = part_a()
    finally:
        kill_all(procs)
    try:
        part_b()
    except Exception as exc:
        check("part_b 运行", False, repr(exc))
    print("\n==== 结果:%d 过 / %d 败 ====" % (len(PASS), len(FAIL)), flush=True)
    if FAIL:
        print("失败项:" + ", ".join(FAIL), flush=True)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

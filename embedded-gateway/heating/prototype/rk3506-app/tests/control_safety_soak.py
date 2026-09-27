#!/usr/bin/env python3
"""阶段8 控制与安全联锁 · 验证(纯标准库)。

覆盖编译期 → 运行期的"写前联锁 + 写后回读确认",全部走编译管线
(compiler → loader → app.py),安全策略由编译产物声明、Controller 强制执行。

段:
  0 编译期:current_draft 校验通过;故意写坏 interlock 引用→编译期报错。
  A 集成(sim 源,走管线):严格模式/限幅/限速拒绝;写后回读确认收敛→confirmed。
  B 单元(确定性,桩快照):写前联锁(急停/质量码)拒;写后回读确认超时→feedback_timeout。
  C 桥接:loader 生成 device 透传 timeout_ms/retries。

用法:python3 tests/control_safety_soak.py
"""
import copy
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(HERE)
PY = sys.executable
PORT = 8098
PASS, FAIL = [], []
sys.path.insert(0, APP_DIR)


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(("  ✅ " if ok else "  ❌ ") + name + (("  — " + detail) if detail else ""), flush=True)


def post(path, obj):
    data = json.dumps(obj).encode()
    req = urllib.request.Request("http://127.0.0.1:%d%s" % (PORT, path), data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.load(r)


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


# ---------------------------------------------------------------------------
def part0_compile():
    print("\n[0] 编译期:声明即合同", flush=True)
    import compiler
    draft = json.load(open(os.path.join(APP_DIR, "current_draft.json")))
    check("current_draft 校验通过", compiler.validate(draft) == [],
          str(compiler.validate(draft)[:2]))
    bad = copy.deepcopy(draft)
    for biz in bad["business_devices"]:
        sp = (biz.get("bindings") or {}).get("setpoint")
        if sp and sp.get("interlocks"):
            sp["interlocks"][0]["point"] = "nonexistent_point"   # 写坏引用
    errs = compiler.validate(bad)
    check("坏 interlock 引用→编译期报错",
          any("interlock" in e and "nonexistent_point" in e for e in errs),
          str(errs))


# ---------------------------------------------------------------------------
def part_a():
    print("\n[A] 集成(sim 源,走 compiler→loader→app.py)", flush=True)
    import loader
    build = tempfile.mkdtemp(prefix="cs_build_")
    rc = subprocess.run([PY, os.path.join(APP_DIR, "compiler.py"),
                         os.path.join(APP_DIR, "current_draft.json"), "--out", build],
                        capture_output=True, text=True)
    if rc.returncode != 0:
        check("compiler 产出", False, rc.stderr[:300]); return []
    cfg = loader.load_runtime_cfg(build, source="sim")
    cfg["poll_interval_s"] = 0.5            # 加快 sim 收敛,让 5s confirm 窗口内可见
    cfg["html_dir"] = "html"
    cfg_path = os.path.join(build, "gen.json")
    json.dump(cfg, open(cfg_path, "w"), ensure_ascii=False)

    app = subprocess.Popen([PY, "-u", os.path.join(APP_DIR, "app.py"),
                            "--config", cfg_path, "--source", "sim", "--port", str(PORT)],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                           cwd=APP_DIR)
    if not wait_port():
        check("app 启动", False, (app.stdout.read() if app.stdout else "")[:600]); return [app]
    check("app 启动(管线生成配置)", True)

    # 这些被拒命令都在写入前挡下,不更新 rate 历史(_last),不污染后续
    r = post("/api/command", {"point_id": "valve_open_sp", "value": 50})
    check("严格模式:policy 外点位被拒", r["ok"] is False, r.get("reason"))
    r = post("/api/command", {"point_id": "pump_freq_sp", "value": 99})
    check("限幅:pump_freq_sp=99(>50)被拒", r["ok"] is False, r.get("reason"))

    # 首条成功命令(无 rate 历史)→ 接受;sim 让 pump_freq 朝 36 收敛 → 写后回读确认
    r = post("/api/command", {"point_id": "pump_freq_sp", "value": 36})
    check("写入被接受(联锁通过:estop/water_low=0)", r["ok"] is True, r.get("reason"))
    confirmed = False
    end = time.time() + 8
    while time.time() < end:
        time.sleep(0.5)
        cmds = get("/api/snapshot").get("commands", [])
        if any(c["point_id"] == "pump_freq_sp" and c["value"] == 36
               and c["status"] == "confirmed" for c in cmds):
            confirmed = True; break
    fb = next((d["points"].get("pump_freq") for d in get("/api/snapshot")["devices"]
               if "pump_freq" in d.get("points", {})), None)
    check("写后回读确认:反馈收敛→confirmed", confirmed, "pump_freq=%s" % fb)

    # 紧接着大跳变 → 限速拒(此时 _last=36)
    r = post("/api/command", {"point_id": "pump_freq_sp", "value": 10})
    check("限速:36→10 大跳变被拒", r["ok"] is False, r.get("reason"))
    return [app]


# ---------------------------------------------------------------------------
class StubSource:
    def write_setpoint(self, pid, val, cmap=None):
        return True


def _runtime_with(points_by_addr, policy):
    import app as appmod
    rt = appmod.Runtime({})
    rt.snapshot = {addr: {"addr": addr, "name": str(addr), "points": pts}
                   for addr, pts in points_by_addr.items()}
    ctl = appmod.Controller(rt, StubSource(), control_map={}, safety_policy=policy)
    return rt, ctl


def part_b():
    print("\n[B] 单元(确定性桩):写前联锁 + 写后回读确认超时", flush=True)
    policy = json.load(open(os.path.join(APP_DIR, "current_draft.json")))  # 取真策略
    import compiler
    pol = compiler.build_safety_policy(policy)["commands"]

    # 联锁:急停触发
    rt, ctl = _runtime_with({5: {"estop": {"v": 1, "q": "good"},
                                 "water_low": {"v": 0, "q": "good"}}}, pol)
    ok, reason = ctl.apply("pump_freq_sp", 30)
    check("联锁:estop=1 → 拒写", ok is False and "联锁" in reason, reason)

    # 联锁点质量码非 good
    rt, ctl = _runtime_with({5: {"estop": {"v": 0, "q": "timeout"},
                                 "water_low": {"v": 0, "q": "good"}}}, pol)
    ok, reason = ctl.apply("pump_freq_sp", 30)
    check("联锁:estop 质量码非 GOOD → 拒写", ok is False and "GOOD" in reason, reason)

    # 联锁全满足 → 放行
    rt, ctl = _runtime_with({5: {"estop": {"v": 0, "q": "good"},
                                 "water_low": {"v": 0, "q": "good"}},
                             2: {"pump_freq": {"v": 30, "q": "good"}}}, pol)
    ok, reason = ctl.apply("pump_freq_sp", 30)
    check("联锁:全满足 → 放行", ok is True, reason)

    # 写后回读确认超时:反馈卡在 0 不收敛
    pol2 = copy.deepcopy(pol)
    pol2["pump_freq_sp"]["confirm_timeout_s"] = 1
    rt, ctl = _runtime_with({5: {"estop": {"v": 0, "q": "good"},
                                 "water_low": {"v": 0, "q": "good"}},
                             2: {"pump_freq": {"v": 0, "q": "good"}}}, pol2)
    ctl._confirm_feedback("pump_freq_sp", 40, "", "test")   # 同步调用,确定性
    timed_out = any(e.get("action") == "feedback_timeout" for e in rt.events)
    check("写后回读确认:反馈不收敛 → feedback_timeout", timed_out,
          "events=%s" % [e.get("action") for e in rt.events])


# ---------------------------------------------------------------------------
def part_c():
    print("\n[C] 桥接:loader 透传可靠性参数", flush=True)
    import loader
    build = tempfile.mkdtemp(prefix="cs_buildc_")
    subprocess.run([PY, os.path.join(APP_DIR, "compiler.py"),
                    os.path.join(APP_DIR, "current_draft.json"), "--out", build],
                   capture_output=True, text=True)
    cfg = loader.load_runtime_cfg(build, source="modbus")
    allok = all("timeout_ms" in d and "retries" in d for d in cfg["devices"])
    check("生成 device 带 timeout_ms/retries", allok,
          "示例=%s" % {k: cfg["devices"][0].get(k) for k in ("timeout_ms", "retries")})


def kill_all(procs):
    for p in procs:
        if p and p.poll() is None:
            p.send_signal(signal.SIGINT)
    time.sleep(1)
    for p in procs:
        if p and p.poll() is None:
            p.kill()


def main():
    part0_compile()
    procs = []
    try:
        procs = part_a()
    finally:
        kill_all(procs)
    part_b()
    part_c()
    print("\n==== 结果:%d 过 / %d 败 ====" % (len(PASS), len(FAIL)), flush=True)
    if FAIL:
        print("失败项:" + ", ".join(FAIL), flush=True)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()

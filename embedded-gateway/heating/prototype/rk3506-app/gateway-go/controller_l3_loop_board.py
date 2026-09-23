#!/usr/bin/env python3
"""板上双端完整闭环 L3:pty 桥 + 从站(A) + Go/Python 闭环(B) 对拍。
用法: controller_l3_loop_board.py <gatewayc-arm> <app.py>
仅 PTY,不触碰 /dev/ttyS*。"""
import sys, os, json, subprocess, time, tempfile
GO = os.path.abspath(sys.argv[1]); APP = os.path.abspath(sys.argv[2])
HERE = os.path.dirname(os.path.abspath(__file__))

def wait_file(p):
    for _ in range(300):
        if os.path.exists(p):
            s = open(p).read().strip()
            if s: return s
        time.sleep(0.02)
    raise RuntimeError(p + " 未生成")

def scenario(dev, case, feedback_reg):
    return {
        "dev": dev, "baud": 9600, "read_timeout_s": 0.5,
        "device": {"addr": 1, "name": "换热站", "type": "采集模块", "start": 10, "count": 11,
                   "points": [{"id": "sec_supply_temp", "reg": feedback_reg, "scale": 1, "unit": "degC"}]},
        "control_map": {"sec_supply_temp_sp": {"addr": 1, "reg": 10, "scale": 1}},
        "policy": {"sec_supply_temp_sp": {"lo": 20, "hi": 75, "feedback": "sec_supply_temp",
                                          "confirm_timeout_s": 4, "confirm_tolerance": 1}},
        "command": {"point_id": "sec_supply_temp_sp", "value": 60, "command_id": case, "origin": "platform"},
    }

def run_case(case, feedback_reg):
    for f in ("/tmp/pty_a", "/tmp/pty_b"):
        if os.path.exists(f): os.unlink(f)
    bridge = subprocess.Popen([sys.executable, HERE + "/pty_link.py"], stderr=subprocess.DEVNULL)
    pa = wait_file("/tmp/pty_a"); pb = wait_file("/tmp/pty_b")
    scfg = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({"regs": {"1": [0] * 40}}, scfg); scfg.close()
    slave = subprocess.Popen([sys.executable, HERE + "/modbus_slave_on.py", pa, scfg.name], stderr=subprocess.DEVNULL)
    time.sleep(0.6)
    sf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump(scenario(pb, case, feedback_reg), sf, ensure_ascii=False); sf.close()
    try:
        go = json.loads(subprocess.check_output([GO, "controllerloop", sf.name], text=True))
        py_out = subprocess.check_output([sys.executable, HERE + "/controller_loop_harness.py", sf.name, APP], text=True)
        py = next(json.loads(l[len("L3RESULT "):]) for l in reversed(py_out.splitlines()) if l.startswith("L3RESULT "))
    finally:
        slave.terminate(); bridge.terminate()
        time.sleep(0.2)
    return go, py

result = {}
ok_all = True
for case, reg, expect in (("confirmed", 10, "confirmed"), ("timeout", 20, "feedback_timeout")):
    go, py = run_case(case, reg)
    same = go == py
    has_expect = expect in go["statuses"]
    result[case] = {"go": go, "py": py, "go==py": same, "expect_%s" % expect: has_expect}
    ok_all = ok_all and same and has_expect
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(0 if ok_all else 1)

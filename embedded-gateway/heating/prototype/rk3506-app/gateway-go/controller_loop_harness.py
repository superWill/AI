#!/usr/bin/env python3
"""Python 端双端闭环 L3:app.py 真实 Controller + ModbusSource + 采集线程,串口回读确认。
用法: controller_loop_harness.py <scenario.json> <app.py>"""
import sys, os, json, time, threading, importlib.util
sc = json.load(open(sys.argv[1]))
spec = importlib.util.spec_from_file_location("rk3506_app", os.path.abspath(sys.argv[2]))
app = importlib.util.module_from_spec(spec); spec.loader.exec_module(app)

source = app.ModbusSource(sc["dev"], int(sc["baud"]), [sc["device"]], timeout=sc.get("read_timeout_s", 0.5))
snap = {"devices": []}
lock = threading.Lock()
stop = threading.Event()

def collector():
    while not stop.is_set():
        samples = source.poll()
        with lock:
            snap["devices"] = list(samples.values())
        time.sleep(0.3)

class RT:
    def __init__(self): self.records = []; self.events = []
    def view(self):
        with lock: return {"devices": list(snap["devices"])}
    def record_command(self, rec): self.records.append(dict(rec))
    def add_event(self, e): self.events.append(dict(e))

ct = threading.Thread(target=collector, daemon=True); ct.start()
time.sleep(0.4)
rt = RT()
ctrl = app.Controller(rt, source, sc["control_map"], safety_policy=sc["policy"])
cmd = sc["command"]
ok, reason = ctrl.apply(cmd["point_id"], cmd["value"], cmd["command_id"], cmd["origin"])
deadline = time.time() + sc["policy"][cmd["point_id"]].get("confirm_timeout_s", 5) + 3
while time.time() < deadline:
    if any(r["status"] in ("confirmed", "feedback_timeout") for r in rt.records): break
    time.sleep(0.2)
stop.set(); ct.join(timeout=1)
fb_name = sc["policy"][cmd["point_id"]].get("feedback")
fb = None
with lock:
    for d in snap["devices"]:
        p = d.get("points", {}).get(fb_name)
        if p: fb = p.get("v")
print("L3RESULT " + json.dumps({"apply_ok": ok, "apply_reason": reason,
                  "statuses": [r["status"] for r in rt.records], "feedback": fb}, ensure_ascii=False))

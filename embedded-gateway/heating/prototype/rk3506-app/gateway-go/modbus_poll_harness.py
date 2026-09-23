#!/usr/bin/env python3
"""ModbusSource.poll 状态机对拍：用 app.py 真实 poll(),stub read_holding + patch 时钟。"""
import sys, os, json, time, threading
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import app
M = app.ModbusSource
sc = json.load(open(sys.argv[1], encoding="utf-8"))
s = M.__new__(M)
s.devices = sc["devices"]; s.timeout = 1.0; s.lock = threading.Lock()
rel = sc.get("reliability", {})
s.offline_after = rel.get("offline_after", 3); s.backoff_base = rel.get("backoff_base_s", 5)
s.backoff_max = rel.get("backoff_max_s", 30); s.default_retries = rel.get("retries", 1)
s.dev_state = {d["addr"]: {"fails":0,"offline":False,"next_due":0.0,"backoff_idx":0,"last_sample":None}
               for d in sc["devices"]}
cur = {"r": {}}
def fake_read(addr, start, count, timeout=None, retries=0):
    r = cur["r"].get(str(addr), {})
    if "err" in r: return None, r["err"]
    return list(r["regs"]), None
s.read_holding = fake_read
res = []
for step in sc["steps"]:
    cur["r"] = step["reads"]
    time.monotonic = (lambda m=step["mono"]: lambda: m)()
    time.time = (lambda w=step["wall"]: lambda: w)()
    res.append(s.poll())
print(json.dumps(res, ensure_ascii=False))

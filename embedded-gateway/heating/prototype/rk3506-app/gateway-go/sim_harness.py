#!/usr/bin/env python3
"""SimSource 对拍 harness：固定 t0/采样时刻跑 app.py 的 SimSource.poll()。
用法: sim_harness.py <t0> <tpoll> <devices.json>"""
import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import app
t0 = float(sys.argv[1]); tp = float(sys.argv[2]); devs = json.load(open(sys.argv[3], encoding="utf-8"))
time.time = lambda: t0
s = app.SimSource(devs)
time.time = lambda: tp
print(json.dumps(s.poll(), ensure_ascii=False, indent=2))

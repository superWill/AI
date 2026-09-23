#!/usr/bin/env python3
"""对拍 Go Runtime 与 app.py 真实 Runtime:脚本化 ops,patch mono/wall 钟,逐项比对。"""
import sys, os, json, time, importlib.util, subprocess, tempfile, argparse
HERE = os.path.dirname(os.path.abspath(__file__))

def load_app():
    spec = importlib.util.spec_from_file_location("rk3506_app", os.path.join(HERE, "..", "app.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def run_python(scenario):
    app = load_app()
    cur = {"mono": 0.0, "wall": 0.0}
    real_mono, real_time = time.monotonic, time.time
    time.monotonic = lambda: cur["mono"]; time.time = lambda: cur["wall"]
    try:
        rt = app.Runtime(scenario.get("cfg", {}))
        results = []
        for o in scenario["ops"]:
            if "mono" in o: cur["mono"] = o["mono"]
            if "wall" in o: cur["wall"] = o["wall"]
            op = o["op"]
            if op == "mark_alive": rt.mark_alive()
            elif op == "update": rt.update(o["snap"])
            elif op == "add_event": rt.add_event(o["ev"])
            elif op == "record_command": rt.record_command(o["rec"])
            elif op == "get": results.append({"op": "get", "out": rt.get()})
            elif op == "collector_age_ms": results.append({"op": "collector_age_ms", "out": rt.collector_age_ms()})
            elif op == "telemetry": results.append({"op": "telemetry", "out": rt.telemetry()})
            elif op == "view": results.append({"op": "view", "out": rt.view()})
    finally:
        time.monotonic = real_mono; time.time = real_time
    return results

def run_go(scenario, go_bin):
    with tempfile.NamedTemporaryFile("w", suffix=".json") as f:
        json.dump(scenario, f, ensure_ascii=False); f.flush()
        cmd = [go_bin, "runtimecase", f.name] if go_bin else ["go", "run", ".", "runtimecase", f.name]
        return json.loads(subprocess.check_output(cmd, cwd=HERE, text=True))

def norm(x):  # 对象不看键序;数组保序;数字按值
    if isinstance(x, dict): return ("o", tuple(sorted((k, norm(v)) for k, v in x.items())))
    if isinstance(x, list): return ("a", tuple(norm(v) for v in x))
    if isinstance(x, bool): return ("b", x)
    if isinstance(x, (int, float)): return ("n", round(float(x), 6))
    if x is None: return ("z",)
    return ("s", str(x))

def scenarios():
    dev1 = {"addr": 1, "name": "采集", "type": "采集模块", "ok": True, "points": {"t": {"v": 50, "u": "", "q": "good"}}}
    dev2 = {"addr": 2, "name": "泵", "ok": False, "points": {}}  # 无 type → 默认 ""
    basic = {
        "cfg": {"device_id": "rk3506-gw-01"},
        "ops": [
            {"op": "mark_alive", "mono": 100.0},
            {"op": "update", "snap": {"1": dev1, "2": dev2}},
            {"op": "add_event", "wall": 1000.0, "ev": {"kind": "alarm", "action": "a1", "detail": "d1"}},
            {"op": "add_event", "wall": 1001.0, "ev": {"kind": "command", "action": "a2", "detail": "d2"}},
            {"op": "record_command", "rec": {"command_id": "c1", "point_id": "p", "value": 50, "status": "accepted", "reason": "", "origin": "hmi", "ts": 1000}},
            {"op": "telemetry", "wall": 1002.0},
            {"op": "telemetry", "wall": 1003.0},
            {"op": "view", "wall": 1004.0, "mono": 105.0},
            {"op": "collector_age_ms", "mono": 110.0},
            {"op": "get"},
        ],
    }
    caps_ops = [{"op": "add_event", "wall": float(2000 + i), "ev": {"i": i}} for i in range(25)]
    caps_ops += [{"op": "record_command", "rec": {"command_id": "k%d" % i, "status": "accepted"}} for i in range(12)]
    caps_ops += [{"op": "view", "wall": 3000.0}]
    caps = {"cfg": {"device_id": "g"}, "ops": caps_ops}
    return {"basic": basic, "caps": caps}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--go-bin"); a = ap.parse_args()
    failed = False
    for name, sc in scenarios().items():
        p, g = run_python(sc), run_go(sc, a.go_bin)
        if norm(p) == norm(g):
            print("[PASS]", name)
        else:
            failed = True; print("[FAIL]", name)
            print("py:", json.dumps(p, ensure_ascii=False)[:400])
            print("go:", json.dumps(g, ensure_ascii=False)[:400])
    raise SystemExit(1 if failed else 0)

if __name__ == "__main__":
    main()

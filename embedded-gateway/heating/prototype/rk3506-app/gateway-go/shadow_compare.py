#!/usr/bin/env python3
"""轨 B 阶段一 · 板外影子比对器(只读)。

订阅 Go 影子输出与生产 MQTT、轮询生产 HTTP 快照,对齐出差异。
**本脚本不发布任何控制、不碰板子文件**,纯消费 + 对账。

  python3 shadow_compare.py --broker <host> [--port 1883] \
      --device rk3506-gw-01 --http http://<板子IP>:8092 \
      [--tol 0.01] [--summary-every 30] [--out shadow_diff.jsonl]

对比维度(对应 track-b-shadow-plan §3):
  - 控制决策:Go(_shadow/go kind=decision)按 command_id 对 Python(command_reply)的 status。
  - 采集值/状态:Go view(_shadow/go kind=view)的每点 v/q 对 Python /api/snapshot。
  - 资源:记录 Go RSS 曲线。
只在分歧或定期摘要时落盘(NAND 上不跑本脚本)。
"""
import argparse, json, time, sys, threading, urllib.request

try:
    import paho.mqtt.client as mqtt
except ImportError:
    sys.exit("需要 paho-mqtt:pip install paho-mqtt")


def status_class(s):
    """把决策状态归一成'放行 / 拦截'两类——影子写被模拟,故比'安全门结论'而非最终写结果。"""
    blocked = {"blocked_by_safety", "blocked_by_interlock", "rate_limited",
               "blocked_by_rate", "write_failed"}
    return "blocked" if s in blocked else "allowed"


class Comparator:
    def __init__(self, a):
        self.a = a
        self.base = f"station/{a.device}"
        self.py_replies = {}      # command_id -> status(Python 实际决策)
        self.go_decisions = {}    # command_id -> status(Go 影子决策)
        self.lock = threading.Lock()
        self.n_view = 0
        self.n_view_diff = 0
        self.n_dec = 0
        self.n_dec_diff = 0
        self.last_rss = 0
        self.out = open(a.out, "a") if a.out else None

    def log(self, rec):
        rec["t"] = time.time()
        line = json.dumps(rec, ensure_ascii=False)
        print(line, flush=True)
        if self.out:
            self.out.write(line + "\n"); self.out.flush()

    def py_snapshot(self):
        try:
            with urllib.request.urlopen(self.a.http + "/api/snapshot", timeout=2) as r:
                return json.load(r)
        except Exception:
            return None

    def py_points(self, snap):
        pts = {}
        for d in (snap or {}).get("devices", []):
            for pid, p in (d.get("points") or {}).items():
                pts[pid] = p
        return pts

    def on_go_view(self, go):
        snap = self.py_snapshot()
        if snap is None:
            return
        pyp = self.py_points(snap)
        diffs = []
        for pid, gp in (go.get("points") or {}).items():
            pp = pyp.get(pid)
            if pp is None:
                diffs.append({"point": pid, "why": "py 快照缺该点"}); continue
            if str(gp.get("q")) != str(pp.get("q")):
                diffs.append({"point": pid, "why": "质量码", "go": gp.get("q"), "py": pp.get("q")}); continue
            try:
                if abs(float(gp.get("v")) - float(pp.get("v"))) > self.a.tol:
                    diffs.append({"point": pid, "why": "值", "go": gp.get("v"), "py": pp.get("v")})
            except (TypeError, ValueError):
                if gp.get("v") != pp.get("v"):
                    diffs.append({"point": pid, "why": "值(非数)", "go": gp.get("v"), "py": pp.get("v")})
        with self.lock:
            self.n_view += 1
            self.last_rss = go.get("rss_kb", self.last_rss)
            if diffs:
                self.n_view_diff += 1
                self.log({"kind": "view_diff", "ts": go.get("ts"), "diffs": diffs})

    def on_go_decision(self, go):
        cid = go.get("command_id")
        with self.lock:
            self.go_decisions[cid] = go.get("status")
            self._match_decision(cid)

    def on_py_reply(self, rec):
        cid = rec.get("command_id")
        with self.lock:
            self.py_replies[cid] = rec.get("status")
            self._match_decision(cid)

    def _match_decision(self, cid):
        if cid in self.go_decisions and cid in self.py_replies:
            g, p = self.go_decisions[cid], self.py_replies[cid]
            self.n_dec += 1
            if status_class(g) != status_class(p):
                self.n_dec_diff += 1
                self.log({"kind": "decision_diff", "command_id": cid,
                          "go": g, "py": p, "go_class": status_class(g), "py_class": status_class(p)})

    def summary(self):
        with self.lock:
            self.log({"kind": "summary", "views": self.n_view, "view_diffs": self.n_view_diff,
                      "decisions": self.n_dec, "decision_diffs": self.n_dec_diff,
                      "go_rss_kb": self.last_rss,
                      "pending_go": len(set(self.go_decisions) - set(self.py_replies)),
                      "pending_py": len(set(self.py_replies) - set(self.go_decisions))})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--broker", required=True)
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--device", default="rk3506-gw-01")
    ap.add_argument("--http", required=True, help="生产 HMI 基址,如 http://192.168.1.10:8092")
    ap.add_argument("--tol", type=float, default=0.01)
    ap.add_argument("--summary-every", type=float, default=30)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    c = Comparator(a)

    try:
        cl = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
    except Exception:
        cl = mqtt.Client()

    def on_connect(client, *_):
        client.subscribe(c.base + "/_shadow/go")
        client.subscribe(c.base + "/command_reply")

    def on_msg(client, _u, m):
        try:
            d = json.loads(m.payload)
        except Exception:
            return
        if m.topic.endswith("/_shadow/go"):
            if d.get("kind") == "view":
                c.on_go_view(d)
            elif d.get("kind") == "decision":
                c.on_go_decision(d)
        elif m.topic.endswith("/command_reply"):
            c.on_py_reply(d)

    cl.on_connect = on_connect
    cl.on_message = on_msg
    cl.reconnect_delay_set(1, 5)
    cl.connect_async(a.broker, a.port)
    cl.loop_start()
    print(f"[compare] 订阅 {c.base}/_shadow/go + /command_reply,Python 快照 {a.http}", flush=True)
    try:
        while True:
            time.sleep(a.summary_every)
            c.summary()
    except KeyboardInterrupt:
        c.summary()


if __name__ == "__main__":
    main()

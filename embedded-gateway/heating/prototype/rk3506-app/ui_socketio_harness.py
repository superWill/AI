#!/usr/bin/env python3
"""增量3 对拍:gatewayc ui 的 socket.io == Python nexus(原始 EIO4/SIO5 polling 协议)。

  python3 ui_socketio_harness.py <ui_base> <nexus_base>

握手 "0"+JSON 结构等;connect("40")回 ack;轮询收 "42" 事件,比 {tag-change/node-change/
system-metrics} 事件名 + tags/nodes 结构 + system-metrics 键。
"""
import sys
import json
import time
import urllib.request

RS = "\x1e"


def http(base, path, method="GET", data=None):
    req = urllib.request.Request(base + path, data=(data.encode() if data else None), method=method)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "replace")


def collect(base):
    """握手 → connect → 等广播 → 轮询,返回 {open_obj, events:{name:data}}。"""
    body = http(base, "/socket.io/?EIO=4&transport=polling")
    assert body.startswith("0"), "握手非 0 包: " + body[:20]
    open_obj = json.loads(body[1:])
    sid = open_obj["sid"]
    http(base, "/socket.io/?sid=" + sid, "POST", "40")   # SIO connect
    events = {}
    ack = False
    deadline = time.time() + 8
    while time.time() < deadline and not (events.get("tag-change") and events.get("node-change") and events.get("system-metrics")):
        body = http(base, "/socket.io/?sid=" + sid)       # 长轮询
        for pkt in body.split(RS):
            if pkt.startswith("40"):
                ack = True
            elif pkt.startswith("42"):
                name, dat = json.loads(pkt[2:])
                events[name] = dat
    return open_obj, ack, events


def s_nodes(ns):
    return sorted((n["id"], n["name"], n["deviceType"], n["slaveId"]) for n in ns)


def s_tags(ts):
    return sorted((t["id"], t["nodeId"], t["name"], t["address"], t["type"], t["access"]) for t in ts)


def main():
    ui, nx = sys.argv[1], sys.argv[2]
    ou, acku, eu = collect(ui)
    on, ackn, en = collect(nx)
    res = []
    # 握手结构(sid 除外)
    ko = lambda o: {k: o[k] for k in o if k != "sid"}
    res.append(("握手结构", ko(ou) == ko(on)))
    res.append(("connect ack(40)", acku and ackn))
    res.append(("事件名集合", set(eu) == set(en) == {"tag-change", "node-change", "system-metrics"}))
    res.append(("tag-change 结构", s_tags(eu["tag-change"]) == s_tags(en["tag-change"])))
    res.append(("node-change 结构", s_nodes(eu["node-change"]) == s_nodes(en["node-change"])))
    res.append(("system-metrics 键", set(eu["system-metrics"]) == set(en["system-metrics"])))
    for name, ok in res:
        print(("  ✅ " if ok else "  ❌ ") + name)
    ok = all(o for _, o in res)
    print("=> 增量3 socket.io 对拍", "通过 ✅" if ok else "不通过 ❌")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

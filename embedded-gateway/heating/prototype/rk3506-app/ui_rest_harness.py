#!/usr/bin/env python3
"""增量2 对拍:gatewayc ui 的 edge-os REST == Python nexus 同端点。

  python3 ui_rest_harness.py <ui_base> <nexus_base>

/api/me·/scada·/history 精确等;/api/login 格式等;/api/init 结构等(值/时戳因两路独立 sim
不同,只比结构);/api/init 未鉴权 401;/api/tags/write 可写点 ok、不可写点同错。
"""
import sys
import json
import urllib.request
import urllib.error


def call(base, path, method="GET", data=None, tok=None):
    h = {}
    if tok:
        h["Authorization"] = "Bearer " + tok
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(
        base + path, data=(json.dumps(data).encode() if data is not None else None),
        headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or "null")


def s_nodes(ns):
    return sorted((n["id"], n["name"], n["type"], n["deviceType"], n["slaveId"]) for n in ns)


def s_tags(ts):
    return sorted((t["id"], t["nodeId"], t["name"], t["address"], t["type"],
                   t["access"], t["unit"], t.get("group")) for t in ts)


def main():
    ui, nx = sys.argv[1], sys.argv[2]
    res = []
    res.append(("/api/me", call(ui, "/api/me")[1] == call(nx, "/api/me")[1]))
    for p in ("/api/scada", "/api/history"):
        res.append((p, call(ui, p)[1] == call(nx, p)[1] == []))
    lu = call(ui, "/api/login", "POST", {"username": "x", "password": "y"})[1]
    ln = call(nx, "/api/login", "POST", {"username": "x", "password": "y"})[1]
    res.append(("/api/login 格式", "token" in lu and "token" in ln
                and len(lu["token"]) == len(ln["token"]) and lu["user"] == ln["user"]))
    su, iu = call(ui, "/api/init", tok=lu["token"])
    sn, inx = call(nx, "/api/init", tok=ln["token"])
    res.append(("/api/init nodes 结构", s_nodes(iu["nodes"]) == s_nodes(inx["nodes"])))
    res.append(("/api/init tags 结构", s_tags(iu["tags"]) == s_tags(inx["tags"])))
    res.append(("/api/init apps/rules", iu.get("apps") == inx.get("apps") == []
                and iu.get("rules") == inx.get("rules") == []))
    res.append(("/api/init 未鉴权→401", call(ui, "/api/init")[0] == call(nx, "/api/init")[0] == 401))
    # 可写点(从 ui 的 tags 取一个 access=RW)
    rw = next((t for t in iu["tags"] if t["access"] == "RW"), None)
    if rw:
        vu = call(ui, "/api/tags/write", "POST", {"tagId": rw["id"], "value": 30})[1]
        vn = call(nx, "/api/tags/write", "POST", {"tagId": rw["id"], "value": 30})[1]
        res.append(("/api/tags/write 可写点(%s)" % rw["id"], vu.get("ok") is True and vn.get("ok") is True))
    bu = call(ui, "/api/tags/write", "POST", {"tagId": "tag-1-nonexistent", "value": 5})[1]
    bn = call(nx, "/api/tags/write", "POST", {"tagId": "tag-1-nonexistent", "value": 5})[1]
    res.append(("/api/tags/write 不可写点同错", bu == bn))

    for name, ok in res:
        print(("  ✅ " if ok else "  ❌ ") + name)
    print("=> 增量2 REST 对拍", "通过 ✅" if all(o for _, o in res) else "不通过 ❌")
    sys.exit(0 if all(o for _, o in res) else 1)


if __name__ == "__main__":
    main()

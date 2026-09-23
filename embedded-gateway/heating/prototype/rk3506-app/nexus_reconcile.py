#!/usr/bin/env python3
"""边界第 2 步 · 并行对账(只读,零生产改动)。

证明:从 **gatewayc(Go 核心)** 的 /api/snapshot 取 view,经 nexus 的 build_nodes_tags
产出的 edge-os nodes/tags **结构**,与从 **内嵌取数(app.py/nexus 同口径)** 产出的结构一致
(值 / 时戳 / status 等时变量除外)。结构一致 = 第 3 步把 nexus 取数切到 gatewayc 安全。

  python3 nexus_reconcile.py --core http://127.0.0.1:8091 \
      --embedded http://127.0.0.1:8092 [--products build/versions/<N>]

两路 view 来自各自独立的 sim 实例,故**值必然不同**;本脚本只比结构(id/name/type/
access/unit/group/节点拓扑),不比值。
"""
import argparse, json, sys, urllib.request
import nexus_server as N


def fetch_view(url, timeout=3):
    with urllib.request.urlopen(url.rstrip("/") + "/api/snapshot", timeout=timeout) as r:
        return json.load(r)


def node_struct(nodes):
    return sorted((n["id"], n["name"], n["type"], n["deviceType"], n["slaveId"]) for n in nodes)


def tag_struct(tags):
    # 只取结构字段:id/节点/名/地址/类型/读写/单位/分组;**不含 value/timestamp**
    return sorted((t["id"], t["nodeId"], t["name"], t["address"], t["type"],
                   t["access"], t["unit"], t.get("group")) for t in tags)


def diff(a, b, label):
    sa, sb = set(a), set(b)
    only_c, only_e = sa - sb, sb - sa
    if not only_c and not only_e:
        print(f"  {label} 结构一致 ✅（{len(a)} 项）")
        return True
    print(f"  {label} 结构不一致 ❌")
    for x in list(only_c)[:5]:
        print(f"    仅 gatewayc: {x}")
    for x in list(only_e)[:5]:
        print(f"    仅 内嵌:    {x}")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", required=True, help="gatewayc 核心基址,如 http://127.0.0.1:8091")
    ap.add_argument("--embedded", required=True, help="内嵌取数基址(app.py/nexus),如 http://127.0.0.1:8092")
    ap.add_argument("--products", default=None, help="编译产物目录(可选;驱动 label/类型/分组)")
    ap.add_argument("--endpoint", default="sim")
    a = ap.parse_args()

    if a.products:
        import os
        pr = json.load(open(os.path.join(a.products, "point_registry.json")))
        dmp = os.path.join(a.products, "display_model.json")
        N.configure_maps(pr, json.load(open(dmp)) if os.path.exists(dmp) else None)
        print(f"[对账] 已加载产物 {a.products}（label/类型/分组生效）")
    else:
        print("[对账] 无产物：用默认 CONTROLLABLE/类型（仍可证结构等价）")

    cv, ev = fetch_view(a.core), fetch_view(a.embedded)
    cn, ct = N.build_nodes_tags(cv, a.endpoint)
    en, et = N.build_nodes_tags(ev, a.endpoint)
    print(f"[对账] gatewayc: {len(cn)} 节点 / {len(ct)} 标签;内嵌: {len(en)} 节点 / {len(et)} 标签")

    n_ok = diff(node_struct(cn), node_struct(en), "nodes")
    t_ok = diff(tag_struct(ct), tag_struct(et), "tags")
    ok = n_ok and t_ok
    print("=> 第2步并行对账:", "通过 ✅（gatewayc 取数与内嵌结构等价,可进第3步切换)" if ok else "不通过 ❌")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

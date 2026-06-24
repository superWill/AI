#!/usr/bin/env python3
"""增量1 对拍:Go `gatewayc nodestags` == Python build_nodes_tags(同 view + 同产物)。

  python3 ui_nodestags_harness.py <gatewayc-bin> <snapshot.json> [products_dir]

同一 view 输入两路产出 edge-os nodes/tags,按 id 排序后语义比较(数字按值;数组顺序无关)。
"""
import sys
import os
import json
import subprocess

import nexus_server as N


def norm(o):
    if isinstance(o, bool):
        return o
    if isinstance(o, (int, float)):
        return round(float(o), 6)
    if isinstance(o, dict):
        return {k: norm(v) for k, v in o.items()}
    if isinstance(o, list):
        return sorted((norm(x) for x in o),
                      key=lambda v: json.dumps(v, sort_keys=True, ensure_ascii=False))
    return o


def main():
    gw, snap = sys.argv[1], sys.argv[2]
    prod = sys.argv[3] if len(sys.argv) > 3 else None
    view = json.load(open(snap))

    if prod:
        pr = json.load(open(os.path.join(prod, "point_registry.json")))
        dmp = os.path.join(prod, "display_model.json")
        N.configure_maps(pr, json.load(open(dmp)) if os.path.exists(dmp) else None)
    pn, pt = N.build_nodes_tags(view, "sim")
    py = {"nodes": pn, "tags": pt}

    cmd = [gw, "nodestags", snap] + ([prod] if prod else []) + ["sim"]
    go = json.loads(subprocess.check_output(cmd, text=True))

    tag = "有产物" if prod else "无产物(默认映射)"
    nodes_ok = norm(py["nodes"]) == norm(go["nodes"])
    tags_ok = norm(py["tags"]) == norm(go["tags"])
    print("[%s] nodes %d/%d %s | tags %d/%d %s" % (
        tag, len(go["nodes"]), len(py["nodes"]), "✅" if nodes_ok else "❌",
        len(go["tags"]), len(py["tags"]), "✅" if tags_ok else "❌"))
    if not (nodes_ok and tags_ok):
        pj = {k: {x["id"]: x for x in py[k]} for k in ("nodes", "tags")}
        gj = {k: {x["id"]: x for x in go[k]} for k in ("nodes", "tags")}
        for k in ("nodes", "tags"):
            for i in set(pj[k]) | set(gj[k]):
                if norm(pj[k].get(i)) != norm(gj[k].get(i)):
                    print("  差异 %s %s:\n    py=%s\n    go=%s" % (k, i, pj[k].get(i), gj[k].get(i)))
        sys.exit(1)
    print("=> 增量1 build_nodes_tags 对拍通过 ✅")


if __name__ == "__main__":
    main()

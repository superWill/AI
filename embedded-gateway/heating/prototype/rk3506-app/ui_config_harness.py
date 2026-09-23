#!/usr/bin/env python3
"""增量4 对拍:gatewayc ui 配置管理 == Python nexus 同端点(各自独立 build,同草稿驱动)。

  python3 ui_config_harness.py <ui_base> <nexus_base> <draft.json>

validate(好/坏)同结论;compile 后 status 摘要等(active/latest/devices/points/...);
products 摘要等;draft 回读结构等;devices 加设备同结论。激活(重启核心)见 #2 已验。
"""
import sys
import json
import urllib.request
import urllib.error


def call(base, path, method="GET", data=None, tok="Bearer x" * 2):
    h = {"Authorization": tok}
    if data is not None:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(
        base + path, data=(json.dumps(data).encode() if data is not None else None),
        headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or "null")


def main():
    ui, nx, draftp = sys.argv[1], sys.argv[2], sys.argv[3]
    draft = json.load(open(draftp))
    res = []

    # validate 好草稿
    vu = call(ui, "/api/config/validate", "POST", draft)[1]
    vn = call(nx, "/api/config/validate", "POST", draft)[1]
    res.append(("validate 好草稿", vu.get("ok") is True and vn.get("ok") is True and vu == vn))
    # validate 坏草稿(删 config_version)
    bad = {k: v for k, v in draft.items() if k != "config_version"}
    bu = call(ui, "/api/config/validate", "POST", bad)[1]
    bn = call(nx, "/api/config/validate", "POST", bad)[1]
    res.append(("validate 坏草稿同错", set(bu.get("errors", [])) == set(bn.get("errors", [])) and not bu.get("ok")))

    # compile 好草稿 → status
    cu = call(ui, "/api/config/compile", "POST", draft)[1]
    cn = call(nx, "/api/config/compile", "POST", draft)[1]
    res.append(("compile ok", cu.get("ok") is True and cn.get("ok") is True))
    su, sn = cu.get("status", {}), cn.get("status", {})
    keys = ["active_version", "latest_version"]
    res.append(("compile 后 status(active/latest)", all(su.get(k) == sn.get(k) for k in keys)))
    lcu, lcn = su.get("latest_compiled") or {}, sn.get("latest_compiled") or {}
    sk = ["version", "config_version", "devices", "points", "display_cards", "safety_commands"]
    res.append(("latest_compiled 摘要", all(lcu.get(k) == lcn.get(k) for k in sk)))

    # products 摘要
    pu = call(ui, "/api/config/products")[1] or {}
    pn = call(nx, "/api/config/products")[1] or {}
    # active 为 null 时两边都 null;compile 不设 active,故 products(读 active)应都 null
    res.append(("products(active=null 时)", pu == pn))

    # draft 回读
    du = call(ui, "/api/config/draft")[1]
    dn = call(nx, "/api/config/draft")[1]
    res.append(("draft has_draft", du.get("has_draft") == dn.get("has_draft") is True))
    res.append(("draft 设备数", len((du.get("draft") or {}).get("hardware_devices", []))
                == len((dn.get("draft") or {}).get("hardware_devices", []))))

    for name, ok in res:
        print(("  ✅ " if ok else "  ❌ ") + name)
    allok = all(o for _, o in res)
    print("=> 增量4 配置端点对拍", "通过 ✅" if allok else "不通过 ❌")
    if not allok:
        print("  (ui status=%s\n   nx status=%s)" % (su, sn))
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""CI · D3 编译对拍:gatewayc compile/load 产物 == Python 回退产物(逐一相等)。

  python3 tests/ci_d3_check.py [gatewayc-bin]

从 rk3506-app 运行;比较同一草稿经 gatewayc 与 Python 两路编译的全部产物。
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # rk3506-app 上 sys.path
import nexus_server as N  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def compile_products(binpath, draft):
    d = tempfile.mkdtemp()
    N.CONFIG_BUILD_DIR = d
    N.GATEWAYC_BIN = binpath
    N.CONFIG_DRAFT_PATH = os.path.join(d, "current_draft.json")
    ok, errs, _ = N.compile_draft(draft)
    if not ok:
        raise SystemExit("compile 失败(%s): %s" % (binpath, errs))
    vd = os.path.join(d, "versions", "1")
    return {f: json.load(open(os.path.join(vd, f))) for f in os.listdir(vd)}


def norm(o):
    """语义归一:数组按值排序(顺序无关)、数字按值、键序无关——与编译器对拍 compare.py 同标准。
    (Go map 迭代顺序非确定,产物数组顺序不应作为差异。)"""
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
    gw = sys.argv[1] if len(sys.argv) > 1 else "gatewayc"
    draft = json.load(open(os.path.join(HERE, "..", "samples", "heating_draft.json")))
    g = compile_products(gw, draft)              # gatewayc compile/load
    p = compile_products("nonexistent-bin-xyz", draft)  # FileNotFoundError → Python 回退
    assert g.keys() == p.keys(), "产物文件集不同: %s vs %s" % (sorted(g), sorted(p))
    diff = [k for k in g if norm(g[k]) != norm(p[k])]   # 语义比较(顺序/数字格式无关)
    assert not diff, "D3 产物语义不一致: %s" % diff
    print("D3 产物语义一致(gatewayc compile/load == Python):", sorted(g.keys()))


if __name__ == "__main__":
    main()

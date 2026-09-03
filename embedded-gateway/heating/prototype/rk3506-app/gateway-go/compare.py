#!/usr/bin/env python3
"""语义对拍两个产物目录：对象不看键序、数组按多重集、数字按数值比较。
用法: compare.py DIR_A DIR_B
"""
import json, sys, os

FILES = ["point_registry.json", "poll_plan.json", "display_model.json", "safety_policy.json"]


def norm(x):
    """把 JSON 值规范成可哈希、可比较的形态（数字统一 float，数组按多重集排序）。"""
    if isinstance(x, dict):
        return ("obj", tuple(sorted((k, norm(v)) for k, v in x.items())))
    if isinstance(x, list):
        return ("arr", tuple(sorted(norm(v) for v in x)))
    if isinstance(x, bool):
        return ("bool", x)
    if isinstance(x, (int, float)):
        return ("num", float(x))
    if x is None:
        return ("null",)
    return ("str", str(x))


def main():
    a, b = sys.argv[1], sys.argv[2]
    ok = True
    for f in FILES:
        pa, pb = os.path.join(a, f), os.path.join(b, f)
        ja = json.load(open(pa, encoding="utf-8"))
        jb = json.load(open(pb, encoding="utf-8"))
        if norm(ja) == norm(jb):
            print(f"  ✅ {f}  一致")
        else:
            ok = False
            print(f"  ❌ {f}  不一致")
            # 粗定位：逐顶层键比
            if isinstance(ja, dict) and isinstance(jb, dict):
                for k in set(ja) | set(jb):
                    if norm(ja.get(k)) != norm(jb.get(k)):
                        print(f"       差异键: {k}")
    print("=== 对拍结果:", "全部一致 ✅" if ok else "有差异 ❌", "===")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

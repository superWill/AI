#!/usr/bin/env python3
"""配置编译器 —— config_draft.json → 运行产物(纯标准库,零依赖)。

输入:  config_draft.json   (契约见 schema/config_draft.schema.json)
输出:  point_registry.json  poll_plan.json  display_model.json  safety_policy.json

设计原则(PRD §22/§23/§30):
  - 纯函数: validate(draft)->errors[]; compile(draft)->products。运行时不再解释草稿。
  - 不依赖 jsonschema: RK3506 零依赖,校验手写,覆盖 schema 的 x-compiler-constraints。
  - 编译器只产中性产物;让产物适配回 app.py 内核的是 loader.py(适配层)。

用法:
  python3 compiler.py samples/heating_draft.json --out build
  python3 compiler.py samples/heating_draft.json --validate-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# 与 schema 对齐的枚举(只列编译器真正依赖的)
PROTO_TEMPLATES = {
    "rs485_8ai_modbus", "rs485_8di_modbus", "rs485_8do_modbus", "rs485_ao_modbus",
    "modbus_tcp_generic", "heat_meter_modbus", "energy_meter_modbus",
    "vfd_modbus", "private_mcu",
}
BUSINESS_TEMPLATES = {
    "temperature_point", "pressure_point", "circulation_pump", "makeup_pump",
    "control_valve", "heat_meter", "energy_meter", "vfd", "safety_io",
}
ROLES = {"measurement", "feedback", "command", "setpoint", "fault", "derived"}
WRITABLE_ROLES = {"command", "setpoint"}
DATA_WIDTH = {"bool": 1, "uint16": 1, "int16": 1, "uint32": 2, "int32": 2, "float32": 2}
PAGES = {"overview", "primary_loop", "secondary_loop", "pumps", "makeup",
         "devices", "alarms", "system"}


# ===========================================================================
# 校验(结构必填 + x-compiler-constraints)
# ===========================================================================
def validate(draft: dict) -> list[str]:
    errs: list[str] = []

    if not isinstance(draft, dict):
        return ["顶层必须是对象"]
    for k in ("config_version", "industry", "buses", "hardware_devices", "business_devices"):
        if k not in draft:
            errs.append(f"缺少必填字段 {k}")
    if errs:
        return errs

    industry = draft["industry"]
    buses = draft.get("buses") or []
    hws = draft.get("hardware_devices") or []
    bizs = draft.get("business_devices") or []

    # --- 总线 ---
    bus_ids: set[str] = set()
    for b in buses:
        bid = b.get("bus_id")
        if not bid:
            errs.append("bus 缺少 bus_id"); continue
        if bid in bus_ids:
            errs.append(f"bus_id 重复: {bid}")          # 约束: bus_id 全局唯一
        bus_ids.add(bid)
        if b.get("type") == "rs485":
            for f in ("baud", "parity", "data_bits", "stop_bits"):
                if f not in b:
                    errs.append(f"rs485 总线 {bid} 缺少 {f}")

    # --- 硬件设备 + 通道 ---
    dev_channels: dict[str, dict] = {}   # device_id -> {channel: chan}
    dev_ids: set[str] = set()
    bus_slaves: dict[str, set] = {}      # bus_id -> {slave}
    for d in hws:
        did = d.get("device_id")
        if not did:
            errs.append("hardware_device 缺少 device_id"); continue
        if did in dev_ids:
            errs.append(f"device_id 重复: {did}")        # 约束: device_id 全局唯一
        dev_ids.add(did)
        if d.get("hardware_template") not in PROTO_TEMPLATES:
            errs.append(f"{did}: 未知 hardware_template {d.get('hardware_template')!r}")
        if d.get("bus_id") not in bus_ids:
            errs.append(f"{did}: bus_id {d.get('bus_id')!r} 未声明")  # 约束: 引用完整性
        slave = d.get("slave")
        if slave is not None:
            bag = bus_slaves.setdefault(d.get("bus_id"), set())
            if slave in bag:
                errs.append(f"总线 {d.get('bus_id')} 从站地址重复: {slave}")  # 约束: 同总线 slave 唯一
            bag.add(slave)
        chans: dict[str, dict] = {}
        for c in d.get("channels", []) or []:
            ch = c.get("channel")
            if not ch:
                errs.append(f"{did}: 通道缺少 channel"); continue
            if ch in chans:
                errs.append(f"{did}: 通道 {ch} 重复")
            chans[ch] = c
            if c.get("data_type") not in DATA_WIDTH:
                errs.append(f"{did}.{ch}: 未知 data_type {c.get('data_type')!r}")
            if ch[:2] in ("AI", "AO"):                  # 约束: AI/AO 必填量程
                if "raw_range" not in c or "eng_range" not in c:
                    errs.append(f"{did}.{ch}: AI/AO 必须配置 raw_range 与 eng_range")
        dev_channels[did] = chans

    # --- 业务设备 + 绑定 ---
    point_ids: set[str] = set()
    biz_ids: set[str] = set()
    for biz in bizs:
        bzid = biz.get("business_id", "?")
        if not biz.get("business_id"):
            errs.append("business_device 缺少 business_id")
        elif bzid in biz_ids:
            errs.append(f"business_id 重复: {bzid}")       # 约束: business_id 全局唯一
        biz_ids.add(bzid)
        if biz.get("business_template") not in BUSINESS_TEMPLATES:
            errs.append(f"{bzid}: 未知 business_template {biz.get('business_template')!r}")
        biz_ind = biz.get("industry", industry)
        if biz_ind != industry:
            errs.append(f"{bzid}: industry {biz_ind!r} 与顶层 {industry!r} 不一致")  # 约束: 行业一致
        bindings = biz.get("bindings") or {}
        if not bindings:
            errs.append(f"{bzid}: 至少需要一个 binding")
        for role, bd in bindings.items():
            if role not in ROLES:
                errs.append(f"{bzid}: 未知绑定角色 {role!r}")
            pid = bd.get("point_id")
            if not pid:
                errs.append(f"{bzid}.{role}: 缺少 point_id"); continue
            if pid in point_ids:
                errs.append(f"point_id 全局重复: {pid}")  # 约束: point_id 全局唯一
            point_ids.add(pid)
            frm = bd.get("from")
            if role == "derived":
                if not bd.get("expr"):
                    errs.append(f"{bzid}.{pid}: derived 点必须有 expr")
            elif frm:
                dd, _, cc = frm.partition(".")
                if dd not in dev_channels:
                    errs.append(f"{bzid}.{pid}: from 引用未知设备 {dd}")     # 约束: 引用完整性
                elif cc not in dev_channels[dd]:
                    errs.append(f"{bzid}.{pid}: from 引用未知通道 {dd}.{cc}")
            else:
                errs.append(f"{bzid}.{pid}: 非 derived 点必须有 from")
            if role in WRITABLE_ROLES:                  # 约束: command/setpoint 必须有限值
                if "limit_lo" not in bd or "limit_hi" not in bd:
                    errs.append(f"{bzid}.{pid}: {role} 必须配置 limit_lo/limit_hi(安全限值)")
                if "feedback" not in bindings:
                    errs.append(f"{bzid}: 含 {role} 的控制对象应绑定 feedback(反馈点)")
        disp = biz.get("display")
        if disp is None and not biz.get("backend_only"):
            errs.append(f"{bzid}: 必须有 display 或标记 backend_only")  # 约束: 显示卡片
        elif disp and disp.get("page") not in PAGES:
            errs.append(f"{bzid}: 未知显示页面 {disp.get('page')!r}")

    return errs


# ===========================================================================
# 编译(假设已 validate 通过)
# ===========================================================================
def _channels_index(draft: dict) -> dict[str, dict]:
    idx = {}
    for d in draft["hardware_devices"]:
        for c in d.get("channels", []) or []:
            idx[f"{d['device_id']}.{c['channel']}"] = (d, c)
    return idx


def build_point_registry(draft: dict) -> dict:
    idx = _channels_index(draft)
    points = {}
    for biz in draft["business_devices"]:
        for role, bd in (biz.get("bindings") or {}).items():
            pid = bd["point_id"]
            entry = {
                "point_id": pid,
                "name": bd.get("label") or pid,
                "role": role,
                "business_id": biz["business_id"],
                "business_template": biz["business_template"],
                "writable": role in WRITABLE_ROLES,
                "quality_rules": {"non_good_on_timeout": True,
                                  "stale_after_polls": 2},
            }
            if role == "derived":
                entry["source"] = {"kind": "derived", "expr": bd.get("expr")}
            else:
                d, c = idx[bd["from"]]
                entry["unit"] = c.get("unit", "")
                entry["source"] = {
                    "kind": "modbus",
                    "device_id": d["device_id"], "bus_id": d["bus_id"],
                    "slave": d.get("slave"), "register": c.get("register"),
                    "function": c.get("function", 3),
                    "data_type": c["data_type"], "scale": c.get("scale", 1),
                }
            if role in WRITABLE_ROLES:
                entry["safety"] = {"lo": bd.get("limit_lo"), "hi": bd.get("limit_hi"),
                                   "rate_per_s": bd.get("rate_limit_per_s")}
            points[pid] = entry
    return {"config_version": draft["config_version"], "points": points}


def build_poll_plan(draft: dict) -> dict:
    """同总线串行、连续寄存器合并(PRD §24)。每设备按功能码合并成读任务。"""
    # point_id 反查(register->point)用于把读到的寄存器映射回点位
    reg_points: dict[str, list] = {}
    for biz in draft["business_devices"]:
        for role, bd in (biz.get("bindings") or {}).items():
            if role == "derived":
                continue
            d_id = bd["from"].split(".")[0]
            reg_points.setdefault(d_id, []).append((bd["point_id"], bd["from"]))

    idx = _channels_index(draft)
    buses = {b["bus_id"]: {"bus_id": b["bus_id"], "type": b["type"], "tasks": []}
             for b in draft["buses"]}
    for d in draft["hardware_devices"]:
        chans = [c for c in d.get("channels", []) or [] if c.get("register") is not None]
        if not chans:
            continue
        # 按功能码分组合并
        by_fn: dict[int, list] = {}
        for c in chans:
            by_fn.setdefault(c.get("function", 3), []).append(c)
        for fn, cs in by_fn.items():
            regs = [(c["register"], DATA_WIDTH[c["data_type"]]) for c in cs]
            start = min(r for r, _ in regs)
            end = max(r + w for r, w in regs)
            pts = []
            for pid, frm in reg_points.get(d["device_id"], []):
                _, c = idx[frm]
                if c.get("function", 3) == fn and c.get("register") is not None:
                    pts.append({"point_id": pid, "register": c["register"],
                                "data_type": c["data_type"], "scale": c.get("scale", 1)})
            buses[d["bus_id"]]["tasks"].append({
                "task_id": f"read_{d['device_id']}_fn{fn}",
                "device_id": d["device_id"],
                "hardware_template": d["hardware_template"], "slave": d.get("slave"),
                "function": fn, "start": start, "count": end - start,
                "period_ms": 2000, "timeout_ms": d.get("timeout_ms", 250),
                "retries": d.get("retries", 1),
                "backoff_after_failures": 3, "backoff_period_ms": 30000,
                "points": pts,
            })
    return {"config_version": draft["config_version"],
            "buses": [b for b in buses.values() if b["tasks"]]}


def build_display_model(draft: dict) -> dict:
    pages: dict[str, dict] = {}
    for biz in draft["business_devices"]:
        disp = biz.get("display")
        if not disp:
            continue
        page = pages.setdefault(disp["page"], {"page": disp["page"], "cards": {}})
        card_name = disp.get("card", biz["business_id"])
        card = page["cards"].setdefault(card_name, {"card": card_name,
                                                    "label": disp.get("label", card_name),
                                                    "priority": disp.get("priority", 50),
                                                    "fields": []})
        for role, bd in (biz.get("bindings") or {}).items():
            card["fields"].append({"point_id": bd["point_id"],
                                   "label": bd.get("label") or bd["point_id"], "role": role})
    out = []
    for p in pages.values():
        cards = sorted(p["cards"].values(), key=lambda c: c["priority"])
        out.append({"page": p["page"], "cards": cards})
    return {"config_version": draft["config_version"], "pages": out}


def build_safety_policy(draft: dict) -> dict:
    cmds = {}
    for biz in draft["business_devices"]:
        for role, bd in (biz.get("bindings") or {}).items():
            if role in WRITABLE_ROLES:
                cmds[bd["point_id"]] = {
                    "lo": bd.get("limit_lo"), "hi": bd.get("limit_hi"),
                    "rate_per_s": bd.get("rate_limit_per_s"),
                    "business_id": biz["business_id"],
                    "feedback": (biz.get("bindings", {}).get("feedback") or {}).get("point_id"),
                }
    return {"config_version": draft["config_version"], "commands": cmds}


def compile(draft: dict) -> dict:
    return {
        "point_registry.json": build_point_registry(draft),
        "poll_plan.json": build_poll_plan(draft),
        "display_model.json": build_display_model(draft),
        "safety_policy.json": build_safety_policy(draft),
    }


# ===========================================================================
# CLI
# ===========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="config_draft.json 编译器")
    ap.add_argument("draft", help="配置草稿 json 路径")
    ap.add_argument("--out", default=os.path.join(HERE, "build"), help="产物输出目录")
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()

    try:
        draft = json.load(open(args.draft, encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"[错误] 读取草稿失败: {e}", file=sys.stderr)
        return 2

    errs = validate(draft)
    if errs:
        print(f"[校验失败] {len(errs)} 项:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("[校验通过]")
    if args.validate_only:
        return 0

    products = compile(draft)
    os.makedirs(args.out, exist_ok=True)
    for name, obj in products.items():
        path = os.path.join(args.out, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        print(f"[产物] {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

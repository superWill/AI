#!/usr/bin/env python3
"""适配层 —— 编译产物 → app.py 内核可消费的运行配置(纯标准库,零依赖)。

编译器(compiler.py)只产中性产物。本模块把产物映射回 app.py 的 main() 已经
接受的扁平 cfg 形状(devices[] + control_map + safety_policy),从而:
  - app.py / SimSource / ModbusSource / Runtime 一行不改即可加载编译产物。
  - 生成配置内联 safety_policy;Controller 据此进入严格模式,不再回退 SAFE_RANGES。

边界(诚实):
  - app.py 的 SAFE_RANGES 仅在"无 safety_policy 的旧 app_config"下作为回退;
    本适配生成的配置带 safety_policy,故走严格模式(policy 外点位一律拒绝)。
  - 草稿不含 sim 仿真字段(base/swing),用 sim 源跑编译配置时非控制点为静态值;
    sim 字段属原型自测产物,不进生产契约。

用法:
  python3 loader.py build --emit-app-config build/app_config.generated.json
  # 然后:python3 app.py --config build/app_config.generated.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_CN = {
    "rs485_8ai_modbus": "采集模块", "rs485_8di_modbus": "安全IO",
    "rs485_8do_modbus": "输出模块", "rs485_ao_modbus": "输出模块",
    "modbus_tcp_generic": "采集模块", "heat_meter_modbus": "热表",
    "energy_meter_modbus": "电表", "vfd_modbus": "循环泵", "private_mcu": "私有控制器",
}


def load_runtime_cfg(build_dir: str, device_id: str = "rk3506-gw-01",
                     source: str = "sim") -> dict:
    poll = json.load(open(os.path.join(build_dir, "poll_plan.json"), encoding="utf-8"))
    reg = json.load(open(os.path.join(build_dir, "point_registry.json"), encoding="utf-8"))
    safety = json.load(open(os.path.join(build_dir, "safety_policy.json"), encoding="utf-8"))
    points = reg["points"]

    # poll_plan 的每个 task 即一个被采集设备 → 还原 app.py 的 devices[] 条目。
    # 设备类型按 hardware_template(物理设备能力)映射,不能用 business_template,
    # 否则 VFD/安全IO 会被错判成"采集模块"。
    devices = []
    for bus in poll["buses"]:
        for t in bus["tasks"]:
            did = t["device_id"]
            dev_points = []
            for pt in t["points"]:
                pinfo = points.get(pt["point_id"], {})
                dev_points.append({"id": pt["point_id"], "reg": pt["register"],
                                   "scale": pt.get("scale", 1),
                                   "unit": pinfo.get("unit", "")})
            dev = {
                "addr": t["slave"], "name": did,
                "type": TEMPLATE_CN.get(t.get("hardware_template", ""), "采集模块"),
                "start": t["start"], "count": t["count"], "fault": "none",
                "points": dev_points,
            }
            # 桥接:把编译出的每设备可靠性参数透传给 app.py(否则静默退回全局默认)
            for k in ("timeout_ms", "retries"):
                if t.get(k) is not None:
                    dev[k] = t[k]
            devices.append(dev)

    # safety_policy.commands → control_map(写设定值用:setpoint_id → addr/reg/scale)
    control_map = {}
    for pid in safety.get("commands", {}):
        src = points.get(pid, {}).get("source", {})
        if src.get("slave") is not None and src.get("register") is not None:
            control_map[pid] = {"addr": src["slave"], "reg": src["register"],
                                "scale": src.get("scale", 1)}

    return {
        "device_id": device_id, "source": source,
        "poll_interval_s": 2, "telemetry_interval_s": 10, "heartbeat_interval_s": 30,
        "html_dir": "html",
        "devices": devices, "control_map": control_map,
        "safety_policy": safety.get("commands", {}),   # Controller 据此取代 SAFE_RANGES
        "_generated_from": "compiler products", "config_version": poll["config_version"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="编译产物 → app.py 运行配置 适配层")
    ap.add_argument("build_dir", help="编译产物目录(含 poll_plan.json 等)")
    ap.add_argument("--device-id", default="rk3506-gw-01")
    ap.add_argument("--source", choices=["sim", "modbus"], default="sim")
    ap.add_argument("--emit-app-config", help="写出 app.py 可直接 --config 的 json")
    args = ap.parse_args()

    cfg = load_runtime_cfg(args.build_dir, args.device_id, args.source)
    if args.emit_app_config:
        with open(args.emit_app_config, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        print(f"[运行配置] {args.emit_app_config}  "
              f"({len(cfg['devices'])} 设备, {len(cfg['control_map'])} 可控点)")
    else:
        json.dump(cfg, sys.stdout, ensure_ascii=False, indent=2)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

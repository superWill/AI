#!/usr/bin/env python3
"""金帧基准生成器:把 dashboard.render 的输出固化成 hmi-go 的像素级对标数据。

每个用例产出三个文件到 tests/golden/:
  <case>.input.json    渲染的全部输入(view/clock/targets/page/表单态/display_model)
  <case>.rgb.gz        fb.buf 原始 RGB888(800*480*3),gzip(mtime=0 保证可复现)
  <case>.buttons.json  按钮列表(sort_keys,rect 元组序列化为数组)

用法:
  python3 tools/gen_golden_frames.py                # 全量生成
  python3 tools/gen_golden_frames.py control        # 单用例
  python3 tools/gen_golden_frames.py --png /tmp/x   # 额外输出 PNG 预览到目录

Go 侧 golden_test.go 读 input.json 走真实解码路径渲染,与 rgb.gz 解压后
逐字节比对(不比 PNG:zlib 实现差异导致字节不同)。
"""
import gzip
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

import dashboard  # noqa: E402


def _display_model():
    """监控页卡片 fixture:覆盖 >6 字段截断、缺 label 回退 card id、
    缺 field label 回退 point_id、未知点位、priority 排序、高度溢出跳卡。"""
    return {"pages": [
        {"page": "p1", "cards": [
            {"card": "hx_run", "label": "机组运行", "priority": 20, "fields": [
                {"point_id": "pri_supply_temp", "label": "一次供温"},
                {"point_id": "sec_supply_temp", "label": "二次供温"},
                {"point_id": "sec_supply_pressure", "label": "供水压力"},
                {"label": "无点位字段被过滤"},
                {"point_id": "sec_return_pressure", "label": "回水压力"},
                {"point_id": "valve_open", "label": "阀位"},
                {"point_id": "estop", "label": "急停"},
                {"point_id": "water_low", "label": "低水位"},
                {"point_id": "pump_run", "label": "泵运行"},
            ]},
            {"card": "pump_status", "fields": [
                {"point_id": "pump_run", "label": "运行状态"},
                {"point_id": "pump_freq", "label": "频率"},
                {"point_id": "pump_current", "label": "电流"},
                {"point_id": "ghost_point", "label": "未知点位"},
                {"point_id": "voltage", "label": "电压"},
                {"point_id": "current", "label": "电流A"},
            ]},
        ]},
        {"page": "p2", "cards": [
            {"card": "heat_meter", "label": "热量计量", "priority": 50, "fields": [
                {"point_id": "supply_temp", "label": "供温"},
                {"point_id": "flow", "label": "流量"},
                {"point_id": "heat_power", "label": "热功率"},
                {"point_id": "sec_supply_temp", "label": "二次供温"},
                {"point_id": "pump_freq", "label": "泵频率"},
                {"point_id": "valve_open", "label": "阀开度"},
            ]},
            {"card": "power", "label": "电力监测", "priority": 5, "fields": [
                {"point_id": "voltage", "label": "电压"},
                {"point_id": "current", "label": "电流"},
                {"point_id": "pump_current", "label": "泵电流"},
                {"point_id": "estop"},
                {"point_id": "flow", "label": "流量"},
                {"point_id": "heat_power", "label": "功率"},
            ]},
            {"card": "overflow", "label": "溢出卡", "priority": 90, "fields": [
                {"point_id": "estop", "label": "字段1"},
                {"point_id": "flow", "label": "字段2"},
                {"point_id": "voltage", "label": "字段3"},
            ]},
        ]},
    ]}


def cases():
    sv = dashboard._sample_view()
    empty = {"devices": [], "events": [{"detail": "正在连接后端…"}]}
    targets = {"valve_open": 70, "pump_freq": 40}
    out = []

    def case(name, view, page, targets=None, dm=None):
        out.append({"name": name, "inputs": {
            "view": view, "clock": "14:32:07", "targets": targets or {},
            "page": page, "display_model": dm}})

    case("overview", sv, "overview", targets)
    case("overview_empty", empty, "overview")
    case("monitor_flat", sv, "monitor", targets)
    case("monitor_cards", sv, "monitor", targets, dm=_display_model())
    case("nodes", sv, "nodes", targets)
    case("nodes_empty", empty, "nodes")
    case("control", sv, "control", targets)
    case("control_empty", empty, "control")
    case("settings", sv, "settings", targets)
    dark = dict(sv)
    dark["local_settings"] = {"brightness": 60, "theme": "dark"}
    case("settings_dark", dark, "settings", targets)
    return out


def render_case(c):
    i = c["inputs"]
    dashboard.configure_display(i["display_model"])
    dashboard.apply_theme((i["view"].get("local_settings") or {}).get("theme", "light"))
    try:
        fb, buttons = dashboard.render(
            i["view"], clock=i["clock"], targets=i["targets"], page=i["page"])
    finally:
        dashboard.configure_display(None)  # 复位模块级 DISPLAY_CARDS
        dashboard.apply_theme("light")
    return fb, buttons


def main():
    args = sys.argv[1:]
    png_dir = None
    if "--png" in args:
        k = args.index("--png")
        png_dir = Path(args[k + 1])
        png_dir.mkdir(parents=True, exist_ok=True)
        del args[k:k + 2]
    only = set(args)

    golden = APP / "tests" / "golden"
    golden.mkdir(parents=True, exist_ok=True)
    for c in cases():
        name = c["name"]
        if only and name not in only:
            continue
        fb, buttons = render_case(c)
        fb2, buttons2 = render_case(c)  # 自证确定性
        assert bytes(fb.buf) == bytes(fb2.buf), "%s: 帧不确定!" % name
        bj = json.dumps(buttons, ensure_ascii=False, sort_keys=True, indent=1)
        assert bj == json.dumps(buttons2, ensure_ascii=False, sort_keys=True,
                                indent=1), "%s: 按钮不确定!" % name
        (golden / (name + ".input.json")).write_text(
            json.dumps(c["inputs"], ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        (golden / (name + ".rgb.gz")).write_bytes(
            gzip.compress(bytes(fb.buf), 9, mtime=0))
        (golden / (name + ".buttons.json")).write_text(bj + "\n", encoding="utf-8")
        if png_dir:
            fb.to_png(str(png_dir / (name + ".png")))
        print("golden %-16s buttons=%-3d" % (name, len(buttons)))


if __name__ == "__main__":
    main()

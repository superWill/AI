#!/usr/bin/env python3
"""编译器 + 适配层回归自测(纯标准库,python3 tests/test_compiler.py 即可跑)。

覆盖:
  1. 合法草稿校验通过、四个产物结构正确。
  2. x-compiler-constraints 五类错误能被 validate 抓到。
  3. draft→compile→loader→未改的 app.py SimSource 端到端点位贯通。
"""
import copy
import json
import os
import sys
from unittest import SkipTest   # 无网络/绑定权限的沙箱里让 HTTP 测试优雅跳过,不算失败

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import compiler          # noqa: E402
from loader import load_runtime_cfg   # noqa: E402

DRAFT = json.load(open(os.path.join(ROOT, "samples", "heating_draft.json"), encoding="utf-8"))


def test_valid_draft_compiles():
    assert compiler.validate(DRAFT) == []
    prod = compiler.compile(DRAFT)
    assert set(prod) == {"point_registry.json", "poll_plan.json",
                         "display_model.json", "safety_policy.json"}
    # 连续寄存器合并:AI1..AI6(reg0..5) → start0 count6
    ai = next(t for b in prod["poll_plan.json"]["buses"]
              for t in b["tasks"] if t["device_id"] == "hx_ai_1")
    assert ai["start"] == 0 and ai["count"] == 6
    # 同总线串行:只有一条 rs485_1 总线承载所有任务
    assert len(prod["poll_plan.json"]["buses"]) == 1
    # safety_policy 抽出可控点限值
    assert prod["safety_policy.json"]["commands"]["pump_freq_sp"]["hi"] == 50


def test_constraints_caught():
    cases = {
        "dup_slave": lambda d: d["hardware_devices"][1].__setitem__("slave", 1),
        "bad_from": lambda d: d["business_devices"][0]["bindings"]["measurement"]
                              .__setitem__("from", "hx_ai_1.AI9"),
        "missing_limit": lambda d: d["business_devices"][2]["bindings"]["setpoint"]
                                   .pop("limit_hi"),
        "missing_range": lambda d: d["hardware_devices"][0]["channels"][0].pop("eng_range"),
        "dup_point_id": lambda d: d["business_devices"][1]["bindings"]["measurement"]
                                  .__setitem__("point_id", "sec_supply_temp"),
    }
    for name, mutate in cases.items():
        d = copy.deepcopy(DRAFT)
        mutate(d)
        assert compiler.validate(d), f"{name} 应当报错却通过了"


def test_end_to_end_with_kernel():
    """编译产物经 loader 适配,驱动未修改的 app.py SimSource。"""
    from app import SimSource
    prod = compiler.compile(DRAFT)
    build = os.path.join(HERE, "_build_tmp")
    os.makedirs(build, exist_ok=True)
    for n, o in prod.items():
        json.dump(o, open(os.path.join(build, n), "w", encoding="utf-8"))
    cfg = load_runtime_cfg(build)
    snap = SimSource(cfg["devices"]).poll()
    got = {pid for dd in snap.values() for pid in dd["points"]}
    want = {"sec_supply_temp", "sec_supply_pressure", "pump_run",
            "pump_freq_sp", "estop", "water_low"}
    assert want <= got, f"丢点位: {want - got}"
    assert cfg["control_map"]["pump_freq_sp"] == {"addr": 2, "reg": 1, "scale": 0.1}


def test_safety_policy_rejects_out_of_range():
    """Controller 用编译出的 safety_policy(非硬编码 SAFE_RANGES)拒绝越界命令。"""
    from app import Controller, Runtime, SimSource
    prod = compiler.compile(DRAFT)
    policy = prod["safety_policy.json"]["commands"]      # pump_freq_sp: lo0 hi50
    rt = Runtime({"device_id": "t"})
    src = SimSource([])          # SimSource.setpoints 内置 pump_freq_sp,与 devices 无关
    ctl = Controller(rt, src, {}, safety_policy=policy)
    ok, reason = ctl.apply("pump_freq_sp", 999, origin="test")   # 越界
    assert not ok and "超出安全限值" in reason, reason
    ok, _ = ctl.apply("pump_freq_sp", 30, origin="test")          # 区间内
    assert ok
    # 未在 policy 也未在 SAFE_RANGES 的点位被拒
    ok, reason = ctl.apply("nonexistent_sp", 1, origin="test")
    assert not ok
    # 关键安全语义:valve_open_sp 在旧 SAFE_RANGES 内,但不在 policy → 严格模式必须拒绝
    assert "valve_open_sp" in __import__("app").SAFE_RANGES
    ok, reason = ctl.apply("valve_open_sp", 50, origin="test")
    assert not ok, "policy 模式下不得回退 SAFE_RANGES 放行 policy 外点位"


def test_configure_maps_empty_clears_old_controllable():
    """--products 驱动模式:产物无可写点时也要清空旧硬编码可控点。"""
    import nexus_server as nx
    saved = dict(nx.CONTROLLABLE)
    try:
        nx.configure_maps({"points": {"sec_supply_temp": {"role": "measurement"}}})
        assert nx.CONTROLLABLE == {}, nx.CONTROLLABLE
    finally:
        nx.CONTROLLABLE.clear(); nx.CONTROLLABLE.update(saved)


def test_devtype_derived_for_vfd_and_safety_io():
    """nexus 从 point_registry 派生设备类型,VFD→pump_vfd、安全IO→io_module。"""
    import nexus_server as nx
    prod = compiler.compile(DRAFT)
    saved_ctrl = dict(nx.CONTROLLABLE)
    saved_dev = dict(nx.DEVTYPE_BY_DEVICE)
    try:
        nx.configure_maps(prod["point_registry.json"])
        assert nx.DEVTYPE_BY_DEVICE["pump_vfd_2"] == "pump_vfd"
        assert nx.DEVTYPE_BY_DEVICE["safety_io_5"] == "io_module"
        # 可写点自映射(取代 feedback→setpoint 硬编码)
        assert nx.CONTROLLABLE.get("pump_freq_sp") == "pump_freq_sp"
    finally:
        nx.CONTROLLABLE.clear(); nx.CONTROLLABLE.update(saved_ctrl)
        nx.DEVTYPE_BY_DEVICE.clear(); nx.DEVTYPE_BY_DEVICE.update(saved_dev)


def test_loader_device_types_correct():
    """loader 用 hardware_template(非 business_template)映射,VFD/安全IO 不再误判。"""
    prod = compiler.compile(DRAFT)
    build = os.path.join(HERE, "_build_tmp2")
    os.makedirs(build, exist_ok=True)
    for n, o in prod.items():
        json.dump(o, open(os.path.join(build, n), "w", encoding="utf-8"))
    cfg = load_runtime_cfg(build)
    types = {d["name"]: d["type"] for d in cfg["devices"]}
    assert types["pump_vfd_2"] == "循环泵", types
    assert types["safety_io_5"] == "安全IO", types


def test_display_model_drives_nexus_tags():
    """nexus 从 point_registry+display_model 派生:Tag.type 按 data_type、附 group、按展示优先级排序。"""
    import nexus_server as nx
    from app import SimSource
    prod = compiler.compile(DRAFT)
    build = os.path.join(HERE, "_build_tmp3")
    os.makedirs(build, exist_ok=True)
    for n, o in prod.items():
        json.dump(o, open(os.path.join(build, n), "w", encoding="utf-8"))
    saved = (dict(nx.CONTROLLABLE), dict(nx.DEVTYPE_BY_DEVICE), dict(nx.POINT_TAGTYPE),
             dict(nx.DISPLAY_RANK), dict(nx.DISPLAY_GROUP), dict(nx.POINT_LABEL))
    try:
        nx.configure_maps(prod["point_registry.json"], prod["display_model.json"])
        cfg = load_runtime_cfg(build)
        snap = SimSource(cfg["devices"]).poll()
        view = {"devices": list(snap.values())}
        nodes, tags = nx.build_nodes_tags(view, "sim")
        by = {t["address"]: t for t in tags}      # address=point_id;name 现在是 label
        # Tag.type 按 data_type 派生(不再全 FLOAT32)
        assert by["estop"]["type"] == "BOOLEAN", by["estop"]
        assert by["sec_supply_temp"]["type"] == "UINT16"
        # Tag.name 用人类可读 label
        assert by["sec_supply_temp"]["name"] == "二次供水温度", by["sec_supply_temp"]
        # display_model 分组标签
        assert by["sec_supply_temp"]["group"] == "secondary_loop/secondary_temp"
        # 同一 node 内按展示优先级排序:secondary_temp(pri10) 在 secondary_pressure(pri20) 前
        n1 = [t["address"] for t in tags if t["nodeId"] == "node-1"]
        assert n1.index("sec_supply_temp") < n1.index("sec_supply_pressure"), n1
    finally:
        (nx.CONTROLLABLE, nx.DEVTYPE_BY_DEVICE, nx.POINT_TAGTYPE,
         nx.DISPLAY_RANK, nx.DISPLAY_GROUP, nx.POINT_LABEL) = saved


def test_display_model_drives_hmi_cards():
    """本地 HMI:configure_display 从 display_model 派生卡片(按 页序,priority 排序);监控页可渲染。"""
    import dashboard as db
    prod = compiler.compile(DRAFT)
    saved = list(db.DISPLAY_CARDS)
    try:
        db.configure_display(prod["display_model.json"])
        titles = [c["title"] for c in db.DISPLAY_CARDS]
        # 卡片标题用人类可读 label;secondary_temp(pri10) 在 secondary_pressure(pri20) 前
        assert titles[0] == "二次供温", titles
        assert titles[1] == "二次供压", titles
        assert "安全IO" in titles
        # 卡片字段保真:(point_id, label)
        c0 = db.DISPLAY_CARDS[0]
        assert c0["fields"] == [("sec_supply_temp", "二次供水温度")], c0
        # 监控页用分组渲染不崩(空 targets/view)
        fb, _ = db.render(db._sample_view(), page="monitor")
        assert fb is not None
        # 无 display_model 时回退平铺
        db.configure_display(None)
        assert db.DISPLAY_CARDS == []
        fb2, _ = db.render(db._sample_view(), page="monitor")
        assert fb2 is not None
    finally:
        db.DISPLAY_CARDS[:] = saved


def test_config_publish_backend():
    """配置发布后端:validate/compile 落产物、status 计数正确、非法草稿不落产物、不热切。"""
    import shutil
    import nexus_server as nx
    saved = (nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH)
    tmp = os.path.join(HERE, "_cfgtmp")
    nx.CONFIG_BUILD_DIR = os.path.join(tmp, "build")
    nx.CONFIG_DRAFT_PATH = os.path.join(tmp, "current_draft.json")
    try:
        ok, errs, status = nx.compile_draft(DRAFT)
        assert ok and errs == [], errs
        # 编译产物写到 versions/1/;摘要在 latest_compiled(active 尚未设置)
        lc = status["latest_compiled"]
        assert lc["devices"] == 3 and lc["points"] == 6, status
        assert status["active_version"] is None, status      # compile 不设 active
        assert status["errors"] == 0 and status["has_draft"], status
        assert os.path.exists(os.path.join(nx.version_dir(1), "poll_plan.json"))
        assert os.path.exists(os.path.join(nx.version_dir(1), "app_config.generated.json"))
        assert nx.latest_compiled_summary()["safety_commands"] == 1
        # 非法草稿:返回错误、status=None、不写新版本目录
        bad = copy.deepcopy(DRAFT)
        bad["hardware_devices"][1]["slave"] = 1          # 同总线 slave 重复
        ok2, errs2, status2 = nx.compile_draft(bad)
        assert not ok2 and errs2 and status2 is None
        assert not os.path.isdir(nx.version_dir(2))      # 校验失败不产生 version 2
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def _add_payload():
    return json.load(open(os.path.join(ROOT, "samples", "add_rs485_ai_payload.json"), encoding="utf-8"))


def test_add_device_to_draft_success():
    """添加一台 RS485 8AI:硬件 +1、业务设备增加、validate 通过、原 draft 不被原地改。"""
    import nexus_server as nx
    base = copy.deepcopy(DRAFT)
    hw0, bz0 = len(base["hardware_devices"]), len(base["business_devices"])
    ok, errs, nd = nx.add_device_to_draft(base, _add_payload())
    assert ok and errs == [], errs
    assert len(nd["hardware_devices"]) == hw0 + 1
    assert len(nd["business_devices"]) > bz0
    assert compiler.validate(nd) == []
    # 原 draft 未被原地修改
    assert len(base["hardware_devices"]) == hw0 and len(base["business_devices"]) == bz0


def test_add_device_to_draft_rejects_duplicate_slave_without_mutating():
    """payload 用已存在 slave → ok=false、报从站地址重复、原 draft 不变、不返回污染草稿。"""
    import nexus_server as nx
    base = copy.deepcopy(DRAFT)
    hw0 = len(base["hardware_devices"])
    payload = _add_payload()
    payload["hardware"]["slave"] = 1                  # 与 hx_ai_1 冲突
    payload["hardware"]["device_id"] = "ai_dup"
    ok, errs, nd = nx.add_device_to_draft(base, payload)
    assert not ok and nd is None
    assert any("从站地址重复" in e for e in errs), errs
    assert len(base["hardware_devices"]) == hw0       # 原 draft 未变


def test_config_devices_endpoint_persists_draft_only():
    """添加设备只更新 current_draft.json,不生成/不改 build 产物;compile 须另行触发。"""
    import shutil
    import nexus_server as nx
    saved = (nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH)
    tmp = os.path.join(HERE, "_devtmp")
    nx.CONFIG_BUILD_DIR = os.path.join(tmp, "build")
    nx.CONFIG_DRAFT_PATH = os.path.join(tmp, "current_draft.json")
    os.makedirs(tmp, exist_ok=True)
    try:
        # 写入合法 current_draft,但不 compile → build 不存在
        json.dump(DRAFT, open(nx.CONFIG_DRAFT_PATH, "w", encoding="utf-8"), ensure_ascii=False)
        base = nx._read_json(nx.CONFIG_DRAFT_PATH)
        ok, errs, nd = nx.add_device_to_draft(base, _add_payload())
        assert ok, errs
        json.dump(nd, open(nx.CONFIG_DRAFT_PATH, "w", encoding="utf-8"), ensure_ascii=False)  # 端点的落盘动作
        # 草稿已更新(+1 硬件设备)
        after = nx._read_json(nx.CONFIG_DRAFT_PATH)
        assert len(after["hardware_devices"]) == len(DRAFT["hardware_devices"]) + 1
        # build 未因添加设备生成(compile 须另行触发)
        assert not os.path.exists(os.path.join(nx.CONFIG_BUILD_DIR, "poll_plan.json"))
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def _cfg_tmp(nx, name):
    """临时 CONFIG_BUILD_DIR/CONFIG_DRAFT_PATH,返回 (saved, tmp)。"""
    saved = (nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH)
    tmp = os.path.join(HERE, name)
    nx.CONFIG_BUILD_DIR = os.path.join(tmp, "build")
    nx.CONFIG_DRAFT_PATH = os.path.join(tmp, "current_draft.json")
    os.makedirs(tmp, exist_ok=True)
    return saved, tmp


def test_build_versions_increment():
    """多次 compile 生成递增版本目录 versions/1、versions/2。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_vtmp")
    try:
        assert nx.list_versions() == []
        nx.compile_draft(DRAFT)
        nx.compile_draft(DRAFT)
        assert nx.list_versions() == [1, 2]
        assert nx.latest_version() == 2
        assert os.path.isdir(nx.version_dir(1)) and os.path.isdir(nx.version_dir(2))
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_active_not_changed_by_compile():
    """普通 compile 不改 active:无 active 时仍 None;有 active 时保持不变。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_atmp")
    try:
        assert nx.read_active() is None
        nx.compile_draft(DRAFT)
        assert nx.read_active() is None              # compile 不自动设 active
        nx.write_active(1)
        nx.compile_draft(DRAFT)                       # 再 compile 出 version 2
        assert nx.read_active() == 1                  # active 不被普通 compile 改动
        assert nx.latest_version() == 2               # 但 latest 前进
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_active_pointer_atomic_readback():
    """active 指针原子写(active.tmp + os.replace)可读回,且不残留 .tmp。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_ptmp")
    try:
        os.makedirs(nx.CONFIG_BUILD_DIR, exist_ok=True)
        nx.write_active(7)
        assert nx.read_active() == 7
        nx.write_active(42)                           # 覆盖式原子替换
        assert nx.read_active() == 42
        assert not os.path.exists(nx._active_file() + ".tmp")   # 临时文件不残留
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_loadable_check_passes_on_compiled_version():
    """干跑校验通过:产物可读、source 可构造、快照骨架含全部非派生点;不碰 runtime。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_lctmp")
    try:
        nx.compile_draft(DRAFT)                       # → versions/1
        ok, errs, report = nx.loadable_check(1)
        assert ok and errs == [], errs
        assert report["devices"] == 3 and report["missing"] == [], report
        assert report["snapshot_points"] >= report["expected_points"]
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_loadable_check_missing_version():
    """不存在的版本 → ok=false,报错,不抛异常。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_lmtmp")
    try:
        ok, errs, report = nx.loadable_check(999)
        assert not ok and errs and report is None
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_loadable_check_rejects_broken_products():
    """产物被破坏(删 poll_plan)→ loader 读不了 → ok=false;不污染、不碰 runtime。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_lbtmp")
    try:
        nx.compile_draft(DRAFT)                       # → versions/1
        os.remove(os.path.join(nx.version_dir(1), "poll_plan.json"))
        ok, errs, report = nx.loadable_check(1)
        assert not ok and errs, errs
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def _make_ctx(nx):
    """构造一个测试 RuntimeContext:旧 SimSource + Controller。"""
    from app import Runtime, SimSource, Controller
    old_src = SimSource([])
    rt = Runtime({"device_id": "t"})
    ctl = Controller(rt, old_src, {"old_sp": {"addr": 1, "reg": 0}}, safety_policy={"old_sp": {"lo": 0, "hi": 1}})
    return nx.RuntimeContext(old_src, ctl, active_version=None), old_src


def test_activate_swaps_runtime_context():
    """activate 成功:ctx 的 source/controller 输入一次性换成新版本,active 指针更新。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_act1")
    try:
        nx.compile_draft(DRAFT)                       # → versions/1(含 pump_freq_sp 安全限值)
        ctx, old_src = _make_ctx(nx)
        ok, errs, state = nx.activate_compiled_version(ctx, 1)
        assert ok and state == "active", (errs, state)
        assert ctx.active_version == 1 and nx.read_active() == 1
        assert ctx.source is not old_src                      # source 已换
        assert ctx.controller.source is ctx.source            # controller 同步换
        assert "pump_freq_sp" in ctx.controller.safety_policy  # 安全策略换成新版本
        assert "old_sp" not in ctx.controller.control_map      # 旧 control_map 被替换
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_activate_failed_on_unloadable_leaves_ctx_untouched():
    """目标版本不可加载 → state=failed,ctx 完全不动,active 不写。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_act2")
    try:
        ctx, old_src = _make_ctx(nx)
        ok, errs, state = nx.activate_compiled_version(ctx, 999)   # 不存在的版本
        assert not ok and state == "failed" and errs
        assert ctx.source is old_src and ctx.active_version is None
        assert nx.read_active() is None                # active 指针未被写
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_activate_failed_on_health_check_never_touches_ctx():
    """§8.2 方案B:健康检查在锁外、切换前。新 source 不健康 → state=failed,
    ctx 从未被替换(无需回滚),active 不前进。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_act3")
    try:
        nx.compile_draft(DRAFT)                       # → versions/1
        ctx, old_src = _make_ctx(nx)

        class BadSource:                              # 注入:新 source poll 即抛 → 切前健康检查失败
            def poll(self):
                raise RuntimeError("device unreachable")
        ok, errs, state = nx.activate_compiled_version(ctx, 1, source_factory=lambda devs: BadSource())
        assert not ok and state == "failed", (errs, state)
        assert ctx.source is old_src                  # 从未替换(健康检查在锁外、切前)
        assert ctx.controller.source is old_src
        assert ctx.active_version is None
        assert nx.read_active() is None               # active 指针未前进
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_activate_singleflight_blocks_concurrent():
    """§8.3 单飞:已有 activate 在途时,try_activate 返回 None(端点据此回 409)。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_actsf")
    try:
        nx.compile_draft(DRAFT)
        ctx, _ = _make_ctx(nx)
        assert nx._ACTIVATE_INFLIGHT.acquire(blocking=False)   # 模拟"另一个 activate 在途"
        try:
            assert nx.try_activate(ctx, 1) is None             # 单飞拒绝
        finally:
            nx._ACTIVATE_INFLIGHT.release()
        assert nx.try_activate(ctx, 1)[0] is True              # 释放后可激活
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_live_activate_collector_sees_new_source():
    """collector 取数模式(锁内取 ctx.source 引用,锁外 poll)在 activate 后看到新版本点位。"""
    import shutil
    import nexus_server as nx
    from app import Runtime, SimSource, Controller
    saved, tmp = _cfg_tmp(nx, "_actlive")
    try:
        rt = Runtime({"device_id": "t"})
        ctx = nx.RuntimeContext(SimSource([]), Controller(rt, SimSource([]), {}))
        rt.update(ctx.current_source().poll())                 # 初始空源 → 无点位
        assert not any(d.get("points") for d in rt.get().values())
        nx.compile_draft(DRAFT)                                # → versions/1
        ok, _, state = nx.activate_compiled_version(ctx, 1)
        assert ok and state == "active"
        rt.update(ctx.current_source().poll())                 # collector 下一轮从 ctx 取新源
        pts = {pid for d in rt.get().values() for pid in (d.get("points") or {})}
        assert "sec_supply_temp" in pts, pts                   # snapshot 变成新版本
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_select_startup_config_uses_active():
    """有 active=N 且 versions/N/app_config.generated.json 存在 → 启动选该文件。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_su1")
    try:
        nx.compile_draft(DRAFT)                       # → versions/1(含 app_config.generated.json)
        nx.write_active(1)
        chosen = nx.select_startup_config("/somewhere/app_config.json")
        assert chosen == os.path.join(nx.version_dir(1), "app_config.generated.json"), chosen
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_select_startup_config_fallback_no_active():
    """无 active → 回退到 --config 路径。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_su2")
    try:
        assert nx.read_active() is None
        chosen = nx.select_startup_config("/somewhere/app_config.json")
        assert chosen == "/somewhere/app_config.json", chosen
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_select_startup_config_fallback_when_gen_missing():
    """active 指向版本但其 app_config.generated.json 缺失 → 仍回退 --config,不报错。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_su3")
    try:
        nx.compile_draft(DRAFT)
        os.remove(os.path.join(nx.version_dir(1), "app_config.generated.json"))
        nx.write_active(1)
        chosen = nx.select_startup_config("/somewhere/app_config.json")
        assert chosen == "/somewhere/app_config.json", chosen
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_products_dir_uses_active():
    """active=N → --products 解析到 versions/N(展示与 live cfg 同源)。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_rp1")
    try:
        nx.compile_draft(DRAFT)                       # → versions/1
        nx.write_active(1)
        assert nx.resolve_products_dir(nx.CONFIG_BUILD_DIR) == nx.version_dir(1)
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_products_dir_fallback_no_active():
    """无 active → 原样返回 products_arg(扁平目录,调用方再判 point_registry)。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_rp2")
    try:
        assert nx.read_active() is None
        assert nx.resolve_products_dir(nx.CONFIG_BUILD_DIR) == nx.CONFIG_BUILD_DIR
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_resolve_products_dir_fallback_when_version_missing():
    """active 指向不存在的版本目录 → 回退 products_arg,不报错。"""
    import shutil
    import nexus_server as nx
    saved, tmp = _cfg_tmp(nx, "_rp3")
    try:
        os.makedirs(nx.CONFIG_BUILD_DIR, exist_ok=True)
        nx.write_active(99)                           # versions/99 不存在
        assert nx.resolve_products_dir(nx.CONFIG_BUILD_DIR) == nx.CONFIG_BUILD_DIR
    finally:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


def test_activate_http_endpoints():
    """HTTP activate/status/rollback:无鉴权 401;响应恒带 wired_to_runtime=False;
    activate v2 → rollback 回 v1。不假装切 live。"""
    import shutil
    import threading
    import urllib.request
    import urllib.error
    from http.server import ThreadingHTTPServer
    import nexus_server as nx
    from app import Runtime, SimSource, Controller
    saved = (nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH)
    tmp = os.path.join(HERE, "_acthttp")
    nx.CONFIG_BUILD_DIR = os.path.join(tmp, "build")
    nx.CONFIG_DRAFT_PATH = os.path.join(tmp, "current_draft.json")
    os.makedirs(tmp, exist_ok=True)
    nx._ACTIVATE_CTX = None                                   # 重置 sandbox ctx
    nx.LAST_ACTIVATE = {"version": None, "state": None, "errors": [], "previous_active": None}
    nx.compile_draft(DRAFT)                                   # versions/1
    nx.compile_draft(DRAFT)                                   # versions/2
    rt = Runtime({"device_id": "t"})
    live_ctx = nx.RuntimeContext(SimSource([]), Controller(rt, SimSource([]), {}))
    handler = nx.make_handler(rt, live_ctx, nx.SocketHub(), tmp, "sim", set())
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    except (PermissionError, OSError) as e:
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)
        raise SkipTest("无端口绑定权限: %s" % e)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = "http://127.0.0.1:%d" % port

    def post(p, body, auth=True):
        h = {"Content-Type": "application/json"}
        if auth:
            h["Authorization"] = "Bearer testtoken123"
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                base + p, data=json.dumps(body).encode(), headers=h), timeout=3)
            return r.status, json.load(r)
        except urllib.error.HTTPError as e:
            try:
                return e.code, json.load(e)      # 读回错误响应体(400 等)
            except ValueError:
                return e.code, None
    try:
        # 无鉴权 → 401
        code, _ = post("/api/config/activate", {"version": 1}, auth=False)
        assert code == 401, code
        # 单飞:已有 activate 在途 → 409
        assert nx._ACTIVATE_INFLIGHT.acquire(blocking=False)
        try:
            code, _ = post("/api/config/activate", {"version": 2})
            assert code == 409, code
        finally:
            nx._ACTIVATE_INFLIGHT.release()
        # 激活 v2:ok、state=active、active 指针=2(active 即 live 真实版本)
        code, r = post("/api/config/activate", {"version": 2})
        assert r["ok"] and r["state"] == "active", r
        assert "wired_to_runtime" not in r                # 该语义已退役
        assert live_ctx.active_version == 2 and nx.read_active() == 2
        # 回滚:回到上一激活版(prev=read_active() before v2 = None?) → 这里 prev 为激活 v2 前的 active
        # 激活 v2 前 active 为 None,故 previous_active=None → rollback 应拒绝
        code, r = post("/api/config/rollback", {})
        assert code == 400 and r["ok"] is False and "无可回滚" in r["errors"][0], (code, r)
        # 再激活 v1,使 previous_active=2;然后 rollback 回 2
        post("/api/config/activate", {"version": 1})
        assert nx.read_active() == 1
        code, r = post("/api/config/rollback", {})
        assert r["ok"] and nx.read_active() == 2, r
    finally:
        httpd.shutdown()
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        nx._ACTIVATE_CTX = None
        shutil.rmtree(tmp, ignore_errors=True)


def test_config_devices_http_auth_and_persist():
    """真起 HTTP handler:无 Bearer → 401;带 Bearer → 添加成功且只落草稿(build 不生成)。"""
    import shutil
    import threading
    import urllib.request
    import urllib.error
    from http.server import ThreadingHTTPServer
    import nexus_server as nx
    from app import Runtime, SimSource, Controller
    saved = (nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH)
    tmp = os.path.join(HERE, "_httptmp")
    nx.CONFIG_BUILD_DIR = os.path.join(tmp, "build")
    nx.CONFIG_DRAFT_PATH = os.path.join(tmp, "current_draft.json")
    os.makedirs(tmp, exist_ok=True)
    json.dump(DRAFT, open(nx.CONFIG_DRAFT_PATH, "w", encoding="utf-8"), ensure_ascii=False)
    rt = Runtime({"device_id": "t"})
    live_ctx = nx.RuntimeContext(SimSource([]), Controller(rt, SimSource([]), {}))
    handler = nx.make_handler(rt, live_ctx, nx.SocketHub(), tmp, "sim", set())
    try:
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    except (PermissionError, OSError) as e:   # 沙箱无端口绑定权限:跳过而非失败
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)
        raise SkipTest("无本机端口绑定权限,跳过 HTTP handler 测试: %s" % e)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/api/config/devices" % port
    payload = json.dumps(_add_payload()).encode()
    try:
        # 无鉴权 → 401
        code = 200
        try:
            urllib.request.urlopen(urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}), timeout=3)
        except urllib.error.HTTPError as e:
            code = e.code
        assert code == 401, code
        # 带鉴权 → ok=true
        resp = json.load(urllib.request.urlopen(urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json", "Authorization": "Bearer testtoken123"}),
            timeout=3))
        assert resp["ok"] is True, resp
        # 只落草稿:current_draft +1 硬件;build 未生成
        after = nx._read_json(nx.CONFIG_DRAFT_PATH)
        assert len(after["hardware_devices"]) == len(DRAFT["hardware_devices"]) + 1
        assert not os.path.exists(os.path.join(nx.CONFIG_BUILD_DIR, "poll_plan.json"))
    finally:
        httpd.shutdown()
        nx.CONFIG_BUILD_DIR, nx.CONFIG_DRAFT_PATH = saved
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    n = skipped = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except SkipTest as s:
                skipped += 1
                print(f"  skip {name}: {s}")
            else:
                n += 1
                print(f"  ok  {name}")
    print(f"\n{n} passed" + (f", {skipped} skipped" if skipped else ""))

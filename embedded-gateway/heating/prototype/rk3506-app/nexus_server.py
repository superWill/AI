#!/usr/bin/env python3
"""nexus-edge-os 前端 + Python 后端适配(纯标准库,零依赖)。

把真 edge-os 已构建的前端 dist 装到 RK3506,用 Python 实现它要的契约:
  - REST: /api/login /api/me /api/init /api/tags/write /api/nodes ... (见 services/api.ts)
  - 实时: 自实现的 socket.io(Engine.IO v4 + Socket.IO v5)轮询服务器,
          推 tag-change / node-change / system-metrics 三个事件。
数据来自 app.py 的统一点表快照(sim 或 modbus 源),控制走 app.py 的安全校验。

用法:
  python3 nexus_server.py --config app_config.json --dist nexus-dist --port 8092
"""
from __future__ import annotations

import argparse
import json
import os
import copy
import random
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from app import Runtime, SimSource, ModbusSource, Controller   # 复用已验证的内核
import compiler                                                 # 配置发布后端复用编译器
from loader import load_runtime_cfg                             # 产物 → 运行配置适配层

HERE = os.path.dirname(os.path.abspath(__file__))

# 配置发布后端(PRD §10 安全入口):草稿落盘 + 校验 + 编译,不热切运行时、不接 /api/nodes。
CONFIG_DRAFT_PATH = os.path.join(HERE, "current_draft.json")
CONFIG_BUILD_DIR = os.path.join(HERE, "build")
GATEWAYC_BIN = "gatewayc"   # D3:配置编译/校验调 gatewayc compile/load;二进制不可用时回退 Python compiler


def _read_json(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---- build 版本化(第1步):build/versions/N/ + 原子 active 指针 ----
# 路径都从 CONFIG_BUILD_DIR 动态取(测试会临时改 CONFIG_BUILD_DIR)。
def _versions_dir():
    return os.path.join(CONFIG_BUILD_DIR, "versions")


def _active_file():
    return os.path.join(CONFIG_BUILD_DIR, "active")


def version_dir(n):
    return os.path.join(_versions_dir(), str(n))


def list_versions():
    d = _versions_dir()
    if not os.path.isdir(d):
        return []
    return sorted(int(x) for x in os.listdir(d)
                  if x.isdigit() and os.path.isdir(os.path.join(d, x)))


def next_version():
    vs = list_versions()
    return (vs[-1] + 1) if vs else 1


def latest_version():
    vs = list_versions()
    return vs[-1] if vs else None


def read_active():
    """读 active 指针 → 版本号(int)或 None。"""
    try:
        with open(_active_file(), encoding="utf-8") as f:
            s = f.read().strip()
    except OSError:
        return None
    return int(s) if s.isdigit() else None


def write_active(n):
    """原子写 active 指针:先写 active.tmp,再 os.replace(),避免半写。"""
    os.makedirs(CONFIG_BUILD_DIR, exist_ok=True)
    tmp = _active_file() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(str(int(n)))
    os.replace(tmp, _active_file())                 # 原子替换


def version_summary(n):
    """某版本目录的产物摘要;读不到返回 None。"""
    if n is None:
        return None
    vd = version_dir(n)
    pr = _read_json(os.path.join(vd, "point_registry.json"))
    pp = _read_json(os.path.join(vd, "poll_plan.json")) or {}
    dm = _read_json(os.path.join(vd, "display_model.json")) or {}
    sp = _read_json(os.path.join(vd, "safety_policy.json")) or {}
    if pr is None:
        return None
    return {"version": n, "config_version": pr.get("config_version"),
            "devices": len({t["device_id"] for b in pp.get("buses", []) for t in b.get("tasks", [])}),
            "points": len(pr.get("points", {})),
            "display_cards": sum(len(p.get("cards", [])) for p in dm.get("pages", [])),
            "safety_commands": len(sp.get("commands", {}))}


def latest_compiled_summary():
    """最新编译版本摘要(与 active 无关)。"""
    return version_summary(latest_version())


def config_products_summary():
    """编译产物摘要,**默认读 active 指向版本**(无 active 则全 null)。"""
    n = read_active()
    vd = version_dir(n) if n is not None else None

    def rd(name):
        return _read_json(os.path.join(vd, name)) if vd else None
    pr, pp, dm, sp = rd("point_registry.json"), rd("poll_plan.json"), rd("display_model.json"), rd("safety_policy.json")
    return {
        "point_registry": None if pr is None else {
            "config_version": pr.get("config_version"), "points": len(pr.get("points", {}))},
        "poll_plan": None if pp is None else {
            "buses": len(pp.get("buses", [])),
            "tasks": sum(len(b.get("tasks", [])) for b in pp.get("buses", [])),
            "devices": len({t["device_id"] for b in pp.get("buses", []) for t in b.get("tasks", [])})},
        "display_model": None if dm is None else {
            "pages": len(dm.get("pages", [])),
            "cards": sum(len(p.get("cards", [])) for p in dm.get("pages", []))},
        "safety_policy": None if sp is None else {"commands": len(sp.get("commands", {}))},
    }


def config_status():
    """运行配置状态:主字段反映 **active 指向版本**;另带 latest 编译版本摘要。"""
    active = version_summary(read_active())
    draft = _read_json(CONFIG_DRAFT_PATH)
    errs = compiler.validate(draft) if draft is not None else None
    return {"active_version": read_active(),
            "config_version": (active or {}).get("config_version"),
            "devices": (active or {}).get("devices", 0),
            "points": (active or {}).get("points", 0),
            "errors": (len(errs) if errs is not None else None),
            "has_draft": draft is not None,
            "latest_version": latest_version(),
            "latest_compiled": latest_compiled_summary()}
    # 注:Step5.3 起 active 即 live 真实运行版本(activate 直接切 live ctx),不再有 wired_to_runtime。


# 自包含只读配置对账页(PRD §10 第1步)。不动 edge-os 预构建前端,nexus 直接吐这一页。
# 自己登录拿 token,读 /api/config/status|products|draft,提供校验框(只读,不 compile/activate)。
CONFIG_PAGE_HTML = """<!doctype html><html lang=zh><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>配置对账</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#e6edf6;
font:14px/1.5 -apple-system,system-ui,"PingFang SC",sans-serif;padding:24px}
h1{font-size:20px;margin:0 0 16px}h2{font-size:14px;color:#8aa0bd;margin:20px 0 8px;font-weight:600}
.row{display:flex;gap:12px;flex-wrap:wrap}.card{background:#121d33;border:1px solid #25344d;
border-radius:10px;padding:14px 16px;min-width:120px}.k{color:#8aa0bd;font-size:12px}
.v{font-size:22px;font-weight:700;margin-top:4px}.v.ok{color:#34d399}.v.bad{color:#f87171}
table{border-collapse:collapse;width:100%;max-width:640px}td,th{text-align:left;padding:6px 10px;
border-bottom:1px solid #25344d}th{color:#8aa0bd;font-weight:600}
textarea{width:100%;max-width:640px;height:150px;background:#0d1626;color:#e6edf6;
border:1px solid #25344d;border-radius:8px;padding:10px;font:12px monospace}
button{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:8px 16px;cursor:pointer;margin-top:8px}
pre{background:#0d1626;border:1px solid #25344d;border-radius:8px;padding:10px;max-width:640px;
white-space:pre-wrap;color:#f87171}.muted{color:#8aa0bd;font-size:12px}
.form{display:flex;gap:12px;flex-wrap:wrap}fieldset{border:1px solid #25344d;border-radius:8px;min-width:210px}
legend{color:#8aa0bd;padding:0 6px;font-size:12px}label{display:block;font-size:12px;color:#8aa0bd;margin:6px 0}
input,select{background:#0d1626;color:#e6edf6;border:1px solid #25344d;border-radius:6px;padding:4px 6px;width:88px}
</style></head><body>
<h1>配置对账 <span class=muted>(只读 · 不发布不热切)</span></h1>
<div class=row id=status></div>
<h2>最新编译版本摘要 <span class=muted>(运行配置=active;active 由后续 activate 设置,现可为"无")</span></h2><table id=products></table>
<h2>当前草稿 current_draft.json</h2><div id=draft class=muted>—</div>
<h2>校验草稿(只校验,不编译/不激活)</h2>
<textarea id=draftin placeholder="把 config_draft.json 粘进来,点校验"></textarea><br>
<button onclick=doValidate()>校验</button><pre id=verr style=display:none></pre>
<h2>添加采集设备 <span class=muted>(三段:硬件→业务点→显示;只写草稿,需再校验/编译/重启生效)</span></h2>
<div class=form>
 <fieldset><legend>① 硬件设备</legend>
  <label>device_id <input id=h_id value=ai_mod_9></label>
  <label>模板 <select id=h_tpl><option>rs485_8ai_modbus</option><option>rs485_8di_modbus</option></select></label>
  <label>总线 <input id=h_bus value=rs485_1></label>
  <label>从站 <input id=h_slave type=number value=9></label>
  <label>通道 <input id=h_ch value=AI1></label>
  <label>寄存器 <input id=h_reg type=number value=0></label>
  <label>数据类型 <select id=h_dt><option>uint16</option><option>int16</option><option>bool</option></select></label>
  <label>工程量程 <input id=h_emin type=number value=0> ~ <input id=h_emax type=number value=150></label>
  <label>scale <input id=h_scale value=0.1></label>
  <label>单位 <input id=h_unit value=℃></label>
 </fieldset>
 <fieldset><legend>② 业务测点</legend>
  <label>business_id <input id=b_id value=new_point></label>
  <label>模板 <select id=b_tpl><option>temperature_point</option><option>pressure_point</option></select></label>
  <label>point_id <input id=b_pid value=new_temp></label>
  <label>名称 <input id=b_label value=新增测点></label>
  <label>角色 <select id=b_role><option>measurement</option></select></label>
 </fieldset>
 <fieldset><legend>③ 显示卡片</legend>
  <label>页面 <select id=d_page><option>primary_loop</option><option>secondary_loop</option><option>system</option></select></label>
  <label>卡片 id <input id=d_card value=new_card></label>
  <label>卡片名 <input id=d_label value=新增卡片></label>
  <label>优先级 <input id=d_pri type=number value=50></label>
 </fieldset>
</div>
<button onclick=addDevice()>添加设备(写草稿)</button><pre id=aerr style=display:none></pre>
<script>
let TOK='';
async function api(m,p,b){const h={'Authorization':'Bearer '+TOK};
if(b)h['Content-Type']='application/json';
const r=await fetch(p,{method:m,headers:h,body:b?JSON.stringify(b):undefined});return r.json()}
async function boot(){
const lg=await(await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},
body:JSON.stringify({username:'config',password:'x'})})).json();TOK=lg.token;
const s=await api('GET','/api/config/status');
const eok=s.errors===0||s.errors===null;const lc=s.latest_compiled;
document.getElementById('status').innerHTML=
card('运行版本(active)',s.active_version??'无',s.active_version==null?'':'ok')+
card('最新编译',s.latest_version??'无')+
card('编译设备',lc?lc.devices:'—')+card('编译点位',lc?lc.points:'—')+
card('草稿错误',s.errors??'无草稿',eok?'ok':'bad')+card('有草稿',s.has_draft?'是':'否');
let rows='<tr><th>项</th><th>值</th></tr>';
if(lc){for(const k of ['version','config_version','devices','points','display_cards','safety_commands'])
 rows+='<tr><td>'+k+'</td><td>'+lc[k]+'</td></tr>'}
else rows+='<tr><td colspan=2>尚无编译版本(先添加设备并点编译)</td></tr>';
document.getElementById('products').innerHTML=rows;
const d=await api('GET','/api/config/draft');
document.getElementById('draft').textContent=d.has_draft?
('hardware_devices: '+d.draft.hardware_devices.length+' · business_devices: '+d.draft.business_devices.length+
' · industry: '+d.draft.industry):'尚无 current_draft(compile 后生成)';
}
function card(k,v,c){return '<div class=card><div class=k>'+k+'</div><div class="v '+(c||'')+'">'+v+'</div></div>'}
function val(id){return document.getElementById(id).value}
async function addDevice(){
const dev=val('h_id'),ch=val('h_ch'),role=val('b_role');
const payload={hardware:{device_id:dev,hardware_template:val('h_tpl'),bus_id:val('h_bus'),
 slave:+val('h_slave'),timeout_ms:250,retries:1,
 channels:[{channel:ch,register:+val('h_reg'),"function":3,data_type:val('h_dt'),
  raw_range:[0,65535],eng_range:[+val('h_emin'),+val('h_emax')],scale:+val('h_scale'),unit:val('h_unit')}]},
 business_devices:[{business_id:val('b_id'),business_template:val('b_tpl'),industry:'heating',
  bindings:{[role]:{point_id:val('b_pid'),label:val('b_label'),from:dev+'.'+ch}},
  display:{page:val('d_page'),card:val('d_card'),label:val('d_label'),priority:+val('d_pri')}}]};
const r=await api('POST','/api/config/devices',payload);const e=document.getElementById('aerr');
e.style.display='block';
if(r.ok){e.style.color='#34d399';
 e.textContent='✓ 已写入草稿(设备总数见上方"有草稿";产物未变,需再编译);可重复添加';boot()}
else{e.style.color='#f87171';e.textContent='✗ '+r.errors.length+' 错:\\n- '+r.errors.join('\\n- ')}}
async function doValidate(){const e=document.getElementById('verr');
let body;try{body=JSON.parse(document.getElementById('draftin').value)}catch(x){
e.style.display='block';e.style.color='#f87171';e.textContent='JSON 解析失败: '+x.message;return}
const r=await api('POST','/api/config/validate',body);e.style.display='block';
if(r.ok){e.style.color='#34d399';e.textContent='✓ 校验通过,'+0+' 错'}
else{e.style.color='#f87171';e.textContent='✗ '+r.errors.length+' 错:\\n- '+r.errors.join('\\n- ')}}
boot();
</script></body></html>"""


def add_device_to_draft(draft, payload):
    """纯函数:把 payload 的一台 hardware_device + 一组 business_device 追加到 draft 的副本,
    校验后返回。**不原地修改 draft**(deepcopy);校验失败不返回污染草稿。

    payload 至少含:
      hardware: 一条 hardware_device(dict)
      business_devices: 一组 business_device(非空 list)
    返回 (ok, errors, new_draft);失败时 new_draft 为 None。
    注意:这里只生成新草稿,不编译、不写盘、不碰 runtime —— 落盘由端点负责。"""
    if not isinstance(payload, dict):
        return False, ["payload 必须是对象"], None
    hw = payload.get("hardware")
    bizs = payload.get("business_devices")
    if not isinstance(hw, dict):
        return False, ["payload.hardware 缺失或非对象"], None
    if not isinstance(bizs, list) or not bizs:
        return False, ["payload.business_devices 缺失或为空"], None
    new_draft = copy.deepcopy(draft)
    new_draft.setdefault("hardware_devices", []).append(copy.deepcopy(hw))
    new_draft.setdefault("business_devices", []).extend(copy.deepcopy(bizs))
    errs = compiler.validate(new_draft)
    if errs:
        return False, errs, None                      # 不返回被污染的草稿
    return True, [], new_draft


def _gatewayc_compile_cli(draft, out_dir=None, validate_only=False):
    """D3:调 `gatewayc compile`。返回 (ok, errors)。out_dir 给定则落 4 产物;
    validate_only 仅校验。gatewayc 二进制不存在抛 FileNotFoundError(由上层回退 Python)。"""
    import subprocess
    import tempfile
    fd, tmp = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(draft, f, ensure_ascii=False)
        cmd = [GATEWAYC_BIN, "compile", tmp]
        if validate_only:
            cmd.append("--validate-only")
        elif out_dir:
            cmd += ["--out", out_dir]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            return True, []
        # gatewayc 把校验错误打到 stderr 的 "  - <err>" 行(与 Python compiler 逐字对拍一致)
        errs = [ln.strip()[2:] for ln in r.stderr.splitlines() if ln.strip().startswith("- ")]
        return False, errs or [(r.stderr.strip() or "gatewayc compile 失败")]
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _validate_draft(draft):
    """D3:优先 gatewayc compile --validate-only;无二进制回退 Python compiler.validate。"""
    try:
        _ok, errs = _gatewayc_compile_cli(draft, validate_only=True)
        return errs
    except FileNotFoundError:
        return compiler.validate(draft)


def _emit_generated(vd):
    """gatewayc load <vd> --emit-app-config <vd>/app_config.generated.json。"""
    import subprocess
    out = os.path.join(vd, "app_config.generated.json")
    subprocess.run([GATEWAYC_BIN, "load", vd, "--emit-app-config", out],
                   capture_output=True, text=True, check=True)


def compile_draft(draft):
    """validate → compile → 写 build/versions/N/*.json + 该目录内 app_config.generated.json
    + 存 current_draft.json。**不设 active、不热切运行时**(activate 留到后续)。返回 (ok, errors, status)。
    D3:编译/校验走 `gatewayc compile/load`;无 gatewayc 二进制(CI/测试)则回退 Python compiler/loader。"""
    errs = _validate_draft(draft)
    if errs:
        return False, errs, None                      # 校验失败不落任何产物
    n = next_version()                                # 写到新版本目录,绝不覆盖 active 所指
    vd = version_dir(n)
    os.makedirs(vd, exist_ok=True)
    try:
        ok, cerrs = _gatewayc_compile_cli(draft, out_dir=vd)
        if not ok:
            return False, cerrs, None
        _emit_generated(vd)                           # gatewayc load → app_config.generated.json
    except FileNotFoundError:                         # 无 gatewayc 二进制 → 回退 Python
        products = compiler.compile(draft)
        for name, obj in products.items():
            json.dump(obj, open(os.path.join(vd, name), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
        cfg = load_runtime_cfg(vd)
        json.dump(cfg, open(os.path.join(vd, "app_config.generated.json"),
                            "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(draft, open(CONFIG_DRAFT_PATH, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    # 普通 compile **不改 active**(activate 才改);如有争议先不自动设 active。
    return True, [], config_status()


def loadable_check(version):
    """干跑校验某编译版本是否"可加载",**完全不碰当前 runtime**(activate 设计文档第2步)。
    检查:产物能被 loader 读 → 能构造 source(用 SimSource,不开真串口)→ 能生成快照骨架,
    且点表注册表里的非派生点都能在快照骨架里出现。返回 (ok, errors, report)。"""
    vd = version_dir(version)
    pr = _read_json(os.path.join(vd, "point_registry.json"))
    if pr is None:
        return False, ["版本 %s 不存在或缺 point_registry" % version], None
    try:
        cfg = load_runtime_cfg(vd)                  # loader 能读产物?
    except Exception as e:                          # 缺 poll_plan 等会在此被抓
        return False, ["loader 读取失败: %s" % e], None
    errors = []
    if not cfg.get("devices"):
        errors.append("生成配置无设备")
    try:
        snap = SimSource(cfg.get("devices", [])).poll()   # 构造 source + 生成快照骨架
    except Exception as e:
        return False, ["构造 source/生成快照失败: %s" % e], None
    snap_points = {pid for d in snap.values() for pid in (d.get("points") or {})}
    expected = {pid for pid, e in pr.get("points", {}).items()
                if (e.get("source") or {}).get("kind") != "derived"}
    missing = sorted(expected - snap_points)
    if missing:
        errors.append("快照骨架缺点位: %s" % ",".join(missing))
    report = {"version": version, "devices": len(cfg.get("devices", [])),
              "snapshot_points": len(snap_points), "expected_points": len(expected),
              "missing": missing}
    return (not errors), errors, report


# ---- activate(第3步):RuntimeContext + 切换服务函数。仅在测试 harness 验证。 ----
# **本步不接 live runtime、不改 collector_loop/make_handler 取数方式**(那是第5步)。
class RuntimeContext:
    """live 采集线程与 handler(Step5.3 起)从这里读 source/controller;activate 替换其内容。
    collector 每轮在 lock 内取一次 source 引用,poll 在锁外执行(§8.2 方案B)。"""
    def __init__(self, source, controller, active_version=None, source_factory=None):
        self.lock = threading.Lock()
        self.source = source
        self.controller = controller
        self.active_version = active_version
        self.source_factory = source_factory          # live modbus 用真串口构造新 source;None=SimSource

    def current_source(self):
        with self.lock:                               # 取引用即释放,poll 在锁外
            return self.source


# activate 单飞锁(§8.3):整个 activate/rollback 操作互斥,禁止并发。
_ACTIVATE_INFLIGHT = threading.Lock()


def build_runtime_from_version(version, source_factory=None):
    """从某版本产物构造一套新的 (source, control_map, safety_policy, cfg)。不碰任何 ctx。
    source_factory 可注入(默认 SimSource,不开真串口);live modbus 由 main() 的工厂提供。"""
    cfg = load_runtime_cfg(version_dir(version))
    factory = source_factory or (lambda devices: SimSource(devices))
    return factory(cfg.get("devices", [])), cfg.get("control_map", {}), cfg.get("safety_policy"), cfg


def _health_check_source(source):
    """§8.2 方案B:对**尚未安装**的新 source 在锁外独立 poll 做健康检查。
    modbus 场景这里应进一步判关键点质量码(§4.3)。返回 (ok, errors)。"""
    try:
        snap = source.poll()
    except Exception as e:
        return False, ["健康检查采集失败: %s" % e]
    if not any((d.get("points") or {}) for d in snap.values()):
        return False, ["健康检查快照无点位"]
    return True, []


def activate_compiled_version(ctx, version, source_factory=None):
    """把某编译版本切成 ctx 的当前运行配置(§8.2 方案B):
    loadable_check(切前) → 构造新对象 → **锁外**对新 source 做健康检查 →
    通过则**锁内只做最短引用交换** → 写 active 指针。
    返回 (ok, errors, state),state ∈ {failed, active}。健康失败=failed(从未碰 live)。
    **锁内绝不 poll**;health 失败时 ctx 完全没动,无需回滚。"""
    ok, errs, _ = loadable_check(version)             # 切前结构校验,不碰 ctx
    if not ok:
        return False, errs, "failed"
    factory = source_factory or getattr(ctx, "source_factory", None)   # live modbus 工厂从 ctx 取
    try:
        new_source, new_cmap, new_spol, _ = build_runtime_from_version(version, factory)
    except Exception as e:
        return False, ["构造运行对象失败: %s" % e], "failed"
    healthy, herrs = _health_check_source(new_source)  # 锁外:对未安装的新 source 独立 poll
    if not healthy:
        return False, herrs, "failed"                  # 未触碰 ctx → failed
    with ctx.lock:                                     # 锁内只换引用,不 poll
        ctx.source = new_source
        ctx.controller.source = new_source
        ctx.controller.control_map = new_cmap
        ctx.controller.safety_policy = new_spol
        ctx.active_version = version
    write_active(version)                              # 提交:原子更新 active 指针
    return True, [], "active"


def try_activate(ctx, version, source_factory=None):
    """单飞包装(§8.3):已有 activate/rollback 在途 → 返回 None(调用方回 409)。
    否则执行 activate_compiled_version。"""
    if not _ACTIVATE_INFLIGHT.acquire(blocking=False):
        return None
    try:
        return activate_compiled_version(ctx, version, source_factory)
    finally:
        _ACTIVATE_INFLIGHT.release()


# ---- activate API 状态(第5.3步:操作 live ctx,active 成功后即 live 真实版本)。 ----
# Step4 的 sandbox ctx 与 wired_to_runtime 语义已退役:activate/rollback 直接切 live。
LAST_ACTIVATE = {"version": None, "state": None, "errors": [], "previous_active": None}


def select_startup_config(config_arg):
    """启动配置选择(Step 5.1):若 build/active 存在且其 app_config.generated.json 在,
    则从 versions/<active>/ 起 live;否则回退到 config_arg(旧 --config 行为)。
    **只决定读哪份 cfg,不改 collector/handler/activate/--products**。返回选中的文件路径。"""
    n = read_active()
    if n is not None:
        gen = os.path.join(version_dir(n), "app_config.generated.json")
        if os.path.isfile(gen):
            return gen
    return config_arg


def resolve_products_dir(products_arg):
    """启动展示派生目录解析(Step 5.2):--products 指向 build 时,解析到当前 active 版本目录
    (<products_arg>/versions/<active>),使展示映射(configure_maps)与 live cfg 同源。
    无 active 或该版本目录不存在 → 原样返回 products_arg(调用方再判 point_registry 是否在,
    不在则不派生、回退硬编码)。**不改 collector/handler/activate。**"""
    n = read_active()
    if n is not None:
        vd = os.path.join(products_arg, "versions", str(n))
        if os.path.isdir(vd):
            return vd
    return products_arg

# 可控点 → 写 tag 时实际下发的设定值点。
# 默认(回退):旧 app_config 把反馈点映射到设定值点;无编译产物时仍用它。
# 有编译产物时由 configure_maps() 改为"可写点自映射"(setpoint 点本身就是被采集点)。
CONTROLLABLE = {"valve_open": "valve_open_sp", "pump_freq": "pump_freq_sp",
                "sec_supply_temp": "sec_supply_temp_sp"}

# 设备类型(中文) → edge-os DeviceType 枚举(展示层标签映射,回退用)。
DEVTYPE = {"换热机组": "boiler", "循环泵": "pump_vfd", "电动调节阀": "valve_actuator",
           "压力传感器": "pressure_sensor", "安全IO": "io_module", "热表": "heat_meter",
           "电表": "energy_meter", "温度传感器": "temp_humidity_sensor", "采集模块": "other"}

# business_template → edge-os DeviceType(有 point_registry 时优先按它派生)。
TEMPLATE2EDGEOS = {"circulation_pump": "pump_vfd", "makeup_pump": "pump_vfd",
                   "vfd": "pump_vfd", "control_valve": "valve_actuator",
                   "pressure_point": "pressure_sensor", "temperature_point": "temp_humidity_sensor",
                   "heat_meter": "heat_meter", "energy_meter": "energy_meter",
                   "safety_io": "io_module"}
DEVTYPE_BY_DEVICE = {}   # device_id -> edge-os type;由 configure_maps() 从 point_registry 派生

# Modbus data_type → edge-os Tag.type 枚举(INT16|UINT16|FLOAT32|BOOLEAN|STRING)。
# uint32/int32 无对应枚举,退 FLOAT32(数值安全)。
DATA2TAGTYPE = {"bool": "BOOLEAN", "uint16": "UINT16", "int16": "INT16",
                "uint32": "FLOAT32", "int32": "FLOAT32", "float32": "FLOAT32"}
POINT_TAGTYPE = {}       # pid -> edge-os Tag.type;由 point_registry.data_type 派生
POINT_LABEL = {}         # pid -> 人类可读名;由 point_registry.name 派生
DISPLAY_RANK = {}        # pid -> 排序键(page 序, card priority, field 序);由 display_model 派生
DISPLAY_GROUP = {}       # pid -> "page/card";display_model 分组(edge-os 前端忽略,前向用)


def configure_maps(point_registry: dict, display_model: dict | None = None):
    """用编译产物派生展示层映射,取代硬编码(PRD §31)。
    point_registry:
      - 可写点(writable=True)即可控点,自映射(setpoint 点本身被采集,可直接写)。
      - 设备类型按 business_template 派生,比中文字符串匹配更稳。
      - Tag.type 按 data_type 派生,取代"全 FLOAT32"。
    display_model(可选):驱动 tag 排序与分组标签。edge-os Tag 模型无 page/card 概念,
      故此处只用于排序与附 group 标签;page/card 的完整语义归本地 HMI。"""
    pts = (point_registry or {}).get("points", {})
    # 产物驱动模式:无条件替换,即使可写点为空也清掉旧硬编码,避免残留可控点。
    ctrl = {pid: pid for pid, e in pts.items() if e.get("writable")}
    CONTROLLABLE.clear(); CONTROLLABLE.update(ctrl)
    DEVTYPE_BY_DEVICE.clear(); POINT_TAGTYPE.clear(); POINT_LABEL.clear()
    for pid, e in pts.items():
        did = (e.get("source") or {}).get("device_id")
        tmpl = e.get("business_template")
        if did and tmpl:
            DEVTYPE_BY_DEVICE[did] = TEMPLATE2EDGEOS.get(tmpl, "other")
        dtype = (e.get("source") or {}).get("data_type")
        if dtype:
            POINT_TAGTYPE[pid] = DATA2TAGTYPE.get(dtype, "FLOAT32")
        if e.get("name"):
            POINT_LABEL[pid] = e["name"]

    DISPLAY_RANK.clear(); DISPLAY_GROUP.clear()
    if display_model:
        for pi, page in enumerate(display_model.get("pages", [])):
            for card in page.get("cards", []):
                for fi, field in enumerate(card.get("fields", [])):
                    pid = field.get("point_id")
                    if not pid:
                        continue
                    DISPLAY_RANK[pid] = (pi, card.get("priority", 50), fi)
                    DISPLAY_GROUP[pid] = "%s/%s" % (page.get("page", ""), card.get("card", ""))


# ===========================================================================
# 快照 → edge-os 的 nodes / tags 模型
# ===========================================================================
def build_nodes_tags(view, endpoint):
    nodes, tags = [], []
    for d in view.get("devices", []):
        addr = d["addr"]
        nid = "node-%s" % addr
        ok = d.get("ok")
        nodes.append({
            "id": nid, "name": d["name"], "type": d.get("type", ""),
            "deviceType": DEVTYPE_BY_DEVICE.get(d.get("name", "")) or DEVTYPE.get(d.get("type", ""), "other"),
            "driver": "Modbus RTU", "endpoint": endpoint, "slaveId": addr,
            "status": "Running" if ok else "Error",
            "metrics": {"tx": 0, "rx": 0, "errors": 0 if ok else 1},
            "uptime": "-",
        })
        for pid, p in (d.get("points") or {}).items():
            controllable = pid in CONTROLLABLE
            tag = {
                "id": "tag-%s-%s" % (addr, pid), "nodeId": nid,
                "name": POINT_LABEL.get(pid, pid),
                "address": pid, "type": POINT_TAGTYPE.get(pid, "FLOAT32"),
                "access": "RW" if controllable else "R",
                "value": p.get("v") if p.get("v") is not None else 0,
                "timestamp": d.get("ts", int(time.time() * 1000)),
                "unit": p.get("u", ""),
            }
            if pid in DISPLAY_GROUP:                 # display_model 分组(前向用)
                tag["group"] = DISPLAY_GROUP[pid]
            tags.append(tag)
    # display_model 有则按 (node, 展示优先级) 排序;未展示点排后,不丢弃(避免藏数据)。
    if DISPLAY_RANK:
        big = (9999, 9999, 9999)
        # address 即 point_id;name 现在是人类可读 label,排序须用 address
        tags.sort(key=lambda t: (t["nodeId"], DISPLAY_RANK.get(t["address"], big), t["address"]))
    return nodes, tags


def gatewayc_view(core_url, timeout=2):
    """从 Go 核心(gatewayc:8091)取 /api/snapshot 作为 view。
    边界重构:nexus 不再内嵌采集,改消费 gatewayc。第3步把 collect/make_handler 切到这里;
    现仅供并行对账(nexus_reconcile.py)与 client 复用。默认 live 仍走内嵌,本函数不改变现有行为。"""
    import urllib.request
    with urllib.request.urlopen(core_url.rstrip("/") + "/api/snapshot", timeout=timeout) as r:
        return json.load(r)


CORE_URL = None   # --core-url 给定则进 remote 模式:nexus 消费 gatewayc,不开 source、不当总线主站


def remote_command(core_url, point_id, value, timeout=3):
    """把控制下发转发到 gatewayc /api/command,返回 (ok, reason)。"""
    import urllib.request
    data = json.dumps({"point_id": point_id, "value": value}).encode()
    req = urllib.request.Request(core_url.rstrip("/") + "/api/command", data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        return bool(d.get("ok")), d.get("reason", "")
    except Exception as e:
        return False, "gatewayc 下发失败: %s" % e


class RemoteController:
    """remote 模式控制器:apply 转发到 gatewayc(Go controller 做安全/决策/写),nexus 不本地写。
    接口对齐 app.Controller.apply(point_id, value, command_id, origin)。"""
    def __init__(self, core_url):
        self.core_url = core_url
        self.source = None             # 占位:remote 模式无本地 source

    def apply(self, point_id, value, command_id="", origin=""):
        return remote_command(self.core_url, point_id, value)


GW_PIDFILE = None   # remote 激活重启 gatewayc 用(supervisor 写的 pid 文件)


def _restart_gatewayc():
    """SIGTERM gatewayc;supervisor 据 gatewayc.pid 重启时会带新 active 配置。"""
    try:
        with open(GW_PIDFILE, encoding="utf-8") as f:
            pid = int(f.read().strip())
        os.kill(pid, 15)                 # SIGTERM(不引 signal 模块)
        return True
    except (OSError, ValueError, TypeError) as e:
        print("[激活] 重启 gatewayc 失败(pidfile=%s): %s" % (GW_PIDFILE, e), flush=True)
        return False


def _wait_gatewayc_healthy(core_url, timeout=30, stale_ms=6000):
    """轮询 gatewayc /api/health,采集新鲜(年龄≤stale_ms)即就绪。"""
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(core_url.rstrip("/") + "/api/health", timeout=2) as r:
                age = json.load(r).get("collector_age_ms", 1e12)
            if 0 <= age <= stale_ms:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def remote_activate(version):
    """remote 模式激活(D1 方案A):翻 active 指针 → 重启 gatewayc(supervisor 带新配置)→
    启动健康门;不过则回退上一版重启。返回 (ok, errors, state)。"""
    if version is None:
        return False, ["无可激活版本(先 compile)"], "failed"
    prev = read_active()
    write_active(version)
    if not _restart_gatewayc():
        if prev is not None:                 # 重启没成 → 回退指针,别留 active 翻了但没切的不一致
            write_active(prev)
        return False, ["无法重启 gatewayc(pidfile 不可用,supervisor 在跑吗?)"], "failed"
    if _wait_gatewayc_healthy(CORE_URL):
        return True, [], "active"
    if prev is not None:                 # 健康门失败 → 回退上一版
        write_active(prev)
    else:
        try:
            os.remove(_active_file())
        except OSError:
            pass
    _restart_gatewayc()
    _wait_gatewayc_healthy(CORE_URL)
    return False, ["新版本 %s 健康门失败,已回退到 %s" % (version, prev)], "rolled_back"


def sys_metrics():
    cpu, mem = 5.0, 30.0
    try:
        with open("/proc/loadavg") as f:
            cpu = min(100.0, float(f.read().split()[0]) * 25)
        mt = ma = 0
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal:"):
                mt = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                ma = int(line.split()[1])
        if mt:
            mem = round((mt - ma) * 100.0 / mt, 1)
    except OSError:
        cpu, mem = round(random.uniform(3, 15), 1), round(random.uniform(28, 45), 1)
    return {"cpu": round(cpu, 1), "memory": mem, "throughput": 0,
            "rx": 0, "tx": 0, "nbRx": 0, "nbTx": 0, "network": []}


# ===========================================================================
# socket.io (Engine.IO v4 + Socket.IO v5) —— 仅 polling 传输,纯标准库
# ===========================================================================
RS = "\x1e"   # EIO4 多包分隔符


def eio_open(sid):
    return "0" + json.dumps({"sid": sid, "upgrades": [], "pingInterval": 25000,
                             "pingTimeout": 20000, "maxPayload": 1000000})


def sio_event(event, data):
    return "42" + json.dumps([event, data], ensure_ascii=False)


class SocketHub:
    def __init__(self):
        self.sessions = {}                  # sid -> {q: deque, ev: Event}
        self.lock = threading.Lock()

    def new_session(self):
        sid = "%016x" % random.getrandbits(64)
        with self.lock:
            self.sessions[sid] = {"q": deque(), "ev": threading.Event()}
        return sid

    def _push(self, sid, packet):
        s = self.sessions.get(sid)
        if s:
            s["q"].append(packet)
            s["ev"].set()

    def broadcast(self, packet):
        with self.lock:
            sids = list(self.sessions)
        for sid in sids:
            self._push(sid, packet)

    def poll(self, sid, timeout=20):
        s = self.sessions.get(sid)
        if s is None:
            return "0" + json.dumps({"sid": self.new_session()})  # 让客户端重握手
        s["ev"].wait(timeout)
        with self.lock:
            packets = list(s["q"]); s["q"].clear(); s["ev"].clear()
        if not packets:
            return "2"                       # ping,维持长轮询
        return RS.join(packets)

    def handle_post(self, sid, body):
        s = self.sessions.get(sid)
        if s is None:
            return
        for pkt in body.split(RS):
            if pkt.startswith("40"):         # Socket.IO CONNECT
                self._push(sid, "40" + json.dumps({"sid": "%016x" % random.getrandbits(64)}))
            elif pkt == "2":                 # client ping → pong
                self._push(sid, "3")
            # "3"(pong)/其它:忽略


# ===========================================================================
# HTTP:静态 dist + REST + /socket.io
# ===========================================================================
def make_handler(runtime, live_ctx, hub, dist_dir, endpoint, tokens):
    # 控制走 live_ctx.controller(activate 会原子替换其 source/control_map/safety_policy)。
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            if isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False))

        def _authed(self):
            auth = self.headers.get("Authorization", "")
            return auth.startswith("Bearer ") and len(auth) > 8

        # ---- GET ----
        def do_GET(self):
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            if path == "/socket.io/":
                sid = qs.get("sid", [None])[0]
                if not sid:
                    sid = hub.new_session()
                    return self._send(200, eio_open(sid), "text/plain; charset=utf-8")
                return self._send(200, hub.poll(sid), "text/plain; charset=utf-8")
            if path == "/config":            # 自包含只读配置对账页
                return self._send(200, CONFIG_PAGE_HTML, "text/html; charset=utf-8")
            if path == "/api/me":
                return self._json({"username": "admin", "role": "admin"})
            if path == "/api/init":
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                view = runtime.view()
                nodes, tags = build_nodes_tags(view, endpoint)
                return self._json({"nodes": nodes, "tags": tags, "apps": [], "rules": []})
            if path == "/api/snapshot":          # 给本地 LCD(drm_hmi_v2)用
                return self._json(runtime.view())
            if path == "/api/config/status":     # 配置发布后端:只读状态
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                return self._json(config_status())
            if path == "/api/config/products":   # 只读:编译产物摘要(对账页)
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                return self._json(config_products_summary())
            if path == "/api/config/draft":      # 只读:当前 config_draft
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                d = _read_json(CONFIG_DRAFT_PATH)
                return self._json({"has_draft": d is not None, "draft": d})
            if path == "/api/config/activate/status":   # 只读:激活状态(active=live 真实版本)
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                return self._json({"active": read_active(), "latest": latest_version(),
                                   "live_active_version": live_ctx.active_version,
                                   "last_activate": LAST_ACTIVATE})
            if path == "/api/scada":
                return self._json([])
            if path == "/api/history":
                return self._json([])
            if path.startswith("/api/"):
                return self._json({})
            return self._static(path)

        def _static(self, path):
            rel = path.lstrip("/") or "index.html"
            full = os.path.normpath(os.path.join(dist_dir, rel))
            if not full.startswith(dist_dir) or not os.path.isfile(full):
                full = os.path.join(dist_dir, "index.html")   # SPA 兜底
            if not os.path.isfile(full):
                return self._send(404, "not found", "text/plain")
            ext = full.rsplit(".", 1)[-1].lower()
            ctype = {"html": "text/html", "js": "text/javascript", "css": "text/css",
                     "json": "application/json", "svg": "image/svg+xml",
                     "png": "image/png", "ico": "image/x-icon",
                     "woff2": "font/woff2", "woff": "font/woff"}.get(ext, "application/octet-stream")
            self._send(200, open(full, "rb").read(), ctype + "; charset=utf-8")

        # ---- POST ----
        def do_POST(self):
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length) if length else b""
            if path == "/socket.io/":
                hub.handle_post(qs.get("sid", [None])[0], raw.decode("utf-8", "replace"))
                return self._send(200, "ok", "text/plain")
            try:
                body = json.loads(raw or b"{}")
            except ValueError:
                body = {}
            if path == "/api/login":
                tok = "%032x" % random.getrandbits(128)
                tokens.add(tok)
                return self._json({"token": tok, "user": {"username": body.get("username", "admin")}})
            if path == "/api/command":          # 本地触摸屏控制面板用
                ok, reason = live_ctx.controller.apply(body.get("point_id", ""), body.get("value"), origin="lcd")
                return self._json({"ok": ok, "reason": reason})
            if path == "/api/tags/write":
                ok, reason = self._write_tag(body.get("tagId", ""), body.get("value"))
                return self._json({"ok": ok, "error": reason} if not ok else {"ok": True})
            if path == "/api/config/validate":   # 校验草稿,返回错误列表(不落产物)
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                errs = _validate_draft(body)          # D3:gatewayc compile --validate-only(无二进制回退 Python)
                return self._json({"ok": not errs, "errors": errs})
            if path == "/api/config/compile":    # 校验+编译+落产物,不热切运行时
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                ok, errs, status = compile_draft(body)
                return self._json({"ok": ok, "errors": errs, "status": status})
            if path == "/api/config/devices":    # 添加采集设备:只更新草稿,不编译/不写 build/不热切
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                base = _read_json(CONFIG_DRAFT_PATH)
                if base is None:                 # 不凭空创建完整 draft
                    return self._json({"ok": False,
                                       "errors": ["无 current_draft;请先 /api/config/compile 生成基础草稿"],
                                       "status": config_status()}, 400)
                ok, errs, new_draft = add_device_to_draft(base, body)
                if ok:                           # 仅写回草稿,绝不 compile/写 build/动 runtime
                    json.dump(new_draft, open(CONFIG_DRAFT_PATH, "w", encoding="utf-8"),
                              ensure_ascii=False, indent=2)
                return self._json({"ok": ok, "errors": errs, "status": config_status()})
            if path == "/api/config/activate":   # 运行中切 live(§8.2 方案B + §8.3 单飞)
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                if CORE_URL:                     # remote 模式:翻指针 + 重启 gatewayc + 健康门 + 回退(D1方案A)
                    version = body.get("version") or latest_version()
                    prev = read_active()
                    ok, errs, state = remote_activate(version)
                    LAST_ACTIVATE.update({"version": version, "state": state,
                                          "errors": ([] if ok else errs),
                                          "previous_active": (prev if ok else LAST_ACTIVATE.get("previous_active"))})
                    return self._json({"ok": ok, "version": version, "state": state,
                                       "errors": errs, "status": config_status()})
                version = body.get("version") or latest_version()
                if version is None:
                    return self._json({"ok": False, "errors": ["无可激活版本(先 compile)"]}, 400)
                prev = read_active()
                res = try_activate(live_ctx, version)
                if res is None:                      # 单飞:已有 activate/rollback 在途
                    return self._json({"ok": False, "errors": ["激活进行中,请重试"]}, 409)
                ok, errs, state = res
                if ok:
                    LAST_ACTIVATE.update({"version": version, "state": state,
                                          "errors": [], "previous_active": prev})
                else:
                    LAST_ACTIVATE.update({"version": version, "state": state, "errors": errs})
                return self._json({"ok": ok, "version": version, "state": state,
                                   "errors": errs, "status": config_status()})
            if path == "/api/config/rollback":   # 回滚到上一激活版本(运行中切 live)
                if not self._authed():
                    return self._json({"error": "Unauthorized"}, 401)
                if CORE_URL:                     # remote 模式:回滚=激活上一版(同样翻指针+重启+健康门)
                    rprev = LAST_ACTIVATE.get("previous_active")
                    if rprev is None:
                        return self._json({"ok": False, "errors": ["无可回滚的上一版本"]}, 400)
                    cur = read_active()
                    ok, errs, state = remote_activate(rprev)
                    if ok:
                        LAST_ACTIVATE.update({"version": rprev, "state": state,
                                              "errors": [], "previous_active": cur})
                    return self._json({"ok": ok, "version": rprev, "state": state,
                                       "errors": errs, "status": config_status()})
                prev = LAST_ACTIVATE.get("previous_active")
                if prev is None:
                    return self._json({"ok": False, "errors": ["无可回滚的上一版本"]}, 400)
                cur = read_active()
                res = try_activate(live_ctx, prev)
                if res is None:
                    return self._json({"ok": False, "errors": ["激活进行中,请重试"]}, 409)
                ok, errs, state = res
                if ok:
                    LAST_ACTIVATE.update({"version": prev, "state": state,
                                          "errors": [], "previous_active": cur})
                return self._json({"ok": ok, "version": prev, "state": state,
                                   "errors": errs, "status": config_status()})
            if path in ("/api/nodes", "/api/tags", "/api/apps", "/api/rules",
                        "/api/scada", "/api/change-password", "/api/restart", "/api/factory-reset"):
                return self._json({"ok": True})
            return self._json({"ok": True})

        def do_DELETE(self):
            return self._json({"ok": True})

        def _write_tag(self, tag_id, value):
            # tag-<addr>-<pid>
            parts = tag_id.split("-", 2)
            if len(parts) != 3:
                return False, "bad tagId"
            pid = parts[2]
            sp = CONTROLLABLE.get(pid)
            if not sp:
                return False, "该点位不可写"
            ok, reason = live_ctx.controller.apply(sp, value, origin="nexus")
            return ok, reason

    return H


# ===========================================================================
# 后台:采集 + 周期广播 socket 事件
# ===========================================================================
def broadcaster(runtime, hub, endpoint, stop):
    while not stop.is_set():
        view = runtime.view()
        nodes, tags = build_nodes_tags(view, endpoint)
        hub.broadcast(sio_event("tag-change", tags))
        hub.broadcast(sio_event("node-change", nodes))
        hub.broadcast(sio_event("system-metrics", sys_metrics()))
        stop.wait(2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(HERE, "app_config.json"))
    ap.add_argument("--dist", default=os.path.join(HERE, "nexus-dist"))
    ap.add_argument("--source", choices=["sim", "modbus"], default=None)
    ap.add_argument("--serial", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--core-url", default=None,
                    help="给定则 remote 模式:从 gatewayc(如 http://127.0.0.1:8091)取数 + 转发控制,nexus 不开 source")
    ap.add_argument("--gw-pidfile", default="/tmp/gwsup/gatewayc.pid",
                    help="remote 激活重启 gatewayc 用的 pid 文件(supervisor 写)")
    ap.add_argument("--gatewayc-bin", default="gatewayc",
                    help="D3:配置编译/校验调用的 gatewayc 二进制路径(不可用时回退 Python compiler)")
    ap.add_argument("--products", default=None,
                    help="编译产物目录;给定则从 point_registry 派生可控点与设备类型")
    args = ap.parse_args()
    global GATEWAYC_BIN
    GATEWAYC_BIN = args.gatewayc_bin                   # D3:配置编译/校验用的 gatewayc 二进制

    cfg_path = select_startup_config(args.config)     # 有 active 则从 versions/<active> 起 live
    cfg = json.load(open(cfg_path))
    if cfg_path != args.config:
        print("[启动] active=%s,从 %s 起 live(Step5.1 启动恢复)" % (read_active(), cfg_path), flush=True)
    else:
        print("[启动] 无 active,用 --config %s" % args.config, flush=True)
    if args.products:
        pdir = resolve_products_dir(args.products)        # 解析到 active 版本目录,与 live cfg 同源
        reg_path = os.path.join(pdir, "point_registry.json")
        dm_path = os.path.join(pdir, "display_model.json")
        if os.path.exists(reg_path):
            display_model = json.load(open(dm_path, encoding="utf-8")) if os.path.exists(dm_path) else None
            configure_maps(json.load(open(reg_path, encoding="utf-8")), display_model)
            print("[映射] 已从 %s 派生 CONTROLLABLE/设备类型/Tag类型%s"
                  % (pdir, "/展示排序" if display_model else ""), flush=True)
        else:                                             # 无 active 产物 → 不派生,回退硬编码
            print("[映射] %s 无 point_registry,跳过派生(回退硬编码映射)" % pdir, flush=True)
    runtime = Runtime(cfg)
    if args.core_url:                                 # remote 模式:消费 gatewayc,不开 source
        global CORE_URL, GW_PIDFILE
        CORE_URL = args.core_url
        GW_PIDFILE = args.gw_pidfile
        endpoint = "gatewayc"
        live_ctx = RuntimeContext(None, RemoteController(args.core_url),
                                  active_version=read_active(), source_factory=None)
        print("[源] 远程 gatewayc %s(nexus 不开 source、不当 RS485 主站)" % args.core_url, flush=True)
    else:
        kind = args.source or cfg.get("source", "sim")
        if kind == "modbus":
            dev = args.serial or cfg.get("serial", "/dev/ttyS1")
            source = ModbusSource(dev, cfg.get("baud", 9600), cfg["devices"])
            endpoint = dev
            print("[源] modbus %s" % dev, flush=True)
        else:
            source = SimSource(cfg["devices"])
            endpoint = "sim"
            print("[源] sim 内置仿真", flush=True)
        controller = Controller(runtime, source, cfg.get("control_map", {}),
                                safety_policy=cfg.get("safety_policy"))
        # live modbus 激活时要用真串口构造新 source(SimSource 默认不开串口)。
        live_source_factory = ((lambda devices: ModbusSource(
            args.serial or cfg.get("serial", "/dev/ttyS1"), cfg.get("baud", 9600), devices))
            if kind == "modbus" else None)
        # Step5.3:live RuntimeContext —— collector/handler/activate 都经它取数,activate 原子替换其内容。
        live_ctx = RuntimeContext(source, controller, active_version=read_active(),
                                  source_factory=live_source_factory)
    hub = SocketHub()
    tokens = set()
    stop = threading.Event()

    def collect():
        while not stop.is_set():
            try:
                if CORE_URL:                          # remote:取 gatewayc view,devices[] 重组回 {addr:dev}
                    v = gatewayc_view(CORE_URL)        # 喂进同一个 runtime,handler/广播器读 runtime.view() 不变
                    runtime.update({d["addr"]: d for d in v.get("devices", [])})
                else:
                    src = live_ctx.current_source()   # 锁内取引用,poll 在锁外(§8.2)
                    runtime.update(src.poll())
            except Exception as exc:
                print("[采集] 异常:", exc, flush=True)
            stop.wait(cfg.get("poll_interval_s", 2))
    threading.Thread(target=collect, daemon=True).start()
    threading.Thread(target=broadcaster, args=(runtime, hub, endpoint, stop), daemon=True).start()

    dist = os.path.normpath(args.dist)
    port = args.port or cfg.get("http_port", 8092)
    handler = make_handler(runtime, live_ctx, hub, dist, endpoint, tokens)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print("[nexus] http://0.0.0.0:%d/  dist=%s" % (port, dist), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()

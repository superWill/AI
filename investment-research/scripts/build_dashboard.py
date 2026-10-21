#!/usr/bin/env python3
"""AI capex 周期看板 · 渲染器。

读 data/dashboard/{daily.csv, quarterly.csv, status.json} → 写 site/dashboards/capex-cycle.html。
单文件、无外链、内嵌数据 + 原生 SVG；深色/浅色；每张图带 hover 十字线 + 表格视图。
图表规范按 dataviz skill：单轴、2px 线、≥8px 端点带 2px 底色环、≤24px 柱、4px 圆角、≥2 系列必有图例、文字不穿系列色。

用法：
    .venv/bin/python scripts/build_dashboard.py
通常由 fetch_dashboard.py 在抓完数据后调用。
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "dashboard"
OUT = ROOT / "site" / "dashboards" / "capex-cycle.html"

NUM_COLS_HINT = None  # 全部非 date 列按数字解析


def load_daily() -> list[dict]:
    p = DATA_DIR / "daily.csv"
    if not p.exists():
        return []
    rows = []
    with p.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            o: dict = {"date": r["date"]}
            for k, v in r.items():
                if k == "date":
                    continue
                try:
                    o[k] = float(v) if v not in ("", None) else None
                except ValueError:
                    o[k] = None
            rows.append(o)
    return sorted(rows, key=lambda r: r["date"])


def load_quarterly() -> dict[str, list[dict]]:
    p = DATA_DIR / "quarterly.csv"
    out: dict[str, list[dict]] = {}
    if not p.exists():
        return out
    with p.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["series"], []).append({"period": r["period"], "value": float(r["value"]), "unit": r["unit"], "source": r["source"]})
    for k in out:
        out[k].sort(key=lambda x: x["period"])
    return out


def load_status() -> dict:
    p = DATA_DIR / "status.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


QUARTERLY_META = [
    # key, 标题, 说明, 增速用 QoQ(需要连续季度)
    ("SPCX_SI_REV", "SPCX SI 分部收入", "$B/季 · Anthropic/Google 云协议 + Cursor + Grok"),
    ("SPCX_CAPEX", "SPCX 合并 capex", "$B/季 · Q4'26 指引 $35–40B"),
    ("SPCX_CONN_REV", "SPCX Connectivity 收入", "$B/季 · Starlink 消费 + 企业政府"),
    ("STARLINK_SUBS", "Starlink 消费订阅", "百万 · 期末"),
    ("STARLINK_NET_ADDS", "Starlink 单季净增", "百万 · 170→160 已下降一季"),
    ("STARLINK_ARPU", "Starlink 消费 ARPU", "$/月 · Q3 环比 +5%"),
    ("SPCX_NAMEPLATE_GW", "SPCX 铭牌算力", "GW · 年底指引 2.5–3，2027 +10"),
    ("CRWV_REV", "CoreWeave 收入", "$B/季"),
    ("ORCL_RPO_QOQ_ADD", "Oracle RPO 环比增量", "$B · 85→26 已下降一季；连续两季 <30 升级"),
    ("DRAM_CONTRACT_QOQ", "DRAM 合约价环比", "% · TrendForce 中值；内存腿二阶导"),
]

LINE_CHARTS = [
    # id, 标题, 副标题, 列→名, 格式, index100
    ("gpu", "算力现货（RunPod 按需最低价）", "$/GPU·小时 · SF Compute/Vast 挡爬虫、SemiAnalysis 付费，这是公开的每日代理；红绿灯按一年期合约另判",
     [("H100_SXM", "H100 SXM"), ("H200_SXM", "H200 SXM"), ("B200", "B200"), ("B300", "B300")], "$", False),
    ("px", "价格（指数化，区间首日 = 100）", "SOXX = 组合真实因子；SPCX/CRWV/ORCL = 算力批发商；单轴指数化而不是双轴",
     [("SOXX", "SOXX"), ("SPCX", "SPCX"), ("CRWV", "CRWV"), ("NVDA", "NVDA"), ("ORCL", "ORCL"), ("SPY", "SPY")], "", True),
    ("rates", "美债收益率", "% · 10Y 5.1 以上是 9/15 三档的基准档上沿",
     [("US10Y", "10Y"), ("US5Y", "5Y"), ("US30Y", "30Y")], "%", False),
    ("credit", "信用代理 HYG / LQD", "高收益 ÷ 投资级 ETF 价格比 · 下行 = 高收益相对走弱（FRED HY OAS 本机不可达）",
     [("HYG_LQD", "HYG/LQD")], "", False),
    ("vix", "VIX", "", [("VIX", "VIX")], "", False),
    ("wti", "WTI 原油", "$/桶 · 油价冲击 = 利率杀的燃料", [("WTI", "WTI")], "$", False),
    ("tokens", "OpenRouter 榜单前十模型 token 合计", "万亿 token · 公开的需求用量代理；看斜率不看绝对值", [("OR_TOP10_TOKENS_T", "前十合计")], "T", False),
    ("odds", "预测市场概率", "% · Polymarket / Kalshi；流动性薄，看趋势",
     [("PM_STARSHIP_LT5_2026", "2026 年 Starship 入轨 <5 次"), ("PM_STARSHIP_REUSE_2027", "2027 前完全复用"),
      ("PM_TSLA_SPCX_MERGER_2027", "TSLA–SPCX 2027 底前合并"), ("KALSHI_MARS_2030", "2030 前登陆火星")], "%", False),
]

TILES = [("SOXX", "SOXX", "", False), ("SPCX", "SPCX", "$", False), ("NVDA", "NVDA", "$", False), ("CRWV", "CRWV", "$", False),
         ("US10Y", "10Y 收益率", "%", True), ("VIX", "VIX", "", True), ("H100_SXM", "H100 现货 $/h", "$", True), ("B200", "B200 现货 $/h", "$", True)]


def build() -> Path:
    daily = load_daily()
    for r in daily:  # 派生列
        r["HYG_LQD"] = round(r["HYG"] / r["LQD"], 4) if r.get("HYG") and r.get("LQD") else None
    quarterly = load_quarterly()
    status = load_status()
    payload = {
        "built": date.today().isoformat(),
        "daily": daily,
        "quarterly": quarterly,
        "qmeta": [{"key": k, "title": t, "sub": s} for k, t, s in QUARTERLY_META],
        "lines": [{"id": i, "title": t, "sub": s, "series": [{"col": c, "name": n} for c, n in cols], "fmt": f, "index100": ix}
                  for i, t, s, cols, f, ix in LINE_CHARTS],
        "tiles": [{"col": c, "label": l, "fmt": f, "upBad": ub} for c, l, f, ub in TILES],
        "status": status,
    }
    html = TEMPLATE.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>AI capex 周期看板</title>
<style>
:root{color-scheme:light;
 --page:#f9f9f7;--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
 --s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#6250d6;--s8:#e34948;
 --good:#0ca30c;--warn:#fab219;--serious:#ec835a;--crit:#d03b3b;--upgood:#006300;--neutral:#f0efec}
@media (prefers-color-scheme: dark){:root:where(:not([data-theme="light"])){color-scheme:dark;
 --page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
 --s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767;--upgood:#0ca30c;--neutral:#383835}}
:root[data-theme="dark"]{color-scheme:dark;
 --page:#0d0d0d;--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
 --s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s5:#d55181;--s6:#008300;--s7:#9085e9;--s8:#e66767;--upgood:#0ca30c;--neutral:#383835}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;padding:0 16px 48px}
header{max-width:1280px;margin:0 auto;padding:20px 0 8px;display:flex;flex-wrap:wrap;gap:12px;align-items:baseline;justify-content:space-between}
h1{font-size:20px;margin:0;font-weight:650}
.meta{color:var(--ink2);font-size:13px}
.toolbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.btn{border:1px solid var(--border);background:var(--surface);color:var(--ink);border-radius:8px;padding:6px 10px;font-size:13px;cursor:pointer}
.btn[aria-pressed="true"]{font-weight:700;box-shadow:inset 0 0 0 1px var(--ink)}
main{max-width:1280px;margin:0 auto;display:grid;gap:14px}
section.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px 16px}
h2{font-size:15px;margin:0 0 4px;font-weight:650}
.sub{color:var(--ink2);font-size:12.5px;margin-bottom:8px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fit,minmax(min(100%,540px),1fr))}
.grid.tiles{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px;display:grid;gap:2px}
.tile .label{font-size:12.5px;color:var(--ink2)}
.tile .value{font-size:24px;font-weight:600}
.tile .delta{font-size:12.5px;color:var(--ink2)}
.tile .delta.up{color:var(--upgood)} .tile .delta.down{color:var(--crit)}
.chips{display:flex;flex-wrap:wrap;gap:8px}
.chip{display:flex;gap:8px;align-items:flex-start;border:1px solid var(--border);border-radius:10px;padding:8px 10px;min-width:240px;flex:1 1 280px;background:var(--surface)}
.chip .dot{width:12px;height:12px;border-radius:50%;margin-top:4px;flex:none}
.chip .t{font-weight:600;font-size:13px}.chip .n{font-size:12.5px;color:var(--ink2)}
.green .dot{background:var(--good)}.yellow .dot{background:var(--warn)}.red .dot{background:var(--crit)}
.chip .state{font-size:11px;color:var(--muted);margin-left:4px}
.chart{position:relative}
svg{width:100%;height:auto;display:block;overflow:visible}
.legend{display:flex;flex-wrap:wrap;gap:10px 14px;font-size:12.5px;color:var(--ink2);margin:4px 0 2px}
.legend .k{display:inline-block;width:14px;height:3px;border-radius:2px;vertical-align:middle;margin-right:5px}
.tip{position:absolute;pointer-events:none;background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:6px 8px;font-size:12px;box-shadow:0 2px 8px rgba(0,0,0,.12);display:none;z-index:2;min-width:120px}
.tip .d{color:var(--ink2);margin-bottom:2px}
.tip .r{display:flex;justify-content:space-between;gap:12px}
.tip .r .n::before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--c);margin-right:5px}
.tbl{display:none;overflow:auto;margin-top:8px}
.tbl table{border-collapse:collapse;font-size:12px;font-variant-numeric:tabular-nums}
.tbl th,.tbl td{border-bottom:1px solid var(--grid);padding:3px 8px;text-align:right}
.tbl th:first-child,.tbl td:first-child{text-align:left}
.chart.table .tbl{display:block}
.toggle{position:absolute;right:0;top:-2px}
.axis text{fill:var(--muted);font-size:11px;font-variant-numeric:tabular-nums}
.grid-line{stroke:var(--grid);stroke-width:1}
.baseline{stroke:var(--axis);stroke-width:1}
.lbl{fill:var(--ink2);font-size:11.5px}
.notes{font-size:12.5px;color:var(--ink2)}
.notes li{margin:2px 0}
@media (max-width:640px){.tile .value{font-size:20px}}
</style>
</head>
<body>
<header>
  <div><h1>AI capex 周期看板</h1><div class="meta" id="meta"></div></div>
  <div class="toolbar">
    <span class="meta">区间</span>
    <button class="btn" data-range="30">30 天</button><button class="btn" data-range="90" aria-pressed="true">90 天</button>
    <button class="btn" data-range="180">180 天</button><button class="btn" data-range="0">全部</button>
    <button class="btn" id="theme">深/浅</button>
  </div>
</header>
<main>
  <section class="card"><h2>四大触发器 <span id="tcount"></span> · 领先读数</h2>
    <div class="sub" id="status-sub"></div>
    <div class="chips" id="triggers"></div>
    <div class="sub" style="margin-top:10px">领先读数（周复盘 3b：价格先动、增速其次、触发器最后）</div>
    <div class="chips" id="leading"></div>
    <div class="sub" id="ladder" style="margin-top:8px"></div>
  </section>
  <div class="grid tiles" id="tiles"></div>
  <div class="grid" id="lines"></div>
  <section class="card"><h2>季度序列：水平与增速二阶导</h2>
    <div class="sub">左图水平、右图环比增速（%）；增速连续两季下降 = 黄。只在连续季度之间算环比，缺季不算。数据手工维护在 data/dashboard/quarterly.csv，财报对账时追加。</div>
    <div class="grid" id="quarterly"></div>
  </section>
  <section class="card"><h2>备注</h2><ul class="notes" id="notes"></ul>
    <div class="sub">数据：Yahoo（价格/收益率）· RunPod GraphQL（GPU 按需价）· OpenRouter 榜单 · Polymarket / Kalshi。日更脚本 scripts/fetch_dashboard.py；状态 data/dashboard/status.json 周复盘手改。</div>
  </section>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const SERIES = ['--s1','--s2','--s3','--s4','--s5','--s6','--s7','--s8'];
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
let RANGE = 90;
const fmtN = (v, f) => v == null ? '—' : (f === '$' ? '$' : '') + (Math.abs(v) >= 1000 ? v.toLocaleString(undefined,{maximumFractionDigits:0}) : (Math.abs(v) >= 100 ? v.toFixed(1) : v.toFixed(2))) + (f === '%' ? '%' : (f === 'T' ? 'T' : ''));
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function niceTicks(lo, hi, n = 4) {
  if (!(hi > lo)) { hi = lo + 1; lo = lo - 1; }
  const span = hi - lo, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
  const step = [1, 2, 2.5, 5, 10].map(m => m * mag).find(s => span / s <= n + 1) || mag * 10;
  const t0 = Math.floor(lo / step) * step, out = [];
  for (let v = t0; v <= hi + step * 0.5; v += step) out.push(+v.toFixed(10));
  return out;
}
function sliced() { return RANGE ? D.daily.slice(-RANGE) : D.daily; }

// ---------- status
function renderStatus() {
  const s = D.status || {};
  document.getElementById('meta').textContent = `数据到 ${D.daily.length ? D.daily[D.daily.length-1].date : '—'} · 页面生成 ${D.built} · 状态更新 ${s.updated || '—'}`;
  document.getElementById('tcount').textContent = s.triggers_count || '';
  document.getElementById('status-sub').textContent = s.updated_by || '';
  const chip = x => `<div class="chip ${x.state}"><div class="dot" role="img" aria-label="${x.state}"></div><div><div class="t">${esc(x.id||'')} ${esc(x.name)}<span class="state">${({green:'绿',yellow:'黄',red:'红'})[x.state]||x.state}</span></div><div class="n">${esc(x.note||'')}</div></div></div>`;
  document.getElementById('triggers').innerHTML = (s.triggers||[]).map(chip).join('');
  document.getElementById('leading').innerHTML = (s.leading||[]).map(chip).join('');
  document.getElementById('ladder').textContent = s.ladder_if_yellow || '';
  document.getElementById('notes').innerHTML = (s.notes||[]).map(n => `<li>${esc(n)}</li>`).join('');
}

// ---------- tiles
function spark(vals, color) {
  const w = 120, h = 28, xs = vals.filter(v => v != null);
  if (xs.length < 2) return '';
  const lo = Math.min(...xs), hi = Math.max(...xs), n = vals.length;
  const pts = vals.map((v, i) => v == null ? null : [(i/(n-1))*w, h - ((v-lo)/((hi-lo)||1))*(h-4) - 2]).filter(Boolean);
  const d = pts.map((p,i)=> (i?'L':'M')+p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' ');
  const last = pts[pts.length-1];
  return `<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" aria-hidden="true"><path d="${d}" fill="none" stroke="${color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" opacity=".55"/><circle cx="${last[0]}" cy="${last[1]}" r="3.5" fill="${color}" stroke="var(--surface)" stroke-width="2"/></svg>`;
}
function renderTiles() {
  const rows = D.daily.slice(-30);
  document.getElementById('tiles').innerHTML = D.tiles.map(t => {
    const vals = rows.map(r => r[t.col]); const cur = [...vals].reverse().find(v => v != null);
    const prevIdx = vals.lastIndexOf(cur); let prev = null; for (let i = prevIdx-1; i >= 0; i--) if (vals[i] != null) { prev = vals[i]; break; }
    const pct = (cur != null && prev) ? (cur/prev - 1)*100 : null;
    const good = pct == null ? '' : ((pct >= 0) !== t.upBad ? 'up' : 'down');
    return `<div class="tile"><div class="label">${esc(t.label)}</div><div class="value">${fmtN(cur, t.fmt)}</div><div class="delta ${good}">${pct == null ? '—' : (pct>=0?'+':'')+pct.toFixed(2)+'% vs 上一数据日'}</div>${spark(vals, css('--s1'))}</div>`;
  }).join('');
}

// ---------- line charts
function lineChart(el, cfg) {
  const rows = sliced();
  let series = cfg.series.map((s, i) => ({ name: s.name, col: s.col, color: css(SERIES[i % 8]), vals: rows.map(r => r[s.col] ?? null) }))
                         .filter(s => s.vals.some(v => v != null));
  if (cfg.index100) series = series.map(s => { const base = s.vals.find(v => v != null); return { ...s, vals: s.vals.map(v => v == null ? null : v / base * 100) }; });
  const W = 560, H = 230, P = { l: 44, r: 90, t: 10, b: 28 };
  const xs = rows.map(r => r.date), n = xs.length;
  const all = series.flatMap(s => s.vals).filter(v => v != null);
  if (!all.length || n < 2) { el.innerHTML = `<h2>${esc(cfg.title)}</h2><div class="sub">${esc(cfg.sub)}</div><div class="sub">暂无数据（源未返回或日更还没积累）</div>`; return; }
  const ticks = niceTicks(Math.min(...all), Math.max(...all)); const lo = ticks[0], hi = ticks[ticks.length-1];
  const X = i => P.l + (i/(n-1))*(W-P.l-P.r), Y = v => P.t + (1-(v-lo)/((hi-lo)||1))*(H-P.t-P.b);
  let g = `<g class="axis">`;
  ticks.forEach(t => { g += `<line class="grid-line" x1="${P.l}" x2="${W-P.r}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${P.l-6}" y="${Y(t)+4}" text-anchor="end">${fmtN(t, cfg.fmt==='$'?'':cfg.fmt)}</text>`; });
  const xt = [...new Set([0, Math.round(n*0.25), Math.round(n*0.5), Math.round(n*0.75), n-1])];
  xt.forEach(i => { g += `<text x="${X(i)}" y="${H-8}" text-anchor="middle">${xs[i].slice(5)}</text>`; });
  g += `<line class="baseline" x1="${P.l}" x2="${W-P.r}" y1="${H-P.b}" y2="${H-P.b}"/></g>`;
  let paths = '', ends = '';
  const labelSlots = series.slice(0, 4).map(s => s.name);
  const endLabels = [];
  series.forEach(s => {
    let d = '', pen = false;
    s.vals.forEach((v, i) => { if (v == null) { pen = false; return; } d += (pen ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1) + ' '; pen = true; });
    paths += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
    let li = s.vals.length-1; while (li >= 0 && s.vals[li] == null) li--;
    if (li >= 0) { ends += `<circle cx="${X(li)}" cy="${Y(s.vals[li])}" r="4" fill="${s.color}" stroke="var(--surface)" stroke-width="2"/>`;
      if (labelSlots.includes(s.name)) endLabels.push({ y: Y(s.vals[li]), x: X(li), text: `${s.name} ${fmtN(s.vals[li], cfg.fmt)}`, color: s.color }); }
  });
  endLabels.sort((a,b)=>a.y-b.y); for (let i = 1; i < endLabels.length; i++) if (endLabels[i].y - endLabels[i-1].y < 13) endLabels[i].y = endLabels[i-1].y + 13;
  const labels = endLabels.map(l => `<line x1="${l.x+5}" x2="${W-P.r+8}" y1="${l.y}" y2="${l.y}" stroke="${l.color}" stroke-width="1" opacity=".6"/><text class="lbl" x="${W-P.r+11}" y="${l.y+4}">${esc(l.text)}</text>`).join('');
  const legend = series.length > 1 ? `<div class="legend">${series.map(s => `<span><span class="k" style="background:${s.color}"></span>${esc(s.name)}</span>`).join('')}</div>` : '';
  const table = `<div class="tbl"><table><thead><tr><th>日期</th>${series.map(s=>`<th>${esc(s.name)}</th>`).join('')}</tr></thead><tbody>${rows.map((r,i)=>`<tr><td>${r.date}</td>${series.map(s=>`<td>${fmtN(s.vals[i], cfg.fmt)}</td>`).join('')}</tr>`).reverse().join('')}</tbody></table></div>`;
  el.innerHTML = `<div class="chart"><button class="btn toggle" aria-pressed="false">表格</button><h2>${esc(cfg.title)}</h2><div class="sub">${esc(cfg.sub)}</div>${legend}
    <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(cfg.title)}">${g}${paths}${ends}${labels}<line class="xh" x1="0" x2="0" y1="${P.t}" y2="${H-P.b}" stroke="var(--axis)" stroke-width="1" style="display:none"/><rect class="hit" x="${P.l}" y="${P.t}" width="${W-P.l-P.r}" height="${H-P.t-P.b}" fill="transparent"/></svg><div class="tip"></div>${table}</div>`;
  const svg = el.querySelector('svg'), tip = el.querySelector('.tip'), xh = el.querySelector('.xh'), chart = el.querySelector('.chart');
  el.querySelector('.toggle').onclick = e => { const on = chart.classList.toggle('table'); e.target.setAttribute('aria-pressed', on); };
  svg.addEventListener('mousemove', ev => {
    const r = svg.getBoundingClientRect(), px = (ev.clientX - r.left) / r.width * W;
    const i = Math.max(0, Math.min(n-1, Math.round((px - P.l) / (W-P.l-P.r) * (n-1))));
    xh.setAttribute('x1', X(i)); xh.setAttribute('x2', X(i)); xh.style.display = '';
    tip.style.display = 'block';
    tip.innerHTML = `<div class="d">${xs[i]}</div>` + series.map(s => `<div class="r"><span class="n" style="--c:${s.color}">${esc(s.name)}</span><span>${fmtN(s.vals[i], cfg.fmt)}</span></div>`).join('');
    const left = (ev.clientX - r.left) + 14, flip = left + 160 > r.width;
    tip.style.left = (flip ? (ev.clientX - r.left) - 170 : left) + 'px'; tip.style.top = Math.max(0, (ev.clientY - r.top) - 10) + 'px';
  });
  svg.addEventListener('mouseleave', () => { tip.style.display = 'none'; xh.style.display = 'none'; });
}
function renderLines() {
  const host = document.getElementById('lines'); host.innerHTML = '';
  D.lines.forEach(cfg => { const el = document.createElement('section'); el.className = 'card'; host.appendChild(el); lineChart(el, cfg); });
}

// ---------- quarterly
function qPrev(p) { const [y, m] = p.split('-').map(Number); const pm = m - 3; return pm > 0 ? `${y}-${String(pm).padStart(2,'0')}` : `${y-1}-${String(pm+12).padStart(2,'0')}`; }
function columns(pts, opts) {
  const W = 300, H = 150, P = { l: 40, r: 10, t: 16, b: 24 }, n = pts.length;
  const vals = pts.map(p => p.v), lo0 = Math.min(0, ...vals), hi0 = Math.max(0, ...vals);
  const ticks = niceTicks(lo0, hi0, 3), lo = ticks[0], hi = ticks[ticks.length-1];
  const Y = v => P.t + (1-(v-lo)/((hi-lo)||1))*(H-P.t-P.b), band = (W-P.l-P.r)/Math.max(n,1), bw = Math.min(24, band*0.6);
  let g = '<g class="axis">';
  ticks.forEach(t => { g += `<line class="grid-line" x1="${P.l}" x2="${W-P.r}" y1="${Y(t)}" y2="${Y(t)}"/><text x="${P.l-5}" y="${Y(t)+4}" text-anchor="end">${fmtN(t, opts.fmt)}</text>`; });
  g += `<line class="baseline" x1="${P.l}" x2="${W-P.r}" y1="${Y(0)}" y2="${Y(0)}"/></g>`;
  let bars = '', labels = '';
  const maxI = vals.indexOf(Math.max(...vals)), minI = vals.indexOf(Math.min(...vals));
  pts.forEach((p, i) => {
    const x = P.l + band*i + (band-bw)/2, y0 = Y(0), y1 = Y(p.v), top = Math.min(y0, y1), h = Math.abs(y0-y1);
    const color = opts.diverging ? (p.v >= 0 ? css('--s1') : css('--s8')) : css('--s1');
    const r = Math.min(4, h); // 4px 圆角在数据端，基线端直角
    const path = p.v >= 0
      ? `M${x} ${y0} V${top + r} Q${x} ${top} ${x+r} ${top} H${x+bw-r} Q${x+bw} ${top} ${x+bw} ${top+r} V${y0} Z`
      : `M${x} ${y0} V${y0+h-r} Q${x} ${y0+h} ${x+r} ${y0+h} H${x+bw-r} Q${x+bw} ${y0+h} ${x+bw} ${y0+h-r} V${y0} Z`;
    bars += `<path d="${path}" fill="${color}"><title>${p.label}: ${fmtN(p.v, opts.fmt)}</title></path>`;
    g += `<text class="axis" x="${x+bw/2}" y="${H-7}" text-anchor="middle" style="fill:var(--muted);font-size:10.5px">${p.label}</text>`;
    if (i === n-1 || i === maxI || i === minI) labels += `<text class="lbl" x="${x+bw/2}" y="${p.v >= 0 ? top-4 : y0+h+11}" text-anchor="middle">${fmtN(p.v, opts.fmt)}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.title)}">${g}${bars}${labels}</svg>`;
}
function renderQuarterly() {
  const host = document.getElementById('quarterly'); host.innerHTML = '';
  D.qmeta.forEach(m => {
    const pts = (D.quarterly[m.key] || []); if (!pts.length) return;
    const unit = pts[0].unit, fmt = unit.startsWith('$') && !unit.includes('/') ? '' : (unit === '%' ? '%' : '');
    const level = pts.map(p => ({ label: p.period.slice(2,7).replace('-','/'), v: p.value }));
    const byP = Object.fromEntries(pts.map(p => [p.period.slice(0,7), p.value]));
    const growth = pts.filter(p => byP[qPrev(p.period.slice(0,7))] != null && byP[qPrev(p.period.slice(0,7))] !== 0)
                      .map(p => ({ label: p.period.slice(2,7).replace('-','/'), v: (p.value / byP[qPrev(p.period.slice(0,7))] - 1) * 100 }));
    const el = document.createElement('div'); el.className = 'card'; el.style.padding = '10px 12px';
    el.innerHTML = `<h2>${esc(m.title)}</h2><div class="sub">${esc(m.sub)}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><div><div class="sub">水平（${esc(unit)}）</div>${columns(level, {fmt, title: m.title})}</div>
      <div><div class="sub">环比增速 %</div>${growth.length ? columns(growth, {fmt:'%', diverging:true, title: m.title+' 环比'}) : '<div class="sub">不足两个连续季度</div>'}</div></div>
      <details><summary class="sub" style="cursor:pointer">表格 / 来源</summary><div class="tbl" style="display:block"><table><thead><tr><th>期末</th><th>值</th><th>来源</th></tr></thead><tbody>${pts.map(p=>`<tr><td>${p.period}</td><td>${p.value}</td><td style="text-align:left;color:var(--ink2)">${esc(p.source)}</td></tr>`).join('')}</tbody></table></div></details>`;
    host.appendChild(el);
  });
}

// ---------- wiring
function renderAll() { renderStatus(); renderTiles(); renderLines(); renderQuarterly(); }
document.querySelectorAll('[data-range]').forEach(b => b.onclick = () => { RANGE = +b.dataset.range; document.querySelectorAll('[data-range]').forEach(x => x.setAttribute('aria-pressed', x === b)); renderLines(); });
document.getElementById('theme').onclick = () => {
  const r = document.documentElement, cur = r.getAttribute('data-theme');
  const osDark = matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = cur ? cur === 'dark' : osDark;
  r.setAttribute('data-theme', isDark ? 'light' : 'dark'); try { localStorage.setItem('dash-theme', r.getAttribute('data-theme')); } catch (e) {}
  renderAll();
};
try { const t = localStorage.getItem('dash-theme'); if (t) document.documentElement.setAttribute('data-theme', t); } catch (e) {}
renderAll();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    print(build())

#!/usr/bin/env python3
"""一手源抓取：绕开转述，直接拉监管/政府/预测市场的原始数据。

用法：
    .venv/bin/python scripts/fetch_primary.py SPCX
    .venv/bin/python scripts/fetch_primary.py SPCX RKLB TSLA --quarters 8
    .venv/bin/python scripts/fetch_primary.py SPCX --only xbrl,edgar      # 只跑部分源
    .venv/bin/python scripts/fetch_primary.py SPCX --json                 # 另存原始 JSON

输出：data/primary/<TICKER>.md（覆盖），--json 时另存 data/primary/<TICKER>.json

五个源（全部免费、全部本机直连、不经任何第三方托管）：
  xbrl        SEC XBRL companyfacts —— 10-Q/10-K 机读科目值，按季度拆出单季数
  edgar       EDGAR 公司申报 atom —— 最近的 Form 4 / 144 / 13G / 8-K / 10-Q，谁在卖、什么时候报
  usaspending USAspending.gov —— 联邦合同按收款人，金额/机构/日期
  polymarket  Polymarket gamma API —— 与 ticker 关键词相关的盘口
  kalshi      Kalshi 公开 API —— 同上

设计约束：
  * 只用标准库（urllib/json），不依赖 yfinance 之类会挂的东西。
  * SEC 要求 User-Agent 带联系方式，见 SEC_UA；连续请求间隔 ≥0.15s。
  * 每个源独立 try/except，一个挂了不影响其他源，错误写进输出文件而不是吞掉。
  * 数字一律原样落盘 + 单位标注，不做任何「调整」；加减法留给读的人。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "primary"

SEC_UA = "Will Song superwill313@gmail.com"
GENERIC_UA = "Mozilla/5.0 (investment-research fetch_primary.py)"
TIMEOUT = 40

# ticker -> 补充信息。CIK 优先从 SEC company_tickers.json 自动解析，这里只放解析不到或要覆盖的。
# usaspending: 收款人检索词（USAspending 按法人名模糊匹配，和 ticker 无关）
# keywords: 预测市场检索词
OVERRIDES: dict[str, dict] = {
    "SPCX": {
        "usaspending": ["SPACE EXPLORATION TECHNOLOGIES"],
        "keywords": ["spacex", "starlink", "starship"],
    },
    "RKLB": {
        "usaspending": ["ROCKET LAB"],
        "keywords": ["rocket lab", "neutron"],
    },
    "TSLA": {
        "usaspending": ["TESLA"],
        "keywords": ["tesla", "robotaxi", "cybercab"],
    },
    "NVDA": {"keywords": ["nvidia"]},
    "GOOGL": {"usaspending": ["GOOGLE"], "keywords": ["google", "alphabet", "gemini"]},
    "META": {"keywords": ["meta ", "llama"]},
    "AMZN": {"usaspending": ["AMAZON WEB SERVICES", "AMAZON.COM"], "keywords": ["amazon", "kuiper"]},
    "CRWV": {"keywords": ["coreweave"]},
    "PLTR": {"usaspending": ["PALANTIR"], "keywords": ["palantir"]},
    "CRCL": {"keywords": ["circle", "usdc"]},
}

# XBRL 科目：优先级列表，命中第一个有数据的就用（公司之间 tag 不统一）
XBRL_CONCEPTS: list[tuple[str, list[str]]] = [
    ("收入", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "SalesRevenueNet"]),
    ("毛利", ["GrossProfit"]),
    ("经营利润", ["OperatingIncomeLoss"]),
    ("净利润", ["NetIncomeLoss", "ProfitLoss"]),
    ("经营现金流", ["NetCashProvidedByUsedInOperatingActivities"]),
    ("资本开支", ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets"]),
    ("现金及等价物", ["CashAndCashEquivalentsAtCarryingValue"]),
    ("长期债务", ["LongTermDebt", "LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations"]),
    ("总债务(含流动)", ["DebtCurrent", "LongTermDebtCurrent"]),
    ("股份数", ["CommonStockSharesOutstanding", "WeightedAverageNumberOfDilutedSharesOutstanding"]),
    ("股权激励费用", ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]),
]

FLOW_CONCEPTS = {"收入", "毛利", "经营利润", "净利润", "经营现金流", "资本开支", "股权激励费用"}


# ---------------------------------------------------------------- http helpers
def _get(url: str, ua: str = GENERIC_UA, data: bytes | None = None, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": ua, **(headers or {})})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _get_json(url: str, **kw) -> dict | list:
    return json.loads(_get(url, **kw).decode("utf-8"))


def _post_json(url: str, payload: dict, ua: str = GENERIC_UA) -> dict:
    body = json.dumps(payload).encode("utf-8")
    return json.loads(_get(url, ua=ua, data=body, headers={"Content-Type": "application/json"}).decode("utf-8"))


def _fmt_money(v: float | int | None, unit: str = "USD") -> str:
    if v is None:
        return "—"
    if unit == "USD":
        a = abs(v)
        if a >= 1e9:
            return f"${v/1e9:,.2f}B"
        if a >= 1e6:
            return f"${v/1e6:,.1f}M"
        return f"${v:,.0f}"
    if unit == "shares":
        return f"{v/1e6:,.1f}M 股"
    return f"{v:,}"


# ---------------------------------------------------------------- SEC: ticker -> CIK
_CIK_CACHE: dict[str, tuple[str, str]] | None = None


def resolve_cik(ticker: str) -> tuple[str, str]:
    """返回 (CIK 10 位零填充, 公司名)。"""
    global _CIK_CACHE
    if _CIK_CACHE is None:
        raw = _get_json("https://www.sec.gov/files/company_tickers.json", ua=SEC_UA)
        _CIK_CACHE = {}
        for row in raw.values():
            _CIK_CACHE[row["ticker"].upper()] = (f"{int(row['cik_str']):010d}", row["title"])
    t = ticker.upper().replace("-", "")
    if t in _CIK_CACHE:
        return _CIK_CACHE[t]
    # BRK-B 之类
    for k, v in _CIK_CACHE.items():
        if k.replace("-", "") == t:
            return v
    raise KeyError(f"SEC company_tickers.json 里找不到 {ticker}")


# ---------------------------------------------------------------- source 1: XBRL
def _dedupe_latest(entries: list[dict]) -> list[dict]:
    """同一 (end, fp, fy) 可能有多份申报（原报/重述），取 filed 最新。"""
    best: dict[tuple, dict] = {}
    for e in entries:
        key = (e.get("start"), e.get("end"), e.get("fy"), e.get("fp"))
        if key not in best or e.get("filed", "") > best[key].get("filed", ""):
            best[key] = e
    return sorted(best.values(), key=lambda e: (e.get("end", ""), e.get("start", ""), e.get("filed", "")))


def _quarterize(entries: list[dict]) -> list[dict]:
    """流量科目：10-Q 的 Q2/Q3 常是年初至今口径（start 到 end 跨多季）。
    用「本期 YTD − 上期 YTD」拆出单季；Q4 = FY − Q3 YTD。
    返回 [{end, fy, fp, val, derived: bool}]，derived=True 表示是减出来的。"""
    out = []
    by_end = {}
    for e in entries:
        start, end = e.get("start"), e.get("end")
        if not start or not end:
            continue
        days = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
        e = dict(e, days=days)
        by_end.setdefault(end, []).append(e)
    for end, group in sorted(by_end.items()):
        # 同一 end 下：单季口径（~90 天）优先；否则用 YTD 减去同 fy 的上一 YTD
        q = [g for g in group if 80 <= g["days"] <= 100]
        if q:
            g = q[-1]
            out.append({"end": end, "fy": g.get("fy"), "fp": g.get("fp"), "val": g["val"], "derived": False, "form": g.get("form"), "basis": "Q"})
            continue
        ytd = [g for g in group if g["days"] > 100]
        if not ytd:
            continue
        g = ytd[-1]
        # 找同一 fy、更早 end 的 YTD
        prev = [p for grp in by_end.values() for p in grp
                if p["end"] < end and p.get("start") == g.get("start")]
        if prev:
            p = sorted(prev, key=lambda x: x["end"])[-1]
            out.append({"end": end, "fy": g.get("fy"), "fp": g.get("fp"), "val": g["val"] - p["val"], "derived": True, "form": g.get("form"), "basis": "Q"})
        elif g["days"] <= 200:
            # 半年 YTD 但找不到 Q1：标注，不拆
            out.append({"end": end, "fy": g.get("fy"), "fp": str(g.get("fp")) + "(YTD)", "val": g["val"], "derived": False, "form": g.get("form"), "basis": "YTD"})
        else:
            out.append({"end": end, "fy": g.get("fy"), "fp": "FY", "val": g["val"], "derived": False, "form": g.get("form"), "basis": "FY"})
    return out


def fetch_xbrl(cik: str, quarters: int) -> dict:
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    data = _get_json(url, ua=SEC_UA)
    facts = data.get("facts", {}).get("us-gaap", {})
    result: dict[str, dict] = {"_meta": {"url": url, "entityName": data.get("entityName"), "tags": len(facts)}}
    for label, tags in XBRL_CONCEPTS:
        for tag in tags:
            if tag not in facts:
                continue
            units = facts[tag]["units"]
            unit = "USD" if "USD" in units else ("shares" if "shares" in units else next(iter(units)))
            entries = _dedupe_latest([e for e in units[unit] if e.get("form") in ("10-Q", "10-K", "10-Q/A", "10-K/A", "S-1", "S-1/A", "20-F", "6-K")])
            if not entries:
                continue
            if label in FLOW_CONCEPTS:
                rows = _quarterize(entries)
            else:
                rows = [{"end": e["end"], "fy": e.get("fy"), "fp": e.get("fp"), "val": e["val"], "derived": False, "form": e.get("form")}
                        for e in entries if e.get("fp")]
            result[label] = {"tag": tag, "unit": unit, "rows": rows[-quarters:]}
            break
    return result


# ---------------------------------------------------------------- source 2: EDGAR filings
def fetch_edgar(cik: str, count: int = 40) -> list[dict]:
    url = ("https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany"
           f"&CIK={cik}&type=&dateb=&owner=include&count={count}&output=atom")
    xml = _get(url, ua=SEC_UA)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    out = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        updated = (entry.findtext("a:updated", default="", namespaces=ns) or "")[:10]
        link = entry.find("a:link", ns)
        href = link.get("href") if link is not None else ""
        form = re.sub(r"\s*\[Amend\]", "", title.split(" - ", 1)[0]).strip()
        out.append({"form": form, "title": re.sub(r"\s+", " ", title), "date": updated, "url": href})
    return out


# ---------------------------------------------------------------- source 3: USAspending
def fetch_usaspending(names: list[str], fy_start: str, fy_end: str, limit: int = 15) -> dict:
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    payload = {
        "filters": {
            "recipient_search_text": names,
            "time_period": [{"start_date": fy_start, "end_date": fy_end}],
            "award_type_codes": ["A", "B", "C", "D"],  # 合同类
        },
        "fields": ["Award ID", "Recipient Name", "Award Amount", "Total Outlays", "Awarding Agency",
                   "Awarding Sub Agency", "Start Date", "End Date", "Description"],
        "limit": limit, "page": 1, "sort": "Award Amount", "order": "desc",
    }
    data = _post_json(url, payload)
    rows = data.get("results", [])
    total = sum((r.get("Award Amount") or 0) for r in rows)
    return {"query": names, "window": [fy_start, fy_end], "rows": rows, "top_n_total": total,
            "note": "Award Amount = 合同上限/义务额，不是当期收入；Total Outlays = 已实际支付"}


# ---------------------------------------------------------------- source 4/5: prediction markets
def fetch_polymarket(keywords: list[str], limit: int = 12) -> list[dict]:
    """gamma 的 public-search 端点按关键词全文检索事件（含嵌套 markets）。"""
    out, seen = [], set()
    for kw in keywords:
        q = urllib.parse.urlencode({"q": kw.strip(), "limit_per_type": 10})
        url = "https://gamma-api.polymarket.com/public-search?" + q
        data = None
        for attempt in range(2):  # 这个端点慢且偶发超时，单独放宽到 90s 并重试一次
            try:
                req = urllib.request.Request(url, headers={"User-Agent": GENERIC_UA})
                with urllib.request.urlopen(req, timeout=90) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except Exception as e:  # noqa: BLE001
                if attempt == 1:
                    print(f"    polymarket[{kw}] 跳过: {e!r}"[:120])
        if not data:
            continue
        for ev in data.get("events", []):
            if ev.get("closed") or ev.get("id") in seen:
                continue
            seen.add(ev.get("id"))
            mkts = []
            for m in ev.get("markets", [])[:8]:
                if m.get("closed"):
                    continue
                try:
                    prices = json.loads(m.get("outcomePrices", "[]"))
                    outcomes = json.loads(m.get("outcomes", "[]"))
                except Exception:  # noqa: BLE001
                    prices, outcomes = [], []
                mkts.append({"question": m.get("question"), "outcomes": dict(zip(outcomes, prices)),
                             "volume": m.get("volumeNum"), "liquidity": m.get("liquidityNum")})
            out.append({"title": ev.get("title", ""), "slug": ev.get("slug"), "end": (ev.get("endDate") or "")[:10],
                        "volume": ev.get("volume"), "liquidity": ev.get("liquidity"), "markets": mkts})
        time.sleep(0.2)
    out.sort(key=lambda e: -(float(e.get("volume") or 0)))
    return out[:limit]


def fetch_kalshi(keywords: list[str], limit: int = 12) -> list[dict]:
    """events 端点不支持全文；拉开放事件池（最多 800 个）一次本地过滤，再按事件取 markets 拿价格。"""
    base = "https://api.elections.kalshi.com/trade-api/v2"
    kws = [k.lower() for k in keywords]
    matched: list[dict] = []
    cursor, pages = "", 0
    while pages < 4:
        q = urllib.parse.urlencode({"status": "open", "limit": 200, "cursor": cursor})
        data = _get_json(f"{base}/events?{q}")
        for ev in data.get("events", []):
            if any(k in ev.get("title", "").lower() for k in kws):
                matched.append(ev)
        cursor = data.get("cursor") or ""
        pages += 1
        if not cursor:
            break
    out = []
    for ev in matched[:limit]:
        try:
            q = urllib.parse.urlencode({"event_ticker": ev["event_ticker"], "limit": 8})
            ms = _get_json(f"{base}/markets?{q}").get("markets", [])
        except Exception:  # noqa: BLE001
            ms = []
        def _c(v):  # "0.6700" dollars -> 67 (cents)
            try:
                return round(float(v) * 100)
            except (TypeError, ValueError):
                return None
        mkts = [{"ticker": m.get("ticker"), "subtitle": m.get("yes_sub_title") or m.get("subtitle") or m.get("title"),
                 "yes_bid": _c(m.get("yes_bid_dollars")), "yes_ask": _c(m.get("yes_ask_dollars")),
                 "last": _c(m.get("last_price_dollars")),
                 "volume": round(float(m.get("volume_fp") or 0)), "oi": round(float(m.get("open_interest_fp") or 0)),
                 "close": (m.get("close_time") or "")[:10]}
                for m in ms]
        out.append({"title": ev.get("title"), "event_ticker": ev["event_ticker"], "category": ev.get("category"), "markets": mkts})
    return out


# ---------------------------------------------------------------- render
def render_md(ticker: str, cik: str, name: str, res: dict, errors: dict, quarters: int) -> str:
    today = date.today().isoformat()
    L = [f"# {ticker} 一手数据 · {today}", "",
         f"> 公司：{name} · CIK {cik} · 生成：`scripts/fetch_primary.py`。",
         "> 数字原样落盘，不调整；流量科目标 `△` 的是「本期 YTD − 上期 YTD」拆出的单季，查原件时注意。", ""]
    if errors:
        L += ["## ⚠️ 抓取失败的源", ""] + [f"- **{k}**：`{v}`" for k, v in errors.items()] + [""]

    # XBRL
    x = res.get("xbrl")
    if x:
        meta = x.pop("_meta", {})
        L += [f"## 一、SEC XBRL 财务（{meta.get('tags')} 个科目可用）", "",
              f"源：{meta.get('url')}", ""]
        # 收集所有期
        ends = sorted({r["end"] for v in x.values() for r in v["rows"]})[-quarters:]
        L.append("| 科目 | " + " | ".join(ends) + " |")
        L.append("|---|" + "---|" * len(ends))
        for label, v in x.items():
            by_end = {r["end"]: r for r in v["rows"]}
            cells = []
            for e in ends:
                r = by_end.get(e)
                if not r:
                    cells.append("—")
                    continue
                s = _fmt_money(r["val"], v["unit"])
                if r.get("derived"):
                    s += " △"
                if str(r.get("fp", "")).endswith("(YTD)"):
                    s += " (YTD)"
                cells.append(s)
            L.append(f"| {label} `{v['tag']}` | " + " | ".join(cells) + " |")
        L.append("")
        # 自动算两个比值，标 COMPUTED
        def _series(label):
            return {r["end"]: r for r in x.get(label, {}).get("rows", [])}
        rev, ocf, capex, ni = _series("收入"), _series("经营现金流"), _series("资本开支"), _series("净利润")
        calc = []
        for e in ends:
            if e not in ocf or e not in capex:
                continue
            basis = ocf[e].get("basis")
            if basis != capex[e].get("basis"):
                continue
            tag = "" if basis == "Q" else f"（{basis} 口径）"
            fcf = ocf[e]["val"] - abs(capex[e]["val"])
            line = f"- {e}{tag}：FCF = OCF − capex = {_fmt_money(fcf)}"
            if e in ni and ni[e].get("basis") == basis:
                line += f"；净利 {_fmt_money(ni[e]['val'])} → FCF−净利 = {_fmt_money(fcf - ni[e]['val'])}"
            if e in rev and rev[e].get("basis") == basis and rev[e]["val"]:
                line += f"；capex/收入 = {abs(capex[e]['val'])/rev[e]['val']*100:.0f}%"
            calc.append(line)
        if calc:
            L += ["**[COMPUTED] 现金流 vs 利润**（信号⑥读数；capex 取绝对值）", ""] + calc + [""]

    # EDGAR
    ed = res.get("edgar")
    if ed:
        L += ["## 二、EDGAR 最近申报（谁在报什么）", ""]
        counts: dict[str, int] = {}
        for f in ed:
            counts[f["form"]] = counts.get(f["form"], 0) + 1
        L.append("表单计数：" + "、".join(f"{k}×{v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1])))
        L.append("")
        L.append("| 日期 | 表单 | 说明 | 链接 |")
        L.append("|---|---|---|---|")
        for f in ed[:25]:
            L.append(f"| {f['date']} | **{f['form']}** | {f['title'].split(' - ',1)[-1][:60]} | [index]({f['url']}) |")
        L += ["", "读法：Form 4 = 内部人已成交；144 = 内部人**拟**出售申报（受限股，先报后卖）；13G = 5% 以上被动持股；13D = 5% 以上主动持股；8-K = 重大事件（财报在这里）；S-8 = 员工股计划登记（稀释来源）。", ""]

    # USAspending
    us = res.get("usaspending")
    if us:
        L += [f"## 三、USAspending 联邦合同（检索：{', '.join(us['query'])}；窗口 {us['window'][0]} → {us['window'][1]}）", "",
              f"前 {len(us['rows'])} 笔合同上限合计 {_fmt_money(us['top_n_total'])}。{us['note']}。", "",
              "| 金额上限 | 已支付 | 机构 | 子机构 | 起 | 止 | 说明 |", "|---|---|---|---|---|---|---|"]
        for r in us["rows"]:
            L.append(f"| {_fmt_money(r.get('Award Amount'))} | {_fmt_money(r.get('Total Outlays'))} | {r.get('Awarding Agency','')} | "
                     f"{(r.get('Awarding Sub Agency') or '')[:28]} | {r.get('Start Date','')} | {r.get('End Date','')} | {(r.get('Description') or '')[:70]} |")
        L.append("")

    # Prediction markets
    pm = res.get("polymarket")
    ks = res.get("kalshi")
    if pm is not None or ks is not None:
        L += ["## 四、预测市场", ""]
        if pm:
            L += ["### Polymarket", ""]
            for ev in pm:
                L.append(f"- **{ev['title']}**（到期 {ev['end']}，成交 {_fmt_money(ev.get('volume'))}，流动性 {_fmt_money(ev.get('liquidity'))}）")
                for m in ev["markets"]:
                    yes = m["outcomes"].get("Yes")
                    L.append(f"  - {m['question']} → Yes {float(yes)*100:.0f}%" if yes else f"  - {m['question']} → {m['outcomes']}")
            L.append("")
        elif pm == []:
            L += ["Polymarket：无匹配盘口。", ""]
        if ks:
            L += ["### Kalshi", ""]
            for ev in ks:
                L.append(f"- **{ev['title']}** `{ev['event_ticker']}`")
                for m in ev["markets"]:
                    L.append(f"  - {m['subtitle']}（{m['close']}）→ last {m['last']}¢ (bid {m['yes_bid']}/ask {m['yes_ask']}, vol {m['volume']}, OI {m['oi']})")
            L.append("")
        elif ks == []:
            L += ["Kalshi：无匹配盘口。", ""]
        L += ["盘口价是赔率不是事实；流动性 < $50k 的盘别当数据。", ""]

    L += ["---", "", "浏览器才能看的一手源（脚本抓不了）：",
          "- APNIC 各国用户估计：https://stats.labs.apnic.net/cgi-bin/aspop?as=14593 （Starlink AS14593）",
          "- Space-Track 轨道目录（免费注册）：https://www.space-track.org",
          "- FCC ICFS 卫星许可：https://licensing.fcc.gov/myibfs/ · FAA 商业发射许可：https://www.faa.gov/space/licenses",
          "- Cloudflare Radar（免费 token 后可接 API）：https://radar.cloudflare.com/as14593", ""]
    return "\n".join(L)


# ---------------------------------------------------------------- main
def run(ticker: str, quarters: int, only: set[str], save_json: bool, fy_start: str, fy_end: str) -> Path:
    ticker = ticker.upper()
    ov = OVERRIDES.get(ticker, {})
    res: dict = {}
    errors: dict = {}
    try:
        cik, name = resolve_cik(ticker)
    except Exception as e:  # noqa: BLE001
        cik, name = "", ticker
        errors["cik"] = repr(e)

    def step(key: str, fn, *args):
        if key not in only:
            return
        t0 = time.time()
        try:
            res[key] = fn(*args)
            print(f"  ✓ {key} ({time.time()-t0:.1f}s)")
        except Exception as e:  # noqa: BLE001
            errors[key] = repr(e)[:200]
            print(f"  ✗ {key}: {errors[key]}")
        time.sleep(0.2)

    print(f"== {ticker} ({name}, CIK {cik or '?'})")
    if cik:
        step("xbrl", fetch_xbrl, cik, quarters)
        step("edgar", fetch_edgar, cik)
    names = ov.get("usaspending") or [name.upper().replace(" INC.", "").replace(" CORP.", "").replace(" INC", "")]
    step("usaspending", fetch_usaspending, names, fy_start, fy_end)
    kws = ov.get("keywords") or [name.split()[0].lower()]
    step("polymarket", fetch_polymarket, kws)
    step("kalshi", fetch_kalshi, kws)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    md = OUT_DIR / f"{ticker}.md"
    md.write_text(render_md(ticker, cik, name, dict(res), errors, quarters), encoding="utf-8")
    if save_json:
        (OUT_DIR / f"{ticker}.json").write_text(json.dumps({"ticker": ticker, "cik": cik, "fetched": date.today().isoformat(),
                                                             "data": res, "errors": errors}, ensure_ascii=False, indent=1, default=str),
                                                 encoding="utf-8")
    return md


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tickers", nargs="+")
    ap.add_argument("--quarters", type=int, default=8, help="XBRL 保留最近几个期（默认 8）")
    ap.add_argument("--only", default="xbrl,edgar,usaspending,polymarket,kalshi", help="逗号分隔，只跑这些源")
    ap.add_argument("--json", action="store_true", help="另存原始 JSON")
    ap.add_argument("--fy-start", default="2021-10-01", help="USAspending 窗口起（默认 FY22 起；窗口过滤的是合同动作日期，金额是合同总义务额）")
    ap.add_argument("--fy-end", default=date.today().isoformat())
    a = ap.parse_args()
    only = {s.strip() for s in a.only.split(",") if s.strip()}
    rc = 0
    for t in a.tickers:
        try:
            p = run(t, a.quarters, only, a.json, a.fy_start, a.fy_end)
            print(f"  → {p.relative_to(ROOT)}")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {t} 整体失败: {e!r}")
            rc = 1
    return rc


if __name__ == "__main__":
    sys.exit(main())

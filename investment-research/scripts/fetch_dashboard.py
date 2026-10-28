#!/usr/bin/env python3
"""AI capex 周期看板 · 日更数据抓取（无钥匙、本机直连、纯标准库）。

用法：
    .venv/bin/python scripts/fetch_dashboard.py            # 抓今天一行 → data/dashboard/daily.csv，然后重建 site/dashboards/capex-cycle.html
    .venv/bin/python scripts/fetch_dashboard.py --no-build # 只抓不画
    .venv/bin/python scripts/fetch_dashboard.py --date 2026-10-20   # 指定日期（补录/覆盖）

每天跑一次（launchd 定时），同一天重复跑会覆盖当天那行。每个源独立 try/except，挂了留空不影响其它列。

源：
  Yahoo chart API   价格：SOXX SPY NVDA SPCX CRWV ORCL GOOGL；^VIX；CL=F（WTI）；^TNX/^FVX/^TYX（10Y/5Y/30Y 收益率）；HYG/LQD（信用代理）
  RunPod GraphQL    GPU 按需最低价 $/GPU·h：H100 SXM / H200 SXM / B200 / B300（=「算力现货」代理；SF Compute/Vast 挡爬虫，SemiAnalysis 付费）
  OpenRouter 榜单   前十模型 token 合计（T）——需求用量的公开周级代理
  Polymarket/Kalshi 几个与 Starship / SpaceX 相关的盘口概率
FRED 从本机不可达（http 000），利率改用 Yahoo 的 ^TNX 系列；HY OAS 用 HYG/LQD 比值代替。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "dashboard"
DAILY = DATA_DIR / "daily.csv"
UA = "Mozilla/5.0 (investment-research fetch_dashboard.py)"
TIMEOUT = 25

YAHOO = {
    "SOXX": "SOXX", "SPY": "SPY", "NVDA": "NVDA", "SPCX": "SPCX", "CRWV": "CRWV", "ORCL": "ORCL", "GOOGL": "GOOGL",
    "VIX": "^VIX", "WTI": "CL=F", "US10Y": "^TNX", "US5Y": "^FVX", "US30Y": "^TYX", "HYG": "HYG", "LQD": "LQD",
}
RUNPOD = {"H100_SXM": "H100 SXM", "H200_SXM": "H200 SXM", "B200": "B200", "B300": "B300"}
POLY = {  # 列名: (检索词, 题目里必须含的子串)
    "PM_STARSHIP_LT5_2026": ("spacex", "less than 5 spacex starship launches"),
    "PM_STARSHIP_REUSE_2027": ("spacex", "fully reusable before 2027"),
    "PM_TSLA_SPCX_MERGER_2027": ("spacex", "merger officially announced by december 31, 2027"),
}
KALSHI = {"KALSHI_MARS_2030": "KXSPACEXMARS-30"}


def _get(url: str, data: bytes | None = None, headers: dict | None = None, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception as e:  # noqa: BLE001
        # 本机 urllib 对个别站点（gamma-api.polymarket.com）会 SSL EOF，curl 能通；GET 退回 curl 再试一次
        if data is not None:
            raise
        import subprocess
        out = subprocess.run(["curl", "-s", "-m", str(timeout), "-A", UA, url], capture_output=True, timeout=timeout + 5)
        if out.returncode == 0 and out.stdout:
            return out.stdout
        raise e


def yahoo_meta(symbol: str) -> dict:
    q = urllib.parse.urlencode({"range": "5d", "interval": "1d"})
    d = json.loads(_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(symbol)}?{q}"))
    return d["chart"]["result"][0]["meta"]


def yahoo_price(symbol: str) -> float | None:
    return yahoo_meta(symbol).get("regularMarketPrice")


def us_trading_date() -> str:
    """行的日期 = SPY 最近一次常规交易的美东日期。北京早上跑，拿到的是前一晚美股收盘，行就该记在那一天。"""
    from datetime import datetime, timedelta, timezone
    m = yahoo_meta("SPY")
    ts = m.get("regularMarketTime")
    off = m.get("gmtoffset", -14400)
    return datetime.fromtimestamp(ts, timezone(timedelta(seconds=off))).date().isoformat()


def et_fallback_date() -> str:
    """Yahoo 拿不到时的退路：按美东时钟推最近一个已收盘的交易日（周末/16:00 前回退），绝不用本机北京日期——
    2026-10-26~28 三天曾因此把前一晚的收盘记到北京日期上，整列错位一天。"""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    now = datetime.now(ZoneInfo("America/New_York"))
    d = now.date() if now.hour >= 16 else now.date() - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.isoformat()


def runpod_prices() -> dict[str, float | None]:
    body = json.dumps({"query": "{ gpuTypes { displayName lowestPrice(input:{gpuCount:1}) { uninterruptablePrice } } }"}).encode()
    d = json.loads(_get("https://api.runpod.io/graphql", data=body, headers={"Content-Type": "application/json"}))
    by_name = {g["displayName"]: (g.get("lowestPrice") or {}).get("uninterruptablePrice") for g in d["data"]["gpuTypes"]}
    return {col: by_name.get(name) for col, name in RUNPOD.items()}


def openrouter_top10_tokens_T() -> float | None:
    h = _get("https://openrouter.ai/rankings", timeout=40).decode("utf-8", errors="ignore")
    figs = re.findall(r"([0-9.]+)([TBM]) tokens", h)
    if not figs:
        return None
    mult = {"T": 1.0, "B": 1e-3, "M": 1e-6}
    vals = sorted({round(float(v) * mult[u], 4) for v, u in figs}, reverse=True)
    return round(sum(vals[:10]), 2)


def polymarket_probs() -> dict[str, float | None]:
    out: dict[str, float | None] = {k: None for k in POLY}
    cache: dict[str, list] = {}
    for col, (kw, needle) in POLY.items():
        try:
            if kw not in cache:
                q = urllib.parse.urlencode({"q": kw, "limit_per_type": 20})
                cache[kw] = json.loads(_get("https://gamma-api.polymarket.com/public-search?" + q, timeout=90)).get("events", [])
            for ev in cache[kw]:
                for m in ev.get("markets", []):
                    if needle in (m.get("question") or "").lower() and not m.get("closed"):
                        prices = json.loads(m.get("outcomePrices", "[]"))
                        outcomes = json.loads(m.get("outcomes", "[]"))
                        yes = dict(zip(outcomes, prices)).get("Yes")
                        if yes is not None:
                            out[col] = round(float(yes) * 100, 1)
                            raise StopIteration
        except StopIteration:
            continue
        except Exception as e:  # noqa: BLE001
            print(f"  polymarket[{col}]: {e!r}"[:120])
    return out


def kalshi_probs() -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for col, event in KALSHI.items():
        try:
            q = urllib.parse.urlencode({"event_ticker": event, "limit": 1})
            ms = json.loads(_get(f"https://api.elections.kalshi.com/trade-api/v2/markets?{q}")).get("markets", [])
            out[col] = round(float(ms[0]["last_price_dollars"]) * 100, 1) if ms else None
        except Exception as e:  # noqa: BLE001
            print(f"  kalshi[{col}]: {e!r}"[:120]); out[col] = None
    return out


def fetch_row(day: str) -> dict:
    row: dict = {"date": day}

    def step(label, fn):
        t0 = time.time()
        try:
            v = fn(); row.update(v); print(f"  ✓ {label} ({time.time()-t0:.1f}s)")
        except Exception as e:  # noqa: BLE001
            print(f"  ✗ {label}: {e!r}"[:140])

    def yahoo_all():
        out = {}
        for col, sym in YAHOO.items():
            try:
                out[col] = yahoo_price(sym)
            except Exception as e:  # noqa: BLE001
                out[col] = None; print(f"    yahoo {sym}: {e!r}"[:100])
            time.sleep(0.3)
        return out

    step("yahoo", yahoo_all)
    step("runpod", runpod_prices)
    step("openrouter", lambda: {"OR_TOP10_TOKENS_T": openrouter_top10_tokens_T()})
    step("polymarket", polymarket_probs)
    step("kalshi", kalshi_probs)
    return row


def upsert(row: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows: dict[str, dict] = {}
    cols: list[str] = ["date"]
    if DAILY.exists():
        with DAILY.open(newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            cols = list(rd.fieldnames or ["date"])
            for r in rd:
                rows[r["date"]] = r
    for k in row:
        if k not in cols:
            cols.append(k)
    old = rows.get(row["date"], {})
    merged = {**old, **{k: ("" if v is None else v) for k, v in row.items()}}
    # 新抓为空、旧值有 → 保留旧值（源临时挂了别把历史擦掉）
    for k, v in old.items():
        if merged.get(k, "") == "" and v not in ("", None):
            merged[k] = v
    rows[row["date"]] = merged
    with DAILY.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for d in sorted(rows):
            w.writerow({c: rows[d].get(c, "") for c in cols})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default=None, help="行日期；默认 = SPY 最近常规交易日（美东），不是本机今天")
    ap.add_argument("--no-build", action="store_true")
    a = ap.parse_args()
    if not a.date:
        try:
            a.date = us_trading_date()
        except Exception as e:  # noqa: BLE001
            a.date = et_fallback_date()
            print(f"  us_trading_date 失败，按美东时钟推算: {e!r}"[:100], "->", a.date)
    print(f"== fetch_dashboard {a.date}")
    row = fetch_row(a.date)
    upsert(row)
    filled = sum(1 for k, v in row.items() if k != "date" and v not in (None, ""))
    print(f"  → {DAILY.relative_to(ROOT)}  ({filled} 个字段有值)")
    if not a.no_build:
        sys.path.insert(0, str(ROOT / "scripts"))
        import build_dashboard  # noqa: E402
        out = build_dashboard.build()
        print(f"  → {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

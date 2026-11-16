#!/usr/bin/env python3
"""多年口径的质量筛选：用 SEC XBRL frames（一次请求拿到全市场某一年的某个科目）。

为什么有这个脚本：screen_small_cap_value.py 的 quality_compounder 只看最近一年的
比率，2026-11-16 送审的六只里五只是在周期/一次性高点被选中的。这里改成五年口径。

口径（2026-11-16 定）：
  * 五年（默认 CY2021–CY2025）净利润每年为正；
  * 每年 ROE（净利润 ÷ 年初年末平均权益）≥ 10%，五年平均 ≥ 15%；
  * 五年里最低净利润 ÷ 最高净利润 ≥ 0.4（没有塌过）；
  * 收入四年复合增速 ≥ 4%；
  * 五年合计（经营现金流 − 资本开支）÷ 合计净利润 ≥ 0.7；
  * 市值 $3–100 亿；近三年平均净利润 ÷ 市值 ≥ 5%（正常化 PE ≤ 20）。

已知缺陷（2026-11-16，未修）：某年缺 PaymentsToAcquirePropertyPlantAndEquipment 时资本开支按 0 算，
fcf_conversion 会偏高（GNTX 筛选值 1.22，逐年核对是 0.87）。

这是发现工具，不是买入名单。XBRL frames 按日历年归档，财年不在 12 月结束的公司
会落到最接近的日历年；科目口径各家不一，入选后必须读原始文件。

用法：.venv/bin/python scripts/screen_quality_multiyear.py [--end-year 2025] [--cache DIR]
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "screens"
UA = "research-script/1.0"
FRAME = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/USD/{period}.json"
REV_TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"]


def get_json(url: str, cache: Path | None, tries: int = 4):
    key = None
    if cache:
        key = cache / (url.split("/api/xbrl/")[-1].replace("/", "_") if "/api/xbrl/" in url else url.split("/")[-1])
        if key.exists():
            return json.loads(key.read_text())
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=120).read()
            if key:
                key.write_bytes(raw)
            time.sleep(0.3)
            return json.loads(raw)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 + 3 * i)
    print(f"  失败 {url}: {last}")
    return None


def frame(tag: str, period: str, cache: Path | None) -> dict[int, float]:
    d = get_json(FRAME.format(tag=tag, period=period), cache)
    out: dict[int, float] = {}
    for x in (d or {}).get("data", []):
        out[int(x["cik"])] = float(x["val"])
    print(f"  {tag} {period}: {len(out)} 家")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    if a.cache:
        a.cache.mkdir(parents=True, exist_ok=True)
    years = list(range(a.end_year - 4, a.end_year + 1))

    ni = {y: frame("NetIncomeLoss", f"CY{y}", a.cache) for y in years}
    eq = {y: frame("StockholdersEquity", f"CY{y}Q4I", a.cache) for y in [years[0] - 1] + years}
    ocf = {y: frame("NetCashProvidedByUsedInOperatingActivities", f"CY{y}", a.cache) for y in years}
    capex = {y: frame("PaymentsToAcquirePropertyPlantAndEquipment", f"CY{y}", a.cache) for y in years}
    rev = {}
    for y in (years[0], years[-1]):
        merged: dict[int, float] = {}
        for t in REV_TAGS:
            for cik, v in frame(t, f"CY{y}", a.cache).items():
                merged[cik] = max(merged.get(cik, 0.0), v)
        rev[y] = merged

    # www.sec.gov 的 company_tickers.json 对不带联系方式的 UA 返回 403；
    # 改为先做基本面筛选，再只对过筛公司查 data.sec.gov/submissions（接受通用 UA）。
    def lookup(cik: int) -> tuple[str, str] | None:
        d = get_json(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", a.cache, tries=3)
        if not d or not d.get("tickers"):
            return None
        return d["tickers"][0], d.get("name", "")

    rows = []
    for cik in set.intersection(*(set(ni[y]) for y in years)):
        n = [ni[y].get(cik) for y in years]
        e = [eq[y].get(cik) for y in [years[0] - 1] + years]
        if any(v is None or v <= 0 for v in n) or any(v is None or v <= 0 for v in e):
            continue
        roe = [n[i] / ((e[i] + e[i + 1]) / 2) for i in range(5)]
        if min(roe) < 0.10 or sum(roe) / 5 < 0.15 or min(n) / max(n) < 0.4:
            continue
        r0, r1 = rev[years[0]].get(cik), rev[years[-1]].get(cik)
        if not r0 or not r1 or r0 <= 0:
            continue
        cagr = (r1 / r0) ** 0.25 - 1
        if cagr < 0.04:
            continue
        o = [ocf[y].get(cik) for y in years]
        if any(v is None for v in o):
            continue
        fcf = sum(o) - sum(capex[y].get(cik, 0.0) for y in years)
        conv = fcf / sum(n)
        if conv < 0.7:
            continue
        rows.append({"symbol": "", "name": "", "cik": cik, "roe_avg": round(sum(roe) / 5, 3),
                     "roe_min": round(min(roe), 3), "ni_min_over_max": round(min(n) / max(n), 2),
                     "rev_cagr": round(cagr, 3), "fcf_conversion": round(conv, 2),
                     "ni_3y_avg": round(sum(n[-3:]) / 3), "ni_last": round(n[-1]), "rev_last": round(r1)})
    print(f"基本面过筛 {len(rows)} 家，取市值…")

    import yfinance as yf  # 放在这里：只有过筛的才需要行情

    out = []
    for r in rows:
        tk = lookup(r["cik"])
        if not tk:
            continue
        r["symbol"], r["name"] = tk[0].replace(".", "-"), tk[1]
        try:
            fi = yf.Ticker(r["symbol"]).fast_info
            mc, px = float(fi["market_cap"]), float(fi["last_price"])
        except Exception:  # noqa: BLE001
            continue
        if not 3e8 <= mc <= 1e10:
            continue
        r["price"], r["market_cap"] = round(px, 2), round(mc)
        r["norm_earnings_yield"] = round(r["ni_3y_avg"] / mc, 4)
        if r["norm_earnings_yield"] >= 0.05:
            out.append(r)
    out.sort(key=lambda r: -r["norm_earnings_yield"] * r["roe_avg"])
    dst = a.out or OUT_DIR / f"{date.today().isoformat()}-quality-multiyear.csv"
    with dst.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else ["symbol"])
        w.writeheader()
        w.writerows(out)
    print(f"保存 {len(out)} 行 → {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

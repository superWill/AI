#!/usr/bin/env python3
"""Fetch comparable fundamentals for a manually selected value shortlist.

Usage:
    .venv/bin/python scripts/enrich_value_shortlist.py AXR SHOE BBW FOR ETD
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import date
from pathlib import Path
from typing import Any

import yfinance as yf


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "screens"
FIELDS = [
    "symbol",
    "name",
    "price",
    "market_cap",
    "enterprise_value",
    "total_cash",
    "total_debt",
    "revenue_ttm",
    "ebitda_ttm",
    "operating_cashflow_ttm",
    "free_cashflow_ttm",
    "trailing_pe",
    "forward_pe",
    "price_to_book",
    "enterprise_to_ebitda",
    "profit_margin",
    "return_on_equity",
    "current_ratio",
    "debt_to_equity",
    "insider_ownership",
    "institutional_ownership",
    "shares_outstanding",
    "float_shares",
    "change_52w",
    "average_volume",
    "currency",
]


def build_row(symbol: str, info: dict[str, Any]) -> dict[str, Any]:
    source = {
        "symbol": symbol,
        "name": info.get("longName") or info.get("shortName"),
        "price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "market_cap": info.get("marketCap"),
        "enterprise_value": info.get("enterpriseValue"),
        "total_cash": info.get("totalCash"),
        "total_debt": info.get("totalDebt"),
        "revenue_ttm": info.get("totalRevenue"),
        "ebitda_ttm": info.get("ebitda"),
        "operating_cashflow_ttm": info.get("operatingCashflow"),
        "free_cashflow_ttm": info.get("freeCashflow"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "enterprise_to_ebitda": info.get("enterpriseToEbitda"),
        "profit_margin": info.get("profitMargins"),
        "return_on_equity": info.get("returnOnEquity"),
        "current_ratio": info.get("currentRatio"),
        "debt_to_equity": info.get("debtToEquity"),
        "insider_ownership": info.get("heldPercentInsiders"),
        "institutional_ownership": info.get("heldPercentInstitutions"),
        "shares_outstanding": info.get("sharesOutstanding"),
        "float_shares": info.get("floatShares"),
        "change_52w": info.get("52WeekChange"),
        "average_volume": info.get("averageVolume"),
        "currency": info.get("currency"),
    }
    return {field: source.get(field) for field in FIELDS}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    failures: list[str] = []
    for symbol in [ticker.upper() for ticker in args.tickers]:
        try:
            info = yf.Ticker(symbol).info or {}
            rows.append(build_row(symbol, info))
            print(f"ok  {symbol}")
        except Exception as exc:  # noqa: BLE001
            failures.append(symbol)
            print(f"err {symbol}: {exc}")
        time.sleep(0.2)

    out_path = args.out or OUT_DIR / f"{date.today().isoformat()}-value-shortlist.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"saved {len(rows)} rows -> {out_path}")
    if failures:
        print(f"failed: {', '.join(failures)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

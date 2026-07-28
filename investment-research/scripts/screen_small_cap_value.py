#!/usr/bin/env python3
"""Screen U.S. small caps for deep-value research candidates.

This is a discovery tool, not a buy list. It uses Yahoo Finance's screener to
find companies that pass one or more accounting-based filters, then writes a
deduplicated CSV for manual SEC-filing review.

Usage:
    .venv/bin/python scripts/screen_small_cap_value.py
    .venv/bin/python scripts/screen_small_cap_value.py --max-results 100
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

import yfinance as yf


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "screens"
EXCHANGES = ["exchange", "NMS", "NYQ", "ASE"]


def equity_query(operator: str, operands: list[Any]) -> yf.EquityQuery:
    return yf.EquityQuery(operator, operands)


def build_queries() -> dict[str, yf.EquityQuery]:
    common = [
        equity_query("eq", ["region", "us"]),
        equity_query("is-in", EXCHANGES),
        equity_query("gt", ["avgdailyvol3m", 100_000]),
    ]

    return {
        "cashflow_value": equity_query(
            "and",
            common
            + [
                equity_query(
                    "btwn", ["intradaymarketcap", 100_000_000, 5_000_000_000]
                ),
                equity_query("btwn", ["peratio.lasttwelvemonths", 0, 15]),
                equity_query("gt", ["leveredfreecashflow.lasttwelvemonths", 0]),
                equity_query("gt", ["returnonequity.lasttwelvemonths", 5]),
                equity_query("lt", ["netdebtebitda.lasttwelvemonths", 2.5]),
            ],
        ),
        "asset_value": equity_query(
            "and",
            common
            + [
                equity_query(
                    "btwn", ["intradaymarketcap", 50_000_000, 3_000_000_000]
                ),
                equity_query(
                    "btwn",
                    ["lastclosepricetangiblebookvalue.lasttwelvemonths", 0, 1.25],
                ),
                equity_query("gt", ["currentratio.lasttwelvemonths", 1.5]),
                equity_query("lt", ["totaldebtequity.lasttwelvemonths", 60]),
                equity_query("gt", ["cashfromoperations.lasttwelvemonths", 0]),
            ],
        ),
        "fallen_profitable": equity_query(
            "and",
            common
            + [
                equity_query(
                    "btwn", ["intradaymarketcap", 200_000_000, 10_000_000_000]
                ),
                equity_query("lt", ["fiftytwowkpercentchange", -20]),
                equity_query("btwn", ["peratio.lasttwelvemonths", 0, 20]),
                equity_query("gt", ["leveredfreecashflow.lasttwelvemonths", 0]),
                equity_query("gt", ["returnonequity.lasttwelvemonths", 8]),
                equity_query("lt", ["totaldebtequity.lasttwelvemonths", 100]),
            ],
        ),
    }


def is_common_equity(quote: dict[str, Any]) -> bool:
    if quote.get("quoteType") != "EQUITY":
        return False
    name = str(quote.get("longName") or quote.get("shortName") or "").lower()
    rejected = (
        "depositary shares",
        "preferred",
        "warrant",
        "acquisition corp",
        "acquisition company",
        "units",
    )
    return not any(term in name for term in rejected)


def finite_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    return None


def discovery_score(quote: dict[str, Any], screen_count: int) -> float:
    """Rank research priority using only fields returned by the screener."""
    score = min(screen_count, 3) * 12.0
    pe = finite_number(quote.get("trailingPE"))
    pb = finite_number(quote.get("priceToBook"))
    change = finite_number(quote.get("fiftyTwoWeekChangePercent"))
    market_cap = finite_number(quote.get("marketCap"))

    if pe is not None and pe > 0:
        score += max(0.0, min(20.0, (20.0 - pe) * 1.25))
    if pb is not None and pb > 0:
        score += max(0.0, min(15.0, (2.0 - pb) * 10.0))
    if change is not None and change < 0:
        score += min(15.0, abs(change) * 0.3)
    if market_cap is not None and market_cap < 2_000_000_000:
        score += 8.0
    return round(score, 2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-results", type=int, default=250)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    matches: dict[str, dict[str, Any]] = {}
    screens: dict[str, set[str]] = defaultdict(set)

    for screen_name, query in build_queries().items():
        result = yf.screen(
            query,
            size=args.max_results,
            sortField="intradaymarketcap",
            sortAsc=True,
        )
        quotes = result.get("quotes", [])
        print(f"{screen_name}: {len(quotes)} returned / {result.get('total')} total")
        for quote in quotes:
            if not is_common_equity(quote):
                continue
            symbol = quote.get("symbol")
            if not symbol:
                continue
            matches[symbol] = quote
            screens[symbol].add(screen_name)

    rows: list[dict[str, Any]] = []
    for symbol, quote in matches.items():
        matched = sorted(screens[symbol])
        rows.append(
            {
                "symbol": symbol,
                "name": quote.get("longName") or quote.get("shortName"),
                "screens": ";".join(matched),
                "screen_count": len(matched),
                "discovery_score": discovery_score(quote, len(matched)),
                "price": quote.get("regularMarketPrice"),
                "market_cap": quote.get("marketCap"),
                "trailing_pe": quote.get("trailingPE"),
                "forward_pe": quote.get("forwardPE"),
                "price_to_book": quote.get("priceToBook"),
                "change_52w_pct": quote.get("fiftyTwoWeekChangePercent"),
                "avg_volume_3m": quote.get("averageDailyVolume3Month"),
                "exchange": quote.get("fullExchangeName") or quote.get("exchange"),
                "quote_time": quote.get("regularMarketTime"),
            }
        )

    rows.sort(key=lambda row: (-row["discovery_score"], row["symbol"]))
    out_path = args.out or OUT_DIR / f"{date.today().isoformat()}-small-cap-value.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["symbol"]
    with out_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"saved {len(rows)} unique common-equity candidates -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

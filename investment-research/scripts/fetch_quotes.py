#!/usr/bin/env python3
"""每日行情快照抓取。

用法：
    python fetch_quotes.py
    python fetch_quotes.py --tickers VRT GLW MRVL    # 只抓指定 ticker

输出：../data/snapshots/YYYY-MM-DD.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import date
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    sys.exit("需要先安装依赖：pip install -r requirements.txt")


ROOT = Path(__file__).resolve().parent.parent
TICKERS_FILE = ROOT / "scripts" / "tickers.txt"
OUT_DIR = ROOT / "data" / "snapshots"

FIELDS = [
    "symbol",
    "shortName",
    "currentPrice",
    "marketCap",
    "trailingPE",
    "forwardPE",
    "priceToSalesTrailing12Months",
    "fiftyTwoWeekLow",
    "fiftyTwoWeekHigh",
    "fiftyDayAverage",
    "twoHundredDayAverage",
    "averageVolume",
    "dividendYield",
    "beta",
]


def load_tickers(path: Path) -> list[str]:
    out: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def fetch_one(symbol: str) -> dict:
    info = yf.Ticker(symbol).info or {}
    row = {f: info.get(f) for f in FIELDS}
    row["symbol"] = symbol
    if row.get("currentPrice") is None:
        row["currentPrice"] = info.get("regularMarketPrice")
    return row


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tickers", nargs="*", help="覆盖 tickers.txt，只抓这些")
    p.add_argument("--out", type=Path, help="覆盖默认输出路径")
    args = p.parse_args()

    symbols = args.tickers or load_tickers(TICKERS_FILE)
    out_path = args.out or (OUT_DIR / f"{date.today().isoformat()}.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    failures: list[tuple[str, str]] = []
    for i, sym in enumerate(symbols, 1):
        try:
            row = fetch_one(sym)
            price = row.get("currentPrice")
            mcap = row.get("marketCap")
            mcap_b = f"{mcap/1e9:.1f}B" if mcap else "—"
            print(f"[{i:2d}/{len(symbols)}] ok  {sym:12s}  ${price}  mcap={mcap_b}")
            rows.append(row)
        except Exception as e:  # noqa: BLE001
            print(f"[{i:2d}/{len(symbols)}] err {sym:12s}  {e}", file=sys.stderr)
            failures.append((sym, str(e)))
        time.sleep(0.2)  # 友好一点，避免限流

    with out_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"\n保存 {len(rows)} 行 → {out_path}")
    if failures:
        print(f"失败 {len(failures)} 个：{', '.join(s for s, _ in failures)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

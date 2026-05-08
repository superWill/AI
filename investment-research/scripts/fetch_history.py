#!/usr/bin/env python3
"""1 年（默认）日线价格历史抓取，按 ticker 分文件保存。

用法：
    python fetch_history.py                          # 抓 tickers.txt 全部
    python fetch_history.py --tickers LITE AEHR      # 只抓指定的
    python fetch_history.py --period 5y --interval 1wk

输出：data/prices/<TICKER>.csv （列：date,open,high,low,close,volume）
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    sys.exit("需要先安装依赖：pip install -r requirements.txt")


ROOT = Path(__file__).resolve().parent.parent
TICKERS_FILE = ROOT / "scripts" / "tickers.txt"
OUT_DIR = ROOT / "data" / "prices"


def load_tickers(path: Path) -> list[str]:
    out: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            out.append(line)
    return out


def fetch_one(symbol: str, period: str, interval: str):
    df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        return None
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index.name = "date"
    return df


def safe_filename(symbol: str) -> str:
    return symbol.replace(".", "_") + ".csv"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tickers", nargs="*", help="覆盖 tickers.txt，只抓这些")
    p.add_argument("--period", default="1y", help="1y / 2y / 5y / 10y / max")
    p.add_argument("--interval", default="1d", help="1d / 1wk / 1mo")
    args = p.parse_args()

    symbols = args.tickers or load_tickers(TICKERS_FILE)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    failures: list[tuple[str, str]] = []
    for i, sym in enumerate(symbols, 1):
        try:
            df = fetch_one(sym, args.period, args.interval)
            if df is None or df.empty:
                print(f"[{i:2d}/{len(symbols)}] empty {sym:12s}", file=sys.stderr)
                failures.append((sym, "empty"))
                continue
            out_path = OUT_DIR / safe_filename(sym)
            df.to_csv(out_path, float_format="%.4f")
            first = df["Close"].iloc[0]
            last = df["Close"].iloc[-1]
            change = (last / first - 1) * 100
            print(f"[{i:2d}/{len(symbols)}] ok    {sym:12s}  {len(df):>4d} bars  "
                  f"{first:>10.2f} → {last:>10.2f}  ({change:+.1f}%)")
        except Exception as e:  # noqa: BLE001
            print(f"[{i:2d}/{len(symbols)}] err   {sym:12s}  {e}", file=sys.stderr)
            failures.append((sym, str(e)))
        time.sleep(0.2)

    print(f"\n保存 {len(symbols) - len(failures)} 个文件 → {OUT_DIR}")
    if failures:
        print(f"失败 {len(failures)}：{', '.join(s for s, _ in failures)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

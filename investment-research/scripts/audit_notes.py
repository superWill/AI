#!/usr/bin/env python3
"""审计：对比 tickers/<TICKER>.md 文档里的市值 vs 最新快照 CSV，标记偏差 > 阈值的标的。

用法：
    python audit_notes.py                       # 阈值默认 20%
    python audit_notes.py --threshold 30
    python audit_notes.py --snapshot ../data/snapshots/2026-05-07.csv

解析规则：
    - 在每个 ticker 文档里，找首个匹配 "市值 |" 行的内容
    - 支持 "$147.1B" / "$10–15B" / "~$1.5T" / "**$156.3B**" / "<$1B" 等格式
    - 范围用中点估值
    - 跳过非 USD 报价（如 .KS / .T 后缀）—— yfinance 返回本币

退出码：偏差 > 阈值时返回 1（便于 CI 用），否则 0。
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TICKERS_DIR = ROOT / "tickers"
SNAPSHOT_DIR = ROOT / "data" / "snapshots"

SUFFIX_MULT = {"K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}

RANGE_PATTERN = re.compile(
    r"\$?(\d+(?:[.,]\d+)?)\s*[–\-—~至到]\s*(\d+(?:[.,]\d+)?)\s*([KMBT])\b",
    re.IGNORECASE,
)
SINGLE_PATTERN = re.compile(
    r"\$?(\d+(?:[.,]\d+)?)\s*([KMBT])\b",
    re.IGNORECASE,
)
ROW_PATTERN = re.compile(r"^\s*\|[^|]*市值[^|]*\|(.+?)(?:\||$)", re.MULTILINE)

# 非 USD（按 yfinance 后缀），跳过审计
NON_USD_SUFFIXES = (".KS", ".T", ".HK", ".SS", ".SZ", ".KQ")


def parse_dollar_amount(s: str) -> float | None:
    """返回美元数值。范围用中点。无法解析返回 None。"""
    m = RANGE_PATTERN.search(s)
    if m:
        lo, hi, suffix = m.group(1), m.group(2), m.group(3)
        try:
            avg = (float(lo.replace(",", "")) + float(hi.replace(",", ""))) / 2
            return avg * SUFFIX_MULT[suffix.upper()]
        except (ValueError, KeyError):
            pass
    m = SINGLE_PATTERN.search(s)
    if m:
        n, suffix = m.group(1), m.group(2)
        try:
            return float(n.replace(",", "")) * SUFFIX_MULT[suffix.upper()]
        except (ValueError, KeyError):
            pass
    return None


def extract_doc_mcap(md_path: Path) -> tuple[str, float | None]:
    text = md_path.read_text()
    m = ROW_PATTERN.search(text)
    if not m:
        return ("", None)
    raw = m.group(1).strip()
    return (raw, parse_dollar_amount(raw))


def latest_snapshot() -> Path:
    snaps = sorted(SNAPSHOT_DIR.glob("*.csv"))
    if not snaps:
        sys.exit(f"未找到任何快照: {SNAPSHOT_DIR}")
    return snaps[-1]


def load_snapshot(path: Path) -> dict[str, float]:
    out: dict[str, float] = {}
    with path.open() as f:
        for row in csv.DictReader(f):
            sym = row["symbol"]
            mcap = (row.get("marketCap") or "").strip()
            if mcap:
                try:
                    out[sym] = float(mcap)
                except ValueError:
                    continue
    return out


def fmt_b(v: float) -> str:
    if v >= 1e12:
        return f"{v/1e12:>6.2f}T"
    return f"{v/1e9:>6.1f}B"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--threshold", type=float, default=20.0, help="市值漂移标记 > X%%")
    p.add_argument("--rev-threshold", type=float, default=100.0,
                   help="内部一致性：卡营收 vs 市值÷P/S 反推，偏差 > X%% 报警（默认 100，只抓数量级错误）")
    p.add_argument("--snapshot", type=Path, help="指定快照 CSV，默认最新")
    args = p.parse_args()

    snap_path = args.snapshot or latest_snapshot()
    snap = load_snapshot(snap_path)

    print(f"对比基准: {snap_path.relative_to(ROOT)}")
    print(f"阈值:     ±{args.threshold:.0f}%\n")

    aligned: list[str] = []
    drifts: list[tuple[str, float, float, float]] = []
    skipped: list[tuple[str, str]] = []
    # 内部一致性：卡营收 vs 快照市值÷P/S 反推
    inconsistencies: list[tuple[str, float, float, float]] = []

    for md_path in sorted(TICKERS_DIR.glob("*.md")):
        sym = md_path.stem
        if sym.startswith("_"):
            continue
        if sym.endswith(NON_USD_SUFFIXES):
            skipped.append((sym, "非 USD（跳过）"))
            continue
        if sym not in snap:
            skipped.append((sym, "无快照数据"))
            continue

        rec = snap[sym]

        # 内部一致性检查（独立于市值漂移；需 mcap + ps + 卡里可解析营收）
        snap_mcap_for_rev = rec.get("mcap")
        ps = rec.get("ps")
        if snap_mcap_for_rev and ps and ps > 0:
            _, doc_rev = extract_doc_revenue(md_path)
            if doc_rev is not None:
                implied_rev = snap_mcap_for_rev / ps
                if implied_rev > 0:
                    rev_diff = (doc_rev - implied_rev) / implied_rev * 100
                    if abs(rev_diff) > args.rev_threshold:
                        inconsistencies.append((sym, doc_rev, implied_rev, rev_diff))

        snap_mcap = rec.get("mcap")
        if snap_mcap is None:
            skipped.append((sym, "快照无市值字段"))
            continue
        raw, doc_mcap = extract_doc_mcap(md_path)
        if doc_mcap is None:
            skipped.append((sym, f"无法解析 '{raw[:40]}'"))
            continue
        diff_pct = (doc_mcap - snap_mcap) / snap_mcap * 100
        if abs(diff_pct) > args.threshold:
            drifts.append((sym, doc_mcap, snap_mcap, diff_pct))
        else:
            aligned.append(sym)

    if drifts:
        print(f"⚠️  偏差 > {args.threshold:.0f}%（{len(drifts)} 只）：\n")
        print(f"  {'TICKER':12s} {'doc':>8s}  {'snapshot':>8s}  {'diff':>8s}")
        print(f"  {'-'*12} {'-'*8}  {'-'*8}  {'-'*8}")
        for sym, doc, snap_v, pct in sorted(drifts, key=lambda x: abs(x[3]), reverse=True):
            print(f"  {sym:12s} {fmt_b(doc):>8s}  {fmt_b(snap_v):>8s}  {pct:>+7.1f}%")
        print()

    if inconsistencies:
        print(f"🔴 内部一致性存疑（{len(inconsistencies)} 只）——卡营收 vs 市值÷P/S 反推：\n")
        print(f"  {'TICKER':12s} {'卡营收':>8s}  {'反推营收':>8s}  {'diff':>8s}")
        print(f"  {'-'*12} {'-'*8}  {'-'*8}  {'-'*8}")
        for sym, doc, imp, pct in sorted(inconsistencies, key=lambda x: abs(x[3]), reverse=True):
            print(f"  {sym:12s} {fmt_b(doc):>8s}  {fmt_b(imp):>8s}  {pct:>+7.0f}%")
        print("  （数量级不符=卡里营收多半写错，如历史上 NET 的 $20B vs 实际 $2.3B）\n")

    if skipped:
        print(f"⏭  跳过（{len(skipped)} 只）：")
        for sym, reason in skipped:
            print(f"  {sym:12s}  {reason}")
        print()

    print(f"汇总: aligned={len(aligned)}, drift>{args.threshold:.0f}%={len(drifts)}, "
          f"一致性存疑={len(inconsistencies)}, skipped={len(skipped)}")

    return 1 if (drifts or inconsistencies) else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""组合相关性矩阵 + 加权 beta + AI capex 见顶情境压力测试。

输出：dashboards/portfolio-risk.md

用法（用项目 venv，已装 yfinance）：
    .venv/bin/python scripts/portfolio_risk.py
    # 或自定义窗口：
    .venv/bin/python scripts/portfolio_risk.py --period 2y
"""
from __future__ import annotations

import argparse
import math
import statistics
import sys
from datetime import datetime
from pathlib import Path

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    sys.exit("需要先在项目 venv 装 yfinance pandas：\n"
             "  .venv/bin/pip install -r scripts/requirements.txt")


ROOT = Path(__file__).resolve().parent.parent

# 当前 v2 组合（portfolios/2026-05-core-thematic-payoff.md）
PORTFOLIO = {
    "VRT": 18,
    "GLW": 12,
    "MRVL": 12,
    "GEV": 8,
    "COHR": 8,
    "MU": 7,
    "IBM": 10,
    "NET": 7,
    "MP": 5,
    "CAMT": 3,
    "PLAB": 2,
    "IONQ": 2,
}
BENCHMARK = "SPY"
SOXX = "SOXX"


def fetch_close(symbol: str, period: str) -> pd.Series | None:
    try:
        df = yf.Ticker(symbol).history(period=period, interval="1d", auto_adjust=True)
        if df.empty:
            return None
        s = df["Close"]
        s.name = symbol
        return s
    except Exception as e:
        print(f"  err {symbol}: {e}", file=sys.stderr)
        return None


def pearson(x, y):
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    dx = math.sqrt(sum((xi - mx) ** 2 for xi in x))
    dy = math.sqrt(sum((yi - my) ** 2 for yi in y))
    if dx == 0 or dy == 0:
        return float("nan")
    return num / (dx * dy)


def beta_vs(stock, bench):
    n = len(stock)
    mx = sum(bench) / n
    cov = sum((b - mx) * (s - sum(stock) / n) for b, s in zip(bench, stock)) / n
    var = sum((b - mx) ** 2 for b in bench) / n
    return cov / var if var else float("nan")


def vol_annual(returns):
    if len(returns) < 2:
        return float("nan")
    return statistics.stdev(returns) * math.sqrt(252)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--period", default="1y")
    args = p.parse_args()

    print(f"Fetching {len(PORTFOLIO) + 2} tickers, period={args.period}...")
    series = {}
    for sym in list(PORTFOLIO.keys()) + [BENCHMARK, SOXX]:
        s = fetch_close(sym, args.period)
        if s is None or len(s) < 50:
            print(f"  skip {sym}")
            continue
        series[sym] = s

    df_close = pd.DataFrame(series).dropna()
    df_ret = df_close.pct_change().dropna()
    print(f"\nAligned {len(df_ret)} trading days: "
          f"{df_ret.index[0].date()} → {df_ret.index[-1].date()}\n")

    held = [t for t in PORTFOLIO if t in df_ret.columns]
    bench = df_ret[BENCHMARK].tolist()

    # ----- Per-holding stats -----
    print("Per-holding stats vs SPY:")
    print(f"{'Ticker':<7} {'Weight':>6} {'Beta':>6} {'1yRet':>8} {'AnnVol':>8}")
    stats = {}
    for t in held:
        r = df_ret[t].tolist()
        b = beta_vs(r, bench)
        ret1y = (df_close[t].iloc[-1] / df_close[t].iloc[0]) - 1
        v = vol_annual(r)
        stats[t] = {"beta": b, "ret1y": ret1y, "vol": v}
        print(f"{t:<7} {PORTFOLIO[t]:>5}% {b:>6.2f} {ret1y * 100:>7.1f}% {v * 100:>7.1f}%")

    # ----- Weighted portfolio beta -----
    total_w = sum(PORTFOLIO[t] for t in held)
    pf_beta = sum(stats[t]["beta"] * PORTFOLIO[t] for t in held) / total_w
    print(f"\nWeighted portfolio beta (vs SPY): {pf_beta:.2f}")

    # ----- Correlation matrix -----
    print("\nPairwise correlation:")
    corr = df_ret[held].corr()
    print(corr.round(2).to_string())

    # ----- Average pairwise correlation -----
    pairs = []
    for i, a in enumerate(held):
        for j, b in enumerate(held):
            if i < j:
                pairs.append((a, b, float(corr.loc[a, b])))
    avg_corr = sum(p[2] for p in pairs) / len(pairs)
    high_corr = sorted([p for p in pairs if p[2] > 0.70], key=lambda x: -x[2])
    print(f"\nAvg pairwise correlation: {avg_corr:.2f}")
    print(f"Pairs >0.70: {len(high_corr)}")

    # ----- SOXX beta -----
    soxx_beta = float("nan")
    if SOXX in df_ret.columns:
        soxx_beta = beta_vs(df_ret[SOXX].tolist(), bench)
        print(f"SOXX beta vs SPY: {soxx_beta:.2f}")

    # ----- Stress test: SPY -15% -----
    print(f"\nStress test (SPY −15% / SOXX −30%):")
    print(f"{'Ticker':<7} {'Weight':>6} {'Beta':>6} {'EstΔ':>8} {'Contrib':>9}")
    total_contrib = 0
    for t in held:
        b = stats[t]["beta"]
        est = -0.15 * b
        contrib = est * PORTFOLIO[t] / 100
        total_contrib += contrib
        print(f"{t:<7} {PORTFOLIO[t]:>5}% {b:>6.2f} {est * 100:>7.1f}% {contrib * 100:>8.2f}%")
    print(f"\nEstimated portfolio P&L (held portion): {total_contrib * 100:.2f}%")

    # ----- Write markdown -----
    out_md = ROOT / "dashboards" / "portfolio-risk.md"
    write_md(out_md, df_ret, held, stats, corr, avg_corr, high_corr, pf_beta,
             total_contrib, soxx_beta)
    print(f"\nWrote {out_md}")
    return 0


def write_md(path, df_ret, held, stats, corr, avg_corr, high_corr, pf_beta,
             stress_pl, soxx_beta):
    L = []
    L.append("---")
    L.append(f"date: {datetime.utcnow().strftime('%Y-%m-%d')}")
    L.append("type: portfolio-risk-snapshot")
    L.append("benchmark: SPY")
    L.append(f"window: {df_ret.index[0].date()} → {df_ret.index[-1].date()} "
             f"({len(df_ret)} trading days)")
    L.append("---\n")
    L.append("# 组合相关性 + 真实 Beta + 压力测试\n")
    L.append("> 来源：`scripts/portfolio_risk.py`，yfinance adjclose 1y 日线。")
    L.append("> 配合 `portfolios/2026-05-core-thematic-payoff.md` v2 仓位读。\n")

    L.append("## 一、每只持仓 vs SPY\n")
    L.append("| Ticker | Weight | Beta(SPY) | 1y Return | Ann. Vol |")
    L.append("|---|---:|---:|---:|---:|")
    for t in held:
        s = stats[t]
        L.append(f"| {t} | {PORTFOLIO[t]}% | {s['beta']:.2f} | "
                 f"{s['ret1y'] * 100:.1f}% | {s['vol'] * 100:.1f}% |")
    L.append("")

    L.append("## 二、组合加权 Beta\n")
    L.append(f"**加权 beta = {pf_beta:.2f}**（held 权重 "
             f"{sum(PORTFOLIO[t] for t in held)}%，现金 6% 不计入）\n")
    if pf_beta > 1.3:
        L.append(f"> ⚠️ 加权 beta {pf_beta:.2f} 显著高于 1.0 —— 市场跌 1%，"
                 f"组合预期跌 {pf_beta:.2f}%。\n")

    L.append("## 三、Pairwise 相关性矩阵\n")
    L.append("| | " + " | ".join(held) + " |")
    L.append("|---|" + "|".join(["---:"] * len(held)) + "|")
    for a in held:
        row = "| **" + a + "** | "
        row += " | ".join(f"{corr.loc[a, b]:.2f}" for b in held)
        row += " |"
        L.append(row)
    L.append("")
    L.append(f"**平均两两相关性：{avg_corr:.2f}**\n")
    if avg_corr > 0.5:
        L.append(f"> ⚠️ 平均相关性 {avg_corr:.2f} —— 名义上 {len(held)} 个标的，"
                 f"实际相关性高，'分散'是错觉。\n")

    L.append("## 四、高度相关簇（>0.70）\n")
    if not high_corr:
        L.append("无。\n")
    else:
        L.append("| A | B | ρ |")
        L.append("|---|---|---:|")
        for a, b, c in high_corr:
            L.append(f"| {a} | {b} | {c:.2f} |")
        L.append("\n这些标的在任何一个共同因子（hyperscaler capex / AI 周期 / 利率）"
                 "变动时会同向。\n")

    L.append("## 五、AI Capex 见顶情境压力测试\n")
    if not math.isnan(soxx_beta):
        L.append(f"参考：SOXX beta vs SPY = **{soxx_beta:.2f}**。\n")
    L.append("**假设**：hyperscaler capex YoY 转 0 → SPY −15%。"
             "用单因子模型（每只 beta × −15%）估算回撤。\n")
    L.append("| Ticker | Weight | Beta | Est. Δ | Contribution |")
    L.append("|---|---:|---:|---:|---:|")
    for t in held:
        b = stats[t]["beta"]
        est = -0.15 * b
        contrib = est * PORTFOLIO[t] / 100
        L.append(f"| {t} | {PORTFOLIO[t]}% | {b:.2f} | "
                 f"{est * 100:.1f}% | {contrib * 100:.2f}% |")
    L.append(f"\n**估算组合回撤（持仓部分）：{stress_pl * 100:.2f}%**\n")
    L.append("> 单因子模型偏保守。真实情境下个股相关于 SOXX 比相关于 SPY 强，"
             "AI capex 链回撤可能比估计大 20–50%。\n")

    L.append("## 六、可操作结论\n")
    if pf_beta > 1.5:
        L.append(f"1. 加权 beta {pf_beta:.2f} 太高 —— 当前 6% 现金缓冲在 SPY −15% 情境下"
                 "完全不够，建议提到 10–15% 或加 SPY put 对冲\n")
    if high_corr:
        clusters_in_capex_chain = [p for p in high_corr if p[0] in ("VRT", "GEV", "COHR", "MU", "MRVL", "GLW", "CAMT") and p[1] in ("VRT", "GEV", "COHR", "MU", "MRVL", "GLW", "CAMT")]
        if clusters_in_capex_chain:
            L.append("2. 高相关簇集中在 AI 算力链 —— 建议给 'AI capex 链合计' 设硬上限 "
                     "（如 ≤ 50%），目前 VRT+GEV+COHR+MU+MRVL+GLW+CAMT = "
                     f"{18+8+8+7+12+12+3}%\n")
    L.append("3. 加 SPY put / VIX call 的成本可以用这个回撤数估值\n")
    L.append("4. 周度刷新 —— 危机时所有相关性会冲向 1.0，平时算的'安全'会失效\n")

    L.append("\n## 七、相关性热图（ASCII）\n")
    L.append("```")
    L.append("        " + " ".join(f"{t:>4s}" for t in held))
    for a in held:
        row = f"{a:<6s}  "
        for b in held:
            c = corr.loc[a, b]
            if a == b:
                ch = "■■■■"
            elif c > 0.8:
                ch = "████"
            elif c > 0.6:
                ch = "▓▓▓▓"
            elif c > 0.4:
                ch = "▒▒▒▒"
            elif c > 0.2:
                ch = "░░░░"
            else:
                ch = "····"
            row += ch + " "
        L.append(row)
    L.append("```")
    L.append("\n图例：■自身 / █>0.8 / ▓>0.6 / ▒>0.4 / ░>0.2 / · ≤0.2\n")

    path.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

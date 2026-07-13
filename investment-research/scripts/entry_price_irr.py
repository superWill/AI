"""目标 IRR 反推入场价 —— 高估值成长股的"多少能买"计算器。

纪律:输出的是"要达到某个回报门槛,入场估值需要多低",**不是买入建议/目标价**。
到价仍须复核增长二阶导(见对应 ticker 卡的退出条件)。触发价 ≠ 扳机。

三块输出:
  1. 当前价隐含的 5 年年化 IRR(营收 CAGR × 终值 P/S 全矩阵)
  2. 为达目标 IRR 的入场价矩阵(同上两轴)
  3. 基准假设下,不同 IRR 门槛对应的入场价阶梯
可选:传 --fcf 触发 reverse DCF,反解市场当前隐含的 10 年 FCF CAGR。

数据来源:price / marketCap / 股本(=mcap/price) / 52 周区间 / beta 自动从最新快照读,
营收指引(--revenue)必须手输(快照无此列,来自财报)。

用法:
  python scripts/entry_price_irr.py PLTR --revenue 7.65 \
      --rev-cagr 25 30 35 --terminal-ps 10 12 15 --target-irr 15
  # 加 reverse DCF(EV = 市值 − 净现金):
  python scripts/entry_price_irr.py PLTR --revenue 7.65 --fcf 4.3 --net-cash 7.8
"""
from __future__ import annotations

import argparse
import glob
import os

import pandas as pd


def latest_snapshot() -> str:
    paths = sorted(glob.glob("data/snapshots/*.csv"))
    if not paths:
        raise SystemExit("找不到 data/snapshots/*.csv —— 先跑 fetch_quotes.py")
    return paths[-1]


def load_from_snapshot(ticker: str, path: str) -> dict[str, float]:
    df = pd.read_csv(path)
    row = df[df["symbol"] == ticker]
    if row.empty:
        raise SystemExit(f"{ticker} 不在快照 {os.path.basename(path)} —— 先把它加进 scripts/tickers.txt 再 fetch")
    r = row.iloc[0]
    price = float(r["currentPrice"])
    mcap = float(r["marketCap"])
    return {
        "price": price,
        "mcap_b": mcap / 1e9,
        "shares_b": (mcap / price) / 1e9,   # 隐含摊薄股本
        "wk52_low": float(r.get("fiftyTwoWeekLow", "nan")),
        "wk52_high": float(r.get("fiftyTwoWeekHigh", "nan")),
        "beta": float(r.get("beta", "nan")),
        "fwd_pe": float(r.get("forwardPE", "nan")),
        "ps_ttm": float(r.get("priceToSalesTrailing12Months", "nan")),
    }


def implied_irr(mcap0_b: float, rev0_b: float, cagr: float, term_ps: float, years: int) -> float:
    """当前市值买入、持有 years 年、终值按 term_ps × 届时营收退出的年化 IRR。"""
    term_mcap = rev0_b * (1 + cagr) ** years * term_ps
    return (term_mcap / mcap0_b) ** (1 / years) - 1


def entry_price(shares_b: float, rev0_b: float, cagr: float, term_ps: float,
                target_irr: float, years: int) -> float:
    """为达 target_irr,今天该付的每股价。"""
    term_mcap = rev0_b * (1 + cagr) ** years * term_ps
    entry_mcap = term_mcap / (1 + target_irr) ** years
    return entry_mcap / shares_b


def implied_fcf_cagr(ev_b: float, fcf0_b: float, r: float = 0.10,
                     term_g: float = 0.03, horizon: int = 10) -> float | None:
    """reverse DCF:反解令 DCF 现值 = 当前 EV 的 10 年 FCF CAGR(二分法)。"""
    def pv(g: float) -> float:
        s = sum(fcf0_b * (1 + g) ** t / (1 + r) ** t for t in range(1, horizon + 1))
        tv = fcf0_b * (1 + g) ** horizon * (1 + term_g) / (r - term_g)
        return s + tv / (1 + r) ** horizon
    lo, hi = -0.5, 1.5
    if not (pv(lo) <= ev_b <= pv(hi)):
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        if pv(mid) < ev_b:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def run_batch(tickers: list[str], snap_path: str, cagr: float, term_ps: float,
              target_irr: float, years: int) -> None:
    """横向"同一把尺子比贵贱":统一假设 + TTM 营收(mcap/P/S 自动推),按隐含 IRR 升序。"""
    print(f"\n=== 批量 IRR 反推 | 快照 {os.path.basename(snap_path)} | "
          f"统一假设 {cagr*100:.0f}%CAGR × {term_ps:.0f}x 终值 × {years}年 ===")
    print("口径:营收=TTM(市值÷P/S,非 forward,偏保守);同尺子横向比,非每股定制估值。\n")
    rows = []
    for t in tickers:
        try:
            s = load_from_snapshot(t, snap_path)
        except SystemExit as e:
            rows.append((t, None, str(e))); continue
        mcap, ps = s["mcap_b"], s["ps_ttm"]
        if not (ps and ps > 0 and mcap > 0):
            rows.append((t, None, "无 P/S/市值")); continue
        ttm_rev = mcap / ps
        flag = "⚠营收<0.5B,结果失真" if ttm_rev < 0.5 else ""
        irr = implied_irr(mcap, ttm_rev, cagr, term_ps, years)
        ep = entry_price(s["shares_b"], ttm_rev, cagr, term_ps, target_irr, years)
        lo = s["wk52_low"]
        dist_lo = (s["price"]/lo - 1) if lo and lo > 0 else float("nan")
        rows.append((t, dict(price=s["price"], rev=ttm_rev, ps=ps, irr=irr, ep=ep,
                             d_now=ep/s["price"]-1, d_lo=dist_lo, flag=flag), None))
    ok = [(t, d) for t, d, err in rows if d]
    ok.sort(key=lambda x: x[1]["irr"])
    print(f"{'ticker':10}{'现价':>9}{'TTMrev':>9}{'P/S':>7}{'隐含IRR':>9}"
          f"{'入场@'+str(int(target_irr*100))+'%':>10}{'Δ现价':>8}{'距52低':>8}  备注")
    for t, d in ok:
        print(f"{t:10}{d['price']:>9.2f}{d['rev']:>8.1f}B{d['ps']:>7.1f}{d['irr']*100:>+8.1f}%"
              f"{'$'+format(d['ep'],'.0f'):>10}{d['d_now']*100:>+7.0f}%{d['d_lo']*100:>+7.0f}%  {d['flag']}")
    for t, d, err in rows:
        if err:
            print(f"{t:10} —— 跳过:{err}")
    print("\n读法:隐含IRR 越低=同尺子下越贵;入场价=达标价非买入建议;距52低=还要跌多少才触及年低。")
    print("⚠️ 统一假设是横向比较用;各股真实 CAGR 不同,深看某只须单跑并定制假设。\n")


def main() -> None:
    p = argparse.ArgumentParser(description="目标 IRR 反推入场价(高估值成长股)")
    p.add_argument("ticker", nargs="+", help="一个(完整矩阵)或多个(--batch 横向表)")
    p.add_argument("--batch", action="store_true", help="批量横向模式:TTM 营收自动推,统一假设")
    p.add_argument("--revenue", type=float, help="单 ticker:当前财年营收(B);不给则用 TTM")
    p.add_argument("--rev-cagr", type=float, nargs="+", default=[25, 30, 35], help="营收 CAGR 情景(%%)")
    p.add_argument("--terminal-ps", type=float, nargs="+", default=[10, 12, 15], help="终值 P/S 情景")
    p.add_argument("--target-irr", type=float, default=15, help="目标年化 IRR(%%),反推矩阵用")
    p.add_argument("--irr-ladder", type=float, nargs="+", default=[10, 12, 15, 20], help="IRR 门槛阶梯(%%)")
    p.add_argument("--years", type=int, default=5, help="持有年数")
    p.add_argument("--price", type=float, help="覆盖当前价(默认读快照)")
    p.add_argument("--shares", type=float, help="覆盖股本 B(默认 mcap/price)")
    p.add_argument("--snapshot", help="指定快照 CSV(默认最新)")
    p.add_argument("--fcf", type=float, help="当前财年 FCF(B),传入则算 reverse DCF")
    p.add_argument("--net-cash", type=float, default=0.0, help="净现金(B),EV=市值−净现金")
    args = p.parse_args()

    snap_path = args.snapshot or latest_snapshot()
    mid_cagr0 = sorted(args.rev_cagr)[len(args.rev_cagr) // 2] / 100
    mid_ps0 = sorted(args.terminal_ps)[len(args.terminal_ps) // 2]

    if args.batch or len(args.ticker) > 1:
        run_batch(args.ticker, snap_path, mid_cagr0, mid_ps0,
                  args.target_irr / 100, args.years)
        return

    ticker = args.ticker[0]
    s = load_from_snapshot(ticker, snap_path)
    if args.revenue is None:
        args.revenue = s["mcap_b"] / s["ps_ttm"]
        print(f"(未给 --revenue,用 TTM 营收 ${args.revenue:.2f}B = 市值÷P/S)")
    price = args.price or s["price"]
    shares = args.shares or s["shares_b"]
    mcap = price * shares
    cagrs = args.rev_cagr
    pss = args.terminal_ps
    tgt = args.target_irr / 100
    yrs = args.years

    print(f"\n=== {args.ticker} 入场价反推 | 快照 {os.path.basename(snap_path)} ===")
    print(f"现价 ${price:.2f} | 市值 ${mcap:.1f}B | 股本 {shares:.2f}B | "
          f"FY营收 ${args.revenue:.2f}B | {yrs}年展望")
    lo, hi, beta = s["wk52_low"], s["wk52_high"], s["beta"]
    if pd.notna(hi):
        print(f"52周区间 ${lo:.0f}–${hi:.0f}(现价距高 {price/hi-1:+.0%}, 距低 {price/lo-1:+.0%}) | beta {beta:.2f}")

    print(f"\n[1] 当前价隐含 5 年年化 IRR (营收CAGR × 终值P/S):")
    header = "CAGR\\PS |" + "".join(f"{ps:>8.0f}x" for ps in pss)
    print(header)
    for c in cagrs:
        cells = "".join(f"{implied_irr(mcap, args.revenue, c/100, ps, yrs)*100:>+8.1f}%" for ps in pss)
        print(f"{c:>5.0f}%  |{cells}")

    print(f"\n[2] 为达 {args.target_irr:.0f}%/年 IRR 的入场价:")
    print(header)
    for c in cagrs:
        cells = "".join(f"${entry_price(shares, args.revenue, c/100, ps, tgt, yrs):>7.0f}" for ps in pss)
        print(f"{c:>5.0f}%  |{cells}")

    mid_c = sorted(cagrs)[len(cagrs) // 2] / 100
    mid_ps = sorted(pss)[len(pss) // 2]
    print(f"\n[3] 入场价阶梯 (基准 {mid_c*100:.0f}%CAGR / {mid_ps:.0f}x P/S):")
    for irr in args.irr_ladder:
        ep = entry_price(shares, args.revenue, mid_c, mid_ps, irr / 100, yrs)
        print(f"  要 {irr:>2.0f}%/年 → 入场 ${ep:>6.0f}  (较现价 {ep/price-1:>+4.0%})")

    if args.fcf:
        ev = mcap - args.net_cash
        g = implied_fcf_cagr(ev, args.fcf)
        print(f"\n[4] reverse DCF (EV ${ev:.1f}B = 市值−净现金 ${args.net_cash:.1f}B; r=10%, 终值g=3%, 10年):")
        if g is None:
            print(f"  当前 EV 落在可解区间外,FCF ${args.fcf:.1f}B 无解")
        else:
            print(f"  市场隐含 10 年 FCF CAGR ≈ {g*100:.1f}%  (EV/FCF {ev/args.fcf:.0f}x)")
            print(f"  判据:该增速是否 durable(见 organic-growth-screen);隐含苛刻度 vs 同倍数同业")

    print("\n⚠️ 输出=达标价,非买入建议。触发价≠扳机,到价须复核增长二阶导。\n")


if __name__ == "__main__":
    main()

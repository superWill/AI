"""回测：按月定投 vs 攒现金等指数从高点跌 30% 一次性投入。价格指数（不含股息），yfinance ^GSPC/^NDX/^SOX。
用法：.venv/bin/python scripts/dip_vs_dca_backtest.py   # 2026-09-22 结论见对话/笔记：长期定投赢 0.2–0.8pp/年，等跌策略只在 2000– 且现金有 4% 收益时小胜。"""
import yfinance as yf, pandas as pd, numpy as np, warnings; warnings.filterwarnings("ignore")

def xirr(cfs):  # list of (date, amount); negative = contribution
    d0=cfs[0][0]; t=np.array([(d-d0).days/365.25 for d,_ in cfs]); a=np.array([x for _,x in cfs])
    f=lambda r: (a/(1+r)**t).sum()
    lo,hi=-0.9,1.0
    for _ in range(200):
        mid=(lo+hi)/2
        if f(lo)*f(mid)<=0: hi=mid
        else: lo=mid
    return mid

def run(px, start, end, dd_trig=0.30, cash_rate=0.0, monthly=1000, retrig_step=None):
    px=px[(px.index>=start)&(px.index<=end)].dropna()
    months=px.groupby([px.index.year,px.index.month]).head(1).index  # first trading day each month
    # DCA
    sh=0; cfs=[]
    for d in months: sh+=monthly/px[d]; cfs.append((d,-monthly))
    dca_val=sh*px.iloc[-1]; cfs_d=cfs+[(px.index[-1],dca_val)]
    # DIP
    cash=0; sh=0; ath=-1; triggered=False; cfs=[]; buys=[]; daily_r=(1+cash_rate)**(1/252)-1
    mset=set(months); last_trig_level=None
    for d,p in px.items():
        cash*=1+daily_r
        if d in mset: cash+=monthly; cfs.append((d,-monthly))
        if p>ath: ath=p; triggered=False; last_trig_level=None
        dd=p/ath-1
        fire=False
        if not triggered and dd<=-dd_trig: fire=True
        elif retrig_step and triggered and last_trig_level is not None and dd<=last_trig_level-retrig_step: fire=True
        if fire and cash>0:
            sh+=cash/p; buys.append((d.date(),round(p,2),round(dd*100,1),round(cash))); cash=0; triggered=True; last_trig_level=dd
    dip_val=sh*px.iloc[-1]+cash; cfs_p=cfs+[(px.index[-1],dip_val)]
    n=len(months)*monthly
    return dict(contrib=n, dca=dca_val, dip=dip_val, dca_irr=xirr(cfs_d), dip_irr=xirr(cfs_p), buys=buys, cash_left=cash)

def fwd(px, dd_trig=0.30):
    ath=-1; trig=False; out=[]
    for d,p in px.items():
        if p>ath: ath=p; trig=False
        if not trig and p/ath-1<=-dd_trig:
            trig=True; r={}
            for y in (1,3,5):
                e=px[px.index>=d+pd.DateOffset(years=y)]
                r[y]=(e.iloc[0]/p-1)*100 if len(e) else np.nan
            out.append((d.date(),round(p,2),r))
    return out

if __name__=="__main__":
    import sys
    spx=yf.Ticker("^GSPC").history(period="max")["Close"]; spx.index=spx.index.tz_localize(None).normalize()
    ndx=yf.Ticker("^NDX").history(period="max")["Close"]; ndx.index=ndx.index.tz_localize(None).normalize()
    sox=yf.Ticker("^SOX").history(period="max")["Close"]; sox.index=sox.index.tz_localize(None).normalize()
    END="2026-09-21"
    print("S&P 500 数据起点", spx.index[0].date(), "NDX", ndx.index[0].date(), "SOX", sox.index[0].date())
    print("\n=== 每次 −30% 触发后的前瞻收益（S&P 500 价格指数）===")
    for d,p,r in fwd(spx): print(f"{d}  {p:8.2f}  1y {r[1]:+7.1f}%  3y {r[3]:+7.1f}%  5y {r[5]:+7.1f}%")
    print("\n=== 定投 vs 攒钱等 −30% 一次投（每月 $1,000，现金收益 0）===")
    rows=[("S&P 1928–2026",spx,"1928-01-01"),("S&P 1950–2026",spx,"1950-01-01"),("S&P 1980–2026",spx,"1980-01-01"),("S&P 2000–2026",spx,"2000-01-01"),("S&P 2010–2026",spx,"2010-01-01"),("NDX 1985–2026",ndx,"1985-10-01"),("SOX 1994–2026",sox,"1994-01-01")]
    print(f"{'区间':16}{'投入$':>10}{'定投终值':>12}{'等跌终值':>12}{'定投IRR':>9}{'等跌IRR':>9}{'剩余现金%':>9}{'触发次数':>6}")
    for n,px,s in rows:
        r=run(px,s,END)
        print(f"{n:16}{r['contrib']:>10,.0f}{r['dca']:>12,.0f}{r['dip']:>12,.0f}{r['dca_irr']*100:>8.2f}%{r['dip_irr']*100:>8.2f}%{100*r['cash_left']/r['dip']:>8.0f}%{len(r['buys']):>6}")
    print("\n=== 敏感度：S&P 1950–2026，现金收益 4%/年（近似 T-bill）；以及每再跌 10% 追加一次 ===")
    for label,kw in [("现金 0%",{}),("现金 4%",dict(cash_rate=0.04)),("现金 4% + 每再跌10%追加",dict(cash_rate=0.04,retrig_step=0.10)),("触发线 −20%，现金4%",dict(dd_trig=0.20,cash_rate=0.04)),("触发线 −40%，现金4%",dict(dd_trig=0.40,cash_rate=0.04))]:
        r=run(spx,"1950-01-01",END,**kw)
        print(f"{label:28} 定投 {r['dca']:>12,.0f} ({r['dca_irr']*100:.2f}%)  等跌 {r['dip']:>12,.0f} ({r['dip_irr']*100:.2f}%)  剩余现金 {100*r['cash_left']/r['dip']:.0f}%  触发 {len(r['buys'])}")
    print("\n=== S&P 1950– 等跌策略的买入记录（日期, 价格, 回撤, 投入现金）===")
    for b in run(spx,"1950-01-01",END)['buys']: print(b)
    print("\n=== SOX 触发记录 ===")
    for b in run(sox,"1994-01-01",END)['buys']: print(b)

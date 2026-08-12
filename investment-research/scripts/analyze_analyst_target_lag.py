import yfinance as yf, pandas as pd, numpy as np, time
TK='TSLA NVDA AAPL MSFT GOOGL META AMZN MU AMD AVGO NFLX INTC'.split()
rows=[]
px={}
for t in TK:
    ud=None
    for a in range(3):
        try:
            ud=yf.Ticker(t).upgrades_downgrades
            if ud is not None and len(ud): break
        except Exception: pass
        time.sleep(5)
    if ud is None or not len(ud): print(t,'no data'); continue
    for a in range(3):
        d=yf.download(t,start='2018-01-01',end='2026-08-13',auto_adjust=True,progress=False)
        if len(d)>500: break
        time.sleep(5)
    px[t]=d['Close'].squeeze().resample('ME').last()
    u=ud.copy(); u.index=pd.to_datetime(u.index).tz_localize(None)
    u['m']=u.index.to_period('M')
    for m,g in u.groupby('m'):
        pa=g['priceTargetAction'].fillna('')
        rows.append(dict(tk=t,m=m,n=len(g),raises=(pa=='Raises').sum(),lowers=(pa=='Lowers').sum()))
    time.sleep(2)
df=pd.DataFrame(rows)
df['net']=(df.raises-df.lowers)/df.n.clip(lower=1)
# 附加远期收益
def fwd(t,m,k):
    s=px[t]
    try:
        i=list(s.index.to_period('M')).index(m)
    except ValueError: return np.nan
    if i+k>=len(s): return np.nan
    return (s.iloc[i+k]/s.iloc[i]-1)*100
for k,lab in [(3,'f3m'),(6,'f6m'),(12,'f12m')]:
    df[lab]=[fwd(r.tk,r.m,k) for r in df.itertuples()]
df=df[df.n>=3]   # 至少3条动作的月份才算
print('样本: {} 只票, {} 个「股票-月」观测 (每月>=3条评级动作)'.format(df.tk.nunique(),len(df)))
print()
q=df.net.quantile([.2,.8])
hi=df[df.net>=q[0.8]]; lo=df[df.net<=q[0.2]]
print('{:28s} {:>8} {:>9} {:>9} {:>9}'.format('分组','样本数','未来3月%','未来6月%','未来12月%'))
for lab,g in [('⬆ 上调最集中(前20%)',hi),('全样本中位',df),('⬇ 下调最集中(后20%)',lo)]:
    print('{:28s} {:8d} {:9.2f} {:9.2f} {:9.2f}'.format(lab,len(g),g.f3m.median(),g.f6m.median(),g.f12m.median()))
print()
print('净上调比例 与 未来收益 的相关系数:')
for lab in ['f3m','f6m','f12m']:
    s=df[['net',lab]].dropna()
    print('  net vs {}: corr={:+.3f}  (n={})'.format(lab,s.net.corr(s[lab]),len(s)))

# ⭐ 关键检验：分析师是在跟随价格，还是领先价格？
def bwd(t,m,k):
    s=px[t]
    try: i=list(s.index.to_period('M')).index(m)
    except ValueError: return np.nan
    if i-k<0: return np.nan
    return (s.iloc[i]/s.iloc[i-k]-1)*100
for k,lab in [(3,'b3m'),(6,'b6m')]:
    df[lab]=[bwd(r.tk,r.m,k) for r in df.itertuples()]
print()
print('='*56)
print('净上调比例 与【过去】收益 的相关系数（检验"跟随 vs 领先"）:')
for lab,nm in [('b3m','过去3月'),('b6m','过去6月')]:
    s=df[['net',lab]].dropna(); print('  net vs {}: corr={:+.3f}  (n={})'.format(nm,s.net.corr(s[lab]),len(s)))
print()
print('对照（上面已算）: net vs 未来3月 corr=+0.030 / 未来6月 -0.018 / 未来12月 -0.049')
print()
# 按过去涨幅分组看上调比例
df['bq']=pd.qcut(df.b3m,5,labels=['跌最多','跌','平','涨','涨最多'])
print('按【过去3个月涨跌】分组，看当月净上调比例:')
print(df.groupby('bq',observed=True)['net'].agg(['mean','count']).round(3).to_string())

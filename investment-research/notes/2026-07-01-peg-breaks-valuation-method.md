---
date: 2026-07-01
type: methodology
status: active
purpose: PEG 在拐点/周期股上系统性失效;记下"三种失效"+ 按标的类型的正确估值口径;供选股复用
holder_context: 由一次 watchlist PEG 计算 + 用户(另一 AI)的严格批评打磨而来;结论=简单PEG常失效对,但"3yCAGR PEG是唯一口径/<1=真便宜"也错
related: memory organic-growth-screen · tickers/AAPL.md · tickers/MU.md · tickers/AMAT.md · tickers/ADBE.md
---

# PEG 的失效与正确口径（方法论）

## 一句话

**简单 PEG(PE ÷ 增长率)在拐点股、周期股、口径混用时系统性骗人。真正的功夫不是算 PEG,是判"分母(增长)是 durable 还是借来的"——和 [[organic-growth-screen]] 同一把尺子。周期股根本不该用 PEG;稳态股也别用单一 PEG,用三档 forward CAGR 敏感度表。**

## 一、PEG 三种失效方式 `[INFERRED]`

用一次 watchlist(AMAT/LRCX/ADBE/MU/AVGO/QCOM/CEG/GEV/ETN/GOOGL/INTU/PDD)实算,三种失效全出现:

1. **周期 base-effect 假便宜(简单 PEG → 0.02–0.13,纯垃圾)**:MU/CEG/GEV/QCOM。
   EPS 从负转正或谷底反弹造上千个百分点增长率 → PEG 趋零但**毫无估值意义**。
   *样本*:MU EPS 序列 7.6, 0.7, **-5.3**, 7.8;GEV 17.7, 5.6, **-1.6, -10.1**。QCOM 反例——3yr EPS 实际 **-24%**(在缩),20x 不是便宜是衰退。
2. **被一个好年份美化(像 AAPL 现在 / 2016)**:AAPL/AMAT/LRCX。
   *样本*:AAPL EPS **6.1,6.1,6.1** 三年躺平才跳到 7.5,3yr CAGR 仅 ~6.9%;AMAT/LRCX 结构增长其实低个位数,"+33%/+41%"是周期上行。
3. **简单 PEG 藏不住的相对便宜**:ADBE/INTU/GOOGL(EPS 单调上行、无负年)——但**只证明"当前价相对过去增长不高",没证明增长能续**。

## 二、这次被打磨掉的错误(一次严格批评的产物)`[KNOWN]`

对的部分(保留):负利润转正/谷底反弹造假增长 → 拒绝用 PEG 判 MU/CEG/GEV,方向对。

**被纠正的错误**:
1. **数据口径错标**:`yfinance info["earningsGrowth"]` 是 **Quarterly Earnings Growth YoY,不是 TTM 同比**。铁证:实算时"TTM列"与"单季列"几乎逐行相同(AAPL 21.8 vs 19.4 / MU 1368 vs 1398)——若一真 TTM 一真单季,对非平坦公司必分叉。所以"简单 PEG"其实是 PE ÷ 单季增长。
2. **"3yr CAGR PEG"不是真 PEG 也非唯一口径**:trailing PE(当前)÷ trailing CAGR(后视)时间方向不一致;且**3 年本身可能正好跨谷底→高点,照样基数失真**(LRCX 序列里 2.9 就是坑)。"3yCAGR 是周期股唯一有效口径"——**撤回**。
3. **"正常化 PEG<1 → 真便宜"是证据越界**:只说明价格相对过去增长不高,未证增长可续(尤其 ADBE 自己在减速)。
4. **口径混用**:trailing PE / forward PE / GAAP 年 EPS / 单季增长混排;软件的 SBC + 并购摊销进一步扭曲(**AVGO trailing 60.6 vs forward 19.2 全是 VMware 摊销**)。

**净判定**:"简单 PEG 常失效"对;"3yCAGR PEG 唯一有效 / <1 即便宜"错。

## 三、正确口径(按标的类型分桶)`[INFERRED]`

| 桶 | 标的 | 用什么(不用 PEG) |
|---|---|---|
| **深周期** | MU/AMAT/LRCX/GEV/CEG/QCOM | **完整周期正常化 EBIT/FCF + 中周期利润率**;看"周期第几局 + 情绪温度"。**trailing/forward/normalized 三种 PEG 全别算**——forward 估计也锚在当前周期上,一样骗人 |
| **稳态成长** | AAPL/ADBE/INTU/GOOGL | **三档 forward EPS/FCF CAGR 敏感度表**(保守/中性/乐观),不外推过去三年;判增长可续性 |
| **特殊结构** | CEG/GEV(电价+capex+订单)、CRCL(利率+float+take-rate) | 各自的利润路径变量,**不能和软件放同一 PEG 排名** |

## 四、模板:AAPL 敏感度表(比单一"正常化 PEG=5"诚实)`[COMPUTED]`

AAPL 过去三年 EPS ~$6.1→$7.5(CAGR ~6.9%),当前 34.4x:

| 假设未来 EPS CAGR | 对应 PEG |
|---:|---:|
| 7% | 4.9 |
| 10% | 3.4 |
| 15% | 2.3 |
| 20% | 1.7 |

**读法:只有未来增长仍接近 7% 时,5 倍 PEG 才成立。** 最新季 EPS +22% 不足以证明长期增速已从 7% 永久提到 20%——**单一数字换成"在什么增长假设下贵/便宜"的区间,才是诚实的估值。**

## 五、数据备注 `[KNOWN]`

- `info["earningsGrowth"]` ≈ 季度 YoY,别当 TTM。
- yfinance 免费数据常只给 ~4–5 季 diluted EPS,**真 TTM-vs-前TTM(需 8 季)往往算不出**——这也是当初退回用季度值的原因,但不改标签错了的事实。
- 脚本:`scripts/`(临时版在 scratchpad `peg_calc*.py`),可随时重跑刷新;live 拉数依赖网络,yfinance 偶发超时。

## 六、和框架的闭环

PEG 字面值在拐点/周期股上系统性骗人 → **回到判分母**:增长是**有机 durable** 还是**买来/周期借来**([[organic-growth-screen]])。这也解释了为什么"用脚投票的采用信号"比财报 PEG 更领先——**估值比率是结果,增长的性质才是因**。

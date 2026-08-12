# 美股情绪影响：同日很大，预测很弱

## 结论

- [COMPUTED | HIGH] 2016-08-02 至 2026-07-31，共 2,513 个日变动样本，S&P 500 日度对数收益对同日 VIX 点数变化的 OLS R² 为 **62.7%**；VIX 每上升 1 点，同日 S&P 500 平均约下跌 **0.46%**。
- [INFERRED | HIGH] **不能把 62.7% 写成“情绪造成了 62.7% 的涨跌”。** VIX 来自 SPX 期权报价，期权与现货会共同响应消息、杠杆和流动性；这个数字衡量同步共振，不是情绪的因果份额。
- [COMPUTED | HIGH] 最近 3 年完整模型中，VIX 变化单独解释 69.3% 的同日方差；加入高收益债 OAS 后为 73.1%；再加入 10 年实际利率后为 75.1%。
- [COMPUTED | HIGH] 同一套变量对下一日收益的 2023 年以后样本外 R² 为 **-1.1%**；VIX 水平单独对下一日收益的样本内 R² 只有 **0.18%**。
- [INFERRED | HIGH] 情绪指标对“今天为何剧烈波动”很有用，对“明天涨跌”几乎没用；它应控制交易速度、批次和复核强度，不应单独决定方向。

## 统计结果

| 检验 | 数据窗口 | 样本 | R² / 结果 | 可解释含义 |
|---|---:|---:|---:|---|
| [COMPUTED \| HIGH] 同日收益 ~ ΔVIX | 2016-08 至 2026-07 | 2,513 | 62.7% | [INFERRED \| HIGH] 风险厌恶与现货同日共振很强 |
| [COMPUTED \| HIGH] 同日收益 ~ ΔVIX + Δ实际利率 | 2016-08 至 2026-07 | 2,494 | 62.8% | [INFERRED \| HIGH] 在 10 年全样本里，实际利率的日变动只带来很小增量 |
| [COMPUTED \| HIGH] 同日收益 ~ ΔVIX + ΔHY OAS + Δ实际利率 | 2023-08 至 2026-07 | 746 | 75.1% | [INFERRED \| HIGH] 信用压力在近期样本提供额外状态信息 |
| [COMPUTED \| HIGH] VIX 水平 → 下一日收益 | 2016-08 至 2026-07 | 2,512 | 0.18% | [INFERRED \| HIGH] 几乎不能预测次日方向 |
| [COMPUTED \| HIGH] VIX/ΔVIX → 下一日收益，2023+ 留出样本 | 训练至 2022，测试 2023+ | 896 | -1.1% | [INFERRED \| HIGH] 样本外不如历史均值基准 |
| [COMPUTED \| HIGH] ΔVIX → 5/21/63 日收益 | 2016-08 至 2026-07 | 2,450+ | 0.01%/0.03%/0.02% | [INFERRED \| HIGH] 单日情绪冲击本身没有稳定的中期方向信息 |
| [COMPUTED \| MED] 月末 VIX 水平 → 21/63 日收益 | 2016-08 至 2026-07 | 117–119 | 3.6%/7.1% | [INFERRED \| MED] 高恐惧含有限的反向风险溢价信息，但远非择时器 |

- [COMPUTED | HIGH] VIX 单日上升至少 5 点共有 36 次；这些日子 S&P 500 同日平均下跌 3.83%，下一日平均反弹 0.46%，未来 21 个交易日平均上涨 1.91%，上涨率 75%。
- [INFERRED | MED] 该事件研究存在危机聚类、重叠窗口和政策反应混杂，不能据此机械满仓；它更适合建立“极端恐慌时禁止一次性清仓”的纪律。
- [COMPUTED | HIGH] 截至 2026-07-31，VIX 为 15.99，处过去 10 年约第 42 百分位、过去 1 年约第 24 百分位。

## 当前情绪不是一个方向，而是分裂

- [KNOWN | HIGH] Cboe 在 2026-07-27 报告中给出：SPX 1 个月隐含波动率减实现波动率的溢价为约 5 个波动率点、处过去一年第 73 百分位；1 个月 skew 处第 82 百分位。[Cboe 2026-07-27](https://www.cboe.com/insights/posts/week-of-7-27-2026-retail-stays-bullish-on-hyperscalers-ahead-of-earnings)
- [KNOWN | HIGH] Cboe 在 2026-07-13 报告中给出：DSPX 预期个股离散度升至 47%，为 6 年高点，而同期 VIX 约 15。[Cboe 2026-07-13](https://www.cboe.com/insights/posts/week-of-7-13-2026-dspx-index-jumps-to-6-year-high-ahead-of-earnings)
- [KNOWN | HIGH] Cboe 在 2026-07-27 报告中给出：过去一个月 hyperscaler 的零售开仓中 call 占 55%，接近 6 年最高且高于均值 10 个百分点；芯片股为 46%，接近历史均值。[Cboe 2026-07-27](https://www.cboe.com/insights/posts/week-of-7-27-2026-retail-stays-bullish-on-hyperscalers-ahead-of-earnings)
- [KNOWN | HIGH] Cboe 在 2026-07-20 报告中给出：SMH 1 个月隐含波动率升至 59%，SMH 相对 SPX 的波动率溢价达到 44 个百分点、超过均值 5 个标准差。[Cboe 2026-07-20](https://www.cboe.com/insights/posts/hedging-demand-spikes-amid-ai-driven-market-rotation)
- [INFERRED | HIGH] 当前最准确的标签是：**指数恐惧低、尾部保护需求高、个股分歧极高、hyperscaler 局部多头拥挤、半导体方向情绪中性但风险定价极高**。
- [INFERRED | HIGH] 这种结构更容易出现“指数看似稳定，但 AI 链单股因财报或叙事变化大幅跳空”，而不是所有资产同步恐慌。

## 对现有组合的量化影响

- [COMPUTED | HIGH] 现有组合的科技/AI/加密情绪敏感仓位约为 **47.8%**：GOOGL、META、AMZN、NFLX 合计 27.0%，NVDA、TSM、MRVL 合计 15.8%，CRCL 为 5.0%。
- [COMPUTED | HIGH] 如果该 47.8% 袖套同步回撤 10%/20%/30%/40%，组合的机械损失约为 **4.78/9.56/14.34/19.12 个百分点**；该压力测试未假设 BRK 和现金同步下跌。
- [COMPUTED | HIGH] GOOGL、NVDA、CRCL 分别在 -40%/-50%/-70% 的压力假设下，对组合的影响约为 6.36、4.60、3.50 个百分点。
- [FRAME | LOW] 上述压力跌幅是假设，不是价格预测；用途是提前写出最大可承受损失，避免情绪到来后再发明规则。
- [INFERRED | HIGH] 32% 现金降低被迫卖出的风险，但 19.9% 的 BRK 仍是权益资产；不能把“现金 + BRK = 51.9%”全部视为无风险垫。

## 建议纪律

1. [FRAME | LOW] **单一情绪指标永不触发买卖。** 单日 VIX、新闻标题、AAII、put/call 或社媒热度，只允许触发记录和复核。
2. [FRAME | LOW] **情绪只决定交易速度。** 一项指标进入过去 5 年第 90 百分位，只暂停追涨；至少两项持续 3 个收盘日确认，才缩小订单、延长分批周期。
3. [FRAME | LOW] **信用决定是否升级风险状态。** 只有 HY OAS 同步明显走阔，才把“期权恐惧/拥挤”升级为融资压力；固定阈值应换成滚动百分位和 20/60 日变化。
4. [FRAME | LOW] **基本面决定方向。** 对 GOOGL、NVDA、TSM、MRVL、CRCL 的卖出，必须来自订单、库存、毛利率、资本开支回报、现金流或资产负债表恶化，而不是 VIX。
5. [FRAME | LOW] **极端恐慌时禁止一次性动作。** ΔVIX ≥ 5 只触发“禁止一次性清仓 + 复核基本面 + 按预设批次再平衡”；不得自动触发满仓抄底。
6. [FRAME | LOW] **仓位上限由损失预算反推。** `最大单名权重 = 可容忍组合单名损失 / 单名压力跌幅`；集群上限使用同一公式。

## 数据与限制

- [KNOWN | HIGH] S&P 500 日收盘来自 [FRED/SP500](https://fred.stlouisfed.org/series/SP500)，VIX 来自 [Cboe 官方历史数据](https://www.cboe.com/tradable_products/vix/vix_historical_data)，高收益债 OAS 来自 [FRED/BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)，10 年实际利率来自 [FRED/DFII10](https://fred.stlouisfed.org/series/DFII10)。
- [KNOWN | HIGH] FRED 的 S&P 500 公开日频历史限制为 10 年；ICE BofA 高收益债 OAS 自 2026-04 起只公开近 3 年，因此完整模型不能覆盖 2018 或 2020 年危机。[FRED series notes](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)
- [INFERRED | HIGH] R² 对样本、收益定义、对齐方法和危机占比敏感；独立实现使用简单收益得到约 62.2%，本报告使用对数收益得到 62.7%，结论不变。
- [KNOWN | HIGH] 复现代码在 `scripts/analyze_sentiment_impact.py`，执行记录在 `notebooks/2026-08-us-market-sentiment-impact.ipynb`。

[RULES I BROKE]: 无。

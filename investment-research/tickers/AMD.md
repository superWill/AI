---
ticker: AMD
name: Advanced Micro Devices
sector: Semiconductors / AI 加速计算（GPU + CPU）
layer: Layer 3 — AI 加速计算平台（[NVDA](NVDA.md) 的唯一可信第二供应商）
position_type: thematic
status: watching
last_updated: 2026-06-21
data_source: 网络调研 2026-06-21
---

# Advanced Micro Devices (AMD)

## 一句话定位

唯一对 [NVDA](NVDA.md) 构成可信威胁的 AI 加速器第二供应商。MI450/Helios 机柜级方案 2026 H2 出货，是市场上第一个"机柜级对标 Nvidia"的产品。超大厂为了**避免单一供应商绑死**，主动扶持 AMD 当第二货源——这是 AMD 最大的非技术性顺风。配卡逻辑：不是赌它打败 Nvidia，是赌它从"第二货源"拿到 15–20% 加速器份额。

## 关键数据（基准 2026-06-21，网络调研）

| 指标 | 数据 |
|---|---|
| 股价 | ~$510（历史新高） |
| 市值 | **~$834B** |
| 2026 年内涨幅 | +133%（12 个月 ~+300%） |
| 分析师均值目标 | ~$472（**略低于现价**）；高目标 $665（Barclays 6/1） |

## 财务（Q1 FY2026）

| 指标 | 数据 |
|---|---|
| 数据中心营收 | **$58 亿，YoY +57%**（已是最大、最赚钱分部） |
| Q2 FY26 营收指引 | **~$112 亿** |
| 旗舰 MI455X | 40 PFLOPS FP4 / 432GB HBM4 / 19.6 TB/s |
| Helios 机柜 | 单柜 3 AI exaflops，**2026 Q3 出货** |

## 护城河类型

**第二货源刚需 + x86 双寡头 + 机柜级追赶**：

- **CPU 端真护城河**：与 Intel 的 x86 双寡头，EPYC 数据中心份额持续抢占——这块是稳的现金牛。
- **GPU 端是"被需要"而非"护城河"**：超大厂**主动要第二货源**压 Nvidia 议价权，这是 AMD GPU 的结构性顺风，但不是壁垒。
- **软件是命门**：ROCm 生态仍落后 CUDA 一截——这是 thesis 的最大缺口（见下）。

## 市场隐含假设 vs 我的分歧 ⭐

> **市场在 price in 什么**：~$834B、远期高估值，隐含 MI450/Helios H2'26 顺利放量 + AMD 在加速器拿到**有意义且可持续**的份额。OpenAI 6GW、Meta 最高 6GW(~$600 亿)、Oracle 5 万卡 Helios 已被当作收入兑现。

**我可能与市场不同的地方**：
1. **"GW 承诺"≠"收入"**——OpenAI 那笔是**带认股权证结构**的产能承诺，本质是 AMD 用股权补贴换装机量。市场把 GW 数字当订单，但兑现节奏、毛利、补贴成本都没充分折价。真实读数要看 **H2'26 数据中心 GPU 毛利率**会不会被"抢份额定价"摊薄。
2. **真正的分歧点是节奏，不是方向**：所有人都同意 AMD 会拿份额。问题是——**Helios(机柜级对标)是一次"阶跃式追平"，还是又一次被 Nvidia 下一代(Rubin)反超的半步？** 这决定 AMD 是"结构性第二"还是"永远差一代"。

**我哪里可能错（证伪条件）**：
- **ROCm 始终追不上 CUDA**：推理/训练迁移成本太高，超大厂"扶第二货源"流于象征，份额卡在个位数。
- **毛利率陷阱**：为抢份额激进定价 + 股权补贴，营收涨但盈利质量恶化。
- **Rubin 反超**：Nvidia 2026–2027 路线把机柜级优势重新拉开，Helios 沦为半步追赶。
- **估值**：$834B 已 price in 大量乐观；均值目标已低于现价。

## 短期增量（3–5 年）

- MI450 + Helios 机柜 2026 H2 放量（OpenAI/Meta/Oracle 三大催化）。
- EPYC 数据中心 CPU 份额继续抢 Intel。
- 推理市场扩张——AMD 在推理（对成本敏感、对 CUDA 依赖较低）比训练更有机会。

## 长期增量（10–20 年）

- 若坐稳"加速器结构性第二货源"，对应万亿级 TAM 的 15–20% = 巨大空间。
- AI PC / 边缘端 APU 第二增长极。

## 风险

- **⚠️ ROCm 软件差距（首要、技术性）**：CUDA 护城河是 AMD GPU 兑现的最大拦路虎。
- **GW 承诺含股权补贴**：OpenAI 交易的认股权证 = 隐性稀释/补贴成本。
- **Nvidia Rubin 反超**：路线图竞速，半步落后就重定价。
- **毛利率被抢份额定价摊薄**。
- **估值**：均值目标已低于现价，安全垫薄。

## 估值锚

- 类比：[NVDA](NVDA.md)（毛利 75%、CUDA 垄断；AMD 是折价的"挑战者"，但折价是因为份额与软件不确定）。
- 现价隐含"AMD 顺利拿到结构性份额"——若只拿到个位数份额，重定价空间大。
- 配卡定位：**主题仓而非核心**，赌"第二货源刚需"，接受高波动。

## 退出条件

- 触发卖出：H2'26 Helios 放量低于预期 + 数据中心 GPU 毛利率明显恶化。
- 触发减仓：ROCm 迁移持续受阻、份额卡在个位数。
- 再加码：Helios 实测对标 Nvidia 机柜兑现 + AI 板块恐慌拉回估值。

## 跟踪信号

- **MI450/Helios H2'26 收入 + 数据中心 GPU 毛利率**（份额 vs 盈利质量的核心读数）
- ROCm 开发者采用 / 推理迁移案例
- 加速器市场份额（vs Nvidia）
- OpenAI/Meta/Oracle 承诺的实际装机兑现节奏
- Nvidia Rubin 路线图（反超风险）

## 仓位与历史

| 日期 | 操作 | 价格 | 仓位 | 备注 |
|---|---|---|---|---|
| 2026-06-21 | 建档观察 | ~$510 | — | 第二货源刚需 + Helios 机柜级追赶；命门在 ROCm 与毛利率；主题仓 |

## 参考

- 对照：[NVDA](NVDA.md)（龙头） · [AVGO](AVGO.md)/[MRVL](MRVL.md)（定制 ASIC 是另一种"去 Nvidia 化"路径） · [ARM](ARM.md)
- [AMD Q1 2026 财报（IR）](https://ir.amd.com/news-events/press-releases/detail/1284/amd-reports-first-quarter-2026-financial-results)
- [TIKR — AMD 数据中心 +57%、$120B CPU TAM](https://www.tikr.com/blog/amd-stock-forecast-2026-a-57-data-center-revenue-jump-and-a-120-billion-cpu-market)
</content>

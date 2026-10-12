---
ticker: SNDK
name: SanDisk
sector: NAND Flash Memory
layer: Layer 2 — NAND 存储
position_type: core
status: watching
last_updated: 2026-10-12
data_source: scripts/fetch_quotes.py snapshot 2026-05-07；2026-10-12 加 FY26Q4 财报（8-K）+ Q1 FY27 指引 + TrendForce 9/30 & 7/30 + 一致预期（WebSearch），快照 2026-10-10
---

# SanDisk (SNDK)

## 一句话定位

2025 年从 Western Digital 拆分独立的纯 NAND 玩家。AI 推理 KV cache offload 到 NAND 是新趋势。

## 关键数据（基准 2026-10-10，scripts/fetch_quotes.py 快照 + 8-K + 一致预期 WebSearch；5/7 旧表折叠在下）

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$1,581.82** | 5/7 $1,340 → +18%；**6/25 高点 $2,335 → 距高 -32.3%**；8/5 创纪录财报次日 -6.8%（beat 被卖） |
| 市值 | **$228.6B** | 5/7 $208.8B |
| trailing PE | 21.4 | 快照 |
| **forward PE（自算）** | **7.4x（FY27 共识 EPS $213.9）/ 6.0x（FY28 $263.5）** | 快照 fwd 5.9；Q1 FY27 指引年化 EPS ~$180 → 8.8x |
| FY26 Q4（6 月季） | 营收 **$8.97B**（环比 +51%）、GAAP EPS $43.97 / 非 GAAP $39.25、**毛利率 84.6%**（上季 78.4%） | 环比增长 1/3 来自量、**2/3 来自价** |
| Q1 FY27 指引 | 营收 $10.3–10.8B、非 GAAP EPS **$44–46**、毛利率 **83–85%「持平到略降」** | **财报 2026-10-29** |
| 长协 | **8 份 NBM，最低 $93.9B，带财务担保**；数据中心占比 12% → 38% | 回购授权扩至 $15.5B |
| 52 周区间 | $116 – $2,354 | 50DMA $1,576 / 200DMA $1,175 |

<details><summary>2026-05-07 旧表（保留判断轨迹）</summary>

| 指标 | 数据 |
|---|---|
| 股价 | **$1,409.98** |
| 市值 | **$208.8B** |
| TTM PE | 48.07 |
| Forward PE | **8.39** |
| Forward P/S | 15.84 |
| 52 周区间 | $33.13 → $1,439.70 |
| 50 日均线 | $805.24 |
| 200 日均线 | $372.73 |

> **⚠️ 笔记勘误**：v1 笔记写"$913 / $80–95B"已严重过期——今日 **$1,410 / $209B**，市值 **2.5×**。一年区间 $33 → $1,440 = **+4,250%**（接近 52 周高点）。
>
> 关键观察：**Forward PE 8.39 接近 MU 的 7.13**——NAND 与 HBM 在估值上几乎平价，意味着市场把 SanDisk 也当成"周期成长股"在重估。这与笔记里"Forward PE 应低于 MU 同期 30–40%"的预设**已被市场反向证伪**。
>
> 也因此 SNDK 已**远超 $200B**，技术上已超出"$10–200B 推荐区间"。

</details>

## 护城河类型

**寡头格局 + 工艺壁垒**：

- 3D NAND 全球只有 6 家：SanDisk、SK Hynix、Samsung、Micron、Kioxia、YMTC
- 工艺壁垒虽不如 HBM，但每一代堆叠层数攀升（200+ 层）门槛仍高
- 拆分后专注度提升，决策更敏捷

## 短期增量（3–5 年）

- QLC NAND 在 AI 推理中加速渗透（每比特存储更便宜）
- 企业级 SSD 受益数据中心扩容
- KV cache offload 到 NAND：把 LLM 推理中昂贵的 HBM 容量需求往 NAND 下沉

## 长期增量（10–20 年）

- 每台机器人需本地 NAND 存储模型权重（50–200GB）
- 10B × 100GB = **1000 EB 累计需求**
- 但单台用量小 + NAND 单价持续下行 → 收入弹性不如 HBM

## ⭐ 2026-10-12：周期位置判定 —— NAND 是本轮最先见顶的品种，SNDK 股价已领先 `[核实 2026-10-12，8-K + TrendForce 9/30、7/30、8/25 + yfinance]`

> **判定：业绩仍在创纪录，但一阶导（毛利率指引「持平到略降」）已转向、市场已按「顶部」交易（距高 -32%）。本档 5/7 的「NAND 周期能否持续 2–3 年」问题，TrendForce 给了答案：DRAM 能，NAND 不能。** `[INFERRED, MED-HIGH]`

**TrendForce 价格路径** `[KNOWN, HIGH]`：

| | 4Q26 合约价 QoQ | 2027 |
|---|---|---|
| 常规 DRAM | +10–15%（1Q +90–95% → 2Q +58–63% → 3Q +13–18%，**连续三季减速**） | 供需缺口扩大，sufficiency -1~-2% |
| HBM | — | 2027 混合 ASP +121% |
| **NAND** | **+15–20%，企业级 SSD 是唯一在加速的品类** | **2H27 新产能上线 + 消费弱 → 供给转松** |

- SNDK 现在的好看正是因为 NAND 是周期里**最后加速**的那一段；存储股股价通常领先合约价见顶 2–3 季 → NAND 合约价若 1H27 见顶，股价顶部窗口 = 2026 下半年到 2027 初，**-32% 已经是市场在做这件事**。
- **毛利率 84.6% 是周期顶的数字**，不是常态；指引「持平到略降」= 一阶导转向的第一个官方信号。
- 反证（真实但不取消斜坡）：8 份 NBM 最低 $93.9B 带担保、数据中心占比 38%、回购 $15.5B。把悬崖变斜坡。
- **新顶部信号**：TrendForce 8/25 称 2027 年 DRAM+NAND 将占大型 CSP capex 的 **68%**。存储挤占 GPU 预算 → 买方签多年 LTA 压价 → DRAM 二阶导下行，这个比例本身是周期尾段特征 `[INFERRED, MED]`。
- 8/5 财报：创纪录 + 指引在线，次日 **-6.8%**。这是 memory `ai-capex-cycle-topsignal-watchlist` 反应函数 v3「被卖的是抢跑后的 beat」在存储上的样本。

**对本档 5/7 判断的修正**：当时写「估值修复空间 3–4×、取决于周期能否持续 2–3 年」。现在 fwd PE 7.4x 不是便宜，是市场对 FY28 EPS 的不信任（FY28 共识 $263 隐含还在涨，股价不信）。**周期股低 PE = 顶部特征，不是修复空间。**

## 仓位与历史

| 日期 | 操作 | 价格 | 仓位 | 备注 |
|---|---|---|---|---|
| 2026-05-07 | 建档观察 | $1,340 | 无 | 5/7 当时已超出 $10–200B 推荐区间 |
| 2026-10-12 | 更新观察 | $1,581.82 | 无（真相源 `portfolios/`） | 距高 -32%；周期位置判「NAND 先于 DRAM 见顶」；退出条件改为领先指标 |

## 风险

- **周期性比 HBM 更剧烈**：NAND 价格历史上波动幅度更大
- **YMTC 国产化**：长江存储在中低端持续追赶
- **拆分后整合不确定性**：销售渠道、ERP、采购关系都在重建
- **HBM 替代部分 NAND 用途**：在某些场景挤压 NAND 角色

## 估值锚

**2026-10-12 修正**：
- 不用 PE 做周期股的锚。锚是 **NAND 合约价环比的符号** 和 **毛利率指引方向**：两者同时转负 = 下行周期确认，PE 会在 EPS 下修中「变贵」。
- 对照 MU：MU fwd 4.99x（快照）/ SNDK 5.9x，仍近平价，5/7 的「市场把 NAND 当周期成长股」判断未变。

**2026-05-07 原文（保留）**：

- 与 MU 类比：MU Forward PE 7.13、SNDK 8.39 —— **几乎平价**（笔记预期的 30–40% 折扣未实现）
- 暗示市场把 NAND 寡头（SK Hynix / Samsung / Micron / SanDisk / Kioxia）整体当作"周期成长股"重估
- 估值修复空间：Forward PE 8.39 vs 半导体行业中位数 ~34x，理论上仍有 **3–4×**——但这取决于 NAND 周期能否持续 2–3 年不回调

## 退出条件

- ~~**触发减仓**：NAND ASP 连续两季 YoY 下滑~~ → **2026-10-12 废止：按 TrendForce 时间表这条要 2028 年才触发，股价早跌完了（滞后两季以上）。**
- **触发减仓（领先版，任一即触发）**：① TrendForce NAND 合约价季度环比预测首次 ≤0；② 公司毛利率指引连续两季下调；③ Kioxia / 三星 / YMTC 任一家确认 2H27 新产能时间表。
- **触发卖出**：YMTC 高端突破 / 产能过剩信号（NAND sufficiency 转正）。
- **再加码**：KV cache offload 成主流推理架构 **且** NAND 合约价环比仍为正（两条同时满足，缺一不加）。

## 跟踪信号

- **Q1 FY27 财报 2026-10-29**：毛利率落在 83–85% 的哪一端、Q2 指引方向、NBM 份数与最低金额是否再增。
- TrendForce 季度合约价预测（每季末发布）：NAND 环比数字 + 企业 SSD 是否仍是唯一加速品类。
- NAND 现货价格（DRAMeXchange）；现货领先合约。
- 数据中心 SSD 出货量；企业级 NAND 占比。
- Kioxia / YMTC / 三星 2027 产能扩张公告；NAND sufficiency ratio。
- TrendForce「存储占 CSP capex 比例」：68% 若继续升，买方 LTA 压价会更强。

## 参考

- 主题笔记：[2026-05 AI/机器人/量子产业链](../notes/2026-05-ai-robotics-quantum-supply-chain-v1.md#5.1)
- SanDisk FY26 Q4 8-K（2026-08-05）— https://www.sec.gov/Archives/edgar/data/0002023554/000162828026053346/sndkq4-26ex991xpressrelease.htm
- SanDisk FY26 Q4 新闻稿 — https://investor.sandisk.com/news-releases/news-release-details/sandisk-reports-fiscal-fourth-quarter-2026-financial-results
- Q1 FY27 指引 / 回购 $15.5B — https://seekingalpha.com/news/4627102-sandisk-forecasts-q1-fy2027-revenue-of-10_3b-10_8b-and-non-gaap-eps-of-44-46-while-expanding
- TrendForce 9/30：4Q26 合约价 — https://www.trendforce.com/presscenter/news/20260930-13258.html
- TrendForce 7/30：2027 DRAM 紧 / NAND 松 — https://www.trendforce.com/presscenter/news/20260730-13158.html
- TrendForce 8/25：存储占 CSP capex 68% — https://www.trendforce.com/presscenter/news/20260825-13198.html
- 一致预期 EPS（FY27 $213.9 / FY28 $263.5）— https://stockanalysis.com/stocks/sndk/forecast/

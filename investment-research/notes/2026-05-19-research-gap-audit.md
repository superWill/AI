---
date: 2026-05-19
type: research-process-audit
status: draft
owner: self-review (acting as senior PM)
---

# 投研体系 Gap 审计 —— 资深投资人视角

> 目的：不评价单一标的对错，而是审计**研究流程本身**有哪些维度缺失或深度不足。
> 优先级：P0（立即补）> P1（本季补）> P2（半年内）> P3（行有余力）。

---

## 总评

你已经做到的（超过大多数散户研究员）：

- 主题驱动 → 标的拆解 → 组合落地 → 持续跟踪，闭环完整
- 估值与基本面分离记录，并用脚本对账（audit_notes.py 防止 copy 老数据）
- 仓位有量化阈值（加仓 / 减仓 / 卖出），不靠"感觉"
- 主题笔记会做 v1/v2 勘误，承认错误而不是删除

明显不够深的地方按重要性排序如下。

---

## P0 ─ 立即补（一周内）

### 1. 估值方法学过于单一，整组合都暴露在"PE 重估"单一逻辑上

当前几乎所有 ticker 文档只看 **TTM PE / Forward PE / P/S**。这三个指标在以下情况下会同时失灵：

- 周期股顶部（MU/SNDK）—— EPS 已经过度膨胀，PE 看起来便宜其实是 normalized 后贵
- 平台型转型公司（IBM）—— 业务分部异质，混合 PE 没意义，必须 SOTP
- 高 capex / 低利润公司（VRT、GEV、AEHR）—— PE 不反映资本回报效率

要补：

- **EV/EBITDA、EV/Sales、FCF Yield、Shareholder Yield**（buyback + dividend + debt paydown）
- **Reverse DCF**：把当前股价反推市场隐含的 5–10 年 revenue CAGR 和稳态 margin
  - 比如 GEV $1,118 隐含的稳态营收是多少？如果今天买的是"AI 电力卖铲子"故事，market 已经 price in 多少？
  - VRT Forward PE 41.67 隐含的稳态增长率？跌到 25% 的时候 PE 会重定价到多少？
- **Normalized / Mid-cycle EPS**：MU/SK 海力士必须用过去 3 个周期的平均 EPS，而不是 FY26 峰值
- **PEG**（增长调整后 PE）：现在所有 ticker 看起来"便宜"的判断都缺这个调整

**单股优先级**：
- MU：今天测算 mid-cycle EPS（用 2018+2021+2024 三轮峰值平均的 60% 折算）
- IBM：必须做 SOTP（咨询 6–8x EBITDA + 软件 / Red Hat 18–22x + 大型机 4–6x + 量子 = option value）
- VRT：incremental margin 测算 + backlog → revenue conversion ratio

### 2. 组合相关性 / 真实分散度

`portfolios/2026-05-core-thematic-payoff.md` 把仓位拆成"核心 / 主题 / 赔率"，但**没算过相关性矩阵**。

实测时你会发现：

- VRT + GEV + COHR + GLW + MRVL + MU + CAMT —— 在"AI capex 见顶"这一个变量下，相关性可能 **0.7–0.9**
- 名义上 7 个赛道，**实际 1 个赌注**

要补：

- 用 `scripts/fetch_history.py` 拉过去 1–2 年所有持仓的日收益率
- 算 Pearson 相关性矩阵；把高度相关（>0.7）的归一类
- 算组合 beta 加权值（每只持仓 beta × 权重 求和）—— 目前没算过，但**几乎肯定 >1.5**
- 做 stress test：假设 SOXX 跌 30% / AI hyperscaler capex YoY 转 0%，组合预期回撤是多少

### 3. 客户集中度与供应链穿透

这是组合里最大的隐性风险之一，所有"卖铲子"逻辑都依赖某一两个客户：

| Ticker | 真正卖给谁？| 当前文档覆盖度 |
|---|---|---|
| ALAB | Nvidia / AMD / hyperscaler（PCIe retimer 在 NVLink 5 替代下需求？） | 缺 |
| CRDO | 同上 + AEC 电缆主客户 | 缺 |
| COHR / LITE | 800G/1.6T 光模块给 Nvidia DGX、Arista、Cisco | 缺 |
| MRVL | 定制 ASIC = AWS Trainium / Google Axion 占多少%？ | 缺 |
| VRT | hyperscaler 4 家 + Equinix + Digital Realty 占多少% | 缺 |
| GLW | 苹果（Gorilla Glass）+ Verizon（光纤）+ 显示玻璃 各自营收占比 | 缺 |
| MP | 唯一关键下游 = GM + 国防部 DPA 协议 | 部分 |
| MU | HBM 客户 = Nvidia 占多少%？ AMD？ Broadcom？ | 缺 |
| AEHR | 单客户 80% 集中度已记录 ✓ | 已记 |

**TODO**：在每只 ticker.md 加 "客户结构" 章节，从 10-K Item 1 / Item 7 / earnings call transcript 抓 top 3 客户营收占比。

### 4. NVLink / CPO / 光电封装路线对 ALAB / CRDO / MRVL 的颠覆风险

PCIe retimer / DSP 业务面临两个**结构性威胁**，目前都没在文档里：

- **NVLink Fusion**（Nvidia 2026 路线）—— 把 retimer 收回到自家 NVSwitch，第三方 retimer 单元价值 ↓
- **CPO（共封装光学）**——Nvidia/Broadcom 都在推进，传统可插拔光模块 2027–2028 起被替代，COHR/LITE 业务结构受冲击

文档里 COHR/LITE 的 thesis 还在"1.6T 光模块放量"上，但**这是 2026–2027 的故事；2028+ 的 CPO 切换会重写产业链格局**。

要补：在 COHR.md / LITE.md / ALAB.md / CRDO.md 加 "技术路线颠覆风险" 章节。

---

## P1 ─ 本季度补（1–3 个月）

### 5. 周期分析 / Supply-Demand 平衡表

存储板块整组合都靠"HBM 范式重估"故事，但缺少最基本的供需测算：

- HBM 产能（SK / 三星 / MU 各自月产能 wpm，按 12-Hi / 16-Hi 拆分）
- HBM 需求（Nvidia GB200/300 出货预测 × HBM/GPU + AMD MI400 + 各家 ASIC × HBM/ASIC）
- ASP / cost spread 走势（DRAMeXchange / TrendForce 数据接入到 dashboard）
- Capex/Sales 比率历史（衡量是否过度扩产）

**判断"HBM 是否还能再涨"必须靠这张表**，目前你只有定性的"长协价锁定"叙述。

### 6. 短期资金面 / 流动性数据

完全缺失的维度：

- Short interest %、days to cover（IONQ/QBTS/RGTI 这种小盘量子股短期最相关）
- Insider transactions（管理层卖出 = 重大信号）
- 13F 大资金动向（Tiger / Coatue / Citadel / Whale Wisdom）
- ETF 持仓变化（SMH / SOXX / DRIV / KQQQ / ROBO 增减持）
- Options 数据（put/call ratio、IV skew、unusual options activity）

**建议**：每周脚本拉一次主要持仓的 short interest（FINRA 数据）+ insider txn（OpenInsider）+ 13F（季度）。

### 7. 同业横向对标（Peer Comp Sheets）

主题笔记里点了竞争对手名字，但**没做数字横向对比表**。资深 PM 看任何一个标的的第一动作就是建 5–7 家同业的 comparable table：

应该建立的 peer comp：

- **AI 电力**：VRT vs SU.PA vs ETN vs Bloom Energy (BE) vs Watts Water (WTS) —— 营收增长、毛利、ROIC、backlog、book-to-bill
- **光模块**：COHR vs LITE vs FN (Fabrinet) vs Bandwidth.io vs InnoLight（中港）
- **存储**：MU vs 000660.KS (SK Hynix) vs 005930.KS (Samsung) vs 285A.T (Kioxia) vs SNDK
- **量子**：IONQ vs RGTI vs QBTS vs IBM Quantum（分部）vs Quantinuum（私）
- **稀土**：MP vs Lynas（澳）vs JL Mag（深 SZ）vs Iluka Resources
- **HBM 量测**：CAMT vs ONTO vs KLAC vs FORM vs Advantest（日 6857）

输出格式：Excel/CSV，列 = 营收、Revenue YoY、Gross Margin、Op Margin、ROIC、Net Debt/EBITDA、Forward PE、EV/EBITDA、3Y CAGR、Buyback Yield。

### 8. 国际竞争与"另一边"的视角

目前组合 100% 美股优先，但产业链的关键节点**不在美股**：

- 半导体设备：**Tokyo Electron (8035)、Advantest (6857)、Disco (6146)、Screen (7735)** —— Advantest 是 HBM 测试事实垄断
- 机器人执行器：**Harmonic Drive (6324)、Nabtesco (6268)、THK (6481)、Fanuc (6954)、Yaskawa (6506)** —— 笔记说"机器人最稀缺是减速器"，但**没一只这种股票在覆盖里**
- 欧洲：**ASML、ASMI、BESI、Soitec、Infineon、Schneider (SU.PA)** —— 你 SU.PA 当 VRT 对照但没单独立档
- 台股：**TSMC (2330)、Hon Hai (2317)、Quanta (2382)、Wistron (3231)、Hiwin (2049)**
- 加拿大：**Celestica (CLS)、Lightspeed**

**至少 Advantest + Harmonic Drive 应该立档**——这是产业链 v1 笔记自己识别的瓶颈节点，但单股研究里完全是空白。

### 9. 宏观因子量化暴露

笔记里宏观风险只在最末段简略提及。需要：

- 组合对 **10Y 实际利率**（10Y - 10Y breakeven）的 beta —— 高 multiple 股的核心折现因子
- 组合对 **美元指数 (DXY)** 的暴露 —— SK Hynix / Kioxia / Samsung 高度敏感
- 组合对 **油价 / 美元天然气**的暴露 —— GEV / VRT 客户的电力成本传导
- **VIX 期权对冲成本**测算：保护组合 10–15% 下行需要多少成本（VIX call 或 SPY put）

### 10. 资本配置评分 / 管理层质量

完全缺失，但这是巴菲特/Druckenmiller/Loeb 看任何公司的第一性问题：

- IBM 历史是"资本配置反面教材"（08–18 大笔回购 + 错误并购），管理层换了 Krishna 后是否真的改善？
- VRT、GEV 高速增长期 capex 是不是用现金流而非债务支撑？
- MU 在周期顶部回购还是建厂？（历史上多次踩错节奏）
- IONQ / QBTS / RGTI 现金消耗率（cash runway 月数）+ 摊薄历史 + 增发节奏

要补：在每只 ticker.md 加 "Capital Allocation Track Record" 章节。

---

## P2 ─ 半年内补（3–6 个月）

### 11. 主题覆盖范围缺口

笔记体系自称"AI / 机器人 / HBM / 量子 / PQC"，但**有几个关键主题完全没研究**：

| 主题 | 关键标的（未覆盖） | 为什么重要 |
|---|---|---|
| **核电 / SMR** | NuScale (SMR)、Oklo (OKLO)、Centrus (LEU)、BWXT、Cameco (CCJ) | "AI 电力卖铲子"的另一端 = 一次能源；CEG 已在覆盖但只算下游 |
| **机器人 AI 模型层** | Tesla Optimus 间接 = TSLA、Figure AI 私募 → ARK 代理、Symbotic (SYM)、UiPath (PATH) | 笔记主题之一但完全空白 |
| **生物制药 AI**（"真正的 AI 应用"）| Recursion (RXRX)、Schrödinger (SDGR)、AbCellera (ABCL)、Absci (ABSI) | 唯一已 monetize 的 AI 垂直应用 |
| **太空 / 国防 AI** | PLTR、ANDV (Anduril 未上市)、RTX、LMT、HII、Kratos | 政府 AI 支出最稳定来源 |
| **网络安全 PQC**（不只 NET）| CRWD、PANW、ZS、OKTA、TENB、S | 比 NET 体量大且 thesis 更直接 |
| **CDN / Edge**（不只 NET）| Fastly (FSLY)、Akamai (AKAM) | NET 估值贵，FSLY 是赔率仓 |
| **数据基础设施**（AI 训练数据 / 向量库）| MDB、SNOW、DDOG、ESTC、Confluent (CFLT) | 笔记的"AI Layer 5"完全没单股 |
| **AI 推理新一代芯片** | Groq (私)、Tenstorrent (私)、Cerebras (拟 IPO)、Lightmatter | 5 年后看是否会替代 H/B100 |

### 12. 退出 / 再平衡机制 / Tax 优化

`watchlist.md` 有触发卖出条件但缺少：

- **时间止损**（持有 X 个月未达指引 → 强制卖出，去情绪化）
- **阶梯式止盈**（涨 30% 砍 1/3，涨 50% 再砍 1/3，剩 1/3 跑长线）
- **再平衡频率**：季度还是阈值（任何单股权重偏离目标 ±30% 触发）
- **Tax-loss harvesting**：年末扫一遍亏损仓位换同主题的"30 天 wash sale" 替代品
- **替代仓位池**：卖出后立刻有"轮换候选"补上（watchlist 现在没明确这件事）

### 13. 评分系统的回测 / 校准

`next-apple-scoring.md` 的五维评分（产品定义权 / 商业化加速度 / 生态控制力 / 财务兑现 / 认知差）框架很好，但：

- 从来没用历史样本验证过——比如 2007 Apple、2013 Tesla、2019 Nvidia、2020 Shopify 在那个时间点上你的评分会不会真的把它们识别出来？
- 没有**校准记录**：什么样的分数对应什么样的预期回报？（比如 80+ 分历史样本平均 5 年回报多少）
- 没有 **base rate 锚**：历史上多少家"被认为是下一只 Apple"真的成了？（10%？2%？）

要补：选 5 个历史成功案例 + 5 个失败案例（被市场过度炒作但没起来的），回到当时时间点用你的评分系统打分，看准确率。

### 14. Pre-mortem / 反事实分析

每个季度末问自己：

> "假设 12 个月后整个组合亏 30%，最可能的原因是什么？"
>
> "假设 12 个月后 IBM 量子 thesis 彻底破灭，组合损失多少？现在的对冲够不够？"

这个练习目前完全没做。

### 15. Attribution（归因）

调仓记录的表头是空的。**每次买卖都应该记录**：

- 买入逻辑（一句话）+ 触发因素
- 当时 thesis 的 3 个关键变量
- 卖出时回看：哪个变量错了 / 对了 / 没起作用

3–6 个月后做归因：哪些主题判断对 / 哪些标的选错 / 哪些时机踩错。**这是从"会研究"进化到"会赚钱"的关键。**

---

## P3 ─ 行有余力（>6 个月）

- 法律风险跟踪（专利诉讼、SEC investigations、auditor changes）
- ESG / 碳成本传导（VRT/GEV 客户被碳关税影响）
- 公司治理评分（韩股折价的部分原因）
- 期权策略（covered call 卖出已重估部分仓位的上行 = 给现金仓"打工"）
- Kelly criterion / position sizing 数学模型
- 自建数据 pipeline（不全靠 yfinance）：Alpha Vantage / Polygon / FRED / EDGAR 直接 pull

---

## 单股层面的具体深化方向

精挑 8 只**最值得马上加深**的：

| Ticker | 缺什么 | 怎么补 |
|---|---|---|
| **MU** | mid-cycle EPS / supply-demand 表 | 取 2018 / 2021 周期数据建表 |
| **IBM** | SOTP 拆分（咨询 / 软件 / 大型机 / Red Hat / 量子） | 五块分别估值后求和 |
| **VRT** | backlog → revenue 转化率、incremental margin、客户集中度 | 翻 10-K + 季度 transcript |
| **GEV** | Backlog $300B+ 的合同结构（fixed-price vs cost-plus）、TSI 服务利润率 | 翻 GE Vernova 上市以来 5 份 10-Q + investor day |
| **GLW** | 分部估值（display / optical / specialty / environmental / life sciences） | 一个 SOTP 模型替代当前混合 PE |
| **QCOM** | Apple modem 内化的量化建模（2024 → 2026 → 2028 流失节奏）+ 汽车增长可见度 | 翻 QCOM IR + Apple 供应链分析 |
| **COHR / LITE** | CPO 切换的时间表 + 客户集中度 + InP / EML 上游缺口 | 看 Nvidia/Broadcom 2027 路线图 |
| **ALAB / CRDO** | NVLink Fusion 对 PCIe retimer 的需求挤压量化 | 翻 Nvidia GTC 2026 路线图 |

---

## 系统层面的"如果只补一件事"

如果时间只够做一件事，做 **#2 组合相关性矩阵 + 真实组合 beta**。

理由：你目前 100% 看多 AI / 半导体 / 算力 / 电力链，名义上 13 个标的、4 个细分赛道，但在"hyperscaler capex YoY 转负"这一个事件下，所有持仓会**同向暴跌**。在确认这个之前，所有"3 阶段建仓 / 现金保留 6%"的精细设计都可能在一个交易日内被冲垮。

这是从"会做股票研究"到"会做组合管理"的分水岭。

---

## 流程改进建议

1. 把这份 audit 作为每季度 review checklist——下一次 v3 portfolio 修订前过一遍
2. `agents/investor-agent-prompt.md` 里加一条："每次写新 ticker.md 必须包含客户集中度、capital allocation track record、reverse DCF 隐含增长率"
3. `dashboards/` 加一个 `peer-comps.md`，至少建 6 张同业对照表（见 §7）
4. 把 `scripts/` 扩展两条：
   - `scripts/fetch_short_interest.py` —— FINRA short interest 跟踪
   - `scripts/fetch_insider_txn.py` —— OpenInsider 抓取持仓异动

---

## 免责

本审计仅针对**研究流程深度**，不评价个股判断对错。投资决策风险自负。

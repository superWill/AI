---
ticker: CEG
name: Constellation Energy
sector: Nuclear Power
layer: Layer 0 — 核电运营
position_type: context
status: watching
last_updated: 2026-10-10
data_source: 主题笔记 2026-05；2026-06-29 加 -36% 回调 A/B 归因 + Calpine merchant 修正 + thesis-break 信号(yfinance + WebSearch)；2026-10-10 加 Q2'26 财报 + Amazon/Google 两张 20 年 PPA + 模板缺章补齐（fetch_quotes 快照 + 公司公告 + WebSearch）
---

# Constellation Energy (CEG)

## 一句话定位

核电运营 + AI DC 电力——美国最大的核电运营商。已与微软等签订专属电力 PPA。

## 关键数据（基准 2026-10-09，scripts/fetch_quotes.py 快照 + 一致预期 WebSearch；6/29 旧值在备注列）

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$298.07**（10/9 收盘） | 6/29 $264 → **+12.9%**；10/6 单日 +12.2%（Google PPA）；10/7–8 利率杀 −4.8% 后 10/9 +4.6% 收复 |
| 市值 | **~$105.6B** | 6/29 ~$94B |
| trailing PE | 29.1 | 快照；6/29 22.9 |
| **forward PE（自算）** | **25.0x（FY26 共识 EPS $11.91）/ 22.3x（FY27 $13.34）** | 快照 fwd 22.4 是 FY27 口径；6/29 自算 19.5 对应当时 $264 / 旧指引中点 |
| 2026 指引 | **$11.50–12.50**（8/6 上调，原 $11–12） | 共识 $11.91 落在区间下半部 |
| 52 周区间 | $228.6 – $412.7 | 距高 **-27.8%**（6/29 时 -36%） |
| vs 50/200DMA | 50DMA $273.3 / 200DMA $286.4 | 已站回 200 线上方 +4%（6/29 时 -17%） |
| 下次财报 | **Q3'26：2026-11-06**（unusualwhales；另有 11/09 估计，待核实） | |

<details><summary>2026-06-29 旧表（保留判断轨迹）</summary>

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$264** | — |
| 市值 | **~$94B** | (旧卡 $100-120B 已过时) |
| trailing PE | 22.9 | — |
| **forward PE** | **19.5** | 三电力标的最便宜(GEV 42.6 / ETN 25.6) |
| 52 周区间 | **$240.5 – $412.7** | **距高 -36%** |
| vs 200DMA | **-17%**($318) | 已跌破长均线 |

</details>

## ⭐ 2026-06-29:-36% 回调归因 = 主要 A(板块/情绪),不是 B(基本面破)`[KNOWN 2026]`

> 核心问题:从 10 月高 $412 → $264(-36%)是"回调机会(A)"还是"价值陷阱(B)"?**拆完:A 占大头,thesis 在 beat。是回调不是接刀。**

**跌因逐条(标 A/B)**:
1. **电价下跌**(2 月 CPI 电价环比大降)→ **混 A/B**:对 merchant 敞口是真基本面,也含周期/情绪。
2. **机构折价配售**:老股东 $281 配 1,100 万股(低于前收)→ **A(技术性 overhang)**。
3. **2026 指引"miss"**:$11-12 adj EPS vs 共识 $11.72(中点略低)→ **轻 A**;且 **Q1 已 beat + 重申该指引**。
4. **Three Mile Island(Crane)重启延迟**("power issues")→ **轻 B(公司时点)**;延迟≠取消。
5. **整条电力交易从狂热高位 de-rate**(GEV/VST/VRT 同步)→ **A(板块轮动)**。

**thesis 完好/增强的证据**:
- **Q1 2026 BEAT**:adj EPS **$2.74 vs 共识 $2.59**、营收 **$11.12B vs 估 $8.81B**、**重申全年 $11-12**。
- **5,650 MW 长协 PPA**(Meta 20 年 1,121MW / 微软 Crane / CyrusOne)。
- **Calpine 收购(1/7/2026 完成,$266 亿)**:成**全美最大电力生产商,55GW、~10% 全美清洁能源**;Q1 盈利由 Calpine + DC 需求驱动。
- **fwd 19.5** 对"全美最大清洁电力商 + 已签 20 年 hyperscaler PPA"= 合理,非陷阱估值。

**⚠️ 修正旧卡"纯核电年金/强地板"说法**:**Calpine 加了天然气+地热 merchant 敞口 → 比纯核电更周期、更吃电价**。地板真(20 年 PPA 的核电部分),但**没那么纯年金;电价正常化是这里唯一真正的 B 类风险**(非情绪,是基本面变量)。另:$266 亿 Calpine 债 + TMI 时点是尾部。

**4 个 thesis-break 信号(真变 B 才撤,否则仍是 A 类回调可拿可加)**:
1. **PPA 被取消**(非签新);
2. **TMI/Crane 重启取消**(非延迟);
3. **电价结构性走低**拖垮 merchant 盈利、且管理层**下修 $11-12 指引**;
4. **Calpine 整合失败 / 债务评级压力**。

**入场纪律**:是回调非接刀,但**分批**——momentum 弱、跌破 200 线,**短期可能续探 $240(52w 低=地板带)**。起始区 $240-265,跌破 $240 且 thesis 完好再加。详见 [[notes/2026-06-29-ai-bottleneck-profit-pool-migration]]。

## 角色

**$100B+ 同主题标的**——AI DC 电力需求中"清洁稳定基荷"的代表。

## 护城河

- 美国最大核电运营商，21 座反应堆
- 已重启 Three Mile Island Unit 1 给微软专供
- 长期 PPA（25 年）锁定收入
- 核电是 AI DC 最理想的"无碳基荷"

## 与组合中其他标的的关系

- **GEV** 是发电设备，CEG 是核电运营
- **VRT / ETN** 是 DC 内部电力
- AI DC 电力供应链：发电（GEV/CEG）→ 输配电（ETN）→ DC 内部（VRT）

## ⭐ 2026-10-10：Q2'26 beat + 上调指引；Amazon/Google 两张 20 年 PPA；Crane 推到 2027 下半年 `[核实 2026-10-10，公司公告 + 8-K + CNBC/Bloomberg + WebSearch]`

> **核心判断：6/29 列的 4 条 thesis-break 信号一条没触发，反方向证据连来两条（新签 PPA）。但 10/6 的 +12% 涨的是倍数不是 EPS——两张单的新增 MW 都在 2028–2032 才并网。** `[INFERRED, MED-HIGH]`

**Q2'26（8/6，8-K）** `[KNOWN, HIGH]`：adj EPS **$2.55 vs 共识 $2.29**（去年同期 $1.91）；GAAP EPS $1.42（去年 $2.67，差额来自 Calpine 并购会计/非经常项）。驱动=Calpine 并表 + 商业业务客户 margin 走高 + 回购增厚，被核电非计划停机部分抵消。**FY26 指引上调至 $11.50–12.50**（原 $11–12）。电话会提 920 MW 新清洁电力交易。股价 8/6 后一个月基本持平——市场当时没给 beat 付钱。

**两张 PPA（本档 6/29 原话「PPA 被取消」是 break 信号 #1，这是它的反面）** `[KNOWN，公司公告，HIGH]`：

| 日期 | 对手方 | 内容 | CEG 出资 | 并网 |
|---|---|---|---|---|
| 10/01 | Amazon | Calvert Cliffs 20 年 PPA 690 MW + 190 MW 扩容；支撑延寿换证 20 年 | ~$30 亿 | 2030–32 |
| 10/06 | Google | 20 年 PPA，PJM 11 台机组 uprate +890 MW；**另加 15 年 2,700 MW 供电协议覆盖现有机组** | ~$43 亿 | 首台 2028 |

- Google 单真正改估值模型的是那 **2,700 MW / 15 年的存量机组协议**，它把一大块 PJM merchant 敞口变成长协——正面打在 6/29 判定的「唯一真 B 类风险 = 电价正常化」上。`[INFERRED, MED-HIGH]`
- 四大超大厂（Meta/微软/Amazon/Google）凑齐，市场读成核电基荷是卖方市场。10/6 +12.2% 中含大盘普涨日 beta，不全是 PPA。
- 冷水：$73 亿 capex 自己掏；新增 MW 2028 起才有 EPS；Calpine 的天然气资产不在这两张单的覆盖范围内，剩余 merchant 敞口的电价风险**只是缩了，没消失**。

**Crane（TMI-1）重启** `[KNOWN, MED-HIGH]`：NRC 环评结论「无显著影响」，FERC 已给豁免；公司口径「2027 下半年」发电，$16 亿、835 MW。比 6/29 时的「延迟」又往后了一点，但仍是**延迟不是取消**（break 信号 #2 未触发）。

**10 月宏观反向**：10/7–8 利率杀（10Y 盘中 5.36%）CEG 两天 -4.8%（10/9 又 +4.6% 收回），和 SOX 同向——它是高久期资产，不是防御。6/29 写的「核电年金 / 强地板」口径此前已修正，本次再确认。

## 短期增量（3–5 年）

- 已签长协容量：Meta 1,121 MW / 微软 Crane 835 MW / Amazon 690+190 MW / Google 890 MW uprate + 2,700 MW 存量 —— 合计 **>6 GW 长协**，新增 MW 2028–2032 分批并网 `[COMPUTED，各公告加总，MED]`。
- Calpine 并表后的商业业务 margin（Q2 已体现）；回购增厚。
- 2027 下半年 Crane 并网 → 835 MW 专供微软，首个完整年 2028。

## 长期增量（10–20 年）

- 美国最大清洁基荷运营商（55 GW，~10% 全美清洁能源）在 AI 用电曲线上的定价权；20 年 PPA 的现金流久期本身就是资产。
- 核电延寿换证（Calvert Cliffs 模式可复制到其他机组）+ uprate 是最便宜的「新核电」。

## 风险

- **电价正常化（真 B，缩小中）**：Calpine 天然气 + 地热 merchant 敞口仍吃电价；两张 PPA 只覆盖核电部分。
- **执行**：$73 亿 uprate/扩容 capex + $16 亿 Crane，并网时点 2027–2032，任何延迟都直接打久期估值。
- **利率**：10 月实测高久期属性（10Y 升 → CEG 和 SOX 同跌）；长协现金流的折现率敏感。
- **杠杆**：$266 亿 Calpine 债；评级压力是尾部。
- **政策**：PJM 容量市场规则 / 联邦核电政策变动。

## 估值锚

- fwd PE 25.0x（FY26 共识）/ 22.3x（FY27）。6/29 自算 19.5x 时判「合理非陷阱」；现在贵了 5.5 个点，买的是「长协簿变厚」。`[COMPUTED]`
- 不给目标价。锚是：长协覆盖率（契约 MW / 总 MW）每升 10 个点，merchant 风险溢价该降多少——这题下次财报后用 `entry_price_irr.py` 跑三档。

## 退出条件

沿用 6/29 的 4 条 break 信号，改成可执行阈值：
1. 任一超大厂 PPA **被取消或重谈降价**（非延迟）；
2. Crane 重启**取消**（非再延期）；
3. 管理层**下修** FY 指引且归因于电价（非一次性停机）；
4. Calpine 债务评级被下调至投资级以下边缘，或整合相关减值。
触发任一 → 论点从 A 类回调改判 B 类，重新评估。

## 仓位与历史

| 日期 | 操作 | 价格 | 仓位 | 备注 |
|---|---|---|---|---|
| 2026-05 | 建档观察 | — | 无 | 主题笔记 §3.2 电力瓶颈 |
| 2026-06-29 | 回调归因 | $264 | 无 | -36% 判 A 类为主；起始区 $240–265 |
| 2026-10-10 | 更新观察 | $298.07 | 无 | Q2 beat + 指引上调；Amazon/Google 两张 PPA；break 信号 0/4；持仓真相源在 `portfolios/`（当前为 context 标的，无仓） |

## 跟踪信号

- **Q3'26 财报（11/06）**：FY26 指引是否再动；核电停机率；Calpine 分部 margin；长协 vs merchant 收入占比（要公司给口径）。
- **Crane 里程碑**：NRC 许可恢复 / 燃料装载 / 并网日期，任何一项后移 >1 季度记一次。
- **新 PPA**：每张公告记 MW、年限、对手方、CEG 出资；长协累计 MW 更新到「短期增量」。
- **PJM 容量拍卖价**（每年 7 月）+ PJM 实时电价月均：merchant 腿的直接输入。
- **10Y 收益率**：10 月实测 CEG 对利率敏感；10Y 每 +25bp 看 CEG 相对 XLU 的超额。

## 参考

- 主题笔记：[2026-05 AI/机器人/量子产业链](../notes/2026-05-ai-robotics-quantum-supply-chain-v1.md#3.2) (电力瓶颈)、§5.3
- 同主题：[GEV](GEV.md) / [VRT](VRT.md)
- Q2'26 8-K（2026-08-06）— https://www.sec.gov/Archives/edgar/data/0001868275/000186827526000097/ceg-20260806991.htm
- Q2'26 新闻稿 — https://www.constellationenergy.com/news/2026/08/constellation-reports-second-quarter-2026-results.html
- Google 890 MW + 2,700 MW 协议（2026-10-06）— https://www.constellationenergy.com/news/2026/10/google-and-constellation-announce-landmark-agreement-to-bring-890-mw-of-new-nuclear-capacity-to-pjm-grid.html
- CNBC：Google 3.6 GW 交易 — https://www.cnbc.com/amp/2026/10/06/google-enters-massive-3point6-gw-power-deal-with-constellation-energy-.html
- Amazon Calvert Cliffs 20 年协议（2026-10-01）— https://www.esgtoday.com/amazon-signs-20-year-deal-with-constellation-to-upgrade-extend-life-of-nuclear-plant/
- Crane 重启进度 / NRC 环评 — https://www.eenews.net/articles/three-mile-island-restart-closes-in-on-nrc-approval/
- 一致预期 EPS（FY26 $11.91 / FY27 $13.34）— https://stockanalysis.com/stocks/ceg/forecast/
- Q3 财报日期 11/06 — https://unusualwhales.com/stock/CEG/earnings

---
ticker: COST
name: Costco Wholesale
sector: 消费必需 / 会员制仓储零售
layer: N/A — 不在 AI 产业链 9 层内；组合里的低 beta 非 SOXX 腿（betaSPY 0.86）
position_type: quality-anchor（候选，未持有）
status: watching
last_updated: 2026-09-16
data_source: 实测行情 2026-09-15（scripts/fetch_quotes.py）+ SEC 8-K/10-K/10-Q（FY2025 年报、FY2026 Q1–Q3、2026-08 月报）+ 电话会转录（Motley Fool / Investing.com）+ Walmart/BJ's 财报 + Placer.ai + WebSearch 多源；两个研究子 agent 2026-09-16 拉取
---

# Costco Wholesale (COST)

## 一句话定位

**收会员费的采购代理**：卖 $2970 亿商品几乎不赚钱（毛利率 11%，加价硬封顶），利润一半来自 $53 亿会费。护城河是**克制**——极少 SKU、不卖广告位、不搞动态定价、故意少赚——模仿者的股东不允许它们这样做。生意质量极高、增长线性（开店 + 涨会费）、估值长期 40–50 倍。这是「看得懂、买不下手」的教科书案例：**论点不在生意好不好，在多少钱能买**。

## 关键数据（基准 2026-09-15 收盘，scripts/fetch_quotes.py 实测 + stockanalysis.com 交叉）

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$901.35** | 9/15 −1.9%；跌破 50 日线 $940 / 200 日线 $961 `[KNOWN]` |
| 市值 | **$399.7B** | EV $388.0B（净现金约 $12B）`[KNOWN]` |
| TTM PE | **46.3** | TTM EPS $19.88 = 5.87+4.50+4.58+4.93 `[COMPUTED]` |
| Forward PE | **39.8–41.3** | yfinance 39.8 / stockanalysis 41.3；对 FY26E $20.58 = 43.8x，对 FY27E $22.63 = 39.8x `[COMPUTED]` |
| Forward P/S | 1.36（TTM） | 零售股 P/S 无意义，看 PE / EV/EBITDA |
| EV/EBITDA | 28.1x | WMT 20.9 / AMZN 16.6 / BJ 12.7 / TGT 9.8 `[KNOWN]` |
| 52 周区间 | $844.06 – $1,096.50 | 历史最高收盘 $1,092.58（2026-05-19）→ 现距高点 **−17.5%** `[COMPUTED]` |
| 一年涨幅 | **−6.9%** | 同期 S&P 创新高，COST 跑输 `[KNOWN]` |
| Beta | 0.86 | 5 年对 SPY；组合真实风险因子是 SOXX，此票对 SOXX 敞口≈0 `[INFERRED]` HIGH |
| 股息 | $5.88/年，0.65% | 2026-04 从 $1.30→$1.47/季（+13%）；FY25 无特别股息 `[KNOWN]` |
| 流通股 | 443.5M | 5 年基本不变，回购只对冲稀释 `[KNOWN]` |

## 财务（FY2025，52 周，截至 2025-08-31；SEC 10-K + 8-K 2025-09-25）

| 项目 | FY2025 | FY2024 | 同比 |
|---|---|---|---|
| 净销售 | $269.9B | $249.6B | +8.1% |
| 会费收入 | **$5.32B** | $4.83B | +10.3% |
| 总营收 | $275.2B | $254.5B | +8.1% |
| 毛利率（商品） | 11.12% | 10.92% | +20 bps `[COMPUTED]` |
| SG&A % | 9.25% | 9.14% | +11 bps `[COMPUTED]` |
| 营业利润 | **$10.38B** | $9.29B | +11.8% |
| 净利 | $8.10B | $7.37B | +9.9% |
| 摊薄 EPS | **$18.21** | $16.56 | +10.0%（FY24 含 $0.14 一次性税收利好）|
| OCF | $13.34B | | |
| Capex | $5.50B | | |
| FCF | **$7.84B** `[COMPUTED]` | | FCF/净利 97% |
| 股息+回购 | $2.18B + $0.90B | | 回购授权余 $1.96B，2027-01 到期 |
| 期末现金 | $14.2B | | 长期债务 $5.7B |

**结构性读数** `[COMPUTED]` HIGH
- **会费 / 营业利润 = 51.3%**。口头常说的「2/3」是旧口径（会费几乎零成本，但商品端营业利润近年上升）。这个比例**下降**是好事：说明商品端在赚钱；上升则说明零售端被压。
- 会员：付费 81.0M（+6.3%）、持卡 145.2M、Executive 38.7M（+9.3%，占付费 47.7%，**贡献销售 73.6%**）。
- 续费率：美加 92.3% / 全球 89.8%。
- 同店（剔油剔汇）：总 +7.6%、美国 +7.3%、加拿大 +8.3%、其他国际 +8.2%、电商 +16.1%。
- 门店 914（美国 629 / 加拿大 110 / 墨西哥 42 / 日本 37 / 英国 29 / 韩国 20 / 澳洲 15 / 台湾 14 / 中国 7 / 西班牙 5 / 其他 6）。FY25 净增 24。
- 电商 $19.6B ≈ 7.3% 净销售；含 Travel 的 digitally-enabled >$27B ≈ 10%；汽油 ≈ 10%。
- 员工 34.1 万，美国平均时薪约 $32（10-K）。

## 财务（FY2026 Q1–Q3 + Q4 已披露销售；Q4 财报 2026-09-24 盘后）

| 项目 | Q1（至 25-11-23） | Q2（至 26-02-15） | Q3（至 26-05-10） | Q4 已知（16 周，至 26-08-30） |
|---|---|---|---|---|
| 净销售 | $66.0B（+8.2%） | $68.2B（+9.1%） | $69.2B（+11.6%） | **$93.9B（+11.3%）** 月报口径 |
| 会费收入 | $1.33B（+14.0%） | $1.36B（+13.6%） | $1.37B（+10.7%） | 共识 ~$1.8B |
| 会费内生增速（剔提价剔汇） | +7.3% | +7.5% | +7.0% | 提价贡献已从 <1/2 → 1/3 → ~1/4 衰减 |
| 毛利率 | 11.32%（+4 bps） | 11.02%（+17 bps） | **11.04%（−21 bps）** | — |
| core-on-core 毛利 | +30 bps | +22 bps | **−9 bps**（首次转负，投向生鲜降价） | 盯 Q4 |
| SG&A % | 9.60% | 9.19% | 8.96%（−20 bps） | — |
| EPS | $4.50（+11%，共识 $4.27） | $4.58（+13.9%，共识 $4.56） | $4.93（+15.2%，共识 $4.91–4.98 三版本） | 共识 $6.51–6.54 |
| 同店（剔油剔汇） | +6.4%（8-K）/ 7.1%（call，口径分歧） | +6.7% | +6.6% | **+6.7%** |
| 客流 / 客单 | +3.1% / +3.2% | +3.1% / +4.2% | **+2.4% / +7.3%**（剔油剔汇 +4.2%） | — |
| 电商同店 | +20.5% | +22.6% | +21.5% | +19.8%（8 月单月降至 17.9%） |
| 付费会员 | 81.4M（+5.2%） | 82.1M（+4.8%） | **82.9M（+4.1%，FY26 最慢）** | — |
| Executive 占付费 | 48.8% | 49.2% | **49.7%**；占销售 75.0% | — |
| 续费率（美加/全球） | 92.2 / 89.7 | 92.1 / 89.7 | 92.2 / 89.7 | — |
| 门店 | 923 | 924 | 928 | **939** |

- **FY2026 全年销售已知**：$297.3B（+10.2%），同店剔油剔汇 +6.6%（美国 +6.6% / 加拿大 +6.7% / 其他国际 +6.5%），电商 +20.7%。`[KNOWN]` 来源：2026-09-02 8 月月报。
- **Q4 营收端大概率 beat**（$93.9B 销售 + ~$1.8B 会费 ≈ $95.7B vs 共识 $94.2–94.9B）`[COMPUTED]` MED；**EPS 端不确定**：Q3 油价通胀 +2.2pts 撑了报表同店但稀释毛利率，Q4 油价走势决定毛利。
- Q3 特殊项：中东冲突推高油价，油量创公司纪录、汽油同店 +20% 段；GLP-1（Wegovy/Ozempic）自费直供入 Member Prescription Program，药房「显著份额提升」；黄金珠宝为「表现最好部门」（**公司从未量化**，Wells Fargo 2024 估月 $100–200M）。
- 8 月单月已现减速：总同店剔油剔汇 +5.4%（含 Labor Day 错位 −75 bps）、加拿大仅 +2.8%、电商 +17.9%。6 月同店从 5 月 12.5% 降至 8.8% 当天股价 −4.2%——**市场对这只票的反应函数是「减速即杀」，beat 不涨**。`[INFERRED]` HIGH

## 商业模式拆解（为什么 11% 毛利能赚 $80 亿）

`[COMMON]` HIGH，除标注外
1. **加价硬封顶**：品牌货 ≤14%、Kirkland ≤15%（公司文化级规则；2025–26 无逐字重申，仅 CFO 转述「固定毛利上限→采购成本降就降价」`(待核实)`）。沃尔玛毛利 ~24%、Target ~28%。
2. **极少 SKU**：约 4,000（超市 3–5 万）→ 单品采购量巨大 → 议价权 → 全市场最低价。全球集采可省 30–40%（Q4 FY25 call）。
3. **负营运资本**：存货周转 13.2x（~28 天），应付账期 ~30 天，10-K 原话「often sell inventory before we are required to pay for it」→ 供应商在给它融资。`[KNOWN]` MED
4. **Kirkland**：FY22 官方口径占 28%；「FY25 $90B / 约 1/3」仅 Motley Fool 单源无出处 `(待核实)` LOW。作用：利润垫 + 对品牌商的谈判筹码 + 关税下的降价武器（Q3 FY26 关税环境中反向降价鸡翅/高尔夫球/床单）。
5. **单店产出**：FY26 ≈ $317M/店/年 `[COMPUTED]`，约 $2,000/sq ft；新店首年年化 $192M（2023 届 $150M）→ 新店质量在**上升**而非被自食。
6. **高频锚**：747 个加油站（油 ≈10% 销售）、药房、Executive 早开门（+1% 美国周销售）、Instacart 每月 $10 抵扣——都是把「来店频次」当产品经营。
7. **员工**：时薪显著高于同业、流失率低 → 损耗低 + 服务好 → 续费率。工会覆盖仅 ~5%（Teamsters 1.8 万人，2025-03 三年合同，2026/2027 各 +$1/h）。

## 护城河类型

**规模 + 信任（品牌）叠加，被「克制」保护** `[INFERRED]` HIGH
- 规模：单店 $317M 是 Sam's 的约 2 倍（Placer.ai：每店访问多 ~50%、单次消费 ~2x，单源 LOW-MED）；SKU 少 + 量大 = 采购成本对手追不上。
- 信任：会员相信「店里任何东西不需要比价」→ 零售最贵的两项成本（顾客决策成本、获客成本）被转成预付会费。续费 90%+ 是这个信任的度量。
- 为什么 3 年内追不上：Sam's 2025-04 宣布每年 15 家新店，**实际 2025 只开 1 家、2026 计划 6 家**；Walmart 股东要利润率，学不了「故意少赚」。BJ's 267 店、会员 8.5M，是区域玩家。
- 反面：护城河**不防估值**，也不防增长天花板。它防的是份额，不是回报。

## 竞争格局（2026）

| | Costco | Sam's Club（WMT） | BJ's |
|---|---|---|---|
| 门店 | 939 | ~601（2026-01，单源） | 267 / 22 州 |
| 会费 | $65 / $130 | $60 / $120（2026-05-01 上调） | $60 / $120（2025-01 上调） |
| 最新同店（剔油） | +6.6%（FY26） | +4.4%（Q2 FY27，客单为负） | +3.1%（Q2 FY26） |
| 电商增速 | +21% | +26% | +30% |
| 会费收入增速 | +10.7% | +6% | +9.9% |
| 客流 Q2 2026（Placer.ai） | **+8.2%** | +4.7–5.0% | +4.9–5.0% |
| 自有品牌 | Kirkland ~1/3（待核实） | Member's Mark ~30%（单源） | — |

`[KNOWN]` MED，来源 WMT 10-Q 2026-07-31 / BJ's 8-K 2026-08-21 / Placer.ai 2026-08-14。
- **三家会费 2026 年全部对齐**——Sam's 涨费消除了价格差，Costco 的 $5 溢价不再是劣势。
- Sam's 的真实威胁在**数字化**（50% 会员用 Scan & Go，1 小时送达）而非开店；Costco 电商 +21% 说明在跟。
- 外部替代：Amazon 同日生鲜 2,300+ 城镇、自称美国第二大 grocer；Walmart+ 会员消费 4x 非会员。这两个抢的是「补货」场景，不是「囤货 + 寻宝」场景。`[INFERRED]` MED
- Numerator 2026 club 渠道 CPG 份额：Costco +0.46pt、Sam's −0.45pt（搜索摘要，原文 403，`(待核实)`）。

## 短期增量（3–5 年）

`[KNOWN]` MED 除标注外
- **开店**：管理层 2025-12 口径每年 30+ 净新，约半数美国，持续 5–10 年；FY26 实际净增 25（年初指引 35→30→28→26，两家推至 FY27）。Capex $6.5B/年。**没有 1,000/1,500 店总量目标陈述**。
- **会费复利**：内生 +7%/年（会员 +4–5% × Executive 升级）；下一轮涨费按 5.5–7 年间隔推 **2029–2031** `[INFERRED]` MED。Executive 渗透已 49.7%，升级红利**边际递减**。
- **电商 20%+**：站点/App 流量 +37%，AI 来源流量三位数增长且转化最高；个性化推荐贡献「just under $5B」（与 Q2 说的 $470M 差一个量级，疑累计口径，`(待核实)`）。
- **零售媒体**：2024-06 建网，2026-03 与 Moloco 合作 AI 站内广告；Kimberly-Clark 案例 ROAS 14:1；**收入未披露**。这是唯一可能改变利润结构的变量——但和「不卖广告位」的文化冲突，管理层会做得很慢。`[INFERRED]` MED
- **GLP-1 药房**：自费 Wegovy/Ozempic $349/月直供（二手）；药房处方量中双位数增长。高频到店 + 高客单。
- **关税退款**：IEEPA 关税 2026-02-20 被最高法院判违法（Learning Resources v. Trump，6–3）；Costco 已收约 1/3 应退款（CFO Dive 2026-08-24），承诺「以某种形式返还会员」→ 走降价而非现金，等于**用退税补贴 comps**。同时被集体诉讼（Stockov，2026-03）要求直接退款。

## 长期增量（10–20 年）

`[INFERRED]` MED
- 国际是唯一非线性的变量：中国 7 店（Executive 会籍 FY26Q3 上线「超预期」，**无分店经营数据**）、日本 37、韩国 20、西班牙 5、法国 3。美国 647 店的密度天花板管理层用「relieving capacity」解释，但美国新店增量必然趋缓。
- 会费是 CPI 挂钩的现金流：每 6–7 年 +8%，历史零流失。
- 它不会变成另一种公司：没有云、没有广告帝国、没有金融。10 年后它大概率还是 Costco，这是优点也是增长上限。**这只票的长期回报 ≈ EPS 增速 10% ± 估值倍数变化**，没有第二增长曲线。

## 风险

- **估值风险（主风险）**：TTM 46x / forward 40x / PEG 3.6 / EV/EBITDA 28x，对 ~10% EPS 增速。2022 回撤 −31.5%（S&P −25%）、2025-H2 −20%、当前距高点 −17.5% 且跌破均线。市场反应函数是「减速即杀、beat 不涨」（6 月月报 −4.2%，Q3 beat 后先跌 ~5%）。**没有安全边际，只有质量溢价。**`[KNOWN/INFERRED]` HIGH
- **基本面风险**：
  - 付费会员增速 6.3% → 4.1%（FY26 三季连降）；续费率 8 季累计 −70/−80 bps（美加 93.0→92.2，全球 90.5→89.7），管理层归因线上注册续费率低。
  - Executive 渗透 49.7%，升级空间见顶。
  - Q3 core-on-core 毛利首次转负（−9 bps），Q4 若延续 = 「用毛利买 comps」。
  - 报表同店被油价通胀（Q3 +2.2pts）和 FX（+1%）虚增；8 月调整后仅 +5.4%。
  - 黄金撑电商 comps，公司不量化 → 金价回落时电商增速失真。
  - 食品通缩（produce/eggs/dairy）压客单；非食品树脂涨价在途。
- **政策/地缘风险**：美国销售约 1/3 进口（CEO 2025-03），其中 <1/2 来自中墨加；IEEPA 判违法后 Section 122 → Section 301 两档 10%/12.5% 接棒（2026-07-24），关税不确定性未消。关税退款诉讼 + 公开承诺「返还」的法律敞口（律所已提示）。FX：CAD/MXN/JPY/KRW。
- **技术替代风险**：低。Amazon/Walmart 抢的是补货场景；真正的替代威胁是「同日达把囤货需求消灭」，10 年尺度看不到证据。`[INFERRED]` MED
- **劳工**：Teamsters 合同到 2028 年初；2026-04 「授权罢工」报道经核为误标日期的 2025 转载，**2026 无罢工**。

## 估值锚

- **类比公司**：WMT（forward 36x，有广告 + 会员 + 电商三引擎）、BJ（19.6x，同模式无品牌）、TGT（16.6x，无会费）。COST 对 WMT 溢价 ~5 倍 PE，对 BJ 溢价 2 倍——**BJ 是「会员制本身值多少」的对照，COST 比 BJ 多出的 20 倍是品牌 + 规模 + 国际**。`[COMPUTED]`
- **历史 PE**：2018 低点 ~25x `(待核实)` LOW；2021-08 ~42x；2026-04 trailing 51.7x；现 46x。10 年逐年表未找到。
- **一致预期**（stockanalysis，39 位，2026-09）：FY26E EPS $20.58（+13%）/ 营收 $302B；FY27E $22.63（+10%）/ $326B。目标价均值 $1,072（$740–1,315），20 强买 / 4 买 / 13 持 / 2 卖。**本档案不给目标价，此为记录卖方分布。**
- **三档情景 5 年 IRR**（`[COMPUTED]` 入场 $901.35，FY26E $20.58，股息 0.65%）：

| 情景 | EPS CAGR | 退出 PE | FY31 股价 | 年化 IRR |
|---|---|---|---|---|
| 悲观 | 7% | 28x | ~$808 | **−1.5%** |
| 基准 | 10% | 35x | ~$1,160 | **+5.8%** |
| 乐观 | 12% | 42x | ~$1,523 | **+11.7%** |

- **反推**（基准情景）：要 10% IRR 入场价 ≈ **$742**；要 15% IRR ≈ **$593**。这不是目标价，是「多少钱这只票才配得上机会成本」。$742 对应 forward PE ~36x（FY26E），仍高于 WMT。`[COMPUTED]` HIGH
- **结论**：基准情景 5.8% IRR < 组合资金的机会成本（BRK-B 锚 / 国债 4.9%）。**当前价买入是在为质量付 100% 的价，不留任何倍数压缩的余地。**

## 退出条件

（未持有，以下是「进入 / 不进入」和持有后的规则）
- **进入门槛**：股价 ≤ $742（基准情景 10% IRR）**且**四项基本面未破：付费会员 YoY ≥ +4%、美加续费 ≥ 91.5%、core-on-core 毛利 ≥ 0、电商 ≥ +12%。到价不等于扳机，到价复核。`[COMPUTED]`
- **触发减仓（若持有）**：forward PE 回到 ≥ 48x 且 FY EPS 增速 < 10% → PEG > 4.8，估值透支。
- **触发卖出（若持有）**：连续两季美加续费 < 91% **或** 付费会员 YoY < +2% → 会员飞轮减速，不再是订阅股。
- **触发卖出**：管理层放弃毛利上限（毛利率连续 4 季 > 12.5% 且非结构性因素）→ 文化变了，这是看似「好消息」的坏消息。
- **持有阈值**：核心逻辑（会费增速 ≥ 名义 GDP + 续费 ≥ 90%）成立时不因估值单独卖出，只不加。

## 跟踪信号

- **财报关注项**（每季 8-K + 电话会）：
  1. 付费会员 YoY（现 4.1%）与美加续费（现 92.2%）——两者同降 = 飞轮问题；
  2. 会费内生增速（剔提价剔汇，现 7.0%）——Q4 FY26 起提价效应清零，看裸数；
  3. core-on-core 毛利 bps（Q3 −9）——连续负 = 用毛利买同店；
  4. 客流 vs 客单拆分（Q3 客流 +2.4% 是 FY26 最低）——客流 < 2% 是警报；
  5. Executive 占付费（49.7%）的增速是否 < 5%；
  6. 电商同店与「黄金珠宝」表述——金价下行时电商是否掉到 15% 以下；
  7. 回购授权是否续（$1.36B 余，2027-01 到期）+ 特别股息（现金 ~$14B+，Fool 猜 2026-H2）。
- **月度销售报告**（每月第一个周三/周四）：剔油剔汇总同店 < 5% 连续两月 → 减速坐实；8 月 5.4%（含 Labor Day −75 bps）是第一个数据点。
- **行业领先指标**：Placer.ai 季度客流（Q2 2026 +8.2%）；Sam's Club 季度 comps 与开店实际数（目标 15/年 vs 实际 1–6）；Numerator club 渠道份额；汽油价格（影响报表同店 ±2pts 和毛利率 ±20 bps 反向）。
- **重大事件日历**：
  - **2026-09-24 盘后 Q4 FY26 财报**（共识 EPS $6.51–6.54，营收 $94.2–94.9B；已知销售 $93.9B）；
  - 2026-10 初 9 月月报；
  - 2026-12 中 Q1 FY27 财报 + FY27 开店指引；
  - IEEPA 退税进度（CBP 已受理 $128.7B）与 Stockov 集体诉讼裁定；
  - 下一次会费上调窗口 2029–2031。

## 仓位与历史

| 日期 | 操作 | 价格 | 仓位 | 备注 |
|---|---|---|---|---|
| 2026-09-16 | 建档观察 | $901.35 | — | 会员制采购代理；生意 A+，价格不留余地；基准 IRR 5.8%；进入门槛 ≤$742 且四项基本面未破 |

> **期权备注**：COST 不在内存/SOXX 减仓腿，**可以**作为 cash-secured put 标的（见 [`put-selling-plan`](../portfolios/2026-07-23-put-selling-plan.md)）。逻辑自洽的行权价是**愿接货价**，即 ≤$742 档；在 $850–900 卖 put 等于在不愿持有的价位承诺持有，违反 playbook。低 beta 0.86 + 距高点 −17.5% 的隐含波动率是否给得够，交易前查 IV。`[INFERRED]` MED

## 参考

- **一手**：[FY2025 10-K](https://www.sec.gov/Archives/edgar/data/909832/000090983225000101/cost-20250831.htm) · [Q4 FY25 8-K 2025-09-25](https://www.sec.gov/Archives/edgar/data/909832/000090983225000093/costex9918-k92525.htm) · [Q1 FY26 8-K](https://www.sec.gov/Archives/edgar/data/909832/000090983225000164/costex9918-k121125.htm) · [Q2 FY26 8-K](https://www.sec.gov/Archives/edgar/data/909832/000090983226000025/costex9918-k3526.htm) · [Q3 FY26 8-K](https://www.sec.gov/Archives/edgar/data/909832/000090983226000046/costex9918-k52826.htm) · [Q3 FY26 10-Q](https://www.sec.gov/Archives/edgar/data/0000909832/000090983226000051/cost-20260510.htm) · [2026-08 月报（含 Q4/FY26 全年销售）](https://investor.costco.com/news/news-details/2026/Costco-Wholesale-Corporation-Reports-August-Sales-Results/default.aspx) · [Q4 FY26 财报日程](https://investor.costco.com/events-and-presentations/events/event-details/2026/Q4-2026-Earnings-Call/default.aspx)
- **电话会**：[Q4 FY25](https://www.investing.com/news/transcripts/earnings-call-transcript-costco-q4-2025-beats-estimates-stock-rises-93CH-4256803) · [Q1 FY26](https://www.fool.com/earnings/call-transcripts/2025/12/11/costco-cost-q1-2026-earnings-call-transcript/) · [Q2 FY26](https://www.fool.com/earnings/call-transcripts/2026/03/05/costco-cost-q2-2026-earnings-call-transcript/) · [Q3 FY26](https://www.fool.com/earnings/call-transcripts/2026/05/28/costco-cost-q3-2026-earnings-transcript/)
- **竞争**：[Walmart Q2 FY27 10-Q](https://www.sec.gov/Archives/edgar/data/0000104169/000010416926000154/wmt-20260731.htm) · [Sam's Club 涨费 2026-05](https://finance.yahoo.com/markets/stocks/articles/sam-club-hikes-membership-prices-090531101.html) · [Sam's 扩张计划 2025-04](https://www.grocerydive.com/news/sams-club-expansion-retail-walmart/745147/) · [BJ's Q2 FY26](https://investors.bjs.com/press-releases/press-release-details/2026/BJs-Wholesale-Club-Holdings-Inc--Announces-Second-Quarter-Fiscal-2026-Results/default.aspx) · [Placer.ai Q2 2026 客流](https://www.placer.ai/anchor/articles/what-q2-2026-visit-trends-reveal-about-superstores-and-wholesale-clubs)
- **关税**：[WilmerHale：最高法院判 IEEPA 关税违法 2026-02-20](https://www.wilmerhale.com/en/insights/client-alerts/20260220-supreme-court-strikes-down-ieepa-tariffs) · [Axios：Costco 承诺返还关税 2026-03-05](https://www.axios.com/2026/03/05/costco-members-tariff-refunds-earnings) · [CFO Dive：退款到账 1/3 + 诉讼 2026-08-24](https://www.cfodive.com/news/costco-fights-customers-tariff-suit-refunds-flow/828644/) · [NRF 退税进度](https://nrf.com/blog/ieepa-tariff-refunds-are-moving-forward) · [进口占 1/3（CEO 2025-03）](https://www.entrepreneur.com/business-news/how-tariffs-will-affect-costcos-prices-ceo-ron-vachris/489632)
- **估值/预期**：[stockanalysis 统计](https://stockanalysis.com/stocks/cost/statistics/) · [stockanalysis 预期](https://stockanalysis.com/stocks/cost/forecast/) · [Barchart Q4 预览 2026-07-27](https://www.barchart.com/story/news/3480268/what-to-expect-from-costco-wholesale-s-q4-2026-earnings-report) · [Fool 空头论点 2026-08-16](https://www.fool.com/investing/2026/08/16/costco-patient-investors-bear-case-nasdaq-cost/) · [Fool 6 月月报股价 −4.2%](https://www.fool.com/investing/2026/07/09/costcos-june-sales-rose-106-but-the-stock-fell-4-h/)
- **其他**：[会费上调 2024-09-01](https://www.cbsnews.com/news/costco-membership-fee-rising-2024/) · [Executive 早开门 2025-06](https://www.axios.com/2025/06/19/costco-hours-executive-members-early-shopping) · [Teamsters 合同 2025-02](https://www.forbes.com/sites/pamdanziger/2025/02/01/costco-strike-averted-after-last-minute-agreement-reached-with-teamsters-union/) · [零售媒体 + Moloco 2026-03](https://p2pi.com/costcos-retail-media-network-adds-ai-onsite-ads) · [Kirkland 占比（单源，待核实）](https://www.fool.com/investing/2026/03/17/how-kirkland-quietly-became-costcos-most-powerful/) · [黄金月销估计（Wells Fargo 2024-04）](https://www.cnbc.com/2024/04/09/costco-selling-up-to-200-million-in-gold-bars-a-month-wells-fargo-estimates.html)
- **组合关联**：[BRK-B](BRK-B.md)（同为低 beta 锚候选；BRK 现价 P/B 与 COST forward PE 的机会成本对照）· [AMZN](AMZN.md)（同日达生鲜 2,300 城镇，补货场景竞争者）· [V](V.md)（Citi Visa 独家卡协议延至 ~2029）

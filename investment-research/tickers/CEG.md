---
ticker: CEG
name: Constellation Energy
sector: Nuclear Power
layer: Layer 0 — 核电运营
position_type: context
status: watching
last_updated: 2026-11-11
data_source: 主题笔记 2026-05；2026-06-29 加 -36% 回调 A/B 归因 + Calpine merchant 修正 + thesis-break 信号(yfinance + WebSearch)；2026-10-10 加 Q2'26 财报 + Amazon/Google 两张 20 年 PPA + 模板缺章补齐（fetch_quotes 快照 + 公司公告 + WebSearch）；2026-11-11 Q3'26 财报对账（8-K 0001868275-26-000116 + 10-Q 0001868275-26-000119 一手直读，电话会为 Fool 二手转录）
---

# Constellation Energy (CEG)

## ⭐ 2026-11-11：Q3'26 财报对账（一手 8-K，2026-11-09 盘前）—— 门控 1 过 / 2 无法判定 / 3 无法判定，不满足「三过二」；指引上调靠 Calpine 并表和 Q3 商业波动收益，原有业务利润持平，得州商业电价敞口在一手数据里清楚可见

> **一句话：论点没有变，但成分更清楚了。** 全年指引 $12.50–12.80 的下沿就是原区间的上沿，门控 1 干净地过了。但拆开看：① Q3 RNF 同比增量约 90% 是 Calpine 并表带来的，原有五个地区分部合计同比 −0.5%，剔除未实现损益后约 −1%（PJM West 电价 +50% 被 PTC 回吐、新英格兰负荷流失和输电成本吃掉）；② 指引上调全部落在「enhanced」（商业波动捕获）这一层，CFO 原话「not transferable to all years」；③ 按指引倒推，Q4 只剩 $2.15–2.45，低于财报前一致预期隐含的 Q4（约 $2.77，二手）。门控 2 没法判：公司不披露单张合同价格，现有 Amazon/Google 合同的单价也从没披露过，所以这道题按原来的写法无解。门控 3 也没法判：10-Q 对 8/3 起的得州数据中心审批暂停只字未提（风险因素「与 2025 10-K 一致」），没有披露任何延期，但沉默不等于放行。同期一手演示稿里 **ERCOT-North 2027 年全时段火花价差远期在一个季度里从 $21.85 跌到 $17.26（−21%）**，已低于公司自己设的 ERCOT 基础假设 $22。按 11/6 写死的规则，**分支 B（CEG 1% 试探仓）的前提不成立。** `[KNOWN, HIGH 一手数字；COMPUTED, HIGH 算术；INFERRED, MED 解读；电话会为 Fool 二手转录 MED]`

> 一手源：[8-K 索引](https://www.sec.gov/Archives/edgar/data/1868275/000186827526000116/0001868275-26-000116-index.htm) · [EX-99.1 新闻稿](https://www.sec.gov/Archives/edgar/data/1168165/000186827526000116/ceg-20261109991.htm) · [EX-99.2 演示稿](https://www.sec.gov/Archives/edgar/data/1168165/000186827526000116/ceg-20261109992.htm) · [10-Q 索引](https://www.sec.gov/Archives/edgar/data/1868275/000186827526000119/0001868275-26-000119-index.htm) · [10-Q 正文](https://www.sec.gov/Archives/edgar/data/1168165/000186827526000119/ceg-20260930.htm)。上季对照：[Q2 EX-99.1](https://www.sec.gov/Archives/edgar/data/1868275/000186827526000097/ceg-20260806991.htm) / Q2 EX-99.2（同目录 `ceg-20260806992.htm`）。电话会引述自 [Motley Fool 转录](https://www.fool.com/earnings/call-transcripts/2026/11/09/constellation-energy-ceg-q3-2026-earnings-call-transcript/) `[KNOWN-二手, MED]`。价格是 yfinance 日线收盘 `[KNOWN, HIGH]`。演示稿的文字是从 HTML 文本层提取的，**图片里的图表数值可能漏读** `[MED]`。

| 关键数据（2026-11-10 收盘） | 数据 | 备注 |
|---|---|---|
| 股价 | **$267.76** | 11/9 +10.5%（$249.95 → $276.09），11/10 −3.0%；10/9 $298.07 → **−10.2%** |
| 市值 | **~$94.1B** | $267.76 × **3.516 亿股**（10-Q 封面 dei:EntityCommonStockSharesOutstanding 351,608,504）`[COMPUTED, HIGH]`；10/10 档 ~$105.6B |
| Q3 调整后 EPS | **$5.06**（去年 $3.04，+66%）；GAAP $5.19（$2.97） | 一致预期 $3.85（[Investing.com](https://in.investing.com/news/stock-market-news/earnings-call-transcript-constellation-energy-tops-q3-2026-forecasts-shares-rise-93CH-5691371) 转述，二手单一来源，`LOW-MED`） |
| FY26 指引 | **$12.50–12.80**（原 $11.50–12.50；三月初始 $11.00–12.00） | 中点 $12.65 ⇒ 现价 / 中点 ≈ **21.2x** `[COMPUTED]`；10/10 档按共识 $11.91 算是 25.0x |
| 稀释股数 | Q3 3.54 亿（去年 3.13 亿，+13%，Calpine 发 5,000 万股）；全年指引口径 3.56 亿 | 9M 回购 ~1,090 万股 / ~$30 亿 |

### 门控检验（11/6 周复盘写死，逐条）

| # | 门槛 | 判定 | 一手原文依据 | 最强反方读法 |
|---|---|---|---|---|
| 1 | FY 调整后 EPS 指引维持或收窄到上半部 = 过 | **过** `[KNOWN, HIGH]` | EX-99.1：「Raising midpoint and narrowing full-year Adjusted (non-GAAP) Operating Earnings guidance range to $12.50 - $12.80 per share」。新区间下沿 = 原区间上沿，股数口径 357 → 356 百万，基本没变 | **上调的部分全是 Q3 一个季度的超额，而且是「enhanced」层。** 9M 调整后 EPS ≈ $2.74 + $2.55 + $5.06 = $10.35（Q1 的 $2.74 来自本档 6/29 节的二手数据）⇒ Q4 隐含 **$2.15–2.45**。财报前一致预期 FY $11.91（10/9）减去 Q1–Q3 共识 ⇒ 共识隐含 Q4 ≈ $2.77。**也就是说，管理层把 Q3 多赚的约 $1.21 只上调了 $0.65 中点，对 Q4 的口径实际是比街上低的** `[COMPUTED, LOW-MED，两个共识数都是二手]`。三月给的 2026 base 是 $6.65–6.75；在 $12.65 中点下，enhanced 占比 ≈ **47%**，超出公司自己说的「30–40%」区间 `[COMPUTED, MED，假设 base 没有重估]`。CFO 原话：「I wouldn't say that is transferable to all years」（二手）。**门槛是按「维持或收窄」这个字面写的，所以判过；但它证明的是 2026 年的波动捕获，不是可以重复的基础盈利。** |
| 2 | 新 PPA 单价 ≥ 现有（Amazon / Google）= 过 | **无法判定** `[KNOWN, HIGH 没有披露]` | 本季确实有新签：Peak+ 270 MW / 20 年 / 2028 起，「unit-contingent energy, capacity, and attributes from our existing nuclear fleet」，**没有价格**；演示稿 p5 写「~4,560 MWs contracted with three customers in Q3」（690 + 890 + 2,700 + 270 = 4,550 `[COMPUTED]`），都**没有单价**。唯一的价格信息是一个区间：p7/p13 写「$20 - $50/MWh premium nuclear pricing to PTC floor」，**和 Q2 演示稿 p13 一字不差**。p25 的「Contracted Clean $/MWh」路径（2026 $70 → 2028 $77 → 2030 $88）脚注写明「do not include PPAs signed in 2026」。**现有的 Amazon/Google 两张单本身也从没披露过单价，所以「≥ 现有」这个比较两边都没有数。** | **偏过的一侧**：溢价区间没有下调；YTD 长协约 8,500 MW；2032 年长协覆盖率从 Q2 的「~30%」升到「45%」；91% 的交易对手是 AA- 或以上。签约的量和信用质量都在变好，没有降价迹象。**偏不过的一侧**：① 新签的结构在变「软」：Google 那 2,700 MW 是「15-year financial energy load following agreement」，是金融合约不是实物 PPA；Peak+ 是用存量机组、按机组发电量交付（unit-contingent）；② CEO 在同一个电话会上说「utilities and grid operators … massive overestimation」以及「another 6 or 7 years' worth of stranded capacity」（二手）——**如果闲置容量有六七年，买方就不缺电，稀缺溢价理应被压**。两边都只是推断，没有一个数字能把它们分开。 |
| 3 | 得州项目无延期 = 过 | **无法判定** `[KNOWN, HIGH 10-Q 原文；INFERRED, MED]` | 10-Q 对得州项目只写了已发生的里程碑：Pin Oak Creek 460 MW 燃气调峰机组 2026-04 投入商运；Freestone 与 CyrusOne 签 380 MW（Q1）+ 二期 380 MW 独家协议；Thad Hill 400 MW（2025 下半年由 Calpine 签）。**全文没有出现「Abbott / pause / audit / Batch Zero」**，Part II 1A 写「our risk factors were consistent with the risk factors described in our 2025 Form 10-K」。电话会没有分析师问得州；CEO 只提到「reasonable safeguards in places like PJM and Texas」「combined cycle machines and ERCOT … vastly underutilized」（二手）。背景：8/3 Abbott 令 PUCT/ERCOT 审计大负荷接入队列，ERCOT 暂停给大型计算负荷通电审批，审计报告约 12/10（[Utility Dive](https://utilitydive.com/news/texas-hits-pause-data-center-interconnections/827046)、[NBC DFW](https://www.nbcdfw.com/news/local/texas-news/data-center-approvals-in-texas-halted-until-audits-completed-gov-greg-abbott-says/4058445/)，二手 MED；12/10 这个日期只有单一来源，`LOW`） | **偏过的一侧**：一份 11/9 提交、带 SOX 认证的 10-Q 没有披露延期；已签的 CyrusOne 协议写成「provides access to power, grid connectivity」，是 CEG 卖电和场地，延期成本主要在开发商那边。**偏不过的一侧（我认为更强）**：① 暂停已经三个月，正好覆盖 Freestone/Thad Hill 这种 ERCOT 大负荷，10-Q 里却一个字都没有——这是**没有写**，不是**写了放行**；② 一手数字显示，得州商业电价这条腿本季在变坏：原有 ERCOT 分部 RNF Q3 **$345M vs $415M，−17%**（9M −7%），MD&A 写「no individually significant drivers」；ERCOT-North **2027 全时段火花价差远期 $21.85（6/30）→ $17.26（9/30），−21%**，高峰时段 $24.62 → $19.32，−22%，同期 PJM-W 2027 年远期 +13.5%。ERCOT 燃气 base 是 2027 年 6,800 万 MWh、按 $22 价差。**粗算：ERCOT 价差每 $1/MWh ≈ $0.15 EPS（税后、未计对冲）**，2027 年远期这一个季度跌掉的 $4.6 如果全额兑现，约 $0.65 EPS `[COMPUTED, LOW——全时段价差 ≠ 机组实际捕获价差，对冲比例未披露]`；③ Q2 演示稿 p13 里「Enhanced Opportunity：$1–$3 power price and spark spread increase → $0.45–1.35」这一行，**到 Q3 版被删了**，同时删掉的还有 FCFbG 2026–27 $84 亿 / 2028–29 $115–130 亿的目标数 `[KNOWN, HIGH 两版对照；为什么删 = INFERRED, LOW-MED，也可能只是改版]` |

**门控合计：1 过 + 2 无法判定。** 11/6 规则是「三过二 → 分支 B 可选；不满足就不开」。**「无法判定」不算过**，所以分支 B 的前提不成立。门控 2 是题目本身写坏了（比较对象不可观测），下面的证伪条件给了一个可观测的替代口径。`[INFERRED, HIGH 规则对照]`

### 对账：上季指引 vs 本季实际 `[KNOWN, HIGH 一手]`

| 项目 | Q2（8/6）指引 / 说法 | **Q3 实际** | 判定 |
|---|---|---|---|
| FY26 调整后 EPS | $11.50–12.50（股数 3.57 亿） | **$12.50–12.80**（股数 3.56 亿），区间宽度 $1.00 → **$0.30** | 收窄并整体上移；Q4 隐含 $2.15–2.45（见门控 1 反方） |
| Q2 给的上调理由 | 「Commercial business outperforming plan … higher realized customer margins … share repurchases … partially offset by higher O&M due to performance related compensation」 | Q3：「Commercial outperformance in a volatile market … partially offset by higher O&M due to commercial outperformance」 | **兑现**，同一机制，但这个机制属于 enhanced 层 |
| 「On path to regulatory clarity in PJM in 2H 2026」（Q2 p5） | — | PJM 一次性可靠性兜底采购：FERC 9 月接受但暂缓到 **2027-02-28 生效**，PJM 10/29 重新提交，**2027-03-01 至 03-28 开放、05-10 公布结果**；Q3 演示稿 p8：「Regulatory goals are clear, although rules are not final」 | **未兑现，滑到 2027 年**（第 1 次） |
| Crane 重启 | 「restarting operations in 2027」；NRC 燃料许可已批、FERC CIR 豁免已批 | 10-Q 没有给日期；电话会：「on track to restart the plant in the second half of 2027, a full year ahead of schedule and under budget」（二手） | **未变**。10-Q 另记 PJM Phase I 研究的部分输电升级「as late as December 2030」，CIR 转移就是为了绕开这一点 |
| 长协覆盖率 | 「~30% of Expected Baseload Clean Generation MWhs under Long-Term Agreement by 2032」 | 「Long-term agreements support **45%** of the clean baseload fleet by 2032」 | **超额兑现**（Amazon + Google 两张单） |
| Brazos Valley 剥离 | 年底前完成 | **10 月完成**，$8.6 亿，Q4 预计收益约 $2.5 亿（不计入调整后 EPS 的剥离项） | 兑现 |
| PJM 五座燃气电厂剥离（4.4 GW，$50 亿） | 年底前完成 | 仍「expected to occur by the end of this year」 | 悬空 |
| capex 指引 | **未取得 Q2 的数字化 capex 指引**（Q2 演示稿文本层里没找到） | 9M capex $34.61 亿（去年 $19.63 亿）；「$1.3B uprate investment already included in 2026–2027 growth capital guidance」；2028–32 新增增长型资本支出约 $30 亿 | **对账缺失** |

**可信度**：五条里兑现四条，一条（PJM 规则落地）滑期。滑期的原因在 FERC/PJM，不在公司执行。**不下调**，但「监管时间表」这一项记 1 次。`[INFERRED, MED-HIGH]`

### 分部驱动：同比增长里多少是并表、多少是有机 `[KNOWN, HIGH 一手 Note 5；COMPUTED, HIGH]`

RNF（营收减购电与燃料，公司的分部考核指标），Q3：

| 分部 | Q3'26 | Q3'25 | 变化 | 10-Q 归因 |
|---|---|---|---|---|
| Mid-Atlantic | $1,027M | $892M | **+15%** | 零售负荷单价上升 +$160M |
| Midwest | $932M | $943M | −1% | 电价带来发电收入 +$175M，被 **PTC 收入 −$105M**、CMC −$55M、输电成本 +$175M 抵消 |
| New York | $412M | $399M | +3% | 无单项重大因素 |
| **ERCOT（原有）** | **$345M** | **$415M** | **−17%** | 「no individually significant drivers」 |
| Other Power Regions | $260M | $343M | −24% | 西部电价下降、新英格兰负荷下降 |
| **Calpine（新并表）** | **$1,927M** | — | — | 并表 |
| Other（含未实现损益） | $247M | $11M | — | 未实现净额 +$120M vs −$131M |
| **合计** | **$5,150M** | **$3,003M** | **+71.5%** | |

- **并表 vs 有机**：RNF 增量 $21.47 亿里，Calpine 占 **$19.27 亿（≈90%）**；原有五个分部合计 $29.76 亿 vs $29.92 亿 = **−0.5%**；加上 Other 并剔除未实现损益，$31.03 亿 vs $31.34 亿 = **−1%**。**原有业务利润同比持平略降。** 10-Q 原文：「it is impracticable to determine Calpine's earnings since the Acquisition Date」——公司自己也不给 Calpine 的利润。CFO：「Accretion from Calpine is the key driver of higher year-over-year Q3 results」（二手）。
- **备考口径**（10-Q Note 2，假设 Calpine 2025-01-01 就已并入）：Q3 营收 $95.50 亿 vs $94.46 亿 **+1.1%**；GAAP 净利 $18.35 亿 vs $15.50 亿 **+18%**；按备考股数（3.13 + 0.50 亿）算每股 **+21%** `[COMPUTED, MED，GAAP 含 MTM/税项噪声]`。和调整后 EPS 标题上的 +66% 差很多。
- **一次性成分**：① Q3 商业波动捕获（enhanced），CFO 自己说不可迁移；② 税项：GAAP 有效税率 18.2% vs 33.4%，调整后口径已剔除 $1.08 亿的递延税调整；③ 2026 年数字里含**即将剥离的 PJM 4.4 GW 燃气资产**的贡献（p23 脚注 5「include earnings contribution from assets to be divested in 2H 2026」），2027 年会消失，部分由 RISEC 609 MW 补上。
- **核电运营**：Q3 发电 46,677 GWh vs 46,477（+0.4%），容量因子 97.2% vs 96.8%；9M 停机天数 231 vs 179（换料多）。PJM West Q3 参考电价 $69.97 vs $46.77（+50%），ERCOT North $34.41 vs $35.05（−2%）。**电价上涨对核电的弹性被 PTC 回吐掉了一部分**（Midwest −$105M PTC），这是 PTC 托底的另一面：价格在 $26–44.75 之间时，PTC 等于把上行让渡掉。
- **资本配置方向**：卖 PJM 燃气 4.4 GW，$50 亿 ≈ **$1,136/kW**；买 RISEC 609 MW，$7.15 亿 ≈ **$1,174/kW**，原文「expected to become part of our merchant generation portfolio」`[COMPUTED, HIGH]`。**公司在主动加商业燃气敞口**，和「长协核电年金」的叙事方向相反。

### 现金流 vs 利润 `[KNOWN, HIGH；COMPUTED, HIGH]`

- 9M OCF **$49.79 亿** vs 净利 $39.46 亿（1.26x）；Q3 单季 OCF ≈ $34.26 亿（9M − 6M $15.53 亿）vs 净利 $18.35 亿。H1 OCF < 净利、Q3 > 净利，主要是营运资本季节性（9M 应付 −$10.99 亿、其他 −$6.99 亿）。非现金项：衍生品公允价值 −$7.76 亿（利润里有、现金里没有），递延税 +$9.32 亿。**没有异常。**
- 存货：资产负债表 $17.36 亿 → $33.86 亿，但现金流量表的存货变动只有 −$1.81 亿 ⇒ 增量基本来自 Calpine 并入，**不是积压** `[INFERRED, MED-HIGH]`。应收同理（现金流量表 +$4.62 亿回收）。
- **资本回报的资金来源**：9M FCF（OCF − 全部 capex）$15.18 亿 < 回购 $30.01 亿 + 股息 $4.59 亿 = $34.60 亿，**缺口约 $19 亿**由现金消耗（$36.41 亿 → $6.03 亿）+ 短期借款净增约 $23 亿弥补；长债发行 $50.01 亿、偿还 $54.60 亿，净减少。Q3 单季 FCF ≈ $24.86 亿 > 回购 $10.30 亿，单季自己覆盖得了。Q4 有 $58.6 亿剥离款（Brazos 已收 + PJM 待收）用于去杠杆。**没有发股（Calpine 对价股除外），所以不算「⑥ 融资结构信号」；但 YTD 资本回报超过 FCF，靠资产出售回补。** `[INFERRED, MED]`
- 杠杆：总债务（短借 $39.89 亿 + 一年内到期 $3.59 亿 + 长债 $190.39 亿）= **$233.9 亿**，年初 $89.9 亿；净债务约 $228 亿。p18：长债 $195 亿（CEG $145 亿 / CPN $49 亿）。评级 **BBB+ / Baa1**（10-Q：「it would take a three-notch downgrade … to go below investment grade」）。p12 写「2.00 - 2.25x Debt/EBITDA」，**是目标还是实际没说清，实际倍数未披露**（待核实）。DOE 有条件贷款承诺 $50 亿（30 年，国债 +37.5bp，用于功率提升），Crane 的 $10 亿 DOE 贷款**尚未提款**。持有待售资产 $56.61 亿，原文「No impairment」。

### 指引口径

- 口径没换（仍是调整后营业 EPS），股数口径 3.57 → 3.56 亿。**区间宽度 $1.00 → $0.30**，到 Q3 收窄是正常的。
- **2027/28 指引没有更新**，推到年终电话会：「we will update our 2027 and 2028 guidance on our year-end call, including a refreshed growth outlook through 2030」（二手）。p14 保留了「Base EPS* growth of 20%+ from 2026 - 2029」和「rolling three-year Base EPS growth of 10%+」。
- **Q3 演示稿删掉的两项**（对照 Q2 p13）：「$1–$3 power price and spark spread increase」这一行 enhanced 上行项，以及 FCFbG 2026–27 $84 亿 / 2028–29 $115–130 亿。删除不等于撤回；但发生在 ERCOT 远期价差 −21% 的同一个季度。**翻译回数字：管理层不再把「电价/价差上涨」列为 2029 年的上行来源。** `[KNOWN 删除；INFERRED, LOW-MED 含义]`
- 形容词核对：「Strong 20%+ Growth through 2029」= base 口径，基数 $6.65–6.75（三月）⇒ 2029 年 $11.40–11.90 base，和 p21 能对上；**它说的是 base，不是总 EPS**，2026 年总 EPS 是 $12.65。如果 2029 年 enhanced 回到 30–35%，2029 年总 EPS ≈ $16–18 `[COMPUTED, LOW]`。

### 股价反应归因 `[KNOWN, HIGH 价格；INFERRED, MED 归因]`

- 路径：11/3 $263.40 → **11/4–5 两天 −9.0%**（$239.65）→ 11/6 +4.3% → **11/9 +10.5%**（$276.09）→ 11/10 −3.0%（$267.76）。**进财报前没有抢跑**（前一周是下跌）。
- 同日对照（11/9）：VST +7.3%、TLN +7.2%、SOXX +7.5%、S&P +2.3%、XLU +1.5%。CEG 比 IPP 同行**多涨约 3 个百分点**。11/3 → 11/10 这一段：CEG +1.7%、VST −6.0%、TLN +1.1%。**VST（得州敞口最重）跑输**，和「市场在给 ERCOT 敞口定价」这个读法一致。
- **结论：无法干净归因，偏 beta。** 11/9 的 +10.5% 里约 7 个点是 AI 电力 + 半导体同步反弹（SOXX 同日 +7.5%），约 3 个点可以归给指引上调。这和「被卖的是抢跑后的 beat」「被卖/被买的是基本面」两种读法都不同。**VST/TLN 11/9 当天是否也有自己的消息，没核** `[待核实]`。

### 论点对账（对照 6/29、10/10 两节的退出条件与跟踪信号）

**退出条件 0/4 触发**：① 没有 PPA 被取消或重谈；② Crane 没有取消（2H27 维持，二手）；③ 指引上调，不是下调；④ 评级 BBB+/Baa1 维持，持有待售资产无减值。`[KNOWN, HIGH]`

1. **证实：「长协簿变厚」（10/10）。** 2032 年覆盖率 30% → 45%，YTD 约 8,500 MW，交易对手 91% 在 AA- 或以上。`[KNOWN, HIGH]`
   - **裂缝**：覆盖率的分母是「clean baseload」（核电 + 地热），**不含 Calpine 的燃气**。合并后公司 55 GW 里，燃气这一块的长协覆盖率公司没给。门控 3 担心的正是这块（ERCOT 燃气 base 6,800–7,100 万 MWh）。45% 这个数字答的是核电那一半的题。
2. **证实（加限定）：「Calpine 并表 + 商业 margin 驱动」（Q2）。** 并表是真的，商业 margin 也是真的；**但原有业务 RNF 同比 −1%**，增长几乎全部来自并表 + 波动捕获。`[COMPUTED, HIGH]`
   - **裂缝**：解释不了的是 **PJM West 电价 +50%、容量价格 $329 vs $270，原有 Mid-Atlantic + Midwest 合计只 +6.8%**。机制有三个候选：PTC 回吐、零售侧按旧合同价锁定、对冲在低价位锁定（Mid-Atlantic 已实现对冲 −$70M）。**哪个是主因决定了 2027 年对冲滚动后的弹性**，10-Q 的口径分辨不出来。
3. **未证实也未证伪：「AI 数据中心 = 核电稀缺溢价」。** 溢价区间 $20–50/MWh 没变、量在涨；但 CEO 自己说了「massive overestimation」和「6 or 7 years' worth of stranded capacity」（二手）。`[INFERRED, MED]`
   - **裂缝**：CEO 这句话有两种读法，现在分不开。(a) 他在为「用存量机组服务数据中心、不用新建」游说，这对拥有存量机组的人是**利多利用率**；(b) 这承认了负荷预测是虚的，稀缺溢价的分母被高估了，对**新签单价**利空。领先信号层面（memory `market-adoption-leading-signal`）：真正的数据中心负荷采用率要看 ERCOT 12/10 的审计结果和 PJM 2027-05-10 的兜底采购结果，财报给不了。
4. **新增风险（本季读出来的）：得州商业电价腿在一手数据里变坏。** 原有 ERCOT RNF −17%，2027 年远期火花价差 −21% 并跌破公司 base 假设，管理层删掉了「电价/价差上行」那一行，同时还在买商业燃气（RISEC）。`[KNOWN, HIGH 数字；INFERRED, MED 合成]`
   - **裂缝**：Calpine 的得州机组在 Calpine 分部里，**不按地区拆**；对冲比例没有披露；全时段价差不等于调峰机组的实际捕获价差（Pin Oak Creek 是调峰机组，只在价差高时开机）。所以 $0.15 EPS / $1 价差的敏感度**是上限，不是估计**。另外，Q3 公司在「volatile market」里赚到了超额——**波动本身对 CEG 是收入**，火花价差均值下降不一定意味着 enhanced 盈利下降。11/6 写的「Calpine = 商业电价敞口」是对的，但它**不是单向**的。

**价格词检查**：四条复述——「核电长协覆盖率升到 45% 但不含燃气」「原有业务利润持平，增长来自并表和波动捕获」「数据中心负荷预测被 CEO 自己称为高估」「得州燃气价差远期下降、公司删掉电价上行项、同时加商业燃气」——**全是公司词**。11/6 那句「两天 −9%」是价格词，本节没有用它当论据。✅

**净结论**：论点未变（退出 0/4），**但成分更清楚了**：CEG = 「45% 长协核电（2032）+ 一个靠波动赚钱的大型商业燃气 + 零售平台」。2026 年的超额来自后一半，而 11/6 的门控担心的也是后一半。门控按写死的规则**没有过**。`[INFERRED, MED-HIGH]`

### 可选动作（只在周复盘窗口执行，下一个是 11/14–15；动作归 position-discipline）

- **不动（默认）** = 继续作为 context / 观察标的，零仓位。到下个窗口的后果：如果 ERCOT 审计（约 12/10）放行、或 2027 年指引给出 base ≥ $7.60，错过的是一个 1% 试探仓的涨幅，对组合影响 < 0.3 个点 `[COMPUTED, LOW]`；如果得州暂停延续到 2027 年立法会期，或 2027 年指引的 enhanced 回吐，避开的也只是 1% 仓位的下跌。**不动的代价不对称地小。**
- **分支 B（CEG 1% 试探仓）**：**前提不成立**（1/3 过）。
- **替代门控（建议写进本档，替换原门控 2/3）**：见证伪条件表里的「YE 合同价格路径」和「ERCOT 审计 + 10-K 得州披露」两行。三项可观测的门控都在 **2027-02 年终电话会**开奖，这就是下一个真正的窗口。
- **不在选项里的**：对 CEG 卖 put（第七问：「跌到 $240 接货」是价格词，没有公司词前提；且 11/9 单日涨幅约为 SOXX 的 1.4 倍，高 beta `[COMPUTED, LOW 单日]`）；任何 long call。

### 三档（12 个月，`[GUESS]` 概率；算术 `[COMPUTED, LOW]`；基准 $267.76）——估值和概率以 probability-analyst 为准，这里只做情景的成分描述

| 档 | 概率 | 情景（公司会发生什么） | 粗算 |
|---|---|---|---|
| 悲观 | 25% | ERCOT 暂停延续进 2027 立法会期，Freestone/Thad Hill 在 10-K 里出现延期；2027 年总指引中点 < $12（enhanced 回吐到 30% 且 ERCOT 价差按远期落地）；YE 更新后的 Contracted Clean 2030 价格 < $88 | 18x × $11.5 ⇒ **~$205，−23%** |
| 基准 | 55% | 2027 年 base $7.60–7.70 兑现，总 EPS $12.5–13.5；得州审计带条件放行；Crane 2H27 维持；PJM 剥离年底完成，杠杆回到 2.0–2.25x | 20–22x × $13 ⇒ **$260–285，−3~+6%** |
| 乐观 | 20% | 新增 ≥1 GW 长协且披露或可推出单价落在溢价区间上半段；PJM 2027-05 兜底采购让存量核电拿到长期容量合约；2027 年指引 ≥ $14 | 23x × $14.5 ⇒ **~$335，+25%** |

期望值 ≈ 0.25×(−23%) + 0.55×(+1.5%) + 0.2×(+25%) ≈ **+0%**——与「门控未过、不开仓」一致。

### 证伪条件（阈值 + 开奖日期）

| 条件 | 阈值 | 开奖 | 触发什么 |
|---|---|---|---|
| **替代门控 2：新合同单价（可观测版）** | 年终更新的「Contracted Clean」价格路径（p25 脚注：每年更新，本次不含 2026 年签约）**2030 年 < $88/MWh** 或 2028 年 < $77 ⇒ 2026 年新签单价低于存量均价 | Q4 财报 / 年终电话会（~2027-02，日期待核） | 门控 2 判不过；「稀缺溢价」论点降级 |
| 溢价区间 | 演示稿「$20–50/MWh premium to PTC floor」**下调**（任一端） | 每季演示稿 | 同上 |
| **替代门控 3：得州** | ① PUCT/ERCOT 审计（约 2026-12-10，单一来源）后暂停延续到 **2027-01-12**（第 90 届立法会期开幕，按奇数年 1 月第二个周二推算 `[COMPUTED]`）之后；**且** ② 10-K 或 Q4 电话会披露 Freestone / Thad Hill 时间表后移 | 2026-12-10 / 2027-02 | 门控 3 判不过；Calpine 得州腿从「敞口」改判为「受损」 |
| ERCOT 价差 | 演示稿「ERCOT – N ATC Spark Spread」2027 年远期 **< $15**（9/30 $17.26），或公司把 ERCOT base 价差从 $22 下调 | Q4 演示稿 ~2027-02 | 商业燃气 base 盈利下修 |
| Q4 兑现 | Q4 调整后 EPS **< $2.15**（FY < $12.50） | ~2027-02 | 指引可信度记一次不兑现 |
| 2027 年指引 | 年终给出的 2027 年 **base < $7.60**（三月口径 $7.60–7.70），或**总 EPS 中点 < $12.65**（低于 2026 年） | ~2027-02 | 「20%+ base 增长」论点下修；2026 年被定性为波动年 |
| Crane | 重启日期后移出 2027 年（记一次）；**取消**（退出条件 ②） | Q4 电话会 / NRC 里程碑 | 退出条件 ② |
| 杠杆 | PJM 4.4 GW / $50 亿剥离 **2026-12-31 前未完成**；或评级任一下调 | 2026-12-31 / 随时 | 短借 $40 亿滚动，退出条件 ④ 观察 |
| PJM 兜底采购 | 2027-05-10 结果：CEG 存量核电**没有**拿到长期容量合约，或机制被 FERC 驳回 | 2027-05-10 | 「监管清晰」第 2 次滑期 ⇒ 管理层监管时间表可信度下调 |
| 正向（论点被证实） | YE 更新后 Contracted Clean 2030 价格 **≥ $88** 且长协覆盖率 > 45%，且 ERCOT 审计放行、得州项目无延期 | 2027-02 | 门控三项重新判定；如果过两项，分支 B 可以在 2027-02 窗口重提 |

### 下一季度要盯的
年终电话会的 2027/28 指引（base / enhanced 拆分）；更新后的 Contracted Clean 价格与量（含 2026 年签约）；ERCOT base 价差假设与远期；PJM 剥离完成与债务偿还（短借 $39.89 亿）；Debt/EBITDA 实际值；回购授权更新（「on or before the fourth quarter call」）；Crane 里程碑；PUCT 第 59220 号案卷 12/10 审计；Freestone / Thad Hill 的接入状态；PJM 兜底采购 2027-03 开放 / 05-10 结果；RISEC 交割。

### 待核实 / 我不知道的
- **Q3 一致预期 $3.85** 只有 Investing.com 一个二手来源；**FY 共识 $11.91** 是 10/9 的数，财报前是否改过不知道 ⇒ 「Q4 隐含低于街上」这一条是 LOW-MED。
- **Q1 调整后 EPS $2.74** 来自本档 6/29 节（二手），本次没有回 Q1 8-K 核对。
- **Q4'25 调整后 EPS** 没取得，所以 Q4 隐含的 $2.15–2.45 没法做同比。
- **Q2 的 capex 指引数字**没取得，capex 对账缺失；p11/p14 的「$3.9B growth capital」口径期间不明。
- **Debt/EBITDA 2.00–2.25x 是目标还是实际**，演示稿没说清。
- **Calpine 得州机组的 MW / 发电量**、商业燃气的对冲比例：公司不按地区拆 Calpine 分部。
- **Peak+ 的交易对手和价格**；Google 2,700 MW 金融负荷跟踪合约的定价：都没披露。
- **得州暂停的 11 月状态**：只找到 8 月的报道（8/3 令、约 12/10 审计报告）；PUCT 第 59220 号案卷原文没读。
- **VST / TLN 11/9 当天是否有自己的消息**：没核，所以「~3 个点超额」这个归因是 LOW。
- 演示稿是**图片 + 文本层**，图表里的数值可能漏读；「删除了电价上行行和 FCFbG 目标」是基于文本层对照，**有可能藏在图片里**（MED）。
- 电话会全部引述来自 Fool 二手转录，「well within the $110 to $130 range」那句的上下文不完整，没有采用。

---

## 一句话定位

核电运营 + AI DC 电力——美国最大的核电运营商。已与微软等签订专属电力 PPA。

## 关键数据（基准 2026-10-09，**11/10 最新值见顶部 Q3'26 财报对账节**；scripts/fetch_quotes.py 快照 + 一致预期 WebSearch；6/29 旧值在备注列）

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$298.07**（10/9 收盘） | 6/29 $264 → **+12.9%**；10/6 单日 +12.2%（Google PPA）；10/7–8 利率杀 −4.8% 后 10/9 +4.6% 收复 |
| 市值 | **~$105.6B** | 6/29 ~$94B |
| trailing PE | 29.1 | 快照；6/29 22.9 |
| **forward PE（自算）** | **25.0x（FY26 共识 EPS $11.91）/ 22.3x（FY27 $13.34）** | 快照 fwd 22.4 是 FY27 口径；6/29 自算 19.5 对应当时 $264 / 旧指引中点 |
| 2026 指引 | **$11.50–12.50**（8/6 上调，原 $11–12） | 共识 $11.91 落在区间下半部 |
| 52 周区间 | $228.6 – $412.7 | 距高 **-27.8%**（6/29 时 -36%） |
| vs 50/200DMA | 50DMA $273.3 / 200DMA $286.4 | 已站回 200 线上方 +4%（6/29 时 -17%） |
| 下次财报 | ~~Q3'26：2026-11-06~~ → 实际 **2026-11-09 盘前已发**（见顶部对账节）；Q4 / 年终电话会 ~2027-02（日期待核实） | FY26 指引已上调到 **$12.50–12.80** |

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
| 2026-11-11 | Q3'26 财报对账，不动 | $267.76 | 无 | 11/6 写死的三项门控：指引过（$12.50–12.80）、新 PPA 单价无法判定、得州无法判定 ⇒ 不满足「三过二」，分支 B（1% 试探仓）前提不成立；原有业务 RNF 同比 −1%，增量 ~90% 为 Calpine 并表；ERCOT 2027 火花价差远期 −21%；退出条件 0/4 |

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

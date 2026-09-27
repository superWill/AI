---
ticker: BE
name: Bloom Energy
sector: AI 数据中心现场供电 / 固体氧化物燃料电池（SOFC）
layer: Layer 6 — AI 基础设施（电力）：并网排队与燃机交期卡点的「速度溢价」卖方
position_type: thematic（候选，未持有）
status: watching
last_updated: 2026-09-25
data_source: 实测行情 2026-09-15（scripts/fetch_quotes.py）+ SEC 10-K FY2025 / 10-Q Q1–Q2'26 / 8-K（可转债、Hunterbrook 回应、S&P 纳入）+ 电话会转录（Motley Fool / Investing.com）+ SemiAnalysis 2025-12-30 & 2026-09-10 + Hunterbrook 做空报告两篇 + GEV/Siemens/CAT 财报 + IRS Notice 2026-15 + EIA STEO；两个研究子 agent 2026-09-16 拉取（WebSearch 配额耗尽，NOT FOUND 项见文末）
---

# Bloom Energy (BE)

## 一句话定位

卖的不是燃料电池，是**时间**：并网排队 5–7 年、燃气轮机槽位排到 2029–30，Bloom 55–90 天出电。2026 年靠 Oracle（最多 2.8 GW）、AEP（1 GW）、Nebius、Brookfield $25B 融资架子把它从「韩国补贴依赖的边缘玩家」变成 AI 现场供电的近独占者（燃料电池赛道内 Bloom 3.8 GW vs 其他 0.03 GW）。营收一年翻倍、毛利 28%→34%、9/21 进 S&P 500。**但 $76B 市值 = 24.6x 销售，已经把 2031 年 40–57% 的营收 CAGR 定价进去了**；单一客户占上半年营收 73%，保修计提半年翻 7 倍，内部人 2026 卖出 $1.1 亿零买入，做空报告直指钪供应链和电堆寿命。这是组合最不需要的东西：一只 beta 3.8 的 AI capex 纯多头。

## 关键数据（基准 2026-09-15 收盘，scripts/fetch_quotes.py 实测 + stockanalysis.com 交叉）

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$266.65**（9/24 收，force majeure 日 −3.1%；9/15 $259.35）| 距 6/25 历史高点 $351.28 **−26%**；7/29 曾跌至 $157（−52%）后 V 型回来 `[KNOWN]` |
| 市值 | **$76.4B** | EV ≈ $76.2–76.5B（现金 $2.67B ≈ 追索债务 $2.48B）`[KNOWN]` |
| TTM PE | **332**（yfinance）/ 292（stockanalysis） | TTM 净利 $245M，口径无意义 |
| Forward PE | **52.6**（FY27E $4.93）/ 95.7（FY26E $2.71） | `[COMPUTED]` |
| Forward P/S | **18.6x**（FY26E $4.12B）/ 11.3x（FY27E $6.79B） | TTM P/S 24.5x；EV/EBITDA TTM 183x，2026E ~45x |
| 52 周区间 | $61.37 – $351.28 | 一年 **+286%**；2026 YTD 约 +150–220%（年初价口径不一，`(待核实)`）|
| Beta | **3.81** | 5 年对 SPY。对组合的 SOXX 因子是**加杠杆**，不是分散 `[INFERRED]` HIGH |
| 股数 | 294.5M（2026-07-22） | 2024-02 225.0M → **+27.8%**；转债 $2.5B @ $194.97 已在价内 `[KNOWN]` |
| 空头 | 19.2M 股 / 6.6% float | 1.5 天回补，借券成本 0.3%，不算拥挤 `[KNOWN]` |
| 股息 | 无 | |

## 财务（FY2025，截至 2025-12-31；SEC 10-K + 8-K 2026-02-05）

| 项目 | FY2025 | FY2024 | 同比 |
|---|---|---|---|
| 总营收 | **$2,024M** | $1,474M | +37.3% |
| 其中产品 / 安装 / 服务 / 售电 | $1,531M / $204M / $228M / $60M | | 产品占 76% |
| 毛利率 GAAP / non-GAAP | 29.0% / 30.3% | 27.5% / 28.7% | +150 bps |
| 服务毛利率（GAAP，Q4） | **16.9%** | −1.7% | 十年首次持续转正 |
| 营业利润 GAAP / non-GAAP | $72.8M / $221.0M | $22.9M / $107.6M | non-GAAP 翻倍 |
| Adj. EBITDA | $271.6M | $160.7M | 2021 年 $14M → 5 年 19 倍 |
| GAAP 净利 / EPS | **−$88.4M / −$0.37** | | 全年 GAAP 仍亏（转债置换 + SBC）|
| non-GAAP EPS（摊薄） | $0.76 | | |
| OCF / Capex / FCF | $113.9M / $56.8M / **$57.1M** `[COMPUTED]` | | 第二年 FCF 为正；Q4 单季 OCF $418M |
| SBC | $139.4M | | = 6.9% 营收 |
| 现金 / 追索债务 | $2,454M / $2,614M | | 净现金 ≈ 0 |
| Backlog（公司口径） | **~$20B**：产品 ~$6B + 服务 ~$14B | | ⚠️ 见「Backlog vs RPO」|
| 年初指引 vs 实际 | 营收 $1.65–1.85B → $2.02B；OI $135–165M → $221M | | 超上限 9%，2025 年每季上调 |

## 财务（2026 Q1–Q2 + 指引演变；Q3 财报约 10/27–29，公司未确认）

| 项目 | Q1'26（至 3/31） | Q2'26（至 6/30） |
|---|---|---|
| 营收 | **$751M（+130%）** | **$1,065M（+166%，环比 +42%）** |
| 产品收入 | $653M（+208%） | $935M（+215%）= 88% 营收 |
| 毛利率 GAAP / non-GAAP | 30.0% / 31.5% | **33.4% / 34.3%**（+668 bps YoY）|
| 分部毛利（non-GAAP） | 产品 35.3% / 服务 18.0% | 产品 37.2% / 安装 −1.4% / 服务 22.0% |
| 营业利润 GAAP / non-GAAP | $72M / $130M（17.3%） | **$182M / $240M**（22.5%）|
| GAAP 净利 / 摊薄 EPS | $70.7M / $0.23 | **$196.3M / $0.62** |
| non-GAAP EPS vs 共识 | $0.44 vs $0.13 | $0.78 vs $0.39–0.41 |
| 营收 vs 共识 | $751M vs $530M（+42%） | $1,065M vs $827M（+29%）|
| OCF / Capex / FCF | $73.6M / $26.2M / $47.4M | $226.4M / $51.6M / **$174.8M** |
| 现金 / 追索债务 | $2,491M / $2,599M | $2,667M / $2,471M |
| **应计保修** | — | **$20.0M（12/31）→ $77.8M（6/30）**；Q2 计提 = 产品收入 4.22%（去年 0.58%）|
| 性能保证付款 | — | H1 $13.8M，公司归因「fleet degradation」|
| 客户集中 | 两客户 ~50% + ~12% | **H1 单一非关联客户 73%**；Q2 两客户 44% + 21%（后者关联方）|
| 关联方收入 | — | H1 $376M = 20.7%（Brookfield JV）|
| RPO（10-Q 未履行履约义务） | — | **$442M** 产品+安装 + $52M 服务 |
| 股价反应 | 盘后 −3.5% → 次日 +22.5% | 当日 −11%（Hunterbrook 第二篇）→ 盘后 +12% → 次日回吐至 −2% |

**FY2026 指引三次上调** `[KNOWN]` HIGH：
- 2/5：营收 $3.1–3.3B / GM ~32% / non-GAAP OI $425–475M / EPS $1.33–1.48
- 4/28：$3.4–3.8B / ~34% / $600–750M / $1.85–2.25
- 7/28：**$3.9–4.2B（中值 +100% YoY）/ ~34% / $800–900M / $2.55–2.85**；OCF「$375M+」
- Sridhar Q1 原话：「not order constrained and not capacity constrained. The pace of our revenue growth is decided by how fast our customers can build their greenfield sites」→ 增速的约束在**客户的土建**，不在 Bloom。

## 技术与单位经济（为什么它能卖时间）

`[KNOWN]` MED，来源 ES 5.5 数据表 / 10-K / SemiAnalysis
- **产品**：330 kW 撬块，天然气 SOFC，电效率 BOL 65% → 全寿命 53%（LHV），公司口径「~60%」，比燃机省 15–20% 燃料。CO2 679–833 lb/MWh（CCGT 750–900，开式燃机 1,100+）：**对 CCGT 碳优势很小，对开式循环/往复机明显**。NOx 0.0017 lb/MWh ≈ 零，**不耗水，加州免空气许可**，Jupiter 走 minor source 路线。
- **部署**：Oracle 首站 55 天；Power Connect（2026-08）再降现场安装 40%+；全线 800V DC ready。
- **成本**：2023 末产品成本 ≈ $2,100/kW `[COMPUTED]`，2024 起不再披露。售价 $3,000–4,000/kW（SemiAnalysis）vs 航改燃机 $1,700–2,000 / 工业燃机 $1,500–1,800 / 往复机 $1,700–2,000——**Bloom 贵一倍，卖的是交期**。AEP $2.65B/1 GW ≈ $2,650/kW（含 20 年 offtake，口径不明）`(待核实)`。
- **LCOE**：~$0.09–0.10/kWh（Oracle 侧引述，单源 LOW）vs 微燃机 $0.07–0.08；燃料成本 ≈ $0.022/kWh @ Henry Hub $3.43 `[COMPUTED]`。
- **电堆寿命 = 服务毛利的分母**：公司称 2014–15 批次中位 4.9 年、最长 7.7 年；SemiAnalysis 估 5–6 年更换。**Hunterbrook（2026-07-30）用 NYSERDA/特拉华 PSC/加州 SGIP/EIA 公开监管数据称**：纽约 37 台中位 <3 年触及更换阈值、20 个月跌破 46.9% 效率保证线；特拉华 156 个月中 152 个月低于 95% 出力保证。做空方利益相关，**但数据源可复核，且 10-Q 保修计提翻 7 倍与之方向一致**。公司未回应第二篇。`[INFERRED]` MED
- **负荷跟随是多 GW 级的未验证项**：SOFC 靠超级电容吃阶跃负荷，SemiAnalysis 估 Jupiter 2.45 GW 需 ~1.6 GW 超容，现有先例仅 58 MW。「数百组电堆 + 超容 + BESS 的配置从未在此规模做过」。
- **氢已退出叙事**：SOEC 官网最新新闻 2021-07；2026 两次电话会未提氢。这只票 2026 年是纯天然气故事。`[INFERRED]` HIGH

## 护城河类型

**时间窗口 + 认证壁垒，不是技术垄断** `[INFERRED]` HIGH
- 真护城河：① 1.5 GW / 1,200 台的运行记录，hyperscaler 的供应商认证周期 1–2 年（Q2 PR：「所有美国主要 hyperscaler 及十余家 neocloud 已验证」）；② 燃料电池赛道内独占（Doosan 50 MW/年、FCEL/Plug 加起来 0.03 GW 订单）；③ 非燃烧 → 空气许可和水权两条监管路径比燃机短。
- 假护城河：「速度」。速度溢价存在的前提是燃机交期 3–5 年。GEV 产能 20 GW/年 → 24 GW（2028）→ 30 GW（2030），Siemens/MHI 同步扩产，**2028–29 若交期回到 12–18 个月，$3,000–4,000/kW 对 $1,500–2,000 的两倍价差失去支撑**。GEV CEO Strazik 已说「燃机其实不是卡点」。
- 为什么 3 年内追不上：不是别人做不出 SOFC，是**hyperscaler 不会在 2026–28 这个窗口换新供应商做认证**。窗口之后护城河要靠服务粘性（100% attach、5–20 年 O&M）和电堆更换收入，而这正是 Hunterbrook 攻击的地方。

## 竞争格局（2026）

| 方案 | 交期 | $/kW | 2026 状态 |
|---|---|---|---|
| **Bloom SOFC** | 55–90 天 | $3,000–4,000 | 3.8 GW 订单；Oracle/AEP/Nebius/Equinix |
| GEV / Siemens / MHI 燃机 | 2029–30 槽位 | $1,500–2,000（涨价中，2027 或 $600/kW 裸机 ×3）| GEV backlog 116 GW，年底 ≥125 GW |
| CAT / Wärtsilä / Jenbacher 往复机 | CAT 3600 系列 ~107 周 | $1,700–2,000 | CAT backlog $63B；2 GW 供 Monarch |
| 电池（Megapack / Fluence） | 短 | 只能做桥 | Google「强烈偏好作并网过渡桥」；SpaceX Q2 买 $295M Megapack |
| SMR | 2028+（Oklo）| — | 十年尺度 |
| 其他燃料电池 | — | — | 0.03 GW，非对手 |

`[KNOWN]` MED，来源 SemiAnalysis 2026-09-10 / power-eng / Utility Dive。
- 2025 年的大项目（xAI Colossus、Abilene、Meta Socrates、Vantage）**全用燃机/往复机，无 Bloom**；2026 起逆转（Oracle Jupiter 弃燃机+柴油改 Bloom，Nebius 取消燃机订单）。逆转的原因是**交期和许可**，不是 LCOE。
- 直接表态：Microsoft/Meta/Google 对燃料电池的公开表态 NOT FOUND；AWS 经 AEP Ohio 6 年合同 + Cologix 15 年间接使用。「Google 怀俄明 900 MW」仅 SemiAnalysis 单源，疑为 Crusoe/Tallgrass 项目的租户 `(待核实)`。

## 商业合同（已披露）

`[KNOWN]` HIGH 除标注
- **Oracle**：2025-07 首签（无规模）→ 2026-04-13 MSA **最多 2.8 GW，已签 1.2 GW**，部署至 2027；Project Jupiter 2.45 GW 独家供电，Oracle 承担全部能源成本。Oracle 持 3.53M 股权证 @ $113.28（已行权 2.15M 股，公允值 $324M 冲减收入）。**H1'26 那家 73% 的客户极可能是 Oracle**（公司未确认）`[INFERRED]` HIGH。
- **Brookfield**：2025-10 $5B → **2026-06-30 $25B**（Brookfield $100B AI 基础设施基金内），模式是 Brookfield 买资产做 PPA、Bloom 签客户 → Bloom 部分持股的 JV 是关联方，H1 关联方收入 20.7%。已部署 GW / 欧洲首站 NOT FOUND。
- **AEP**：2024-11 最多 1 GW，首单 100 MW；「$2.65B / 20 年 offtake」仅二手（Simply Wall St / fuelcellsworks），Bloom IR 无稿 `(待核实)`。已交付 MW NOT FOUND。
- **Nebius**：2026-05-20 首项目 328 MW（2026 投运）；CNBC 称 10 年 $2.6B 主协议（正文 403，单源）`(待核实)`。Industrial Development Funding（Oaktree/MUFG/MS）承诺 $2.6B 项目融资。
- **Equinix** >100 MW（2025-02）；**CoreWeave**（Chirisa，2025 Q3 投运，规模未披露）；**SK ecoplant** 500 MW 至 2027（2023 协议），**已于 2026-04 清仓全部 Bloom 股份**，韩国占比被稀释到 ~10%（美国营收占比 Q1'25 56% → H1'26 90%）。
- **Backlog vs RPO 的 45 倍差**：公司口径 ~$20B（产品 $6B + 服务 $14B）；10-Q 不可撤销履约义务只有 **$0.49B**。服务合同按 5–20 年计入 backlog 但含年度便利终止条款（Hunterbrook 指控）。**Backlog 是营销数字，RPO 是会计数字，两者差 45 倍是这只票信息质量的度量。**`[INFERRED]` HIGH

## 政策

`[KNOWN]` MED
- **48E ITC**：OBBBA（2025-07-04）给燃料电池 **30% ITC、取消 GHG 要求**，2025-12-31 后开工适用，2033 后退坡至 2036 归零。这是 2025 年 7 月 JPM 上调、股价起飞的起点。**Bloom 的经济性含 30% 补贴**。
- **FEOC / 材料援助（IRS Notice 2026-15）**：MACR 门槛 2026 40% → 2030 60%。燃料电池 ITC 生效日与 FEOC 规则生效日相同，**Hunterbrook 的中国钪路径若成立直接触及 ITC 资格** `[INFERRED]` MED。公司 8-K 回应「不依赖中国」「25 GW/年供应链可见度」，未逐条反驳。
- **韩国**：CHPS 2026 招标量 −30%，政府称 LNG 制灰氢燃料电池「不符合脱碳政策」→ 韩国这条腿在萎缩，已被美国 DC 替代。
- **天然气**：EIA STEO Henry Hub 2026 $3.43 / 2027 $3.28，库存高于五年均 5%。燃料由谁承担合同条款 NOT FOUND（Jupiter 由 Oracle 承担）。
- **接入规则**：FERC 2025-12 令 PJM 重写共址规则；德州 SB6 2026-07 首例裁定紧急切负荷不以 BTM 容量为上限。方向对现场供电有利。EPA 2026-01 燃机 NSPS 新增「临时」子类，对燃机松绑 → 对 Bloom 相对不利 `[INFERRED]` LOW。

## ⭐ 2026-09-24：Oracle 对 Project Jupiter 发 force majeure —— 退出条件①的前兆 `[核实 2026-09-25，TechCrunch 9/24]`

- **事件**：Oracle 就 Project Jupiter（新墨西哥 Stargate 园区，**2.45 GW，Bloom 独家供电**，媒体称 $165B）向出资方 Blue Owl 发不可抗力通知。原因两条：① Energy Transfer 天然气管道许可被拒，延至 **2027-02-01**；② **Bloom 燃料电池的空气许可待批**（州限 11/23）。条款允许 2028 上线延误时**延付款项**，不退租。Oracle：「按计划」；Blue Owl：「财务承诺不变」。
- **股价**：ORCL −3.47%、**BE −3.10%**、GEV 受累（Barron's）。
- **对本档**：Jupiter 是 Oracle 1.2 GW 已签量的核心，也是 H1'26 那家 73% 客户的主要交付地。档案退出条件①「Oracle 或 Brookfield 任一公告缩减/延后 GW 承诺」——**这次是「延后付款」不是「缩减承诺」，前兆而非触发**。但它验证了两条风险：a) 「速度溢价」的前提是 55–90 天出电，而**电出不来的原因不在 Bloom 产能，在燃气管道许可和空气许可**——Bloom 的「免空气区许可」优势是加州口径，新墨西哥要批；b) Hunterbrook 引 SemiAnalysis 说的「Jupiter 首电 2027→2029」从做空方单源变成了 Oracle 自己的通知。
- **对 watchlist 信号⑥**：此前三形态都是钱（⑥-a 发股、⑥-b 卖方扛信用、⑥-c 买方预付）。**这是第一个「实体交付不了」的形态：不是融资断，是电/许可断，付款条款随之后移。** 归为 ⑥-d。`[INFERRED, HIGH]`
- **跟踪**：11/23 新墨西哥空气许可裁决；Q3 财报（10 月底）Oracle 相关 RPO 与客户集中度是否变化；GEV 燃机是否因此获得 Jupiter 替代订单（若是，速度溢价论点直接受损）。

## 风险

- **估值风险（主）**：EV/Sales 24.6x、FY27E PE 53x。三档情景（见估值锚）基准 IRR **−14%**，乐观才 +6%；要拿 15% IRR 需 2031 营收 $22–38B（CAGR 40–57%）。7 月已示范过 −52% 回撤后 V 型收复，这是 beta 3.8 的日常。`[COMPUTED]` HIGH
- **AI capex 周期**：敞口 ~100%，且是**晚周期品种**——客户是「等不到并网/燃机」的人，capex 骤停时它是第一个被砍的可选项。Sridhar Q2 自己说 AI 投资节奏「I do not know for sure」。与组合 SOXX 因子同向且放大（见 memory `ai-capex-cycle-topsignal-watchlist` ⑥ 融资结构信号：Brookfield 融资架子 = 买方资本替卖方出，和 NVDA vendor financing 是同一根线）。`[INFERRED]` HIGH
- **客户集中**：H1 单客 73%。Oracle 自身在 2026 年靠发债/租赁融资 capex（见 OCI 相关笔记），Oracle 的融资能力就是 Bloom 的营收能力。
- **电堆寿命 / 保修**：应计保修半年 $20M → $78M，Q2 计提率 4.22%（7 倍）；性能保证付款 $13.8M。若 Hunterbrook 的 <3 年更换周期成立，$14B 服务 backlog 的毛利模型（现 22%）要重算。
- **稀释**：股数两年半 +28%；$2.5B 0% 转债 @ $194.97 已价内（≈12.8M 股，10-Q 一处写 19.6M 股 `(待核实)`）；Oracle 权证；SBC 6.9% 营收。**内部人 2026 卖出 ≈ $110M+，零买入**；CEO 5 年 20 卖 0 买，持股 5%。
- **做空 / 诉讼史**：Hindenburg 2019 → 2020-02 财务重述（MSA 收入确认）；Hunterbrook 2026-07 两篇；证券集体诉讼集体期 2025-02-27 ~ 2026-07-08，首席原告截止 2026-09-28。
- **供应链**：钪氧化物。空头称 5 GW/年需 ~220 吨 vs 全球供给 ~240 吨；公司称 25 GW 可见度，未给吨数。**两边都没给可核实的数字。**
- **执行**：多 GW 级 SOFC 阵列 + 超容 + BESS 从未做过；Jupiter 首电 2027→2029、AEP 怀俄明 2028→2030 的延期说法仅做空方引 SemiAnalysis `(待核实)`。
- **燃机正常化**（2028–29）：见护城河节。这是终局风险，不是 2026 风险。

## 估值锚

- **类比**：GEV（forward PE ~46x，backlog 排到 2030，年营收 $40B+）、VRT（DC 电源）、CEG（核电 PPA）。BE 对 GEV 的 EV/Sales 溢价约 3 倍，理由是增速（+100% vs +15%），代价是能见度（RPO $0.49B vs GEV backlog $125 GW）。`[COMPUTED]`
- **一致预期**（Yahoo/stockanalysis 2026-09）：FY26 营收 $4.12B / EPS $2.71（近 30 日 24 上修 0 下修）；**FY27 营收 $6.79B（$5.3–9.6B，离散度极大）/ EPS $4.93（$2.95–7.01）**。评级 29 人：15 买 / 12 持 / 2 卖；目标价均值 $276（$97–390）。**记录卖方分布，不给目标价。**
- **三档情景 5 年 IRR**（`[COMPUTED]` 入场 $259.35，FY26 营收中值 $4.05B，2031 摊薄股数 330M）：

| 情景 | 营收 CAGR | FY31 营收 | 净利率 | 退出 PE | FY31 股价 | 年化 IRR |
|---|---|---|---|---|---|---|
| 悲观（燃机正常化 + 电堆更换成本坐实） | 5% | $5.2B | 10% | 15x | ~$23 | **−38%** |
| 基准（DC 供电份额稳住，增速回落到行业水平） | 20% | $10.1B | 16% | 25x | ~$122 | **−14%** |
| 乐观（Oracle 2.8 GW + Brookfield $25B 全部兑现，成第二个 GEV） | 32% | $16.2B | 20% | 35x | ~$344 | **+5.8%** |

- **当前价隐含**：要 15% IRR，FY31 营收需 $22–38B，即 5 年 CAGR **40–57%**，且退出时仍给 25–35x。作为参照，GEV 现在年营收 $40B。**市场把 Bloom 定价成了 2031 年的 GEV 一半规模。**
- **反推**：基准情景 10% IRR 入场价 ≈ **$76**，15% ≈ **$61**——恰好是 52 周低点 $61.37。换句话说，一年前的价格才配得上基准情景的机会成本。这不是目标价，是「多少钱这只票的赔率才对得起风险」。
- **结论**：论点（速度溢价、认证壁垒、独占赛道）**成立**；价格不成立。这是「对的故事、错的价格、错的因子」三合一：故事对，价格已透支两年，因子和组合最大风险同向。

## 退出条件

（未持有，以下是「进入 / 不进入」和若持有的规则）
- **不进入的硬条件**（任一成立即不看价格）：① 组合 betaSOXX > 0.5 时不加任何 AI 电力纯多头（现 0.32，见 memory `portfolio-soxx-factor-risk`）；② H1/FY 单客户集中 > 50%；③ RPO / 公司 backlog < 5%。**三条现在全部成立。**
- **进入门槛**（三条解除后）：股价 ≤ $76（基准 10% IRR）**且**保修计提率回到产品收入 < 2%、关联方收入 < 15%、Q 客户集中 < 40%。到价复核，到价 ≠ 扳机。
- **触发减仓（若持有）**：FY 指引首次**不上调**或下调；产品毛利率环比降 > 200 bps；保修计提率连续两季 > 4%。
- **触发卖出（若持有）**：① Oracle 或 Brookfield 任一公告缩减/延后 GW 承诺；② 10-Q 披露 FEOC/MACR 不合规风险或 ITC 资格被质疑；③ 电堆更换周期被公司自己下修至 < 4 年；④ AI capex 四大触发器 ≥ 2/4 转红（见 watchlist）。
- **持有阈值**：只在「速度溢价窗口」（燃机交期 > 24 个月）内持有；GEV/Siemens 交期回到 18 个月以内即为窗口关闭信号，无论股价。

## 跟踪信号

- **财报关注项**（每季 10-Q + 电话会）：
  1. **应计保修余额与计提率**（$77.8M / 4.22%）——这是电堆寿命争议唯一的会计侧证；
  2. **RPO**（$442M + $52M）vs 公司 backlog——比值 < 5% 持续 = 信息质量问题未解；
  3. 客户集中（73%）与关联方收入占比（20.7%）；
  4. 产品毛利率（37.2%）——「为客户时间牺牲成本」的取舍是否侵蚀；
  5. 股数与转债转股进度（294.5M，转债 12.8M 股价内）；
  6. FY 指引方向（三次上调后，第一次「维持」就是拐点信号）；
  7. 出货 MW（公司 2025 起停披露 acceptances，若恢复披露看 $/kW 趋势）。
- **行业领先指标**：
  - **GEV 燃机交期与 2029–30 槽位**（现 ~10 GW 剩余，产能 20→30 GW）——交期是速度溢价的分母；
  - SemiAnalysis BTM 供电项目追踪（Bloom 3.8 GW vs 其他）；
  - Henry Hub（$3.43）——燃料是 LCOE 的 20–25%；
  - IRS FEOC 拟议法规（PFE 身份认定）发布时间与内容；
  - Oracle 融资动作（OCI capex 的资金来源 = Bloom 73% 客户的付款能力）。
- **重大事件日历**：
  - **2026-09-21** S&P 500 纳入生效（被动买盘一次性，之后没有）；
  - **2026-09-28** 证券集体诉讼首席原告截止；
  - **2026-10-27/29** Q3'26 财报（共识营收 $1.06B / EPS $0.67；注意共识环比**持平**于 Q2，管理层会否第四次上调）；
  - 2026-12 底 2 GW/年产能是否如期；
  - 2027 Oracle 1.2 GW 已签部分交付进度、Jupiter 首电时间；
  - Hunterbrook 第三篇（做空方通常在财报前后出）。

## 仓位与历史

| 日期 | 操作 | 价格 | 仓位 | 备注 |
|---|---|---|---|---|
| 2026-09-16 | 建档观察，**不进入** | $259.35 | — | 论点成立、价格透支、因子与组合最大风险同向；三条硬条件全部成立；基准情景 10% IRR 入场 ≈ $76 |

> **期权备注**：BE 不在内存/SOXX 减仓腿名单，但它是 **beta 3.8 的 AI capex 纯多头**，对它卖 put 等于用期权放大 SOXX 敞口，触犯 playbook 禁区第四条（见 memory `ibkr-options-playbook` / [`put-selling-plan`](../portfolios/2026-07-23-put-selling-plan.md)）。IV 高不是理由——IV 高是因为它该高。**不做。**

## 参考

- **一手**：[FY2025 10-K](https://www.sec.gov/Archives/edgar/data/1664703/000162828026006516/be-20251231.htm) · [Q4/FY25 业绩稿 2026-02-05](https://investor.bloomenergy.com/press-releases/press-release-details/2026/Bloom-Energy-Reports-Fourth-Quarter-and-Full-Year-2025-Financial-Results-with-Record-Full-Year-Revenues/default.aspx) · [Q1'26 8-K](https://www.sec.gov/Archives/edgar/data/1664703/000162828026027913/ex991_q126financialresults.htm) · [Q1'26 10-Q](https://www.sec.gov/Archives/edgar/data/0001664703/000162828026028021/be-20260331.htm) · [Q2'26 8-K](https://www.sec.gov/Archives/edgar/data/1664703/000162828026050150/ex991_q226financialresults.htm) · [Q2'26 10-Q](https://www.sec.gov/Archives/edgar/data/0001664703/000162828026050247/be-20260630.htm) · [Q2'26 补充材料（EBITDA 历史）](https://www.sec.gov/Archives/edgar/data/0001664703/000162828026050150/ex992q226supplementalfin.htm) · [8-K 回应 Hunterbrook 2026-07-09](https://www.sec.gov/Archives/edgar/data/1664703/000162828026047734/be-20260709.htm) · [2030 可转债定价 2025-10-30](https://investor.bloomenergy.com/press-releases/press-release-details/2025/Bloom-Energy-Corporation-Prices-Upsized-2-2-Billion-Convertible-Senior-Notes-Offering/default.aspx) · [ES 5.5 数据表](https://bloomenergy.m3iworks.com/wp-content/uploads/bloom-energy-server-datasheet-2023.pdf)
- **电话会**：[Q4'25](https://www.fool.com/earnings/call-transcripts/2026/02/05/bloom-energy-be-q4-2025-earnings-call-transcript/) · [Q1'26](https://www.fool.com/earnings/call-transcripts/2026/04/28/bloom-energy-be-q1-2026-earnings-transcript/) · [Q2'26](https://www.investing.com/news/transcripts/earnings-call-transcript-bloom-energy-tops-q2-2026-forecasts-shares-jump-after-hours-93CH-4818294)
- **合同**：[Oracle 2.8 GW 2026-04-13](https://investor.bloomenergy.com/press-releases/press-release-details/2026/Bloom-Energy-and-Oracle-Expand-Strategic-Partnership-to-Deploy-up-to-2-8-GW-to-Accelerate-AI-Infrastructure-Build-Out/default.aspx) · [Oracle Jupiter 2026-04-27](https://www.prnewswire.com/news-releases/oracle-borderplex-and-bloom-energy-to-power-project-jupiter-with-cleaner-water-efficient-fuel-cell-technology-302754698.html) · [Brookfield $25B 2026-06-30](https://investor.bloomenergy.com/press-releases/press-release-details/2026/Brookfield-and-Bloom-Energy-Expand-AI-Infrastructure-Partnership-to-25-Billion-Fivefold-Increase-to-Build-and-Finance-Rapid-Power-for-AI-Infrastructure/default.aspx) · [AEP 1 GW 2024-11](https://investor.bloomenergy.com/press-releases/press-release-details/2024/Bloom-Energy-Announces-Gigawatt-Fuel-Cell-Procurement-Agreement-with-AEP-to-Power-AI-Data-Centers/default.aspx) · [Nebius 328 MW 2026-05-20](https://nebius.com/newsroom/nebius-and-bloom-energy-partner-to-power-ai-infrastructure-build-out) · [Equinix >100 MW](https://investor.bloomenergy.com/press-releases/press-release-details/2025/Bloom-Energy-Expands-Data-Center-Power-Agreement-with-Equinix-Surpassing-100MW/default.aspx) · [S&P 500 纳入 2026-09-04](https://press.spglobal.com/2026-09-04-Bloom-Energy,-Illumina,-and-Everpure-Set-to-Join-S-P-500-Others-to-Join-S-P-100,-S-P-MidCap-400,-and-S-P-SmallCap-600)
- **竞争 / 技术**：[SemiAnalysis：BTM 供电为什么难 2026-09-10](https://newsletter.semianalysis.com/p/what-is-so-hard-about-behind-the) · [SemiAnalysis：AI lab 如何解电力 2025-12-30](https://newsletter.semianalysis.com/p/how-ai-labs-are-solving-the-power) · [GEV 燃机槽位 2026-04](https://www.power-eng.com/gas/turbines/data-centers-drive-record-surge-in-ge-vernova-power-equipment-orders-as-turbine-slots-tighten-through-2030/) · [GEV backlog 116 GW](https://www.turbomachinerymag.com/view/ge-vernova-gas-turbine-backlog-hits-116-gw-as-power-orders-more-than-double) · [Siemens Energy 2026-06](https://www.spglobal.com/energy/en/news-research/latest-news/electric-power/063026-siemens-energy-lifts-global-gas-turbine-outlook-on-data-center-demand) · [CAT 交期 107 周](https://www.investing.com/news/analyst-ratings/caterpillar-engine-lead-times-extend-as-data-center-demand-surges-93CH-4435497) · [Utility Dive：2 GW 产能 2025-10](https://www.utilitydive.com/news/bloom-energy-says-its-on-track-for-2-gw-annual-production-capacity/804291/)
- **做空 / 争议**：[Hunterbrook 一：Bloom's Big Lie 2026-07-08](https://hntrbrk.com/investigations/bloom) · [Hunterbrook 二：电堆性能 2026-07-30](https://hntrbrk.com/investigations/bloom-2) · [Hindenburg 2019](https://hindenburgresearch.com/bloom-energy-a-clean-energy-darling-wilting-to-its-demise/) · [保修计提分析 2026-07-29](https://analysis.org/bloom-energy-be-q2-2026-warranty-accruals-hit-4-2-of-product-revenue-seven-times-last-years-rate/) · [集体诉讼截止 2026-09-28](https://www.prnewswire.com/news-releases/be-deadline-levi--korsinsky-reminds-bloom-energy-corporation-investors-of-upcoming-securities-class-action-deadline-302860226.html) · [内部人卖出 2026-05](https://finance.yahoo.com/markets/stocks/articles/bloom-energy-insiders-sold-us-120007429.html) · [Form 4 汇总](https://www.secform4.com/insider-trading/1664703.htm)
- **政策**：[OBBBA 燃料电池 ITC（NatLawReview）](https://natlawreview.com/article/congress-phases-out-energy-tax-credits) · [IRS Notice 2026-15 FEOC](https://www.irs.gov/newsroom/treasury-irs-provide-guidance-for-certain-energy-tax-credits-regarding-material-assistance-provided-by-prohibited-foreign-entities-under-the-one-big-beautiful-bill) · [韩国 CHPS 减量 2026-06](https://en.sedaily.com/finance/2026/06/09/korea-cuts-hydrogen-power-auction-volume-30-percent) · [EIA STEO 天然气 2026-09](https://www.eia.gov/outlooks/steo/report/natgas.php) · [FERC PJM 令 2025-12](https://www.ferc.gov/news-events/news/ferc-directs-nations-largest-grid-operator-create-new-rules-embrace-innovation-and) · [德州 SB6 首例裁定](https://www.whitecase.com/insight-alert/puct-affirms-curtailment-authority-over-co-located-data-centers-first-net-metering)
- **估值 / 预期**：[stockanalysis 统计](https://stockanalysis.com/stocks/be/statistics/) · [Yahoo 分析师预期](https://finance.yahoo.com/quote/BE/analysis/) · [Fool：涨幅背后的算术 2026-09-14](https://www.fool.com/investing/2026/09/14/bloom-energy-is-up-x-this-year-heres-the-math-behi/) · [股价年度史](https://www.statmuse.com/money/ask/bloom-energy-stock-price-history-by-year)
- **组合关联**：[GEV](GEV.md)（燃机交期 = 本票速度溢价的分母）· [VRT](VRT.md)（同层 DC 电源）· [CEG](CEG.md)（核电 PPA，另一种「卖确定性」）· [NVDA](NVDA.md)（vendor financing 与 Brookfield 融资架子同源）· 主题笔记 [AI 瓶颈利润池迁移](../notes/2026-06-29-ai-bottleneck-profit-pool-migration.md) · [token 即电力价值链](../notes/2026-06-24-token-is-electricity-value-chain.md)
- **NOT FOUND（子 agent 配额耗尽未补）**：FY2025 acceptances MW；官方 $/kW；Brookfield 已部署金额；AEP 已交付 MW；Q3 财报日公司确认；Microsoft/Meta/Google 对燃料电池的直接表态；CFO Berenbaum 2026-04 离任原因；转债 capped call 条款。

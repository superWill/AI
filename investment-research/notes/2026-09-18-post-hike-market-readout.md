---
date: 2026-09-18
type: 事件读数 / 宏观 → 市场传导
status: active
data_source: 一手：Fed 声明 + SEP + Warsh 发布会 transcript（2026-09-16）、FRED（DGS2/10/30、DFII10、HY/IG OAS、SP500/DJIA）、Treasury 日曲线、Freddie Mac PMMS 9/17、Census 零售/新屋开工、BLS 进口价、DOL 初请、费城联储、FINRA 保证金 8 月、ICI 周流量、Lennar Q3、CoreWeave 8-K、BoE/ECB；二手：Reuters/MarketWatch/Motley Fool via Yahoo、Investing.com（含 Fed Rate Monitor 替代 CME FedWatch）。实测：yfinance 指数/利率至 9/17 收盘，个股/ETF 至 9/16（9/17 未入库）。主会话与子 agent WebSearch 配额均耗尽，全部 WebFetch 一手页
purpose: 回答「加息后的实际影响」——市场怎么定价、哪些资产真的动了、9/15 油价笔记的三档情景现在落在哪一档、对组合的动作是什么
related: notes/2026-09-15-oil-cycle-deep-dive.md（传导框架与三档情景）· memory ai-capex-cycle-topsignal-watchlist（信号 ⑥ 融资结构）· tickers/BE.md · tickers/GOOGL.md · portfolios/2026-06-24-actual-holdings-snapshot.md
---

# 9/16 加息后两日：市场把「鹰派」吃下去了，但只吃了一口

## 一句话

**加息本身不是新闻（会前定价 90%），新闻是 2027 年点阵不降 + Warsh 明说「金融条件不算紧」。** 市场反应分两段：9/16 当日实际利率 +6bp、道指 −631 点、区域银行/能源领跌；9/17 全部回吐并反超——S&P +1.14%（8 月以来最佳）、SOX +3.14%、10Y 回到 4.94%、VIX −13%。**两天净结果：股票涨、利率平、美元涨、油跌、信用利差收窄。** 这不是「市场不信 Fed」，是市场在会前已经定价了近 4 次加息，Fed 给了 2 次，属于「鹰派但没有更鹰」的解压。9/15 笔记的三档里，现在落在**基准档**（9 月 + 12 月至 4.00–4.25，10Y 4.9–5.3）。对组合：**不动，理由不变，但信号 ⑥ 这周多了两个数据点（CoreWeave $3B 转债 + ATM、Warsh 亲口把 hyperscaler 发债列为长端上行原因）。** `[INFERRED, HIGH]`

## 一、Fed 到底说了什么

`[KNOWN, HIGH]` 来源：[声明](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm) · [SEP](https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm) · [发布会 transcript](https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20260916.pdf)

| 项目 | 9 月 | 6 月 | 变化 |
|---|---|---|---|
| 目标区间 | **3.75–4.00%**（+25bp，12–0） | 3.50–3.75% | |
| 点阵中值 2026 末 | **4.1%**（18 人中 16 人看年内再加 ≥1 次） | 3.8% | +1 次 |
| 2027 末 | **4.1%**（8 人在 4.375、6 人 4.125、4 人 ≤3.625） | 3.6% | **从降 1 次改为不降** |
| 2028 末 / 长期 | 3.9% / 3.2% | 3.4% / 3.1% | |
| 核心 PCE 2026 / 2027 | 3.4% / 2.5% | — | 2% 推到 2029 |
| 失业率 2026 | 4.1% | 4.3% | 更强 |

**Warsh 发布会五句话**（verbatim）：
1. 为什么加：「I would be hard-pressed to describe broad financial conditions as restrictive… So we removed a dose of accommodation.」→ 定性是**撤走宽松**，不是紧缩。
2. 七周变了什么：经济走强 + 「the inflation summer trends weren't passing the test」+ 地缘判断变了。
3. 油价：「We cannot affect any individual price… But what we can do, and will do, is ensure that any change in relative prices don't broaden out.」→ **明确不 look through**，与 9/15 笔记判断一致。
4. 前瞻指引：「I'm not in the forward guidance business」；本人不提交点阵。
5. **长端为什么涨**（答 Axios，最重要的一句）：三个原因——经济强、「**competition for capital. The surge in capital expenditures… the so-called hyperscalers are out in the market raising funding**」、地缘（crack spread 而非现货）。→ Fed 主席亲口把 AI capex 融资列为期限溢价来源，这是信号 ⑥ 的官方背书。`[INFERRED, HIGH]`

## 二、市场实际怎么动的

### 2.1 利率：9/16 打、9/17 回，两天净平

`[KNOWN, HIGH]` FRED / Treasury / Reuters

| | 9/15 | 9/16 | 9/17 | 两日净 |
|---|---|---|---|---|
| 2Y | 4.67 | **4.74** | 4.67 | 0 |
| 10Y | 5.00 | **5.01**（2007 年来最高） | **4.94** | −6bp |
| 30Y | 5.36 | 5.35 | 5.29 | −7bp |
| **10Y TIPS 实际** | 2.62 | **2.68** | **2.61** | −1bp |
| 10Y 盈亏平衡 | 2.38 | 2.33 | 2.33 | −5bp |
| 30Y 按揭（Freddie 9/17） | 6.76（上周） | | **6.95%**（2025-01 来最高） | +19bp |

- 9/16 的冲击全在**实际利率**（+6bp），盈亏平衡反而降——市场读的是「Fed 会压通胀」，不是「通胀失控」。9/17 实际利率回到 2.61，**仍在 9/15 笔记基准档 2.6–2.9 的下沿，没有见顶信号**。
- 曲线：2Y 平、30Y 降 7bp → **熊平变牛平**，长端相信 Fed。
- 期限溢价（NY Fed ACM）会后未更新，9/15 值 0.709，8 月末 0.763。

### 2.2 期货定价：年底 ~1.3 次，略高于点阵

`[KNOWN, MED]` [Investing.com Fed Rate Monitor 9/17 19:45 EDT](https://www.investing.com/central-banks/fed-rate-monitor)（替代 CME，原站超时）
- 10/28：不加 44.9% / 加 55.1%
- 12/9：3.75–4.00 12.6% / 4.00–4.25 47.8% / 4.25–4.50 39.6%
- 年底隐含中点 ≈ **4.19%** `[COMPUTED]` = 1.27 次 → 比 SEP 中值 4.1 略鹰。
- ⚠ Raymond James 称「两次概率 83%」与上表不符，单一来源。会前同口径快照 NOT FOUND，只知会前定价「近 4 次」（UBS）。

### 2.3 股票：9/16 利率敏感挨打，9/17 科技全收回

`[KNOWN, HIGH]` yfinance 实测 + FRED

| | 9/16 | 9/17 | 两日 | YTD |
|---|---|---|---|---|
| S&P 500 | −0.45% | **+1.14%** | +0.69% | +11.4% |
| Nasdaq 100 | +0.02% | +1.73% | +1.76% | +16.8% |
| 道指 | **−1.21%（−631 点）** | +0.61% | −0.60% | +7.0% |
| Russell 2000 | −0.40% | +0.55% | +0.15% | +14.6% |
| **SOX** | +0.63% | **+3.14%** | +3.79% | +57.4% |
| S&P 等权 | −0.79% | （未入库） | | +11.0% |
| VIX | 17.71 | **15.44（−12.8%）** | | |

- **9/16 板块**（ETF）：能源 −2.9%（油跌）、区域银行 −1.8%、金融 −1.6%、建商 −1.0%、可选消费 −0.6%、REIT −0.6%；科技 +0.1%、公用 0。**利率敏感板块挨打，AI 板块没事**——和 9/15 笔记「半导体走实际利率」的判断表面矛盾，解释在下节。
- **9/17**：科技、公用、材料领涨；GNRC +18%（Amazon 数据中心备用发电 $2.4B）、SMCI +9.5%、INTC +7.7%、AMD +6.4%、MU +5.5%、NVDA +2.5%、ORCL +5.2%（OpenAI $1.2T 融资传闻）；CRWV **−4.2%**（$3B 转债 + 3,500 万股 ATM）。
- 单日 9/17 是「8 月以来最佳」，Truist：「Technology is reasserting leadership as investors move past an event」。

### 2.4 为什么半导体两天反而 +3.8%

`[INFERRED, MED-HIGH]`
- 会前一周 SOX 已跌 −5.7%（SMH −5.0%、MU −9.9%），**加息被提前交易了**。9/15 笔记的 −0.41 相关是周频，这周的周度读数是 10Y 平（+0.06%）、SOX 平（−0.13%）——**相关性没破，是两边都没动**。
- 9/17 的反弹是「事件过去 + 实际利率回落 7bp + 内存涨价叙事（Intel CEO 称内存价格涨 500%+，单一来源）」三件事叠加，不是对加息的反应。
- **不要把 9/17 读成「半导体对利率免疫」**：真正的检验是 10Y 再上 5.1–5.3 时 SOX 跟不跟跌，那才是基准档上沿的压力测试。

### 2.5 信用：没有压力，反而收窄

`[KNOWN, HIGH]` FRED BAMLH0A0HYM2 / BAMLC0A0CM
- HY OAS：9/15 2.76% → **9/16 2.70%**（会议日收窄 6bp）；IG 0.80 → 0.78。周环比持平。
- **这是加息「实际影响」里最重要的一条：信用市场没把加息当紧缩。** 与 Warsh「金融条件不紧」的判断互为印证，也说明 Fed 还有继续加的空间而不触发信用事件。
- AI 融资链本周三个点：① CoreWeave $3B 可转优先票据 + 最多 3,500 万股 ATM（9/17，股价 −4.2%，Bernstein 称其「最暴露于 AI 训练放缓」）；② Oracle CDS 走阔（Motley Fool 提及，无 bp，单一来源）；③ Holtec 核电 $900M IPO 因「市场条件」暂停（单一来源）。**信号 ⑥ 本周 +2 个数据点，但都是「还能融到」，不是「融不到」。**

### 2.6 美元 / 油 / 黄金

- DXY 100.31（9/16，七周高）→ 100.24；USD/JPY 156，EUR 1.147。9/17 终止六连涨。
- Brent 期货 9/15 $108.75 → 9/17 **$104.16**（沙特东西管线重启、利比亚恢复、美伊降温）；**但 FRED 现货 9/15 $130.80**，比期货高 $20+，实货极度紧张。霍尔木兹商船通行降至 3 艘/日。JPM「无明确 endgame」。
- 黄金 9/17 方向两源相反（Reuters 现货 +1.9% / Yahoo 期货 −0.3%），$4,340–4,390 区间，**距 1 月高点仍 −18%**，无企稳信号。

## 三、宏观数据：经济没有配合「加息会伤增长」的剧本

`[KNOWN, HIGH]` Census / BLS / DOL / 费城联储 / Freddie Mac / Lennar
- 8 月零售 **+1.2%** m/m（预期 +0.9%），y/y +6.0%。
- 初请 **196K**（预期 208K），续请 173 万（2024-01 来最低）。
- 8 月进口价 **+7.0% y/y**（2022-08 来最大）、非燃料 +5.5%——**关税 + 美元之外的输入通胀**，这是 Warsh「too many categories above 3%」的来源之一。
- 费城联储 9 月 37.8（8 月 47.4），**支付价格 48.6（+8）、收取价格 31.3（+14）**——价格扩散仍在。
- 新屋开工 1,275K（−2.6%），竣工 −27% y/y；Lennar Q3 新订单 **−9%**、激励占 ASP 12%、按揭 6.95%。**住房是唯一已经在挨打的实体部门。**
- 8 月 FINRA 保证金 **$1.454 万亿**（+2.6% m/m，6 月高点 $1.502 万亿）——杠杆没降。ICI 截至 9/9 当周股票基金 **−$118 亿**（美国 −$134 亿）、债券 +$115 亿，连续两周股→债。

**读法**：增长强 + 通胀广化 + 信用宽松 + 杠杆未降 = **Fed 没有理由停**。这和「加息会伤经济所以很快停」的市场惯性相反。点阵 2027 不降在数据上是自洽的。`[INFERRED, HIGH]`

## 四、全球同步：这是 G3 一起加

`[KNOWN, HIGH]`
- ECB 9/10 加 25bp 至 2.50%（年内第二次）。
- BoE 9/17 维持 3.75%，**6–3**，三人主张加息，「second-round effects had increased」。
- BoJ 9/17–18 预期加至 1.25%（31 年高），结果**待核**。
- 三家央行的共同语言是「二阶效应」。这不是美国的油价问题，是全球供给冲击广化的问题，**美元不会因为 Fed 独自鹰派而单边走强**，DXY 100 附近可能就是这轮的上限。`[INFERRED, MED]`

## 五、对照 9/15 笔记的三档情景

| | 悲观（油回落 + Fed 停） | **基准（9 月 + 12 月至 4.00–4.25）** | 升级（3–4 次或增长恐慌） |
|---|---|---|---|
| Fed | 9/16 加后停 | **✅ 点阵 4.1 = 再加一次；期货 1.3 次** | 期货 12 月 4.25–4.50 有 40% |
| 10Y / 实际 | 4.4–4.6 / 2.2–2.3 | **✅ 4.94 / 2.61** | 5.3–5.6 / 3%+ |
| 油 | 回落 | **✅ $104，但现货 $130** | |
| 信用 | | **✅ HY 2.70，无压力** | 利差走阔 |

**结论：落在基准档，且靠近基准档的鸽派一侧**（10Y 4.94 在 4.9–5.3 下沿）。升级档的概率在期货里是 40%，不可忽略。基准档对组合的含义 9/15 已写：SOX 倍数受压但不崩，BRK 和现金是正确头寸。

## 六、加息的「实际影响」清单

按已经发生 vs 尚未发生分：

**已经发生** `[KNOWN]`
1. 按揭 6.95%，建商新订单 −9%，住房是第一个实体受害者。
2. 美元七周高，日元 156，新兴市场承压（具体 NOT FOUND）。
3. 黄金距高点 −18%，实际利率是它的天敌。
4. 股票基金连续两周净流出转债券。
5. AI 融资链的融资成本上移：CoreWeave 转债 + ATM，Oracle CDS 走阔。

**尚未发生（要盯）** `[INFERRED]`
1. 半导体倍数压缩——10Y 5.1–5.3 才是压力测试，本周没测到。
2. 信用利差走阔——HY 2.70 是 2021 以来低位区，一点压力没有。
3. 增长放缓——零售 +1.2%、初请 196K，完全没有。
4. 通胀广化收敛——费城联储价格指数还在扩散，9/30 PCE、10/14 CPI 是下两个检验点。

## 七、对组合：不动，理由比 9/15 更硬

`[INFERRED, HIGH]`
- **不动的理由**：32% 现金每 25bp 多赚年化 ~8bp；BRK 19.9% 是加息受益腿；betaSOXX 0.32 把半导体倍数风险压到个位数。这三条昨天之后全部更成立。
- **不加半导体**：SOX 两日 +3.8% 是解压反弹不是拐点信号；实际利率 2.61 没见顶；黄金没企稳；核心 PCE 月环比没回 0.2。四个信号 0/4。见 memory `dip-buy-trigger-signals-not-daycount`——「踏空了该追吗」和「跌了几天该抄吗」是同一个错误。
- **不加 XLE**：9/16 能源 −2.9% 是这周最差板块之一，油在跌、现货在涨，它只对冲三档中的一档。
- **信号 ⑥ 记账**：本周 +2（CoreWeave 融资、Warsh 点名 hyperscaler 发债推高长端）。四大触发器上次 0/4，本周仍 0/4，但 ⑥ 的证据密度在上升。下次读数：GOOGL $400 亿 ATM 动用进度（Q3 财报 10 月底）、Oracle 债券利差、CoreWeave 转债定价（利率和转股溢价是市场对 AI 信用的实时报价）。
- **BE**：加息两日 +8.3%（$259 → $281），9/21 进指数的被动买盘。档案结论不变：不进入，且它是 0% 转债再融资窗口的直接受害者，利率每高一点它下一次融资的转股溢价就低一点。

## 八、下两周日历

| 日期 | 事件 | 看什么 |
|---|---|---|
| 9/18 | BoJ 决定、工业生产 | 是否加至 1.25%（日元、套息） |
| 9/21 | S&P 500 调整生效（BE/ILMN/P 进） | BE 被动买盘后是否见顶 |
| 9/23–24 | GIS / DRI 财报 | 消费价格传导 |
| 9/24 | COST Q4 财报 | 见 tickers/COST.md 跟踪信号 |
| 9/30 | **8 月 PCE + Q2 GDP 三读** | 核心 PCE 月环比是否 0.2（Warsh 判据） |
| 9/30 | MU 财报 | 内存涨价叙事的官方数字 |
| 10/14 | 9 月 CPI | |
| 10/27–28 | FOMC | 期货 55% 加息 |
| 10/29 | Q3 GDP 初值 | |

## 数据缺口（诚实清单）

会前同口径 FedWatch 快照、9/17 板块 ETF 与个股收盘（yfinance 未入库，个股数字来自 Yahoo 页面）、EPFR / ETF 级流量、截至 9/16 当周 ICI、大行正式修改 Fed 路径或 S&P 目标、BoJ 实际结果、特朗普会后表态、期限溢价会后值、数据中心 ABS/私募信贷压力、EM 具体读数。单一来源：Holtec IPO 暂停、Oracle CDS 走阔、Intel CEO「内存涨 500%」、Raymond James 83%。

## 参考

- [FOMC 声明 9/16](https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm) · [SEP 9/16](https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260916.htm) · [Warsh 发布会 transcript](https://www.federalreserve.gov/mediacenter/files/FOMCpresconf20260916.pdf) · [FOMC 日历](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)
- [FRED 收益率 DGS2/10/30/DFII10](https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2,DGS10,DGS30,DFII10) · [Treasury 实际收益率曲线](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_real_yield_curve&field_tdr_date_value_month=202609) · [FRED HY OAS](https://fred.stlouisfed.org/data/BAMLH0A0HYM2.txt) · [NY Fed ACM 期限溢价](https://www.newyorkfed.org/medialibrary/media/research/data_indicators/ACMTermPremium.xls) · [Freddie Mac PMMS](https://www.freddiemac.com/pmms)
- [Investing.com Fed Rate Monitor](https://www.investing.com/central-banks/fed-rate-monitor) · [「As hawkish as it gets」策略师汇总 9/17](https://www.investing.com/news/stock-market-news/wall-street-on-fed-rate-hike-as-hawkish-as-it-gets-4905491) · [UBS 为何不担心股市 9/17](https://www.investing.com/news/stock-market-news/the-fed-is-hiking-why-isnt-ubs-worried-about-stocks-4905218) · [Reuters via Yahoo：加息后股市 9/18](https://finance.yahoo.com/economy/policy/articles/shares-tick-higher-fed-hikes-020459399.html) · [MarketWatch：加息安抚不了债市 9/17](https://finance.yahoo.com/markets/stocks/articles/fed-rate-hike-fails-calm-214000690.html)
- [Census 零售 8 月](https://www.census.gov/retail/marts/www/marts_current.pdf) · [BLS 进口价 8 月](https://www.bls.gov/news.release/ximpim.nr0.htm) · [DOL 初请 9/17](https://www.dol.gov/ui/data.pdf) · [Census 新屋开工 8 月](https://www.census.gov/construction/nrc/pdf/newresconst.pdf) · [费城联储 9 月](https://www.philadelphiafed.org/surveys-and-data/regional-economic-analysis/mbos-2026-09) · [FINRA 保证金](https://www.finra.org/rules-guidance/key-topics/margin-accounts/margin-statistics) · [ICI 周流量](https://www.ici.org/research/stats/combined_flows) · [Lennar Q3](https://newsroom.lennar.com/2026-09-16-Lennar-Reports-Third-Quarter-2026-Results)
- [CoreWeave $3B 转债 + ATM 9/17](https://finance.yahoo.com/markets/stocks/articles/coreweave-raises-3-billion-convertible-165635619.html) · [Oracle +5% / CDS 9/17](https://finance.yahoo.com/markets/stocks/articles/why-oracle-stock-jumped-6-171651571.html) · [油市无 endgame（JPM）9/17](https://www.investing.com/news/commodities-news/jp-morgan-says-it-has-no-clear-oil-market-endgame-as-iran-conflict-drags-on-4906287) · [ECB 9/10](https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp260910~314e508016.en.html) · [BoE 9/17](https://www.bankofengland.co.uk/monetary-policy-summary-and-minutes/2026/september-2026) · [S&P 500 调整 9/21](https://press.spglobal.com/2026-09-04-Bloom-Energy,-Illumina,-and-Everpure-Set-to-Join-S-P-500-Others-to-Join-S-P-100,-S-P-MidCap-400,-and-S-P-SmallCap-600)

## ⭐ 2026-09-22 补记：加息后一周变成 risk-on 轮动，驱动是油 + AI 叙事，不是利率

`[KNOWN, HIGH]` yfinance 至 9/21 收盘 + 子 agent（Yahoo/CNBC/TradingEconomics/FRED/CoreWeave IR）

**加息后 4 个交易日累计**（9/15 → 9/21）：S&P **+2.4%**、NDX **+5.3%**、SOX **+11.3%**、Nasdaq 综指 9/21 创收盘新高（6 月以来首次）；道指 −0.1%、Russell +0.2%、等权几乎没动。BRK-B **−2.9%**、XLE −4.7%、KRE −2.2%。10Y 4.96、TIPS 实际 2.68（9/18，本轮高位）、HY OAS 2.68、VIX 14.9。**被买的是久期最长 beta 最高的腿，被卖的是防守和利率受益股——这是 AI 交易回归，不是广谱「经济好」。**

**三个具体触发**：
1. **油**：Brent 9/21 收 $100.06（−3.7%）、WTI $95.59（−4.7%），连跌四日。原因是 Trump 周日称「probably open to」在 UNGA 见伊朗总统，自称 deciding mode；CENTCOM 称霍尔木兹流量回到 6 个月高点、中东出口 17.1 mb/d；沙特东西管线**仍关闭**，**无停火**。⚠ yfinance BZ=F 显示 9/21 −6.7% 至 $96.92，与 TradingEconomics 差 $3，疑为合约换月造成的假跳空，采后者。
2. **META +11.4%**（$741）：Muse agent app 6 天 902K 下载、9/19 单日 264K 创纪录，Wells Fargo 目标价 640 → 796。Amazon 周日夜起封锁 Muse。**这是 8/20 笔记「agent 层」叙事的第一个消费级数据点。**
3. **芯片**：INTC +12.1%（Altera 秘密递交 IPO + SK hynix 谈代工，单源 LOW-MED）、AMD +10%（盘中市值首破 $1T，供应链称 Q4 提价 10%，单源）、ARM +14%、MRVL 加息后 +16%、MU +12.5%。

**Fed 侧没有变软**：9/21 Musalem（Reuters 独家）「without further policy restraint… more likely to be substantially above our 2% target in 18 months than at target」，称加息后政策可能仍在刺激。FedWatch 10/28 加息 51–58%（三源口径不一，无一手 CME）。BoJ 9/18 加至 1.25%（1995 年来最高，7–2），日元不升反跌。

**信号⑥ +1，且这次有价格**：CoreWeave 转债 9/17 夜定价，上调至 **$3.7B**（+$500M 超额权），**票息 2.875%、转股溢价 22.5%**（$97.85）、capped call 上限 +150%，9/22 交割，另有 3,500 万股 ATM。对照 Bloom 2025-10 的 0% / 52.5% 溢价——**11 个月内 AI 基础设施转债的融资条件从「零息高溢价」变成「有息低溢价」，这是信号⑥第一个可量化的价格读数。** OpenAI 据报要价 $1.5T（上轮 $730B）。

**⚠ 内存 4 信号的新输入**：TrendForce 常规 DRAM 合约价 1Q26 +90–95% → 2Q +58–63% → **3Q +13–18%**，原因是消费需求弱 + 高基数 + 美系 CSP 签多年 LTA 限制涨价。**二阶导明显下行**，MU 9/30 财报（共识 EPS $31.16，约 6x）是检验点。MU 一周 +13% 是在二阶导下行的数据上涨的，这是 `dip-buy-trigger-signals-not-daycount` 第二形态（踏空反弹）的教科书环境。

**BTC +13% 至 $85.6K**：$82–85K 强平空头 $230–648M，ETF 9/17–18 净流入 $592M。**本周是空头被杀不是多头建仓**，方向信息量低。

**对 §五三档的修正**：仍在基准档，但市场这周按「Fed 信用够 + 油见顶」定价，把升级档概率往下压。这个定价的前提要在 9/30 核心 PCE（Warsh 判据 m/m 0.2）上验证。**动作不变：不动。** 组合本周跑输（现金 32% + BRK −2.9% + betaSOXX 0.32），是「宁愿错过」的结构性代价，不是判断错。

其他：9/18 四巫日约 $7T 名义到期（史上第二大）无波动；道指周 −1.7% 为 3 月来最差周；8 月工业生产 0.0%（预期 +0.3%）、LEI −0.1%（3 月来首降）；Oura 递交 IPO（拟募 >$2.2B）；9/24 Trump–Xi 白宫峰会（AI 护栏 / 芯片准入 / 关税休战）；9/23 flash PMI。

### 09-23 追加（9/22 收盘）`[KNOWN, HIGH]` yfinance + Yahoo/stockanalysis/FRED/Richmond Fed
- 9/22：S&P 持平 7,764、Nasdaq +0.45% 连续第二日新高、道指 −0.36%、**SOX +2.06%（加息后累计 +13.6%）**、VIX 14.21。MU +5.0%（$1,096，9/30 财报前）、SNDK +5%（Rosenblatt 首评 $2,400）、META −0.63%（IBKR 平台被卖最多）、CRWV +1.6%（$3.7B 转债 9/22 交割）、BE +1.3%。
- 利率：10Y 4.97、2Y 4.75、TIPS 2.62；**2Y 拍卖高收益 4.787%（前次 4.315%）**。Barkin 9/22「Why Hike?」：>60% PCE 分项年化 >3%、「'passing' shocks aren't proving to be short-lived」、「Will additional hikes be required? We'll see.」FedWatch 10/28 加息 55–60%。
- 油：WTI **$90（−5.9%）**、Brent $99，连跌六日。Trump UNGA：伊朗「make a deal or annihilate」，Kushner/Witkoff 与伊方 3 小时会谈，称伊朗请求停火（伊方否认）；沙特东西管线重启口径不一。**无停火，霍尔木兹 <20 艘/日。**
- NVDA：Bloomberg 9/22 前瞻 P/E **<17x**，十年最低，与本笔记 9/16 七姐妹表一致（yfinance 13.6）。
- 日历：9/23 Meta Connect（4pm PT）、flash PMI（53.6/55.8 是否 actual 待核）；**9/24 Trump–Xi 白宫会谈**（关税休战 11/10 到期、芯片管制、稀土）+ **COST 财报**（共识 $94.85B / EPS $6.55）；9/30 MU（共识 EPS $31.14 / $50.4B）。
- 环境：macOS 27 后 x86 Homebrew Python 失效（bad CPU type），`.venv` 已用 arm64 系统 Python 3.9 重建，yfinance 1.2.0；旧 venv 改名 `.venv-x86_64-broken`。

### 09-25 追加（9/23–24）：利率杀第二波 + Oracle force majeure `[KNOWN, HIGH]` Investrade / Yahoo / FRED / Fed 官网 / TechCrunch
- **9/23**：S&P −0.75%、Nasdaq −1.13%、Russell −1.77%；**S&P 成分 >51% 跌破 200 日线**；11 板块只有能源收红。驱动：**flash PMI 综合 58.4**（制造 57.0 = 2022-05 来最强，投入成本「四年最陡」，Williamson：「近二十年调查史上最严重供应瓶颈之一」）→ 10Y +13.7bp 至 5.11%，**5Y 5.03% 2007 年来首破 5%**。
- **9/24**：S&P −0.02%（盘中 −0.5% 被「美伊分阶段协议」头条拉回）、道指三连跌、SOX −0.33%、VIX 15.67；**10Y 5.14–5.16%（盘中破 5.2%）、30Y 5.446%（2004 年来最高）、TIPS 实际 2.76%（9/23）**；5Y 拍卖尾 3.1bp、BTC 2.21（史上第二大尾，单源）；7Y 5.085%。**三位 Fed 官员排队说再加**：Williams 9/24「今年再加一次合理」、Barr 9/23「可能需要进一步调整」+ 点名 AI 投资需求是通胀源、Paulson 9/24「温和的进一步加息」。FedWatch 10/28 54% → 9/25 TE 64–67%。
- **对 9/15 三档**：10Y 5.16 / TIPS 2.76 已到**基准档上沿**（4.9–5.3 / 2.6–2.9），升级档（5.3–5.6 / 3%+）一步之遥。**SOX 的压力测试开始了：10Y 5.1–5.2 区间 SOX 两日只 −0.3%、AMD/INTC 反涨**——半导体这次没跟利率跌，与 4.2 节「2026 敏感度回到 2022 水平」的判断**相反**，待更多数据。`[INFERRED, MED]`
- **COST Q4**：EPS $6.75 beat $0.20，其中 $0.15 是关税退税；剔油剔汇同店 6.7%、付费会员 +3.8%（首次跌破 4%）、续费率止跌 +10bp、core-on-core −32bp（公司归因退税再投资降价）；无特别股息；管理层定调「6–7% 是更正常的水平」；盘后 +0.3%。详见 tickers/COST.md ⭐9/24。
- **Trump–Xi 9/24**：休战延 2 个月至 2027-01-10；**芯片管制零宣布**（无 H20/B30A/H200）；稀土「按月过日子」；成果 = 两只熊猫 + 10 万学生签证。半导体/中概零反应。
- **⭐ Oracle force majeure（Jupiter 2.45 GW）**：燃气管道许可被拒延至 2027-02、Bloom 空气许可待批 → 对 Blue Owl 发不可抗力，可延付。ORCL −3.5%、BE −3.1%。**信号⑥第四形态 ⑥-d：不是钱断，是电/许可断。** 详见 tickers/BE.md ⭐9/24。
- **Meta Connect**：VR Glasses $1,299（2027 春）、Ray-Ban Gen 3 $449；Muse 连接器加 **Walmart**/Best Buy/Sephora/Instacart/Shop Pay/PayPal；Walmart+Target 站 Google/Shopify 的 UCP；META 9/24 **+4.5%** 至 $777.59（「Muse 变现策略」）。Amazon 仍封。
- 油：胡塞 6 枚导弹射延布/塔伊夫被拦；沙特东西管线已重启；沙特产量 1990 年来最低；Brent 9/24 $106.6（+3.4%），9 月 MTD +17%。美伊「分阶段协议」（重开霍尔木兹换解除港口封锁）在谈，**无停火**。
- 其他：初请 197K；8 月新屋销售 684K（预期 620K）；HY OAS 273bp（周 +5bp，仍紧）；USDJPY 158.7（财务省 7 月末起干预 ¥15.4T）；黄金 $4,283 周 −2%；PAYX −8.8%、CTAS −3.4%、MGM −10%（Diller 撤回要约）；Micron 9/30 共识 $50.45B / EPS $31.16，看 FQ1'27 指引能否 >$55B；Oura 9/28 当周定价；Q2 GDP 三读 + 8 月 PCE 均 **9/30**（含年度修订）。

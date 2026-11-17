---
ticker: TEM
name: Tempus AI
sector: Healthcare / Diagnostics + Data
layer: N/A
position_type: none            # 不持有
status: passed                 # value-investor 判「不懂，过」
last_updated: 2026-11-17
data_source: 2026-11-17 value-investor 判决（Q3'26 8-K 业绩稿 EX-99.1 一手直读；电话会为 MarketBeat 二手转述；10-Q 全文未读；现价 yfinance 11/16 收盘）
---

# Tempus AI (TEM)

> 这是一份**判决记录**，不是完整档案。起因：2026-11-17 用户看到段永平 Q3 13F 里有 2 万股 TEM（占其组合 0.01%，观察仓）后问「对标谁」「值不值得碰」。

## 一句话定位

三块拼成的公司：肿瘤基因检测（收入大头，靠医保和商保报销）、遗传病检测（2025 年初收购 Ambry）、把「临床记录 + 基因」数据授权给药企并做 AI 应用（收购了 Paige）。整体最接近的对标是 Caris Life Sciences；检测对 Foundation Medicine（罗氏）、Guardant、Natera；数据对 Flatiron（罗氏）。`[KNOWN, 凭训练记忆, MED]`

## 2026-11-17：`value-investor` 判决 —— 不懂，过（停在第 1 关）

**讲不清它靠什么赚钱。** 逐块看：

- **检测**：只披露总量。Q3 收入 $303.5M（+20%），肿瘤检测量 +32%，毛利率 62.4%。**没有**每次检测的单价、医保与商保各报多少、拒付率。`[KNOWN, HIGH, Q3 8-K]`
- **涨价来源不在公司手里**：2027 年约 $80M 的肿瘤单价提升取决于 FDA 批准的 xT 拿到的医保定价。`[KNOWN, MED, 电话会转述]`
- **数据**：收入 $108.1M（+33%）。剩余合同价值、净收入留存率本季都没披露。关联方 Pathos 一家贡献 $22.1M（约占数据收入 20%）；SB Tempus 一个季度内从 $6.3M 降到 0。`[KNOWN, HIGH, 8-K]`
- **AI（Paige）**：收入没有单独拆出。
- **医生为什么不换到 Foundation / Caris / Guardant**：说不出具体机制。

第二、三、四关没有走到。

**顺手看到的事实（不作判决依据）：**

- Ambry 收购满一年，Q3 同口径只增长 3%。`[KNOWN]`
- 还在继续收购：Personalis 的股东投票定在 11/30，管理层承认它「每做一次检测都亏钱」。`[KNOWN, MED]`
- 市值约 $11.8B，企业价值约 $12.3B，约为过去 12 个月收入的 8 倍。`[COMPUTED]`
- 前 9 个月经营现金流 −$71.6M，股权激励每季度约 $50M → owner earnings 为负。可转债约 $1.35B。`[COMPUTED / KNOWN]`

**五个永久损失来源：** 踩第 2 条（能力圈外）；第 1 条（为增长付高价）可能也踩。

**证伪条件（复核日 2027-03）：** 2027-03-01 前发布的 FY2026 10-K 同时满足 (a) 分产品披露每次检测的单价和报销率、数据业务的剩余合同价值和净收入留存率；(b) 经营现金流 − capex − 股权激励 ≥ 0。两条都满足就重审第一关。

**引文：**「Predicting the long-term economics of companies that operate in fast-changing industries is simply far beyond our perimeter.」（1999 年报，`data/brk-annual-reports/txt/1999.txt` 第 837–838 行，agent 已 Grep 核对）

**它列的「不知道」：** 10-Q 全文没读；各项检测的单价和报销结构；剩余合同价值、净收入留存率、对 Google 等大客户的依赖；Personalis 收购价；11/10–11/16 一周跌约 20% 的原因。

## 可选动作

- **不动（默认）** = 不持有，不建仓。按项目规则，「不懂，过」到此为止，不用期望值或情景把它绕过去。
- 想继续看：先补上面「不知道」里的头三项（读 10-Q），再重跑第一关。

## 参考

- [Q3 2026 8-K 业绩稿 EX-99.1](https://www.sec.gov/Archives/edgar/data/0001717115/000119312526442619/tem-ex99_1.htm)
- [Q3 业绩会转述（MarketBeat，二手）](https://www.marketbeat.com/instant-alerts/transcript-what-tempus-ai-tem-said-on-its-q3-earnings-call-2026-11-02/)
- 前向记录：`notes/2026-11-16-value-investor-agent-eval.md` 第四节

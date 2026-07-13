---
ticker: NET
name: Cloudflare
sector: Network Security / CDN
layer: Layer 6 — 网络安全基础设施
position_type: thematic
status: watching
last_updated: 2026-07-09
data_source: scripts/fetch_quotes.py snapshot 2026-05-07 / 复核 2026-07-06
---

# Cloudflare (NET)

## ⭐ 2026-07-09:第二条叙事腿 Monetization Gateway(x402)——战略对,但作为投资论点三硬伤 `[INFERRED, MED-HIGH]`

> **一句话:方向漂亮的"卖铲子",但没有护城河、被 AWS 免费竞争、零已兑现收入——是叙事期权,不是已兑现的 franchise。在 P/S 37 顶部估值上,别为它再付溢价。**

**是什么(先纠正常见误读)**:2026-07-01 上 waitlist 的 **Monetization Gateway**,底层 **x402 协议**(复活 HTTP 402 + USDC/Base 稳定币结算)。**不是 Cloudflare 向开发者按 agent 调用收费**(那是 Workers 用量计费),而是 Cloudflare 提供**收费闸口**,让客户(内容/API/MCP 方)向来访 AI agent 收过路费,自己当"收单行"抽成。战略=把自己从"被 AI 爬虫白嫖带宽的成本中心"变成"agentic web 收费公路"。坐拥约 20% 互联网流量,是天然收费点——**卖铲子逻辑的教科书延伸,方向认可。**

**但作为 NET 投资论点,三个硬伤**:
1. **无协议护城河**:x402 是**开放协议**(Linux Foundation,成员含 AWS/Anthropic/Circle/Coinbase),Cloudflare 无独占。
2. **AWS 已免费做同样的事** `[KNOWN 2026-07, InfoQ]`:AWS CloudFront 的 x402 集成**已 GA、不额外收费**(只收标准 WAF 费);Cloudflare 的 Monetization Gateway 还只是 **waitlist、无定价、无时间表**。开放协议 + 头号云厂免费竞争 + 你还想收费 = 护城河红旗。
3. **零已兑现收入,纯双重条件期权**:waitlist 阶段。Coinbase 报 x402 一年 1.69 亿笔,但单笔"a fraction of a cent",年化金额可能微不足道。计入估值 = 买"agentic web 起来 **且** Cloudflare 收得到费"的双重赌。

**对估值的含义**:NET 现 **P/S ~37 / fwd PE 154**(复核 2026-07-06 $242.41;上一轮批量同尺子隐含 5yr IRR 仅 **+3.8%**),已泡沫顶部。市场大概率已把这条叙事 price 进去。**现在 NET = 两条诱人叙事(PQC + agentic 收费)叠顶部估值 = 好方向坏价格**,和 [[PLTR]] 同病。入场看估值,不看叙事新增。

## 一句话定位

PQC（后量子加密）合规迁移浪潮最直接的软件层受益者。卖的不是"量子能力"，是"**保险**"。

## 关键数据（基准日 2026-07-06，快照 fetch_quotes）

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **$242.41** | 较 5-07 的 $248.59 微降 |
| 市值 | **$86.0B** | |
| Forward PE | **153.6** | trailing PE 空（GAAP 微利/亏损）|
| P/S (TTM) | **36.9** | 旧表误标"Forward P/S 40.5"；顶级 SaaS 估值 |
| 52 周区间 | **$158.8 → $276.8** | 现价距高 −12% / 距低 +53% |
| 50 / 200 日均线 | $225.5 / $208.2 | 现价在两均线上方 |
| Beta | 1.67 | 对 SPY |

| 基本面（财报口径）|  |
|---|---|
| TTM 营收 | **~$2.3B** |
| 企业版占比 | ~60% ≈ $1.4B |

> **⚠️ 勘误（2026-07-09）**：旧表"总营收 ~$20B/年 / 企业版 $12B"是**数量级错误**——NET 真实 TTM 营收仅 **~$2.3B**（P/S 36.9 × 市值 $86B 反推一致），企业版 ~60% ≈ **$1.4B**。这个错误此前让人误判营收规模,现纠正。P/S ~37x 已是顶级 SaaS 估值，PQC + agentic 收费两条叙事的增量已被市场充分定价（见顶部 ⭐ 段）。

## 护城河类型

**网络位置 + 透明升级**：

- 全球互联网约 **20% 流量代理**经过 Cloudflare
- 边缘节点已默认部署 ML-KEM（FIPS 203），客户开关一行配置
- 硬件厂商升级摩擦高（要换设备），Cloudflare 透明（合规月费）
- 与零信任产品组合，每个握手都是一次 PQC 部署机会

## 短期增量（3–5 年）

**核心：Mosca 定理触发的强制迁移**

```
X(数据保密年限) + Y(迁移时间) > Z(量子破解还有多少年)  →  你已经输了
```

银行案例：30 + 5 > 5 → 今天的客户数据已经不安全 → 必须**今天**就迁移。

**全球 PQC 合规支出估算 $200–500B**：
- Cloudflare 占 5–10% = $10–50B 增量
- 5 年分摊：每年 $2–10B 增量收入
- 杠杆是合同等级升级（一个金融客户从 $50K → $200K/年）

**政府强制令时间表**：
- 加拿大 2026/4 计划 → 2031 高优先级 → 2035 全部
- NSA CNSA Suite 2.0 — 2033 默认遵守
- 美国联邦机构 — 2035 完成
- Google 内部 — 2029 完成

## 长期增量（10–20 年）

- 即便量子永远不工作，Cloudflare 仍赚到 PQC 钱（合规已定）
- 若某种 PQC 算法被破解（如 SIKE 已破解的前车），是**重复收入机会**

## 风险

- **大云厂内化**：AWS、Azure、Google Cloud 都在做 PQC，长期可能内化吃掉份额
- **算法翻车**：如 ML-KEM 被发现漏洞，整个部署要第二次重做
- **监管时间表滑动**：2035 听起来"远"，组织会拖
- **估值不便宜**：高 P/S 倍数，对增速敏感

## 估值锚

- Forward P/S 已在 20x+ 区间
- 类比：Akamai (AKAM) Forward P/S 5x，但增速远低
- 故事溢价应在 PQC 强制令第一波（2026–2028）落地时达到峰值

## 退出条件

- **触发减仓**：AWS/Azure 推出与 Cloudflare PQC 直接对位的免费层产品；**或 Monetization Gateway 正式定价后被 AWS CloudFront 免费 x402 集成压制(采用/take-rate 起不来)——证伪 agentic 收费叙事**
- **触发卖出**：Q-Day 显著推后（量子破解资源估算反向上调）
- **再加码**：任何政府 PQC 强制令收紧 / 提前

## 跟踪信号

- 季度企业版 NRR (Net Revenue Retention)
- 每年 NIST FIPS 标准更新与 PQC 算法状态
- 合规驱动客户的合同等级跳升数据
- 中美 + 欧盟 PQC 监管要求变动

## 参考

- 主题笔记：[2026-05 AI/机器人/量子产业链](../notes/2026-05-ai-robotics-quantum-supply-chain-v1.md#7.5)（第七部分 PQC 深度）

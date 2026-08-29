---
date: 2026-06-24
type: thesis + correlation-check
status: active
purpose: 评估"token=AI 时代的电"这个类比，拆 token 经济的价值链，并实测"字面电力"那条腿对半导体书的相关性。**2026-08-29 补 §二.1：原表漏了「调度+结算」整层，而 Stripe 以 $70–80 亿收购 OpenRouter 刚给这层标了价**
holder_context: 用户重仓 token 经济的"涡轮机"格(NVDA/TSM/HBM/光/网络)=最赚钱但最周期;在找非相关、抗通缩的腿
related: 2026-06-24-memory-storage-cycle-mechanics.md · 2026-06-21-ai-value-chain-layer-fill.md · organic-growth-screen(memory) · **2026-08-20-ai-ipo-wave-and-agent-layer.md**(Stripe 若 IPO 与「发行在放量」同族) · memory `llm-relay-sub2api-assessment`(网关层的合规边界)
---

# "Token 是 AI 时代的电"——类比对错 + 谁真正拥有电

## 一句话

**类比对一半：token 确实是 AI 的计量消费单位(量会因 Jevons 爆炸)。但正因为它"是电"——商品、每年通缩 ~90%、底端 race to zero——所以裸拥有 token 生产是赔本买卖。钱在电子之外：涡轮机(你已重仓、最周期)、字面电力(实测仅中等不相关,非干净对冲)、价值捕获层(GOOGL/META/PLTR,抗通缩)。**

> ⚠️ 注意来源：「AI 工厂生产 token」最大推手是黄仁勋——利益相关方框架(你信 token=电就多买 GPU)。`[INFERRED]`

## 一、类比哪里成立，哪里塌 `[COMMON/KNOWN]`

**成立**：① 计量消费(kWh / 百万 token，usage-based) ② 万能投入 ③ Jevons 弹性(越便宜用越多，量爆炸——volume 多头真实)。

**塌掉(更重要)**：
1. **电子完全同质，token 不是**：前沿 token(推理/可靠)≠ 弱模型 token。底端商品化、前沿仍溢价——**分叉,不是统一商品**。
2. **没有"token 电网"**：各模型商 token 不互换、有锁定，不像电即插即换。
3. **致命——通缩速率**：电价百年稳定；**token 每年崩 ~10x**。单价每年跌 90% 的东西**不是稳定公用事业，是通缩科技品** → 打死"拥有 token 收费公路躺收过路费"的幻想。
4. **成本结构**：大头是训练模型的固定 R&D，且模型几个月作废(专利悬崖) → 像"叠在公用事业上的创新药"。

**结论** `[INFERRED, MED-HIGH]`：作为需求叙事对(量爆)，作为投资结论错——**token 越像电，产 token 越像卖电：商品、零毛利。**

## 二、谁拥有电——电力业赚钱的从来不是电子

| 电力业 | 赚钱逻辑 | token 经济对应 | 标的 | 对你 |
|---|---|---|---|---|
| **电子本身** | ❌ 商品零毛利 | 纯模型商/token 本身 | OpenAI/Anthropic/Llama/DeepSeek | 价格战通缩，**别裸拥有** |
| **涡轮机/设备** | ✅ 卖铲子 | 造 token 的机器 | **NVDA/TSM/HBM/网络/光** + **GEV** | **你已重仓——最赚但最周期** |
| **电网/收费** | ✅ 受监管过路费 | 分发+计量的云 | MSFT/AMZN/GOOGL 云 | 部分持有(GOOGL) |
| **稀缺燃料/选址** | ✅ 卡脖子 | **字面的电** + 先进封装/HBM | **CEG/VST** + TSM CoWoS | **最缺的格,但见下方修正** |
| **终端价值捕获** | ✅ 拥有客户/数据/工作流 | 买便宜 token 卖贵结果 | **PLTR / GOOGL / META** | **抗通缩,该补** |
| **🔴 调度 + 结算**<br>**(2026-08 补，原表漏了)** | ✅ **ISO/RTO：实时按价调度 + 计量清算** | **路由 + 计量 + 收付** | **OpenRouter → Stripe**（私有）· LiteLLM（开源） | **不可直投，但见 §二.1** |

## 二.1 ⭐ 2026-08 补：这张表漏了一整层——而那层刚被标价 $70 亿

`[KNOWN, HIGH——Stripe 官方新闻室 2026-08-19 · Bloomberg · TechCrunch · CNBC · Axios]`

### 事件

| | |
|---|---|
| **Stripe 收购 OpenRouter** | **2026-08-19 官宣**（8/16 Bloomberg 先曝）；**Bloomberg >$70 亿 / NYT $75 亿 / Axios >$80 亿**（现金+股票）；创始人分得 **$15 亿** |
| **估值跳升** | 5 月 Series B 才 **$13 亿** → **5.4 倍，三个月** |
| **OpenRouter 体量** | ARR **$1.4 亿**（2026-07；2025 年底 $5,000 万）；**400+ 模型 / 80+ 供应商 / 1000 万开发者**；客户含 **NVIDIA、Zoom、Lovable** |
| **抽成** | **约 5%**（credit 购买 5.5%） |

### 🔴 我漏掉这一层是个方法错误，不是信息错误

**电力市场里，ISO/RTO（PJM、ERCOT）本来就同时做「实时调度」和「计量清算」——这是电力市场的既有结构。**

> **所以类比本身预测了这次合并。是我 6/24 写这张表时没把类比用完，整层没写。**
> **`[INFERRED]` 教训：类比的价值在于「照着原型逐层点名」，而不是只挑自己已经想到的格填。**

### ⭐ 判断：结算层比调度层更上游

**依据不是推理，是方向——被收购的是调度层，收购方是结算层，不是反过来。**

**而且 Stripe 的拼图是四块，OpenRouter 是最后一块：**

| 时间 | 动作 | 补的位置 |
|---|---|---|
| 2026/2 | 收购 **Metronome**（用量计费——因 Stripe Billing 扛不住真实用量计费） | 计量底座 |
| Sessions 2026 | **Token Billing**：LLM token 原生计量 + **自动加价** | **收入侧** |
| Sessions 2026 | **Agentic Commerce Suite**（首发伙伴 OpenAI / Perplexity / Vapi） | 支付形态 |
| **2026/8** | **OpenRouter** | **成本侧** |

> ## **拼起来：Stripe 同时握住 AI 公司的收入侧（向客户收钱）和成本侧（向模型厂付钱）= 想当 AI 公司毛利率的托管方。**

**Collison 原话**：token 是用 AI 构建的公司的**核心货币**。
分析师 Franco Granda：这是 Stripe **主动把自己嵌进 AI 时代资本流的中间**。

### ⭐ 费率套利：14 倍

`[COMPUTED；Stripe 净 take rate 0.36% 为单一来源，但支付处理商 0.3–0.4% 属行业常识，量级可信——MED]`

| | 抽成率 |
|---|---:|
| Stripe 自己（支付） | **~0.36%** |
| OpenRouter（推理支出） | **~5%** |

**同一个商业模式（坐在流量中间抽一刀），这一刀厚 14 倍。Stripe 的核心业务是结构性通缩的费率，OpenRouter 是一条还没被压过价的新水管。**

**反推**：$1.4 亿 ÷ 5% = **约 $28 亿年化推理支出流经**；**$70 亿 ÷ $1.4 亿 = 50 倍 ARR**。

### 🔴 但这笔买卖最可能这么错（四条）

1. **5% 撑不住**——聚合层高费率是早期租金不是护城河。压价来自模型厂自建路由（OpenAI/Anthropic 的 model picker）、云厂商（Bedrock/Vertex 天生是多模型网关）、大客户议价（**客户名单里有 NVIDIA**）。**而把支付费率压到 0.36% 的历史，主角正是 Stripe 自己。**
2. **50 倍 ARR**——即便 ARR 再翻三倍到 $4.2 亿，仍是 17 倍。
3. **⭐ 中立性悖论**——OpenRouter CEO Atallah 说「开发者需要一个**中立层**」，然后公司被支付巨头买了。**中立是它唯一真正的资产，而收购这个动作本身就在损耗它。**
4. **利益冲突已存在**——Stripe 的 Agentic Commerce 首发伙伴是 OpenAI，同时它现在拥有决定「用哪个模型」的路由层。**不是潜在冲突，是当下的。**

### 对本书的实际含义

- **Stripe 私有，不可直投。** 这条的价值是**给「AI 中间层」标了价**（50x ARR、2.5x 流经 GMV）。
- **补腿清单不变**：§四 的优先级（价值捕获层 > 字面电力）不受影响。
- **⚠️ 但要注意方向**：结算/调度层的商业模式（抽成）和 §一「token 每年通缩 90%」是**对冲关系**——**单价跌但流量涨，按 % 抽成的人不怕通缩。** 这是这一层相对模型厂的结构性优势，也是它值 50x 的辩护理由。

## 三、⚠️ 实测修正：字面电力**不是**干净对冲腿（我此前高估）

上一轮口头说电力是"像 MP/NFLX 那样的非相关腿"——**实测打脸，订正如下。** `[COMPUTED 2026-06-24]`

| | 角色 | betaSPY | betaSOXX | **corr 半导体书(均)** | 1 年 | fwdPE |
|---|---|---|---|---|---|---|
| **CEG** | 核电/merchant 发电(真握电) | 1.47 | 0.48 | **0.34** | **-15%** | 20x |
| **VST** | merchant 发电(真握电) | 1.61 | 0.56 | **0.38** | -12% | 14.8x |
| **GEV** | 涡轮机制造(卖铲子) | 1.99 | 0.67 | **0.46** | **+103%** | 42x |
| NRG | 发电/零售 | 1.51 | 0.55 | 0.39 | -9% | 11.9x |
| SMR/OKLO | 前期核电(投机) | ~4.0 | ~1.2 | ~0.37 | -75% / -6% | 负(无盈利) |

**对照真·非相关腿**：NFLX 0.05-0.09、IBM 0.08-0.18、MP(corrNVDA 0.24)。

**读数**：
1. **电力是"中等相关"(0.34-0.46)，不是"低相关"**。原因：市场把"AI 数据中心耗电"当**同一个 AI buildout 篮子**交易，电力股跟 AI 情绪同涨跌。**真正 AI-capex 急跌那天，电力会跟着跌(corr 0.4)，不是旁观。** 它比再加一只半导体干净(半导体彼此 0.5-0.78)，但够不上 NFLX/IBM 那种 orthogonal。
2. **GEV 不是"握电"，是又一只 picks-shovels AI 股**(beta 1.99、corr 0.46、+103%、42x)——和你 NVDA 那格同质，**不解决集中度**。
3. **真正"拥有电"的是 CEG/VST(发电资产)**：相关性更低、更便宜、且今年**跌了**(像 NFLX/META 一样 de-rate 过，不是追高)。
4. **CEG-VST 彼此相关 0.80**(都是核电/merchant 发电，同一笔赌注)——**别两个都买，二选一**(VST 更便宜 14.8x，CEG 核电纯度更高 20x)。
5. **SMR/OKLO 排除**：beta ~4、无盈利(fwdPE 负)、SMR 1 年 -75%——投机品，踩资本保全雷③，不碰。

## 四、资本保全结论

- **token=电 的真正投资含义**：别拥有通缩的 token，拥有它周围稀缺的东西。
- **你书的诊断**：重仓"涡轮机"格(token 经济里真赚钱处)，但=最周期(绑 capex + 内存周期)。
- **补腿优先级**：
  1. **价值捕获层(GOOGL 已有 / META 刚补 / PLTR)** —— **抗 token 通缩**(买便宜 token 卖贵结果)，自驱动非周期，是比电力更该补的格。
  2. **字面电力**：可作"驱动因子不同"的腿，但**认清它中等相关(0.4)、急跌时会跟跌**；若要，选 **VST 或 CEG 二选一**，估值已回落非追高，当"半个分散 + 物理瓶颈 beta"持有，不是干净对冲。
- **明确排除**：GEV(伪握电、贵、AI 同质)、SMR/OKLO(投机)。

## 五、跟踪
- token 价格/百万 token 趋势(通缩速率是否放缓 → 模型商喘息)。
- 数据中心电力并网/GW 排队、燃气轮机交期(GEV 订单簿)、PJM 容量拍卖价(CEG/VST 现金流)。
- 价值捕获层：谁把便宜 token 转成有定价权的结果(应用层 ARR、毛利)。
- **🔴 结算/调度层(2026-08 新增)**：
  - **OpenRouter 的 5% 抽成会不会被压**——这是 §二.1 反驳①的直接读数，也是 50x 估值的生死线。
  - **模型厂是否自建路由**(OpenAI/Anthropic 的 model picker 是否对外开放为 API)、**云厂商 Bedrock/Vertex 的多模型网关**渗透率。
  - **中立性是否被侵蚀**：Stripe 是否开始把流量导向对自己经济最优的模型(可从 OpenRouter 的模型份额变化观察)。
  - **Stripe 是否 IPO**——与 notes/2026-08-20 的「发行在放量、承接在恶化」那条同族。

## 六、来源
- 实测 beta/相关性：yfinance CEG/VST/GEV/NRG/SMR/OKLO vs 半导体书(2026-06-24)。
- token 价格通缩 ~10x/年、模型作废节奏：`[KNOWN ≤2026-01]`。
- 电力瓶颈(GW/并网/核电复兴)：`[KNOWN 2025]`，具体 2026 数据待 WebSearch 补。
- **§二.1 (2026-08-29 补)**：
  - [Stripe 官方新闻室 — 同意收购 OpenRouter](https://stripe.com/newsroom/news/stripe-agrees-to-acquire-openrouter)
  - [Bloomberg — 敲定 $70 亿+ 收购](https://www.bloomberg.com/news/articles/2026-08-16/stripe-nears-deal-to-buy-ai-firm-openrouter-for-over-7-billion)
  - [TechCrunch — Stripe 买 OpenRouter 并不是因为"奇点"](https://techcrunch.com/2026/08/19/stripe-didnt-really-buy-openrouter-because-of-the-singularity/)
  - [Axios — 交易规模 >$80 亿](https://www.axios.com/2026/08/17/stripe-openrouter-paypal)
  - [OpenRouter 官方博客 — 加入 Stripe](https://openrouter.ai/blog/announcements/openrouter-is-joining-stripe/)
  - [Sacra — OpenRouter 营收/估值/费率](https://sacra.com/c/openrouter/)
  - [BusinessModelAnalyst — $70 亿买 5.5% 费率，自己只有 0.36%](https://businessmodelanalyst.com/stripe-openrouter-take-rate-arbitrage/)
  - [Stripe — Sessions 2026 共 288 项发布](https://stripe.com/newsroom/news/sessions-2026)
  - [PYMNTS — Stripe 推 AI 用量计量与计费](https://www.pymnts.com/news/artificial-intelligence/2026/stripe-introduces-billing-tools-to-meter-and-charge-ai-usage/)

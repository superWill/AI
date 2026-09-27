---
date: 2026-09-22
type: 产业地图 / agent 层
status: active
data_source: 子 agent 50 次 WebSearch + ~30 次 WebFetch（2026-09-22）；一手：Alphabet Q2 财报、Microsoft FY26Q4、Salesforce Q2 FY27、ServiceNow Q2、Palantir Q2、Anthropic/Meta/Stripe 官方公告、Ramp AI Index 8 月、Menlo 消费者报告 9 月、SEC（SpaceX 换股）；Bloomberg/CNBC 多为 403 摘要，聚合站数字全部标 ⚠
purpose: 回答「现在的 AI agent 有哪些」，按真实采用而不是功能排；给 8/20 笔记「agent 层」补一张有数字的地图
related: notes/2026-08-20-ai-ipo-wave-and-agent-layer.md（Grok Bot 观察项）· notes/2026-06-24-token-is-electricity-value-chain.md（OpenRouter/Stripe）· memory market-adoption-leading-signal
---

# AI Agent 地图（2026-09-22）：采用集中在编码和企业客服，消费级通用 agent 刚开局

## 一句话

`[INFERRED, HIGH]` 按「谁有真实采用」排，agent 只有两类已经成生意：**编码 agent**（Codex 20M WAU、Cursor $3B ARR、Claude Code $2.5B 年化、Antigravity 2.4M WAU）和**企业客服/CRM agent**（Agentforce $1.5B ARR、ServiceNow AI ACV $1B、Sierra $200M）。**消费级「帮你做事」的通用 agent 2026 年三家大厂各砍过一次形态**（OpenAI Atlas 8 月下线、Google Mariner 5 月关停、OpenAI Instant Checkout 3 月回退），Meta Muse 上线 12 天就被 Amazon 封，是这个品类最诚实的状态。

## 一、总量锚点 `[KNOWN, HIGH]` 除标注

| | 数字 | 来源 |
|---|---|---|
| Anthropic 年化收入 | **$65B**（7 月末；2 月 $14B → 5 月 $47B），估值 $965B，已秘密递交 IPO | Bloomberg via TechCrunch 8/17 |
| OpenAI 年化收入 | >$40B（8 月）；coding + work 产品 20M WAU | Bloomberg 8/13 ⚠摘要 |
| Gemini app | **950M MAU**，AI Mode >1B | Alphabet Q2 财报 |
| M365 Copilot | **>30M 付费席位**（单季 +10M） | MSFT FY26Q4 |
| 企业付费份额（Ramp 8 月） | **Anthropic 43.5% / OpenAI 39.7% / xAI 4%**；企业 AI 采用率 3 月首破 50% | Ramp AI Index |
| 消费者（Menlo 9 月，n=5,067） | 64% 美国成人用 AI；AI 用户中 41% 试过 agent、24% 常用、32% 允许不确认就行动；agent 份额 Codex 35% / Claude Code+Cowork 32% / Perplexity 24% | Menlo |
| 流量份额（Similarweb） | ChatGPT 76% → 53%，Gemini 9% → 27%，Claude 2% → 9%（2025-06 → 2026-05）| ⚠二手 |

## 二、按类别（★ = 有硬采用数据）

### 1. 编码 agent ★★★
| 产品 | 采用 | 置信 |
|---|---|---|
| OpenAI Codex | 5M WAU（6 月）→ 8M（7 月）；coding+work 20M WAU（8 月） | HIGH/MED |
| Cursor | ARR $3B（5 月，Bloomberg）；**被 SpaceX 以 $60B 全股票收购，8/14 交割**（SEC：换 3.89 亿股 SpaceX A 类） | HIGH |
| Claude Code | 年化 $2.5B（2 月），8–9 月无更新 | MED ⚠聚合站 |
| Google Antigravity | 2.4M WAU（Q2 财报），ADK 累计 70M 下载 | HIGH |
| GitHub Copilot | 4.7M 付费订阅（FY26Q2，+75%） | MED |
| Cognition（Devin + Windsurf） | ARR $492M（5 月），Series D $26B；「$900M」单源 | MED/LOW |
| Replit / Lovable | ARR ~$525M / $400–500M | LOW-MED ⚠聚合站 |

### 2. 企业 / 工作流 agent ★★★
- **Salesforce Agentforce**：ARR >$1.5B（+240%），Agentforce + Data 360 $3.9B；累计 70 亿「Agentic Work Units」。⚠ 本季起口径并入 Slackbot 等，可比性打折。
- **ServiceNow**：AI ACV 首破 $1B（+40% QoQ），agentic 生产部署 9 个月 9 倍。
- **Microsoft Agent 365**：5/1 GA，两个月 ~40M agent 注册。
- **Google Gemini Enterprise**：「~90% Fortune 100 在用」，客户数未披露。
- **Palantir**：美国商业收入 $764M +149%（Q2），agent 专属数据无。
- **垂直 agent**：Sierra ARR $200M / 估值 $15.8B（客服，按对话或按解决收费）；Decagon $100M / $4.5B；Harvey $400M / $15.5B（法律，$1,200/律师/月，1,500+ 客户）；Glean $300M（官方）。
- **定价形态在变**：按对话、按解决结果、按 agent 用量（Workday Flex Credits）——从 seat 转向 outcome，这是 SaaS 估值模型要重算的地方。`[INFERRED, MED]`

### 3. 消费级通用 agent ★
- **Meta Muse**（9/8 上线）：Sensor Tower 902K / 6 天，9/18 登顶美区 App Store 超 ChatGPT；Apptopia 2.8M 全球 / 12 天、美国 DAU 642K（ChatGPT 同期 231K）、95% 用户同时是 Facebook 用户。跑在专属云 VM 里能开浏览器、填表、付款。**9/20–21 Amazon 封杀**（不自报 agent 身份、保留用户凭证）。META +11%。
- **Anthropic Claude in Chrome**：8/26 GA，可自主执行；官方红队注入成功率 0–0.3%。用户数未披露。Claude Cowork（1 月桌面 agent）。
- **OpenAI**：ChatGPT agent（2025-07）；Atlas 浏览器 2025-10 上线 → **2026-08-09 下线**，并回 ChatGPT + Codex「超级应用」；Jony Ive 硬件 H2 2026。
- **Google**：Project Mariner **5/4 关停**，并入 Gemini Agent Mode；Gemini 950M MAU 是底盘。
- **Apple**：WWDC 6/8「Siri AI」，重推理路由到 Gemini，消费者 beta 稍后，EU 延迟。
- **Amazon**：5/13 Rufus 并入 Alexa+ 改名「Alexa for Shopping」，成美区默认 AI 层；Rufus 2025 年 300M+ 顾客用过；agent 功能 = 到价自动买、定期补货。**Amazon 的策略是自己做 agent + 封别人的 agent。**
- **xAI（SpaceXAI）**：Grok Bot 8/11 beta（$120–300/月档），见 8/20 笔记；企业付费份额 4%。
- **Perplexity Comet**：MAU 3M vs 18M 两源冲突，UNKNOWN。

### 4. Agentic 商务 / 支付 ★
- OpenAI Instant Checkout：2025-09 上线 → 2026-03 仅 ~30 家 Shopify 商户接入，错误多、无购物车 → **回退为「商户控制结账」，AI 只管发现 + 意图**。
- Stripe 收购 OpenRouter（8/16–19，$7–8B，冲突），8M 用户、400+ 模型——支付层买下路由层，见 6/24 笔记。
- Google AP2（60+ 伙伴）+ UCP（Shopify/Target/Walmart 背书）；Visa Intelligent Commerce 只披露「数百笔」试点交易。**agent 支付的真实交易量 2026 年仍是零头。**
- 反方向：Amazon 封 Muse + 数十个 agent；Cloudflare 9/15 起默认封混合用途爬虫、Pay Per Crawl 转 Pay Per Use。**内容方和零售方在 2026 年集体收门票，agent 的「免费通行」时代结束。**`[INFERRED, HIGH]`

### 5. 基础设施 / 协议
- MCP：97M+ 月 SDK 下载、10K+ 公开 server（2025-12 官方），已捐 Linux Foundation；企业生产使用率 41%（Stacklok）vs 78%（聚合站），取 41%。
- Google ADK 70M 下载；A2A 采用数 NOT FOUND；LangChain $16M ARR（2025 旧数）。

### 6. 中国
- 豆包 345M MAU（Q1，第一）；**6 月上线订阅（¥68/200/500）当月掉 6.1M 用户**——付费意愿的直接读数。
- Qwen app 100M（1 月）→ 167M（5 月），1 月打通淘宝购物。DeepSeek ~130M。Kimi 90M vs 10–15M 冲突，UNKNOWN。
- Manus：Meta 收购（2025-12，$2–3B）被发改委 4/27 叫停 → 8/11 宣布独立运营；ARR $125M（2025-12）。
- 智谱 1 月港股 IPO，OpenRouter 份额 5.6%。

### 7. 物理 agent（一行）
Optimus 累计「低几百台」（V3 H2 量产为目标非实绩）；Figure「1 万台部署」疑夸大；NVIDIA GR00T N2 预览。全部 LOW。

## 三、2026 年的摩擦事件（比产品发布更有信息量）

1. 三家大厂各砍一次 agent 形态：Atlas 下线、Mariner 关停、Instant Checkout 回退。
2. Amazon 封 Muse（9/20），把主流消费 agent 当未授权入侵者。
3. 豆包收费掉 6.1M 用户。
4. PocketOS（4 月）：编码 agent 一次调用删掉生产库 + 备份（单源 MED-LOW）；LiteLLM PyPI 后门被自主攻击 bot 拉入 47K 下载（OWASP）。
5. Gartner 4 月 Hype Cycle 把 Agentic AI 放在「期望膨胀顶峰」；预测 40%+ agentic 项目 2027 底前取消。McKinsey：仅 23% 企业在 scaling agent。

## 四、投资含义 `[INFERRED, MED]`

- **卖铲子的层级已经清楚**：模型商（Anthropic/OpenAI，收入 $105B+ 合计年化）→ 编码 agent（最硬）→ 企业 agent 平台（CRM/ITSM 现有分发优势）→ 消费 agent（未验证）→ agent 支付（零头）。越往下越是故事。
- **上市可买的 agent 收入**：CRM（Agentforce $1.5B）、NOW（AI ACV $1B）、MSFT（30M 席位）、GOOGL（Antigravity + Gemini Enterprise）、PLTR。私有的 Cursor/Cognition/Sierra/Harvey 全在一级市场，Cursor 已进 SpaceX。
- **Meta 是本周的变量**：Muse 的 12 天数据是消费 agent 第一个像样的采用读数，但 Amazon 封杀说明分发权在零售商手里。Muse 若要付款，要么谈判要么走 Meta 自己的商务闭环——这是 META 而不是 AMZN 的问题。
- **对 8/20 笔记 Grok Bot 观察项**：xAI 企业份额 4%，Grok Bot 无用户数，Cursor 并入 SpaceXAI 后 xAI 的 agent 入口是 Cursor 不是 Grok Bot。
- **不做的事**：不因 agent 叙事买 NET（Cloudflare 收门票是防守不是增量）、不买 agent 支付概念（Visa 数百笔）。

## 冲突 / 待核实

Muse 下载三口径（Sensor Tower 902K/6d、730K/10d 美国、Apptopia 2.8M/12d）；Cursor ARR $3B vs $4B；Stripe-OpenRouter $7–8B；Comet MAU；Kimi MAU；MCP 企业采用率；Copilot 家族 MAU 150M vs 420M；Harvey 9 月轮 / Cognition $900M / Lovable $13.3B / Replit $525M 全部只有聚合站。Dia / Opera Neon / Jules / Kiro / 百度 / A2A 未查。

## 参考（一手优先）

- [Alphabet Q2 2026](https://blog.google/company-news/inside-google/message-ceo/alphabet-earnings-q2-2026/) · [Microsoft FY26Q4](https://news.microsoft.com/source/2026/07/29/microsoft-cloud-and-ai-strength-fuels-fourth-quarter-results-4/) · [Salesforce Q2 FY27](https://www.salesforce.com/news/press-releases/2026/08/26/fy27-q2-earnings/) · [ServiceNow Q2 2026](https://newsroom.servicenow.com/press-releases/details/2026/ServiceNow-Reports-Second-Quarter-2026-Financial-Results/default.aspx) · [Palantir Q2 2026](https://www.businesswire.com/news/home/20260802523449/en/)
- [Anthropic $65B（TechCrunch 8/17）](https://techcrunch.com/2026/08/17/anthropics-annualized-revenue-surges-to-65b/) · [Claude in Chrome GA](https://claude.com/blog/claude-in-chrome-generally-available) · [Meta Muse 发布](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) · [Muse 超 ChatGPT（TechCrunch 9/21）](https://techcrunch.com/2026/09/21/metas-muse-is-outpacing-chatgpts-early-mobile-launch/) · [Amazon 封 Muse（SiliconANGLE）](https://siliconangle.com/2026/09/21/amazon-blocks-metas-muse-agent-from-shopping-on-users-behalf/) · [Atlas 下线](https://help.openai.com/en/articles/20001371-evolving-atlas-into-chatgpt-for-browser-based-agentic-work) · [Codex 5M WAU](https://www.constellationr.com/insights/news/openai-touts-broadening-codex-usage-5-million-weekly-active-users) · [Cursor 被 SpaceX 收购](https://en.wikipedia.org/wiki/Cursor_(company)) · [Agent 365 GA](https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/) · [Glean $300M](https://www.glean.com/press/glean-surpasses-300m-arr-unrivaled-enterprise-context-fuels-ai-adoption)
- [Ramp AI Index 8 月](https://ramp.com/data/ai-index-august-2026) · [Menlo 消费者 AI 2026](https://menlovc.com/perspective/2026-the-state-of-consumer-ai/) · [Gartner 40% 取消](https://www.gartner.com/en/newsroom/press-releases/2025-06-25-gartner-predicts-over-40-percent-of-agentic-ai-projects-will-be-canceled-by-end-of-2027) · [Sacra：Sierra](https://sacra.com/c/sierra/) · [Sacra：Harvey](https://sacra.com/c/harvey/) · [Stripe 收购 OpenRouter](https://stripe.com/newsroom/news/stripe-agrees-to-acquire-openrouter) · [Shopify UCP](https://shopify.engineering/ucp) · [Cloudflare 收费爬取](https://techcrunch.com/2026/07/01/cloudflares-new-policy-pushes-ai-companies-to-pay-for-publishers-content/) · [豆包掉用户（SCMP）](https://www.scmp.com/tech/big-tech/article/3355782/china-ready-pay-ai-bytedances-doubao-loses-6-million-users) · [Manus 独立](https://en.wikipedia.org/wiki/Manus_(AI_agent)) · [OWASP Q1 2026](https://genai.owasp.org/2026/04/14/owasp-genai-exploit-round-up-report-q1-2026/)

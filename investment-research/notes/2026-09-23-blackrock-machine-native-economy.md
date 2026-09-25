---
date: 2026-09-23
type: 报告研读 / 稳定币与代币化主题
status: active
data_source: 一手：BlackRock Digital Assets Research 白皮书《The Machine-Native Economy》PDF 全文（子 agent 下载 + pypdf 提取逐字核对）；Fink 2026 年度信（WebFetch 直读）；BlackRock Thematic 2026 中期展望；CoinDesk 2026-03-24 Mitchnick 讲话；a16z crypto 2026-05 RWA 数据汇总；BIS 2026 年报 Ch.III。二手：金色财经/BlockTempo/PANews 转载、eco.com 转引 rwa.xyz、CryptoSlate 转述 IMF
purpose: 用户转来一段中文摘要（「大模型 token 和资产 token 是同一件事」），找到原文、核对措辞被改了多少、报告到底主张什么、有什么软肋，以及对 CRCL 持仓（5%，5 年 venture）和 V/COIN 观察档案的含义（V/COIN 未持有，持仓真相源是 portfolios/）
related: notes/2026-06-24-token-is-electricity-value-chain.md（OpenRouter/Stripe，算力即货币）· notes/2026-09-22-ai-agent-landscape.md（agent 支付「零头」判断）· tickers/V.md · tickers/COIN.md · tickers/CRCL.md · memory single-source-confirming-thesis-low-confidence
---

# 贝莱德《The Machine-Native Economy》：类比是真的，「同一件事」是改写者加的

## 一句话

`[KNOWN, HIGH]` 出处是贝莱德数字资产研究部 **2026-09-22** 发布的 11 页白皮书《The Machine-Native Economy: How digital assets connect intelligence, commerce, and compute》，作者 Will Su / Robert Mitchnick / Jay Jacobs / William Helm。「LLM 分词 ≈ 资产代币化」确实是全文三大论点的第一条，但原文措辞是 **"analogous" / "functionally comparable, though technically distinct" / "The functions are distinct"**——中文摘要把这些保留语抹平成「同一件事」，「动手的格式」「同步数据」是改写者加的。**报告的真正主张不是这个类比，是三段推论：AI 是机器原生智能 → agent 需要机器原生货币（稳定币）→ 算力会成为新的数字资产。** 这是一份产品叙事文件，不是市场研究。`[INFERRED, HIGH]`

## 一、原文逐字（对应用户那段摘要）

Executive Summary 第一条（p.2）：
> "LLMs and blockchains share analogous tokenization architectures. Large language models divide human language into tokens and encode them numerically for model interpretation and processing. Blockchains similarly represent economic value and entitlements as digital asset tokens designed for machine-verifiable transfer and settlement. **The functions are distinct**, but both workflows translate real-world inputs into formats that machines can use natively."

正文小标题（p.3）：
> "AI and digital asset tokenization convert real-world inputs into machine-native representations"

正文（p.3）：
> "At the architectural level, tokenization in artificial intelligence and digital assets serves an analogous purpose: translating information and economic entitlements into discrete, standardized representations that machines can process natively. AI tokens encode information, while digital asset tokens represent units of value, ownership, or economic claims."
> "Blockchains apply a **functionally comparable, though technically distinct**, process to stores of value and economic claims."

对应「查余额、链上结算」（p.4）：
> "Through programmable interfaces, agents can evaluate balances and rules before executing authorized transactions and verifying settlement, with limited reliance on manual processes."

总纲（p.2）：
> "AI represents machine-native intelligence, while digital assets represent machine-native money."

Figure 1 是双栏对照图："AI is changing the world" → tokens → 数字 ID → embedding 矩阵 ‖ "$100 beneficial interest in a money market fund" → 代币化基金份额 → 编码交易字段 → 链上记录。**这张图就是中文两句话的视觉原型**，例子暗指 BUIDL 但全文未点名任何贝莱德产品。

**措辞核对表** `[COMPUTED]`

| 中文摘要 | 原文 | 判定 |
|---|---|---|
| 在做同一件事 | analogous / functionally comparable, though technically distinct | **强化**，原文三处留保留语 |
| 翻译成机器能直接读、动手的格式 | translate real-world inputs into formats that machines can use natively | 「动手」是引申（原文另处讲 agentic AI 「toward real-world action」）|
| 切成 Token | divides human language into tokens | 对应 |
| 查余额、链上结算 | evaluate balances… verifying settlement | 对应 |
| 同步数据 | 无 | 加的 |

中文最早转载是 9/23 金色财经，那版贴近原文；用户手里这版是二次口语化改写，来源 NOT FOUND。

## 二、报告结构与三大论点 `[KNOWN, HIGH]`

1. **架构类比**（上）。
2. **Agentic commerce 需要机器原生支付轨道**：「stablecoins, native cryptoassets, and other on-chain assets can serve as machine-native instruments for payment and settlement」；ACH/卡网络「less suited to always-on, very low-value transactions requiring programmable execution」。协议栈：MCP（Anthropic 2024-11）、A2A（Google 2025-04）为基础层；支付层 x402（Coinbase）、MPP（Stripe+Tempo）、ACP（Stripe+OpenAI）、AP2（Google）、TAP（Visa）。合规：AML/KYC/**KYA（know-your-agent）**链下做、结果上链。
3. **算力成为新的数字资产**：「Analyst estimates suggest that hyperscaler cloud revenues could exceed $1 trillion annually by 2030… standardized claims on compute capacity could become a significant digital asset use case」；x402 可按 per-use / per-model-token / per-job 结算。

**报告内数字**（脚注来源）

| 项目 | 数值 | 来源 |
|---|---|---|
| 稳定币流通市值 | >$300B（2026-09） | RWA.xyz |
| 稳定币 2025 调整后交易量 | >$11T，「same broad range as Visa and Mastercard」 | Visa/Allium；**脚注自认「not directly comparable」** |
| ACH 2025 | $93T | Nacha |
| 稳定币 2020–25 CAGR | 80%（ACH ~8.5%） | |
| AI capex 2025–30 累计 | >$5T | Goldman |
| 三大云 2030 合计收入 | ~$1.1T，29% CAGR | Bloomberg 一致预期 2026-08-31 |
| OpenRouter | >400 模型 / >80 供应商，Stripe 2026-08 收购 | Stripe |

**没有的东西**：RWA 市场规模预测（无「$x 万亿 by 2030」）；BUIDL/IBIT/DTCC 一字未提；唯一的实证「agent 偏好稳定币付款、比特币储值」来自 Bitcoin Policy Institute 的**模拟**，原文自注「reflect simulated model responses rather than observed agent behavior」。结论段自己降温：「The ecosystem remains nascent, with agentic payment activity and compute-market liquidity still limited.」

## 三、贝莱德这条叙事的演化 `[KNOWN, HIGH]`

| 日期 | 出处 | 关键句 |
|---|---|---|
| 2025-03 | Fink 2025 年度信 | 「Every stock, every bond, every fund—every asset—can be tokenized」「If SWIFT is the postal service, tokenization is email itself」 |
| 2025-12 | Fink & Goldstein，The Economist | 「a bond is still a bond, even if it lives on a blockchain」；代币化 ≈ 1996 年互联网 |
| 2026-03-23 | Fink 2026 年度信 | 「tokenization today may be roughly where the internet was in 1996」；数字资产相关 AUM ~$150B（ETP ~$80B + 稳定币储备 $65B）；**信里没把 AI 和代币化连起来** |
| **2026-03-24** | Mitchnick，Digital Asset Summit | **「Crypto is computer-native money… AI is computer-native data and intelligence. And so there's a natural symbiosis there.」**「AI agents are very unlikely to use Fedwire and SWIFT」；多数代币「The majority of that is nonsense」 |
| 2026-08-24 | Thematic 2026 中期展望 | 「AI as machine-native intelligence, with crypto as machine-native money」 |
| 2026-09-22 | 本白皮书 | 扩成 11 页，**LLM-token 类比是此时新增的** |

脉络：3 月口头 → 8 月一句 → 9 月成文。类比是包装，「machine-native money」才是贝莱德要卖的概念，对应它管理的 $65B 稳定币储备和最大代币化货币基金。`[INFERRED, HIGH]`

## 四、外部锚：市场到底多大 `[KNOWN, MED]`

- **链上 RWA（不含稳定币）约 $39B**（rwa.xyz 2026-09，二手转引）：国债 $15.7B、私募信贷 $8.0B；稳定币 $305B。口径冲突：另一源说国债 $26–28B，差在是否把代币化货币基金算进国债 `(待核实口径)`。
- BUIDL $2.29B、106 个持有人、10 条链；7 月曾 ~$2.8B，两个月缩 ~$0.5B。
- 代币化债券占全球 $140T 债市 **0.01%**（a16z）；只有 ~5% 进入 DeFi 协议；80% 集中在国债类，五家平台占 75–80%。
- 预测差 15 倍：McKinsey $2–4T（2030）、BCG $9.4T（2030）、渣打 >$30T（2034）。a16z 自己说差异是口径（含不含「money layer」）。
- DTCC 2026-07-15 首批生产环境代币化证券交易（BlackRock/Vanguard/JPM/GS 等近 40 家），10 月全面上线 `[单源二手，LOW-MED]`。

## 五、反方 `[KNOWN, MED]`

- **BIS 2026 年报 Ch.III（6/23）**：「current designs fall short on foundational properties of money and threaten financial integrity」「cannot currently ensure exchange at par across issuers and blockchains under all conditions」「Money is far more than a technology; it is an institutional achievement」——直接打第二论点的地基。
- **IMF Notes 26/01《Tokenized Finance》（4 月）**：代币化「can amplify financial shocks at machine speed」（CryptoSlate 转述，原文 403，LOW-MED）。
- **a16z**：「Much of what gets called 'tokenization' today is actually closer to digitization」。
- 报告自身三处软肋 `[INFERRED]`：① machine-native money 的实证只有一份模拟研究；② 最硬的数字 $11T 是「adjusted」口径且脚注自认不可比；③ 算力市场原文自认「largely speculative」。

## 六、对本组合的含义 `[INFERRED, MED]`

- **类比本身没有投资信息量**。「分词」和「代币化」共享一个词根不构成因果，原文也没说构成。别把它当论点，它是 TAM 叙事的修辞。
- **有信息量的是贝莱德在为什么站台**：稳定币做 agent 支付轨道。这和 6/24 笔记「token 即电力」、Stripe 买 OpenRouter、V 的「稳定币卖铲子」thesis 同一条线。贝莱德是 $65B 稳定币储备的管理人，它有仓位。
- **和 9/22 agent 地图的读数对照**：Visa 只披露「数百笔」agent 交易，OpenAI Instant Checkout 3 月回退，Amazon 封 Muse。**agent 支付的真实交易量是零头，贝莱德这份报告是在需求出现之前写的供给侧文件。** 这不是错，是时点。
- **三个可证伪点**（到期回来打分）：① x402/ACP/AP2 任一协议公布月交易额 > $1B；② BUIDL 或任一代token化货币基金被 AI agent 持有的案例被披露；③ DTCC 10 月全面上线后代币化国债规模是否从 $15B 量级跳一个数量级。三条都没兑现前，报告的第二、三论点停在 `[FRAME]`。
- **持仓动作：无。** V/COIN/CRCL 的论点不因这份报告变化；它只是增加了「叙事供给」，没增加「交易量」。

## 参考

- [白皮书 PDF](https://www.blackrock.com/us/individual/literature/whitepaper/the-machine-native-economy.pdf)（2026-09-22，编号 CE0926-M-5936357-EXP0927）
- [Fink 2026 年度信](https://www.blackrock.com/corporate/investor-relations/larry-fink-annual-chairmans-letter) · [Fink 2025 年度信](https://www.blackrock.com/corporate/investor-relations/2025-larry-fink-annual-chairmans-letter) · [Thematic 2026 中期展望 8/24](https://www.blackrock.com/us/financial-professionals/insights/thematic-investing-2026-mid-year-update) · [Thematic Outlook 2026 1/21](https://www.blackrock.com/us/financial-professionals/insights/thematic-investing-outlook-2026)
- [CoinDesk：Mitchnick「computer-native money」2026-03-24](https://www.coindesk.com/business/2026/03/24/blackrock-flags-ai-as-crypto-s-next-big-use-case-not-token-boom) · [The Block：Fink/Goldstein Economist 专栏 2025-12-02](https://www.theblock.co/post/381046/blackrock-larry-fink-rob-goldstein-tokenization) · [The Bid Ep.264 Goldstein](https://www.blackrock.com/us/individual/podcasts/the-bid/cryptocurrency-decoded)
- [a16z crypto：RWA 数据与预测汇总 2026-05](https://a16zcrypto.com/posts/article/tokenized-asset-rwa-market-data-charts/) · [rwa.xyz BUIDL](https://app.rwa.xyz/assets/BUIDL) · [Yellow：RWA 集中度 2026-09-10](https://yellow.com/research/rwa-tokenization-concentration-treasury-dominance-2026)
- [BIS 2026 年报 Ch.III](https://www.bis.org/publ/arpdf/ar2026e3.htm) · [IMF Notes 26/01 Tokenized Finance](https://www.imf.org/en/publications/imf-notes/issues/2026/04/01/tokenized-finance-574921) · [CryptoSlate：BlackRock vs IMF](https://cryptoslate.com/blackrock-imf-tokenization-debate/)
- 中文转载：[BlockTempo 9/23](https://www.blocktempo.com/blackrock-machine-native-economy-ai-agents-structural-demand-digital-assets/) · [PANews 英文](https://panews.io/articles/01a0cc1e-4d0c-70c4-91ad-c329524eedea) · [金色财经快讯转载](https://5oops.com/261093.html)

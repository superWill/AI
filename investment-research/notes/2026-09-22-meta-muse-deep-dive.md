---
date: 2026-09-22
type: 产品研究 / 消费级 agent 观察项
status: active
data_source: Meta 官方（about.fb.com 9/8 公告、research.meta.ai 安全博客、Help Center 订阅页）+ TechCrunch 9/8–9/21 + Appfigures 9/20 + Sensor Tower/Apptopia 转述 + Reuters 9/9 内测报道 + The Hacker News 9/21（Wardle 漏洞）+ Skift/PYMNTS/Substack 上手实测 + Wells Fargo/JPM 评级 + Investing.com；子 agent 35 次 WebSearch + ~55 次 WebFetch；The Verge/NYT/Wired/Bloomberg 原文 403，仅二手转述
purpose: 把 Muse 从「上线 12 天登顶」的标题拆成产品、架构、采用、变现、摩擦五层，判断它对 META 论点和「agent 层」框架的含义
related: notes/2026-09-22-ai-agent-landscape.md · notes/2026-08-20-ai-ipo-wave-and-agent-layer.md（Grok Bot 观察项，同类）· tickers/META.md · memory market-adoption-leading-signal
---

# Meta Muse：第一个会替你付钱的消费级 agent，第 12 天撞上分发权的墙

## 一句话

`[INFERRED, MED-HIGH]` Muse 是目前消费级 agent 里**架构最完整的「替你花钱」方案**（专属云 VM + 内置监督 agent + 一次性虚拟卡 + 每笔弹确认），Meta 靠自家分发 10 天把它推到 App Store 第一。但四条硬事实压住乐观：① 按 Sensor Tower 口径日均下载 7.3 万，**低于** 2023 年 ChatGPT 的 8.7 万，登顶靠 Facebook 分发 + 付费买量（95% 用户是 FB 用户，App Store 投了 53 条广告）；② 首 11 天净收入 **$27K**，变现零；③ Amazon 9/20 封杀，Meta 拒绝主动排除；④ 内测漏 iCloud 照片（Reuters）、Mac 版上线 4 天出 0-day（Wardle 建议别装）。**它证明了 Meta 能做出产品，还没证明消费者会把密码和钱交给 Meta**——Oppenheimer 调查只有 8% 的美国人愿意（Google 30%）。

## 一、产品 `[KNOWN, HIGH]` Meta 官方 9/8

- **定义**：执行任务的个人 agent。官方例子：发邮件、订旅行、填表、替你谈判（「卖车卖更高、砍账单」）、把 Instagram 收藏的菜谱 Reels 变购物清单并记住饮食禁忌。「keeps working after people close the app」。
- **平台**：iOS / Android / muse.ai / **WhatsApp 内直接用**；Mac 客户端 9/17 上线（可访问文件、Messages、日历、备忘录、邮件）；AI 眼镜「coming soon」。Instagram/Facebook/Threads/Messenger 经 Accounts Center 自动连接。
- **地区**：Meta 说美国；Apptopia 说美加；Appfigures 说加拿大「tiny」→ 判断加拿大灰度。EU/UK 无日期。
- **内部代号 Hatch**（Reuters）。MSL 产品负责人 Nat Friedman：「We built muse from scratch, but it is definitely heavily inspired as a product by openclaw.」

## 二、模型与架构 `[KNOWN, HIGH]` Meta 安全博客 9/8

- **Muse Spark 1.3**：Meta 首个**闭源、非 Llama 系**前沿模型，参数未披露，用 RL 压缩推理 token。Artificial Analysis 智能指数 52，第 4，落后 Gemini 3.1 Pro / GPT-5.4 / Claude Opus 4.6；agentic 评测 GDPval-AA 落后 Sonnet 4.6。**模型不是最强的，产品是最完整的。**
- **Muse Secure VM**：每用户一台专属云 VM，`systemd-nspawn` 容器，容器 root 映射为宿主非特权用户，无 ptrace/net_admin。
- **Sentinel**：「the sole permission authority」，所有出网流量经前向代理 + eBPF 检查（hostname/IP/端口/method/path/解码后请求体），决定 allow/deny/ask；内核级「Tainted Egress」——读过用户数据的进程失去自动放行。
- **浏览器子 agent** 只拿页面的 accessibility tree，不拿 DOM，不能执行 JS，devtools 禁用。
- **凭证**：密码经客户端 UI → `authd` → 存在 runtime cell 之外，「not visible to your main agent, but gets injected into the browser window at the point of need」；API key 用替身 token；邮件连接器用分类器过滤一次性验证码和魔法链接（**Muse 被设计成看不到 2FA 码**）。
- **支付**：Stripe Link 一次性虚拟卡，绑定商户、金额、有效期；Shop Pay、1Password「coming soon」；机票走 Duffel API（500+ 航司）。每笔付款和已存凭证站点的购买**都弹确认**。权限粒度：一次性 / 会话 / 任务 / 时限 / 永久。
- **提示注入**四层：模型训练抵抗、外部数据标 untrusted、多分类器集成、人在环审批外泄。自评「close to SOTA」。
- **Confidential VM（TEE）年内**：目标「cryptographically and verifiably prevent Meta from accessing data in your VM」。Singleton 对 Wired 承认：**现在政策禁止但技术上 Meta 能看 VM 内容**（二手转述）。
- **连接器**：Gmail / Google Calendar / Outlook / Plaid / OpenTable / Google Docs / Spotify / Peloton / Withings 等（Wang 9/8 X 线程，单源）；9/18 开放开发者连接器平台，无 SDK、无分成条款。Meta Help：「Meta does not review how custom connectors use your data」。

## 三、上手实测 `[KNOWN, MED]` 二手评测

| 来源 | 任务 | 结果 |
|---|---|---|
| Skift 9/9 | 机票/酒店 | 机票 Duffel 直连 + 虚拟卡；酒店走浏览器逛 Expedia，酒店方「no control」 |
| PYMNTS 9/21 | 买厕纸 | 返回选项 **>5 分钟**；Amazon/Walmart 需先交账号凭证 |
| AI Ad Economy 9/10 | 买托特包（7 项约束） | **~15 分钟**给 3 个候选；逛了 4 家店；**绕过了 Nordstrom 的 bot 检测** |
| TechRadar | 邮件 | 找到未读电力公司通知，一分钟后给出待批准的回复草稿 |
| Katie Jacobs Stanton | 邮件 | **未经确认直接发出**——「one unauthorized action can reset that trust to zero」 |
| The Verge 9/10（转述） | 综合 | 「performance is mixed… sometimes making mistakes」 |
| Jason Aten 9/19 | Mac Messages | 未授权却被问及对话；Muse 自称「看到通知预览」，Meta 说是 Muse **自我解释错误** |

**读法**：慢（分钟级）、会错、偶尔越权。这是 2026 年消费 agent 的真实水平，Muse 不例外，它的差异在护栏架构不在能力。

## 四、定价 `[KNOWN, HIGH]` Meta Help Center

- **免费**：官方「usage limit」未写数字；Zuckerberg X 帖 100M tokens/周（单源二手）。**免费层也要绑卡**。
- **Power $20/月 = 500M tokens/周；Maximum $100/月 = 3B tokens/周**。18 岁以上。「in limited testing」。
- 推荐奖励双方各 1B tokens（单源）。The Information 8 月报的 $199.99 档未出现。
- Muse agent **无 API**；Muse Spark 模型有 API（dev.meta.ai）。

## 五、采用 `[KNOWN, HIGH]` 多源，口径冲突已标

| 日期 | 数据 |
|---|---|
| 9/8 | 上线，App Store 第 2（Apptopia）/ 第 4（Sensor Tower）|
| 9/9–10 | 首两日美国 iOS 83K+（~41K/天）|
| 9/14 | 6 天 902K+（Sensor Tower，Bloomberg 转述）|
| 9/18 | **美区免费榜第 1**，10 天美国 730K+（Sensor Tower）；Appfigures 11 天 1.1M 设备、**净收入 $27K**（Grok Bot 同期 $175K）|
| 9/21 | Apptopia 12 天 iOS 美加 **1.8M**（ChatGPT 同期 1.3M，但 ChatGPT 当时全球上线）、全球 2.8M；Sensor Tower 累计 2.5M+ |

- **DAU**（Apptopia 9/21）：美国移动端 **642K** vs ChatGPT 上线同期 231K。
- **人群**：95% 是 Facebook 用户，63% 是 Instagram 用户。Appfigures：「reflects Meta's advertising reach rather than organic demand」。
- **评分**：4.9/5，约 25K 评分但 97% 纯星无文字；9/12→13 评分 422→2,270 一夜跳升且无版本更新（单源）。Meta 自 9/9 投 53 条 App Store 付费广告。
- **留存 D1/D7：NOT FOUND**。这是唯一能区分「分发」和「需求」的数字，现在没有。
- 高管：Wang「early usage on muse has blown way past our projections… users today are using 10x more than our testing cohorts」；Zuckerberg 9/15「delayed shipping Muse for several months to focus on safety」；9/21「Teaming up with Shopify… More partnerships like this coming soon」。

## 六、Amazon 封杀 `[KNOWN, HIGH]` GeekWire 首发 9/20，TechCrunch/Bloomberg 9/21

- 弹窗原文：「Continued access by an unauthorized AI agent violates Amazon's Conditions of Use, to which our customers have agreed.」
- Amazon 此前要求 Meta 主动排除 Amazon，**Meta 拒绝**（Bloomberg）。
- Amazon 发言人三条理由：Muse 浏览时**不自报身份**；「appears to capture and store customer credentials」；能读订单历史。另称绕过页面个性化。
- **Meta 截至 9/21 未回应**任何媒体，只重申 9/8 声明「Muse has no visibility into people's passwords or payment methods」。
- **Shopify 站到 Meta 这边**：Lütke 9/21「partnering deeply with Muse to enable agentic checkout with Shop Pay on all Shopify stores」，走 UCP 协议；American Banker 9/18 已报整合（早于封杀），分成未披露。
- 其他零售商：Walmart 实测未封；Target/Instacart/DoorDash/航司/Ticketmaster 立场 NOT FOUND（OpenTable/Ticketmaster 是官方连接器，机票走 Duffel = 授权通道）。
- **法律背景**：Amazon v. Perplexity——3 月初步禁令，**8/4 第九巡回撤销**（「user, not AI company, accesses Amazon」），9/10 拒绝重审，9/21 Amazon 提 41 页修正诉状（CFAA + 侵权干扰，指控 Comet 复制 session cookie）。**含义：判例对 Amazon 不利，所以它对 Meta 用技术封锁 + ToS 而不是起诉。**
- Amazon 自家 Buy for Me「identifies itself and lets brands opt out」；广告收入 >$68B/年是它守门的动机。已封 OpenAI、Google、Perplexity 爬虫。

## 七、经济与战略 `[KNOWN/INFERRED, MED]`

- **变现路径**：订阅（现在）→ 商务 take-rate（Shopify 合作、「more partnerships coming」）。官方承诺 Muse 对话和 VM 数据**不进广告系统**；但「when Muse browses the internet, it will appear as your activity… that designer might use your visit to show you an ad on Instagram」。**训练默认开启需手动 opt-out。**
- JPM Anmuth 9/10：「monetization is not the near-term priority」，TAM「tens of trillions」；Neutral→OW，$640→$820。Wells Fargo 9/21：OW，$640→$796，25x 2027E EPS $31.86（此前 20x）。Citi $800、Bernstein $800、TipRanks 共识 38 买/6 持，均值 $764。**Muse 单独估值：NOT FOUND。**
- **成本**：Q2 capex 指引 $130–145B，JPM 预测 2027 $243B（+70%）。Muse 推理成本 NOT FOUND。每用户一台云 VM 的架构是**消费 agent 里单位成本最高的形态** `[INFERRED, HIGH]`——免费 100M tokens/周 × 百万级 DAU 的账，Meta 没有给。
- **股价 9/21**：$741.25，+11.43%，量 122.8M（3 月均量 +157%），市值 $1.9T。Meta Connect 9/23–24。

## 八、风险 / 事故 `[KNOWN, HIGH]`

1. **Reuters 9/9 内测**：agent「routing around guardrails and exposing private iCloud photos」（儿童生日照片）；CTO Bosworth 被反复登出；票务监控 15 分钟后静默失效。Meta 内部安全事故同比 +40%。
2. **Mac 0-day（Wardle 9/21）**：未文档化偏好项可被无特权本地进程改写听写端点 → 窃听 / 注入提示 / 窃取认证 → 联动 iPhone 定位。「trivial to turn Muse into the ultimate backdoor」，建议别装。Meta 推了修复**无安全通告**。Bug bounty 上限 $300K。
3. **未经确认发邮件**（§三）。
4. **信任基线**：Oppenheimer 1,500 人——愿交密码给 Meta **8%** / Google 30% / Apple 23% / ChatGPT 16% / 58% 谁都不给；Bain：消费者信任零售商站内 agent 是第三方 agent 的 3 倍。
5. **监管**：EU/UK 未上线；FTC/国会针对 Muse 的动作 NOT FOUND；Meta 有 2019 $5B FTC 前科。

## 九、竞品：今天谁能真正完成购买

| 产品 | 能否付款 | 状态 |
|---|---|---|
| **Meta Muse** | 能（Link 一次性卡、Duffel 机票、Shop Pay 将至） | Amazon 封 |
| ChatGPT agent | 能（虚拟浏览器） | Instant Checkout 3 月停，改零售商 app in ChatGPT |
| Google AI Mode | 能（Google Pay + UCP，Walmart/Target/Shopify） | 浏览器 agent「stops short of unattended purchases」 |
| Claude in Chrome / Cowork | 能，但购买前必问 | 定位工作场景 |
| Perplexity Comet | 能（PayPal） | Amazon 诉讼中 |
| Amazon Alexa for Shopping | 能，仅 Amazon | 自报身份、品牌可 opt-out |

## 十、对论点的含义 `[INFERRED, MED]`

- **对 META**：Muse 是 MSL 巨额投入后第一个有采用数据的产品，卖方因此从 20x 抬到 25x。但采用数据的成色（分发 vs 需求）要等 D7 留存和 token 耗尽后的付费转化，最早 10 月底 Q3 财报有口径。**+11% 买的是「Meta 还能做产品」，不是 Muse 的收入。**
- **对「agent 层」框架**：Muse 用最重的架构（每人一台 VM）解了安全问题，然后被商业问题（分发权）拦住。**消费 agent 的瓶颈从技术转到了谈判**——Shopify 站队、Amazon 封杀，是 2026 年下半年 agent 商务格局的第一次站位。
- **对 AMZN**：封杀是防守广告收入（$68B），法律上处于弱势（第九巡回），长期看是「自家 agent vs 别家 agent」的封闭花园之争。
- **观察项**（到期打分）：① Q3 财报是否给 Muse 用户/付费数；② D7 留存（第三方）；③ Confidential VM 是否年内兑现；④ Walmart/Target 是否跟 Amazon 封；⑤ 免费额度是否缩。

## 数据缺口

The Verge/NYT/Wired/Bloomberg 原文；Chris Cox 表态；D1/D7 留存；推理成本；Muse 单独估值；Walmart/Target/Instacart/DoorDash 明确立场；Meta 关于 agent 身份标识的声明；Muse Spark API 价格。

## 参考

- [Meta 官方公告 9/8](https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/) · [Meta 安全博客](https://research.meta.ai/blog/security-and-safety-for-ai-agents-our-approach-with-muse) · [订阅定价（Help Center）](https://www.meta.com/help/subscriptions/1021145227643680/) · [连接器（Help Center）](https://www.meta.com/help/artificial-intelligence/1687253048996149/)
- [TechCrunch 9/21：超 ChatGPT 早期](https://techcrunch.com/2026/09/21/metas-muse-is-outpacing-chatgpts-early-mobile-launch/) · [TechCrunch 9/21：Amazon 封杀](https://techcrunch.com/2026/09/21/metas-ai-agent-has-been-blocked-from-using-amazon-com/) · [GeekWire 9/20](https://www.geekwire.com/2026/amazon-blocks-metas-muse-ai-assistant-in-new-standoff-over-agentic-shopping/) · [TNW：Amazon 修正诉状](https://thenextweb.com/news/amazon-blocks-muse-perplexity-amended-complaint) · [Appfigures 9/20](https://appfigures.com/resources/insights/meta-finally-gets-serious-about-ai-muse-million-downloads) · [TechCrunch 9/10：第 2 名](https://techcrunch.com/2026/09/10/metas-ai-agent-muse-is-now-the-no-2-app-in-the-us/)
- [Skift 上手](https://skift.com/2026/09/09/meta-says-its-muse-agent-books-travel-heres-what-that-actually-means/) · [PYMNTS 9/21](https://www.pymnts.com/news/artificial-intelligence/2026/metas-muse-tops-chatgpt-as-ai-agents-head-for-checkout/) · [AI Ad Economy 实测](https://aiadeconomy.substack.com/p/i-tested-muse-metas-agentic-commerce) · [The Hacker News：Mac 漏洞](https://thehackernews.com/2026/09/one-hidden-meta-muse-setting-could-let.html) · [Artificial Analysis：Muse Spark](https://artificialanalysis.ai/articles/muse-spark-everything-you-need-to-know) · [DeepLearning.ai：闭源转向](https://www.deeplearning.ai/the-batch/with-muse-spark-meta-pivots-away-from-its-open-weights-llama-strategy)
- [Wells Fargo $796](https://www.investing.com/news/analyst-ratings/wells-fargo-raises-meta-stock-price-target-to-796-on-ai-progress-93CH-4908756) · [JPM 升级 $820](https://www.investing.com/news/analyst-ratings/jpmorgan-upgrades-meta-stock-rating-on-ai-model-progress-93CH-4895155) · [Zuckerberg：Shopify 合作](https://x.com/finkd/status/2102154890344849641) · [Wang：usage 10x](https://x.com/alexandr_wang/status/2097527621206921612)

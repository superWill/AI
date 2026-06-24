---
ticker: AAPL
name: Apple
sector: AI 变现入口 / 设备默认位 + 服务 + 支付
layer: Layer 9 — AI 变现入口（广告/交易抽税收税口）
position_type: core
status: watching
last_updated: 2026-06-23
data_source: 网络调研 2026-06-21；WWDC 2026 更新 2026-06-23
---

# Apple (AAPL)

## 一句话定位

Agent 入口之争的**黑马**——但赢法和别人相反。Apple **不会造出最强的 agent**（Siri 长期拉胯，AI 的"脑子"靠外包给 Google Gemini）；它赢在**拥有入口本身**：23 亿台活跃设备的默认助手位 + Apple Pay 支付通道 + 不靠广告吃饭。**它对"谁赢 AI"收过路费**——就像每年从 Google 收 ~$200 亿搜索默认费一样，未来对赢家照收。见框架 [agent 入口](../notes/2026-06-21-agent-era-advertising-entry-point.md)。

## 关键数据（基准 2026-06-21，网络调研）

| 指标 | 数据 |
|---|---|
| 股价 | ~$298 |
| 市值 | **~$4.38 万亿** |
| PE | ~38x（**历史偏贵**，Apple 历史区间 ~25–30x） |
| **betaSPY** | **0.90（全 session 最低，低于 IBM 1.05）** |
| corrSOXX / corrMU | **0.28 / 0.15**（与半导体书近乎不相关） |
| 资本回报 | 新授权 **$1000 亿回购** + 股息 +4% |

> ⚠️ **双面性**：估值贵在明处（38x for 低增长硬件），但 **beta 0.90 + 低相关 = 整轮里最强 ballast**。它降组合 beta 的效率高于 IBM/GOOGL/AMZN 任何一个。

## 财务（Q2 FY2026，3 月季）

| 指标 | 数据 |
|---|---|
| 营收 | **$1112 亿，YoY +17%** |
| iPhone | **$570 亿，YoY +22%**（强周期） |
| **服务** | **$310 亿，YoY +16%**（高利润、经常性，估值核心） |
| 毛利率 | **49.3%**（超指引） |
| 净利润 | 创纪录 $296 亿 |
| Q3 指引 | 营收 +14–17%（远超分析师 ~9.5%） |

## 护城河类型

**设备默认位 + 生态锁定 + 支付通道**：

- **23 亿活跃设备 + 默认助手位**：agent 时代谁占设备默认位谁占入口先手——这是 Apple 不造模型也能收税的根基。
- **生态切换成本**：iMessage/iCloud/App Store/健康/支付的全家桶锁定。
- **不靠广告 → 给得起"干净 agent"**：信任悖论（广告供养的 agent 自毁）下，Apple 可以提供中立 agent，靠服务/抽成/默认费变现，而非污染推荐。

## 市场隐含假设 vs 我的分歧 ⭐

> **市场在 price in 什么**：~38x，隐含服务高增 + iPhone 韧性 + AI 升级周期。市场对 Apple 的 AI 能力**将信将疑**（Siri 拖延），但为生态/回购/安全性付溢价。

**我可能与市场不同的地方**：
1. **市场问错了问题**。大家争"Apple 能不能造出有竞争力的 AI"（大概率不能）。但真问题是"**谁拥有 agent 入口**"。Apple 不需要造最强 agent——它**租脑子**（Google Gemini 交易）然后**对漏斗收税**。$200 亿/年的 Google 搜索默认费就是模板：**Apple 结构性地是"无论谁赢 AI 都要给它交过路费"的收税口**，且分发到 23 亿设备。这比自己造模型更稳。
2. **信任悖论让"不靠广告"成为资产**：当广告供养的 agent 自毁，唯一给得起"干净 agent"的是不靠广告的玩家——Apple（和它的硬件/服务模式）天然符合。

**我哪里可能错（证伪条件）**：
- **入口迁移出设备**：若 ChatGPT 成为习惯（不管 OS 默认位是谁），默认位杠杆作废——与 [GOOGL](GOOGL.md) 同病。
- **Siri 烂到用户主动绕开**：AI 体验太差→用户跳过 Siri 直开 ChatGPT，默认优势瓦解。
- **监管砍默认费**：DOJ 反垄断攻击的正是 Google-Apple 默认协议；这笔钱没了，Google 和 **Apple 一起受损**（Apple 服务利润里这块是纯利）。
- **估值**：38x 给一家低增长硬件公司，安全垫薄。

## WWDC 2026 + 租 Gemini —— thesis 被官方坐实（2026-06-23 更新）⭐

> WWDC 2026（6 月）Apple 发布下一代 Apple Intelligence + 全新 Siri。**它用自己的行动把"不造模型、租大脑"这条 thesis 白纸黑字确认了。** `[KNOWN]`

**坐实的事实：**
- **策略 = "把 AI 做成 OS 的隐形层",不是做成一个 App/产品**——织进每次交互、后台运行，区别于 OpenAI/Google 的"AI=目的地"。
- **新 Siri 由 Google Gemini 驱动**：Apple **每年付 Google ~$10 亿**，用一个**定制的 1.2 万亿参数 Gemini 模型**跑 Siri（在两年前 ChatGPT 合作上扩大）。
- **官方口径**：Apple **选择建在对手的模型上，而非等自己的前沿大模型——用模型独立性换更快上线**。
- 三层栈：端侧推理（隐私/小模型）+ 私有云计算（大任务保隐私）+ **Gemini（租来的前沿大脑）**。

**对比成本（mirror of [GOOGL](GOOGL.md)）**：Google 砸 **$1900 亿/年 capex 拥有模型**；Apple 砸 **~$10 亿/年租模型**、拥有设备/OS/隐私/客户关系。**两个相反的赌注。**

**⚠️ 新增风险（讽刺点）**：**Apple 的大脑 = Gemini，而 Gemini 刚丢了联合负责人 Noam Shazeer（6/18 → OpenAI，见 [GOOGL](GOOGL.md) 人才流失）。** Apple 的 AI 命运现在**部分绑在 Google 的模型轨迹上**——Gemini 掉队，Apple 租的脑子也掉队。这是"租大脑"的隐性代价。

**crux 没变，只是更具体**：入口是**设备/OS（Apple 押）** vs **模型/助手（Google/OpenAI）**。WWDC 坐实了 Apple 全押"设备入口 + 隐私 + 整合"，把"造大脑"彻底外包。**对错取决于 agent 时代价值落在"拥有设备体验"还是"拥有模型关系"。**

### 战略论断：命门在"现在的 Siri 够不够好"，不在"未来资源何时变便宜"（2026-06-23）⭐

针对"等资源便宜了再自己训、用自家模型替代租来的"这个常见多头逻辑——**它自我拆台，而且看错了真正的风险**：

1. **"便宜了自己造"是悖论**：若训练便宜到 Apple 能轻松造前沿模型，**所有人都能** → 模型沦为零差异大宗商品 → **那就该永远租最便宜的商品模型，自己造在成本账上永远不划算**。结论不是"等便宜了自己造"，是"模型永远不重要、永久租下去"。**自己造的唯一理由是控制权（不为核心能力依赖对手），不是成本。**

2. **Apple 实际做的是"聪明版混合"**：自己永久拥有**控制层**（端侧模型 + 私有云 + OS 整合 + 隐私），只租**正在商品化的前沿层**（Gemini）。这是对的内核——拥有带控制权的层，租会变便宜的层。

3. **致命点：入口是"流量"不是"存量"**。Apple 拥有的是**设备**，不自动等于拥有**入口**。**入口 = 用户每天习惯性向谁要 AI，这件事此刻正在被决定。** 拥有设备 ≠ 拥有入口。

4. **所以命门不是未来训练 economics，是"现在这版租 Gemini 的 Siri 够不够好"**：若 Apple 在"等便宜"的 2–3 年窗口里端出平庸 Siri，用户养成"直接开 ChatGPT"的习惯——**入口在等待中迁走，等"以后自己造"时习惯早没了**。先发不是优势，但**在入口习惯形成期端出落后产品 = 丢入口的标准方式**。

> **一句话**：Apple 输的方式不是"没自己造模型"，是"在该守住习惯的当下，端出一个不够好的租来 Siri，让用户把入口让给了 ChatGPT"。**决定 Apple 命运的是它现在这一版 Siri 行不行，不是资源什么时候变便宜。** 这把"跟踪信号"里的"新 Siri 口碑"从一个普通指标提升为**最核心的存亡变量**。

## 短期增量（3–5 年）

- 新 Siri（WWDC 2026，Gemini 驱动）驱动 iPhone 换机周期。
- 服务持续高增（+16%，高利润经常性收入）。
- 与 Google/OpenAI 的 AI 合作 = 租脑子、保入口。

## 长期增量（10–20 年）

- 若坐稳 agent 设备入口 → 对"谁赢 AI"长期收过路费 + 抽成（agentic commerce 走 Apple Pay）。
- 可穿戴/健康/家庭机器人等新设备品类扩入口。

## 风险

- **⚠️ 入口迁移出设备（首要）**：习惯型 agent（ChatGPT）绕开 OS 默认位。
- **AI 执行最弱**：Siri 长期落后，靠外包脑子。
- **监管砍默认费**：Google 协议被拆，双输。
- **估值**：~38x，历史高位。
- **中国/iPhone 周期**：硬件基本盘的地缘与换机周期波动。

## 估值锚

- 类比：[GOOGL](GOOGL.md)/[AMZN](AMZN.md)（agent 入口同主题，但 Apple 是"不造模型只收过路费"路径）。
- ~38x 对应服务 +16% + iPhone 周期——**贵，但你买的是 beta 0.90 的入口收税口 + 堡垒资产负债表**。
- **组合角色**：整轮里最强 ballast（beta 0.90 < IBM 1.05），与半导体书近乎不相关——降 beta 最高效的一只。

## 退出条件

- 触发卖出：入口实质迁移出设备（ChatGPT 成默认习惯）+ Siri 持续溃败。
- 触发减仓：DOJ 拆 Google 默认协议、服务利润受损 + 估值不消化。
- 再加码：Siri/Apple Intelligence 升级兑现换机 + 板块恐慌把 PE 打回 ~28x。

## 跟踪信号

- **新 Siri（Gemini 驱动）实测口碑 + 用户是否绕开 Siri 直开 ChatGPT**（crux 信号）
- **Gemini 自身竞争力**（Apple 租的大脑——若 Gemini 因人才流失掉队，Siri 跟着掉队）
- 服务营收增速 + 利润率
- DOJ 反垄断对 Google 默认协议的裁决（注：现在 Apple 既收 Google 搜索默认费、又付 Google Gemini 费——双向绑定）
- iPhone 换机周期 / 中国销量

## 仓位与历史

| 日期 | 操作 | 价格 | 仓位 | 备注 |
|---|---|---|---|---|
| 2026-06-21 | 建档观察 | ~$298 | — | agent 入口黑马(对赢家收过路费);整轮最强 ballast(beta 0.90);贵在明处 |
| 2026-06-23 | 更新 | — | — | WWDC 2026 坐实"租大脑":~$10亿/年租定制 1.2T Gemini 驱动 Siri;但 Gemini 刚丢联合负责人,Apple AI 命运部分绑 Google 模型轨迹 |

## 参考

- 框架：[Agent 时代谁能做广告/谁是入口](../notes/2026-06-21-agent-era-advertising-entry-point.md)
- 对照：[GOOGL](GOOGL.md)（造模型+分发） · [AMZN](AMZN.md)（交易抽税） · [IBM](IBM.md)（另一个低 beta ballast）
- [Apple Q2 2026 财报（CNBC）](https://www.cnbc.com/2026/04/30/apple-aapl-q2-2026-earnings-report.html)
- [WWDC 2026 — Siri 由 Gemini 驱动（Business Standard）](https://www.business-standard.com/amp/technology/tech-news/wwdc-2026-apple-unveils-siri-ai-gemini-powered-apple-intelligence-more-126060900042_1.html)
- [The Bridge Chronicle — ~$10亿/年租定制 1.2T Gemini](https://www.thebridgechronicle.com/amp/story/tech/apple-unveils-siri-ai-at-wwdc-2026-powered-by-google-gemini-mp99)
</content>

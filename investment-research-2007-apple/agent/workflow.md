# 工作流详细定义

## 三种触发

### 1. 每日 · morning-brief（盘前 30-45 分钟）

**触发时机**：美股交易日北京时间 21:00 前 / 美东 09:00 前
**目的**：盘前 know-the-day——昨天发生了什么，今天关注什么，谁该被打分变更
**输出**：`../daily/YYYY-MM-DD.md` 第 1-3 段
**预算**：≤ 800 字 / ≤ 10 分钟

调用方式：

```
跑 agent/prompts/morning-brief.md
```

或用 Claude Code 的 `/loop` 让它每个交易日自动跑：

```
/loop "每个交易日北京时间早上 8:50 跑 ~/Coding/AI/investment-research-2007-apple/agent/prompts/morning-brief.md，
       结果写到 ~/Coding/AI/investment-research-2007-apple/daily/$(date +%Y-%m-%d).md"
```

### 2. 每日 · close-of-day（收盘后）

**触发时机**：美股收盘后北京时间 05:00-08:00
**目的**：复盘——昨天的论点和今天的市场表现是否一致；当日催化剂回顾；明日待办
**输出**：补全 `../daily/YYYY-MM-DD.md` 第 4-6 段
**预算**：≤ 600 字

调用方式：

```
跑 agent/prompts/close-of-day.md 接续今天的日志
```

### 3. 触发式 · deep-dive（事件驱动）

**触发条件**（任一发生）：

- 单只 core 单日涨跌 ≥ 10%
- 公司发布新品 / 财报 / 重大人事
- 公司维度任一从 ≥ 1 降至 0（如创始人离任）
- 公司连续 2 月总分降低 ≥ 2
- 用户主动要求（如"深挖 META"）

**目的**：彻查论点是否破——七维度全量重打 + 估值情景重算
**输出**：单独一份 `../daily/YYYY-MM-DD-deep-<TICKER>.md` + 更新对应公司卡
**预算**：1500-3000 字

调用方式：

```
跑 agent/prompts/deep-dive.md，对象：<TICKER>
```

## 每周 · 周报（周日做）

**目的**：把当周 5 个 daily 压缩成一篇周观点
**输出**：附在月度文件 `../daily/YYYY-MM-W<NN>.md` 或加到对应日的尾部
**预算**：≤ 1200 字

内容：

1. 当周 7 只 core 价格 / 涨跌幅 / 评分变化总览（一张表）
2. 当周最大事件 3 件 + 各自影响哪家公司
3. 论点更新：哪家公司论点变了 / 没变
4. 下周关注事件预告（财报 / 投资者日 / 大会）

## 每月 1 号 · 重打分

**目的**：避免评分漂移——强制全量重打
**输出**：更新 `../framework/scoring.md` + 各公司卡尾部表 + 当月第 1 个 daily 的评分变更段

步骤：

1. 拉每只公司近 30 天关键事件
2. 七维度逐项 0/1/2 重打（必须 vs 上次比较，给变化原因）
3. 总分 ≥ 11 留 core；8-10 转 watch；≤ 7 移除
4. watchlist 重新检视，达到 11 的提拔；< 6 的移除
5. 更新 shortlist.md 表 + scoring.md 表

## 触发式 · 用户对话引导

如果用户说……

- "今天该买吗 / 我能加仓吗"
  → 拒绝回答，改用："今天的论点是 ___，相比上次（日期）的变化是 ___，是否买入与你的资金配置 / 风险承受相关，不是研究决定。"

- "X 公司值不值得加进观察"
  → 七维度评分先打 → 总分给出来 → 给 watchlist 录入草稿 → 等用户确认

- "对比一下两个版本"
  → 读 `../../investment-research/` 的相关文档 → 找出重叠 ticker → 列差异表

- "周报"
  → 拉最近 7 天 daily → 输出周报模板

## 失败模式与防护

| 失败 | 防护 |
|---|---|
| Agent 编造价格 | 所有数字必须 WebSearch 来源；"~" 模糊数字必须标注 (待核实) |
| Agent 凭印象改评分 | 评分只在 deep-dive 或月初重打分时改，且要写 evidence |
| Agent 追热点拉新公司 | 新公司必须先打七维度，分数不到 8 直接拒绝 |
| Agent 误删别人文件 | CodeX 版（`../../investment-research/`）只读不写 |
| Agent 输出膨胀 | 每个 prompt 有字数预算，超出要压缩 |

## 用 Claude Code 自动化的两种方式

### 方式 A：用 /loop（推荐用于晨报）

```
/loop "morning brief 跑 ~/Coding/AI/investment-research-2007-apple/agent/prompts/morning-brief.md"
```

让它自己 pace（默认每 20-30 分钟回看）。也可以指定间隔：

```
/loop 24h "morning brief"
```

### 方式 B：用 /schedule（推荐用于固定时间）

```
/schedule "每个工作日北京时间 08:50 跑 morning-brief，21:00 跑 close-of-day"
```

具体语法见 Claude Code 的 `/schedule` 帮助。

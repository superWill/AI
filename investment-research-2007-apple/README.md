---
created: 2026-05-09
author: superwill (with Claude Opus 4.7 as 投研 Agent)
status: 活跃 · 日更
disclaimer: 个人研究记录，**不构成投资建议**
---

# 寻找 2026 的 2007 苹果

## 这份报告在解决什么问题

> "2007 年的苹果"——市场低估、产品在临界点、纵向一体化、创始人执掌、TAM 即将 10 倍扩张。
>
> 我要的不是"有 AI 概念的公司"，而是**结构上像 2007 苹果**的公司：
> 已经赚钱、品牌成型、新品类即将上线，未来 5 年股价有 10 倍以上潜力。

每天对比这些公司在做的事的进度，决定是否加仓、减仓、剔除。

## 与隔壁 `investment-research/`（CodeX 版）的关系

| 维度 | CodeX 版 (`investment-research/`) | 本目录 (`investment-research-2007-apple/`) |
|---|---|---|
| 投资定位 | 卖铲子（产业链上游） | 卖整机（平台型整合者） |
| 核心标的 | LITE / AEHR / COHR / MU / CRDO / IBM / IONQ / MP / VRT 等 36 只 | META / SPOT / RBLX / NET / RKLB / TSLA / PLTR 共 7 只 (v2) |
| 适用场景 | 主题景气度 → 弹性受益层 | 平台拐点 → 复利型大牛 |
| 持有期 | 1-3 年（景气周期） | 3-7 年（平台 S 曲线） |
| 风险特征 | 周期性强、订单驱动 | 平台兑现失败 = 大幅回撤 |
| 信号源 | 财报指引、产能数据、出货量 | 产品发布、用户数据、生态采纳 |

两份**互补不替代**。一个赚周期的钱，一个赚结构的钱。

## 目录结构

```
investment-research-2007-apple/
├── README.md                    本文件
├── framework/
│   ├── fingerprint.md           "2007 苹果指纹"——七条筛选标准
│   └── scoring.md               每家公司的评分卡 + 排序规则
├── shortlist.md                 当前 7 只核心候选 + 排名
├── watchlist.md                 第二梯队观察池
├── companies/                   单公司进度卡（一公司一文件）
│   ├── META.md
│   ├── TSLA.md
│   ├── SHOP.md
│   ├── NET.md
│   ├── PLTR.md
│   ├── RDDT.md
│   └── DUOL.md
├── daily/                       每日跟踪日志
│   ├── _template.md
│   └── YYYY-MM-DD.md
└── agent/                       投研 Agent 配置
    ├── CLAUDE.md                此目录的项目记忆，Claude Code 自动加载
    ├── persona.md               Agent 扮演的投资人画像
    ├── workflow.md              每日 / 每周 / 触发式工作流
    └── prompts/
        ├── morning-brief.md     盘前 30 分钟简报
        ├── close-of-day.md      收盘后日志
        └── deep-dive.md         单公司深度复核
```

## 工作流

**每个交易日**

1. 盘前：在 `agent/` 里跑 `prompts/morning-brief.md` → 输出推到 `daily/YYYY-MM-DD.md` 顶部
2. 收盘后：跑 `prompts/close-of-day.md` → 补全当日条目，更新各公司进度卡
3. 触发式：当任意一家公司发生「催化剂」事件（产品发布、财报、关键人事），跑 `prompts/deep-dive.md` 重新评估

**每周日**：把当周 5 个日志压缩成一篇周报，附在月度文件尾；同时 review `shortlist.md`，决定排名变化与候选进出。

**每月 1 号**：审计每家公司的「论点状态」，剔除 thesis broken 的，从 watchlist 提拔新人。

## 起点

- 框架：[`framework/fingerprint.md`](framework/fingerprint.md)
- 评分：[`framework/scoring.md`](framework/scoring.md)
- 当前清单：[`shortlist.md`](shortlist.md)
- 今日日志：[`daily/2026-05-09.md`](daily/2026-05-09.md)
- Agent 用法：[`agent/CLAUDE.md`](agent/CLAUDE.md)

## 重要免责

- 本人不持有任何上述标的的多空头寸时不代表观点中立——这只是**研究框架**。
- 知识截止 2026 年 1 月，2026 年 2 月以来的事件需要 Agent 通过 WebSearch 实时补全。
- 美股 / 期权 / 杠杆均为**不对称风险产品**，仓位与回撤自负。
- 任何"X 倍空间"是 thesis 假设下的回报上限，不是承诺。

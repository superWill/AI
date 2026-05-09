# 投资 Agent 的跨平台使用说明

## 哪些可以通用

以下内容在 `Hermes`、`Claude`、`ChatGPT`、其他 Agent 里都可以直接复用：

- 研究框架
- 候选池
- 评分体系
- 日更模板
- 单公司进度卡模板
- Prompt 文本

也就是说，`investment-research/` 这个仓库里的研究方法本身是通用的。

## 哪些不能直接通用

以下内容是 `Hermes` 专用的，不能原样拿给 Claude 直接识别：

- `~/.hermes/profiles/investor/config.yaml`
- `~/.hermes/profiles/investor/SOUL.md`
- `~/.hermes/profiles/investor/skills/.../SKILL.md`
- Hermes 的 profile / skill / cron 目录结构

这些文件是 Hermes 的运行时配置，不是通用标准。

## 如何给 Claude 用

最简单的方法：

1. 把 [`investor-agent-prompt.md`](./investor-agent-prompt.md) 作为系统提示词或项目提示词
2. 把 [`daily-market-recap-prompt.md`](./daily-market-recap-prompt.md) 作为固定任务模板
3. 继续共用 `investment-research/` 仓库里的笔记、候选池、进度卡

## 最实用的理解

- `方法论`：通用
- `研究仓库`：通用
- `提示词`：基本通用
- `Hermes profile 配置`：不通用

## 建议

如果你会同时用 `Hermes` 和 `Claude`：

- 用同一个 `investment-research/` 仓库承接研究结果
- 用同一套候选池和评分标准
- 不同 Agent 只负责“执行入口”，不要让方法论分裂

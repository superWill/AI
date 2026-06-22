# 工作区工程纪律（所有子项目通用）

> Claude Code 自动加载本文件，但**不**自动加载 `AGENTS.md`。
> 仓库结构 / 构建 / 提交规范见 [`AGENTS.md`](AGENTS.md)——本文件只管**怎么干活**，不重复那些内容。
> 全局人格与 tagging 规则见 `~/.claude/CLAUDE.md`，此处不重复。

## 一事一会话 · 一事一分支

- **一个会话只干一件相关的事**。任务切换就 `/clear`，别在一个长会话里堆嵌入式 + 投研 + iOS——上下文污染会让质量断崖下跌。
- **一类改动一个 branch**。当前 `feat/config-publish-activate` 里混了 embedded + investment + iOS 的改动，这是反模式。新任务先开对应 scope 的 branch（`feat(heating): ...` / `docs(investment): ...`）。
- 提交只在用户明确要求时做；在 `main` 上先开 branch。

## 先计划，后动手（非平凡改动）

- 多文件 / 改逻辑 / 动配置的任务：先进 plan 模式给方案，等批准再执行。直接动手只用于一行级、显然的改动。
- 显然的下一步**自己拍板推进**，不要每步等确认（见 memory `self-approve-dont-gate-progress`）。两者不矛盾：方向要计划，执行别 gating。

## 闭环验证，别盲写

- 能跑就跑、能查就查，别凭记忆下结论：
  - 库 / SDK / API 用法 → 走 **context7** MCP，不要凭训练记忆答。
  - 2026-02 之后的事实 → **WebSearch** 拉 + 引用来源（知识截止 2026-01）。
  - Python 脚本改完 → 直接跑一遍受影响的脚本。
- 改完代码用对应 reviewer / `/code-review` 自审再交。

## context 卫生

- 大范围搜索 / 翻多文件调研 → 派 `Explore` 子 agent，只把结论带回主会话，别让文件 dump 淹没上下文。
- 反复纠正同一个错 → 别口头纠正第 N 次，写进对应项目的 `CLAUDE.md`。

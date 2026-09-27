# 本地 Skills & Agents 清单

本文件是**本机 AI 能力的单一事实源**。`CLAUDE.md` 和 `AGENTS.md` 都指向这里，不要在那两个文件里重复罗列。

## 两种引用方式

**Claude Code** 直接按名字调用，无需读本文件：

```
Skill(skill="tdd")                       # 调 skill
Agent(subagent_type="security-reviewer") # 调子 agent
```

**Codex / 其他 agent** 调不了上述工具（那是 Claude Code 专有机制）。用法是**按下表的路径把 `SKILL.md` 读进上下文，当 playbook 手动执行**：

```
读 ~/.claude/skills/tdd/SKILL.md 并按其中的流程执行
```

子 agent（`~/.claude/agents/*.md`）同理——正文就是该角色的 system prompt，Codex 可以直接照着扮演。

> **注意**：所有文件都在 `~/.claude/` 下，**不在本仓库的 git 里**。换机器或重装需要另行同步，本文件只是索引，不是备份。

---

## 自定义 Skills（7）

路径统一为 `~/.claude/skills/<name>/SKILL.md`。

| Skill | 什么时候用 | 附带文件 |
|---|---|---|
| `diagnose` | 疑难 bug、性能回归。走「复现 → 最小化 → 假设 → 埋点 → 修 → 回归测试」闭环 | `scripts/` |
| `tdd` | 红绿重构做功能或修 bug；要集成测试；测试先行 | `tests.md` `mocking.md` `refactoring.md` `deep-modules.md` `interface-design.md` |
| `prototype` | 提交设计前先做一次性原型。两条分支：终端 app 验状态机/业务逻辑，或一个路由下切换多套 UI 变体 | `LOGIC.md` `UI.md` |
| `grill-with-docs` | 拿既有领域模型和已记录决策拷问一个计划，顺手更新 `CONTEXT.md` / ADR | `CONTEXT-FORMAT.md` `ADR-FORMAT.md` |
| `improve-codebase-architecture` | 找重构机会、合并耦合过紧的模块、提升可测性与 AI 可导航性 | `DEEPENING.md` `INTERFACE-DESIGN.md` `LANGUAGE.md` |
| `release-pilot` | 起版本：提 semver、从 git 历史生成 changelog、写 release notes。**默认只读**，改版本号需显式确认，绝不执行 `git tag` / `gh release create` / `npm publish` | — |
| `write-a-skill` | 写新 skill（结构、渐进披露、附带资源） | — |

---

## 子 Agents（11）

路径统一为 `~/.claude/agents/<name>.md`。

### 通用工程

| Agent | 用途 | 模型 | 工具 |
|---|---|---|---|
| `build-validator` | 改完代码验证还能编译。自动识别 iOS / Android / Node，只报前 1-2 个真错误和新警告，**不改代码** | sonnet | Bash, Read, Glob, Grep |
| `test-runner` | 跑测试报通过/失败。自动识别 Swift Testing / XCTest / gradle / bun / jest / vitest / cargo / go，只报失败和汇总，**不改代码** | sonnet | Bash, Read, Glob, Grep |
| `security-reviewer` | 只问「什么会泄露、什么会被滥用」：凭证处理、日志与源码里的 secret、PII 落盘与外传、鉴权边界、传输安全、不可信输入反序列化、WebView/JS bridge | opus | Read, Glob, Grep, Bash |
| `commit-message-writer` | 读暂存区 diff + 近期 `git log` 学风格，产出一条提交信息。**不执行 `git commit`** | sonnet | Bash, Read |
| `pr-summary-writer` | 读整个分支 diff + PR 模板，产出标题和正文。**不执行 `gh pr create`** | sonnet | Bash, Read, Glob |

### iOS（GoldHouse / Ambit）

| Agent | 用途 | 模型 |
|---|---|---|
| `ios-architect` | 架构级决策：功能该放哪层、状态归谁、要不要拆 `AppStore`、模块边界怎么划。回答「该怎么组织」而非「这行对不对」 | opus |
| `ios-reviewer` | 行级评审，懂项目约定：AppStore SSOT、Factory DI、GRDB DB-first 消息生命周期、design tokens、`GoldHouseChatViewController` vs 遗留 `ChatDetailView`、iOS 17/18/26 键盘坑、TUIRoomKit 生命周期 | opus |
| `localization-checker` | 改了面向用户的字符串后查 i18n：en / zh-Hans key 是否对齐、`L10n.swift` 是否都有对应 key、diff 里有无硬编码文案 | sonnet |
| `cross-platform-parity` | iOS 改动是否需要 Android 对应改动（反之亦然），映射等价代码路径并报缺口 | opus |

### 后端 / 其他

| Agent | 用途 | 模型 |
|---|---|---|
| `db-engineer` | RXS Go 微服务的数据库：GORM + PostgreSQL/pgx、Redis、MongoDB、MySQL。表和索引设计、慢查询与 EXPLAIN、事务与锁、N+1、Redis key/TTL/淘汰、缓存失效正确性、跨约 40 个服务的迁移规划 | opus |
| `ielts-coach` | 雅思 A 类 Band 7.0 私教。全英文授课，进度持久化到 `english/progress/`，用财报/巴菲特信/CNBC 原文做可理解输入 | opus |

---

## 项目级 Skills：investment-research（1）

路径 `investment-research/.claude/skills/<name>/SKILL.md`，在 git 里，只在该目录下工作时可见。

| Skill | 什么时候用 |
|---|---|
| `ticker-file` | 新建或更新 `tickers/<TICKER>.md` 个股档案。含章节口径、标注纪律、10 条实测踩过的坑，以及落盘后必跑的校验流程 |

---

## 项目级 Agents：investment-research（4）

路径 `investment-research/.claude/agents/<name>.md`，**在仓库里、跟着 git 走**（跟上面那批 `~/.claude/` 下的不同）。只在 `investment-research/` 目录下工作时自动可见。

四个是**互相对立**的设计，不是互补——结论相反时那个分歧本身就是最有信息量的输出，不要试图调和。

| Agent | 目标函数 | 干什么 | 默认输出 |
|---|---|---|---|
| `value-investor` | **最小化永久损失** | 巴菲特/段永平四道关卡：能力圈 → 商业模式 → 管理层 → 价格。过一遍五个永久损失来源 | **「不懂，过」** |
| `probability-analyst` | **最大化期望值** | 卖方式七步：基率 → 反推市场已定价什么 → 三档情景 EV → 敏感度 → 可证伪催化剂日历 → 同业对照 → 仓位含义 | 一个带误差带的数 |
| `earnings-reader` | **论点对账** | 六步读数：上季指引 vs 本季实际对账 → 分部驱动拆解 → 现金流背离 → 指引口径偷换 → 股价反应归因 → 回 ticker 文件逐条对 | **「论点未变」** |
| `position-discipline` | **机械核对** | 六项检查：仓位上限 / SOXX 集中度 / 现金底线 / 期权禁区 / 四级动作梯 / 顶部信号。外加**手痒拦截** | **「无需动作」** |

几条设计要点，改这些文件前先理解：

- **默认输出都是「不做」。** 高通过率、频繁给动作 = 放水，不是眼光好。
- `position-discipline` **不产生规则**，规则写死在 `portfolios/2026-07-30-high-valuation-trim-discipline.md`（四级动作梯 + 仓位上限表）和 `portfolios/2026-06-24-actual-holdings-snapshot.md`（唯一真相源）。它只负责取出来对一遍。发现规则不够用是**报告缺口**，不是当场补一条。
- **手痒拦截**是 `position-discipline` 最高价值的功能：「跌了 N 天」和「反弹 N% 踏空了」都不是触发器，是同一错误的两面。触发器只有信号转红、仓位破线、退出条件阈值到达三种。
- 四个都**不写文件**，产出交父 agent 定夺；都不给目标价和买卖建议（项目 `CLAUDE.md` 硬性规定）；都继承全局 tagging + 置信度纪律。

---

## Claude Code 内置 & 插件（Codex 不可用）

以下不是本地文件，由 Claude Code 或官方插件提供，**Codex 无法引用**，列在这里只为避免重复造轮子。

**已装插件（6）**：`swift-lsp` · `clangd-lsp` · `code-review` · `commit-commands` · `pr-review-toolkit` · `claude-md-management`

**常用内置 skill**：`code-review:code-review`（评审 PR）· `security-review`（分支待提交改动的安全审查）· `simplify`（复用/简化/效率清理，只管质量不找 bug）· `dataviz`（**画任何图表前必读**）· `artifact-design` / `artifact-diagramming` / `artifact-capabilities`（发布 Artifact 页面）· `claude-api`（Claude API/SDK 参考，涉及 Anthropic 模型时必读，别凭记忆答）· `update-config`（改 settings.json / 配 hooks）· `run`（跑起来看效果）· `loop` / `schedule`（定时与循环任务）· `fewer-permission-prompts`（减少权限弹窗）

---

## 维护

新增或删除 `~/.claude/skills/` 或 `~/.claude/agents/` 下的条目后，回来更新本表。核对当前实际状态：

```bash
ls ~/.claude/skills/ ~/.claude/agents/
```

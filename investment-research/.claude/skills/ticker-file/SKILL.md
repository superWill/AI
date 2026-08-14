---
name: ticker-file
description: 建立或更新 investment-research/tickers/<TICKER>.md 个股档案的完整流程，含数据抓取、章节口径、标注纪律和落盘后必跑的校验脚本。Use when 用户说"建个 X 的档案"、"给 X 建档"、"更新 X 的 ticker"、"把 X 加进跟踪"、"X 的估值数据过期了"、"补一下 X 的财报数据"，或需要新增/修改 tickers/ 目录下任何个股文件时。
---

# Ticker 档案

## 成功标准（做完长什么样，不是怎么做）

一份合格的 ticker 档案满足以下全部条件：

1. **章节骨架与 `tickers/_template.md` 一致**，缺的章节留空而不是删掉。
2. **每个数字有基准日**：`关键数据` 的 `##` 标题上带 `（基准 YYYY-MM-DD，来源）`，frontmatter 的 `last_updated` 同步更新。
3. **每条论断带标注**：`[KNOWN]`/`[COMPUTED]`/`[INFERRED]`/`[COMMON]`/`[GUESS]` + 置信度。不确定的数字标 `(待核实)`。
4. **`退出条件` 和 `跟踪信号` 写得可执行**——是具体阈值和数据项，不是形容词。这两节是 `earnings-reader` 和 `position-discipline` 的输入，写虚了下游全废。
5. **`audit_notes.py` 对这个 ticker 报 `aligned`，不是 `无快照数据`。**（退出码 0 不够，见坑 ⑦）
6. 没有目标价、没有买卖建议（项目 `CLAUDE.md` 硬规定）。

## 流程

**新建**：`cp tickers/_template.md tickers/<T>.md` → 抓数 → 填 frontmatter（`layer` 是 9 层产业链位置，`position_type` = core/thematic/payoff/hedge）→ 自上而下填 → 跑校验。

**更新**：先看 `last_updated` 有多旧 → 只改需要改的章节 → **重大事件另起 `## ⭐ YYYY-MM-DD：<事件>` 插在 `风险` 之前**，不要改写原文（保留判断轨迹）→ 跑校验。

## 已知的坑（都是真踩过的，不是预防性猜测）

**① 市值漂移会让 `audit_notes.py` 退出 1。** 改了估值/市值就必须跑，这是 `CLAUDE.md` 的硬规定。默认阈值 20%。

**② 单一来源 + 印证既有结论 → 置信度封顶 MED，标「待交叉核实」。** 这个错在本仓库重复过至少 3 次（见 memory `single-source-confirming-thesis-low-confidence`）。广泛转载不等于独立验证，要追到原始来源。

**③ 快照可能是坏数据，别拿它推翻真价。** SKHY 那次把真实价 $167.88 当幻觉、信了坏快照 $63.75。数字反常时先用 `wc`/`md5`/重定向到文件再 Read 聚合观测，别信肉眼原始流（memory `bash-output-aggregate-observation` / `suspicion-allocation-external-anchor`）。

**④ `仓位与历史` 表有口径冲突，写之前想清楚。** 项目规定「持仓状态只在 `portfolios/` 记」，但 75 个 ticker 里有 27 个填了这张表，且记录了权重变化。**现行口径**：ticker 表记**决策轨迹与理由**（为什么做），当前权重的真相源是 `portfolios/`。**往 ticker 表里写一行不等于更新了持仓**——两处冲突时以 `portfolios/` 为准。

**⑤ 2026-02 之后的事实必须 WebSearch 并引用来源 URL 或季报页码。** 知识截止 2026-01，凭记忆填财务数据是本项目最严重的违规。

**⑥ 有期权禁区的标的要在 `仓位与历史` 下加引用块提醒。** 正在减仓的内存/SOXX 腿（MU/SKHY/NVDA/TSM）不得卖 put，NVDA 档案里有现成写法可抄。

**⑦ ⚠️ `audit_notes.py` 退出 0 常常是假绿。** 它只校验快照里存在的 ticker，不在快照里的直接 skip 且**不影响退出码**。2026-08-06 实测：73 个档案里 72 个被 skip，`aligned=1`，退出码 0。

**⑧ ⚠️ `fetch_quotes.py --tickers X` 不带 `--out` 会污染当天的正式快照。** 源码是 `out_path = args.out or (OUT_DIR / today.csv)`——窄集合会**覆盖**当天的全量快照。这已经发生过：快照 ticker 数 07-17 是 56、07-13 是 54，到 07-30 塌成 12（一次 BRK 分析留下的）。**要抓单个 ticker 必须给 `--out` 指到临时路径，再用 `--snapshot` 喂给 audit。**

**⑨ 新建档案后要把 ticker 加进 `scripts/tickers.txt`。** 否则它永远进不了全量快照，也就永远不被校验。当前 `tickers.txt` 有 57 个而 `tickers/` 有 73 个档案——**16 个档案在校验范围外**，别再加一个。

## 确定性工具

```bash
cd investment-research
.venv/bin/python scripts/fetch_quotes.py --tickers <T>          # 抓最新快照 → data/snapshots/
.venv/bin/python scripts/audit_notes.py --threshold 20          # 落盘后必跑，退出码 0 才算完
.venv/bin/python scripts/entry_price_irr.py <T> --target-irr 15 # 估值锚：反推入场价（不是目标价）
python3 scripts/build_html_site.py                              # 改了导航/新增文件才跑
```

`entry_price_irr.py` 支持 `--fcf` 触发 reverse DCF、`--batch` 多标的横向对比，详见其 docstring。

## 验收

落盘后按顺序跑。**第 1 步不能省**，否则第 2 步是假绿（坑 ⑦）：

```bash
cd investment-research
T=NVDA   # 换成目标 ticker
grep -qx "$T" scripts/tickers.txt || echo "$T" >> scripts/tickers.txt   # 1. 先纳入 universe（坑 ⑨）

# 2. 抓快照。二选一，别用第三种写法：
.venv/bin/python scripts/fetch_quotes.py                                # 全量，写当天正式快照（推荐）
# 只抓单个时必须给 --out，且 --out/--snapshot 都要用绝对路径（坑 ⑧⑩）：
# .venv/bin/python scripts/fetch_quotes.py --tickers $T --out "$PWD/data/_tmp-quotes.csv"
# .venv/bin/python scripts/audit_notes.py --threshold 20 --snapshot "$PWD/data/_tmp-quotes.csv"
# rm -f data/_tmp-quotes.csv

.venv/bin/python scripts/audit_notes.py --threshold 20 | grep -- "$T"   # 3. 必须看到对比结果，不是"无快照数据"
grep -cE "待核实" tickers/$T.md                                          # 4. 允许有，但你要知道有几个
grep -E "^(ticker|last_updated):" tickers/$T.md                         # 5. frontmatter 没漏
```

**⑩ ⚠️ `audit_notes.py --snapshot` 只接受绝对路径。** 传相对路径会在 `audit_notes.py:133` 的 `snap_path.relative_to(ROOT)` 抛 `ValueError` 崩掉（2026-08-06 实测），脚本 docstring 里写的相对路径用法是坏的。

`audit_notes.py` 报 drift 时不要调高阈值绕过——那是在关掉这个仓库唯一的机器校验。

## 相关

- 骨架：`tickers/_template.md`；范例：`tickers/NVDA.md`（含 ⭐ 事件段和禁区提醒的写法）
- 另一种卡片形态：`tickers/_next-apple-progress-template.md`（进度卡，不是估值档）
- 下游消费者：`.claude/agents/earnings-reader.md`、`.claude/agents/position-discipline.md`

---
name: weekly-review
description: 投研周复盘的固定节拍流程——时间驱动（不是事件驱动）地跑一遍四大触发器读数、持仓纪律检查、行为盲区自检，落一段周记到 notes/。Use when 用户说"周复盘"、"做个复盘"、"这周投研盘一盘"、"/weekly-review"，或距上次周记 ≥7 天需要主动提醒时。解决的问题：事件驱动的复盘逮不住"手痒/踏空焦虑/信号读数漂移"这类慢性偏差，只有固定节拍才逮得住（思路来源 @bitfish 的"周复盘"Loop）。
---

# 投研周复盘

> 这是**时间驱动**的 Loop，不是事件驱动。哪怕这周啥也没发生也要跑——"没发生"本身就是一条读数。
> 目标不是产出观点，是**给上周的自己报错**：读数漂了没、纪律破了没、手痒了没。

## 成功标准（做完长什么样）

一次合格的周复盘满足全部：

1. **四大机械触发器有本周读数**（AI capex 顶部信号 watchlist 的 0/4 计数 + 逐条状态），并与上周对比"哪条动了"。
2. **持仓过了一遍 `position-discipline`**（仓位上限、现金底线、期权禁区、四级动作梯），产出"有没有被破 + 破了的规定动作"。
3. **行为盲区自检**：本周有没有出现 memory 里记过的发作模式——手痒（`capital-preservation-first`）、按天数/深度抄底（`dip-buy-trigger-signals-not-daycount`）、踏空焦虑、单来源印证既有结论（`single-source-confirming-thesis-low-confidence`）。有就点名，没有就写"本周未发作"。
4. **一段周记落 `notes/YYYY-MM-DD-weekly-review.md`**（当周周日或复盘当日日期）。**不落盘 = 没做**（这正是断点①："信息不过系统等于没进过脑子"）。
5. **不产出目标价/买卖建议**（项目 `CLAUDE.md` 硬规定）——产出的是论点变化 + 可选动作 + 三档情景。

## 流程

1. **先看上一份周记**：`ls -t notes/*weekly-review.md | head -1`，读它的"待观察"清单，逐条对账"兑现了没"。没有上一份就写"首次周复盘"。
2. **刷价格快照**（改了估值判断才需要）：`.venv/bin/python scripts/fetch_quotes.py`。
3. **四大触发器读数**：对照 memory `ai-capex-cycle-topsignal-watchlist` 的四大机械触发器 + ⑥融资结构信号，逐条给本周状态，算 X/4。
3b. **领先读数：算力价格 + 增速二阶导（2026-10-21 起，用户定）**。四触发器全是滞后量（capex 指引、NVDA 指引要等财报），这两组先动，先看：
   - **算力租金价格**（周期里唯一不滞后的量）：SemiAnalysis H100 一年期合约指数（newsletter.semianalysis.com）· SF Compute H100 现货（sfcompute.com）· Blackwell 按需价（Lambda / RunPod 公开价目）。**判据：现货见顶回落 = 黄；一年期合约连续两个月跌 >20% = 红。** 2026-10 基线：H100 1y $2.35（3 月，自 $1.70 +40%）、Blackwell 现货 $4.08（两月 +48%）。
   - **增速二阶导**：**任何需求序列「增速连续两季下降」= 黄，不必等价格跌。** 序列：SPCX SI 收入 QoQ 增速与每 GW 收入（Q1'27 指引隐含 $36–43B/GW，行业 $15–20B）· CRWV / ORCL OCI 收入增速与 RPO 环比增量 · GCP / Azure 增速 · MSFT / GOOGL RPO 增量 · NVDA 数据中心 QoQ（= 触发器③）· Starlink 消费净增（Q2 170 万 → Q3 160 万，已下降一次）· OpenRouter 周 token 量（openrouter.ai/rankings，公开、周级）· OpenAI / Anthropic ARR 增速（有一手报道时）。
   - **规则**：增速下降 + 供给（capex / GW）仍加速 = 黄 → **当周把对应的动作梯级别写死**；再加价格转跌 = 红 → 执行。黄灯本身不是动作。
   - **信用**：CRWV 无担保债收益率 / CDS、ORCL CDS（延续）。
   - **其它待观察（10/20 待办合并进来）**：GS prime 半导体净仓位、BofA FMS 现金水平、USDCNY、NVDA 担保簿 $105B 上限动用额、ACIE 增速、ASML 2027/2028 产能措辞。
   - 一手源优先：`.venv/bin/python scripts/fetch_primary.py <TICKER>`（见 memory `primary-sources-over-secondary`）。
4. **持仓纪律**：调 `position-discipline` agent（或按其规则手动过）——只看 `portfolios/`，不看研究记录（避免双源真相）。
5. **行为自检**：对照成功标准第 3 条那几个 memory，诚实点名本周的冲动/偏差。
6. **落盘**：写周记（模板见下），列出"本周结论变化 / 下周待观察 / 待核实项"。
7. **更新 memory**（可选）：若本周发现一个新的稳定偏差或反应模式，追加/更新对应 memory，并在 `MEMORY.md` 加一行指针。

## 周记模板

```markdown
# 周复盘 YYYY-MM-DD

## 上周待观察对账
- <上周列的项> → <兑现了/没兑现/仍在等>

## 四大触发器（X/4）
- ①CoWoS 缺口: <状态>
- ②超大厂卖过剩算力: <状态>
- ③NVDA 二阶导: <状态>
- ④capex 是否骤停: <状态>
- ⑥融资结构（vendor financing/发股 fund capex）: <状态>

## 领先读数（价格 + 二阶导）
- 算力租金（H100 1y / 现货 / Blackwell）: <本周值，环比，绿/黄/红>
- 增速二阶导: <哪个需求序列增速连续下降、几季；供给端是否仍加速>
- 信用（CRWV / ORCL）: <bp，环比>
- 黄灯对应的动作梯级别（若有）: <写死，不执行>

## 持仓纪律
- 仓位/现金/期权禁区: <有无被破 + 规定动作>

## 行为自检
- 手痒/抄底冲动/踏空焦虑/单来源印证: <本周是否发作，点名>

## 本周结论变化
- <哪个论点被数据改了>

## 下周待观察
- <可证伪的判据 + 开奖时间>

## 待核实
- <标 (待核实) 的项>
```

## 已知的坑

**① 别把周复盘做成"再研究一遍"。** 它是报错机制不是产出机制——重点是对账上周、逮本周偏差，不是生成新观点。跑超过 20 分钟就是跑偏了。

**② "这周没事"要照跑照写。** 慢性偏差（读数漂移、纪律松动）恰恰在平静周积累。空周记也是数据点。

**③ 触发器状态别只写数字，要写"哪条动了"。** 0/4 连续 N 周和"这周③从绿转黄但仍 0/4"是两条完全不同的信息。

**④ 持仓只从 `portfolios/` 读。** 研究记录 ≠ 持仓记录，混用会造成双源真相（`CLAUDE.md` 硬规定）。

**⑥ 增速下降 ≠ 价格下降 ≠ 动作。** 二阶导转负是黄灯，作用是提前把动作梯写死，不是减仓理由；价格（租金指数）转跌才是红灯。把黄灯当红灯，就是 `dip-buy-trigger-signals-not-daycount` 的镜像错误。

**⑤ 落盘走投研提交纪律**：`git branch --show-current` 确认在 main → `git add investment-research/` → `git diff --cached --name-only | grep -v "^investment-research/"` 验零跨目录 → commit。**若 HEAD 不在 main（别的会话切了分支）或全局有跨目录脏改动，停下问用户，不擅自切分支。**

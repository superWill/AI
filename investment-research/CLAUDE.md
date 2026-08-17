# investment-research · 工作纪律

> 跨项目纪律见 [`../CLAUDE.md`](../CLAUDE.md)。本文件只补**投研特有**的。
> 目录结构 / 日更流程见 [`README.md`](README.md)；agent 提示词见 [`agents/`](agents/)。
> 姊妹版 `../investment-research-2007-apple/` 是互补不替代，重叠 ticker 两边都要更新、互不覆盖。

## 数据：不臆造，知识截止 2026-01

- 价格、市值、财务数据——**不凭空造**。2026-02 之后的事实必须 WebSearch 拉 + 引用来源（URL / 季报页码）。
- 估值不确定 → 标「(待核实)」，不要装确信。
- 改了 `tickers/<T>.md` 的估值/市值 → 跑 `scripts/audit_notes.py` 查陈旧；改了导航/生成页 → 跑 `scripts/build_html_site.py`。

## 账户硬约束（来自 memory）

- **期权：可用但只走两条正道**（2026-07-23 确认有权限、可卖 put）：cash-secured put（愿接货价=收钱的限价单）+ 备兑 call。禁区：买短期虚值博方向、裸卖 call、对正在减仓的内存/SOXX 腿（MU/SKHY/NVDA/TSM）卖 put、用期权放大 SOXX 敞口。短 put 义务必须记入 `portfolios/`（见 `ibkr-options-playbook`）。
- 组合真实风险对象是**半导体周期不是大盘**：betaSOXX 0.89 / betaSPY 2.31。风险讨论锚定 SOXX（见 `portfolio-soxx-factor-risk`）。

## 表达纪律

- 不给「目标价」「建议买入/卖出」——给的是**论点变化 + 可选动作 + 三档情景（悲观/基准/乐观）IRR**。
- 持仓状态只在 `portfolios/` 记，研究记录不等于持仓记录，避免双源真相。

## 环境

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/fetch_quotes.py
```

## 提交流程（2026-08-17 起，本项目覆盖 [`../CLAUDE.md`](../CLAUDE.md) 的分支纪律）

- **直接在 `main` 上提交，不开分支。** 上层 `../CLAUDE.md` 的「一类改动一个 branch / 在 main 上先开 branch」**对投研不适用**——用户已明确改为 main 直提。
- **每次调研产出落盘后可直接 commit + push，不必每次征求同意。** 这是常驻授权，仅限本目录。
- 用 `docs(investment): ...` scope。

### ⚠️ 但这三条是硬约束，每次都要做

1. **提交前先确认当前分支**：`git branch --show-current`。（曾因未确认而在分支切换后提错位置。）
2. **只 stage `investment-research/`**：`git add investment-research/`，然后必须验证零跨目录混入：
   `git diff --cached --name-only | grep -v "^investment-research/"` —— 有输出就停下。
3. **这是 monorepo，`/Users/songzijian/Coding/AI` 下同时跑着 embedded-gateway / iOS 等其他会话的改动**（见 memory `stay-in-investment-lane`）。**绝不 `git add .`、绝不 `git commit -a`。**

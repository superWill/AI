# investment-research · 工作纪律

> 跨项目纪律见 [`../CLAUDE.md`](../CLAUDE.md)。本文件只补**投研特有**的。
> 目录结构 / 日更流程见 [`README.md`](README.md)；agent 提示词见 [`agents/`](agents/)。
> 姊妹版 `../investment-research-2007-apple/` 是互补不替代，重叠 ticker 两边都要更新、互不覆盖。

## 数据：不臆造，知识截止 2026-01

- 价格、市值、财务数据——**不凭空造**。2026-02 之后的事实必须 WebSearch 拉 + 引用来源（URL / 季报页码）。
- 估值不确定 → 标「(待核实)」，不要装确信。
- 改了 `tickers/<T>.md` 的估值/市值 → 跑 `scripts/audit_notes.py` 查陈旧；改了导航/生成页 → 跑 `scripts/build_html_site.py`。

## 账户硬约束（来自 memory）

- **不能做期权**。任何对冲方案排除 put / call，只能用成分管理 + 现金（见 `no-options-trading`）。
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

## 提交 scope

- 用 `docs(investment): ...`，**不要**和嵌入式 / iOS 改动混进同一个 commit 或 branch。

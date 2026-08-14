# investment-research

个人美股投研工作区。聚焦 AI / 机器人 / HBM / 量子 / PQC 产业链。

## 目录结构

```
investment-research/
├── notes/         主题/产业链研究笔记（按 YYYY-MM-<topic>.md 命名）
├── tickers/       单只股票深度研究（文件名 = 大写 ticker）
├── portfolios/    组合配置与调仓记录
├── dashboards/    关注列表与跟踪信号
├── data/
│   ├── snapshots/ scripts/fetch_quotes.py 输出的每日行情快照
│   └── prices/    历史日线（按需）
└── scripts/       数据抓取与分析脚本
```

## 工作流

1. **主题驱动** — `notes/` 写产业链/主题级笔记，识别瓶颈节点和受益层
2. **标的拆解** — 从主题笔记提取候选 ticker，在 `tickers/<TICKER>.md` 单独深挖
3. **组合落地** — `portfolios/` 写当前持仓 + 仓位逻辑 + 调仓记录
4. **持续跟踪** — `dashboards/watchlist.md` 列关注信号；定期跑脚本刷新行情

### 寻找“下一只 2007 苹果”的日更流程

适合做`未来平台型大牛股`跟踪，不是一次性报告，而是持续更新进度。

1. **候选池** — [`dashboards/next-apple-candidates.md`](dashboards/next-apple-candidates.md)
2. **评分规则** — [`dashboards/next-apple-scoring.md`](dashboards/next-apple-scoring.md)
3. **单公司进度卡** — [`tickers/_next-apple-progress-template.md`](tickers/_next-apple-progress-template.md)
4. **每日更新日志** — [`dashboards/daily-progress-log.md`](dashboards/daily-progress-log.md)

日更时只回答三件事：

- 昨天发生了什么
- 对 thesis 是利多还是利空
- 候选排序是否变化

## 数据脚本

首次环境准备（创建项目内 venv，避开 PEP 668）：

```bash
python3 -m venv .venv
.venv/bin/pip install -r scripts/requirements.txt
```

之后每次运行：

```bash
# 1. 行情快照（每日跑一次）
.venv/bin/python scripts/fetch_quotes.py
# → data/snapshots/YYYY-MM-DD.csv（40 行：当日价格/市值/PE/52周区间/beta 等）

# 2. 历史日线（按需跑，回看走势/验证涨跌幅）
.venv/bin/python scripts/fetch_history.py --tickers LITE AEHR --period 1y
# → data/prices/<TICKER>.csv（每只一份 OHLCV）

# 3. 审计：对比 ticker 文档里的市值数据 vs 最新快照，标记偏差
.venv/bin/python scripts/audit_notes.py
# 阈值默认 ±20%，可加 --threshold 30 调整

# 4. 小市值错定价初筛（发现工具，不是买入清单）
.venv/bin/python scripts/screen_small_cap_value.py
# → data/screens/YYYY-MM-DD-small-cap-value.csv

# 5. 为人工挑选的候选补充可比财务字段
.venv/bin/python scripts/enrich_value_shortlist.py AXR SHOE BBW FOR ETD
# → data/screens/YYYY-MM-DD-value-shortlist.csv
```

`audit_notes.py` 是写新 ticker 文档时的对账工具——任何手写市值与最新快照偏差超过阈值会被列出，便于发现"copy 自老笔记"的过期数据。

## HTML 阅读层

推荐日常阅读直接看 HTML：

- 原型首页：[`index.html`](index.html)
- 完整站点首页：[`site/index.html`](site/index.html)
- 全部文档索引：[`site/all-docs.html`](site/all-docs.html)

重新生成整站 HTML：

```bash
python3 scripts/build_html_site.py
```

脚本会把 `README / notes / dashboards / agents / portfolios / tickers` 下的 Markdown 自动生成到 `site/` 目录。

## 约定

- 主题笔记文件名：`notes/YYYY-MM-<topic>.md`
- 单股研究文件名：`tickers/<TICKER>.md`（大写，不带前缀）
- 组合文件名：`portfolios/YYYY-MM-<name>.md`
- 所有日期用 ISO（YYYY-MM-DD），不用相对时间
- 每个 ticker 文档顶部带 frontmatter，便于后续脚本聚合

## 起点文档

- HTML 首页：[`index.html`](index.html) —— 推荐日常阅读入口
- 完整 HTML 站点：[`site/index.html`](site/index.html)
- 主题笔记：[`notes/2026-05-ai-robotics-quantum-supply-chain-v1.md`](notes/2026-05-ai-robotics-quantum-supply-chain-v1.md) —— AI/机器人/HBM/量子产业链全景
- 日度市场热点：[`notes/2026-05-08-us-market-hotspots.md`](notes/2026-05-08-us-market-hotspots.md)
- 当前组合：[`portfolios/2026-05-core-thematic-payoff.md`](portfolios/2026-05-core-thematic-payoff.md)
- 关注列表：[`dashboards/watchlist.md`](dashboards/watchlist.md)

## 免责

本目录所有内容仅为个人研究与决策参考，**不构成投资建议**。半导体、量子板块波动剧烈，仓位与风险自负。

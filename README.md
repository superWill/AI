# AI

个人调研工作区的统一容器。所有"研究类"工作（投研、产品、市场、技术）都归这里，避免散落在各处。

## 当前调研项目

| 目录 | 主题 | 状态 |
|---|---|---|
| [`investment-research/`](investment-research/) | 美股 AI / 机器人 / HBM / 量子 / PQC 产业链投研 | 活跃，含 36 只 ticker 档、组合 v2、数据抓取脚本 |
| [`product-research-business-scenarios/`](product-research-business-scenarios/) | 业务场景驱动的产品调研框架 | 活跃，含场景库、用户分群、竞品矩阵、机会图 |

每个子目录有自己的 README、目录约定和工作流，独立运转。

## 约定

### 新增调研项目

放在 `AI/<name>/`，目录名用小写英文 + 连字符（例：`market-research-china-evs/`）。

每个子项目应该有：
- `README.md`：一句话定位 + 目录结构 + 工作流
- 清晰的子目录划分（每一步研究阶段一个目录）
- 大文件 / 敏感数据交给仓库根的 `.gitignore` 兜底

### 命名约定

- 调研笔记：`YYYY-MM-<topic>.md`（按月归档）
- 单股研究：`tickers/<TICKER>.md`（大写）
- 组合 / 决策文档：`portfolios/YYYY-MM-<name>.md`
- 日期统一用 ISO（`2026-05-08`），不用相对时间

### 数据 vs 笔记

- **笔记 / 决策**（.md）—— 提交到 git
- **抓取数据**（.csv / .json snapshots）—— 小的可以提交（提供历史审计），大的考虑用 LFS 或外部存储
- **venv / 缓存 / 凭证**（`.venv/` `.env` `__pycache__/`）—— 已在 `.gitignore` 排除

## 自动化

`investment-research/` 已接入 [Hermes Agent](https://hermes-agent.nousresearch.com/)：
- 每日定时跑数据抓取与文档审计
- 通过飞书机器人推送报告
- 配置文件不在本仓库（在 `~/.hermes/`），避免凭证泄露

## 免责

仅个人研究记录，**不构成投资建议或决策依据**。市场分析、产品判断、用户画像等结论均为研究过程中的工作假设，需结合一手数据与专业意见验证。

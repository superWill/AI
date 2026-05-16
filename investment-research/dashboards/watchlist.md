# Watchlist & 跟踪信号

> 配合 `scripts/fetch_quotes.py` 每日/每周快照使用

## 周度跟踪

- HBM3E / HBM4 现货价格走势（DRAMeXchange、TrendForce）
- 主要标的 forward PE 变化
- MU / SK Hynix / VRT / GLW 重大新闻
- VIX / SOXX 相对表现（板块 beta 信号）

## 月度跟踪

- WSTS / SIA 半导体行业月度数据
- AI 数据中心订单（VRT、SU.PA、ETN 财报评论）
- 机器人厂商出货数据（Tesla Optimus、Figure、Unitree）
- 主要标的的相对强弱（SMH 为基准）

## 季度跟踪（财报季）

- 全部持仓公司财报：营收、毛利、指引、FCF
- backlog / book-to-bill（设备股）
- NRR（Cloudflare / 软件股）
- McKinsey、Gartner、IDC 行业报告

## 重大事件监控

### 已记录宏观重大事件

| 日期 | 事件 | 类型 | 市场含义 | 需要跟踪 |
|---|---|---|---|---|
| 2026-05-13 | Kevin Warsh 获美国参议院确认出任美联储主席，接替 Jerome Powell；Powell 主席任期于 2026-05-15 结束。 | 政策 / 利率 / Fed 独立性 | 市场重新定价 Fed 政策路径、政治独立性和长端利率风险；高估值成长股、AI 链、小盘股对收益率上行更敏感。 | 10Y/30Y 美债收益率、FOMC 票委表态、Warsh 对资产负债表和降息路径的表述、美元与黄金反应 |

### 触发项

- [ ] 任何 PQC 算法被破解
- [ ] 中国稀土出口管制变化
- [ ] AI 大模型架构突破（Mamba 类 / MoE 普及）
- [ ] 量子优势演示成功/失败
- [ ] HBM 长协价格更新
- [ ] Warsh 上任后首次 FOMC / 国会证词改变降息或缩表预期

## 2026 H2 关键时间点

- HBM4E 三星样品交付（Q2）
- IBM 演示首次"量子优势"（Q4）
- 加拿大 PQC 迁移计划（4 月）
- Tesla Optimus 50,000 台目标

## 2027–2028 关键拐点

- HBM5 量产
- 1.6T 光模块成主流
- Quantinuum IPO 可能性
- 第一波 PQC 强制合规截止

## 关键阈值（触发提示）

> 数据基准 2026-05-07 yfinance 快照；与 [portfolios/2026-05-core-thematic-payoff.md](../portfolios/2026-05-core-thematic-payoff.md) v2 联动。

### 持仓阈值

| 标的 | 当前 | 减仓阈值 | 加仓阈值 |
|---|---|---|---|
| MU Forward PE | 7.13 | >12（"科技股化"信号 → 估值已透支）| <6（极度便宜） |
| GLW TTM PE | 86.88 | 维持 → 暂不加仓 | 回调到 50 日均线 $150 |
| GLW Forward PE | 44.92 | >55（泡沫区） | <30 |
| IBM Forward PE | 16.78 | — | 维持现状即继续分批加 |
| IBM 价格 | $225.74 | $300+（接近 v1 看涨情境上沿）| <$220（贴 52w 低，加倍） |
| GEV 价格 | $1,118.96 | $1,200+（贴 52w 高，估值透支） | <$900（回到 50 日均线下）|
| VRT YoY 增速 | ~30%+ | <15% | — |
| Cloudflare NRR | — | <115% | >125% |
| 单台 IBM/MU/GEV 已涨 50%+ | — | 部分止盈 30% | — |

### 跟踪但暂不持有（demoted）

| 标的 | 触发"重新加入推荐"的条件 |
|---|---|
| ACLS | Veeco 合并整合落地 + PE 回到 25x 以下 |
| AEHR | 客户数破 5 + 单客户占比 < 50% + beta 回落到 < 2.5 |
| SNDK | Forward PE 反超 MU 30%+（NAND 与 HBM 重新分化） |
| LITE | 回调 30%+ 且 Forward PE < 25x |

### 板块触发卖出

详见 portfolio v2 的"系统性风险触发卖出"表。

## 数据快照

每次跑 `scripts/fetch_quotes.py` 后，可在 `data/snapshots/YYYY-MM-DD.csv` 查最新行情。

```bash
ls -lt ../data/snapshots | head -5    # 最近 5 个快照
```

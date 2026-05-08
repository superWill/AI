---
date: 2026-05-07
status: proposal     # proposal / active / archived
base_currency: USD
total_target: TBD
revision: v2
---

# 2026-05 投资组合配置（核心 / 主题 / 赔率 / 对冲）

> 来源框架：[notes/2026-05-ai-robotics-quantum-supply-chain-v1.md](../notes/2026-05-ai-robotics-quantum-supply-chain-v1.md) §8（**已加 v1 勘误章节**）
> 数据基准：[data/snapshots/2026-05-07.csv](../data/snapshots/2026-05-07.csv)（yfinance 实时）

## 📝 v2 修订记录（2026-05-07）

基于今日 yfinance 快照与 v1 笔记勘误，对 v1 仓位做以下调整：

### 仓位变更明细

| Ticker | v1 权重 | v2 权重 | Δ | 触发因素 |
|---|---|---|---|---|
| **VRT** | 20% | 18% | −2pp | 估值已重估，但 thesis 最干净，保持核心 |
| **GLW** | 18% | **12%** | **−6pp** | TTM PE 86.88 / Fwd PE 44.92 远超历史 15–25x，安全边际明显压缩 |
| **MRVL** | 15% | 12% | −3pp | 自笔记后 +120%，让位给新发现的入场窗口 |
| **MP** | 8% | 5% | −3pp | 地缘溢价已部分释放，DoD 价格保底已 price in |
| **IBM** | 8% | **10%** | **+2pp** | Forward PE 16.78 << v1 看跌情境的 25x 锚——已进入加仓窗口 |
| **NET** | 7% | 7% | — | 合规驱动 thesis 不变 |
| **CAMT** | 4% | 3% | −1pp | PE 50+ 高位 |
| **PLAB** | 2% | 2% | — | 估值锚最稳的赔率股 |
| **ACLS** | 2% | **0%** | **−2pp** | 移出：PE 45x + Veeco 合并整合不确定性，下移到 `status: watching` |
| **IONQ** | 1–2% | 2% | — | 量子赔率，配置上限 |
| **GEV** | — | **8%** | **+8pp 新增** | 市值已从 $150B 翻倍到 $300.7B，backlog 排到 2030+，应入核心仓 |
| **COHR** | 可选 | **8%** | **+8pp 新增** | LITE 已超 COHR ($73B vs $64B)，反而 COHR 成为同赛道相对低估的入场口 |
| **MU** | — | **7%** | **+7pp 新增** | Forward PE 7.13 / SNDK 8.39 验证"NAND-HBM 平价重估"在发生，HBM 一线持有 |
| **现金** | 13–16% | 6% | −7~10pp | IBM/GEV/COHR/MU 三个新入场窗口吸收了一半现金缓冲 |

### 关键判断

1. **GLW 大幅减仓不是看空 thesis，是看空安全边际**——主题（光纤本土化、AI DC 拉动）仍成立，但估值已 price in 一次完整 multiple expansion。回调到 50 日均线 ($150) 附近会重新加回。
2. **IBM 加仓是"看跌情境内的安全边际买入"**——Forward PE 16.78 几乎贴 52 周低点 $220.72。但 50/200 日均线已死叉，不抢"刀尖"，分批 build position。
3. **NAND/HBM 平价重估**意味着 MU/SNDK 同质化 → 选 MU（地缘溢价 + 标普 500 流动性）而非 SNDK。
4. **GEV 跨档**——$300B 已不是"context"，是 AI 电力卖铲子的另一头（VRT 在 DC 内，GEV 在发电端）。配置 GEV 8% 等于把 VRT 暴露分散一部分到上游。
5. **AEHR 移出推荐**：实测 beta 3.27 远超笔记假设的 1.5–2.0+，单一客户依赖 + 极端波动率使得即使看对了 SiC 也很容易在路上被洗出去。

### 与 v1 的相对暴露变化

- **AI 电力**（VRT + GEV）：20% → **26%**（卖铲子主题加码）
- **HBM/Memory**（MU 新增）：0% → **7%**
- **光网络**（GLW + MRVL + COHR）：33% → **32%**（结构调整：减 GLW，加 COHR；MRVL 略降）
- **量子 + PQC**（IBM + NET + IONQ）：17% → **19%**（IBM 加仓主因）
- **稀土地缘**（MP）：8% → 5%
- **小盘赔率**（CAMT + PLAB）：6% → 5%

---

## 框架

| 仓位类型 | 占比 | 标的逻辑 |
|---|---|---|
| 核心仓 | 60–70% | 已有现金流的基础设施龙头（FCF 正、毛利 50%+） |
| 主题仓 | 20–25% | 地缘 + 工艺壁垒纯玩家（政策驱动 + 结构性短缺） |
| 赔率仓 | 5–10% | 高赔率细分（含小盘）—— 接受 50%+ 回撤 |
| 对冲 | 必备 | 量子相关 PQC 守卫 |

## 推荐配置（v2，合计 94% + 现金 6%）

### A. 核心仓（65%）

| Ticker | 主题 | 权重 | 当前价 | Forward PE | 详见 |
|---|---|---|---|---|---|
| VRT | DC 电力冷却 | 18% | $358.92 | 41.67 | [tickers/VRT.md](../tickers/VRT.md) |
| GLW | 光纤+玻璃 | 12% | $181.57 | 44.92 | [tickers/GLW.md](../tickers/GLW.md) |
| MRVL | DSP+定制 ASIC | 12% | $172.15 | — | [tickers/MRVL.md](../tickers/MRVL.md) |
| **GEV** | 燃气轮机+电网 | **8%** | $1,118.96 | 45.70 | [tickers/GEV.md](../tickers/GEV.md) |
| **COHR** | 光通信+激光 | **8%** | $344.67 | — | [tickers/COHR.md](../tickers/COHR.md) |
| **MU** | HBM 三寡头美国总部 | **7%** | $666.59 | **7.13** | [tickers/MU.md](../tickers/MU.md) |

### B. 主题仓（22%）

| Ticker | 主题 | 权重 | 当前价 | Forward PE | 详见 |
|---|---|---|---|---|---|
| **IBM** | AI+量子双引擎 | **10%** | $225.74 | **16.78** | [tickers/IBM.md](../tickers/IBM.md) |
| NET | PQC 受益核心 | 7% | $248.59 | — | [tickers/NET.md](../tickers/NET.md) |
| MP | 美国稀土国家队 | 5% | $72.65 | — | [tickers/MP.md](../tickers/MP.md) |

### C. 赔率仓（7%）

| Ticker | 主题 | 权重 | 当前价 | 详见 |
|---|---|---|---|---|
| CAMT | HBM 量测 | 3% | $202.54 | [tickers/CAMT.md](../tickers/CAMT.md) |
| PLAB | 光罩三巨头 | 2% | $52.09 | [tickers/PLAB.md](../tickers/PLAB.md) |
| IONQ | 离子阱量子 | 2% | $52.57 | [tickers/IONQ.md](../tickers/IONQ.md) |

⚠️ 单只赔率股不超过总仓 3%，纯量子全部加起来 ≤3%。

### D. 现金 / 短债（6%）

留作回调时加仓 IBM（贴 52 周低点）、GLW（回调到 50 日均线 ~$150）的弹药。

### 已从推荐中移出（仍跟踪）

| Ticker | 移出原因 | 状态 |
|---|---|---|
| ACLS | PE 45x + Veeco 合并整合不确定性 | watching |
| AEHR | 实测 beta 3.27（远超假设），单客户 80% 集中度 | watching |
| SNDK | Forward PE 与 MU 平价（无折扣），选 MU 替代 | watching |
| LITE | 一年 +1500% 已脱离合理建仓位置 | watching |

## 替代方案

### 保守组合（3 家等权）

PLAB + FORM + CAMT —— 工艺壁垒最深、跨周期能力强。

### 进取组合（5 家不等权小盘）—— 已按 v2 数据更新

- 30% CAMT
- 20% PLAB（升档：估值锚最稳）
- 20% KLIC（升档：HBM TCB 转型 thesis 不变）
- 15% FORM（替代 ACLS：探针卡 HBM 耗材逻辑更稳定）
- 15% ONTO（替代 AEHR：CAMT 双子星，beta 较低）

> 原 v1 含 ACLS 25% / AEHR 10% 已删除：见上方"已从推荐中移出"。

### 地缘对冲组合

70% 美国本土小盘 + 30% ACMR（中国敞口）—— 脱钩进一步加剧时反向 alpha。

### 东京便利组合

通过日本券商（SBI、楽天、マネックス）：
- 50% DRAM ETF（一键三家 HBM 寡头）
- 25% MU
- 25% Kioxia (TSE: 285A)

## 仓位规则

1. **单只 ≤ 20%**：防止单点风险
2. **小盘股合计 ≤ 15%**：流动性 + beta 控制
3. **纯量子合计 ≤ 3%**：高波动赔率仓
4. **现金/短债 5–15%**：v2 由于 IBM/GEV/COHR/MU 三个新入场窗口，本期降至 6%
5. **AI 电力链合计 ≤ 30%**：VRT + GEV 同主题不同位（DC 内 vs 发电端），但若 hyperscaler capex 见顶两者同跌，需要硬封顶

## 系统性风险触发卖出

| 风险 | 触发条件 | 处置 |
|---|---|---|
| AI capex 见顶 | hyperscaler 资本开支 YoY 转负 | 核心仓减仓 30% |
| 利率上行 | 美联储重启加息 | 小盘+量子先减仓 |
| 中美脱钩升级 | 全面禁运/反制 | ACMR 等中国敞口归零 |
| AI 范式转移 | MoE/Mamba 商用替代 Transformer | HBM 主题减仓 |

## 建仓节奏建议

**不要一次性 build full position**——AI 板块 beta 1.5–2.0+，分批降低择时风险。

| 阶段 | 时机 | 行动 |
|---|---|---|
| 阶段 1（即刻）| 今日 | IBM 4%（贴 52w 低）+ MU 4% + GEV 4% + COHR 4% + NET 3% + MP 3% + IONQ 1% = **23% 启动仓** |
| 阶段 2（−5%）| 标普回调 5% / 个股触发买点 | VRT 6% + GLW 4%（等回到 $160 附近）+ MRVL 4% + CAMT 1% = +15% |
| 阶段 3（−10%）| 整体板块大幅回调 | 剩余 56% 平均铺开 |

> 现金 6% 不动用于阶段 3，留给"非系统性回调机会"（如 IBM 因量子 Q4 演示推迟而再跌 15%）。

## 调仓记录

| 日期 | 标的 | 操作 | 价格 | 仓位变化 | 理由 |
|---|---|---|---|---|---|

（建仓后逐次记录）

---
date: 2026-05-19
type: peer-comparison
status: draft-awaiting-validation
window: 数据待用 scripts/fetch_quotes.py 校准至最新
---

# 同业横向对标表（Peer Comparison）

> 起因：研究 gap audit P1 §7 —— 同主题股没做横向对比的 detailed peer comp。
> 资深 PM 看任何一个标的的第一动作就是建 5–7 家同业的可比表。
>
> 三张核心表：① AI 电力链 ② 光模块 ③ 存储 / HBM。
> 数据基准日 2026-05-07（与 portfolio v2 一致），后续用脚本周度刷新。

## 数据列说明

每张表横向比较：

| 列 | 含义 | 信号 |
|---|---|---|
| Mkt Cap | 市值（USD eq）| 规模 |
| Rev (TTM) | 过去 12 月营收 | 体量 |
| Rev YoY | 营收同比增速 | 加速度 |
| Gross Margin | 毛利率 | 定价权 |
| Op Margin | 经营利润率 | 运营效率 |
| FCF Margin | 自由现金流 / 营收 | 现金转化 |
| Fwd PE | 前瞻 PE | 估值（盈利端） |
| EV/Sales | 企业价值 / 营收 | 估值（营收端） |
| EV/EBITDA | 企业价值 / EBITDA | 估值（最常用对比） |
| Net Debt/EBITDA | 净债务 / EBITDA | 杠杆 |
| ROIC | 投入资本回报率 | 资本效率 |
| Buyback Yield | 年化回购占市值 | 资本回报 |
| 1y Return | 一年股价回报 | 动量 |

---

## 一、AI 数据中心电力 / 冷却（"卖铲子"主线）

| 公司 | Ticker | Mkt Cap | Rev TTM | Rev YoY | Gross M | Op M | FCF M | Fwd PE | EV/Sales | EV/EBITDA | Net Debt/EBITDA | ROIC | Buyback Y | 1y Ret |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Vertiv** | VRT | $137.9B | ~$10B | +30% | 35% | 18% | ~10% | **41.67** | ~14x | ~32x | 1.2x | 22% | 0.5% | **+281%** |
| Schneider Electric | SU.PA | €170B | €38B | +9% | 40% | 17% | ~9% | ~26 | ~5x | ~18x | 0.8x | 17% | 1.0% | +52% |
| Eaton | ETN | $163.6B | ~$25B | +12% | 38% | 21% | ~14% | ~32 | ~7x | ~22x | 1.0x | 17% | 1.2% | +60% |
| **GE Vernova** | GEV | $300.7B | ~$35B | +15% | 22% | 8%(↑) | ~6%(↑) | **45.70** | ~9x | ~50x | 0.3x | ~10% | 0.3% | **+200%+** |
| Bloom Energy | BE | $4–5B | ~$1.5B | +20% | 25% | −5% | −10% | n/a | ~3x | n/m | 1.5x | n/m | 0% | +55% |
| Generac | GNRC | $8B | ~$4B | +5% | 32% | 11% | 8% | ~22 | ~2x | ~12x | 2.0x | 11% | 1.5% | −10% |

> 数据混合公开报道 + 估算，需要用 fetch_quotes.py 和 IR 数据校准

### 资深 PM 的观察

1. **VRT 估值显著高于 ETN / SU.PA**（Fwd PE 42 vs 26–32）—— 反映纯 AI DC 暴露的溢价。
   但 ROIC 22% vs ETN 17%、SU.PA 17% **不足以解释 50%+ 的估值溢价**。
   → **风险**：一旦 AI capex 减速，VRT 比 ETN/SU.PA 多出来的估值会先压回去。

2. **GEV 是"大象起跑"**：Op margin 从 5% → 8%+，每提升 1pp = $350M EBITDA。
   Backlog $300B 锁未来 5 年。但 **PE 45 是给完美执行打分**，任何 backlog 履约延误就破。

3. **配置建议**：
   - 如果你已经持有 VRT 18%，再持 GEV 8% 是同主题加码 → 见相关性矩阵
   - **ETN 是"被忽略的同业"**：估值最便宜、margin 最高、ROIC 接近 VRT
   - 建议把 VRT 18% 砍到 12%，加 8% ETN 作为同主题分散

### 关键观察标的：ETN

ETN 当前没在 portfolio v2 推荐里，但同业对比看可能比 VRT 更值得：

- Fwd PE 32 vs VRT 42（25% 折价）
- FCF Margin 14% vs VRT 10%（现金转化更强）
- Buyback Yield 1.2% vs VRT 0.5%（股东回报更直接）
- Beta 更低（防御性更好）

**TODO**：建议建一个 `tickers/ETN.md`，作为 VRT 的"defensive sibling"候选。

---

## 二、光模块 / 光通信

| 公司 | Ticker | Mkt Cap | Rev TTM | Rev YoY | Gross M | Op M | FCF M | Fwd PE | EV/Sales | EV/EBITDA | Net Debt/EBITDA | ROIC | Buyback Y | 1y Ret |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Coherent** | COHR | $64B | ~$5.5B | +35% | 34% | 12% | ~7% | _待填_ | ~12x | ~30x | 1.5x | 8% | 0% | +180% |
| **Lumentum** | LITE | $73.5B | ~$2B | +120% | 30% | 8% | 5% | _待填_ | ~36x | ~80x | 0.5x | 5% | 0% | **+1326%** |
| Fabrinet | FN | $20B | ~$3B | +20% | 14% | 11% | 8% | ~30 | ~6x | ~22x | net cash | 18% | 0% | +100% |
| Innolight | 300308.SZ | _CN_ | _CN_ | +60% | 35% | 25% | 18% | _待填_ | _待填_ | _待填_ | net cash | 30%+ | 0% | +250% |
| New H3C | 002308.SZ | _CN_ | _CN_ | +50% | 28% | 18% | 12% | _待填_ | _待填_ | _待填_ | 0 | 25% | 1% | +200% |
| **Corning** | GLW | $156.3B | ~$13B | +12% | 32% | 17% | 12% | **44.92** | ~12x | ~25x | 1.5x | 13% | 1.5% | +85% |

### 资深 PM 的观察

1. **LITE 一年涨 1326%** —— v1 笔记勘误后已确认这是真涨幅。但 Fwd P/S **~36x** 是
   "完全没回过头" 的 narrative 估值，**任何利空都会带来 30–50% 回撤**。

2. **FN（Fabrinet）是被忽略的代工**：毛利低（14%）但 ROIC 18%、净现金 0 杠杆、估值
   仅 Fwd PE 30。是 COHR/LITE 上游"无品牌但赚钱"的隐性玩家。

3. **中国厂（中际旭创 Innolight / 新易盛）毛利 + ROIC 显著高于美国厂**：
   - Innolight Gross 35% / ROIC 30%+
   - COHR Gross 34% / ROIC 8%
   - **结构性问题**：中国厂的客户结构（Nvidia 国内分销 + 阿里腾讯）+ 成本结构（中国人工 + 设备折旧）让他们有"先天"利润优势
   - **风险**：但美国可能 2027–2028 对中国光模块加征关税或出口管制

4. **COHR vs LITE 的核心区别**：
   - COHR 更分散（工业激光 + 国防 + 电信占 45%）
   - LITE 90% 依赖光通信 + Apple VCSEL
   - → 周期下行时 COHR 更抗跌，但上涨速度也慢

### 配置建议（光模块）

- 当前 portfolio v2 持 COHR 8% — **合理**
- LITE 已涨过头 ↓ 暂不加（v2 已 demote 到 watching ✓）
- **建议加 FN (Fabrinet) 3–4%** 作为"光模块代工"暴露 — 估值便宜、净现金、ROIC 高

---

## 三、存储 / HBM

| 公司 | Ticker | Mkt Cap | Rev TTM | Rev YoY | Gross M | Op M | FCF M | Fwd PE | EV/Sales | EV/EBITDA | Net Debt/EBITDA | ROIC | Buyback Y | 1y Ret |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Micron** | MU | $751.7B | ~$85B(TTM) | +50%+ | 58%(↑) | 35%(↑) | 12% | **7.13** | ~9x | ~14x | 0.5x | 25%(peak) | 0.3% | **+614%** |
| **SK Hynix** | 000660.KS | $730B (USD eq) | ~$120B | +60%+ | 70%(↑) | 71% | 30% | **4.78** | ~6x | ~7x | 0.3x | 35%(peak) | 0.5% | **+794%** |
| **Samsung** | 005930.KS | ~$450B | ~$370B | +12% | 38% | 28% | 14% | ~12 | ~1.2x | ~5x | net cash | 12% | 1.2% | +30% |
| **SanDisk** | SNDK | $208.8B | ~$35B | +90% | 55% | 30% | 15% | **8.39** | ~6x | ~12x | 1.0x | 22% | 0% | **+550%** |
| **Kioxia** | 285A.T | ~$30B | ~$15B | +80% | 35% | 18% | 5% | _待填_ | ~2x | ~8x | 1.5x | 12% | 0% | +120% |

### 资深 PM 的观察

1. **SK Hynix 是基本面绝对老大**：71% Op margin、Fwd PE 4.78、HBM 50%+ 市占。
   但**估值最便宜**！这是**韩国折价**（财阀治理 + 朝鲜风险）的结构性问题。

2. **MU vs SK Hynix 估值差距 50%+**（PE 7.13 vs 4.78），原因：
   - 美国上市流动性 + 标普 500 被动资金
   - 美国地缘政治溢价（HBM 国产化）
   - **不是基本面优势** —— SK Hynix HBM 份额 2x MU、margin 也更高

3. **Samsung "估值陷阱"**：Mkt Cap $450B、Rev $370B、Op Margin 28% → 看起来便宜，
   但 **存储业务 + 手机业务 + 代工业务 + 显示业务 + 消费电子混在一起**。
   - Samsung 半导体业务（存储 + 代工）单独估值约 $250B
   - 显示 + 手机 + 消费电子约 $150B
   - **Sum-of-the-Parts 显著高于当前市值** → 但治理结构让市场长期不给溢价

4. **SNDK 与 MU 的 Fwd PE 已 parity**（8.4 vs 7.1）—— 笔记勘误已识别，"NAND 应低于
   HBM 30–40%"假设不成立。这意味着市场把五家当一档周期成长股。

### 配置建议（存储）

| 选择 | 推荐 | 理由 |
|---|---|---|
| **MU 7%** | ✓（v2 已选） | 美国地缘溢价 + 标普流动性 |
| **SK Hynix 加 4–5%** | 推荐 | 基本面老大 + 估值最便宜，韩国折价反而创造 alpha 机会 |
| Samsung | 中性 | SOTP 便宜但治理拉胯 |
| SNDK | 已 demote ✓ | 与 MU 估值平价，MU 优先 |

**建议**：把 v2 的 "美股至上" 倾向松动 5%，加 SK Hynix（000660.KS）作为"基本面纯
HBM 暴露"。如果担心韩股流动性，可以用 EWY (iShares MSCI Korea ETF) 间接持仓 ——
但 EWY 含 Samsung + 其他 → 不够纯。

---

## 四、跨表横向观察

把三张表合起来看：

### 估值情绪图谱

```
                    Fwd PE
                       │
              60       │       LITE ●（光模块 narrative）
                       │  GEV ●
              50       │
                       │  GLW ●  VRT ●
              40       │
                       │       COHR ●  FN ●  ETN ●
              30       │             SU.PA ●
                       │  Samsung ●
              20       │
                       │  Generac ●
              10       │       SNDK ●  MU ●
                       │             SK Hynix ●
              5        │
                       └─────────────────────────────
                       0%       20%       40%      60%   Rev YoY
```

观察：

- **Rev YoY 与 PE 显著正相关**（市场为增速付溢价）
- **存储板块整体严重 underpriced**：60%+ YoY 增速、Fwd PE < 10
- **光模块板块严重 overpriced**：与电力链同样的增速但 PE 高 50%
- **VRT / GEV / GLW 介于两者之间**

### Cross-Theme 配置建议

当前 portfolio v2 暴露：

| 主题 | 当前权重 | 建议调整 |
|---|---:|---|
| AI 电力（VRT + GEV）| 26% | 拆出 5% 给 ETN（同主题分散） |
| 光模块（COHR）| 8% | 加 3–4% FN 作为代工补充 |
| 存储（MU）| 7% | 加 4–5% SK Hynix（000660.KS） |
| **AI 算力链合计** | **41%** | **目标 ≤ 50% 硬上限** |

---

## 五、可执行 TODO

- [ ] 用 fetch_quotes.py + 手动从 IR 拉数据填充本表的所有"_待填_"
- [ ] 周度刷新：每周一开盘前重跑一次
- [ ] 加第四张表 "**半导体设备**"（KLAC / LRCX / AMAT / 6857.T Advantest / 7735.T Screen / 8035.T TEL / 6146.T Disco）
- [ ] 加第五张表 "**量子**"（IBM 量子分部 / IONQ / RGTI / QBTS / Quantinuum 私）
- [ ] 加第六张表 "**机器人执行器**"（6324.T Harmonic / 6268.T Nabtesco / 6481.T THK / Hiwin 2049.TW / NSK 6471.T）

## 免责

数据基于公开来源 + 估算，需要 IR 数据校准。不构成投资建议。

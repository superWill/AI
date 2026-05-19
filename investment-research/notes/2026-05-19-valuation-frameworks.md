---
date: 2026-05-19
type: valuation-methodology
status: draft
applies_to: [IBM, MU, VRT, GEV, GLW]
---

# 估值方法多元化 —— 跳出单一 PE 视角

> 起因：研究 gap audit P0 第一条 —— 整组合都用 TTM / Forward PE / P/S，
> 对周期股（MU/SNDK）、平台型转型公司（IBM）、高 capex 增长股（VRT/GEV）都会失灵。
>
> 本文为 IBM / MU / VRT / GEV / GLW 五只核心持仓建立可重复的估值框架。
> 同时输出可直接挪到 `tickers/<TICKER>.md` "估值锚"章节的更新内容。

---

## 一、IBM —— Sum-of-the-Parts（SOTP）

### 为什么必须 SOTP

IBM 是异质业务组合，混合 PE 无意义：

- **咨询（Consulting）**：低增速、低毛利、人月密集 → 给 IT 服务 multiple
- **软件（Software）含 Red Hat**：高毛利、订阅经常性收入 → 给 SaaS multiple
- **基础设施（Infrastructure）含大型机**：周期性现金牛 → 给硬件 / 价值股 multiple
- **量子（Quantum）**：option value，不在当前 EPS 中

直接对 IBM 用 Forward PE 16.78 是把这四块"按等权混合"，不反映真实价值。

### 分部数据（2025 FY 口径）

> ⚠️ 数据需要从 IBM 2025 10-K Segment Information 章节精确填入；下表是模型骨架。

| 分部 | 营收 (2025E) | Op Income | Op Margin | EBITDA 估算 | YoY 增长 |
|---|---:|---:|---:|---:|---:|
| Software (含 Red Hat) | ~$27B | ~$8.5B | ~31% | ~$10B | 9–11% |
| Consulting | ~$22B | ~$2.4B | ~11% | ~$2.8B | 3–4% |
| Infrastructure | ~$13B | ~$2.5B | ~19% | ~$3.5B | 0–5%（周期） |
| Financing + Other | ~$2B | ~$0.3B | — | ~$0.4B | 持平 |
| **合计** | **~$64B** | **~$13.7B** | **~21%** | **~$16.7B** | — |

### SOTP 估值

| 分部 | 应用 multiple | 估值方法 | EV |
|---|---|---|---:|
| Software (Red Hat) | 18–22x EBITDA | 类比 Microsoft、SAP、ADBE 软件分部 | $180–220B |
| Consulting | 6–8x EBITDA | 类比 ACN、INFY | $17–22B |
| Infrastructure | 4–6x EBITDA | 类比 HPE、DELL | $14–21B |
| Financing | 净资产 / 1.0x book | — | $5B |
| **EV 合计（业务）** | — | — | **$216–268B** |
| 减：净债务（含养老金）| | ~$50B | |
| **股权价值（不含量子）** | | | **$166–218B** |
| 加：**量子 Option Value** | 见下 | | $20–80B |
| **股权价值（含量子）** | | | **$186–298B** |

当前市值 **$212B** 落在区间 $186–298B 的 **下沿偏中** — 软件分部以下基本被 price in，
**量子完全没 price in**。

### 量子 Option Value 测算

不能用 NPV，应该用期权框架（Black-Scholes-like 思路）：

- **底层资产**：2030 容错量子计算市场（TAM 估 $50–150B）
- **行权概率**：IBM 在超导路线上保持 1/3 市占 = 30–40%
- **行权价**：技术成熟 + 商业化 → 时间窗 2028–2032
- **波动率**：极高 → 期权时间价值大

简化测算：

```
量子 Option Value ≈ P(技术成功) × P(IBM 胜出) × 折现后市值贡献
                ≈ 50% × 30% × $300B（10 年后量子业务市值假设）/ 折现因子 1.5
                ≈ $30B
```

合理区间 **$20–80B**，取中位数 **$45B**。

### 单股估值结论（替代当前 ticker.md "估值锚"章节）

```
SOTP 公允股权价值：$186B（看跌）/ $250B（中性）/ $298B（看涨）
对应每股价格：$200 / $265 / $315
当前价 $225.74：定价在看跌中位数附近
量子 option value $45B = 每股 $48 = 21% 上行空间未被 price in
```

如果你信"量子真的会在 2030 成熟 + IBM 不会输给 Google/Microsoft"，
SOTP 公允 = **$265+**，当前价格隐含的概率约 30%。

### 反向证伪

- 如果量子优势演示在 2026 Q4 失败 → option value 砍到 $10B → 公允 $230
- 如果 Red Hat 增速跌到 5% 以下 → Software 估值砍 20% → 公允 $190
- 如果 Consulting 进入衰退（GenAI 替代）→ Consulting 估值砍 30% → 公允 $215

→ 安全边际 = $215（最坏情况下的"地板"）vs 当前价 $225 ≈ −4.5%

**这就是为什么 IBM 现在是"看跌情境内的安全边际"买入** — 但安全边际不大。

---

## 二、MU —— Mid-Cycle EPS + Supply-Demand

### 为什么必须用 mid-cycle 而非 Forward EPS

MU Forward PE 7.13 看起来便宜，但**前提是 FY26 EPS 兑现**。
内存周期 30 年来 5 次崩盘，每次峰值 EPS 在 12–24 个月内被腰斩。

正确估值框架：

```
Fair Value = Mid-Cycle EPS × Cycle-Adjusted Multiple
```

### Mid-Cycle EPS 测算

取过去 3 个完整周期峰值 EPS 平均的 50–60%：

| 周期 | 峰值年 | 峰值 EPS | 谷底年 | 谷底 EPS |
|---|---|---:|---|---:|
| 2014 周期 | FY15 | $2.47 | FY16 | $0.06 |
| 2017 周期 | FY18 | $11.95 | FY19 | $6.35 |
| 2021 周期 | FY22 | $8.35 | FY23 | $(4.45) |
| 2024 AI 周期 | FY26E | ~$15-22 | — | — |

**Mid-cycle EPS 估算**：

```
平均峰值 EPS（2018/22/26）= ($11.95 + $8.35 + $18) / 3 = ~$13
平均周期低点 EPS = ~$1.5（含一年大幅亏损）
真实 mid-cycle = (Peak + Trough) / 2 = ~$7
                                       或
真实 mid-cycle = Peak × 0.5 = ~$6.5
```

**但 AI 周期"半超级周期"假设**：

- 如果 HBM TAM 从 $35B → $100B（2028）且寡头格局维持
- 三家分（SK 50% / Samsung 25% / MU 25%）→ MU HBM 营收 $25B（vs FY26 ~$10B）
- 即使 DRAM 主业回到 mid-cycle，HBM 增量带来 +$2–3 EPS 的"floor lift"

**调整后 mid-cycle EPS = $9–10**

### Cycle-Adjusted Multiple

存储股历史 mid-cycle PE 通常 10–14x：

| 情境 | EPS | Multiple | 公允股价 |
|---|---:|---:|---:|
| 周期回到 2018/22 历史路径 | $7 | 10x | **$70** |
| AI 半超级周期成立 | $9–10 | 12x | **$108–120** |
| 完整科技股重估 | $10 | 18x | **$180** |
| Forward EPS 兑现且无回调 | $20 | 8x | $160 |

当前价 **$666**？？？数据有偏差，参考 MU.md 的 $666.59 应该是 split-adjusted 错误，
按官方 2025 财报 actual EPS 推算合理范围应该是百元数量级。
**TODO**：在本地用 yfinance 验证 MU 当前股价，更新此模型。

### Supply-Demand 平衡表（HBM 专项）

| 年份 | 全球 HBM 产能 (Gb wafer/m) | 需求估算 | 缺口 |
|---|---:|---:|---:|
| 2024 | ~280K | ~280K | 平衡 |
| 2025 | ~480K | ~520K | 短缺 7% |
| 2026 | ~720K | ~780K | 短缺 7% |
| 2027 | ~1,000K | ~1,000K | 平衡 |
| 2028 | ~1,300K | ~1,150K | **过剩 11%** |

> 数据是行业研究机构（TrendForce / DRAMeXchange）口径粗略估算。
> 需要在你的 dashboards 里加这张表的活数据 pipeline。

**关键判断**：2027–2028 供应可能赶上需求 → ASP 见顶 → MU EPS 见顶。
现在 7x Forward PE 看似便宜，但市场可能已预期 FY27 EPS 同比转负。

### 单股估值结论（替代当前 ticker.md "估值锚"章节）

```
Mid-cycle EPS：$9–10
公允 PE：12–14x
公允股价：$110–140（如按拆股后均价）
                  vs
完整科技股重估（PE 18x）：$180

仓位逻辑：
- 当前已涨过 mid-cycle 公允的中位数 → 不是"便宜"，是"市场已开始定价半超级周期"
- 安全边际取决于"半超级周期是否真的成立" = 取决于 HBM TAM 2028 是否破 $100B
- 一旦 2027 供需平衡反转 → ASP 下行 → 股价快速回到 mid-cycle 公允
```

### 反向证伪信号

- HBM3E 现货价 YoY 转负 → 第一警报
- TSMC HBM4E 逻辑芯片量产推迟到 2028+ → 良率问题暴露
- CXMT 在 HBM3 突破（国产替代提速）→ 长期格局裂变
- 出现"算法范式转移"信号（MoE / 线性注意力 / 3D DRAM 商用化）

---

## 三、Reverse DCF —— VRT / GEV / GLW

### 为什么用 Reverse DCF 而非 Forward DCF

Forward DCF 需要你预测 5–10 年增长率、margin、capex —— 输入误差 ±20% 会让估值 ±100%。
**Reverse DCF 反过来**：给定当前股价，市场隐含的 5/10 年增长率是多少？
如果隐含数字过于乐观或悲观，就有 alpha。

### 模型框架（通用）

```
Current Price = Σ [FCFt / (1+r)^t] + Terminal Value / (1+r)^N

简化：
FCFt = FCF0 × (1+g)^t
Terminal Value = FCF_N × (1+g_terminal) / (r - g_terminal)

输入：
- r = WACC = 9% (高 beta 股可上调到 11–12%)
- g_terminal = 3% (永续增长 = 名义 GDP)
- N = 10 年显式预测期
- FCF0 = TTM FCF
```

### VRT — Reverse DCF

**输入**：

- FCF0 (TTM) = ~$1.2B（待用 IR 数据精确填）
- 当前市值 = ~$137.9B
- WACC = 11%（beta 1.7 + 高估值）
- 永续增长 = 3%

**反推**：需要多大的 10 年 FCF CAGR 才能匹配当前估值？

```
$137.9B = $1.2B × Σ (1.X)^t / (1.11)^t [for t=1..10]
        + $1.2B × (1.X)^10 × 1.03 / (0.11 - 0.03) / 1.11^10

解出 X ≈ 27%/年
```

**市场隐含**：VRT 未来 10 年 FCF CAGR **~27%**。

**对照管理层指引**：VRT 2025 营收增长 30%+，但增长率不可能保持 10 年。
合理增长曲线：

- Y1–3：30% × 3 = +120% accumulated
- Y4–6：20% × 3 = +73%
- Y7–10：10% × 4 = +46%
- **混合 CAGR ≈ 19%**

市场隐含 27% vs 合理建模 19% → **VRT 已 price in 比合理乐观情景更激进的增长**。

**结论**：估值已透支 ~30%（即如果 thesis 完美兑现，公允估值 ~$96B）。

### GEV — Reverse DCF

**输入**：

- FCF0 (TTM) = ~$2B
- 当前市值 = $300.7B（v1 笔记勘误后）
- 但 backlog $300B+ 锁到 2030+

**反推**：

```
GEV 隐含 10 年 FCF CAGR ≈ 22–25%（粗略）
```

**对照**：

- backlog 显示未来 5 年营收锁定，但 backlog → FCF 转化率取决于：
  - 合同结构（fixed-price 还是 cost-plus）
  - Services & TSI 业务的高毛利占比
  - capex 投入（新工厂、电网设备扩产）

**关键缺数据**：GEV backlog 的 fixed-price / cost-plus 拆分。需要从最近一份 10-Q segment notes 抓。

### GLW — Reverse DCF

**输入**：

- FCF0 (TTM) = ~$1.5B（估算）
- 当前市值 = $156.3B
- 业务异质（display / optical / specialty / environmental / life sciences）

**SOTP 比 Reverse DCF 更合适**：

| 分部 | 营收占比 | 应用 multiple | 估值 |
|---|---:|---|---:|
| Display Tech | ~30% | EV/EBITDA 6x（成熟）| ~$25B |
| Optical Comm | ~30% | EV/EBITDA 15x（AI 受益）| ~$60B |
| Specialty Materials（Gorilla Glass）| ~20% | EV/EBITDA 10x | ~$25B |
| Environmental | ~10% | EV/EBITDA 8x | ~$10B |
| Life Sciences | ~10% | EV/EBITDA 12x | ~$15B |
| **合计 EV** | | | **~$135B** |
| 减：净债务 | | | ~$5B |
| **股权价值** | | | **~$130B** |

当前市值 $156B vs SOTP $130B → **溢价 20%** = 市场为"光纤本土化 + AI DC 拉动"叙事支付。

如果回到 SOTP 公允 $130B → 股价回调 ~17%。

这与 v2 portfolio 文档判断的 "GLW 安全边际明显压缩" 吻合。

### 单股估值更新建议

把每只 ticker.md 的"估值锚"章节扩展为：

```markdown
## 估值锚

### 单一指标快照
- TTM PE / Forward PE / P/S

### 多元化估值（每季度刷新）
- **EV/EBITDA**：X.X（同业中位数 Y.Y，溢价/折价 Z%）
- **FCF Yield**：X.X%（10Y 实际利率 Y.Y%，spread W%）
- **Reverse DCF 隐含 10y FCF CAGR**：X%（合理建模 Y%，差距 Z%）
- **SOTP（如适用）**：$XXX–YYY → 当前 vs SOTP 中位数 +/− Z%
- **Mid-cycle EPS（周期股）**：$X × PE Y = $Z 公允股价

### 估值得分
- 安全边际：最差情境地板 vs 当前价
- 期权价值：未 price in 的可选权（如 IBM 量子）
- 估值情绪：超买 / 中性 / 超卖
```

---

## 四、可执行 TODO

- [ ] **本周内**：把这份框架挪进 `tickers/IBM.md`、`tickers/MU.md`、`tickers/VRT.md`、
      `tickers/GEV.md`、`tickers/GLW.md` 的估值锚章节
- [ ] **下周**：从 10-K segment information 抓真实分部数据，更新 IBM SOTP / GLW SOTP
- [ ] **每月**：跑一次 reverse DCF，把市场隐含的增长率写入跟踪
- [ ] **数据 pipeline**：scripts 加一个 `fetch_fundamentals.py`，抓 yfinance `info` 里的
      EV、EBITDA、净债务、FCF，用于多元化估值

## 免责

估值模型基于公开数据 + 简化假设，不构成投资建议。

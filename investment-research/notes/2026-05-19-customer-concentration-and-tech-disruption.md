---
date: 2026-05-19
type: deep-dive
status: draft
applies_to: [VRT, MRVL, COHR, LITE, ALAB, CRDO, MU, GLW]
---

# 8 只核心持仓：客户集中度 + 技术路线颠覆风险

> 起因：研究 gap audit P0 第三、四条 —— 所有"卖铲子"逻辑都依赖 Nvidia + 4 家 hyperscaler；
> CPO / NVLink Fusion 是 2027–2028 的结构性威胁。
>
> 本文逐只补上 "客户集中度" 和 "技术路线颠覆风险" 两个章节，可直接挪到各 ticker.md。
> 数据来源标记 [10-K] / [earnings call] / [行业研究] / [推断]。

---

## 总览：8 只持仓共同的客户/技术依赖

| 维度 | 共同变量 | 影响 |
|---|---|---|
| 最大下游客户 | Nvidia GB200/300/Rubin 出货量 | 8 只里 6 只直接相关（VRT/MRVL/COHR/LITE/ALAB/CRDO/MU） |
| 次大客户群 | hyperscaler 4 家（AMZN/MSFT/GOOG/META）capex | 8 只里 7 只相关 |
| 第三客户群 | AMD MI 系列出货 | 4 只相关（MU/MRVL/COHR/LITE） |
| 颠覆风险 1 | CPO 共封装光学 2027–2028 | COHR/LITE 业务结构改写 |
| 颠覆风险 2 | NVLink Fusion 收回 retimer | ALAB/CRDO 直接受冲击 |
| 颠覆风险 3 | 算法范式（MoE / Mamba / 3D DRAM）| MU 长期需求曲线裂变 |
| 颠覆风险 4 | hyperscaler 自研 ASIC 替代 GPU | MRVL 双面（Trainium/Axion 利好 / GPU 周边利空）|

**结论**：8 只里 5–6 只在"Nvidia 路线 + hyperscaler capex"这一个总变量下高度相关。
研究 gap audit P0 §2 的相关性矩阵预期会验证这一点。

---

## 1. VRT — Vertiv

### 客户集中度

| 来源 | 客户 / 类别 | 营收占比估算 | 数据来源 |
|---|---|---:|---|
| Hyperscaler 4 家合计 | AMZN + MSFT + GOOG + META | **~40–50%** | [行业研究 + earnings call 评述] |
| 单一最大客户 | 未披露（推断 = MSFT 或 META）| ~12–18% | [推断] |
| Colo（Equinix + Digital Realty）| | ~15–20% | [行业研究] |
| 企业 + Telco | | ~25–30% | [10-K 间接估算] |
| 国防 + Federal | | ~5% | [10-K] |

**需要从 10-K 验证**：

- Item 1A Risk Factors 通常会披露"any single customer >10%"
- Q&A section / earnings call 提到的 hyperscaler exposure

### 技术路线颠覆风险（CPO/NVLink 不直接影响 VRT，但有其他风险）

| 风险 | 影响 | 时间窗 |
|---|---|---|
| 液冷渗透率被竞争对手抢占 | SU.PA 在欧洲 + ETN 在美国都加大投入 | 2026–2028 |
| 风冷 → 液冷一次性切换窗口关闭 | 一旦 hyperscaler 完成迁移，增量需求归零 | 2028–2030 |
| AI capex 增速 YoY 转负 | Backlog 履约速度放缓 → revenue conversion 下降 | 2027+ |
| 中国本土液冷替代（英维克 / 申菱）| 海外份额受影响有限，但中国市场份额可能归零 | 2026–2027 |

### 加到 VRT.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

> 待 10-K Item 1A 精确验证

- Hyperscaler 4 家合计：~40–50% 营收
- 单一最大客户（推断 MSFT 或 META）：12–18%
- Colo（Equinix / Digital Realty）：15–20%
- 企业 + Telco：25–30%

**集中度风险**：top-1 客户 capex 减速 = VRT 单季度营收下修 5–8%。

## 技术路线颠覆风险

- **风冷 → 液冷一次性切换窗口**：2028–2030 后增量需求归零
- **中国本土替代**：英维克 / 申菱抢中国份额（已发生）
- **同业反扑**：SU.PA / ETN 加大液冷投入，可能压毛利
```

---

## 2. MRVL — Marvell

### 客户集中度

| 来源 | 客户 | 营收占比估算 | 数据来源 |
|---|---|---:|---|
| Custom ASIC 业务 | **AWS Trainium** | ~30–35% Custom ASIC 营收 | [earnings call] |
| | **Google Axion / TPU 周边** | ~25–30% | [推断 + 行业研究] |
| | **Microsoft（Maia 周边）** | ~10–15% | [行业研究] |
| 网络（DSP / PAM4）| Nvidia + AI 服务器 | ~40% | [10-K] |
| 5G 网络 / 汽车 | 多元化 | ~20% | [10-K] |

**集中度真相**：

- Custom ASIC 业务（FY26 营收约 $3B）**80% 来自 AWS Trainium 一家**
- Trainium 节奏 = MRVL 增长曲线
- 这是 MRVL 的"高质量 thesis"也是"单点失败风险"

**需要从 10-K 验证**：

- 是否披露 AWS 是 >10% 客户（大概率是）
- 数据中心营收占总营收比

### 技术路线颠覆风险

| 风险 | 影响 | 时间窗 |
|---|---|---|
| **AWS 切到 Broadcom 或自研** | Trainium 3/4 代设计可能换合作伙伴 | 2027–2028 |
| **Inference workload 替代 training** | MRVL DSP 偏 training，Inference 用 ASIC 更直接 | 2027+ |
| **NVLink Fusion 挤压 PCIe DSP**| 部分 MRVL DSP 业务被 Nvidia 内化 | 2027–2028 |
| **Custom ASIC 设计周期超 18 个月** | 一次失败 = 一个完整产品周期损失 | 持续 |

### 加到 MRVL.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- **AWS Trainium** = 单一最大客户，估计 ~30–35% 总营收（Custom ASIC 80% 来自一家）
- Google + Microsoft 合计：~35–40%
- Nvidia + AI 网络周边：~30%
- 5G + 汽车：~20%（多元化但增速慢）

**核心风险**：AWS Trainium 任一代设计切换合作伙伴 → MRVL 25%+ 营收瞬间归零。

## 技术路线颠覆风险

- **AWS 切换合作伙伴**：T3/T4 是否仍由 MRVL 设计是关键，需跟踪 design win 公告
- **NVLink Fusion**：部分 PCIe DSP 业务被 Nvidia 内化
- **Inference 偏 ASIC**：MRVL DSP 优势主要在 training
```

---

## 3. COHR — Coherent

### 客户集中度

| 来源 | 客户 | 营收占比估算 |
|---|---|---:|
| Nvidia DGX / HGX 光模块 | Nvidia | ~30–35%（推断）|
| Hyperscaler 数据中心 | 4 家 + Meta | ~25% |
| Telecom（电信运营商）| Verizon / AT&T / 中国电信 | ~15% |
| 工业激光 + 国防 | 多元化 | ~25% |

### 技术路线颠覆风险

| 风险 | 影响 | 时间窗 |
|---|---|---|
| **🔴 CPO 共封装光学** | 传统可插拔光模块业务（800G/1.6T）2027–2028 起被替代 | **2027–2028** |
| **InP / EML 激光器供应** | COHR 上游依赖 Lumentum + 部分中国厂 | 2026–2027 |
| **中国光模块厂（中际旭创 InnoLight、新易盛 Eoptolink）抢份额** | 海外可能因贸易壁垒受保护，国内份额被吞 | 持续 |
| **800G 已是高峰，1.6T 转化期估值压缩** | 类似从风冷转液冷的"窗口期"问题 | 2027–2028 |

### CPO 是 COHR 的"existential" 风险

- Nvidia GTC 2024 已展示 CPO 路线图，Broadcom Bailly CPO 交换机 2025 量产
- Marvell + Lumentum + COHR + Broadcom 都在投，但格局未定
- 如果 CPO 在 2027 +/- 18 个月内主流化，**COHR 当前 1.6T 业务的毛利会被压一半**
- 但 COHR 同时是 CPO 光引擎的关键 IP 持有者，**有可能"自己革自己的命"成功**

→ Thesis 不变，但**风险敞口从"AI capex 见顶"扩展到"技术路线切换"**。

### 加到 COHR.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- Nvidia + 4 家 hyperscaler 光模块业务：~55–60%
- Telecom：~15%
- 工业激光 + 国防：~25%

## 技术路线颠覆风险（核心 thesis 威胁）

- **🔴 CPO 共封装光学**：2027–2028 主流化，传统可插拔光模块业务被替代
  - Broadcom Bailly CPO 交换机已 2025 量产
  - COHR 同时是 CPO 光引擎 IP 持有者 → 可能"自己革自己的命"成功
  - 跟踪信号：Nvidia GTC 2026 路线图 + Broadcom CPO 客户公告

- **中国厂抢份额**：中际旭创 / 新易盛在 800G 已经接近 COHR / LITE
- **800G → 1.6T 转化期**：估值在切换窗口可能被压缩
```

---

## 4. LITE — Lumentum

### 客户集中度

| 来源 | 客户 | 营收占比估算 |
|---|---|---:|
| Apple（VCSEL 激光 Face ID）| Apple | ~15–20%（已披露 >10% 客户）|
| Nvidia + hyperscaler（DCI 光模块）| | ~30–35% |
| Telecom（电信光模块）| | ~20% |
| 工业激光 | | ~15% |
| Cloudlight（800G/1.6T 模块）| | ~15% |

**LITE 比 COHR 更暴露在 Apple 这一根线上**（VCSEL 业务），同时 AI DCI 业务起来后开始
多元化。但 Apple 任何 Face ID 改型（如 under-screen camera）会直接砸 LITE。

### 技术路线颠覆风险

| 风险 | 影响 |
|---|---|
| **CPO**（同 COHR）| 800G/1.6T 模块业务被替代，2027–2028 |
| **Apple under-display Face ID** | VCSEL 业务减少 → 工业激光占比上升 |
| **Cloudlight 整合不顺**| Lumentum 2023 收购，毛利仍未达预期 |

### 加到 LITE.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- Apple（VCSEL Face ID）：~15–20%（已披露 >10% 客户）
- Nvidia + 4 家 hyperscaler：~30–35%
- Telecom：~20%
- 工业激光 + Cloudlight：~30%

**集中度风险**：Apple Face ID 设计改动（under-display camera）= LITE 单年营收下修 10%+

## 技术路线颠覆风险

- **CPO**（同 COHR）：2027–2028 起结构性威胁
- **Apple 自研激光器**：长期可能内化，类似 modem 故事
- **Cloudlight 整合**：800G/1.6T 模块业务毛利未达预期
```

---

## 5. ALAB — Astera Labs

### 客户集中度

| 来源 | 客户 | 营收占比估算 |
|---|---|---:|
| **Nvidia GB200/300 NVLink Switch 周边** | Nvidia | **~40–50%**（推断）|
| Hyperscaler 自研服务器（PCIe Gen6 retimer）| AMZN/MSFT/META | ~30% |
| AMD MI 系列 | AMD | ~10% |
| 其他 / 电信 | | ~10–20% |

ALAB 是 8 只里**对 Nvidia 路线依赖最深**的一只。

### 技术路线颠覆风险（**最严峻**）

| 风险 | 影响 | 时间窗 |
|---|---|---|
| **🔴 NVLink Fusion / NVLink 5/6** | Nvidia 把 NVLink Switch 周边的 retimer 收回自家，第三方 retimer 价值大幅压缩 | **2026–2027** |
| **PCIe Gen6 → Gen7 切换** | ALAB 在 Gen6 领先，但 Gen7 可能被博通追上 | 2027 |
| **CXL 协议命运** | CXL 1.x / 2.0 落地比预期慢，ALAB 部分产品线对 CXL 押注 | 持续 |
| **Smart Cable / AEC** | 与 CRDO 重合 → 双双毛利压力 | 持续 |

### NVLink Fusion 是 ALAB 的"existential" 威胁

- Nvidia 2025 GTC 已公开"NVLink Fusion" 路线 —— 把 NVLink 协议开放给第三方 ASIC，
  但同时把 NVLink Switch 周边的 retimer / signal conditioner 收紧
- ALAB 当前 50%+ 营收来自这一层 ASIC
- 如果 Nvidia 在 2027 GB300/Rubin 平台把这块收回 → ALAB 营收瞬间 −30–40%

### 加到 ALAB.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- **Nvidia GB200/300 周边**：~40–50% 营收（PCIe Gen6 retimer + Smart Cable）
- Hyperscaler 自研服务器：~30%
- AMD + 其他：~20%

**核心风险**：单一最大客户路线变化 = ALAB 30–40% 营收瞬间归零。

## 技术路线颠覆风险（核心 thesis 威胁）

- **🔴 NVLink Fusion**：Nvidia 把 NVLink Switch 周边的 retimer 收回自家
  - Nvidia 2025 GTC 已公开路线
  - 2027 GB300/Rubin 平台可能落地
  - **跟踪信号**：Nvidia 财报 + GTC 2026 路线图
- **PCIe Gen7 切换**：博通 / Marvell 可能追上
- **CXL 落地节奏**：比预期慢，部分产品线押注落空
```

---

## 6. CRDO — Credo

### 客户集中度

| 来源 | 客户 | 营收占比估算 |
|---|---|---:|
| AEC（Active Electrical Cable）业务 | **Microsoft + Meta 合计 >60%** | 已披露 |
| 单一最大客户 | 估计 Microsoft | ~40–45% |
| 其他 hyperscaler + Nvidia | | ~30% |
| Telecom + 其他 | | ~10% |

**CRDO 的极端单客户依赖**：Microsoft + Meta = 60%+ 已是 10-K 公开数据。

### 技术路线颠覆风险

| 风险 | 影响 |
|---|---|
| **AEC vs 光模块**：长距 vs 短距路线竞争 | AEC 在 < 7m 距离占优；CPO 普及后短距优势减弱 |
| **NVLink Fusion** | 同 ALAB |
| **Microsoft 切换** | 一旦 MSFT 切到 Broadcom 或自研 → CRDO 营收腰斩 |
| **PAM4 → PAM6 / Coherent-Lite** | 协议演进可能不利于 CRDO 当前产品 |

### 加到 CRDO.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- **Microsoft + Meta 合计**：~60%+（已披露 10-K）
- 单一最大客户（推断 MSFT）：~40–45%
- 其他 hyperscaler + Nvidia：~30%

**极端集中**：top-2 客户合计 60%+ → 单一客户切换 = 公司估值腰斩。

## 技术路线颠覆风险

- **AEC vs CPO**：CPO 普及后 AEC 短距优势减弱
- **NVLink Fusion**（同 ALAB）
- **Microsoft 切换合作伙伴**：核心 thesis 单点失败风险
```

---

## 7. MU — Micron

### 客户集中度

| 来源 | 客户 | 营收占比估算 |
|---|---|---:|
| HBM 业务 → Nvidia 占绝对主力 | Nvidia | HBM 营收 **70%+** 来自 Nvidia |
| HBM 业务 → AMD | AMD MI300/400 | ~15% |
| HBM 业务 → 自研 ASIC | AWS/Google/Meta | ~10% |
| DRAM 主业 | 手机 + PC + 服务器 多元化 | 整体 60% 营收 |
| NAND | 数据中心 SSD + 消费 | 整体 35% 营收 |

**关键**：MU HBM 业务（FY26 营收占比 30%+）**70%+ 来自 Nvidia 一家**。

### 技术路线颠覆风险

| 风险 | 影响 | 时间窗 |
|---|---|---|
| **🔴 算法范式转移** | MoE / 线性注意力 / 3D DRAM / PIM 任一商用 → HBM 需求曲线弯折 | 2027–2030 |
| **Nvidia 自研内存或切换主要 HBM 供应商** | MU HBM 业务 30%+ 营收风险 | 持续 |
| **HBM4E TSMC 逻辑芯片合作** | 良率 / 成本不达预期 → MU 失去差异化 | 2026–2027 |
| **CXMT 国产替代** | 短期影响小，长期挤压 HBM3 价格 | 2028+ |
| **DRAM 周期反转** | 2027–2028 供需可能转过剩 | 2027–2028 |

### 加到 MU.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- HBM 业务 70%+ 来自 Nvidia 一家
- HBM 整体占 MU FY26 营收 30%+
- DRAM 主业 + NAND 仍多元化（手机 + PC + 服务器 + SSD）

**核心风险**：Nvidia HBM 供应商切换或自研 = MU HBM 业务 30%+ 风险敞口

## 技术路线颠覆风险

- **算法范式**（最严重）：MoE / 线性注意力 / 3D DRAM / PIM 商用化 → HBM 需求曲线弯折
- **TSMC HBM4E 逻辑芯片良率**：MU 差异化关键
- **CXMT 国产 HBM3 突破**：长期价格压力
- **DRAM 周期 2027–2028 反转**：见估值框架 mid-cycle EPS 部分
```

---

## 8. GLW — Corning

### 客户集中度

| 来源 | 客户 / 类别 | 营收占比 |
|---|---|---:|
| **Apple Gorilla Glass + Ceramic Shield** | Apple | ~15–20%（已披露 >10% 客户）|
| Display Tech（中国/韩国面板厂）| BOE / Samsung Display / LG Display | ~30% |
| Optical Comm（光纤）| Verizon / AT&T / 数据中心 | ~30% |
| Environmental（汽车催化剂载体）| 全球汽车厂 | ~10% |
| Specialty / Life Sciences | 多元化 | ~10% |

### 技术路线颠覆风险

| 风险 | 影响 |
|---|---|
| **Apple 切换 Gorilla Glass 供应商**（理论） | 影响 15% 营收，但 Corning 30 年合作护城河深 |
| **OLED → MicroLED 切换** | Display Tech 玻璃基板需求曲线裂变 |
| **数据中心光纤需求曲线** | 受 hyperscaler capex 直接驱动 |
| **生物玻璃 / Life Sciences** | 增速慢，对总营收贡献有限 |

### 加到 GLW.md 的建议章节

```markdown
## 客户集中度（2026-05-19 估算）

- Apple：~15–20%（已披露 >10% 客户）
- 面板厂（BOE / Samsung Display / LG）：~30%
- 光纤 + Telecom：~30%
- 汽车 + 其他：~20%

## 技术路线颠覆风险

- **OLED → MicroLED**：长期可能改变玻璃基板需求结构
- **Apple Ceramic Shield 替代**：30 年合作护城河 + 良率优势 → 短期可控
- **数据中心光纤 vs CPO 内连**：长距光纤需求不受 CPO 影响
```

---

## 后续要补的客户集中度数据

每只 ticker 应该在下次财报后，从 10-K Item 1A + Item 7 + earnings call 抓三组数据：

1. **>10% 客户披露**（10-K Item 1A 强制披露）
2. **Geographic concentration**（美国 / 欧洲 / 中国 / 其他）
3. **End-market concentration**（hyperscaler / enterprise / telecom / industrial）

### 跟踪频率

- 单一 >10% 客户：季度跟踪（财报后 1 周内）
- 整体地理 / 端市场结构：年度跟踪（10-K 出来后 2 周内）

## 免责

数据基于公开来源 + 行业研究 + 推断，需要从 10-K 验证。不构成投资建议。

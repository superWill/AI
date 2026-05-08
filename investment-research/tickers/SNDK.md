---
ticker: SNDK
name: SanDisk
sector: NAND Flash Memory
layer: Layer 2 — NAND 存储
position_type: core
status: watching
last_updated: 2026-05-07
data_source: scripts/fetch_quotes.py snapshot 2026-05-07
---

# SanDisk (SNDK)

## 一句话定位

2025 年从 Western Digital 拆分独立的纯 NAND 玩家。AI 推理 KV cache offload 到 NAND 是新趋势。

## 关键数据（基准日 2026-05-07，yfinance 实时）

| 指标 | 数据 |
|---|---|
| 股价 | **$1,409.98** |
| 市值 | **$208.8B** |
| TTM PE | 48.07 |
| Forward PE | **8.39** |
| Forward P/S | 15.84 |
| 52 周区间 | $33.13 → $1,439.70 |
| 50 日均线 | $805.24 |
| 200 日均线 | $372.73 |

> **⚠️ 笔记勘误**：v1 笔记写"$913 / $80–95B"已严重过期——今日 **$1,410 / $209B**，市值 **2.5×**。一年区间 $33 → $1,440 = **+4,250%**（接近 52 周高点）。
>
> 关键观察：**Forward PE 8.39 接近 MU 的 7.13**——NAND 与 HBM 在估值上几乎平价，意味着市场把 SanDisk 也当成"周期成长股"在重估。这与笔记里"Forward PE 应低于 MU 同期 30–40%"的预设**已被市场反向证伪**。
>
> 也因此 SNDK 已**远超 $200B**，技术上已超出"$10–200B 推荐区间"。

## 护城河类型

**寡头格局 + 工艺壁垒**：

- 3D NAND 全球只有 6 家：SanDisk、SK Hynix、Samsung、Micron、Kioxia、YMTC
- 工艺壁垒虽不如 HBM，但每一代堆叠层数攀升（200+ 层）门槛仍高
- 拆分后专注度提升，决策更敏捷

## 短期增量（3–5 年）

- QLC NAND 在 AI 推理中加速渗透（每比特存储更便宜）
- 企业级 SSD 受益数据中心扩容
- KV cache offload 到 NAND：把 LLM 推理中昂贵的 HBM 容量需求往 NAND 下沉

## 长期增量（10–20 年）

- 每台机器人需本地 NAND 存储模型权重（50–200GB）
- 10B × 100GB = **1000 EB 累计需求**
- 但单台用量小 + NAND 单价持续下行 → 收入弹性不如 HBM

## 风险

- **周期性比 HBM 更剧烈**：NAND 价格历史上波动幅度更大
- **YMTC 国产化**：长江存储在中低端持续追赶
- **拆分后整合不确定性**：销售渠道、ERP、采购关系都在重建
- **HBM 替代部分 NAND 用途**：在某些场景挤压 NAND 角色

## 估值锚

- 与 MU 类比：MU Forward PE 7.13、SNDK 8.39 —— **几乎平价**（笔记预期的 30–40% 折扣未实现）
- 暗示市场把 NAND 寡头（SK Hynix / Samsung / Micron / SanDisk / Kioxia）整体当作"周期成长股"重估
- 估值修复空间：Forward PE 8.39 vs 半导体行业中位数 ~34x，理论上仍有 **3–4×**——但这取决于 NAND 周期能否持续 2–3 年不回调

## 退出条件

- **触发减仓**：NAND ASP 连续两季 YoY 下滑
- **触发卖出**：YMTC 高端突破 / 产能过剩信号
- **再加码**：KV cache offload 成主流推理架构

## 跟踪信号

- NAND 现货价格（DRAMeXchange）
- 数据中心 SSD 出货量
- 企业级 NAND 占比（毛利率指引）
- Kioxia / YMTC 产能扩张

## 参考

- 主题笔记：[2026-05 AI/机器人/量子产业链](../notes/2026-05-ai-robotics-quantum-supply-chain-v1.md#5.1)

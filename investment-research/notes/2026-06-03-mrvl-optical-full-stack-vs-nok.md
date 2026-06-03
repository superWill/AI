# MRVL 光通信全栈 + 黄仁勋催化 vs NOK

> 起因：2026-06-02 MRVL 单日 +41.84%，市场称其为"光通信里的全能型"。本笔记拆解涨因、"全能"的真实含义，并对比 NOK 的光网络定位。
> 关联 ticker：[MRVL](../tickers/MRVL.md) · [COHR](../tickers/COHR.md) · [LITE](../tickers/LITE.md) · [AVGO](../tickers/AVGO.md) · [GLW](../tickers/GLW.md)

## 核心结论

- MRVL +40% **不是业绩驱动，是英伟达背书 + 订单绑定**：黄仁勋在 COMPUTEX 称其为"下一个万亿美元公司"并宣布约 20 亿美元合作。
- 真正支撑这个故事的，是 MRVL **从电到光踩满整条光互联链**——这才是"全能"的含义，别人大多只占一两环。
- MRVL 与 NOK **同在"光"，但不是同一战场**：MRVL 玩机房内 GPU 集群高速互联（短链、走量、贴 AI 算力）；NOK 玩机房间/城域长途相干传输（慢变量、偏运营商、2027 才量产）。

一句话：

`MRVL = 算力内部的神经；NOK = 机房之间的血管。要 AI 数据中心爆发的直接弹性，是 MRVL。`

## 一、6/2 +41.84% 的涨因

催化剂是英伟达，不是财报：

- 6/2 台北 COMPUTEX，黄仁勋与 MRVL CEO Matt Murphy 同台，直接称 MRVL 是"下一个万亿美元公司"，并宣布约 **$2B 合作**。当天 **+41.84%**。
- 基本面是配角但给了底气：
  - Q1 营收 **+28% 到 $2.4B**
  - 数据中心已占总营收 **75%**（两年前 50%）
  - Rule-of-40 ≈ 69%，YTD ≈ +130%

> 结论：**光通信全栈能力是这个估值故事能成立的底层逻辑，英伟达背书是点火器。**

## 二、为什么"全能"——踩满整条光互联链

光模块/光互联分工极细，大多数公司只占一两环。MRVL 罕见地几乎全踩到：

| 环节 | MRVL 的料 | 对手格局 |
|---|---|---|
| 电信号处理 DSP | Ara / Alaska / Nova，1.6T 全系 | AVGO 也强 |
| SerDes / 以太网 PHY | 自家平台（Inphi IP） | — |
| 交换芯片 | 有 | AVGO 占高端 >80% |
| 驱动器 + TIA | LPO 驱动 + TIA 芯片组 | LITE/COHR 偏器件 |
| 硅光引擎 | Silicon Photonics Light Engine | COHR / Intel |
| CPO / 光互联 | 2025-12 收购 Celestial AI（最高 $5.5B） | NVDA / AVGO 各搞各的 |
| 链路遥测 | RELIANT 平台 | — |

对手是"单点强、不全"：

- **LITE（Lumentum）**：激光/EML——目前唯一量产 **200G/lane EML**，强但单点。
- **COHR（Coherent）**：激光 + 硅光 + 收发器 + 光开关，宽，但缺高端 DSP/交换这个电侧大脑。
- **AVGO（Broadcom）**：交换 + DSP 电侧霸主，但器件侧不如 MRVL 全。

> "全能"的真正含义：别人卖零件，MRVL 能从 DSP、驱动、TIA、硅光引擎到 LPO/CPO **端到端打包**，并随 AI 数据中心从可插拔光模块演进到 CPO。

## 三、NOK（诺基亚）——同在"光"，不同战场

容易被放一起，但定位差很远：

- 诺基亚的光是**电信/传输级相干光**：校园 DCI、城域、长途、海缆。
- 靠 **2025 收购 Infinera** 补齐光网络团队和 InP 产能（San Jose 6 寸 InP 厂 + 宾州先进封装）。
- OFC 2026 发 4 颗新相干 DSP + InP/硅光前端，主打 AI 时代**机房之间/跨园区** scale-across 连接，号称 TCO 降最高 70%。
- **节奏慢**：2027 年中送样、下半年量产。

## 四、定位对照

| 维度 | MRVL | NOK |
|---|---|---|
| 战场 | 机柜内 / 数据中心内互联 | 机房之间 / 城域长途传输 |
| 产品 | 800G/1.6T 光模块、CPO、DSP | 相干 DSP + 光线路系统 |
| 链路特性 | 短链、走量、贴 GPU 集群 | 长链、相干、偏运营商生意 |
| 与 AI 算力关系 | 直接弹性 | 间接（把机房连成一片的管道） |
| 兑现节奏 | 当下放量 | 2027 才量产，慢变量 |
| 角色比喻 | 算力内部的神经 | 机房之间的血管 |

> 两者不是替代，是 AI 网络的不同层。

## 五、对持仓的含义

- MRVL 的弹性和确定性当前都更高，但**风险也写在脸上**：估值已 price in 高增长（见 [MRVL ticker](../tickers/MRVL.md) 退出条件），英伟达绑定既是护城河也是单一依赖；CPO 长期可能重构 DSP 市场结构（MRVL 用 Celestial AI 对冲）。
- NOK 更像传输侧的慢变量，逻辑成立但兑现要等 2027，不适合作为"AI 数据中心爆发"的直接表达。

## 跟踪信号

- MRVL：$2B 合作落地细节、Q2 数据中心营收占比与增速、1.6T 出货节奏（COHR/LITE 联动）、Celestial AI/CPO 进展。
- NOK：Infinera 整合后的送样/量产时间是否按 2027 兑现、相干 DSP 客户公告。

## 参考

- [Invezz — Huang: Marvell could reach $1T](https://invezz.com/news/2026/06/02/marvell-stock-could-soar-410-and-reach-a-1-trillion-valuation-jensen-huang-says/)
- [GuruFocus — MRVL surges on Nvidia CEO remarks](https://www.gurufocus.com/news/8895889/marvell-mrvl-stock-surges-over-27-following-nvidia-ceos-remarks)
- [Marvell — 1.6T Optical DSP Platform Portfolio](https://www.marvell.com/company/newsroom/marvell-1-6t-optical-dsp-ai-data-center-connectivity.html)
- [Marvell — 1.6 Tbps LPO Chipset](https://www.marvell.com/company/newsroom/marvell-introduces-1-6-tbps-lpo-chipset.html)
- [PhotonCap — Marvell confirms AI optical signal（Celestial AI / Lumentum / Coherent）](https://photoncap.net/p/the-third-signal-in-may-marvell-confirms)
- [Nokia — completes Infinera acquisition](https://www.nokia.com/newsroom/nokia-completes-acquisition-of-infinera-to-create-innovation-powerhouse-in-optical-networks-with-the-scale-to-power-the-data-center-revolution/)
- [Nokia — application-optimized optical solutions（OFC 2026）](https://www.nokia.com/newsroom/nokia-launches-suite-of-applicationoptimized-optical-solutions-for-ai-era-networks/)
- [Lightreading — Nokia rebuilds its optical engine](https://www.lightreading.com/optical-networking/nokia-rebuilds-its-optical-engine-one-building-block-at-a-time)

# 具身智能的"不可或缺"卡点：脑 - 关节 - 磁材

> 起因：把"不可或缺=卡脖子点"框架套到具身智能（人形机器人）。结论：卡点是 **大脑（Nvidia）+ 关节（谐波减速器/滚柱丝杠）+ 磁材（稀土永磁）** 三道关。但与半导体收税口有本质区别，必须先讲清楚。
> 关联 ticker：[NVDA](../tickers/NVDA.md) · [6324.T](../tickers/6324.T.md) · [MP](../tickers/MP.md) · [MRVL](../tickers/MRVL.md)
> 承接：[硅基消费 × 碳基娱乐](2026-06-19-silicon-consumption-carbon-entertainment.md) · [EDA 双寡头](2026-06-19-eda-duopoly-snps-vs-cdns.md)

## 0. 与半导体收税口的本质区别（先读这条）

半导体的收税口（[TSM](../tickers/TSM.md)/[ASML](../tickers/ASML.md)）是**已验证、有现金流的垄断**——当下就在收过路费。
具身智能现在**还没量产**——"供应商生态尚未为大规模生产建好"（McKinsey）。

> **所以这里的"不可或缺"是对未来瓶颈的前瞻押注，不是当下收钱的收费站。确定性 < TSMC/ASML，早期性与赔率 > 它们。别用同一个确定性标准。**

摩根士丹利"Humanoid 100"框架把链条分三段：**大脑（Nvidia）/ 身体（中国主导 + 日本零部件）/ 整合（Tesla）**。卡点都在前两段。

## 1. 大脑 / 算力 —— Nvidia（NVDA）✅最像"安卓"的平台垄断

- **Jetson Thor**（算力，2070 FP4 TFLOPS/128GB）+ **GR00T**（基础模型）+ **Isaac Sim/Omniverse**（仿真/合成数据）三件套。
- 2026/5/31 发开源人形参考设计（Unitree H2 底盘 + Sharpa 触觉手 + Jetson Thor）。
- **为什么不可或缺**：几乎每家机器人公司（Figure、1X、波士顿动力…）都在 Isaac 上开发；仿真+合成数据训练是别人难复制的护城河。TechCrunch："英伟达想做通用机器人的安卓。"
- **catch**：$5 万亿巨头，机器人占比极小——是**机器人的免费看涨期权，不是纯暴露**。详见 [NVDA 卡](../tickers/NVDA.md)。

### 1.1 ⭐ 修正（2026-08-09）：「大脑」不是一个卡点，是两个——Google 被本篇漏掉了

`[KNOWN via web, MED-HIGH，多源一致]`

**本篇原稿把「大脑」层整个判给 NVDA，通篇零次提及 Google。这是漏项，不是判断分歧。** 准确的切分是**两个不同性质的卡点**：

| | **NVIDIA** | **Google** |
|---|---|---|
| 卡什么 | **算力 + 仿真工具链**（Jetson Thor / Isaac Sim / Omniverse） | **最强的 VLA 模型本身** |
| 基础模型 | **GR00T N1 开源**，N1.7 商业授权 | **Gemini Robotics 2 闭源**，仅早期合作伙伴 |
| 硬件 | 自产（Jetson Thor） | **不造**，载体是 Apptronik Apollo 2 |
| 商业模式 | **卖铲子 / 做安卓**——收所有人的过路费 | **垂直整合自用**（Waymo / Intrinsic / Cloud） |
| 变现现状 | 数据中心主业已在收钱，机器人是增量 | 除 Waymo 外**收入 ≈ 0** |

**Google 的四条腿（2026-08 现状）：**

1. **Gemini Robotics 2（2026-07-30 发布）** — 三件套：**Gemini Robotics 2**（VLA，视觉语言转动作）+ **ER 2**（具身推理/多步规划）+ **On-Device 2**（端侧）。首次做到**全身控制**（此前仅上半身操作），扩展到行走/弯腰/平衡/穿越杂乱空间。**最硬的指标：端侧模型用 <200 个演示样本、数小时内适配全新机器人硬件。**
2. **Intrinsic**（2026-02 从 Other Bets 并入 Google）— 工业机器人软件；**2025-10 与富士康合资**做电子制造全厂自动化。**Google 具身线唯一有明确 B 端路径的一块。**
3. **Waymo** — **规模最大的具身 AI 实盘**：11 个美国城市（年内新增 6 个）、**每周 >50 万次全自动驾驶行程**；新 Ojai robotaxi 把 Gemini 做成车内界面。
4. **Apptronik 合作**（2024-12 起）— Google 不造硬件，只出大脑。

**判定与 catch：**

- **不改变本篇的可投结论**。Google 的具身线**当期收入 ≈ 0**（Waymo 仍在 Other Bets 亏损），性质与 NVDA 同为「免费看涨期权」，且 GOOGL 的分母比 NVDA 更大——**稀释更严重，不是更纯的暴露**。
- **⚠️ 生态位比模型能力更难撼动**：NVIDIA 开源 + 全栈 + 几乎所有机器人公司都在 Isaac 上开发。**「模型最强」≠「会赢」**，Google 手里真正稀缺的是 **Waymo 的 50 万次/周真实数据**，不是参数。
- **🔴 人才风险刚好打在这条腿上，时间点极难看**：**Gemini Robotics 2 发布于 7/30，8/5 就出走四人**——其中 **Oriol Vinyals 是 Gemini 团队 co-lead**、Jeff Dean 首席科学家、Sanjay Ghemawat、Quoc Le，同期 Hassabis 卸任 DeepMind 日常管理。**发布后第六天核心班子解体**，后续必须盯（详见 [GOOGL 卡](../tickers/GOOGL.md) 2026-08-09 节）。
- **对 §4「灵巧手格局未定」的补充**：Gemini Robotics 2 的全身控制若成立，**卡点会从机械自由度部分转移到控制模型**——这会削弱"灵巧手硬件是价值高地"的假设。**尚未验证，列为观察项。**

## 2. 执行器 / 关节 —— 谐波减速器（[6324.T](../tickers/6324.T.md)）+ 行星滚柱丝杠 ✅最硬的物理卡点

- **谐波减速器**：全行业最清晰的执行器瓶颈。Harmonic Drive（6324.T，市占 **70%+**）、Nabtesco 主导。精密+资本密集+认证周期长，**扩产结构性困难**（不像电子能快速加产能）。
- **行星滚柱丝杠**：比减速器**更急的卡点**——SKF + 少数亚洲专家，供应窄、交期长、几乎无替代，用于人形四肢的直线执行器（Tesla Optimus 走这条路线）。
- **为什么不可或缺**：一台人形要 20–40 个执行器，每个都要减速器或丝杠，供给短期补不上。物理/精密工艺壁垒。
- **catch**：① 被**中国厂（绿的谐波/Leaderdrive 等）追赶**——和 EUV"无挑战者"不同，机械护城河会被侵蚀；② 量产没起来；③ **路线风险**：若滚柱丝杠（Tesla 路线）成主流，谐波减速器需求可能减 30–50%（但 Figure/1X/波士顿动力仍用谐波）。详见 [6324.T 卡](../tickers/6324.T.md)。

## 3. 磁材 / 肌肉原料 —— MP Materials（[MP](../tickers/MP.md)）+ Lynas ✅地缘卡点

- 每个电机都要 NdFeB 永磁，一台人形 **2–3kg，是 EV 的 2–3 倍**。中国控制 **~90% 精炼/加工**。
- ex-China 的稀缺供给 = **MP（DoD 持股+价格保底）、Lynas、USA Rare Earth**。MS 指出名单里 4 家稀土股全是表现最好的一档。
- **为什么不可或缺**：**材料级 + 地缘级**双卡点——绕不开磁材，又绕不开"非中国来源"的战略需求。
- **catch**：MP 仍亏损（TTM EPS -$0.42），靠 DoD 保底+磁材放量转盈；地缘溢价若中国放松管制会回吐。详见 [MP 卡](../tickers/MP.md)。

## 4. 灵巧手 / 触觉 —— 价值最大（31% BOM）但格局未定 ⚠️

- 灵巧手是单一最大成本项（占 BOM **31%**），但自由度、传动、触觉传感路线**还在剧烈变化**。
- **暂无清晰的公开卡脖子点**——价值高地，但赢家未知，**还不能算稳定的"不可或缺"**。要盯、但不是现在能押。

## 5. 结论：真正"不可或缺"的几个

| 卡点层 | 公司 | 不可或缺度 | 最大 catch |
|---|---|---|---|
| 大脑·算力/工具链 | **[NVDA](../tickers/NVDA.md)** | 平台级垄断（安卓化） | 巨头，机器人是免费期权 |
| 大脑·模型（**2026-08 补**） | **[GOOGL](../tickers/GOOGL.md)** | 最强 VLA 且闭源，但**生态位弱于 NVDA** | 分母更大、当期收入≈0、核心团队 8/5 出走 |
| 执行器（旋转） | **[6324.T](../tickers/6324.T.md)** | 物理瓶颈、扩产难 | 中国厂追赶 + 路线风险 + 未量产 |
| 执行器（直线） | 行星滚柱丝杠（SKF/亚洲专家） | 最急瓶颈 | 无干净纯公开标的 |
| 磁材 | **[MP](../tickers/MP.md)** + Lynas | 材料+地缘双卡点 | 仍亏损 + 商品/地缘价格波动 |
| 灵巧手 | （未定） | 价值最大但格局未定 | 赢家未知，不能押 |

**最干净 + 可投 + 库里已覆盖的三个**：**NVDA（脑）+ 6324.T（关节）+ MP（磁材）**——具身智能"不可或缺"最纯的三角表达。

> **一句话**：具身智能的不可或缺 = Nvidia（脑）+ 谐波减速器/滚柱丝杠（关节）+ 稀土磁材（肌肉原料）三道关。但与半导体收税口的本质差别是：它们要么是被稀释的巨头（NVDA），要么是会被中国追赶、且尚未量产的机械/材料卡点。**这是押"未来瓶颈兑现"，不是收"当下的过路费"。**

## 6. 跟踪信号

- NVDA：Jetson Thor/GR00T 在人形量产中的采用、数据中心增速（主业）。
- **GOOGL（2026-08 新增）**：① Gemini Robotics 2 的 VLA/端侧模型**是否从"早期合作伙伴"转为公开可用**（转公开=抢生态位，不转=只自用）；② **Intrinsic × 富士康合资**是否产出可计收入的部署；③ **Waymo 周行程数**（当前 >50 万）；④ **8/5 出走后 DeepMind 机器人团队是否继续出人**。
- 6324.T：机器人客户订单 YoY、FY27 利润反转兑现、中国厂高端突破、Tesla 执行器选型（谐波 vs 滚柱丝杠）。
- MP：磁材业务转盈、DoD 合同、中国稀土出口管制变动。
- 共享：人形量产 first wave（Tesla/Figure/1X/Unitree）是否在 2026–2027 兑现——这是所有卡点变现的总开关。

## 7. 参考

- [Morgan Stanley — The Humanoid 100（价值链地图）](https://advisor.morganstanley.com/john.howard/documents/field/j/jo/john-howard/The_Humanoid_100_-_Mapping_the_Humanoid_Robot_Value_Chain.pdf)
- [McKinsey — 人形供应链瓶颈](https://www.mckinsey.com/industries/industrials/our-insights/turning-humanoid-supply-chain-constraints-into-billion-dollar-wins)
- [TechCrunch — 英伟达想做通用机器人的安卓](https://techcrunch.com/2026/01/05/nvidia-wants-to-be-the-android-of-generalist-robotics/)
- [Oceanwall — 机器人与稀土磁材瓶颈](https://oceanwall.com/wp-content/uploads/2025/10/Robotics-Market-and-Rare-Earth-Magnet-Supply-Chain_.pdf)
- 关联：[2026-05 AI/机器人/量子产业链](2026-05-ai-robotics-quantum-supply-chain-v1.md)

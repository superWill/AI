---
ticker: TSLA
name: Tesla
sector: EV + 自动驾驶/机器人（robotaxi/Optimus 期权）
layer: 观察名——不在持仓、不在 SOXX 因子
position_type: watch（观察，非持仓）
status: watching
last_updated: 2026-07-26
data_source: 2026-07-22 Q2'26 财报 + 2026-07-26 robotaxi 现状(WebSearch)。价格待核(yfinance 自相矛盾)
---

# Tesla (TSLA)

## 为什么在这本册子里（先说清定位）

**TSLA 不是持仓、不在 SOXX 因子**。它进跟踪系统只因两个角色：

1. **capex 融资结构信号的 n=2 样本**：Q2'26 FCF -$10.9 亿首负（2024 初以来首次），opex +47% 烧 AI/Optimus/robotaxi——与 GOOGL FCF 首负同周，是「AI 开支把现金机器逐个推过 FCF=0 线」的第二个样本。见 [顶部信号 note](../notes/2026-06-25-top-signals-and-panic-discipline.md) 第⑥信号行。
2. **叙事股定价的活标本**：营收创纪录但利润崩（Q2 调整 EPS $0.33 vs 预期 $0.53，miss ~38%；经营利润率 4.1%→1.4%），股价却几乎不动——**市场给 TSLA 定价的是 robotaxi/Optimus 期权,不是当期汽车利润**。「坏消息砸不动」是「好消息卖不动」（TSM/GOOGL）的镜像。

## 关键数据

| 指标 | 数据 | 备注 |
|---|---|---|
| 股价 | **待核** | yfinance 自相矛盾:spot $313 vs marketCap $1.24T 反推 ~$385,且与 7/24 的 ~$374 冲突。用前在 IBKR 核实 |
| Trailing / Forward PE | ~285x / ~141x（口径待核） | 无论哪个数都是**天价倍数=纯期权定价**,当期盈利支撑不了 |
| Beta | ~1.8 | |
| 52 周区间 | ~$298–499（待核） | |
| 段永平成本锚 | **~$372**（Q1'26 建仓 340.9 万股/$12.67 亿） | 现价大致平进平出;他买的也是期权不是当期基本面 |

## ⭐ 2026-07-26：Robotaxi / FSD 现状

**一句话：技术跨过「车里没人」这道坎（新城市首日即无安全员），但规模仍是玩具级——~40 辆 vs Waymo 3,000+，叙事跑在运营前面很远。** `[KNOWN 2026-07, 规模数字为第三方估算 MED-HIGH]`

**运营：**
- 城市：Austin(TX) + Miami/Orlando/Tampa(FL);本月一口气加三个佛州城。累计 **>38 万英里无监督里程**。
- 安全员:Austin 2026-01 起车内无安全员;**Miami 7/3 新城首日即无车内安全员**。尾巴:早期部署**跟随车(trailing vehicle)带安全员在后吊着**=系统仍需近距离兜底。
- 软件:跑 **FSD v15 早期版**;Musk 把放量绑定 v15(架构重写,模型 ~10 亿→~100 亿参数,10x)。**FSD v15 放量成败 = TSLA 版检验点**(类比 watchlist 的带日期可证伪预言)。
- Musk 口径(Q1 & 7/22 财报会):安全验证是放量**唯一约束**,"as fast as humanly possible"但卡安全。

**用户体验:**
- 好:整车厢归乘客一人(打游戏/看电影);iOS 实时活动时间预估准(优于 Uber/Lyft);公开运营早期零事故。
- 痛:**叫不到车**(需求远超 ~40 辆供给);**绕远路+躲高速**(选长路线,影响时间车费);佛州雨=camera-only 最硬测试。

**对 Waymo(关键,别被"无人"叙事带跑):**

| | Tesla | Waymo |
|---|---|---|
| 车队 | ~34–40 辆(仅 ~20 无安全员) | **~3,000–3,500 辆** |
| 周订单 | ~4,000 | **~500,000** |
| 传感器 | 纯摄像头 | LiDAR+radar+摄像头冗余 |
| 无安全员 | 2026 才起步 | 早已常态 |

规模差 ~100 倍。分析师(Gary Black)指 Tesla 在「无安全员运营」这个真正落地指标上落后 Waymo;有报道称事故率高于 Waymo `[MED 单方观点]`。

## 多空核心

- **多头**:38 万英里 → 若能扩到 3,800 万英里,camera-only 全无人 scale 成立 = 期权兑现,当前天价倍数被追认。
- **空头**:纯视觉路线赌注未结算(佛州雨季第一考);运营规模落后 Waymo 100 倍;"兑现在哪"始终是问号;当期基本面(利润率 1.4%/FCF 负)撑不起估值。

## 跟踪信号

- FSD v15 放量节奏 + 无安全员城市数(真正落地指标,别看总里程)。
- robotaxi 事故率 vs Waymo(camera-only 路线验伪/证实)。
- FCF 能否转正(capex 融资结构信号,与 GOOGL 并列跟踪)。
- Optimus 进展(第二个期权腿)。

## 参考

- [顶部信号 note](../notes/2026-06-25-top-signals-and-panic-discipline.md)（第⑥信号 n=2）
- Smart Cities Dive – 四城运营/安全 · Not a Tesla App – 38万英里/FSD v15 · Benzinga – 落后 Waymo(Gary Black) · Basenor – 乘客反馈 · TechTimes – Miami 雨季测试（均 WebSearch 2026-07-26）

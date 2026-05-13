# Market Reference: Heating Substation Controllers

## Summary

市面上成熟的供热换热站/热能控制产品，通常不是单独一个“屏幕”，而是以下组合：

```text
现场设备
  温度、压力、流量、热表、泵、阀、变频器、液位、电表
        |
        v
现场控制器
  PLC / DDC / RTU / 专用供热控制器
        |
        v
本地 HMI
  参数显示、状态显示、告警、手动操作、调试
        |
        v
远程平台
  SCADA / 智慧供热平台 / 移动 App / 运维系统
```

对我们现在的 MVP 来说，第一阶段最应该参考的是：设备添加、点表采集、本地 HMI 实时显示、基础告警、通信状态。

## Representative Products and Practices

## 1. Danfoss ECL Comfort / Leanheat

定位：供热、区域供热、生活热水等场景的智能温度控制器和远程监控方案。

做法：

- 用专用控制器做天气补偿和供水温度控制。
- 通过应用 Key 适配不同供热应用，减少现场配置复杂度。
- 控制器本体带图形显示，适合现场调试和日常查看。
- 支持远程监控、App 或工具软件，用于参数管理和运维。
- 典型 I/O 包括 Pt1000 温度输入、继电器输出、三点阀门控制输出、扩展模块、能量表、执行器等。

值得借鉴：

- 第一版 HMI 不要复杂，但要让用户快速看到系统概览。
- 参数配置应按“应用模板”组织，而不是让用户从零配点。
- 控制器要能单机运行，远程平台是增强能力。

## 2. Siemens District Heating / Climatix

定位：区域供热换热站的控制、传感器、阀门执行器、本地和远程服务组合。

做法：

- 设备组合包括控制器、阀门执行器、传感器、表计和远程服务系统。
- 强调远程监控、故障诊断、预测维护和现场/远程服务。
- 本地 HMI 用于现场服务，远程系统用于运维中心集中查看。

值得借鉴：

- 本地屏要服务现场人员，界面重点是状态、告警、参数和调试。
- 远程平台要服务管理人员，重点是多站点概览、趋势、诊断和运维。
- 设备数据要结构化，后续才能做预测维护和节能分析。

## 3. Domestic PLC Control Cabinet Solutions

定位：换热站 PLC 控制柜、变频柜、无人值守换热站系统。

常见做法：

- PLC 负责采集和控制。
- 触摸屏/按钮在站内完成监视、控制、手自动切换。
- 采集一次网、二次网温度、压力、流量、热量、室外温度。
- 采集循环泵、补水泵、变频器、调节阀、液位、电表等状态。
- 控制循环泵、补水泵、一次侧电动调节阀。
- 通过 GPRS、4G、光纤、互联网等方式连接监控中心。
- 远程平台实现无人值守、告警、报表、参数调整。

值得借鉴：

- 国内工程现场更看重可靠、可维护、兼容已有平台。
- 点表和通信协议通常比 UI 更关键。
- 要支持本地自动、本地手动、远程监控/远程参数。

## 4. Schneider / ABB Style Remote Monitoring

定位：更偏工业级远程监控、SCADA、RTU、资产诊断。

做法：

- 本地设备采集数据，边缘端处理和显示。
- 远程 SCADA 平台做实时监控、历史记录、告警、维护。
- 强调协议兼容、可靠通信、网络安全、历史数据和告警生命周期。

值得借鉴：

- 事件、告警、历史数据要从第一版就留好结构。
- 通信中断时，本地系统仍要继续采集和显示。
- 远程平台不能替代现场安全判断。

## Product Pattern

市面成熟产品一般分为三层：

### 1. Local Controller

职责：

- 采集现场设备。
- 做数据校验。
- 做基础告警。
- 做本地显示。
- 必要时做自动控制。
- 断网时继续运行。

### 2. Local HMI

职责：

- 设备总览。
- 一次侧/二次侧实时数据。
- 泵阀状态。
- 通信状态。
- 告警列表。
- 参数配置。
- 手动/自动模式。
- 调试和维护。

### 3. Remote Platform

职责：

- 多站点监控。
- 数据历史。
- 告警推送。
- 报表。
- 参数下发。
- 权限管理。
- 远程升级。
- 节能分析。

## What This Means for Our MVP

我们的最小版本应该先做成：

```text
设备管理
  添加设备、设备类型、采集地址、通信状态

实时监控
  一次侧、二次侧、泵、阀、热表、传感器

基础告警
  超温、低压、通信异常、设备故障

本地显示
  总览卡片、设备列表、当前设备详情

数据模型
  点表、单位、量程、质量标记、更新时间
```

暂时不要急着做：

- 完整自动控制。
- 复杂 AI 节能算法。
- 多租户 SaaS 平台。
- 完整 OTA。

## Suggested Device Types for MVP

- 换热机组。
- 板式换热器。
- 循环泵。
- 补水泵。
- 电动调节阀。
- 温度传感器。
- 压力传感器。
- 流量计。
- 热量表。
- 电表。
- 水箱液位。
- 变频器。
- 通信网关。

## Sources

- Danfoss ECL Controllers: https://www.danfoss.com/en-gb/products/dhs/electronic-controls/electronic-controllers-and-application-keys/ecl-controllers/
- Danfoss ECL Comfort 310: https://designcenter.danfoss.com/products/climate-solutions-for-heating/electronic-controllers-and-monitoring-solutions/ecl-comfort-controllers/ecl-comfort-310
- Siemens District Heating: https://www.siemens.com/en-us/products/hvac/district-heating/
- Danfoss Connected Systems: https://www.danfoss.com/en-gb/markets/buildings-commercial/dhs/connected-systems/
- 华东工控换热站自控系统案例: https://www.hdic.cc/articles/yytsrl.html
- 德兰电气换热站 PLC 控制柜: https://www.delanac.com/plc/34.html
- 海林智慧供热系统: https://www.hailin.com/index/index/news_detail?id=436
- Schneider Remote Monitoring and Automation: https://www.se.com/us/en/work/solutions/industrial-automation-solutions/remote-scada/

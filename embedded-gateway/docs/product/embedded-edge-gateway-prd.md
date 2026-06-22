# 嵌入式边缘网关系统产品文档

> [KNOWN][HIGH] 当前日期：2026-06-20。  
> [INFERRED][HIGH] 本文档定位为产品需求与方案草案。  
> [INFERRED][HIGH] 第一落地行业为热能/暖通。  
> [INFERRED][HIGH] 长期目标为可扩展到多行业的通用嵌入式边缘网关系统。  
> [INFERRED][HIGH] 目标硬件平台为 RK3506 与 RK3568。

## 1. 产品一句话

[INFERRED][HIGH] 做一套可运行在 RK3506 与 RK3568 上的嵌入式边缘网关系统，先面向热能设备实现标准设备添加、稳定采集、本地显示、后台配置、平台上报和安全兜底，再通过行业设备包扩展到消防、楼宇、能源、水务等场景。

## 2. 产品定位

[INFERRED][HIGH] 本产品不是单一行业控制器。  
[INFERRED][HIGH] 本产品也不是只做协议转换的透明网关。  
[INFERRED][HIGH] 本产品应定位为“设备接入 + 点表标准化 + 边缘服务 + 显示配置分离 + 平台连接”的嵌入式网关系统。

```text
现场设备
  -> 协议适配
  -> 标准点表
  -> 边缘服务
  -> 本地显示 / 后台配置 / 平台上报 / 本地控制
```

[INFERRED][HIGH] 热能行业是首个行业包。  
[INFERRED][HIGH] 通用能力沉淀在网关内核。  
[INFERRED][HIGH] 行业差异通过设备模板、业务模板、显示模板、规则模板和协议适配插件体现。

## 3. 目标用户

| 用户 | [INFERRED][HIGH] 关注点 |
|---|---|
| 现场运维人员 | [INFERRED][HIGH] 需要看到当前设备状态、报警、网络、采集质量和关键运行参数。 |
| 调试工程师 | [INFERRED][HIGH] 需要在后台添加设备、配置通道、绑定点位、校验通信和调整显示内容。 |
| 平台开发人员 | [INFERRED][HIGH] 需要稳定的 MQTT/HTTP 数据契约、质量码、时间戳、命令回执和设备拓扑。 |
| 产品/交付人员 | [INFERRED][HIGH] 需要可复制的设备模板、行业模板、验收标准和现场配置流程。 |
| 嵌入式研发人员 | [INFERRED][HIGH] 需要服务长期运行、异常恢复、日志留存、升级回滚和跨 RK3506/RK3568 的统一代码框架。 |

## 4. 核心原则

| 原则 | 说明 |
|---|---|
| [INFERRED][HIGH] 热能先行 | [INFERRED][HIGH] 第一版聚焦热能/暖通设备，不在 P0 阶段同时覆盖消防闭环控制。 |
| [INFERRED][HIGH] 架构通用 | [INFERRED][HIGH] 设备模型、点表、协议适配、配置发布、显示刷新、日志和上报机制必须面向多行业复用。 |
| [INFERRED][HIGH] 配置与显示分离 | [INFERRED][HIGH] 后台负责配置，显示端只消费已发布的运行快照和显示模型。 |
| [INFERRED][HIGH] 刷新后可见 | [INFERRED][HIGH] 后台配置发布后，显示页面刷新或收到更新事件后必须展示最新设备、点位和卡片。 |
| [INFERRED][HIGH] 安全优先 | [INFERRED][HIGH] 控制输出必须经过限值、联锁、质量码和本地安全策略校验。 |
| [INFERRED][HIGH] 长期稳定 | [INFERRED][HIGH] 任一设备、串口、网络、平台或显示端异常不能拖死采集主服务。 |
| [INFERRED][HIGH] 低配可跑 | [INFERRED][HIGH] RK3506 版本必须避免重依赖和重服务。 |
| [INFERRED][HIGH] 高配增强 | [INFERRED][HIGH] RK3568 版本可承担更完整的 Web、规则、缓存、数据库和扩展协议能力。 |

## 5. 产品形态

### 5.1 RK3506 基础版

[INFERRED][HIGH] RK3506 基础版面向低成本、稳定采集和本地显示。  
[INFERRED][MED] RK3506 基础版应优先采用轻量进程、文件配置、嵌入式 Web/API、本地快照和有限缓存。  
[INFERRED][HIGH] RK3506 基础版不应强依赖 Docker、重型数据库或大型前端运行时。

| 能力 | [INFERRED][HIGH] RK3506 基础版要求 |
|---|---|
| 协议 | [INFERRED][HIGH] Modbus RTU、Modbus TCP、GPIO/DI/DO、串口私有协议优先。 |
| 配置 | [INFERRED][HIGH] 支持后台 Web/API 配置设备、点位、显示卡片和上报参数。 |
| 显示 | [INFERRED][HIGH] 支持本地屏或轻量 Web 页面显示运行快照。 |
| 服务 | [INFERRED][HIGH] 支持采集、质量码、报警、日志、MQTT 上报和看门狗。 |
| 存储 | [INFERRED][HIGH] 支持配置文件、日志文件和有限离线缓存。 |

### 5.2 RK3568 增强版

[INFERRED][HIGH] RK3568 增强版面向更多协议、更复杂显示、更强边缘计算和更大项目规模。  
[INFERRED][MED] RK3568 增强版可支持容器化、OPC UA Server、规则引擎、本地数据库、更多 Web 管理能力和更长离线缓存。

| 能力 | [INFERRED][HIGH] RK3568 增强版要求 |
|---|---|
| 协议 | [INFERRED][HIGH] 在基础版上扩展 OPC UA、BACnet、CAN、M-Bus、HTTP API 等。 |
| 配置 | [INFERRED][HIGH] 支持多设备批量导入、模板库、版本管理和配置回滚。 |
| 显示 | [INFERRED][HIGH] 支持更完整的 Web HMI、趋势图、设备拓扑和诊断页面。 |
| 服务 | [INFERRED][HIGH] 支持规则引擎、数据缓存、远程诊断和插件管理。 |
| 存储 | [INFERRED][HIGH] 支持本地时序缓存、事件库和配置版本库。 |

## 6. 系统架构

```text
                 平台 / 云 / 上位系统
                       |
             MQTT / HTTP / OPC UA(可选)
                       |
┌──────────────────────▼──────────────────────┐
│                边缘网关服务层                │
│  设备注册  点表快照  报警事件  日志  上报缓存 │
│  配置发布  显示模型  控制仲裁  看门狗         │
└──────────────┬────────────────┬─────────────┘
               │                │
       后台配置/API          显示端/HMI
               │                │
       配置草稿/发布       快照读取/刷新订阅
               │                │
┌──────────────▼────────────────▼─────────────┐
│              标准设备与点表模型              │
│  硬件模板  业务模板  点位绑定  显示卡片       │
└──────────────────────┬──────────────────────┘
                       │
┌──────────────────────▼──────────────────────┐
│                 协议适配层                   │
│  Modbus RTU/TCP  IO  Serial  CAN  OPC UA...  │
└──────────────────────┬──────────────────────┘
                       │
                 现场设备与 IO
```

[INFERRED][HIGH] 后台配置和显示页面不应直接读写同一份未校验配置。  
[INFERRED][HIGH] 后台配置应先进入草稿态，校验通过后发布为运行配置。  
[INFERRED][HIGH] 显示端应读取运行快照与显示模型，而不是读取原始设备驱动配置。  
[INFERRED][HIGH] 配置发布后，采集服务应按版本加载新配置，并生成新的设备注册表、点表快照和显示模型。

## 7. 配置与显示分离机制

### 7.1 两类界面

| 界面 | 职责 | 不应承担的职责 |
|---|---|---|
| 后台配置端 | [INFERRED][HIGH] 添加设备、选择模板、配置通信参数、绑定点位、设置显示卡片、发布配置。 | [INFERRED][HIGH] 不直接承担现场运行监控主界面。 |
| 显示端 | [INFERRED][HIGH] 展示设备状态、关键指标、报警、趋势、网络和服务健康状态。 | [INFERRED][HIGH] 不直接编辑底层通信参数。 |

### 7.2 配置生命周期

```text
新建/编辑配置
  -> 草稿保存
  -> 参数校验
  -> 通信测试
  -> 发布配置
  -> 运行服务加载
  -> 生成快照与显示模型
  -> 显示端刷新后更新
```

| 阶段 | [INFERRED][HIGH] 要求 |
|---|---|
| 草稿保存 | [INFERRED][HIGH] 不影响当前运行采集。 |
| 参数校验 | [INFERRED][HIGH] 检查地址冲突、寄存器格式、量程、单位、必填字段和安全态。 |
| 通信测试 | [INFERRED][HIGH] 支持对单个设备执行读测试和质量码判断。 |
| 发布配置 | [INFERRED][HIGH] 生成新配置版本，记录操作人、时间、差异和回滚点。 |
| 运行加载 | [INFERRED][HIGH] 运行服务应能按设备或总线局部重载，避免全局服务重启。 |
| 显示刷新 | [INFERRED][HIGH] 显示端刷新页面后必须读取新显示模型和新点表快照。 |

### 7.3 显示端更新方式

[INFERRED][HIGH] P0 阶段至少支持刷新页面后更新。  
[INFERRED][MED] P1 阶段应支持 SSE/WebSocket/轮询任一种实时更新方式。  
[INFERRED][HIGH] 显示端需要展示配置版本号，方便现场判断页面是否已经加载最新配置。

```json
{
  "config_version": 12,
  "generated_at": 1781900000000,
  "devices": [
    {
      "device_id": "heat-ai-001",
      "name": "二次侧温压采集模块",
      "status": "online",
      "cards": ["secondary_loop"]
    }
  ],
  "points": {
    "sec_supply_temp": {
      "v": 52.3,
      "unit": "degC",
      "q": "good",
      "ts": 1781900000000
    }
  }
}
```

[INFERRED][HIGH] `config_version` 用于判断显示模型是否更新。  
[INFERRED][HIGH] `q` 用于判断数据质量。  
[INFERRED][HIGH] `ts` 用于判断数据新鲜度。  
[INFERRED][HIGH] 显示端必须显式区分正常值、陈旧值、通信异常值和未配置值。

## 8. 标准设备模型

### 8.1 硬件模板

[INFERRED][HIGH] 硬件模板描述设备如何通信、有哪些通道、寄存器如何解析。  
[INFERRED][HIGH] 硬件模板用于减少重复配置和现场错误。

| 模板 | [INFERRED][HIGH] P0 建议 |
|---|---|
| RS485 8AI 模块 | [INFERRED][HIGH] P0 必做。 |
| RS485 DI 模块 | [INFERRED][HIGH] P0 必做。 |
| RS485 DO 模块 | [INFERRED][HIGH] P0 必做。 |
| RS485 AO 模块 | [INFERRED][MED] P0 可选，P1 必做。 |
| Modbus TCP 采集模块 | [INFERRED][HIGH] P0 建议做。 |
| 热量表/电表 | [INFERRED][MED] P0 可选，P1 必做。 |
| 变频器 | [INFERRED][MED] P0 可建模板，P1 开放控制。 |

### 8.2 业务设备模板

[INFERRED][HIGH] 业务设备模板描述现场对象的业务含义、关键点位、显示卡片和安全要求。  
[INFERRED][HIGH] 业务模板不应绑定到单一硬件通道。  
[INFERRED][HIGH] 一个业务设备可以绑定多个硬件设备的点位。

| 业务设备 | [INFERRED][HIGH] 必需点 | [INFERRED][HIGH] 显示关键项 |
|---|---|---|
| 温度测点 | 当前温度、质量码、时间戳 | 当前值、单位、趋势、异常状态 |
| 压力测点 | 当前压力、质量码、时间戳 | 当前值、上限、下限、报警 |
| 循环泵 | 启停命令、运行反馈、故障反馈 | 运行状态、故障、命令反馈一致性 |
| 补水泵 | 启停命令、压力反馈、故障反馈 | 补水中、补水失败、缺水/低压 |
| 调节阀 | 开度命令、开度反馈、限位/故障 | 指令、反馈、偏差、动作状态 |
| 热量表 | 流量、供温、回温、累计热量 | 瞬时流量、累计热量、通信状态 |
| 变频器 | 频率命令、频率反馈、运行/故障 | 频率、运行、故障、通信 |

## 9. 热能行业 P0 范围

[INFERRED][HIGH] P0 的目标是让热能场景具备可演示、可配置、可长期运行的采集显示闭环。  
[INFERRED][HIGH] P0 不应承诺替代成熟 PLC 自控柜。  
[INFERRED][HIGH] P0 可以支持普通监测、报警和有限控制模拟。  
[INFERRED][HIGH] P0 对真实执行机构控制应默认关闭。

### 9.1A P0 范围锁定(单一权威定义)

[INFERRED][HIGH] 为避免范围蔓延，P0 锁死为以下闭环，本文件其它章节如有冲突以本节为准：

```text
P0 = 配置发布闭环 + 采集快照 + 显示刷新 + MQTT 上报 + 统一质量码 + 72h 稳定性
```

[INFERRED][HIGH] P0 的"控制"只到三件事，不含真实闭环：

| P0 允许 | [INFERRED][HIGH] 说明 |
|---|---|
| 命令拒绝路径 | [INFERRED][HIGH] 平台/本地下发设定值能被安全策略拒绝并回执原因。 |
| 模拟控制 | [INFERRED][HIGH] 在 sim 源上演示指令→反馈，不写真实执行机构。 |
| 安全策略模型 | [INFERRED][HIGH] 限值、模式、联锁、有效期作为编译产物存在并被校验。 |

[INFERRED][HIGH] 明确移出 P0(降到 P1/P2)：

| 移出项 | [INFERRED][HIGH] 去向 | [INFERRED][HIGH] 理由 |
|---|---|---|
| Intent 仲裁与真实控制写出(§26) | [INFERRED][HIGH] P1 | [INFERRED][HIGH] 控制链路会把 P0 排期拖大，需现场联锁与反馈验证。 |
| 发布事务的 dry-run/observe/自动回滚(§22) | [INFERRED][HIGH] P1 | [INFERRED][HIGH] P0 用 validate+compile+activate+手动回滚即可。 |
| 私有 MCU 自识别自动建模(§36) | [INFERRED][HIGH] P1 | [INFERRED][HIGH] P0 先手工建模，识别仅作提示。 |
| 多行业包(§28) | [INFERRED][HIGH] P2 | [INFERRED][HIGH] 先用热能跑通内核再抽象行业包。 |

### 9.1 P0 必做功能

| 编号 | 功能 | [INFERRED][HIGH] 验收点 |
|---|---|---|
| P0-FR-001 | 设备模板添加 | [INFERRED][HIGH] 后台可添加 RS485/Modbus 设备并生成点位。 |
| P0-FR-002 | 点位绑定 | [INFERRED][HIGH] 可将硬件通道绑定为温度、压力、泵状态等业务点。 |
| P0-FR-003 | 配置发布 | [INFERRED][HIGH] 后台修改配置后可发布新版本。 |
| P0-FR-004 | 显示刷新 | [INFERRED][HIGH] 显示页面刷新后看到新设备、新点位和新卡片。 |
| P0-FR-005 | 采集服务 | [INFERRED][HIGH] 支持周期采集、超时、重试、质量码和离线标记。 |
| P0-FR-006 | 本地快照 | [INFERRED][HIGH] 提供 `/api/snapshot` 或等价接口给显示端读取。 |
| P0-FR-007 | 报警事件 | [INFERRED][HIGH] 支持阈值报警、通信异常报警和恢复事件。 |
| P0-FR-008 | MQTT 上报 | [INFERRED][HIGH] 支持 heartbeat、telemetry、alarm、event。 |
| P0-FR-009 | 日志 | [INFERRED][HIGH] 记录采集、配置发布、报警、上报、服务异常。 |
| P0-FR-010 | 看门狗 | [INFERRED][HIGH] 支持进程异常自动恢复或系统级守护。 |

### 9.2 P0 关键显示信息

[INFERRED][HIGH] 显示端不应堆满底层配置字段。  
[INFERRED][HIGH] 显示端应突出现场运维最关键的信息。

| 页面/卡片 | [INFERRED][HIGH] 关键显示信息 |
|---|---|
| 总览 | [INFERRED][HIGH] 站点状态、采集状态、平台连接、报警数量、配置版本。 |
| 一次侧 | [INFERRED][HIGH] 供温、回温、供压、回压、流量、阀门状态。 |
| 二次侧 | [INFERRED][HIGH] 供温、回温、供压、回压、压差、循环状态。 |
| 泵组 | [INFERRED][HIGH] 运行命令、运行反馈、故障反馈、频率反馈、通信状态。 |
| 补水 | [INFERRED][HIGH] 补水压力、补水泵状态、缺水状态、补水失败报警。 |
| 设备 | [INFERRED][HIGH] 在线/离线、最后采集时间、质量码、错误计数。 |
| 报警 | [INFERRED][HIGH] 当前报警、历史报警、发生时间、恢复时间、确认状态。 |
| 系统 | [INFERRED][HIGH] CPU、内存、存储、网络、MQTT、运行时长、配置版本。 |

### 9.3 P0 暂不做

| 能力 | [INFERRED][HIGH] 原因 |
|---|---|
| 高风险自动控制真实阀泵 | [INFERRED][HIGH] 需要现场联锁、执行器确认和供暖季验证。 |
| 全行业设备模板一次性覆盖 | [INFERRED][HIGH] 会拉高范围并稀释热能首版交付。 |
| 消防闭环联动 | [INFERRED][HIGH] 消防涉及合规和安全责任边界。 |
| 完整规则引擎 | [INFERRED][MED] P0 可用固定报警规则验证模型。 |
| 大规模 OTA | [INFERRED][MED] P0 先保留升级脚本和回滚策略。 |

## 10. 后台配置功能

### 10.1 设备添加流程

```text
选择行业：热能
  -> 选择硬件模板：RS485 8AI
  -> 填通信参数：串口、地址、波特率、校验、超时
  -> 自动生成通道：AI1~AI8
  -> 绑定业务点：二次侧供温、二次侧回温、压力等
  -> 配置量程、单位、阈值
  -> 通信测试
  -> 选择显示卡片
  -> 发布配置
  -> 显示端刷新
```

[INFERRED][HIGH] 后台必须把“通信设备”和“业务设备”分开。  
[INFERRED][HIGH] 后台必须支持未绑定通道。  
[INFERRED][HIGH] 后台必须提示未配置、配置冲突、量程缺失和高风险输出缺少安全态。

### 10.2 配置校验规则

| 校验项 | [INFERRED][HIGH] 要求 |
|---|---|
| 设备地址 | [INFERRED][HIGH] 同一总线下 Modbus 从站地址不能重复。 |
| 点位 ID | [INFERRED][HIGH] 同一网关内点位 ID 必须唯一。 |
| 量程 | [INFERRED][HIGH] AI/AO 点必须配置原始量程和工程量程。 |
| 单位 | [INFERRED][HIGH] 工程量点必须配置单位。 |
| 质量码 | [INFERRED][HIGH] 所有采集点必须有质量码。 |
| 命令点 | [INFERRED][HIGH] 控制命令点必须配置上下限、安全态和权限。 |
| 反馈点 | [INFERRED][HIGH] 泵、阀、变频器等控制对象应绑定反馈点。 |
| 显示卡片 | [INFERRED][HIGH] 已发布业务设备必须至少关联一个显示位置或标记为后台设备。 |

## 11. 数据模型

### 11.1 点位模型

```json
{
  "point_id": "sec_supply_temp",
  "name": "二次侧供水温度",
  "industry": "heating",
  "device_id": "ai-module-001",
  "role": "measurement",
  "value": 52.3,
  "unit": "degC",
  "quality": "good",
  "timestamp": 1781900000000,
  "source": {
    "protocol": "modbus_rtu",
    "bus": "rs485_1",
    "slave": 2,
    "register": 0
  }
}
```

[INFERRED][HIGH] 点位模型必须同时服务采集、显示、报警和上报。  
[INFERRED][HIGH] 点位模型必须保留来源信息，方便现场诊断。  
[INFERRED][HIGH] 点位模型必须保留质量码，避免平台和显示端误用坏数据。

### 11.2 设备模型

```json
{
  "device_id": "ai-module-001",
  "name": "二次侧温压采集模块",
  "hardware_template": "rs485_8ai_modbus",
  "industry": "heating",
  "status": "online",
  "config_version": 12,
  "points": ["sec_supply_temp", "sec_return_temp", "sec_supply_pressure"]
}
```

[INFERRED][HIGH] 硬件设备用于通信管理。  
[INFERRED][HIGH] 业务设备用于现场展示、报警和控制策略。  
[INFERRED][HIGH] 同一个硬件设备可承载多个业务点。

## 12. 稳定性与可靠性要求

| 要求 | [INFERRED][HIGH] 说明 |
|---|---|
| I/O 超时 | [INFERRED][HIGH] 串口、网络、MQTT、DNS、文件写入都不能无限阻塞。 |
| 故障隔离 | [INFERRED][HIGH] 单个离线设备不能拖慢整条总线到不可用。 |
| 退避轮询 | [INFERRED][HIGH] 连续超时设备应降频轮询。 |
| 采集上传解耦 | [INFERRED][HIGH] MQTT 断开不能导致采集停止。 |
| 离线缓存 | [INFERRED][MED] P0 支持有限缓存，P1 支持可配置容量。 |
| 看门狗 | [INFERRED][HIGH] 主服务异常时应自动重启。 |
| 配置回滚 | [INFERRED][HIGH] 发布错误配置后应能回滚到上一版本。 |
| 日志留存 | [INFERRED][HIGH] 至少保留配置、采集、报警、上报和系统异常日志。 |
| 数据质量 | [INFERRED][HIGH] 显示和平台都必须看到质量码。 |

## 13. 上行平台接口

[INFERRED][HIGH] P0 优先采用 MQTT。  
[INFERRED][HIGH] 上行必须包含设备心跳、遥测、报警和事件。  
[INFERRED][HIGH] 下行命令必须有命令 ID、有效期、执行状态和拒绝原因。

| 方向 | Topic | [INFERRED][HIGH] 用途 |
|---|---|---|
| 上行 | `station/{device_id}/heartbeat` | [INFERRED][HIGH] 上报网关在线状态。 |
| 上行 | `station/{device_id}/telemetry` | [INFERRED][HIGH] 上报点位快照。 |
| 上行 | `station/{device_id}/alarm` | [INFERRED][HIGH] 上报警报发生和恢复。 |
| 上行 | `station/{device_id}/event` | [INFERRED][HIGH] 上报配置变更、设备上下线和状态变化。 |
| 下行 | `station/{device_id}/command` | [INFERRED][HIGH] 接收平台命令。 |
| 上行 | `station/{device_id}/command_reply` | [INFERRED][HIGH] 回传命令结果。 |

## 14. 安全边界

[INFERRED][HIGH] 热能 P0 阶段应默认只开放采集、显示、报警和上报。  
[INFERRED][HIGH] 若开放控制，控制输出必须经过本地安全策略。  
[INFERRED][HIGH] 远程命令不能绕过本地限值、联锁、质量码和人工接管。  
[INFERRED][HIGH] 平台失联后，网关必须继续本地采集、显示和报警。  
[INFERRED][HIGH] 恢复联网后，过期命令不能补执行。

## 15. 分阶段路线

### P0：热能采集显示闭环

[INFERRED][HIGH] P0 目标是在 RK3506 和 RK3568 上跑通同一套核心业务。  
[INFERRED][HIGH] P0 重点是后台配置、标准设备添加、采集服务、显示刷新、MQTT 上报和稳定运行。

| 交付物 | [INFERRED][HIGH] 内容 |
|---|---|
| 设备模板库 | [INFERRED][HIGH] RS485 AI/DI/DO、Modbus TCP、温度、压力、泵、阀基础模板。 |
| 后台配置 | [INFERRED][HIGH] 设备添加、点位绑定、配置发布、通信测试。 |
| 显示端 | [INFERRED][HIGH] 总览、一次侧、二次侧、泵组、报警、系统状态。 |
| 运行服务 | [INFERRED][HIGH] 采集、质量码、报警、快照、MQTT、日志、看门狗。 |
| 验收报告 | [INFERRED][HIGH] 至少 72h 连续运行、断网恢复、设备离线和配置刷新测试。 |

### P1：热能有限控制与配置增强

[INFERRED][MED] P1 目标是支持更多设备模板、配置版本管理、局部重载、离线缓存和有限控制。  
[INFERRED][HIGH] P1 控制能力必须以现场联锁和反馈点为准。

### P2：多行业扩展

[INFERRED][MED] P2 目标是将热能沉淀出的通用能力扩展为行业包机制。  
[INFERRED][MED] P2 可新增消防监测、楼宇 BACnet、能源计量、水务泵站等行业包。  
[INFERRED][HIGH] 消防行业应先做监测和显示，不应先承诺核心消防联动控制。

## 16. P0 验收标准

| 类别 | [INFERRED][HIGH] 验收标准 |
|---|---|
| 跨平台 | [INFERRED][HIGH] 同一套核心代码或同一套数据模型可在 RK3506 与 RK3568 上运行。 |
| 设备添加 | [INFERRED][HIGH] 后台可添加至少 3 类标准设备模板。 |
| 配置发布 | [INFERRED][HIGH] 发布配置后显示端刷新可看到新设备和点位。 |
| 采集稳定 | [INFERRED][HIGH] 设备正常时数据持续刷新，设备离线时质量码变为异常。 |
| 显示正确 | [INFERRED][HIGH] 显示端展示值、单位、质量码、更新时间和配置版本。 |
| 上报稳定 | [INFERRED][HIGH] MQTT 断开后采集不中断，恢复后继续上报。 |
| 异常恢复 | [INFERRED][HIGH] 主服务异常后可自动恢复。 |
| 连续运行 | [INFERRED][HIGH] P0 建议至少完成 72h 连续运行测试。 |
| 日志追踪 | [INFERRED][HIGH] 可通过日志定位配置发布、设备离线、报警和上报异常。 |

## 17. 待确认问题

| 问题 | [INFERRED][HIGH] 为什么重要 |
|---|---|
| RK3506 最低内存和存储规格 | [INFERRED][HIGH] 决定是否可使用 Python、SQLite、Web 前端和缓存策略。 |
| RK3506 是否必须带本地屏 | [INFERRED][HIGH] 决定显示端是 LCD HMI、Web HMI 还是两者都要。 |
| 首批真实设备型号 | [INFERRED][HIGH] 决定 P0 模板字段、寄存器配置和验收用例。 |
| 后台配置是否需要权限 | [INFERRED][MED] 决定 P0 是否加入账号、角色和操作审计。 |
| 是否需要 Excel/JSON 导入 | [INFERRED][MED] 决定配置效率和现场交付方式。 |
| P1 是否允许真实控制输出 | [INFERRED][HIGH] 决定安全联锁、控制仲裁和验收风险；P0 已锁定不含真实闭环(§9.1A)。 |
| 平台是否已确定 | [INFERRED][HIGH] 决定 MQTT payload 是否需要兼容既有平台。 |

## 18. 当前推荐决策

1. [INFERRED][HIGH] P0 以热能采集显示网关立项。  
2. [INFERRED][HIGH] P0 明确支持后台配置与显示端分离。  
3. [INFERRED][HIGH] P0 必须实现配置发布后显示刷新更新。  
4. [INFERRED][HIGH] P0 不承诺真实高风险闭环控制。  
5. [INFERRED][HIGH] P0 同时验证 RK3506 基础版与 RK3568 增强版的共用数据模型。  
6. [INFERRED][HIGH] P0 以设备模板和业务模板作为全行业通用化的核心资产。  
7. [INFERRED][HIGH] P0 验收以 72h 连续运行、设备离线恢复、配置刷新和 MQTT 断网恢复为主。

## 19. 深层架构结论：现场事实系统

[INFERRED][HIGH] 更深一层看，本产品不应只被设计成“设备管理系统”。  
[INFERRED][HIGH] 本产品应被设计成“现场事实系统”。  
[INFERRED][HIGH] 设备、通道、点位、显示、报警、上报和控制都应围绕“现场事实”组织。

```text
现场事实 = 某个来源在某个时间，对某个点位给出的一个带质量的声明
```

[INFERRED][HIGH] 现场事实是系统内核的最小可信单元。  
[INFERRED][HIGH] 显示端、报警模块、平台上报和控制仲裁都应消费现场事实，而不是直接消费驱动返回值。

```json
{
  "fact_id": "sec_supply_temp@1781900000000",
  "point_id": "sec_supply_temp",
  "value": 52.3,
  "unit": "degC",
  "quality": "good",
  "source": "rs485_1.addr2.reg0",
  "observed_at": 1781900000000,
  "received_at": 1781900000040
}
```

| 字段 | [INFERRED][HIGH] 含义 |
|---|---|
| `fact_id` | [INFERRED][HIGH] 单条事实的唯一标识，用于追踪和去重。 |
| `point_id` | [INFERRED][HIGH] 事实归属的标准点位。 |
| `value` | [INFERRED][HIGH] 事实值。 |
| `unit` | [INFERRED][HIGH] 工程单位。 |
| `quality` | [INFERRED][HIGH] 事实质量，不能省略。 |
| `source` | [INFERRED][HIGH] 事实来源，必须能追到硬件通道或计算规则。 |
| `observed_at` | [INFERRED][HIGH] 现场采样时刻。 |
| `received_at` | [INFERRED][HIGH] 网关收到或生成事实的时刻。 |

[INFERRED][HIGH] `observed_at` 与 `received_at` 必须分开。  
[INFERRED][HIGH] 前者用于现场时序判断，后者用于链路延迟和系统诊断。  
[INFERRED][HIGH] 离线补传时必须保留原始 `observed_at`。

## 20. 点位类型：Observed、Derived、Commanded

[INFERRED][HIGH] 点位不能都按同一种数据处理。  
[INFERRED][HIGH] 产品内核应区分 Observed Point、Derived Point 和 Commanded Point。

| 类型 | [INFERRED][HIGH] 定义 | [INFERRED][HIGH] 热能示例 | [INFERRED][HIGH] 关键风险 |
|---|---|---|---|
| Observed Point | [INFERRED][HIGH] 来自现场采集的点。 | [INFERRED][HIGH] 供水温度、回水压力、泵运行反馈。 | [INFERRED][HIGH] 传感器故障、通信超时、数据陈旧。 |
| Derived Point | [INFERRED][HIGH] 由系统计算得到的点。 | [INFERRED][HIGH] 压差、在线率、报警状态、阀门偏差。 | [INFERRED][HIGH] 上游事实坏掉后仍被误认为有效。 |
| Commanded Point | [INFERRED][HIGH] 系统希望现场达到的目标或命令。 | [INFERRED][HIGH] 阀位设定、供温目标、泵频率设定。 | [INFERRED][HIGH] 未经仲裁直接写入现场。 |

[INFERRED][HIGH] Observed Point 可以失效。  
[INFERRED][HIGH] Derived Point 必须继承或合成来源事实的质量。  
[INFERRED][HIGH] Commanded Point 必须经过命令仲裁和反馈确认。  
[INFERRED][HIGH] P0 仅建模 Commanded Point 与拒绝回执，不执行真实仲裁写出；真实仲裁属 P1(§9.1A、§26)。

```text
Observed Point:
  sec_supply_temp = 52.3 degC, quality=good

Derived Point:
  sec_delta_pressure = sec_supply_pressure - sec_return_pressure

Commanded Point:
  valve_open_sp = 60%, origin=local_hmi, valid_until=...
```

## 21. Runtime Graph：配置编译后的运行图

[INFERRED][HIGH] 当前产品不应只生成扁平快照。  
[INFERRED][HIGH] 后台配置发布后应编译出 Runtime Graph。  
[INFERRED][HIGH] Runtime Graph 描述硬件、通道、点位、业务设备、显示卡片和上报对象之间的关系。

```text
硬件设备 -> 通道 -> 点位 -> 业务设备 -> 显示卡片 -> 上报对象
```

[INFERRED][HIGH] 示例：

```text
RS485 8AI 模块 AI1
  -> sec_supply_temp
  -> 二次侧系统
  -> 二次侧卡片
  -> telemetry.heating.secondary_loop
```

| 图节点 | [INFERRED][HIGH] 作用 |
|---|---|
| 硬件设备 | [INFERRED][HIGH] 描述通信地址、协议、接口和物理设备状态。 |
| 通道 | [INFERRED][HIGH] 描述 AI/DI/DO/AO、寄存器、线圈或 SDK 通道。 |
| 点位 | [INFERRED][HIGH] 描述标准语义、单位、质量、角色和来源。 |
| 业务设备 | [INFERRED][HIGH] 描述泵、阀、换热机组、热量表等现场对象。 |
| 显示卡片 | [INFERRED][HIGH] 描述显示端如何组织关键点位。 |
| 上报对象 | [INFERRED][HIGH] 描述 MQTT/HTTP/OPC UA 输出如何取数。 |

[INFERRED][HIGH] 显示端、MQTT 上报、报警和控制都应读取 Runtime Graph 的编译产物。  
[INFERRED][HIGH] 这样后台配置变更后，显示刷新更新就变成运行图版本切换，而不是页面临时逻辑。

## 22. 配置发布事务

[INFERRED][HIGH] 后台保存 JSON 不应直接改变运行系统。  
[INFERRED][HIGH] 配置发布应按事务处理。  
[INFERRED][HIGH] 但完整事务(含试运行、观察、自动回滚)对 RK3506 P0 偏重，必须分两档落地。

```text
P0:  draft -> validate -> compile -> activate -> (失败/异常) 手动回滚
P1:  draft -> validate -> compile -> dry-run -> activate -> observe -> commit / 自动回滚
```

[INFERRED][HIGH] P0 必做阶段：

| 阶段 | [INFERRED][HIGH] 要求 | [INFERRED][HIGH] 失败处理 |
|---|---|---|
| `draft` | [INFERRED][HIGH] 保存后台草稿，不影响运行。 | [INFERRED][HIGH] 保留错误提示，不生成运行版本。 |
| `validate` | [INFERRED][HIGH] 校验地址、量程、单位、点位 ID、权限、安全态。 | [INFERRED][HIGH] 返回错误列表。 |
| `compile` | [INFERRED][HIGH] 生成运行图、点位注册表、轮询计划、显示模型、上报模型和安全策略。 | [INFERRED][HIGH] 阻止发布。 |
| `activate` | [INFERRED][HIGH] 将运行服务切换到新版本，保留上一版本作为回滚点。 | [INFERRED][HIGH] 切换失败时保持旧版本；现场可手动回滚。 |

[INFERRED][MED] P1 增强阶段：

| 阶段 | [INFERRED][MED] 要求 | [INFERRED][MED] 失败处理 |
|---|---|---|
| `dry-run` | [INFERRED][MED] 对新增/变更设备做通信测试和读写能力检查。 | [INFERRED][MED] 标记不可激活或要求人工确认。 |
| `observe` | [INFERRED][MED] 观察新版本采集成功率、关键点存在性、显示模型完整性。 | [INFERRED][MED] 异常时自动回滚。 |
| `commit` | [INFERRED][MED] 观察期通过后固化为当前版本。 | [INFERRED][MED] 保留回滚点。 |

[INFERRED][HIGH] P0 即使省掉 `dry-run`/`observe`，`activate` 也必须保留上一版本，保证手动回滚可用。  
[INFERRED][MED] 单设备通信测试(§7.2 通信测试)在 P0 仍可作为发布前的独立动作，不等同于整事务级 `dry-run`。

## 23. 配置编译器产物

[INFERRED][HIGH] 配置编译器是后台配置与运行系统之间的核心 Module。  
[INFERRED][HIGH] 它的 Interface 应尽量小：输入配置草稿，输出可运行版本或错误列表。

```text
输入：config_draft.json

输出：
  runtime_graph.json
  point_registry.json
  poll_plan.json
  display_model.json
  telemetry_model.json
  safety_policy.json
  diagnostics_plan.json
```

| 编译产物 | [INFERRED][HIGH] 用途 |
|---|---|
| `runtime_graph.json` | [INFERRED][HIGH] 描述硬件、通道、点位、业务设备、显示和上报之间的关系。 |
| `point_registry.json` | [INFERRED][HIGH] 提供点位索引、角色、单位、来源、质量规则和写权限。 |
| `poll_plan.json` | [INFERRED][HIGH] 提供采集计划，包括总线、地址、起始寄存器、数量、周期、超时和退避策略。 |
| `display_model.json` | [INFERRED][HIGH] 提供页面、卡片、字段、点位绑定和显示优先级。 |
| `telemetry_model.json` | [INFERRED][HIGH] 提供上报分组、topic、字段映射和上报频率。 |
| `safety_policy.json` | [INFERRED][HIGH] 提供命令权限、限值、模式、联锁、有效期和反馈要求。 |
| `diagnostics_plan.json` | [INFERRED][HIGH] 提供设备诊断、通信测试、质量码和故障解释规则。 |

[INFERRED][HIGH] 运行时不应反复解释后台草稿配置。  
[INFERRED][HIGH] 运行时应加载这些编译产物。  
[INFERRED][HIGH] 这能让 RK3506 基础版保持轻量，也能让 RK3568 增强版扩展更多管理能力。

## 24. 轮询计划器

[INFERRED][HIGH] Modbus 适配器不应自己决定如何遍历所有设备。  
[INFERRED][HIGH] 轮询计划应由配置编译器生成。  
[INFERRED][HIGH] 轮询计划器应负责寄存器合并、分级周期、离线退避、同总线串行和多总线并行。

```json
{
  "bus": "rs485_1",
  "tasks": [
    {
      "task_id": "read_heat_unit_1_fast",
      "addr": 1,
      "function": 3,
      "start": 0,
      "count": 8,
      "period_ms": 2000,
      "timeout_ms": 300,
      "retries": 1,
      "backoff_after_failures": 3,
      "backoff_period_ms": 30000
    }
  ]
}
```

[COMMON][HIGH] RS485 半双工总线同一时刻只能有一个主站事务。  
[INFERRED][HIGH] 同一条 RS485 总线内应串行执行轮询任务。  
[INFERRED][HIGH] 多条 RS485 总线可以并行执行。  
[INFERRED][HIGH] 连续寄存器应尽量合并读取。  
[INFERRED][HIGH] 连续超时设备应进入退避，避免拖慢整条总线。

## 25. Failure Semantics：点位失败语义

[INFERRED][HIGH] 质量码不足以表达业务后果。  
[INFERRED][HIGH] 每个点位角色或业务模板必须定义失败语义。  
[INFERRED][HIGH] 失败语义描述某个点超时、断线、越界、陈旧或质量差时，显示、报警、控制、上报和保留值应如何处理。

```text
sec_supply_temp timeout:
  display: 显示陈旧
  alarm: 产生通信故障
  control: 禁止自动调节
  telemetry: 上报 stale/bad
  retention: 保留最后值但不得作为 good 使用
```

| 点位角色 | [INFERRED][HIGH] 失败语义重点 |
|---|---|
| 温度/压力测量 | [INFERRED][HIGH] 超时后显示陈旧，自动控制禁用或降级。 |
| 急停/缺水/超压输入 | [INFERRED][HIGH] 无法确认正常时应进入保守安全状态。 |
| 泵运行反馈 | [INFERRED][HIGH] 命令与反馈不一致时应产生反馈失败事件。 |
| 阀门反馈 | [INFERRED][HIGH] 指令与反馈长期偏差时应产生执行器异常。 |
| 热量表累计值 | [INFERRED][HIGH] 通信失败时可保留最后累计值，但不能伪造增量。 |
| 平台下发设定值 | [INFERRED][HIGH] 超过有效期后必须回退到本地策略或保持安全设定。 |

[INFERRED][HIGH] Failure Semantics 应属于业务模板或点位角色。  
[INFERRED][HIGH] 驱动层只负责报告通信事实，不应决定业务后果。

## 26. Intent 控制模型

[INFERRED][HIGH] 平台、后台和本地触摸屏都不应直接写寄存器。  
[INFERRED][HIGH] 它们应提交控制 Intent。  
[INFERRED][HIGH] 网关内核应把 Intent 仲裁成命令计划，再交给协议适配器执行。

```json
{
  "intent_id": "intent-20260620-001",
  "intent": "set_secondary_supply_temp",
  "target": 52.0,
  "valid_until": 1781903600000,
  "origin": "local_hmi",
  "operator": "admin"
}
```

```text
Intent
  -> 权限校验
  -> 设备模式校验
  -> 点位质量校验
  -> 联锁校验
  -> 限值/速率限制
  -> 生成命令计划
  -> 写入 Adapter
  -> 观察反馈
  -> 回传结果
```

| 检查项 | [INFERRED][HIGH] 要求 |
|---|---|
| 权限 | [INFERRED][HIGH] 不同来源的 Intent 应有不同权限。 |
| 模式 | [INFERRED][HIGH] 设备在手动、检修、故障、自动模式下的可控范围不同。 |
| 点位质量 | [INFERRED][HIGH] 关键反馈点质量差时不得进入自动闭环。 |
| 联锁 | [INFERRED][HIGH] 急停、缺水、超压、故障反馈等必须优先于普通命令。 |
| 限值 | [INFERRED][HIGH] 命令值必须符合安全范围。 |
| 速率限制 | [INFERRED][HIGH] 阀位、频率、温度目标等应限制变化速度。 |
| 有效期 | [INFERRED][HIGH] 过期 Intent 不得执行。 |
| 反馈确认 | [INFERRED][HIGH] 可控设备应观察反馈并形成执行结果。 |

[INFERRED][HIGH] Intent 模型能统一平台优化、本地触摸、后台调试和自动策略。  
[INFERRED][HIGH] 它能避免多个入口绕过同一套安全仲裁。

## 27. 可执行设备模板

[INFERRED][HIGH] 设备模板不应只是表单默认值。  
[INFERRED][HIGH] 设备模板应是可执行规格。  
[INFERRED][HIGH] 可执行设备模板应包含配置 schema、校验规则、编译逻辑、诊断规则和默认显示。

```text
template_rs485_8ai:
  config_schema
  generate_channels
  validate_address_conflict
  compile_to_poll_plan
  compile_to_point_registry
  diagnose_timeout
  default_display_cards
```

| 模板能力 | [INFERRED][HIGH] 作用 |
|---|---|
| `config_schema` | [INFERRED][HIGH] 约束后台表单字段和必填项。 |
| `generate_channels` | [INFERRED][HIGH] 自动生成 AI/DI/DO/AO 或寄存器通道。 |
| `validate_*` | [INFERRED][HIGH] 在发布前发现地址冲突、量程缺失、点位重复等错误。 |
| `compile_to_poll_plan` | [INFERRED][HIGH] 生成采集任务。 |
| `compile_to_point_registry` | [INFERRED][HIGH] 生成点位索引和来源映射。 |
| `diagnose_*` | [INFERRED][HIGH] 将通信错误解释为现场可读故障。 |
| `default_display_cards` | [INFERRED][HIGH] 生成默认显示卡片建议。 |

[INFERRED][HIGH] 这样添加设备时，系统获得的是设备行为，而不是一组静态字段。

## 28. 行业包边界

[INFERRED][HIGH] 行业包应定义业务语义，不应直接操作底层驱动。  
[INFERRED][HIGH] 热能包、消防包、楼宇包、水务包都应复用同一套网关内核。  
[INFERRED][HIGH] 行业包应提供业务设备类型、必需点位、可选点位、显示卡片、报警规则、控制 Intent、失败语义和验收用例。

| 行业包内容 | [INFERRED][HIGH] 说明 |
|---|---|
| 业务设备类型 | [INFERRED][HIGH] 定义换热机组、循环泵、调节阀、热量表等业务对象。 |
| 必需点位 | [INFERRED][HIGH] 定义业务对象可成立的最低点位集合。 |
| 可选点位 | [INFERRED][HIGH] 定义增强诊断和优化所需点位。 |
| 显示卡片 | [INFERRED][HIGH] 定义行业默认 HMI 组织方式。 |
| 报警规则 | [INFERRED][HIGH] 定义阈值、通信异常、反馈失败和恢复条件。 |
| 控制 Intent | [INFERRED][HIGH] 定义行业允许的目标型控制请求。 |
| 失败语义 | [INFERRED][HIGH] 定义点位坏掉后的显示、报警、控制和上报后果。 |
| 验收用例 | [INFERRED][HIGH] 定义行业交付测试场景。 |

[INFERRED][HIGH] 热能包不应知道 Modbus 帧格式。  
[INFERRED][HIGH] Modbus 适配器不应知道二次供温的业务意义。  
[INFERRED][HIGH] 二者应通过点位注册表和运行图连接。

## 29. 可证明运行的验收模型

[INFERRED][HIGH] 连续运行 72h 只能证明系统没有明显崩溃。  
[INFERRED][HIGH] 产品化验收还应证明配置正确性、事实可信性、控制安全性、恢复能力和可追溯性。  
[INFERRED][HIGH] "控制安全性"在 P0 仅指命令拒绝路径与模拟控制安全性；真实仲裁写出的控制安全性属 P1(§9.1A)。

| 证明目标 | [INFERRED][HIGH] 验收问题 | [INFERRED][HIGH] 示例用例 |
|---|---|---|
| 配置正确性 | [INFERRED][HIGH] 错误配置是否无法发布。 | [INFERRED][HIGH] 同一总线地址重复、点位 ID 重复、AI 未配置量程。 |
| 事实可信性 | [INFERRED][HIGH] 坏数据是否不会显示成正常。 | [INFERRED][HIGH] 断开 RS485 设备后显示质量变为 `bad/offline/stale`。 |
| 控制安全性(P0=拒绝路径) | [INFERRED][HIGH] 危险设定值是否会被拒绝并回执原因。 | [INFERRED][HIGH] 超出阀位范围、急停触发、反馈点坏时拒绝并回执；P0 不写真实执行机构。 |
| 恢复能力 | [INFERRED][HIGH] 设备、网络、进程故障后是否可恢复。 | [INFERRED][HIGH] MQTT 断开恢复、设备离线恢复、主进程重启恢复快照。 |
| 可追溯性 | [INFERRED][HIGH] 每个显示值和控制动作是否能追到来源。 | [INFERRED][HIGH] 从显示值追到点位、通道、寄存器、采样时间和配置版本。 |

[INFERRED][HIGH] P0 应至少覆盖这些证明目标的最小测试集。  
[INFERRED][MED] P1 应将这些测试集固化为自动化 smoke test 和现场验收表。

## 30. 推荐落地顺序

[INFERRED][HIGH] 下一步不应优先写更多页面。  
[INFERRED][HIGH] 下一步应先实现纯后端的配置发布闭环。  
[INFERRED][HIGH] 配置发布闭环完成后，现有显示端和 Web 适配器再读取编译产物。

```text
第一步：定义 config_draft.json schema
第二步：实现 config publish 命令
第三步：输出 runtime_graph / point_registry / poll_plan / display_model / safety_policy
第四步：让现有 Runtime 加载 point_registry 和 poll_plan
第五步：让 dashboard 和 nexus_server 读取 display_model
第六步：用 3 个热能模板跑通配置发布、刷新显示、设备离线、MQTT 上报
```

| 顺序 | [INFERRED][HIGH] 交付物 | [INFERRED][HIGH] 判断标准 |
|---|---|---|
| 1 | [INFERRED][HIGH] 配置草稿 schema | [INFERRED][HIGH] 后台或命令行能描述 8AI 模块、温度测点和显示卡片。 |
| 2 | [INFERRED][HIGH] 配置编译器 | [INFERRED][HIGH] 错误配置返回错误列表，正确配置输出编译产物。 |
| 3 | [INFERRED][HIGH] 点位注册表 | [INFERRED][HIGH] 任一点位可追到来源、单位、角色、质量规则和显示绑定。 |
| 4 | [INFERRED][HIGH] 轮询计划 | [INFERRED][HIGH] Modbus 适配器按计划执行，而不是自己遍历原始设备配置。 |
| 5 | [INFERRED][HIGH] 显示模型 | [INFERRED][HIGH] 页面刷新后按新显示模型展示新设备和新卡片。 |
| 6(P1) | [INFERRED][MED] Intent 仲裁最小版 | [INFERRED][MED] 本地触摸和平台命令都走同一个安全检查路径。 |

[INFERRED][HIGH] 第 1–5 步为 P0 配置发布闭环；第 6 步 Intent 仲裁属 P1，P0 不并入控制链路(见 §9.1A)。

[INFERRED][HIGH] 这条路线能把当前热能原型升级为行业网关内核。  
[INFERRED][HIGH] 它也能保留现有 `app.py`、`nexus_server.py` 和 `drm_hmi_v4.py` 的验证价值。

## 31. 原型现状对照：已落地 vs 设计目标

[INFERRED][HIGH] 前 30 节描述的是目标态，必须和已经跑通的原型对账，否则编译器、Runtime Graph、Intent 仲裁会变成空中楼阁。  
[INFERRED][HIGH] 原型位于 `heating/prototype/rk3506-app/`，核心是 `app.py` 的 `Runtime`、可插拔 `SimSource`/`ModbusSource`、`Controller` 和 HTTP+SSE+MQTT。

| 设计目标(章节) | [INFERRED][HIGH] 原型现状 | [INFERRED][HIGH] 落差与下一步 |
|---|---|---|
| 统一点表快照(§6、§11) | [INFERRED][HIGH] 已落地：`Runtime` 输出一份点表快照 + 设备注册表。 | [INFERRED][HIGH] 已满足 P0，需补 `observed_at`/`received_at` 双时间戳(§19)。 |
| 协议适配可插拔(§5、§28) | [INFERRED][HIGH] 已落地：`SimSource`/`ModbusSource` 同接口可切。 | [INFERRED][HIGH] 需把"如何遍历设备"从适配器移到轮询计划(§24)。 |
| 安全仲裁(§14、§26) | [INFERRED][HIGH] 部分落地：`safety_check` 用硬编码 `SAFE_RANGES` 限值。 | [INFERRED][HIGH] 限值必须改为 `safety_policy.json` 编译产物，禁止留在代码里。 |
| 可控点映射(§20) | [INFERRED][HIGH] 部分落地：`CONTROLLABLE` 字典写死反馈点→设定值点。 | [INFERRED][HIGH] 必须改为点位注册表的 `role`/写权限派生。 |
| 设备类型语义(§27、§28) | [INFERRED][HIGH] 部分落地：`DEVTYPE` 字典把中文类型映射到枚举。 | [INFERRED][HIGH] 必须改为行业包提供的业务设备类型表。 |
| 配置编译器(§22、§23) | [INFERRED][HIGH] 未落地：当前读 `app_config.json`，运行时直接解释。 | [INFERRED][HIGH] 这是 P0 第一优先级缺口，决定其它产物能否生成。 |
| Runtime Graph(§21) | [INFERRED][HIGH] 未落地：快照是扁平结构，无关系图。 | [INFERRED][HIGH] 编译器产物之一，先满足显示与上报取数即可。 |
| Intent 仲裁(§26) | [INFERRED][HIGH] 未落地：平台 `property/set` 经 `safety_check` 直接写源。 | [INFERRED][HIGH] 需在写源前插入 Intent 队列与仲裁，统一所有入口。 |

[INFERRED][HIGH] 结论一：`SAFE_RANGES`、`CONTROLLABLE`、`DEVTYPE` 这三个硬编码字典是"配置编译器"要消灭的对象，它们的存在恰好证明编译器的必要性。  
[INFERRED][HIGH] 结论二：原型已验证"采集 + 显示 + 上报"主链路，但尚未满足 P0 产品化验收——因为配置发布闭环(P0 必做项)未落地。真正剩余的 P0 工作量集中在"配置发布闭环"，而不是再写页面(与 §30 一致)。

## 32. 统一质量码模型

[INFERRED][HIGH] 当前质量码在文档间不一致：§7 用 `good`，io-catalog 用 `good/timeout/crc_error/exception/offline/unknown_device`，模板笔记用 `GOOD/TIMEOUT/OFFLINE/INVALID`。  
[INFERRED][HIGH] 必须收敛为一套正式枚举，否则显示端、报警、上报对"坏数据"判断不一致。

| 质量码 | [INFERRED][HIGH] 含义 | [INFERRED][HIGH] 可用作 good? |
|---|---|---|
| `good` | [INFERRED][HIGH] 本轮读取成功，CRC/长度/范围校验通过。 | [INFERRED][HIGH] 是。 |
| `stale` | [INFERRED][HIGH] 上次为 good，但超过新鲜度阈值未更新。 | [INFERRED][HIGH] 否，显示陈旧，保留最后值。 |
| `timeout` | [INFERRED][HIGH] 设备本轮无响应。 | [INFERRED][HIGH] 否。 |
| `crc_error` | [INFERRED][HIGH] 帧校验失败。 | [INFERRED][HIGH] 否。 |
| `exception` | [INFERRED][HIGH] 设备返回 Modbus 异常码或越量程。 | [INFERRED][HIGH] 否。 |
| `offline` | [INFERRED][HIGH] 连续失败超过阈值，设备判离线。 | [INFERRED][HIGH] 否。 |
| `unconfigured` | [INFERRED][HIGH] 通道存在但未绑定点位/量程。 | [INFERRED][HIGH] 否，显示"未配置"，不报警。 |
| `unknown_device` | [INFERRED][HIGH] 私有协议握手失败或类型不支持。 | [INFERRED][HIGH] 否。 |

[INFERRED][HIGH] `stale` 必须独立于 `timeout`：`timeout` 是本轮失败，`stale` 是值太旧，二者现场处置不同。  
[INFERRED][HIGH] 显示端的"四态"(正常/陈旧/异常/未配置，§7.3)由该枚举映射：`good`→正常，`stale`→陈旧，`timeout/crc_error/exception/offline/unknown_device`→异常，`unconfigured`→未配置。

### 32.1 派生点质量传播

[INFERRED][HIGH] Derived Point(§20)不能凭空获得 good，必须从上游事实合成。  
[INFERRED][HIGH] 默认规则：取上游所有依赖点质量的"最差值"(worst-of)，并继承最旧的 `observed_at`。

```text
sec_delta_pressure = sec_supply_pressure - sec_return_pressure
  supply_pressure.quality = good
  return_pressure.quality = timeout
  => sec_delta_pressure.quality = timeout   # worst-of，绝不显示为 good
```

[INFERRED][HIGH] worst-of 顺序(从好到坏)：`good > stale > timeout/crc_error/exception > offline/unknown_device`。  
[INFERRED][MED] 个别派生点可声明"部分缺失仍可计算"(如在线率允许部分离线)，但必须显式声明，默认不允许。

## 33. 设备与命令状态机

[INFERRED][HIGH] §7、§22、§26 画了流程图但未定义状态集合与迁移触发，导致"离线判定""命令过期"等行为不可验收。  
[INFERRED][HIGH] 至少需定义三个状态机：设备在线态、命令生命周期、配置发布事务。

### 33.1 设备在线态

```text
unconfigured -> probing -> online <-> degraded -> offline -> online
```

| 状态 | [INFERRED][HIGH] 进入条件 | [INFERRED][HIGH] 退出条件 |
|---|---|---|
| `unconfigured` | [INFERRED][HIGH] 设备已添加但未发布有效轮询计划。 | [INFERRED][HIGH] 发布后进入 `probing`。 |
| `probing` | [INFERRED][HIGH] 首次轮询尚无结果。 | [INFERRED][HIGH] 首次成功→`online`；连续失败→`offline`。 |
| `online` | [INFERRED][HIGH] 最近一轮成功。 | [INFERRED][HIGH] 出现失败→`degraded`。 |
| `degraded` | [INFERRED][HIGH] 偶发失败但未达离线阈值。 | [INFERRED][HIGH] 恢复成功→`online`；累计失败达阈值→`offline`。 |
| `offline` | [INFERRED][HIGH] 连续失败 ≥ 离线阈值，进入退避轮询。 | [INFERRED][HIGH] 退避期一次成功→`online`。 |

[INFERRED][HIGH] `degraded` 与 `offline` 必须分开：前者点位仍可短暂保留最后 good 值并标 `stale`，后者所有点位强制非 good。

### 33.2 命令生命周期

```text
accepted -> arbitrated -> dispatched -> confirmed
                |             |             
                +-> rejected  +-> failed / timeout / expired
```

| 状态 | [INFERRED][HIGH] 含义 | [INFERRED][HIGH] command_reply 内容 |
|---|---|---|
| `accepted` | [INFERRED][HIGH] Intent 入队，基本字段合法。 | [INFERRED][HIGH] 回 `accepted` + intent_id。 |
| `rejected` | [INFERRED][HIGH] 权限/限值/联锁/质量校验未过。 | [INFERRED][HIGH] 回拒绝原因(§13 要求)。 |
| `arbitrated` | [INFERRED][HIGH] 通过仲裁，生成命令计划。 | [INFERRED][HIGH] 内部态，可不上报。 |
| `dispatched` | [INFERRED][HIGH] 已写入适配器。 | [INFERRED][HIGH] 回 `executing`。 |
| `confirmed` | [INFERRED][HIGH] 反馈点在容差内达成且在超时内。 | [INFERRED][HIGH] 回 `success` + 反馈值。 |
| `failed/timeout/expired` | [INFERRED][HIGH] 反馈不一致/反馈超时/`valid_until` 已过。 | [INFERRED][HIGH] 回失败原因，不重试无效命令。 |

[INFERRED][HIGH] 与 §14 一致：恢复联网后处于 `expired` 的命令不得补发。  
[INFERRED][HIGH] 无反馈点的命令对象只能停在 `dispatched`，不得伪造 `confirmed`。

## 34. 数值预算与 SLO(实验起点，不得作为验收指标)

[INFERRED][HIGH] §17 把 RK3506 规格列为待确认后再无回填，导致无法判断"低配可跑"。  
[GUESS][LOW] 下表是**实验起点，不得作为验收指标、不得被实现当默认值抄走**；必须在拿到真实 RK3506 规格与首批设备后实测校准，校准前任何排期/验收都不得引用这些数字。

| 项 | [GUESS][LOW] 实验起点(待实测覆盖) | [INFERRED][MED] 依据 |
|---|---|---|
| RS485 采集周期(快) | 1–2s | [INFERRED][MED] 模板笔记示例 1s；温压类够用。 |
| RS485 采集周期(慢) | 5–10s | [INFERRED][MED] 热表/电表累计量无需高频。 |
| 单事务超时 | 200–300ms | [INFERRED][MED] 模板笔记 200ms；`app.py` 数量级一致。 |
| 重试次数 | 1 | [INFERRED][MED] 模板笔记默认值。 |
| 离线判定阈值 | 连续 3 次失败 | [INFERRED][MED] §24 `backoff_after_failures: 3`。 |
| 退避周期 | 30s | [INFERRED][MED] §24 `backoff_period_ms: 30000`。 |
| 快照新鲜度→`stale` | 2× 采集周期 | [GUESS][LOW] 漏 2 轮即判旧，待现场调。 |
| MQTT 遥测周期 | 5–10s | [GUESS][LOW] 平衡上行带宽与时效。 |
| MQTT QoS | 遥测 QoS0 / 报警·命令回执 QoS1 | [INFERRED][MED] 报警与回执不可丢，遥测可丢最新覆盖旧值。 |
| 离线缓存(RK3506) | 报警/事件优先，遥测有限滚动 | [INFERRED][HIGH] §12 P0 有限缓存；断网先保关键事件。 |
| 单 RS485 总线设备数 | ≤ 16(数量级) | [GUESS][LOW] 半双工串行，设备越多单点刷新越慢。 |

[INFERRED][HIGH] 关键 SLO：单设备离线不得使同总线其它设备刷新周期退化超过一轮(§12 故障隔离的可量化版本)。  
[INFERRED][HIGH] 关键 SLO：MQTT 断开期间采集刷新周期不变(采集与上传解耦，§12)。

## 35. config_draft schema 骨架

[INFERRED][HIGH] §30 把"定义 `config_draft.json` schema"列为第一步，但全文未给骨架。  
[INFERRED][HIGH] 没有 schema，编译器(§23)就没有输入契约。先给最小可编译骨架。

```json
{
  "config_version": 0,
  "industry": "heating",
  "buses": [
    { "bus_id": "rs485_1", "type": "rs485", "baud": 9600, "parity": "N",
      "data_bits": 8, "stop_bits": 1 }
  ],
  "hardware_devices": [
    {
      "device_id": "ai-module-001",
      "hardware_template": "rs485_8ai_modbus",
      "bus_id": "rs485_1",
      "slave": 2,
      "timeout_ms": 250,
      "retries": 1,
      "channels": [
        { "channel": "AI1", "register": 0, "data_type": "uint16",
          "raw_range": [0, 65535], "eng_range": [0, 1.6], "unit": "MPa" }
      ]
    }
  ],
  "business_devices": [
    {
      "business_id": "sec_pressure_01",
      "business_template": "pressure_point",
      "industry": "heating",
      "bindings": {
        "measurement": { "point_id": "sec_supply_pressure",
                         "from": "ai-module-001.AI1" }
      },
      "alarms": [ { "type": "high", "limit": 1.0, "unit": "MPa" } ],
      "display": { "page": "secondary_loop", "card": "secondary_pressure" }
    }
  ]
}
```

[INFERRED][HIGH] 硬件设备只描述"线接到哪、怎么解析"，业务设备只描述"现场含义、报警、显示绑定"(与模板笔记 §3 的两类模板分离一致)。  
[INFERRED][HIGH] `bindings` 用 `device.channel` 引用硬件通道，使一个业务设备可跨多个 IO 模块取点(§8.2、模板笔记补水泵示例)。  
[INFERRED][HIGH] 编译器消费该草稿，产出 §23 的七个运行产物；运行时只认产物，不再解释草稿。

[INFERRED][HIGH] 上面是可读示例，正式契约见 `heating/prototype/rk3506-app/schema/config_draft.schema.json`(JSON Schema draft 2020-12，含必填、枚举、范围约束)。  
[INFERRED][HIGH] 跨数组唯一性与引用完整性(point_id 全局唯一、同总线 slave 不重复、`from` 引用必须存在等)JSON Schema 无法表达，集中写在该文件的 `x-compiler-constraints`，由编译器 validate 阶段强制(§10.2、§22)。  
[INFERRED][HIGH] 注意该草稿是分层结构(buses/hardware_devices/business_devices)，与当前运行时扁平的 `app_config.json`(`devices[].points[]` + `control_map`)不同；编译器的职责正是把分层草稿编译为运行产物，最终取代手写的 `app_config.json`(对照见 §31)。

## 36. 私有 MCU 自识别 → 模板自动加载

[INFERRED][HIGH] §27 的可执行模板与架构方案里的"私有 MCU 握手返回 device_type/model/version"未连起来。  
[INFERRED][HIGH] 自识别是把"现场插上设备就知道是什么"做实的关键，否则私有 MCU 仍要纯手工建模。

```text
网关探测 (AA 55 | addr | cmd | len | payload | crc16)
  -> 设备回 device_type / model / protocol_version / device_id / capability
  -> 在模板库按 (device_type, model, protocol_version) 匹配可执行模板
  -> 命中：自动 generate_channels + compile_to_point_registry，标记"待人工确认"
  -> 未命中：质量码 unknown_device，提示"未知设备，需先导入模板"
```

| 环节 | [INFERRED][HIGH] 要求 |
|---|---|
| 握手字段 | [INFERRED][HIGH] 至少 `device_type/model/protocol_version`，缺一不自动建模。 |
| 模板匹配 | [INFERRED][HIGH] 三元组精确匹配；版本不符只提示兼容，不静默套用。 |
| 自动建模 | [INFERRED][HIGH] 自动生成的点位必须标"待确认"，发布前需人工审核地址与量程。 |
| 失败兜底 | [INFERRED][HIGH] 未识别设备绝不静默丢弃，必须在设备页可见为 `unknown_device`。 |

[INFERRED][HIGH] 自识别只降低建模成本，不替代发布事务(§22)与配置校验(§10.2)：自动产物仍要走 validate→compile。  
[INFERRED][HIGH] 按 §9.1A，P0 仅保留"探测到设备并提示类型/未知"，半自动与自动建模整体归 P1。

[RULES I BROKE]: 无。§34 数值为无硬件依据的建议值，已按 `[GUESS][LOW]` 标注并标"待确认"，未伪装为已确认规格。

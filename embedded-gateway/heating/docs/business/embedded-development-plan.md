# Embedded Development Plan for Thermal Energy Co-controller

## 1. Confirmed Product Boundary

本项目的共控机面向换热站和小区供热系统，不是单个孤立热能设备控制器。

已确认边界：

- 控制对象：换热站 + 小区侧供热系统。
- 一次侧热媒：热水。
- 换热设备：板式换热器。
- 主通信协议：MQTT。
- 本地交互：需要本地屏幕。
- 远程能力：需要远程升级。
- 离线能力：需要断网自治运行。
- 控制优先级：安全优先，其次是稳定，再其次是节能和舒适。

仍需确认：

- 循环泵是定频还是变频。
- 是否一用一备、多泵并联或多泵轮换。
- 现场传感器类型和数量。
- 执行器类型：继电器、模拟量、485 变频器、以太网设备等。
- 本地屏幕是串口屏、Linux HMI、MCU 直连屏还是 Web HMI。
- MQTT 平台主题、报文格式、QoS、鉴权和离线缓存要求。

设备接入范围、常见协议和典型数据先按 `docs/business/controllable-industrial-devices.md` 管理，后续再沉淀为正式点表和驱动配置。

## 2. Development Objective

嵌入式软件目标不是只把设备“接起来”，而是让换热站在正常、异常、断网和人工干预场景下都能安全自治。

第一目标：

- 不超温。
- 不超压。
- 不缺水空转。
- 不因通信中断失控。
- 不因传感器异常做危险动作。

第二目标：

- 二次侧供水温度稳定。
- 二次侧供回水压差稳定。
- 补水动作可靠。
- 数据上报完整。
- 本地和远程参数一致。

第三目标：

- 节能优化。
- 泵阀寿命优化。
- 多泵轮换。
- 远程诊断。
- 运行策略持续调优。

## 3. Recommended System Architecture

```text
Sensors / Meters / Device Feedback
        |
        v
IO & Protocol Drivers
        |
        v
Data Validation and Filtering
        |
        v
Safety Protection Layer  <---- Local Emergency Input
        |
        v
State Machine
        |
        v
Control Algorithms
        |
        v
Device Command Layer
        |
        v
Valves / Pumps / VFD / Refill / Alarm Output

MQTT Platform <----> Communication Layer <----> Parameter & Data Model
Local Screen  <----> HMI Adapter         <----> Parameter & Data Model
OTA Service   <----> Upgrade Manager
```

建议把安全保护层放在控制算法之前。任何自动控制、远程指令、本地屏操作都必须先通过安全条件判断。

## 4. Software Module Split

### 4.1 Hardware Abstraction Layer

职责：

- 统一读取 AI、DI、温度传感器、压力传感器、流量计、热表。
- 统一控制 AO、DO、继电器、阀门、变频器。
- 屏蔽硬件差异，让上层只关心标准点位。

建议输出：

- `read_point(point_id)`
- `write_point(point_id, value)`
- `get_device_status(device_id)`
- `set_device_command(device_id, command)`

### 4.2 Point Table Module

职责：

- 管理所有测点和控制点。
- 定义点位名称、单位、量程、数据类型、报警阈值、采样周期。
- 支持本地屏和 MQTT 使用同一套数据模型。

关键点位：

- 一次侧供水温度、回水温度、压力、流量。
- 二次侧供水温度、回水温度、供水压力、回水压力、流量。
- 补水压力、水箱液位。
- 调节阀开度、阀门反馈。
- 循环泵运行、故障、频率、电流。
- 补水泵运行、故障。
- 本地/远程、手动/自动、通信状态。

### 4.3 Data Validation Module

职责：

- 过滤传感器噪声。
- 判断断线、短路、超量程、跳变过大。
- 标记数据质量：正常、可疑、故障、离线。

建议规则：

- 温度不能瞬间大幅跳变。
- 压力不能为负或超过物理上限。
- 泵已运行但流量/压差长期无变化，应判断循环异常。
- 阀门开度指令变化后反馈长期不变，应判断阀门卡滞或反馈异常。

### 4.4 Safety Protection Module

职责：

- 最高优先级处理超温、超压、低压、缺水、泵故障、传感器关键故障。
- 输出保护动作，不受普通自动控制覆盖。

保护动作示例：

- 二次侧供温过高：关闭或减小一次侧调节阀，循环泵延时运行散热。
- 二次侧压力过高：降低循环泵频率，停止补水，必要时泄压。
- 二次侧压力过低：启动补水，失败后停循环泵。
- 泵故障：停故障泵，若有备用泵则切换备用泵。
- 关键传感器故障：退出自动控制，进入降级或停机保护。

### 4.5 State Machine Module

建议状态：

- `POWER_ON`
- `SELF_CHECK`
- `STANDBY`
- `STARTING`
- `RUNNING`
- `ADJUSTING`
- `ALARM`
- `EMERGENCY_STOP`
- `MAINTENANCE`
- `OTA_UPDATING`

状态机要明确每个状态允许哪些动作。例如 OTA 升级时不应随意改变泵阀状态，急停状态下远程启动指令必须被拒绝。

### 4.6 Control Algorithm Module

第一阶段建议实现：

- 二次侧供水温度控制一次侧调节阀。
- 二次侧供回水压差控制循环泵。
- 二次侧低压控制补水。

后续可扩展：

- 室外温度补偿曲线。
- 分时段供热策略。
- 回水温度优化。
- 泵阀防频繁启停。
- PID 参数在线调整。

### 4.7 MQTT Communication Module

职责：

- 设备注册和鉴权。
- 实时数据上报。
- 告警上报。
- 事件上报。
- 参数下发。
- 远程控制指令。
- OTA 升级通知。

建议主题设计：

```text
station/{device_id}/telemetry
station/{device_id}/event
station/{device_id}/alarm
station/{device_id}/property/get
station/{device_id}/property/set
station/{device_id}/command
station/{device_id}/ota
station/{device_id}/heartbeat
```

建议所有远程控制指令都包含：

- `command_id`
- `timestamp`
- `operator`
- `command_type`
- `payload`
- `safety_policy`

设备执行后返回：

- 已接收。
- 已拒绝。
- 执行中。
- 执行成功。
- 执行失败。
- 被安全保护拦截。

### 4.8 Local HMI Module

本地屏建议包含：

- 系统总览。
- 一次侧参数。
- 二次侧参数。
- 泵阀状态。
- 当前模式。
- 告警列表。
- 参数设置。
- 手动控制。
- 通信状态。
- 升级状态。

本地屏权限建议分级：

- 观察员：只能查看。
- 运维员：可确认告警、切换模式、修改常规参数。
- 管理员：可修改保护阈值、通信参数、升级配置。

### 4.9 Offline Autonomy Module

断网后共控机必须继续运行。

断网策略：

- 保持最后一次有效参数。
- 本地自动控制继续执行。
- 远程控制不可用时，本地屏接管。
- 告警和运行数据进入本地缓存。
- 网络恢复后补传关键事件和告警。

必须避免：

- 因 MQTT 断线停止供热。
- 因平台不可达导致参数清空。
- 因重复下发历史指令导致设备误动作。

### 4.10 OTA Upgrade Module

远程升级建议采用双分区或可回滚机制。

升级流程：

1. 平台下发升级通知。
2. 设备检查版本、签名、电量/供电、运行状态。
3. 下载升级包。
4. 校验完整性和签名。
5. 写入备用分区。
6. 切换启动分区。
7. 启动后自检。
8. 成功则确认新版本，失败则回滚。

安全要求：

- 供热关键运行期间可限制升级窗口。
- 急停、严重告警时禁止升级。
- 升级失败不能影响安全保护逻辑。

## 5. Main Task Priority

### Phase 1: Minimal Safe Controller

目标：设备能安全上电、采集、显示、控制和保护。

任务：

- 建立点表。
- 实现 IO 驱动。
- 实现数据校验。
- 实现状态机。
- 实现基础安全保护。
- 实现本地手动/自动模式。
- 实现基础温度控制和补水控制。

### Phase 2: Station Control

目标：适配换热站实际运行。

任务：

- 实现板换相关点位。
- 实现一次侧阀门控制。
- 实现二次侧压差控制。
- 接入循环泵和补水泵。
- 接入本地屏。
- 完成启停顺序和联锁。

### Phase 3: MQTT Platform Integration

目标：支持远程监控和远程配置。

任务：

- MQTT 鉴权和心跳。
- 实时数据上报。
- 告警上报。
- 远程参数下发。
- 远程指令执行与回执。
- 断网缓存与恢复补传。

### Phase 4: OTA and Reliability

目标：支持远程升级和长期稳定运行。

任务：

- OTA 下载、校验、切换、回滚。
- 看门狗。
- 本地日志。
- 参数掉电保存。
- 异常重启恢复。
- 长稳测试。

### Phase 5: Optimization

目标：提升节能和运维效率。

任务：

- 室外温度补偿曲线。
- 分时段策略。
- 回水温度优化。
- 多泵轮换。
- 远程诊断。
- 控制参数自动调优。

## 6. Recommended Runtime Loop

```text
fast_loop_100ms:
    feed_watchdog()
    scan_emergency_inputs()
    update_critical_io()
    run_hard_protection()

main_loop_1s:
    read_all_points()
    validate_points()
    update_state_machine()
    run_safety_protection()
    run_control_algorithms()
    dispatch_device_commands()
    update_hmi_snapshot()

communication_loop_5s:
    mqtt_heartbeat()
    upload_telemetry()
    upload_alarms()
    process_remote_commands()

maintenance_loop_60s:
    persist_runtime_data()
    rotate_logs()
    check_ota_task()
    check_device_health()
```

## 7. Development Deliverables

建议后续逐步产出这些文件：

- `requirements.md`：需求规格说明。
- `point-table.xlsx`：点表。
- `state-machine.md`：状态机设计。
- `mqtt-protocol.md`：MQTT 主题和报文协议。
- `control-algorithm.md`：控制算法说明。
- `safety-rules.md`：安全保护规则。
- `hmi-pages.md`：本地屏页面设计。
- `ota-design.md`：远程升级设计。
- `test-plan.md`：嵌入式测试计划。

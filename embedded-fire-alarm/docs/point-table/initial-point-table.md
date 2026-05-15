# Initial Point Table

三层数据模型：**Device → Zone → Group**。所有运行时状态都以这三层为索引。

## Layer 1: Device

回路上的物理点位。每条回路最多 200 个 device（行业惯例，GB 4717 允许更高但很少超过 250）。

| Field | Type | Notes |
| --- | --- | --- |
| `loop_id` | u8 | 1-N，对应物理回路 |
| `addr` | u8 | 1-200，回路内地址 |
| `type` | enum | 详见 Device Types |
| `subtype_code` | u8 | 厂内子型号 |
| `state` | enum | NORMAL / ALARM / ACTION / FEEDBACK / FAULT / SHIELDED / UNREGISTERED |
| `value` | u16 | 模拟量（烟雾浓度、温度等，由 device 上报）|
| `threshold_alarm` | u16 | 报警阈值（厂内可调，受 GB 4717 限制）|
| `last_seen_tick` | u32 | 最近一次轮询响应时间 |
| `fault_flags` | u8 | bit0=open / bit1=short / bit2=timeout / bit3=invalid_response |
| `shielded` | bool | 屏蔽位（GB 4717 要求保留，需密码或钥匙开关解除）|
| `zone_id` | u16 | 所属防火分区 |

### Device Types

| Type | Examples | Triggers Alarm? | Drives Output? |
| --- | --- | --- | --- |
| `SMOKE_PHOTO` | 光电感烟探测器 | Y | N |
| `SMOKE_ION` | 离子感烟探测器（停产，仅维保）| Y | N |
| `HEAT_DIFF` | 差温探测器 | Y | N |
| `HEAT_FIX` | 定温探测器 | Y | N |
| `HEAT_COMBO` | 差定温组合 | Y | N |
| `FLAME_IR` | 红外火焰探测器 | Y | N |
| `GAS_CO` | CO 气体探测器 | Y | N |
| `GAS_FLAM` | 可燃气体探测器 | Y | N |
| `MANUAL_CALL` | 手动报警按钮 | Y（立即）| N |
| `HYDRANT_BTN` | 消火栓按钮 | Y | N |
| `MODULE_INPUT` | 输入模块（水流指示器、信号阀、压力开关）| Y/N（按配置）| N |
| `MODULE_OUTPUT` | 控制模块（驱动继电器）| N | Y |
| `MODULE_IO` | 输入输出模块 | Y | Y |
| `SOUNDER` | 声光警报器 | N | Y |
| `BROADCAST` | 消防广播终端 | N | Y |
| `PHONE` | 消防电话分机 | N | N |

## Layer 2: Zone (防火分区)

| Field | Type | Notes |
| --- | --- | --- |
| `zone_id` | u16 | |
| `name` | str | 工程命名（如 "1F-电梯前室"）|
| `device_count` | u16 | 区域内 device 数量 |
| `alarm_count` | u16 | 当前已确认报警的 device 数 |
| `first_alarm_at` | u32 | 第一个报警的时间戳 |
| `confirmed` | bool | 是否已满足"两点报警"的交叉确认 |
| `cross_confirm_threshold` | u8 | 默认 2，与 `config.alarm.cross_zone_confirm_count` 一致 |

## Layer 3: Group / Interlock Trigger

联动规则的逻辑分组。一个 group 内的 zones 都报警 → 触发该 group 关联的联动动作。

| Field | Type | Notes |
| --- | --- | --- |
| `group_id` | u16 | |
| `name` | str | 工程命名（如 "B1 车库消防联动组"）|
| `zone_list` | u16[] | 关联的 zone_id 集合 |
| `trigger_logic` | enum | ANY / ALL / N_OF_M |
| `interlock_actions` | action_t[] | 关联的联动设备 + 延时 |
| `state` | enum | IDLE / DELAYING / EXECUTING / DONE |

## Persistence

- **运行时**：SRAM 全表镜像。
- **快照**：每次配置变更后立即写 Flash，断电恢复用。
- **历史日志**：与 point table 分离，按时间序写入环形缓冲（≥10 000 条，GB 4717 强制）。

## Naming Convention

工程现场调试时，每个 device 必须有人类可读名（"3F-走道-东"），存储在外部工程数据库（CRT 端）或本机 ROM 区。device 名不参与逻辑判定，只用于显示与打印。

## Capacity Targets (Phase 1)

- 单主机 1 回路 × 200 device = 200 点
- Zone 数 ≤64
- Group 数 ≤32
- Action 总条目 ≤256

后续多回路时按比例扩展，Phase 2 目标：8 回路 × 200 = 1600 点。

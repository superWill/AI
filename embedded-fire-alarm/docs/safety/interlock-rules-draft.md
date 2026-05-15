# Interlock Rules Draft

联动控制矩阵。按 GB 50116-2013 第 4 章构建，单条规则由"触发条件 → 联动设备 + 延时"组成。

## Rule Priority

联动规则的优先级最高，**任何输入或屏蔽逻辑不可旁路**。包括：

- 手动屏蔽 SHIELD 命令不能阻止联动启动。
- "手动允许"状态下，人员可以**额外**启动联动设备；不可阻止已触发的自动联动。
- 远程 CRT 下发的复位命令在联动执行期间被拒绝；必须先完成或人工"复位授权"。

## Trigger Vocabulary

| Trigger | Definition |
| --- | --- |
| `SINGLE_ALARM(device)` | 单点报警（手动按钮 / 消火栓按钮 / 任一探测器）|
| `CROSS_ALARM(zone, N)` | 同一防火分区内 ≥ N 个探测器在窗口内报警（默认 N=2）|
| `MANUAL_START(device)` | 人员手动启动该联动设备 |
| `WATER_FLOW(detector)` | 水流指示器动作 |
| `PRESSURE_SWITCH(detector)` | 压力开关动作 |
| `GAS_RELEASE_SIGNAL` | 气体灭火启动信号 |

## Output Vocabulary

| Action | Output device class |
| --- | --- |
| `SOUND_LIGHT(zone)` | 声光警报器（按区域或全楼）|
| `BROADCAST(zone, clip)` | 消防广播（按疏散区域播放预录语音）|
| `DOOR_RELEASE(zone)` | 防火门释放器（常开门 → 关闭）|
| `SHUTTER_DESCEND(zone, stage)` | 防火卷帘下降（疏散通道分两段：1.8 m → 完全下降）|
| `ELEVATOR_RECALL` | 电梯迫降到首层 |
| `SMOKE_DAMPER_OPEN(zone)` | 排烟阀打开 |
| `AIR_DAMPER_OPEN(zone)` | 送风阀打开 |
| `SMOKE_FAN_ON(zone)` | 排烟风机启动 |
| `SUPPLY_FAN_ON(zone)` | 加压送风机启动 |
| `FIRE_PUMP_ON` | 消防水泵启动 |
| `SPRINKLER_PUMP_ON` | 喷淋泵启动（受水流指示器或压力开关触发）|
| `STABILIZE_PUMP_OFF` | 稳压泵停止 |
| `NON_FIRE_POWER_OFF(zone)` | 切除非消防电源 |
| `ALARM_GAS_RELEASE(zone)` | 气体灭火启动指令 |

## Rules (Phase 1 Subset)

### R1 - 全楼报警声光

| | |
| --- | --- |
| Trigger | `SINGLE_ALARM(manual_call OR hydrant_button)` 或 `CROSS_ALARM(any_zone, 2)` |
| Delay | 0 ms（立即）|
| Action | `SOUND_LIGHT(all_zones)` + `BROADCAST(all_zones, "evacuate")` |
| Source | GB 50116 § 4.8 |

### R2 - 防火门释放

| | |
| --- | --- |
| Trigger | `CROSS_ALARM(zone, 2)` 或 `SINGLE_ALARM(manual_call.in(zone))` |
| Delay | 0 ms |
| Action | `DOOR_RELEASE(zone)` |
| Source | GB 50116 § 4.6 |

### R3 - 防火卷帘下降（疏散通道）

| | |
| --- | --- |
| Trigger | `SINGLE_ALARM(smoke_detector.in(zone))` |
| Action stage 1 | `SHUTTER_DESCEND(zone, 1.8 m)`，延时 0 ms |
| Trigger | `SINGLE_ALARM(heat_detector.in(zone))` 或 stage 1 后 30 s |
| Action stage 2 | `SHUTTER_DESCEND(zone, full)` |
| Source | GB 50116 § 4.6.3 |

### R4 - 电梯迫降

| | |
| --- | --- |
| Trigger | `CROSS_ALARM(any_zone, 2)` 或 `SINGLE_ALARM(manual_call)` |
| Delay | 3000 ms（避免轿厢突停）|
| Action | `ELEVATOR_RECALL` |
| Feedback timeout | 60 s 内未收到 "已迫降首层" 反馈 → 故障上报，但**不**回滚动作 |
| Source | GB 50116 § 4.10 |

### R5 - 防排烟（按防烟分区独立判定）

| | |
| --- | --- |
| Trigger | `CROSS_ALARM(smoke_zone, 2)` |
| Delay (vents) | 5000 ms |
| Action | `SMOKE_DAMPER_OPEN(smoke_zone)` + `AIR_DAMPER_OPEN(adjacent_zones)` |
| Delay (fans) | 8000 ms |
| Action | `SMOKE_FAN_ON(smoke_zone)` + `SUPPLY_FAN_ON(adjacent_zones)` |
| Source | GB 50116 § 4.5 |

### R6 - 消防泵

| | |
| --- | --- |
| Trigger | `WATER_FLOW(detector)` 或 `PRESSURE_SWITCH(detector)` |
| Delay | 0 ms（直接启泵，本机不延时；硬接线优先）|
| Action | `SPRINKLER_PUMP_ON` 或 `FIRE_PUMP_ON` |
| Note | GB 50116 § 4.2.1 强制要求"硬接线"直启，本机软件矩阵作为冗余 |

### R7 - 非消防电源切除

| | |
| --- | --- |
| Trigger | `CROSS_ALARM(zone, 2)` |
| Delay | 0 ms |
| Action | `NON_FIRE_POWER_OFF(zone)` |
| Source | GB 50116 § 4.10.1 |

### R8 - 气体灭火（仅气体保护区）

| | |
| --- | --- |
| Trigger | `CROSS_ALARM(gas_protected_zone, 2 of which ≥1 smoke + ≥1 heat)` |
| Delay 1 | 0 ms：`SOUND_LIGHT(gas_zone)` + `BROADCAST(gas_zone, "people_evacuate_30s")` + 关闭所有通风设备 |
| Delay 2 | 30 s：`ALARM_GAS_RELEASE(gas_zone)`，但本机需先收到"延时按钮未被按下"确认 |
| Override | 现场紧急停止按钮 → 取消释放 |
| Source | GB 50116 § 4.4 |

## Execution Semantics

- 一条规则一旦触发，状态机进入 `DELAYING` → `EXECUTING` → `DONE` / `FAULT`。
- `DELAYING` 期间允许同优先级或更高优先级的新触发"提前执行"（合并）。
- `EXECUTING` 期间收到 STOP（手动 + 钥匙开关）→ 进入 `MANUAL_STOPPED`，记录日志，**仍上报 CRT**。
- 反馈超时 → 标记该 device 故障，规则状态仍记为 `DONE`（动作已下达）。
- 复位指令清除 `DONE` 状态，但**先决条件**：所有触发该规则的火警源已复位。

## Open Items

- 是否支持"延时取消"窗口？即在 stage 1 后人员按下"延时取消"按钮，是否允许撤回？规范不强制，工程上有争议。
- 多规则同时触发同一设备时的合并策略：当前用"最先 wins" + 后续触发刷新状态，但不重启执行。需要工程现场验证。
- 矩阵编辑：是否允许 CRT 在线编辑规则？目前倾向 NO —— 仅允许在工程调试 PC 工具上编辑后批量下发，避免运行时被人误改。

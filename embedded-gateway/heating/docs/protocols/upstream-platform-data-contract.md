# 面向优化平台的数据接口契约（草案）

> 用途：定义本网关与上游"优化平台"之间的数据接口——上送点表、采样频率、时间戳与质量码规范、以及接收平台下发设定值并回传执行结果的协议。
> 版本：2026-06-02（草案）
> 关联：[数据缺口与补位策略](../business/upstream-platform-data-gap-filling.md) · [MQTT 协议草案](mqtt-protocol-draft.md) · [初始点表](../point-table/initial-point-table.md) · [控制逻辑](../business/thermal-energy-co-controller-logic.md)

## 0. 设计原则

本契约直接服务于[补位策略](../business/upstream-platform-data-gap-filling.md)中的五大缺口，三条硬约束贯穿始终：

1. **每个数据点必带时间戳 + 质量码**——解决平台"数据不同步、不可信"的命门（缺口②）。
2. **执行闭环**——平台下发设定值，网关执行并回传实际结果，不做开环（缺口④）。
3. **断网无洞**——网关本地缓存、恢复后补传，平台时间序列连续（缺口⑤）。

传输沿用现有 [MQTT 协议草案](mqtt-protocol-draft.md) 的 topic 与命令应答模型，本契约只做面向平台的扩展约定。

## 1. Topic 约定（扩展自 MQTT 草案）

| 方向 | Topic | 用途 |
|---|---|---|
| 上行 | `station/{device_id}/telemetry` | 周期遥测（带时间戳+质量码） |
| 上行 | `station/{device_id}/event` | 事件驱动上报（状态突变、快变） |
| 上行 | `station/{device_id}/alarm` | 报警（泵故障、超温超压、补水激增） |
| 下行 | `station/{device_id}/property/set` | 平台下发设定值 |
| 上行 | `station/{device_id}/command_reply` | 设定值执行结果回传 |
| 上行 | `station/{device_id}/heartbeat` | 在线心跳 |

`{device_id}` 唯一标识一个站点/网关，平台据此拼装拓扑。

## 2. 时间戳与质量码规范（核心）

### 2.1 时间戳

- 统一 **Unix 毫秒**（UTC），字段 `ts`。
- 网关本地需 **NTP/PPS 时间同步**；同步状态作为整帧元数据 `clock_sync` 上报（`synced` / `holdover` / `unsynced`）。
- **同一帧 telemetry 内所有点共享同一采样时刻**，保证平台水力计算拿到的是"同一时刻快照"，而非错位拼接。

### 2.2 质量码 `q`

| 值 | 含义 | 平台处理建议 |
|---|---|---|
| `good` | 正常有效 | 直接采信 |
| `stale` | 超过刷新周期未更新 | 降权/标记陈旧 |
| `bad` | 传感器故障/超量程/断线 | 剔除，触发数据缺失逻辑 |
| `est` | 网关估计值（插值/模型补） | 仅作参考，不入训练真值 |
| `manual` | 人工置数（调试/检修） | 排除出自动建模 |

> 没有质量码的数据对数字孪生是污染源。本契约强制每点带 `q`。

## 3. 上行遥测报文

```json
{
  "device_id": "stn-001",
  "ts": 1717286400000,
  "clock_sync": "synced",
  "seq": 84213,
  "points": {
    "pri_supply_temp":  { "v": 78.4, "q": "good" },
    "pri_return_temp":  { "v": 45.1, "q": "good" },
    "pri_flow":         { "v": 32.7, "q": "good" },
    "pri_valve_feedback": { "v": 61.0, "q": "good" },
    "sec_supply_temp":  { "v": 52.3, "q": "good" },
    "sec_return_temp":  { "v": 41.8, "q": "good" },
    "sec_flow":         { "v": 88.2, "q": "good" },
    "circ_pump_freq_fb": { "v": 38.5, "q": "good" },
    "refill_pressure":  { "v": 0.32, "q": "good" },
    "outdoor_temp":     { "v": -3.2, "q": "good" }
  }
}
```

- `seq`：单调递增序号，平台据此识别丢帧/补传。
- 补传帧带原始 `ts`（采样时刻，非补发时刻）+ 标志 `replay: true`。

## 4. 采样与上送频率

> 原则：快环本地跑，平台按其建模需要的粒度取；不为上送而牺牲本地控制实时性。

| 数据类 | 本地采样 | 上送平台 | 说明 |
|---|---|---|---|
| 温度（供回温、室外温、室温） | 1 s | 30~60 s | 慢变量，平台建模足够 |
| 压力 | 1 s | 10~30 s | 水力计算需较密 |
| 流量 / 热量 | 1 s | 30~60 s | 累积量另报累计值 |
| 阀位 / 泵频 反馈 | 1 s | 变化上报 + 60 s 心跳 | 执行状态 |
| 事件 / 报警 | 实时 | **即时**（event/alarm） | 不等周期 |
| 室温（荷侧） | 1~5 min | 5~10 min | 无线节点，节电 |

水力计算需"同步快照"时，平台可通过 `property/set` 临时调高压力/流量上送频率。

## 5. 补位点表（在初始点表基础上新增的荷侧/质量字段）

> 复用[初始点表](../point-table/initial-point-table.md)的 `point_id`；以下为面向平台补位、原表未覆盖的部分（缺口①荷侧）。

| Point ID | 名称 | 单位 | 类型 | 平台用途 |
|---|---|---|---|---|
| `bldg_inlet_supply_temp` | 楼栋入口供水温度 | degC | AI | 二次网平衡、过/欠供识别 |
| `bldg_inlet_return_temp` | 楼栋入口回水温度 | degC | AI | 同上 |
| `bldg_inlet_flow` | 楼栋入口流量 | m3/h | AI/Meter | 楼栋级负荷分配 |
| `bldg_heat_meter` | 楼栋热量表累计 | GJ | Meter | 负荷预测真值 |
| `room_temp_{n}` | 抽样户室温 #n | degC | AI/Wireless | **负荷预测核心需求信号** |
| `heat_total` | 站级累计供热量 | GJ | Meter | 负荷预测/考核 |

## 6. 下行设定值与执行回传（闭环）

### 6.1 平台下发设定值（`property/set`）

```json
{
  "command_id": "set-20260602-001",
  "ts": 1717286400000,
  "operator": "platform",
  "command_type": "set_point",
  "payload": {
    "sec_supply_temp_target": 50.0,
    "valid_until": 1717290000000
  }
}
```

- 网关将平台设定值作为**本地气候补偿+PID 的目标值**，由本地闭环执行——平台给"要什么"，网关决定"怎么拧"。
- `valid_until`：设定值有效期；超期网关回退到本地默认策略（防平台失联后跑飞）。
- **安全优先**：任何下发若与安全联锁/限值冲突，网关拒绝并回 `blocked_by_safety`，绝不越过本地安全分层。

### 6.2 网关回传执行结果（`command_reply`）

```json
{
  "command_id": "set-20260602-001",
  "ts": 1717286480000,
  "status": "success",
  "achieved": {
    "sec_supply_temp": 49.8,
    "pri_valve_feedback": 58.5
  },
  "reason": ""
}
```

`status` 取值沿用 MQTT 草案：`accepted` / `rejected` / `running` / `success` / `failed` / `blocked_by_safety`。

`achieved` 回传**实际达到值**，把"建议→执行"闭成可验证的环——这是平台单靠 DCS/SCADA 拿不到的。

## 7. 断网与补传（缺口⑤）

- 断网期间网关本地缓存遥测（环形缓冲，容量见非功能要求）。
- 恢复后按 `seq` 顺序补传，帧标 `replay: true` 且保留原始 `ts`。
- 平台据 `seq` 连续性判断是否仍有缺口并请求重传。

## 8. 安全边界（与控制逻辑一致）

> 平台是**顾问/优化角色，不是安全角色**。安全分层 `机械 > 硬接线 > MCU > RK` 不因接入平台而改变。

- 平台只能下发**设定值/目标值**，不能直接驱动执行器，更不能绕过 MCU/机械安全。
- 平台失联 → 网关按本地策略自治，不依赖平台维持安全。
- 所有下发经本地限值与联锁校验，冲突即拒绝并回传原因。

## 9. 待定 / 下一步

- `device_id` 与站点拓扑编码规范（与平台对齐命名）。
- 累计量（热量/水量）的累计值 vs 增量上报方式二选一。
- 认证与加密（MQTT TLS + 设备证书）细化。
- 本地缓存容量与补传节流参数（接非功能要求/硬件选型）。

# Device Presence and Data Flow

> 状态：设计草案  
> 场景：设备插入后自动进入本地 HMI 设备列表；设备拔出后不删除历史配置，而是置灰显示；采集数据持续刷新到 HMI，并通过 MQTT 上报平台。

## 1. 核心原则

设备接入状态和设备业务数据要分开处理：

```text
设备接入状态：有没有插入、链路是否存在、系统是否识别出 /dev 节点
设备业务数据：温度、压力、流量、泵状态、热量、电流、故障码
```

插拔事件只决定设备是否在线、是否显示为灰色，不直接触发控制输出。控制输出仍必须经过状态机和安全保护层。

## 2. 设备状态模型

设备列表建议保留设备记录，不因拔出而删除。

```json
{
  "id": "dev-001",
  "name": "1号热表",
  "type": "热表",
  "address": "1",
  "interface_kind": "serial",
  "interface_name": "ttyUSB0",
  "status": "online",
  "last_seen_at": 1799900000,
  "last_data_at": 1799900000,
  "quality": "good"
}
```

字段说明：

| 字段 | 示例 | 说明 |
|---|---|---|
| `interface_kind` | `ethernet` / `serial` / `usb` / `can` | 设备接入类型 |
| `interface_name` | `eth0` / `ttyUSB0` / `can0` | Linux 侧接口名 |
| `status` | `online` / `offline` / `fault` | HMI 列表状态 |
| `last_seen_at` | Unix 时间戳 | 最近一次插入或心跳时间 |
| `last_data_at` | Unix 时间戳 | 最近一次有效业务数据时间 |
| `quality` | `good` / `stale` / `bad` | 点位质量 |

## 3. 插入与拔出流程

### 插入

```text
udev / netlink 发现设备
        |
        v
生成 interface_event(action=add)
        |
        v
识别设备类型与接口名
        |
        v
设备注册表 upsert
        |
        v
HMI 设备列表新增或恢复在线
        |
        v
采集调度器开始轮询该设备
```

HMI 行为：

- 新设备：加入设备列表，显示“在线 / 已接入”。
- 已存在设备：从灰色恢复正常，更新时间。
- 不能识别的 USB：只显示接口事件，不自动加入业务设备列表，等待人工绑定。

### 拔出

```text
udev / netlink 发现 remove 或 carrier=0
        |
        v
生成 interface_event(action=remove)
        |
        v
设备注册表 status=offline
        |
        v
采集调度器停止轮询或标记超时
        |
        v
HMI 对应设备置灰，保留最后一次数据
```

HMI 行为：

- 设备卡片置灰。
- 当前值保留最后一次有效值。
- 点位质量显示“离线”。
- 当前设备状态显示“离线”。
- 不自动删除设备配置。

## 4. Linux 侧监听方式

| 设备类型 | 监听方式 | 业务确认 |
|---|---|---|
| 网口 / 网线 | `NETLINK_ROUTE` 监听 `RTM_NEWLINK` | `/sys/class/net/eth0/carrier` |
| USB 串口 | `udev` 或 `NETLINK_KOBJECT_UEVENT` | `/dev/ttyUSB*` / `/dev/ttyACM*` |
| U 盘 | `udev` block 事件 | `/dev/sd*` / `lsblk` |
| CAN | `ip link` / netlink | `can0` 是否 up |
| RS485 仪表 | 串口存在 + Modbus 读寄存器成功 | 设备地址响应 |

网口 carrier=1 只代表物理链路建立，不代表业务设备可用。业务设备可用必须由采集驱动确认。

## 5. 数据采集链路

```text
Physical Device
        |
        v
Driver Adapter
  - AI / DI
  - Modbus RTU
  - Modbus TCP
  - CAN
  - MQTT Local
        |
        v
Point Table
        |
        v
Validation / Quality
        |
        v
Runtime Snapshot
        |
        +--> WebSocket -> HMI
        |
        +--> MQTT -> Cloud Platform
        |
        +--> Local Log / Ring Buffer
```

## 6. 本地 HMI 传输

嵌入式 Web HMI 推荐使用 WebSocket。HTTP 只用于首屏加载和历史查询。

### 设备事件消息

```json
{
  "type": "device_event",
  "kind": "serial",
  "action": "add",
  "name": "ttyUSB0",
  "device_name": "1号热表",
  "device_code": "HM-001",
  "address": "1",
  "detail": "检测到 USB 串口 ttyUSB0，已加入设备列表",
  "timestamp": 1799900000
}
```

### 设备离线消息

```json
{
  "type": "device_event",
  "kind": "serial",
  "action": "remove",
  "name": "ttyUSB0",
  "detail": "USB 串口 ttyUSB0 已移除，关联设备置为离线",
  "timestamp": 1799900060
}
```

### 快照消息

```json
{
  "type": "snapshot",
  "device_id": "HM-001",
  "status": "online",
  "timestamp": 1799900010,
  "points": [
    {
      "point_id": "supply_temp",
      "name": "供水温度",
      "value": 72.4,
      "unit": "degC",
      "quality": "good",
      "updated_at": 1799900010
    }
  ]
}
```

HMI 原型已经暴露两个入口：

```js
window.tecPushInterfaceEvent({
  kind: "serial",
  action: "add",
  name: "ttyUSB0",
  detail: "检测到 USB 串口 ttyUSB0，已加入设备列表"
});

window.tecPushDeviceEvent({
  kind: "serial",
  action: "remove",
  name: "ttyUSB0",
  detail: "USB 串口 ttyUSB0 已移除，关联设备置为离线"
});
```

真实后端接入时，把 WebSocket 消息转换为上述函数调用即可。

## 7. 云端 MQTT 传输

MQTT 不负责本地插拔显示的实时性，主要用于云端可见性和远程运维。

推荐 topic：

```text
station/{station_id}/device/{device_id}/telemetry
station/{station_id}/device/{device_id}/event
station/{station_id}/device/{device_id}/alarm
station/{station_id}/heartbeat
```

设备插入：

```json
{
  "event": "device_online",
  "device_id": "HM-001",
  "interface": "ttyUSB0",
  "timestamp": 1799900000
}
```

设备拔出：

```json
{
  "event": "device_offline",
  "device_id": "HM-001",
  "interface": "ttyUSB0",
  "reason": "udev_remove",
  "timestamp": 1799900060
}
```

## 8. 超时兜底

不能只依赖 remove 事件。工业现场可能出现设备无响应但接口仍存在的情况。

建议规则：

| 条件 | 状态 |
|---|---|
| 接口存在，连续 3 次读取成功 | `online` |
| 接口存在，连续 3 次读取失败 | `fault` 或 `stale` |
| 接口 remove / carrier=0 | `offline` |
| 超过 3 个采样周期无新数据 | 点位质量 `stale` |

## 9. MVP 实施顺序

1. HMI 设备卡支持 `online/offline` 两种状态。
2. 后端提供 `/api/devices` 查询当前设备注册表。
3. 后端提供 WebSocket `/ws/events` 推送 `device_event` 和 `snapshot`。
4. Linux 侧先实现 udev 串口插拔监听。
5. 再实现 netlink 网线 carrier 监听。
6. 最后接 Modbus/AI/DI/CAN 的真实采集驱动。

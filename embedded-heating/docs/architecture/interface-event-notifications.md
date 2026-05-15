# Interface Event Notifications

> 状态：设计草案  
> 场景：热能控制系统检测网线、USB、串口等设备接入，并在本地 HMI 提示。  
> 目标：设备插入/拔出后，控制程序能收到事件，HMI 能提示运维人员。

## 1. 事件来源

在嵌入式 Linux 上，设备插拔不是读普通业务点位，而是监听系统事件：

| 类型 | 推荐监听方式 | 兜底读取 |
|---|---|---|
| 网线插入/拔出 | `NETLINK_ROUTE` / `RTM_NEWLINK` | `/sys/class/net/<ifname>/carrier` |
| USB 插入/拔出 | `udev` 或 `NETLINK_KOBJECT_UEVENT` | `/sys/bus/usb/devices` |
| USB 串口 | `udev`，匹配 `ttyUSB*` / `ttyACM*` | `/dev/ttyUSB*`、`/dev/ttyACM*` |
| U 盘 | `udev`，匹配 `block` | `/dev/sd*`、`lsblk` |

## 2. 统一事件模型

控制层不应该把 netlink / udev 原始字段直接丢给 HMI，建议转换成统一事件：

```json
{
  "type": "interface_event",
  "kind": "ethernet",
  "action": "add",
  "name": "eth1",
  "detail": "检测到网线插入，链路已建立",
  "severity": "info",
  "timestamp": "2026-05-15 11:58:00"
}
```

字段说明：

| 字段 | 示例 | 说明 |
|---|---|---|
| `kind` | `ethernet` / `usb` / `serial` / `storage` | 接口类型 |
| `action` | `add` / `remove` / `change` | 接入、移除、状态变化 |
| `name` | `eth1` / `ttyUSB0` / `sda1` | 设备名 |
| `detail` | `检测到 USB 设备插入` | 给 HMI 展示的文本 |
| `severity` | `info` / `warn` / `danger` | 提示等级 |

## 3. 控制层处理原则

接口事件只负责提示和状态更新，不应直接绕过安全控制。

推荐顺序：

```text
系统事件监听
        |
        v
事件归一化
        |
        v
写入事件队列 / 日志
        |
        v
更新接口状态缓存
        |
        v
WebSocket 推送 HMI
        |
        v
HMI 弹出提示 + 最近事件列表
```

## 4. 热能控制里的建议模块

```text
backend/
  app/
    core/
      interface_events.py       # 事件模型、队列、推送
    services/
      netlink_watcher.py        # 网线插拔监听
      udev_watcher.py           # USB/串口/U盘监听
    api/
      interface_events.py       # 最近事件查询
```

如果控制主程序是 C/C++，建议分成：

```text
interface_event.h
interface_event_linux.c
interface_event_queue.c
hmi_event_publisher.c
```

## 5. HMI 展示方式

当前原型已加入：

- 侧边栏“接口事件”列表。
- 右下角接入提示浮层。
- `window.tecPushInterfaceEvent(event)` 原型接口。

前端可接收如下事件：

```js
window.tecPushInterfaceEvent({
  kind: "ethernet",
  action: "add",
  name: "eth1",
  detail: "检测到网线插入，链路已建立"
});
```

或：

```js
window.dispatchEvent(new CustomEvent("tec-interface-event", {
  detail: {
    kind: "usb",
    action: "add",
    name: "ttyUSB0",
    detail: "检测到 USB 串口设备插入"
  }
}));
```

后续接真实后端时，把 WebSocket 消息转成同样的事件即可。

## 6. 典型提示文案

| 事件 | 文案 |
|---|---|
| 网线插入 | `检测到 eth1 网线插入，链路已建立` |
| 网线拔出 | `检测到 eth1 网线断开，请检查网络连接` |
| USB 插入 | `检测到 USB 设备插入，等待识别设备类型` |
| USB 串口 | `检测到 USB 串口 ttyUSB0，可用于仪表调试` |
| U 盘 | `检测到存储设备 sda1，可导入/导出配置` |
| USB 移除 | `USB 设备已移除` |

## 7. 注意事项

1. 网线插入不等于网络可用，只代表物理链路建立。
2. USB 插入不等于业务设备可用，还要看驱动是否生成 `/dev/ttyUSB0`、`/dev/sdX` 等节点。
3. 事件提示不要触发控制输出；控制输出仍必须走状态机和安全保护层。
4. 离线设备不能依赖临时安装 `pyudev` / `pyroute2`，需要把依赖打入发布包，或用 C 直接监听 netlink。
5. 事件需要限流，避免网线抖动或 USB 接触不良导致 HMI 被刷屏。

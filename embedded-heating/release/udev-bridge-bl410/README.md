# udev → HMI Event Bridge (BL410)

把 BL410 Linux 上的真实 udev 事件（USB / 串口 / 网线插拔）通过 SSE
推给 HMI，让 prototype 设备列表能即时显示真插入 / 拔出。

## 拓扑

```text
USB / 网线插拔
        │
        ▼  udevadm monitor --property --udev
udev_bridge.py  ──HTTP/SSE──▶  Browser HMI
  :8765/events                  EventSource('/events')
  :8765/health                  → tecPushInterfaceEvent()
```

## 部署

```bash
cd /tmp/udev-bridge-bl410
chmod +x install.sh uninstall.sh
sudo ./install.sh
```

安装后：

- 脚本: `/opt/udev-bridge/udev_bridge.py`
- 服务: `/etc/systemd/system/udev-bridge.service`
- 端口: `0.0.0.0:8765`

## 验证

设备本机：

```bash
curl http://127.0.0.1:8765/health
# {"ok": true, "clients": 0}

# 一窗口订阅事件流
curl -N http://127.0.0.1:8765/events
# 另一窗口插拔 USB / 网线，应该看到 data: {...} 实时输出

journalctl -u udev-bridge -f
```

从开发机（同网段）：

```bash
curl http://192.168.1.110:8765/health
```

## 卸载

```bash
sudo ./uninstall.sh
```

## 事件 schema

推给 HMI 的 device_event JSON：

| 字段 | 类型 | 含义 |
|---|---|---|
| `kind` | `serial` / `ethernet` / `usb` | 接口类别 |
| `action` | `add` / `remove` | 事件方向 |
| `name` | str | 接口名（`ttyUSB0` / `eth0` / 设备路径）|
| `deviceName` | str | 给 HMI 显示的可读名 |
| `deviceCode` | str | `VendorID:ProductID` 或接口名 |
| `detail` | str | HMI 提示语 |
| `timestamp` | float | Unix epoch（秒）|

对应 prototype HMI 的 `window.tecPushInterfaceEvent(event)` 接口。

## 设计选型

- **SSE 不是 WebSocket**：单向推送够用，浏览器端 EventSource 自动重连
- **零外部依赖**：只用 Python 标准库 + `udevadm monitor` 子进程；不需要 `pip install` 任何包，离线设备友好
- **broadcast-fanout**：每个连进来的 SSE 客户端有独立 queue，互不影响

## 与 release / prototype HMI 的关系

| 服务 | 端口 | 跟本桥的关系 |
|---|---|---|
| release HMI（完整版）| 8092 | 不消费 SSE（旧版没接）|
| **prototype HMI**（设备插拔版）| **8094** | **消费 SSE，自动响应** |
| **本桥** | **8765** | 数据源 |

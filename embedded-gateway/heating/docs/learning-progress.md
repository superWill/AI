# 嵌入式学习进度

> 目标:围绕 RK3506 供热网关,按"能看懂现场、能调通设备、能守住稳定和安全"推进。

## 当前进度

当前学到: **3. RS485 / Modbus RTU 与私有 MCU 协议**,正在推进 **4. RK3506 应用 + 104 设备模拟**。

当前目标不是继续扩展 BLE,而是在 RK3506 上做一个实际运行的供热网关应用:104 机器模拟各种现场设备,RK3506 采集、做点表、判断质量码,再把数据呈现到本地 LCD。

## 学习路线

| 阶段 | 状态 | 要掌握什么 | 本项目落点 |
|---|---|---|---|
| 0. 项目全局认知 | 已完成 | RK3506 网关、MCU/HMI/MQTT/断网自治、安全优先的整体关系 | `docs/embedded-learning-mindmap.md` |
| 1. 嵌入式通信分层 | 已完成 | 应用协议层、芯片外设层、电气接口层、物理接线层的区别 | 能区分 Modbus、UART、RS485、A/B 接线 |
| 2. RK3506 蓝牙与串口验证 | 已完成 | BLE Central/Peripheral、GATT RX/TX、串口日志、227 作为调试机 | `prototype/rk3506-bringup/README.md` |
| 3. RS485 / Modbus RTU 与私有 MCU 协议 | 进行中 | 主从轮询、帧格式、功能码、CRC、异常码、超时、设备类型识别 | `docs/protocols/fieldbus-modbus-rs485-basics.md`, `docs/protocols/private-mcu-device-identification.md` |
| 4. RK3506 应用 + 104 设备模拟 | 进行中 | 模拟设备清单、点表映射、LCD 展示、故障注入 | `docs/architecture/rk3506-104-simulator-application-plan.md` |
| 5. 现场设备与 IO 点表 | 进行中 | 设备表、点表、状态表、设备模板、DI/DO/AI/AO、量程换算、App 添加设备 | `docs/point-table/point-table-learning-notes.md`, `docs/point-table/device-template-design-notes.md`, `../../docs/field-device-io-catalog.md` |
| 6. 采集可靠性 | 待学 | 轮询周期、超时、重试、离线判断、质量码、断线恢复 | `docs/architecture/gateway-reliability-and-performance.md` |
| 7. 本地 HMI 和 MQTT | 待学 | 本地显示、遥测上报、断网缓存、补传 | `prototype/hmi/`, `prototype/cloud-gateway-mqtt/` |
| 8. 控制与安全联锁 | 待学 | 限幅、互锁、回读确认、失联回退、人工接管 | `docs/safety/safety-rules-draft.md` |

## 当前阶段任务

### 3.1 先记住分层

- Modbus RTU 是协议层:规定地址、功能码、寄存器、CRC。
- UART 是芯片外设层:负责收发字节。
- RS485 是电气接口层:负责远距离差分传输。
- A/B 双绞线是物理接线层:现场最容易接错。

### 3.2 看懂一帧 Modbus RTU

先掌握读保持寄存器:

```text
01 03 00 00 00 02 C4 0B
```

- `01`:从站地址。
- `03`:读保持寄存器。
- `00 00`:起始寄存器。
- `00 02`:读取 2 个寄存器。
- `C4 0B`:CRC16,低字节在前。

### 3.3 必须带着安全和稳定去学

- 没有响应就是超时,不能卡死主循环。
- CRC 错就丢弃,不能当有效数据。
- 异常响应要识别,不能当普通数据解析。
- 连续失败要给质量码,设备状态要变离线。
- 写控制寄存器前必须限幅、互锁,写后要回读确认。

## 下一次学习建议

1. 跑 `modbus_demo.py`,对照帧格式拆每个字节。
2. 手写一次读取从站 `1` 的 2 个保持寄存器请求。
3. 看懂 `0x03` 正常响应和 `0x83` 异常响应。
4. 再进入真实串口或 USB-RS485 调试。

# RK3506 + 104 设备模拟应用方案

> 目标:在 RK3506 上做一个可实际运行的供热网关应用,由 104 机器通过 USB-TTL/串口模拟各种现场设备,数据最终显示到 RK3506 本地 LCD,后续再上 MQTT。

## 当前硬件拓扑

```text
104 机器
  /dev/ttyUSB1
  modbus_sim.py / 私有协议模拟器
        |
        | TTL 串口线: TX/RX 交叉 + GND 共地
        v
RK3506
  /dev/ttyS1
  采集服务 + 点表 + LCD HMI
  /dev/dri/card0 直写 800x480 屏幕
```

当前已跑通链路:

- 104: `python3 -u /tmp/modbus_sim.py /dev/ttyUSB1 /tmp/sim_config.json`
- RK3506: `python3 /userdata/energy-hmi/drm_hmi.py /dev/ttyS1`
- LCD 当前读取从站 `1` 的温湿度和从站 `2` 的电压。

## 应用模块清单

| 模块 | 运行位置 | 职责 | 当前文件 |
|---|---|---|---|
| 设备模拟器 | 104 | 模拟热表、电表、坏表、后续扩展泵阀/安全 IO | `prototype/rk3506-bringup/modbus_sim.py` |
| 采集层 | RK3506 | 按协议轮询设备,处理超时/CRC/异常 | `prototype/rk3506-bringup/gateway.py` |
| 点表层 | RK3506 | 把寄存器或私有 payload 映射成统一点位 | `prototype/rk3506-bringup/gateway_config.json` |
| 本地 LCD | RK3506 | 显示关键点位、通信状态、告警 | `prototype/rk3506-bringup/drm_hmi.py` |
| Web HMI | RK3506 | 浏览器访问版本,用于调试或外接浏览器 | `release/energy-hmi-rk3506/` |
| MQTT 上传 | RK3506 | 后续把点表快照上报平台,断网缓存补传 | `prototype/cloud-gateway-mqtt/` |

## 104 要模拟的设备

第一阶段先用 Modbus RTU 模拟。每个设备有地址、类型、点位、故障状态。

| 地址 | 设备类型 | 当前/目标 | 点位 | 用途 |
|---:|---|---|---|---|
| `1` | 热表/温湿度模块 | 已跑 | `supply_temp`, `humidity`, `status` | 验证连续采集和 LCD 数值刷新 |
| `2` | 电表 | 已跑 | `voltage`, `current` | 验证多从站轮询 |
| `3` | 坏表 | 已跑 | 无有效点位 | 验证超时、离线、退避 |
| `4` | 压力模块 | 待加 | `pri_supply_pressure`, `sec_supply_pressure` | 验证压力点位和单位 |
| `5` | 变频器/循环泵 | 待加 | `run_fb`, `fault`, `freq_fb`, `current` | 验证泵状态显示 |
| `6` | 阀门控制器 | 待加 | `valve_cmd`, `valve_feedback`, `limit_open`, `limit_close` | 验证执行器反馈 |
| `7` | 安全 IO 板 | 待加 | `estop`, `water_low`, `over_pressure`, `door_open` | 验证安全状态和告警 |
| `8` | 私有 MCU 控制器 | 待加 | 通过握手返回 `device_type/model/version` | 验证设备自动识别 |

## 协议清单

### Modbus RTU

用于模拟常见现场仪表和 IO 模块。

```text
请求: addr 03 start_hi start_lo count_hi count_lo crc_lo crc_hi
响应: addr 03 byte_count data... crc_lo crc_hi
```

当前例子:

```text
01 03 00 00 00 02 C4 0B
```

含义:读取 `1` 号设备,从寄存器 `0` 开始读 `2` 个保持寄存器。

### 私有 MCU 协议

用于模拟厂家控制器或自研 MCU 板。网关先查询设备身份:

```text
AA 55 | addr | cmd | len | payload | crc16
```

设备信息响应至少包含:

```text
device_type, model, protocol_version, device_id, capability
```

网关据此加载设备模板。详见 `../protocols/private-mcu-device-identification.md`。

## 点表模型

所有协议最终都要转成统一点表,上层 HMI/MQTT/控制逻辑只看点表。

```json
{
  "id": "sec_supply_temp",
  "name": "二次侧供水温度",
  "value": 45.2,
  "unit": "C",
  "quality": "good",
  "source": "modbus:addr=1,reg=0",
  "timestamp": 1710000000000
}
```

质量码最低要求:

| 质量码 | 含义 |
|---|---|
| `good` | 本轮读取成功,CRC 和长度正确 |
| `timeout` | 设备无响应 |
| `crc_error` | 校验失败 |
| `exception` | 设备返回异常码 |
| `offline` | 连续失败超过阈值 |
| `unknown_device` | 私有协议握手失败或类型不支持 |

## RK3506 显示目标

第一版 LCD 不追求复杂页面,先显示能证明系统跑通的关键数据:

- 当前时间/时钟是否可信。
- 设备在线/离线数量。
- 一次/二次侧温度、压力。
- 循环泵运行、故障、频率。
- 阀门指令与反馈。
- 安全 IO 告警。
- MQTT 在线/离线。

当前 `drm_hmi.py` 只显示 `T/H/V`,下一步要改成读取点表快照,而不是直接在 LCD 程序里读 Modbus。

## 运行步骤

104 启动模拟器:

```bash
sudo python3 -u /tmp/modbus_sim.py /dev/ttyUSB1 /tmp/sim_config.json
```

RK3506 启动 LCD:

```bash
killall lv_demo 2>/dev/null || true
python3 /userdata/energy-hmi/drm_hmi.py /dev/ttyS1
```

后续目标启动方式:

```bash
python3 /userdata/energy-hmi/gateway.py /dev/ttyS1 /userdata/energy-hmi/gateway_config.json
python3 /userdata/energy-hmi/lcd_hmi.py /userdata/energy-hmi/run/points.json
```

## 下一步实现顺序

1. 扩展 104 的 `sim_config.json`,加入压力、泵、阀、安全 IO。
2. 让 RK3506 采集服务输出统一点表快照 `points.json`。
3. 改 LCD 程序读取 `points.json`,不直接碰串口。
4. 加入私有 MCU 协议模拟器,验证 `device_type/model/version` 握手。
5. 在 LCD 显示设备类型、在线状态、质量码和告警。
6. 接入 MQTT,上报同一份点表快照。
7. 做长跑测试:拔线、坏 CRC、异常码、离线恢复、模拟器重启。

## 安全边界

这个阶段只做采集和显示,不自动控制泵阀。即使 104 模拟出控制器或执行器,网关也只能展示指令/反馈/告警。真正输出控制前,必须补齐限幅、联锁、回读确认、手自动权限和失联回退。


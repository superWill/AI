# Thermal Energy Co-controller Embedded Project

热能共控机嵌入式项目，用于换热站和小区侧供热系统。

## Confirmed Scope

- 控制对象：换热站 + 小区侧系统。
- 一次侧热媒：热水。
- 换热设备：板式换热器。
- 主通信协议：MQTT。
- 本地交互：需要本地屏。
- 远程能力：需要远程升级。
- 离线能力：需要断网自治运行。
- 控制优先级：安全优先。

## Directory Layout

```text
embedded-heating/
  README.md
  config/                Default runtime configuration (default-parameters.json)
  docs/                  All design documentation
    architecture/        System architecture, module responsibilities, runtime loops
    business/            Market reference, development plan, control-logic write-up
    point-table/         Initial point-table draft
    protocols/           MQTT protocol draft
    safety/              Safety-rules draft
  firmware/              Production firmware tree (设计中，no MCU/RTOS picked yet)
    include/             Public C headers (tec_control / tec_safety / tec_mqtt / ...)
    README.md            Firmware-layer design notes
  prototype/             Throwaway prototypes to flush out the product shape
    hmi/                 Browser-side HMI mock + sample device data + collector pseudocode
    firmware-sim/        Buildable C simulator (Makefile + main.c)
  .gitignore
```

## Architecture Rule

安全保护层优先级最高。远程 MQTT 指令、本地屏手动操作、自动控制算法都不能绕过安全保护。

## First Development Target

当前第一阶段先完成"设备信息采集 + 嵌入式平台显示"的最小产品：

1. 点表模型。
2. 设备数据采集。
3. 数据校验和状态判断。
4. 本地屏/HMI 实时显示。
5. 告警状态显示。
6. MQTT 遥测上报。
7. 后续再加入控制算法和安全联锁。

原型入口：

- `prototype/hmi/`：浏览器侧的 HMI 模拟页 + 采样数据 + 采集伪代码，用来对齐显示需求。
- `prototype/firmware-sim/`：可编译运行的 C 模拟器（Makefile + main.c），后续补充泵阀控制和保护策略。

关键设计文档：

- `docs/architecture/device-presence-and-data-flow.md`：设备插入/拔出监控、设备列表在线/离线状态、HMI/WebSocket/MQTT 数据传输链路。
- `docs/architecture/interface-event-notifications.md`：网线、USB、串口等接口事件监听和 HMI 提示模型。
- `docs/business/controllable-industrial-devices.md`：热能中控机可接入/可控制的工业设备、协议、典型数据和 BL412B 硬件映射。

`firmware/` 当前只放公共头文件（`include/`）和架构 README，模块代码 app/core/drivers/platform 等到选型确定后再建。

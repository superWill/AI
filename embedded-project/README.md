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
embedded-project/
  business-analysis/     Business analysis and HTML explanation pages
  firmware/              Embedded firmware source tree
    app/                 Product-level application modules
    core/                Reusable core logic
    drivers/             Device and protocol drivers
    platform/            Board, RTOS, and HAL adaptation
    include/             Public headers
  docs/                  Architecture, protocol, point table, and test docs
  tests/                 Unit, integration, and HIL tests
  tools/                 Generators, simulators, and helper scripts
  config/                Default runtime configuration
```

## Architecture Rule

安全保护层优先级最高。远程 MQTT 指令、本地屏手动操作、自动控制算法都不能绕过安全保护。

## First Development Target

当前第一阶段先完成“设备信息采集 + 嵌入式平台显示”的最小产品：

1. 点表模型。
2. 设备数据采集。
3. 数据校验和状态判断。
4. 本地屏/HMI 实时显示。
5. 告警状态显示。
6. MQTT 遥测上报。
7. 后续再加入控制算法和安全联锁。

MVP 入口：

- `mvp-device-display/`：采集设备信息并在嵌入式平台显示的最小产品原型。
- `mvp-firmware-sim/`：控制逻辑模拟器，后续用于补充泵阀控制和保护策略。


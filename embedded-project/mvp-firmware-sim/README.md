# MVP Firmware Simulator

这是热能共控机的最小嵌入式 MVP。它不是最终硬件固件，而是一个可以在电脑上运行的 C 语言固件模拟器，用来验证核心产品逻辑。

## What This MVP Shows

- 设备上电、自检、待机、启动、运行、告警、急停状态机。
- 二次侧供水温度控制一次侧调节阀。
- 二次侧供回水压差控制循环泵频率。
- 低压时启动补水。
- 超温、超压、低压、关键传感器故障安全保护。
- MQTT 遥测和告警上报的 mock 输出。
- MQTT 断线后继续本地自治运行。

## Build and Run

```sh
make
./build/tec_mvp
```

Run with scenario:

```sh
./build/tec_mvp normal
./build/tec_mvp low_pressure
./build/tec_mvp over_temp
./build/tec_mvp mqtt_offline
./build/tec_mvp sensor_fault
```

## Why This Exists

真实嵌入式开发通常要等硬件、IO 板卡、传感器、阀门、水泵、变频器、MQTT 平台都陆续准备好。这个 MVP 先把“控制器大脑”跑起来：

```text
State Machine -> Safety -> Control -> Device Output -> MQTT/HMI Snapshot
```

后续可以逐步替换：

- mock 传感器 -> 真实 AI/485/热表采集
- mock MQTT -> 真实 MQTT SDK
- printf HMI -> 本地屏
- host build -> MCU/RTOS build


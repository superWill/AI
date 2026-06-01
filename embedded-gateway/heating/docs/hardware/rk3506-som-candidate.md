# RK3506 SoM Candidate — HD-RK3506-CORE

候选硬件：**厚德 HD-RK3506-CORE 核心板**（基于 Rockchip RK3506 系列，35 mm × 35 mm 邮票孔 SoM）+ 配套开发板。本文档收录原厂资料 + 与本项目的匹配度评估，作为硬件选型阶段的参考。

> 状态：候选 / 未决。最终 MCU/SoM 选型还在并行评估 STM32F407、GD32F407、AT32F437 等 MCU 方案；待 Phase 1 prototype 验证后再决定。

## SoC 系列分级

RK3506 系列分三档，核心板用 **RK3506B/J**（不是 G2）：

| 型号 | 内存方式 | 封装 | 工作温度 | 定位 | EVB 参考 |
|---|---|---|---|---|---|
| RK3506G2 | Embedded DDR3L 128 MB | QFN128L 12.3 × 12.3 mm | -20 ~ +80 ℃ | 入门，内嵌内存 | RK_EVB1_RK3506G_V10_20240511 |
| RK3506B | 外挂 DDR2/3/3L 16-bit, ≤ 1024 MB | FBGA333L 13.3 × 11.3 mm | -20 ~ +80 ℃ | 通用 | RK_EVB1_RK3506B_DDR3P116SD4_V10_20240723 |
| RK3506J | 同 B | 同 B | **-40 ~ +85 ℃** 工业级 | 工业 | 同 B |

## CPU / MCU 架构

- 主核：**Cortex-A7 三核** @ 1.3 GHz（datasheet 上限 1.5 GHz），16K/16K L1 + 128 KB L2，含 NEON / FPU
- 协核：**Cortex-M0**
- L2 后挂 128 KB，独立 Interrupt Controller
- **AMP 异构** 两种官方配置：
  1. 2 × A7 (Linux) + 1 × A7 (RTOS) + M0 (HAL)
  2. 3 × A7 (RTOS) + M0 (HAL)
- 核间通信 **RPMsg**，中断响应延迟 < 5 μs
- 内嵌存储：SYSTEM SRAM 48 KB + ROM 32 KB + OTP（1 Kbit 用户空间 + 7 Kbit 安全空间）
- 加密：硬件 Crypto + RNG × 2

## 系统 / 软件栈（原厂）

| 类别 | 内容 |
|---|---|
| 系统框架 | Linux Kernel 6.1 · RT-Thread 4.1 · 裸机 · Preempt-RT / Xenomai 实时补丁 · 多核异构 AMP |
| 显示 | LVGL 轻量级 UI · RGA 硬件加速 · MIPI / RGB / OSPI 屏支持 |
| Turnkey APP | 视频 / 音频播放器 · 设置 · Launcher |
| 视频 | Rockit 软件解码库 · RTSP 实时流 · DVP 摄像头 |
| 语音算法 | RK 自有音频算法（离线）· 第三方离/在线算法适配 |
| 其他 | 差分 OTA · A/B 分区 · 快速开机 |

## HD-RK3506-CORE 核心板规格

| 类别 | 规格 |
|---|---|
| SoC | Rockchip RK3506B / J，主频 1.3 GHz |
| 操作系统 | Linux、RT-Thread |
| 加密 | 硬件加密，保护应用软件版权 |
| 内存 | 256 MB / 512 MB DDR3L |
| 存储 | 256 MB / 8 GB eMMC |
| MIPI DSI 2 Lane | 1280 × 1280 @ 60 Hz |
| RGB888 | 1280 × 1280 @ 60 Hz |
| 以太网 | 2 路百兆网（RMII × 2）|
| USB 2.0 | 2 路 USB 2.0 OTG |
| SDMMC | 1 路（支持 SDIO 3.0）|
| ADC | 4 路 10-bit SARADC |
| DSMC | 1 路 Master + 1 路 Slave |
| FLEXBUS | 1 路 |
| 音频 | SAI × 4 · PDM × 1 · SPDIF TX/RX × 1 · MIC × 1 |
| CAN | 2 路 |
| UART | 5 路通用 + 1 路调试 |
| I2C | 3 路 |
| PWM | 12 路 |
| SPI | 2 路通用 + 1 路 SPI APB |
| TOUCH KEY | 8 路 |
| GPIO | 3.3V GPIO × 81 + 1.8V GPIO × 5 |
| 机械 | 35 mm × 35 mm（外框 37.8 × 35），厚 3 mm |

## DSMC（双倍数据速率串行接口）

专门为 **FPGA 扩展** 设计：

- 支持 8 线或 16 线串行传输
- 最高 4 片选（CS0–CS3）
- 高带宽 + 低延迟
- 拓扑：RK3506 DSMC Master ↔ FPGA DSMC Slave

热能场景如果需要做高速 AD 采集（多通道同步采样）或确定性 IO 扩展，DSMC + FPGA 是一条路径。Phase 1 用不上，记录备查。

## 配套开发板

DC 12V 供电 · ETH0/ETH1 双百兆网 · USB Host × 2 + USB Device（固件下载）· 40Pin 扩展 · 背面 TF 卡 · RTC 电池座 · RGB565 屏接口 · WiFi+蓝牙模组 + 天线座 · 蜂鸣器 · 看门狗 · RECOVERY / RESET / LED · 调试串口（TXD/RXD/GND）。

板载芯片：RK3506 SoC · eMMC · DDR3L · MASKROM · WDG。

## 功耗 / 性能

低功耗（SoC 功耗 mW）：

| 场景 | 功耗 | 备注 |
|---|---|---|
| 待机（Logic 断电）| 8 mW | GPIO 唤醒 |
| 待机（Logic 不断电）| 30 mW | |
| IDLE | 109 mW | 无显示，WiFi 连接 |
| 静态桌面 | 200 mW | UI 显示不含屏、WiFi 连接 |

高性能（@1.5 GHz CPU + DDR 800 MHz）：

| 项目 | 分数 |
|---|---|
| Unixbench 单核 | 194.7 |
| Unixbench 多核 | 455.8 |
| Dhrystone | 5,128,205 |
| Whetstone | 3333.3 MIPS |
| Stream | 2225 MB/s |

## 官方应用案例

地铁导乘 / PIS 系统 · AGV 控制器 · 生化分析仪 · 电力/能源网关。前后两类都是"工业控制 + 本地 HMI + 数据上行"，与热能共控机场景接近。

## 与本项目的匹配度

### 优势

| 方面 | 评估 |
|---|---|
| AMP 架构 | 与本项目"安全实时层（PID 闭环 + 安全联锁）+ 应用层（MQTT + OTA + HMI）+ 通用 IO 层" 的分层意图直接对应：M0 / A7-RTOS 跑控制环路与安全规则，A7-Linux 跑 MQTT、远程升级、本地 LVGL 屏；核间走 RPMsg，确定性中断 < 5 μs，满足 1 ms tick 主循环 |
| 实时性 | Preempt-RT / Xenomai 补丁现成；A7-RTOS 直接跑 RT-Thread；M0 跑裸机更稳 |
| HMI | LVGL + RGA 硬件加速 + MIPI 屏支持，省去自研 UI 框架 |
| 通信 | 2 路百兆以太网（可一路上行 MQTT、一路工程网调试）+ CAN × 2（与现场仪表对接）+ UART 6 路（其中 5 路通用，可分给 Modbus RTU / 调试 / 备用）|
| OTA | 原厂带差分 OTA + A/B 分区 |
| 开发效率 | Linux 容器化构建 + 现成 BSP，比裸 STM32 + 自研协议栈快 |
| 工业级温区 | RK3506J -40 ~ +85 ℃，覆盖北方寒区换热站冬季机房极限 |

### 劣势 / 风险

| 方面 | 评估 |
|---|---|
| 成本 | 整 SoM 价格 > 单片 STM32F407 + DDR + Flash 的 BOM；只适合"有 HMI + 网关 + OTA"那一档定位，纯控制柜不划算 |
| 功耗 | IDLE 109 mW + 屏 + 外设，总功耗比纯 MCU 高一个量级，需评估机柜散热 |
| 软件复杂度 | 三种 OS 混跑（Linux + RTOS + 裸机 M0）调试难度高，需要熟练的 Yocto / RT-Thread BSP 经验 |
| 资料 | RK3506 是 2024 年新片，中文社区资料少；遇到 BSP bug 主要靠厚德 / 瑞芯微 FAE |
| 单源风险 | RK3506 国产单源，无 pin-to-pin 替代；如果做长期供应链方案需要做 STM32 / GD32 / NXP 的备选 |

### 适合本项目的场景

- 工程级换热站（有本地大屏 + 实时上云 + 一定算力余量做远程诊断）→ **强匹配**
- 小型供热子站（盒子式控制器，只做闭环 + Modbus）→ **过剩**，更适合 STM32F407 类
- 工业级温区（-40 ℃）部署 → **必选 RK3506J**

## 开放问题

- 实际 BOM 价格区间？目前没拿到厚德官方报价。
- 与 Rockchip RK3308 / RK3328 比，RK3506 的优势是不是只在 AMP + 工业温区？
- RT-Thread 4.1 在 RK3506 上的 RTOS 核心是社区版还是厚德定制版？
- M0 协核的固件构建工具链（GCC / Keil？）以及调试方式（J-Link / RPMsg console）？
- 工业认证（CE / FCC / UL）厂方是否已经备齐？
- 长期供货承诺（RK3506 寿命周期，对应工程项目通常需要 ≥ 7 年保供）。

## Decision Pending

最终是否选用 RK3506 取决于：

1. Phase 1 prototype（`prototype/firmware-sim/`）跑通后估算的算力 / 资源占用是否真的需要 A7 级
2. 工程目标定位（盒子机 vs 大屏机）
3. 采购侧的供应链与价格谈判
4. 团队对 Linux + RTOS + Bare-metal 混跑的接受度

候选并列方案：

- **MCU 路线**：STM32F407 / GD32F407（单芯片 + RT-Thread + 裸机 LCD 驱动）
- **SoM 路线**：本机型，或 全志 T113-S3 / 瑞芯微 RK3308 / NXP i.MX RT1170 等

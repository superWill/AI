# Firmware Architecture

消防共控机固件，安全 + 联动优先；总线主控 + 上行链路 + 本地 HMI 三个 I/O 面。

## Current State

主控 MCU / RTOS / 总线驱动 IC 都未定型，本目录目前只有公共头文件接口和本文档。

```text
firmware/
  include/   Public C headers
    fac_loop.h        Loop bus master interface
    fac_point.h       Runtime point-table data model
    fac_alarm.h       Alarm decision engine
    fac_interlock.h   Interlock matrix engine (highest priority)
    fac_link.h        Upstream CRT (graphics workstation) link
    fac_panel.h       Local HMI (LCD + keypad + LEDs + printer)
  README.md
```

实现模块（drivers / app / core / platform）等选型与试制板出来再加。

## Target Layers (post-hardware-selection)

```text
firmware/
  app/
    alarm/        Cross-zone confirm, single-point alarm
    interlock/    Matrix evaluator + execution state machine
    panel/        Display pages, key handler, LED matrix, printer queue
    link/         CRT frame codec + retransmission window + offline replay
    power/        Mains/battery switch-over + low-power thresholds
    log/          Ring buffer + Flash persistence (≥10 000 entries)
  core/
    point_table/  Three-layer device/zone/group model
    config/       Default & persistent parameters
    crc/          CRC-16/CCITT, CRC-16/MODBUS
    hmac/         HMAC-SHA256 for downstream control auth
  drivers/
    loop_bus/     UART + current-loop modulator + short/open detect
    rs485/        CRT link transport (alt: rs232, ethernet)
    lcd/          Mono / TFT panel driver
    keypad/       Matrix keypad scan + debounce
    led_matrix/   Indicator panel drive
    printer/      Thermal printer command set
    rtc/          Battery-backed real-time clock
    flash/        Internal + external SPI flash partitioning
  platform/
    bsp/          Pin map, clock tree, boot
    hal/          MCU peripheral abstraction (vendor SDK shim)
    rtos/         RT-Thread or FreeRTOS adapter
  include/        Existing public headers
```

## Selection Constraints

CCCF + GB 4717 / GB 16806 加在硬件 / 软件上的具体约束（节选）：

- **后备电池**：满载工作 30 min + 监视 8 h（GB 4717 § 5.2.4）。
- **响应时间**：从探测器触发到主机报警显示 ≤10 s。
- **报警容量**：单回路 ≥128 点；整机 ≥1024 点（GB 4717 § 4.3）。
- **历史记录**：≥10 000 条，断电不丢（GB 4717 § 5.6）。
- **故障检测**：单点失联、回路短路、回路开路、主备电故障，均需自动检测并显示。
- **操作级别**：≥3 级，逐级密码（GB 4717 § 5.1.4）。
- **环境**：工作温度 −10 ℃ ~ +55 ℃；湿度 ≤93 %RH（GB 12978 严酷等级 2）。
- **EMC**：GB 17626 全套抗扰 + GB 9254 Class B 发射。

候选 MCU：

| MCU | 主频 | Flash | SRAM | 备注 |
| --- | --- | --- | --- | --- |
| STM32F407VG | 168 MHz | 1 MB | 192 KB | 国际通用，CCCF 资料齐全 |
| GD32F407VG | 168 MHz | 1 MB | 192 KB | 国产替代，pin-to-pin |
| MM32F0270 | 96 MHz | 256 KB | 32 KB | 低端，单回路够用 |
| AT32F437 | 288 MHz | 4 MB | 512 KB | 高端，多回路 + 图形 LCD |

候选 RTOS：

- **RT-Thread**（国内消防行业最常见，BSP 多，社区支持好）
- **FreeRTOS**（国际通用，但生态偏国外）
- **裸机 + 状态机**（Phase 1 单回路其实够，但扩到多回路 + Ethernet 后建议引入 RTOS）

## Build System

选型后再加。目前候选：

- **CMake + ARM GCC**：通用，方便 CI；缺点是 STM32CubeMX 生成代码与 CMake 集成需手工调。
- **ScopusCube / GD32CubeIDE**：原厂 IDE，新人上手快，但 CI 流水线难。
- **RT-Thread Studio / Env**：用 RT-Thread 时首选。

## Prototype Path

在选型未定前，可以先用 PC 端的"逻辑模拟器"验证状态机与联动矩阵：

```text
../prototype/
  loop-bus-sim/   伪造回路总线 + N 个 device，用 stdin/stdout 触发报警
  matrix-eval/    联动矩阵 + 规则评估的 PC 端实现
```

prototype 还没建，等 Phase 1 真要做的时候再起。

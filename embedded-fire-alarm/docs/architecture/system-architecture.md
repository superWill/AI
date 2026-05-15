# System Architecture

消防共控机一台主机内部的功能分层。横向是数据流向，纵向是优先级（上层不可被下层旁路）。

```text
              ┌──────────────────────────────────────────┐
              │     Local HMI (LCD + Keypad + LEDs)     │
              │     Printer / Microphone / Recorder      │
              └────────────────┬─────────────────────────┘
                               │
              ┌────────────────▼─────────────────────────┐
              │     Application Layer                     │
              │  ─ Alarm Decision Engine                  │
              │  ─ Interlock Matrix (priority highest)    │
              │  ─ Zone / Group / Shielding Management    │
              │  ─ History Log (≥10 000 entries)          │
              └────────┬────────────────┬─────────────────┘
                       │                │
        ┌──────────────▼──┐     ┌───────▼──────────┐
        │ Loop Bus Master │     │ Upstream Link    │
        │ (Two-wire bus)  │     │ (CRT graphics)   │
        │ Polling + Frame │     │ GB 16806 iface   │
        └──────┬──────────┘     └──────────────────┘
               │
       ┌───────┴────────────────────────────────┐
       │  Loop 1   Loop 2   Loop 3   ... Loop N │
       │                                        │
       │  Detectors / Manual Buttons / Modules  │
       │  (smoke, heat, CO, IO modules driving  │
       │   relays, dampers, fans, pumps, doors) │
       └────────────────────────────────────────┘

              ┌──────────────────────────────────────────┐
              │     Reliability Layer                     │
              │  ─ Dual Power (mains + 24V battery)       │
              │  ─ Watchdog + brown-out reset             │
              │  ─ Fail-safe defaults                     │
              │  ─ Self-diagnostic loop                   │
              └──────────────────────────────────────────┘
```

## Priority Order

1. **Safety / interlock layer** — 触发条件满足即输出动作信号，不可旁路。
2. **Local manual control (with key switch armed)** — 仅消防控制室人员可启停联动设备，不能屏蔽自动联动判定。
3. **Application logic** — 报警判定、屏蔽、延时、确认。
4. **Upstream CRT / 远程指令** — 仅允许查询、复位、播放语音；下行控制必须经本机仲裁。

任何来自第 4 层的指令都不能让第 1 层失效。

## Concurrency Model

- 实时主循环：1 kHz tick，跑总线轮询调度 + 报警判定 + 联动矩阵评估。
- 慢任务（≥100 ms）：HMI 刷新、CRT 帧收发、历史记录写入、电池电压采样。
- 中断只做"硬关键路径"——总线 UART RX / RTC 秒中断 / 主备电切换。
- 全程 RTOS 或裸机 + 状态机皆可；选择见 `firmware/README.md`。

## Failure Modes & Fail-safe

| Mode | Detection | Default action |
| --- | --- | --- |
| Loop short | 总线电流持续 > 阈值 | 标记该回路故障，其余回路仍工作 |
| Loop open | 末端检测帧丢失 | 同上 |
| Device missing | 连续 3 轮轮询无响应 | 该点位标记故障，不影响判定其他点 |
| MCU watchdog timeout | 看门狗未喂 | 复位 → 启动后回到 STANDBY 并立即上报"主机复位"事件 |
| Mains lost | 主电检测电压 < 阈值 | 切到电池，亮"主电故障"灯，上报，继续工作 |
| Battery low | 电池电压 < 21.0 V | 上报"备电故障"，继续工作直到 19.5 V 才切断 |
| CRT link lost | 心跳超时 | 本机继续判定与联动，缓存事件，链路恢复后补发 |

"失效偏报警"原则：当探测器自身故障与可疑火警无法区分时，倾向报警（人为复位代价 < 漏报代价）。

## Hardware Selection

未定，候选：

- 主控 MCU：STM32F407 / GD32F407 / MM32F0270 系列（成本与性能平衡，国产化备选明确）。
- 隔离总线驱动：厂商私有 ASIC 或基于 UART + 电流环驱动 + 短路保护 MOSFET。
- 显示：240×128 单色 LCD（带 LED 背光），后续可升至 480×272 TFT。
- 电源：AC 220 V → 27.6 V 浮充 → 24 V 系统 + 5 V / 3.3 V 二次降压。

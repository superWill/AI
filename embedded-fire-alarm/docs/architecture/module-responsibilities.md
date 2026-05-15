# Module Responsibilities

主控固件按模块划分；每个模块对应 `firmware/include/fac_*.h` 中一个头文件接口。

## `fac_loop` — Loop Bus Driver

| Concern | Detail |
| --- | --- |
| Bus topology | 二线制，极性无关，电源 + 数据复用 |
| Frame format | 私有协议，地址 + 命令 + 数据 + CRC（详见 `docs/protocols/loop-bus-draft.md`） |
| Polling | 1 Hz 全点轮询，报警/动作中断式抢占 |
| Diagnostics | 短路/开路/单点失联检测；上抛 `LOOP_FAULT` 事件 |
| Output | 解码后向 `fac_point` 推送 `loop_event_t` |

## `fac_point` — Point Table

| Concern | Detail |
| --- | --- |
| Data model | 三层：Device → Zone → Group |
| Device fields | id, type (smoke/heat/manual/IO/...), state, last_seen, shielded, fault_flags |
| Zone fields | id, name, member device list, alarm count, alarm timestamp |
| Group fields | id, name, member zones, triggered interlock IDs |
| Persistence | 全表存 SRAM 运行时镜像 + Flash 全表快照（断电恢复）|
| Mutation | 仅允许由 `fac_loop` 和 `fac_alarm` 修改，其他模块只读 |

## `fac_alarm` — Alarm Decision Engine

| Concern | Detail |
| --- | --- |
| Single-point alarm | 任一探测器或手动按钮触发即报警 |
| Cross-zone confirm | 同一防火分区内，≥2 个探测器在窗口内触发才允许联动启动（GB 50116 第 4.1 节）|
| Manual call point | 立即报警 + 立即联动，无延时 |
| Hysteresis | 复位指令清除报警；故障状态自动恢复需 60 s 稳定 |
| Output | 向 `fac_interlock` 推送"已确认的火警事件" |

## `fac_interlock` — Interlock Matrix

| Concern | Detail |
| --- | --- |
| Priority | 最高，任何输入或屏蔽逻辑不可旁路 |
| Matrix | "触发条件 → 联动设备" 表，按 GB 50116 第 4.2-4.10 节构建（详见 `docs/safety/interlock-rules-draft.md`）|
| Delay | 每条规则可独立配置延时（0 ~ 30 s）以满足规范 |
| Execution | 调用 `fac_loop` 下发输出模块"启动"命令 |
| Feedback | 等待输出模块反馈，10 s 内未收到反馈 → 故障，上报 |
| Manual override | 仅允许"启动" / "停止"，不允许"屏蔽" |

## `fac_link` — Upstream CRT Link

| Concern | Detail |
| --- | --- |
| Transport | RS-485 / Ethernet（按机型）|
| Protocol | GB 16806 接口；厂商私有应用层（详见 `docs/protocols/crt-link-draft.md`）|
| Uplink | 火警 / 动作 / 故障 / 屏蔽 / 监管 / 心跳 |
| Downlink | 查询、复位（需密码）、手动启动（需钥匙开关 + 密码）、广播触发 |
| Offline | 缓存上行事件，链路恢复后按时间序回放 |

## `fac_panel` — Local HMI

| Concern | Detail |
| --- | --- |
| Display | 主页（系统状态汇总）/ 事件列表 / 探测器详情 / 设置 |
| Keypad | 0-9 / Enter / Cancel / 复位 / 消音 / 自检 / 手自动切换（钥匙开关）|
| LEDs | 火警 / 动作 / 反馈 / 屏蔽 / 故障 / 启动 / 监管 / 延时 / 手动允许 / 主电 / 备电 |
| Printer | 内置热敏打印机；火警与动作事件自动打印 |
| Audio | 蜂鸣器（火警 1 Hz / 故障 0.5 Hz / 监管 间歇）+ 接警话筒 + 录音 |
| Permission | 三级权限（操作员 / 管理员 / 维护）|

## Cross-cutting

- **Watchdog**：所有主循环模块 1 Hz 喂狗；任何模块阻塞 > 2 s → 复位。
- **Logging**：环形缓冲 + Flash 持久化，≥10 000 条历史（GB 4717 强制）。
- **Self-diagnostic**：每 5 分钟跑一次自检，覆盖 Flash 校验、RAM 校验、电池电压、回路阻抗。

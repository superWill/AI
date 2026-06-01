# Loop Bus Protocol (Draft)

二总线物理层 + 私有应用层。各厂私有，不同厂主机与探测器不可互通。本文档定义本项目自己的版本（CCCF 申报时按此版本提交）。

## Physical Layer

| Parameter | Value | Notes |
| --- | --- | --- |
| 拓扑 | 总线（多分支允许，无 T 型限制）| 末端检测靠主机轮询响应 |
| 线对数 | 2（电源 + 数据复用）| 极性无关 |
| 总线电压 | 24 V DC ± 10 %（监视）/ 数据帧期间调制 | |
| 数据信号 | 主机端 ±2 V 调制脉冲 / 从机端电流环响应 | |
| 通信速率 | 9600 baud（4 kHz 调制载波）| |
| 最大单回路距离 | 1500 m（线径 ≥1.5 mm² RVS）| |
| 最大单回路点数 | 200（规范 + 容量约束）| |
| 短路保护 | 主机端电流限制 + 短路检测 → 关闭该回路输出 | |
| 极性无关 | 总线两端可调 | 探测器内置整流桥 |

## Frame Format

```text
┌──────┬─────┬──────┬────────┬──────┬──────┬─────┐
│ SYNC │ DST │ CMD  │ LEN    │ DATA │ CRC  │ END │
│ 0xAA │ u8  │ u8   │ u8     │ ...  │ u16  │ 0x55│
└──────┴─────┴──────┴────────┴──────┴──────┴─────┘
```

| Field | Size | Meaning |
| --- | --- | --- |
| `SYNC` | 1 B | 同步头 `0xAA` |
| `DST` | 1 B | 目标地址（1-200；0x00 广播；0xFF 主机自身）|
| `CMD` | 1 B | 详见 Command Codes |
| `LEN` | 1 B | DATA 字节数（0-32）|
| `DATA` | 0-32 B | 命令载荷 |
| `CRC` | 2 B | CRC-16/CCITT，覆盖 DST..DATA |
| `END` | 1 B | 结束标志 `0x55` |

总帧长 7-39 B。`0xAA` 与 `0x55` 在 DATA 中需做转义（`0x1B 0xAA` → `0xAA` 数据；`0x1B 0x55` → `0x55`；`0x1B 0x1B` → `0x1B`），转义在 CRC 之后做。

## Command Codes

主机 → 从机：

| Code | Name | Direction |
| --- | --- | --- |
| 0x01 | POLL | M→S 轮询（最常用，每 5 ms 一帧）|
| 0x02 | READ_STATE | M→S 读完整状态 |
| 0x03 | READ_ANALOG | M→S 读模拟量（烟浓度、温度等）|
| 0x04 | SET_THRESHOLD | M→S 设报警阈值 |
| 0x05 | RESET | M→S 复位单点 |
| 0x06 | SHIELD | M→S 屏蔽 |
| 0x07 | UNSHIELD | M→S 解除屏蔽 |
| 0x08 | OUTPUT_ON | M→S 输出模块启动 |
| 0x09 | OUTPUT_OFF | M→S 输出模块停止 |
| 0x0A | SELF_TEST | M→S 自检 |
| 0x0B | READ_FAULT | M→S 读故障字 |

从机 → 主机（响应）：

| Code | Name | Trigger |
| --- | --- | --- |
| 0x81 | ACK_NORMAL | POLL 响应：正常 |
| 0x82 | ACK_ALARM | POLL 响应：报警 |
| 0x83 | ACK_FAULT | POLL 响应：自身故障 |
| 0x84 | ACK_ACTION | POLL 响应：输出模块已动作 |
| 0x85 | ACK_FEEDBACK | POLL 响应：联动设备反馈到位 |
| 0x86 | ACK_DATA | READ_* 命令的数据响应 |
| 0xFE | NACK | 拒绝命令（无效参数 / 越权）|

## Polling Schedule

- 主机以 5 ms 间隔逐个轮询所有已注册 device（POLL，1 帧≈10 ms 含响应）。
- 满 200 点 → 1 秒一轮，满足 GB 4717 "10 s 响应"的余量。
- 当某 device 在 POLL 响应里报告 ALARM/FAULT/ACTION，主机立即用 READ_STATE 拉详细信息，**不等下一轮**。
- 广播帧（DST=0x00）用于"同步复位"、"全员消音"等罕用动作，主机一次广播后用一轮 POLL 验证全员状态。

## Error Handling

| Symptom | Diagnosis | Action |
| --- | --- | --- |
| 单点 3 轮 POLL 无响应 | 该点失联 | 标记 `state=FAULT, fault_flags |= TIMEOUT` |
| 整条回路 5 s 无响应 | 总线短路 / 主机驱动故障 | 关闭该回路输出，亮"回路故障"灯，CRT 上报 |
| CRC 错误 | 干扰 / 噪声 | 该帧丢弃，不更新状态；连续 10 帧 CRC 错触发"回路质量差"事件 |
| DST 不一致 | 编程错误 / 总线冲突 | 丢弃 |
| LEN > 32 | 协议越界 | 丢弃 |

## Open Items

- 是否引入 device 自动地址分配（鼎信、海湾的"自学习编址"）？还是手工 DIP 拨码 + 配置表？
- 是否预留厂家私有命令段（0xC0-0xFE）以支持扩展？目前认为预留 + 文档化即可。
- 总线驱动 ASIC vs MCU + 分立驱动？决定后回填到 `system-architecture.md` 的硬件章节。

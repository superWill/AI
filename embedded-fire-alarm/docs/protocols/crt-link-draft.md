# CRT Link Protocol (Draft)

主机 ↔ 消防控制室图形显示装置（CRT）之间的接口。GB 16806 第 4.10 节规定了物理层与基本帧格式，应用层各厂私有。本文档定义本项目的版本。

## Physical Layer

| Parameter | Value |
| --- | --- |
| 主接口 | RS-485 半双工 + 备用 RS-232 全双工（按工程选）|
| 备选 | 100Base-T 以太网（新工程优先）|
| RS-485 速率 | 9600 / 19200 / 38400 baud（默认 9600）|
| RS-232 速率 | 同上 |
| 字符格式 | 8N1（8 数据位 / 无校验 / 1 停止位）|
| 半双工切换时间 | ≤2 ms |
| 隔离 | 主机端电气隔离（光耦或磁耦），耐压 ≥1500 V AC |

## Application Frame

```text
┌──────┬──────┬─────┬─────┬──────┬────────┬──────┬─────┬──────┐
│ SOF  │ VER  │ SEQ │ SRC │ DST  │ TYPE   │ LEN  │ DATA│ CRC  │
│ 0x7E │ u8   │ u16 │ u16 │ u16  │ u8     │ u16  │ ... │ u16  │
└──────┴──────┴─────┴─────┴──────┴────────┴──────┴─────┴──────┘
```

| Field | Size | Meaning |
| --- | --- | --- |
| `SOF` | 1 B | `0x7E` |
| `VER` | 1 B | 协议版本，当前 0x01 |
| `SEQ` | 2 B | 序号；CRT 端必须按序确认，主机端缓存窗口 |
| `SRC` | 2 B | 源地址（主机自身 = 0x0001；CRT = 0x0080）|
| `DST` | 2 B | 目标地址 |
| `TYPE` | 1 B | 帧类型（详见 Frame Types）|
| `LEN` | 2 B | DATA 长度（0-1024）|
| `DATA` | 0-1024 B | 帧体 |
| `CRC` | 2 B | CRC-16/MODBUS，覆盖 SOF..DATA |

`0x7E` 在 DATA 中转义为 `0x7D 0x5E`；`0x7D` 转义为 `0x7D 0x5D`。

## Frame Types

主机 → CRT（上传）：

| Type | Name | DATA |
| --- | --- | --- |
| 0x01 | HEARTBEAT | 主机时间戳 + 当前主备电状态 |
| 0x10 | ALARM_REPORT | event_id, zone_id, device_id, alarm_type, timestamp |
| 0x11 | ACTION_REPORT | event_id, group_id, device_id, action_type, timestamp |
| 0x12 | FEEDBACK_REPORT | event_id, device_id, feedback_type, timestamp |
| 0x13 | FAULT_REPORT | event_id, device_id, fault_flags, timestamp |
| 0x14 | SHIELD_REPORT | event_id, device_id, shielded, by_user, timestamp |
| 0x15 | SUPERVISORY_REPORT | event_id, device_id, supervisory_type, timestamp |
| 0x16 | RESET_REPORT | reset_scope, by_user, timestamp |
| 0x17 | POWER_EVENT | event_type (main_fault / battery_low / battery_fault), timestamp |
| 0x80 | LIST_DEVICES_RESP | 设备列表分页响应 |
| 0x81 | READ_STATE_RESP | 单点状态响应 |
| 0x82 | SELF_TEST_RESP | 自检结果响应 |

CRT → 主机（下行）：

| Type | Name | DATA | Requires |
| --- | --- | --- | --- |
| 0x02 | ACK | acked_seq, status (0=ok / 1=crc / 2=auth / 3=unknown_type) | — |
| 0x20 | LIST_DEVICES | filter (loop_id, zone_id, type) | — |
| 0x21 | READ_STATE | device_id | — |
| 0x22 | SELF_TEST | scope (system / loop_id / device_id) | — |
| 0x23 | RESET | scope, password_hash | 密码 |
| 0x24 | MANUAL_START | device_id, password_hash | 密码 + 钥匙开关 |
| 0x25 | MANUAL_STOP | device_id, password_hash | 密码 + 钥匙开关 |
| 0x26 | SHIELD | device_id, shielded, password_hash | 密码 |
| 0x27 | SET_PARAM | param_id, value, password_hash | 密码（仅维护级）|
| 0x28 | PLAY_BROADCAST | broadcast_zone_list, audio_clip_id | 密码 |

## Heartbeat & Liveness

- 主机每 5 s 发 HEARTBEAT；CRT 每 10 s 内必须收到至少一条，否则判定链路异常。
- CRT 每 5 s 发"心跳应答"（用 ACK 帧覆盖最近一次 HEARTBEAT 的 SEQ）。
- 任一方判定链路异常 → 上抛 `LINK_LOST` 本地事件，主机本机继续工作。

## Reliability

- 上行重要事件（ALARM/ACTION/FAULT/POWER）使用"确认窗口"机制：
  - 主机发出 → 期望 5 s 内收到 ACK
  - 超时未 ACK → 重发，最多 3 次
  - 3 次仍失败 → 缓存到 Flash 队列（容量 ≥1000 条），链路恢复后按时序补发
- 心跳与 LIST_DEVICES 等查询帧不重发，丢就丢。

## Security

- 下行控制命令必须带 `password_hash`：HMAC-SHA256(secret + seq + payload)
- `secret` 在工程出厂时写入主机 EEPROM，CRT 端通过工程配置写入；不在协议层传输。
- 维护级命令（SET_PARAM、固件升级）需要二次确认（CRT 端发 PREPARE → 主机回 NONCE → CRT 用 NONCE 加签 → 主机执行）。
- 没有 TLS（GB 16806 不要求；上述对称密钥够）。

## Offline Replay

- 链路断开期间，所有 ALARM_REPORT / ACTION_REPORT / FAULT_REPORT 写入 Flash 队列。
- 链路恢复后按时间序逐条发出，每条带原时间戳；CRT 端 UI 上区分"实时"与"补传"。
- 队列写满（1000 条）后丢弃最老的非火警事件，火警事件优先保留。

## Open Items

- 是否要支持以太网 + TCP 的封装？需要的话上层帧不变，只换 transport。
- 是否要支持多 CRT（一台主机 → 多个图形工作站）？工程要求来定。
- 是否引入"差分时间同步"机制（NTP / PTP）以保证多主机时戳一致？目前各机本地 RTC + 上电校时即可。

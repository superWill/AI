# 云端管理后台 · P0 设计冻结（Design Freeze）

> 状态：**DRAFT / 待评审**（评审通过后本文件锁定为 P0 实现契约）
> 范围：RK3506 供暖网关 → 自建 EMQX → Go 后端 → TimescaleDB → Web，端到端最小闭环。
> 配套架构图见 conversation artifact（v3）。上游一律称「平台」，不写厂商名。
> 标签规则见 `~/.claude/CLAUDE.md`：`[KNOWN]` 已从代码/文档核实，`[INFERRED]` 推断，`(待核实)` 需查 datasheet/抓包。

本文件存在的唯一理由：**远程改供暖设定值是高后果操作。** P0 开工前必须把「协议信封、命令语义、去重、安全、存储」这些跨边缘/云的契约冻结成机器可校验的定义，避免边缘和云各写各的。

---

## 0. 阶段门禁（本文件冻结 P0，P1/P2 仅列边界）

| 阶段 | 内容 | 门禁 |
|---|---|---|
| **P0a** | 边缘（Go migration 分支）补：MQTT TLS 接入、`boot_id`、协议信封字段、schema 冻结。**遥测/控制业务逻辑不改。** | 改动落点/差距/回滚见 §9（已核实 Go 代码） |
| **P0b** | 云侧新建：TLS 接入 + 分方向 ACL、遥测落库+去重、在线态、趋势（限跨度+降采样）、云端派生只读告警。 | 依赖 P0a 的 TLS/`boot_id`/schema 落地 |
| **P1** | 安全下发闭环：`property/set`、RBAC+审计+审批、`command_id` 幂等、`valid_until`、202+命令查询、告警 ack/关闭。 | **门禁：边缘命令状态机 + 反馈收敛 + 命令持久化，测试通过后才开放下发。** |
| **P2** | OTA（签名/灰度/回滚）、多租户、高可用、大规模分层存储。 | 生产阶段再议 |

> **关键更正（相对早期草图）**：P0b 不是「零边缘改动」。P0b 依赖 P0a 先在边缘落 TLS/`boot_id`/schema——这是边缘改动。若暂不改边缘，只能在受控测试网用 1883 明文联调，**不得称为正式 P0 接入**。

---

## 1. 协议信封冻结（envelope）

所有上行报文（`telemetry` / `alarm` / `event` / `heartbeat` / `command_reply`）共享顶层信封。相对现状 `[KNOWN]`（`app.py` 仅含 `device_id/ts/seq/clock_sync/devices`），**P0a 新增 4 个字段**：

| 字段 | 类型 | P0a 新增? | 语义 |
|---|---|---|---|
| `device_id` | string | 现有 | 网关唯一标识，等于 MQTT client_id 与 topic 段 |
| `schema_version` | string(semver) | **新增** | 报文契约版本；云端按此路由/兼容。多网关版本可不一致。注：Go 已有 `config_version`（点表编译版本，`compiler.go`/`loader.go:103`）`[KNOWN]`，**那是另一回事，不复用** |
| `boot_id` | string(uuid/单调) | **新增** | **每次进程启动唯一**；解决 seq 跨重启归零导致的去重失效 |
| `firmware_version` | string | **新增** | 固件版本；用于 OTA 前置与能力判断 |
| `capabilities` | string[] | **新增** | 该网关支持的能力（如 `telemetry`/`alarm.publish`/`command.statemachine`）；云端**不得假设所有设备能力一致** |
| `ts` | int64(ms) | 现有 | 报文生成时刻（边缘时钟，Unix ms） |
| `seq` | int64 | 现有 | **单次启动内**单调递增，仅用于缺帧检测；`[KNOWN]` `runtime.go:107` 每次启动从 0 起、不持久化 |

**遥测体结构冻结** `[KNOWN]`：以生产 `runtime.go Telemetry()` 的 **`devices[]` 嵌套结构**（每设备 `addr/name/type/ok/points`）为准，**不用**旧版 `mqtt/gateway_mqtt.go` 的扁平 `points` 结构。

### Topic 与 QoS 冻结

| 方向 | topic | QoS | retained | 备注 |
|---|---|---|---|---|
| 上行 | `station/{id}/telemetry` | 0 | 否 | 周期高频；靠 `boot_id+seq` 幂等消费，丢一帧无妨 |
| 上行 | `station/{id}/alarm` | **1** | 否 | 不可丢 |
| 上行 | `station/{id}/event` | 1 | 否 | |
| 上行 | `station/{id}/heartbeat` | 0 | 否 | 在线态判定输入之一 |
| 上行 | `station/{id}/command_reply` | **1** | 否 | 命令闭环回执，不可丢 |
| 下行 | `station/{id}/property/set` | 1 | **否（强制）** | `[INFERRED]` retained 会让设备重连后执行旧命令 → 高后果，禁用 |
| 下行 | `station/{id}/command` | 1 | 否 | |

**接收侧确认时机** `[INFERRED]`：QoS1 消息**入库成功后再 PUBACK**（at-least-once + 幂等消费）；schema 校验失败的消息进**隔离队列（dead-letter）**并计数,不静默丢弃。

---

## 2. 遥测入库与去重语义

- **去重键 = `(device_id, boot_id, seq)`** `[INFERRED, 采纳 review]`。不用 `(device_id, seq)`——`[KNOWN]` seq 每次启动归零，会把重启后的新数据误判为旧数据。
- **双时间戳**：`observed_at`（= 信封 `ts`，边缘采集时刻）与 `received_at`（云端入库时刻）分开存，不可混用。
- **快照更新规则**：`latest snapshot` 表按 **`observed_at` 优先、同 `observed_at` 再比 `(boot_id, seq)`** 条件更新——**旧帧不得覆盖新帧**。
- **replay 只是传输属性**：补传报文可带 `replay:true`，但**它不单独决定数据新旧**；新旧一律由 `observed_at + boot_id + seq` 判定。补传旧数据入历史表，但不得覆盖当前 snapshot。
- **告警数据源（P0b 决策）** `[KNOWN]`：现状边缘只 publish `telemetry`/`heartbeat`/`command_reply`，**不发 `alarm`/`event`**。故：
  - **P0b：告警由云端对遥测做阈值派生**（只读列表）。
  - 边缘上报原生 `alarm`/`event` 的能力 → 归 P0a 可选项或延后；由 `capabilities` 声明后云端才消费。

---

## 3. 命令下行冻结（P1 落地，P0 先冻结契约）

### 命令报文 schema（`property/set` / `command`）

```
{ "command_id": str(uuid, 幂等键),
  "ts": int64(ms),
  "operator": str(审计用),
  "command_type": "setpoint" | "...",
  "payload": { "<point_id>": <value>, ... },   // 仅此层是控制点
  "valid_until": int64(ms) }                     // 过期即拒绝执行
```

**冻结约束**：
- **控制点只从 `payload` 层取；无 `payload` 键 → 拒绝（`rejected: bad_schema`），不回退到遍历顶层。**（Python 版 `app.py:712` `cmd.get("payload", cmd)` 有此 footgun；Go 版取值方式以 §9 落地为准，冻结此规则以杜绝。）
- `valid_until` 过期 → `rejected: expired`。`[KNOWN]` Go 版 `gateway_run.go:94-108 cmdValid` **已校验**，但当前只发本地 event、**不回 `command_reply`** → P1 须补回执。

### 命令状态机（P1 强制）

```
accepted → dispatched → success | failed | timeout | expired
                      ↘ blocked_by_safety / blocked_by_interlock（安全/联锁拒绝）
```

- **Go 现状比 Python 远，但仍不完整** `[KNOWN]`：`controller.go` 已有 `accepted / blocked_by_safety / blocked_by_interlock / write_failed` + 异步 `confirmed / feedback_timeout`（goroutine 轮询回读点，`controller.go:188-231`）。**已经不是 app.py 那种「写成功即假闭环」。**
- **差距（P1 收敛）**：缺正式态 `dispatched / success / expired`；`rejected_expired` 只发 event 不回 reply；**无 `command_id` 幂等**；reply **按点位拆分**（一条多点命令 → 多条 reply，`gateway_run.go:176-178`）。
- **冻结**：`accepted` 仅表示「已受理且下发」，**终态由反馈收敛或超时产生**；现有六态映射进上面的目标状态机（叠加，不推翻）。
- **幂等**：同 `command_id` 只执行一次（Go 现无去重，须加 command_id 表）。
- **多点命令 reply**：允许按点位拆分，但每条须带 `command_id + point_id`；**命令终态 = 各点终态聚合**（云端 `/api/commands/{id}` 做聚合视图）。
- **HTTP 语义**：`POST /api/gateways/{id}/command` 返回 **202 + `command_id`**，`GET /api/commands/{command_id}` 查聚合状态。**不得同步假装执行完成。**

### command_reply schema

```
{ "command_id": str, "ts": int64, "status": <状态机枚举>,
  "achieved": <实测反馈值|null>, "reason": str }
```

---

## 4. 点位命名冻结

- **统一命名**：冻结为 `sec_supply_temp_target`（二次供温设定）等「`_target`」后缀，替换现状代码里的 `sec_supply_temp_sp`（`sp` 后缀）`[KNOWN]`。命令 schema 与云端 UI 一律用冻结名，边缘做一层别名映射到寄存器。
- **可控点位与安全区间**：`[KNOWN]` 同一组值在 Python `app.py SAFE_RANGES`(L39-57) 与 Go `controller.go:15-19 safeRanges` 都有：`valve_open_sp` 0–100、`pump_freq_sp` 0–50Hz、`sec_supply_temp_sp` 20–75℃。
  - ⚠️ **这些区间是代码内置值，对应真实设备量程 (待核实 datasheet)**。按 `heating/CLAUDE.md`「不臆造硬件事实」，冻结前须用点表/datasheet 逐条溯源，错误区间会写坏设备。
  - 安全仲裁**优先用编译产物 `safety_policy`**，无 policy 才回退 `SAFE_RANGES` `[KNOWN]`。

---

## 5. 接入与控制面安全冻结

### 设备接入
- **MQTT 8883 TLS**，边缘做**服务端证书校验**（防中间人）。`[KNOWN]` 现状裸 `socket.create_connection`，无 TLS → 这是 P0a 必须补的。
- **每设备独立凭据**（禁用空口令 / 共享账号）。`[KNOWN]` 现状用户名/密码为空。
- **凭据生命周期**（不只是「有个认证点」）`[INFERRED]`：签发 → 首次烧录 → 轮换 → 吊销 → 设备遗失处理。P0 至少实现签发+烧录+吊销。

### Topic ACL（分方向，非笼统 `station/{id}/#`）`[INFERRED, 采纳 review]`

| 主体 | 允许 publish | 允许 subscribe |
|---|---|---|
| 网关 `{id}` | `station/{id}/{telemetry,alarm,event,heartbeat,command_reply}` | `station/{id}/{property/set,command}` |
| 云后端 | `station/+/{property/set,command}` | `station/+/{telemetry,alarm,event,heartbeat,command_reply}` |

### Web 控制面
- **HTTPS :443**（登录/Cookie/命令接口全程 TLS）+ **CSRF** + **登录限流** + **会话过期**。
- **认证 + RBAC + 操作审计 + 下发审批边界**：拿到后台访问权 ≠ 可随意改供暖设定值。

---

## 6. 云侧存储冻结（PostgreSQL + TimescaleDB）

**三张表**（不要只存整帧 JSONB，也不要只拆长表丢证据）`[INFERRED, 采纳 review]`：

1. **`raw_envelope`**：原始 MQTT 报文（含信封）。审计 + 重放依据。
2. **`point_values`（hypertable）**：规范化 `(device_id, point_id, observed_at, value, q, boot_id, seq)`。趋势 / 降采样 / CAGG 走这张。
3. **`latest_snapshot`**：每 `(device_id, point_id)` 一行，**条件更新（旧帧不覆盖新帧，见 §2）**。

**数据策略（必须明确，缺一不可运行）**：retention（保留期）· 压缩 · 连续聚合 CAGG · 备份恢复 · 磁盘上限告警。

> ⚠️ **部署约束（实测踩坑）** `[KNOWN]`：retention/压缩/CAGG 依赖 TimescaleDB 的 **TSL(community) 许可构建**。发行版包（如 Alpine `postgresql-timescaledb`）是 Apache 许可编译，这些功能直接 `not supported under "apache" license`。**ECS 部署必须用官方 `timescale/timescaledb` docker 镜像**（免费，全功能），不得用发行版包。

**`/api/history` 护栏**：限时间跨度 · 限点位数 · 限返回行数 · 支持降采样。`[INFERRED]` 否则任意时间范围原始点查询会拖垮库和浏览器。

---

## 7. P0 可观测性（最低限度）

`[INFERRED]` MQTT 连接数 · 消费延迟 · 入库失败数 · 重复帧数 · 网关补传积压 · DB 磁盘使用率 · 备份结果。缺了这些，原型出问题无法定位。

---

## 8. HTTP 接口冻结（P0）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/gateways` | 列表 + `online/degraded/offline`（heartbeat TTL + broker 事件 + 最近遥测 综合判定） |
| GET | `/api/gateways/{id}/snapshot` | 最新值（latest_snapshot，非 replay 覆盖） |
| GET | `/api/history` | 限跨度 + 限点数 + 降采样 |
| GET | `/api/alarms` | P0b 云端派生，含生命周期状态 |
| POST | `/api/gateways/{id}/command` | **P1**；202 + `command_id`（不假装同步完成） |
| GET | `/api/commands/{command_id}` | **P1**；查命令状态机结果 |

---

## 9. 边缘实现差距与改动落点（Go migration 分支）

> `[KNOWN]` 已核实 Go 生产代码（`feat/heating-gateway-go-migration`）。**注意两套 MQTT 实现**：生产 daemon（`gatewayc run`）走**根目录** `mqttpub.go`+`runtime.go`+`controller.go`+`gateway_run.go`；`mqtt/gateway_mqtt.go` 是**旧独立二进制**（已含 TLS/atomic seq，但生产不走它，仅作参考）。**P0a 改的是根目录这套。**

| P0a 项 | Go 现状 `[KNOWN]` | 差距 | 改动落点 | 回滚 |
|---|---|---|---|---|
| **MQTT TLS** | `mqttpub.go:33` 硬编码明文 `tcp://`，无 TLS/8883 | **近**：逻辑可直接照搬旧版 `mqtt/gateway_mqtt.go:136-151 buildTLS()`（`x509.NewCertPool`+`LoadX509KeyPair`；**搬时确认 ServerName/CA 校验，勿 InsecureSkipVerify**） | `mqttpub.go`(`NewMqttPub` 加 scheme+`SetTLSConfig`) + `gateway_run.go:156-160`(读 `cfg.mqtt.{tls,ca_certs,cert,key}`) + `loader.go` 补 TLS 字段 | cfg 开关：`mqtt.tls=false` 回落 1883 明文；不删旧路径 |
| **boot_id** | 全仓零痕迹；`runtime.go:19` seq int64，`runtime.go:107` `r.seq++`，**init 0 每次启动归零、不持久化** | **中**：全新概念 | `runtime.go`(`NewRuntime` 生成一次 boot_id，`Telemetry()` 注入信封) | 新增字段，云端旧逻辑忽略未知字段即可；纯增量 |
| **命令 schema+状态机** | `controller.go` **已有** `accepted/blocked_by_safety/blocked_by_interlock/write_failed` + **异步** `confirmed/feedback_timeout`（goroutine 轮询回读，`controller.go:188-231`）；`gateway_run.go:94-108 cmdValid` **已校验 valid_until**（过期发本地 event `rejected_expired`） | **中偏远**：缺 `dispatched/success/expired` 正式态；**无 command_id 幂等**；`rejected_expired` 只发 event **不回 command_reply**；reply **按点位拆分**（一命令多点→多条 reply，`gateway_run.go:176-178`） | `controller.go`+`gateway_run.go` 统一状态机 + command_reply schema + 加 command_id 去重表 | 状态机为叠加语义，保留现有六态映射；幂等表可关 |
| **待传队列持久化** | `mqttpub.go:17` 内存环形 buf（`buffer_max` 默认 5000），满丢最旧；`flush` 标 `replay:true` 保原始 ts/seq；**无落盘，重启全丢** | **中**：`replacement-scope-and-gaps.md:51-52` 已记此 gap（列为待评估） | `mqttpub.go` 缓存改文件/落盘队列（FileStore 或自实现 spool） | 落盘失败回落纯内存 buf |

**已记录的 gap**：`docs/replacement-scope-and-gaps.md` §4 已列 TLS（`:50`）、内存队列持久化（`:51-52`）；**`boot_id` 与命令状态机两项该文档未记，落地时补进去。**

**分支协调**：`feat/heating-gateway-go-migration` 正被并行 session 开发（worktree `/Users/songzijian/Coding/AI-heating` 占用中）。动 Go 代码前须与在飞工作错开，避免抢 `mqttpub.go`/`runtime.go`/`controller.go`。回滚总兜底：`deploy/revert_to_python.sh`（切回 Python 栈）。

**安全文化提示** `[KNOWN]`：`docs/track-b-shadow-plan.md` 表明项目有「影子只读、写路径 `//go:build shadow`+panic 封死」的强约束和 ≥14 天浸泡对拍要求。P0a 碰控制路径须尊重这套，改动走对拍验证。

---

## 10. 开放问题（评审需拍板）

1. **可控点位安全区间溯源**：§4 的量程 (待核实)，谁负责查点表/datasheet。
2. **告警源**：P0b 云端派生是否够用，还是 P0a 就要让边缘发原生 `alarm`（进 `capabilities`）。
3. **`boot_id` 形态**：UUID（推荐，简单）vs 持久化单调 seq（需处理文件损坏/重刷）vs 每帧 `message_id`。§1 暂定 `boot_id`。
4. **capabilities 协商策略**：云端遇到低版本/缺能力网关的降级行为。
5. **凭据烧录方式**：首次如何安全注入每设备凭据（产线/现场）。

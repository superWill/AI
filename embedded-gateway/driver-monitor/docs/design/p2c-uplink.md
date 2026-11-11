# P2c 设计:事件上行 / 两级托管 / 四级分类 / MQTT

- 状态:**Proposed(待评审)** — 评审通过后实现 P2c-a。
- 日期:2026-07-01
- 关联:[ADR-0001 §②③④⑤⑥](../adr/0001-vision-security-boundaries.md);已落地 P0(motion)、P1a(person_observation)、P2a(片段录制)。
- 范围:把本地事件 + 片段证据**可靠上行到 platform**,承载 ADR 的两级托管、两阶段确认、四级运营分类、通知升级、诚实降级。

> 本文只钉 P2c 的**实现设计**;能力/权限边界已由 ADR-0001 钉死,此处不重复,只引用其不变量。

---

## 1. 关键现实:P2c 跨两块板

ADR ④⑤⑥ 把职责切开:

| 板 | 职责 | 本仓关系 |
|---|---|---|
| **视觉板**(本 repo = driver-monitor) | 产事件(motion/person_observation)+ 片段证据(P2a);本地 durable outbox;**推自足事件包给 RK3506**;处理 `custody_ack`;按 `event_id` 响应拉片段。**永不直接上行 platform。** | 已有 P0/P1a/P2a |
| **RK3506**(heating repo,另一块板) | relay outbox;**四级分类 + 工单缓存**(离线自治);MQTT 上行 platform;`delivery_ack`;通知升级;平台心跳目标。 | 逻辑在此仓原型,部署到彼板 |

**四级分类 + MQTT 严格属于 RK3506**,不在视觉板。但它们**全是纯逻辑**,与 P0/P1a/P2a 同样离线可测。**决策(已定):P2c-a 纯逻辑先全部建在本 repo(可移植、单一测试套件),物理部署切分留到上板阶段。**

---

## 2. 子阶段分解

| 子阶段 | 内容 | 依赖 | 可离线 |
|---|---|---|---|
| **P2c-a** | 两阶段托管 outbox 状态机 + 四级分类器 + 工单缓存 + 通知升级 + 幂等去重 + `UplinkTransport` 接口 + Fake | 无(合成时钟 + Fake transport) | ✅ 全部 |
| **P2c-b** | 真 paho-mqtt 接 `UplinkTransport`;视觉板↔RK3506 传输落地 | RK3506 + broker | ✗ 上板 |
| **P2c-c** | platform 契约对接(topic/QoS/ack 语义/工单缓存下发/缩略图传输) | platform 规格 | ✗ 集成 |

本设计详述 **P2c-a**;P2c-b/c 只列接口约束与开放问题。

---

## 3. 模块布局(P2c-a)

```
src/uplink/
  envelope.py         # EventEnvelope:自足事件包
  outbox.py           # DurableOutbox:两阶段托管 + 幂等 + 优先级 + 存储转发
  classify.py         # 四级运营分类器(RK3506 语义)
  workorder_cache.py  # 带版本+TTL 的工单/巡检窗缓存
  escalate.py         # 通知升级状态机(只升通知等级)
  transport.py        # UplinkTransport 接口 + FakeUplinkTransport
```

全部纯 stdlib(无 numpy/gi/网络),ts 注入 → 确定性、可重放、可单测。

---

## 4. 数据模型

### 4.1 `EventEnvelope`(自足事件包,ADR⑤)
```
EventEnvelope{
  event_id:        str      # 稳定 id(motion=ep-*, person=po-*),幂等去重键
  kind:            str      # motion_episode | person_observation | recorder_health | camera_health | uplink_health
  occurred_at:     float    # 事件原始发生时间(单调/epoch),补投永不冒充
  priority_class:  str      # high(person/入侵/健康) | low(visual_prealert:最低耐久档)
  payload:         dict     # 事件本体字段
  thumbnail_ref:   str|None # 小缩略图引用(完整片段留视觉板,按需拉)
  evidence_status: str      # complete | partial | unavailable | pending(接 P2a manifest)
  evidence_ref:    dict|None# {clip event_id, segments, gaps}(P2a as_evidence_ref)
  origin_board:    str      # vision-cam0 等
  schema_version:  str
}
```
构造:视觉板把 person_observation/motion_episode + P2a 的 `ClipManifest.as_evidence_ref()` 打包成 envelope。缩略图小、可内联;完整片段不进 envelope(ADR⑤:只留视觉板按需拉)。

### 4.2 托管三态(视觉板本地 outbox)
```
QUEUED ──push──▶ SENT ──custody_ack──▶ CUSTODY ──delivery_ack──▶ DELIVERED
   ▲              │(超时/断网重推,幂等)
   └──────────────┘
```
- `CUSTODY`:RK3506 已接管副本 → 视觉板**停止重推**(但 **clip 仍不可淘汰**)。
- `DELIVERED`:platform 业务确认(经 RK3506 尽力回传)→ 回喂 P2a `ring.mark_delivered(event_id)`,clip 方获淘汰资格。
- **`custody_ack` 不授权淘汰,只有 `delivery_ack` 授权**(ADR⑤;已在 P2a ring 层实现)。
- 握手幂等:`custody_ack` 回程丢失 → RK3506 重发,视觉板按 event_id 去重,不重复落盘。

### 4.3 RK3506 relay outbox(镜像三态)
```
RECEIVED(持久化)──▶ 回 custody_ack ──▶ QUEUED_UP ──publish──▶ PUBLISHED ──platform delivery_ack──▶ DELIVERED
```
- 两级 outbox **允许重复、禁止静默丢失**;platform + 两级 outbox 均按稳定 `event_id` 幂等去重。
- 视觉板**永不直接重传上行**,只向 RK3506 重新交接;`delivery_ack` 回传视觉板为尽力而为(丢了只多占保留,不丢数据)。

### 4.4 补投与优先级(ADR③)
- 补投序 = **优先级(high 先)→ 原始 `occurred_at`(旧先)**;`sent_at/attempts` 是独立元数据,**绝不用重发时间冒充 `occurred_at`**。
- 分档托管:high = 保证 custody;low(visual_prealert)= 最低耐久档,容量压力下最先淘汰,避免噪声通道饿死真事件。

---

## 5. 四级运营分类器(RK3506 语义,ADR⑥)

**输入**:`person_observation` 事件(带 `occurred_at`)+ 工单缓存窗;(后续)门磁/门禁信号(ADR⑦,依赖设备清单 F1/F2,P2c-a 先不接)。
**输出**:一个**运营分类叠加事件**,引用 person_observation 的 `event_id`,**绝不改底层 person_observation 事实**。

| 分类 | 触发 |
|---|---|
| `expected_presence` | 缓存内有覆盖 `occurred_at` 的**有效**工单/巡检窗(带 `cache_version + as_of_ts`;**不证明身份**) |
| `unverified_presence` | 授权上下文缺失/过期/不可访问 → **默认降级到此** |
| `suspected_intrusion` | 窗口外出现,或与门禁/门磁/工单规则冲突 |

不变量:
- **`confirmed_intrusion` 永不由分类器产生**(只来自值班人员确认或被指定的独立安防系统)。
- **不确定 → `unverified_presence`**,绝不编造 `expected_presence`,绝不冒充分类。
- **缓存过期 + 断网 → 降级 `unverified_presence`**,不假装完成授权判断。
- `suspected_intrusion` 需人工双向裁决;裁决仅在治理下改进规则,**绝不自动回调权威规则**。
- 分类是**运营层叠加**,person_observation 事实原样保留、照常上行。

---

## 6. 工单缓存(`workorder_cache.py`)

- platform 是工单/巡检窗**权威源**,RK3506 **缓存带版本 + 有效期**。
- `as_of_ts`:缓存快照时间;`cache_version`:平台侧版本(可能因撤销而 stale)。
- 断网且缓存过期 → 分类降级 `unverified_presence`(见 §5)。
- **高安防场景缓存有效期要短**(平台侧撤销后 stale 窗越短越安全)。
- P2c-a 离线:用注入的缓存快照测「有效窗→expected」「过期→降级」「无窗→unverified/suspected」。

---

## 7. 通知升级(`escalate.py`,ADR②)

- 可通知事件(person_observation / suspected_intrusion / 健康告警)→ `NOTIFY_L1` 推值班岗 + **要求 ack**。
- ack 在 `T1` 内 → 解决。
- 超 `T1` 无 ack → `NOTIFY_L2`(更多人 / 更响)→ 超 `T2` → `L3` …(有上限)。
- **升级只升通知等级(谁被 ping、多响),永不升事件分类、永不升火警等级。**
- 真火响应由认证链自主联动,**不在人工 ack 关键路径上**(无人值守/ack 慢不危及消防)。
- ts 注入、确定性;纯计时状态机。

---

## 8. 接口:`UplinkTransport`

```
UplinkTransport(ABC):
  publish(envelope) -> local_msg_id        # 发一条,返回本地句柄
  poll() -> list[Inbound]                  # 拉入站:custody_ack / delivery_ack / 缓存更新 / 连接状态
```
- `FakeUplinkTransport`(离线):可脚本化模拟 custody/delivery ack、丢包、重连、重复投递、断网窗口。
- 真 MQTT(P2c-b):paho-mqtt;QoS/topic/ack 见 §10 开放问题。

---

## 9. 健康信号(ADR③)

以下**本身产 `uplink_health` 高优先事件**(经 outbox 上行,不静默):
- outbox 积压深度 / 最旧未投递事件年龄 超阈值。
- 磁盘逼近上限(复用 P2a ring 的 `disk_pressure`)。
- **通知链失联**(无 ack 回路 / broker 长断)。
- RK3506 是「上报」单点 → 其存活须 **platform 侧心跳监测**(死网关报不了自己的死;此为 platform 侧约束,记录在案)。

---

## 10. 离线测试计划(P2c-a,纯 stdlib)

- **outbox**:三态迁移;幂等(重复 push/ack 不重复落盘);补投序=优先级→occurred_at;`custody_ack` 不授权淘汰、`delivery_ack` 才回喂 ring;断网存储转发不丢;积压→health;low 档容量压力先淘、不饿死 high。
- **classify**:有效窗→expected(带 version/as_of);无窗→suspected;缓存缺失/过期→unverified;**confirmed 永不自动**;分类不改底层事实。
- **workorder_cache**:版本/TTL;过期降级;撤销(新版本)使旧窗失效。
- **escalate**:ack 及时→解决;超时逐级升;**升级不改事件分类**;火警路径不受 ack 影响。
- **transport(Fake)**:custody/delivery 往返;custody_ack 回程丢失→重发+去重;重连后不重复投递。
- **端到端**:person_observation(+P2a evidence_ref)→ envelope → outbox → Fake transport → custody → delivery → 回喂 ring.mark_delivered;蒸汽(无 person 事件)不产 envelope。

---

## 11. 开放问题(platform 契约,多数需 platform 规格 / 上板才定)

- **F-U1**:MQTT topic 结构 + QoS?(建议 **QoS1 at-least-once + 幂等去重**,而非 QoS2;去重已由 event_id 保证)
- **F-U2**:`delivery_ack` 语义 —— 必须是 platform **业务确认**,不是 broker PUBACK(ADR⑤:custody_ack≠平台已收)。契约需明确业务 ack 的 topic/字段。
- **F-U3**:工单缓存下发机制 —— retained MQTT topic 推送 vs REST 拉?TTL 策略?高安防短 TTL?
- **F-U4**:缩略图传输 —— 内联 base64 vs 独立拉取?MQTT payload 上限?
- **F-U5**:门磁/门禁融合(ADR⑦,喂 `suspected_intrusion`)依赖设备清单 F1/F2 —— P2c-a 先留接口不接。
- **F-U6**:是否已有可对接的 platform + RK3506,还是 spec-ahead(如 P1b/P2b)?决定 P2c-b/c 何时能验。

---

## 12. 不变量清单(实现须逐条守,来自 ADR ②③④⑤⑥)

1. 证据不静默覆盖;两级 outbox 禁止静默丢失,允许重复 + 幂等去重。
2. 补投按优先级 + 原始发生时间,**不冒充发生时间**。
3. 淘汰资格 = `delivery_ack`,**永不 = `custody_ack`**。
4. 视觉板永不直接上行 platform,只向 RK3506 交接。
5. 四级分类是运营叠加,`confirmed_intrusion` 永不自动;不确定→`unverified_presence`,不编造。
6. 缓存过期+断网→诚实降级,不假装完成授权判断;`expected_presence` 带版本+as-of。
7. 通知升级只升通知等级,永不升事件分类/火警等级;火警响应不在人工 ack 关键路径。
8. 队列积压/磁盘逼近/通知链失联本身产健康告警;RK3506 存活须 platform 心跳。

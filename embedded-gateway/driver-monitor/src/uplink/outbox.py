#!/usr/bin/env python3
"""durable 上行 outbox —— 纯逻辑。两阶段托管 + 幂等 + 优先级 + 存储转发。ADR-0001 ③⑤。

**独立于遥测环**:遥测可丢旧值,证据/事件不可静默丢。每条包三态推进:
  QUEUED ─push→ SENT ─custody_ack→ CUSTODY ─delivery_ack→ DELIVERED
- CUSTODY:RK3506 已接管副本 → 停止重推(但 clip 仍不可淘汰)。
- DELIVERED:platform 业务确认 → 回调 on_delivered(据此喂 P2a ring.mark_delivered)。
- 断网:publish 返回 None → 留队重试(存储转发)。
- 补投序:优先级(high 先)→ 原始 occurred_at(旧先);**绝不用重发时刻冒充 occurred_at**。
- 幂等:按 msg_key 去重;重复 enqueue/ack 不重复落盘、不回退状态。
- 禁止静默丢失:high 永不丢(积压发健康告警);low 档超容量**淘汰但发 low_priority_dropped**,非静默。

注意(P2c-b 补):当前 `_entries`/`_delivered_keys` 为**内存态**,重启即失;真正的跨重启
durable 依赖 P2a 环上 pin 的证据 + P2c-b 的持久化 outbox。名字里的 "durable" 指语义目标,
非当前实现已跨重启。
"""
from __future__ import annotations

from dataclasses import dataclass, field


class OutboxState:
    QUEUED = "queued"
    SENT = "sent"
    CUSTODY = "custody"
    DELIVERED = "delivered"


@dataclass
class OutboxConfig:
    resend_after_s: float = 30.0        # SENT 无 custody_ack 超此重推
    max_backlog: int = 1000             # 未 delivered 条数超此 → backlog 告警
    oldest_age_warn_s: float = 300.0    # 最旧未投递年龄超此 → 告警
    low_priority_cap: int = 200         # low 档未投递上限,超则最先淘汰 low(发告警,非静默)


@dataclass
class _Entry:
    envelope: object
    state: str
    enqueued_at: float
    last_send_ts: float = -1e18
    attempts: int = 0
    priority_rank: int = field(default=1)   # low=0, high=1(供发送/淘汰排序)


_RANK = {"low": 0, "high": 1}


class DurableOutbox:
    def __init__(self, transport, config: OutboxConfig | None = None,
                 on_delivered=None):
        """on_delivered(envelope):投递确认回调(如 lambda e: ring.mark_delivered(e.event_id))。"""
        self.transport = transport
        self.cfg = config or OutboxConfig()
        self._on_delivered = on_delivered
        self._entries: dict[str, _Entry] = {}     # msg_key → entry
        self._delivered_keys: set[str] = set()      # 已投递 msg_key(幂等,拒重复入队)
        self._backlog_reported = False

    # ---- 入队(幂等) ----
    def enqueue(self, envelope, now: float) -> list[dict]:
        key = envelope.msg_key
        if key in self._delivered_keys or key in self._entries:
            return []                               # 已投递 / 在队 → 幂等忽略
        self._entries[key] = _Entry(
            envelope=envelope, state=OutboxState.QUEUED, enqueued_at=now,
            priority_rank=_RANK.get(envelope.priority_class, 1))
        return self._cap_low_priority(now)

    # ---- 驱动:收 ack + 发送 + 健康 ----
    def pump(self, now: float) -> list[dict]:
        health: list[dict] = []
        self._drain_acks()
        self._send_due(now)
        health += self._backlog_health(now)
        return health

    def _drain_acks(self) -> None:
        for msg in self.transport.poll():
            entry = self._entries.get(msg.msg_key) if msg.msg_key else None
            if msg.kind == "custody_ack" and entry is not None:
                if entry.state in (OutboxState.QUEUED, OutboxState.SENT):
                    entry.state = OutboxState.CUSTODY          # 停止重推
            elif msg.kind == "delivery_ack":
                self._mark_delivered(msg.msg_key)

    def _mark_delivered(self, key: str) -> None:
        entry = self._entries.pop(key, None)
        if entry is None:
            return                                             # 未知/重复 ack:不毒化 _delivered_keys、不误回调
        self._delivered_keys.add(key)                          # 幂等:后续重复 ack/入队忽略
        if self._on_delivered is not None:
            self._on_delivered(entry.envelope)

    def _send_due(self, now: float) -> None:
        # 补投序:high 先(rank 降序)→ 原始 occurred_at 旧先
        due = [e for e in self._entries.values()
               if e.state == OutboxState.QUEUED
               or (e.state == OutboxState.SENT
                   and now - e.last_send_ts >= self.cfg.resend_after_s)]
        due.sort(key=lambda e: (-e.priority_rank, e.envelope.occurred_at))
        for e in due:
            msg_id = self.transport.publish(e.envelope)
            if msg_id is None:                                 # 断网 → 留队(存储转发)
                continue
            e.state = OutboxState.SENT
            e.last_send_ts = now
            e.attempts += 1

    # ---- 容量:low 档超限淘汰(发告警,非静默) ----
    def _cap_low_priority(self, now: float) -> list[dict]:
        lows = [e for e in self._entries.values() if e.priority_rank == 0]
        if len(lows) <= self.cfg.low_priority_cap:
            return []
        # 只淘 QUEUED 的 low(尚未交接);在途(SENT/CUSTODY)的不丢——否则其 delivery_ack
        # 会 no-op,on_delivered 永不触发,带证据的 clip 就永远 pin 死在环上。
        droppable = [e for e in lows if e.state == OutboxState.QUEUED]
        if not droppable:
            return []
        droppable.sort(key=lambda e: e.envelope.occurred_at)    # 最旧的可淘 low 先淘
        drop = droppable[0]
        self._entries.pop(drop.envelope.msg_key, None)
        return [self._health("low_priority_dropped",
                             f"low outbox over cap {self.cfg.low_priority_cap}, "
                             f"dropped {drop.envelope.msg_key}", now)]

    # ---- 健康:积压 / 最旧年龄 ----
    def _backlog_health(self, now: float) -> list[dict]:
        pending = list(self._entries.values())
        oldest_age = max((now - e.enqueued_at for e in pending), default=0.0)
        over = (len(pending) > self.cfg.max_backlog
                or oldest_age > self.cfg.oldest_age_warn_s)
        if over and not self._backlog_reported:
            self._backlog_reported = True
            return [self._health("uplink_backlog",
                                 f"{len(pending)} pending, oldest {round(oldest_age, 1)}s", now)]
        if not over:
            self._backlog_reported = False
        return []

    def _health(self, status: str, detail: str, ts: float) -> dict:
        return {"type": "uplink_health", "status": status,
                "detail": detail, "ts": round(ts, 3)}

    # ---- 只读 ----
    def state_of(self, msg_key: str) -> str | None:
        if msg_key in self._delivered_keys:
            return OutboxState.DELIVERED
        e = self._entries.get(msg_key)
        return e.state if e else None

    @property
    def pending_count(self) -> int:
        return len(self._entries)

    def pending_keys(self) -> list[str]:
        return list(self._entries.keys())

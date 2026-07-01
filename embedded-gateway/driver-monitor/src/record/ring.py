#!/usr/bin/env python3
"""录像段环形存储 —— 纯逻辑,证据保留策略的核心。ADR-0001 ③⑤。

跟踪段/总量/pin 集,按上限淘汰旧段;但**证据不可静默覆盖**:
淘汰序 = 未 pin 普通段 → 已 delivery 的 pin 段(低优先在前)→ **未 delivery 的 pin 段永不删**
(逼上限只发健康告警,不删)。pre-roll 地板保最近 R_pre 秒,保证下个事件有前卷。

不变量(ADR ③⑤):
  - 未 delivery 的 pin 段永不静默删。
  - **`custody_ack` 不授予淘汰资格,只有 `delivery_ack` 授予**(两阶段确认;custody 只是 RK3506 接管副本)。
  - `mark_lost` 是**显式损失**(磁盘损坏等),发 `evidence_loss` 健康信号,非静默丢。
  - 队列积压/磁盘逼近/写停滞 → 设备健康告警。
"""
from __future__ import annotations

from dataclasses import dataclass

from .segment_source import SegmentRecord

# 事件优先级 → 淘汰排位(数值小者先淘汰):低耐久档(visual_prealert)先于高档(person/入侵)
_PRIORITY_RANK = {"low": 0, "high": 1}


@dataclass
class RingConfig:
    max_bytes: int
    pre_roll_floor_s: float = 5.0      # 保最近这些秒的段不淘汰(下个事件的前卷地板)
    disk_warn_frac: float = 0.9        # 总量达上限此比例 → disk_pressure 告警
    write_stall_s: float = 6.0         # 无新段超过此秒 → write_stall 告警


class SegmentRing:
    def __init__(self, config: RingConfig):
        self.cfg = config
        self._segs: dict[int, SegmentRecord] = {}
        self._pins: dict[int, set[str]] = {}        # seg_id → 引用它的 event_id 集
        self._event_priority: dict[str, str] = {}
        self._delivered: set[str] = set()
        self._custody: set[str] = set()
        self._total_bytes = 0
        self._last_add_ts: float | None = None
        self._disk_reported = False
        self._overcap_reported = False
        self._stall_reported = False

    # ---- 段读写 ----
    def add(self, seg: SegmentRecord) -> list[dict]:
        self._segs[seg.seg_id] = seg
        self._total_bytes += seg.bytes
        self._last_add_ts = seg.end_ts
        self._stall_reported = False
        return self._disk_health()

    def get(self, seg_id: int) -> SegmentRecord | None:
        return self._segs.get(seg_id)

    def segments(self):
        return list(self._segs.values())

    def __contains__(self, seg_id: int) -> bool:
        return seg_id in self._segs

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    # ---- pin / 两阶段确认 ----
    def pin(self, seg_id: int, event_id: str, priority: str = "high") -> None:
        if seg_id in self._segs:
            self._pins.setdefault(seg_id, set()).add(event_id)
            self._event_priority[event_id] = priority

    def mark_custody(self, event_id: str) -> None:
        """RK3506 接管副本 —— **不**授予淘汰资格(证据仍须留在视觉板直到 delivery)。"""
        self._custody.add(event_id)

    def mark_delivered(self, event_id: str) -> None:
        """平台业务确认 —— 授予其 pin 段淘汰资格。"""
        self._delivered.add(event_id)

    def mark_lost(self, seg_id: int) -> list[dict]:
        """显式损失(磁盘损坏/文件丢失),非淘汰。发 evidence_loss,绝不静默。"""
        seg = self._segs.pop(seg_id, None)
        if seg is not None:
            self._total_bytes -= seg.bytes
        evs = self._pins.pop(seg_id, None) or set()
        self._forget_if_orphaned(evs)
        return [self._health("evidence_loss", f"segment {seg_id} lost",
                             self._last_add_ts or 0.0)]

    # ---- 淘汰 ----
    def prune(self, now: float) -> tuple[list[SegmentRecord], list[dict]]:
        evicted: list[SegmentRecord] = []
        health: list[dict] = []
        floor_ts = now - self.cfg.pre_roll_floor_s
        while self._total_bytes > self.cfg.max_bytes:
            victim = self._pick_victim(floor_ts)
            if victim is None:                     # 只剩未投递 pin 段/地板 → 不删,告警
                if not self._overcap_reported:
                    self._overcap_reported = True
                    health.append(self._health(
                        "over_cap_pinned",
                        f"over cap {self._total_bytes}/{self.cfg.max_bytes}: "
                        f"only undelivered-pinned or pre-roll-floor left", now))
                break
            seg = self._segs.pop(victim)
            self._total_bytes -= seg.bytes
            evs = self._pins.pop(victim, None) or set()
            evicted.append(seg)
            self._forget_if_orphaned(evs)          # 段没了就忘掉只被它引用的事件元数据(防泄漏)
        else:
            self._overcap_reported = False         # 正常收敛到上限内
        health += self._disk_health()
        health += self._stall_health(now)
        return evicted, health

    def _pick_victim(self, floor_ts: float) -> int | None:
        """挑一个可淘汰段:排除 pre-roll 地板内、排除未投递 pin 段;
        排序键(升序,取第一个):未 pin(0) 先于 pin(1);低优先先于高优先;最旧先。"""
        cands = []
        for sid, seg in self._segs.items():
            if seg.end_ts > floor_ts:              # pre-roll 地板保护
                continue
            if self._undelivered_pinned(sid):      # 未投递 pin 段永不删
                continue
            cands.append(sid)
        if not cands:
            return None
        cands.sort(key=lambda s: (1 if self._pins.get(s) else 0,
                                  self._seg_priority(s), s))
        return cands[0]

    def _forget_if_orphaned(self, event_ids: set[str]) -> None:
        """段被移除后,若某 event 已无任何 pin 段引用 → 丢弃其元数据(event_id 唯一不复用,安全)。"""
        if not event_ids:
            return
        live: set[str] = set()
        for evs in self._pins.values():
            live |= evs
        for eid in event_ids:
            if eid not in live:
                self._event_priority.pop(eid, None)
                self._delivered.discard(eid)
                self._custody.discard(eid)

    def _undelivered_pinned(self, seg_id: int) -> bool:
        evs = self._pins.get(seg_id)
        return bool(evs) and any(e not in self._delivered for e in evs)

    def _seg_priority(self, seg_id: int) -> int:
        evs = self._pins.get(seg_id, set())
        ranks = [_PRIORITY_RANK.get(self._event_priority.get(e, "high"), 1) for e in evs]
        return max(ranks) if ranks else 0

    # ---- 健康信号(去重:仅状态跳变时报一次) ----
    def _disk_health(self) -> list[dict]:
        pressured = self._total_bytes >= self.cfg.disk_warn_frac * self.cfg.max_bytes
        if pressured and not self._disk_reported:
            self._disk_reported = True
            return [self._health("disk_pressure",
                                 f"{self._total_bytes}/{self.cfg.max_bytes} bytes",
                                 self._last_add_ts or 0.0)]
        if not pressured:
            self._disk_reported = False
        return []

    def _stall_health(self, now: float) -> list[dict]:
        if (self._last_add_ts is not None and not self._stall_reported
                and now - self._last_add_ts >= self.cfg.write_stall_s):
            self._stall_reported = True
            return [self._health("write_stall",
                                 f"no segment for {round(now - self._last_add_ts, 1)}s", now)]
        return []

    def _health(self, status: str, detail: str, ts: float) -> dict:
        return {"type": "recorder_health", "status": status,
                "detail": detail, "ts": round(ts, 3)}

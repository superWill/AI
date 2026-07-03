#!/usr/bin/env python3
"""自足事件包 —— 上行的最小单元。纯数据,零依赖。ADR-0001 ⑤。

把本地事件(person_observation/motion_episode/健康)+ P2a 的片段证据引用打包成一个
**自足**的包:元数据 + 缩略图引用 + evidence_status/ref(完整片段留视觉板按需拉)。

- `event_id`:稳定关联键(证据/去重/幂等都用它)。
- `msg_key`:**消息级**幂等键。person_observation 的 OPEN 与 CLOSE 共享 event_id 但是两条
  不同消息 → msg_key 用 `event_id:phase` 区分,二者都要投递,不能互相当重复删掉。
- `occurred_at`:事件**原始发生时间**,补投永不冒充(用重发时刻覆盖它)。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 事件类别 → 优先级档(ADR⑤:入侵/健康=high 保证 custody;实验性=low 最低耐久)
_PRIORITY_BY_KIND = {
    "person_observation": "high",
    "suspected_intrusion": "high",
    "recorder_health": "high",
    "camera_health": "high",
    "uplink_health": "high",
    "motion_episode": "low",
    "visual_prealert": "low",
}


@dataclass
class EventEnvelope:
    event_id: str
    kind: str
    occurred_at: float
    priority_class: str = "high"          # high | low
    payload: dict = field(default_factory=dict)
    thumbnail_ref: str | None = None
    evidence_status: str = "pending"      # complete | partial | unavailable | pending
    evidence_ref: dict | None = None      # 接 P2a ClipManifest.as_evidence_ref()
    origin_board: str = "vision-cam0"
    schema_version: str = "envelope-v1"
    msg_key: str = ""                     # 消息级幂等键;空则回落 event_id

    def __post_init__(self):
        if not self.msg_key:
            self.msg_key = self.event_id

    @classmethod
    def from_event(cls, ev: dict, *, kind: str | None = None,
                   evidence_ref: dict | None = None, thumbnail_ref: str | None = None,
                   origin_board: str = "vision-cam0") -> "EventEnvelope":
        """从事件 dict(person_observation/motion_episode/健康)构造包。"""
        kind = kind or ev.get("type", "")
        event_id = ev["event_id"]
        phase = ev.get("event_kind", "")               # open | close(若有)
        occurred = ev.get("ts_start", ev.get("ts", 0.0))
        status = evidence_ref.get("evidence_status", "pending") if evidence_ref else "pending"
        return cls(
            event_id=event_id,
            kind=kind,
            occurred_at=occurred,
            priority_class=_PRIORITY_BY_KIND.get(kind, "high"),
            payload=dict(ev),
            thumbnail_ref=thumbnail_ref,
            evidence_status=status,
            evidence_ref=evidence_ref,
            origin_board=origin_board,
            msg_key=f"{event_id}:{phase}" if phase else event_id,
        )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "msg_key": self.msg_key,
            "kind": self.kind,
            "occurred_at": self.occurred_at,
            "priority_class": self.priority_class,
            "payload": self.payload,
            "thumbnail_ref": self.thumbnail_ref,
            "evidence_status": self.evidence_status,
            "evidence_ref": self.evidence_ref,
            "origin_board": self.origin_board,
            "schema_version": self.schema_version,
        }

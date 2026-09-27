#!/usr/bin/env python3
"""事件→录像片段 映射 —— 纯逻辑。把 person_observation 事件绑到一段录像证据上。ADR-0001 ⑤。

- OPEN(event_id, ts_start):pin **前卷** [ts_start-R_pre, ts_start](ring 里已有的段);
  之后**滚动 pin** 事件期间到达的每个新段。
- CLOSE(event_id, ts_end):转 CLOSING,继续 pin 到 **后卷** ts_end+R_post 截止,然后 finalize。
- finalize → `ClipManifest{event_id, 有序段, gaps, evidence_status, lost_segments}`,
  `as_evidence_ref()` 挂回事件。

evidence_status(ADR ⑤:片段丢 → 事件仍在,标状态):
  - `unavailable`:**core 段(重叠事件窗 [ts_start,ts_end])丢失** —— 事件期间发生什么无法重建。
  - `partial`:仅前/后卷段丢 / 段含 has_gap / 时间覆盖有缺口。
  - `complete`:全 present、无缺口。

不变量:补投不冒充发生时间(manifest 时间全取段/事件原始 ts);淘汰资格只认 delivery(在 ring 层)。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ClipConfig:
    r_pre: float = 5.0                  # 前卷秒数
    r_post: float = 5.0                 # 后卷秒数


@dataclass
class ClipManifest:
    event_id: str
    ts_start: float
    ts_end: float
    segments: list[int]                 # present 段 id,按时间序
    gaps: list[tuple[float, float]]     # 跨度内未覆盖的时间区间
    lost_segments: list[int]            # pin 过但已丢失的段 id
    evidence_status: str                # complete | partial | unavailable

    def as_evidence_ref(self) -> dict:
        """挂回事件的证据引用(person_observation 事件据此带 evidence_status)。"""
        return {
            "event_id": self.event_id,
            "evidence_status": self.evidence_status,
            "segments": list(self.segments),
            "gaps": [list(g) for g in self.gaps],
            "lost_segments": list(self.lost_segments),
            "ts_start": self.ts_start,
            "ts_end": self.ts_end,
        }


class _OpenClip:
    def __init__(self, event_id: str, ts_start: float, priority: str):
        self.event_id = event_id
        self.ts_start = ts_start
        self.priority = priority
        self.ts_end: float | None = None
        self.deadline: float | None = None
        self.closing = False
        self.pinned: dict[int, tuple[float, float]] = {}   # seg_id → (start_ts,end_ts) 记录时快照


class ClipManager:
    """把 person_observation OPEN/CLOSE 映射成录像片段并 pin 进 ring。"""

    def __init__(self, ring, config: ClipConfig | None = None):
        self.ring = ring
        self.cfg = config or ClipConfig()
        self._open: dict[str, _OpenClip] = {}

    # ---- 事件驱动 ----
    def on_person_open(self, event_id: str, ts_start: float, priority: str = "high") -> None:
        clip = _OpenClip(event_id, ts_start, priority)
        lo = ts_start - self.cfg.r_pre
        for seg in self.ring.segments():           # 前卷:pin ring 里已有、重叠 [ts_start-R_pre, ts_start] 的段
            if seg.overlaps(lo, ts_start):
                self._pin(clip, seg)
        self._open[event_id] = clip

    def on_segment(self, seg) -> list[ClipManifest]:
        """新段到达:对每个 open/closing clip 滚动 pin;CLOSING 过后卷截止则 finalize。"""
        finalized: list[ClipManifest] = []
        for clip in list(self._open.values()):
            if clip.closing:
                if seg.start_ts >= clip.deadline:  # 后卷已满 → 收尾(本段属后卷之外,不 pin)
                    finalized.append(self._finalize(clip))
                elif seg.overlaps(clip.ts_start - self.cfg.r_pre, clip.deadline):
                    self._pin(clip, seg)
            else:                                  # OPEN:事件期新段全 pin(滚动)
                if seg.end_ts > clip.ts_start - self.cfg.r_pre:
                    self._pin(clip, seg)
        return finalized

    def on_person_close(self, event_id: str, ts_end: float) -> None:
        clip = self._open.get(event_id)
        if clip is None:
            return
        clip.ts_end = ts_end
        clip.closing = True
        clip.deadline = ts_end + self.cfg.r_post

    def tick(self, now: float) -> list[ClipManifest]:
        """定时收尾:CLOSING 的 clip 到达后卷截止(即使无新段,如录制停)也 finalize。"""
        finalized = []
        for clip in list(self._open.values()):
            if clip.closing and clip.deadline is not None and now >= clip.deadline:
                finalized.append(self._finalize(clip))
        return finalized

    def force_finalize_all(self) -> list[ClipManifest]:
        """关机等:收尾所有未决 clip(不留悬空 pin)。"""
        return [self._finalize(c) for c in list(self._open.values())]

    # ---- 内部 ----
    def _pin(self, clip: _OpenClip, seg) -> None:
        clip.pinned[seg.seg_id] = (seg.start_ts, seg.end_ts)
        self.ring.pin(seg.seg_id, clip.event_id, clip.priority)

    def _finalize(self, clip: _OpenClip) -> ClipManifest:
        self._open.pop(clip.event_id, None)
        ts_start = clip.ts_start
        ts_end = clip.ts_end if clip.ts_end is not None else ts_start
        span_lo = ts_start - self.cfg.r_pre
        span_hi = ts_end + self.cfg.r_post

        present = []
        lost = []                                  # (seg_id, start, end) 记录时快照,供 core/roll 判定
        for sid, (s, e) in sorted(clip.pinned.items()):
            seg = self.ring.get(sid)
            if seg is None:
                lost.append((sid, s, e))
            else:
                present.append(seg)
        present.sort(key=lambda s: s.start_ts)

        # core 段 = 重叠事件窗 [ts_start, ts_end];仅前/后卷 = roll
        core_lost = any(e > ts_start and s < ts_end for (_, s, e) in lost) \
            if ts_end > ts_start else any(e >= ts_start and s <= ts_start for (_, s, e) in lost)
        gaps = self._gaps(present, span_lo, span_hi)
        has_gap_flag = any(s.has_gap for s in present)

        if core_lost:
            status = "unavailable"
        elif lost or has_gap_flag or gaps:
            status = "partial"
        else:
            status = "complete"

        return ClipManifest(
            event_id=clip.event_id,
            ts_start=round(ts_start, 3),
            ts_end=round(ts_end, 3),
            segments=[s.seg_id for s in present],
            gaps=gaps,
            lost_segments=[sid for (sid, _, _) in lost],
            evidence_status=status,
        )

    def _gaps(self, present, lo: float, hi: float, eps: float = 1e-6):
        """跨度 [lo,hi] 内未被 present 段覆盖的时间区间。"""
        gaps = []
        cursor = lo
        for s in present:
            if s.start_ts > cursor + eps:
                gaps.append((round(cursor, 3), round(s.start_ts, 3)))
            cursor = max(cursor, s.end_ts)
        if cursor < hi - eps:
            gaps.append((round(cursor, 3), round(hi, 3)))
        return gaps

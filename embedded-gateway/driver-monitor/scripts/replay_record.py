#!/usr/bin/env python3
"""离线回放 —— P2a 片段录制整链(纯逻辑,不依赖板子/splitmuxsink/numpy)。

合成录像段流(FakeSegmentSource)+ 注入 person_observation 事件,演示:
  - 真人事件 → pin 前卷/滚动/后卷 → ClipManifest(evidence_status)。
  - 事件期录像缺口 → partial。
  - 蒸汽期(无 person 事件)→ 只录像、不产 clip。
  - 健康信号(磁盘/积压/写停滞)。

  python3 scripts/replay_record.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.segment_source import FakeSegmentSource                # noqa: E402
from record.ring import SegmentRing, RingConfig                    # noqa: E402
from record.clip import ClipManager, ClipConfig                    # noqa: E402


# person_observation 事件(来自 P1 confirm):(ts, kind, event_id)
PERSON_EVENTS = [
    (6.0, "open", "po-000001"),      # 真人 A:完整证据
    (8.0, "close", "po-000001"),
    (24.0, "open", "po-000002"),     # 真人 B:事件期录像有缺口 → partial
    (26.0, "close", "po-000002"),
]
GAP_SEGMENTS = {24}                  # 段24 落在 po-000002 事件窗内且 has_gap


def main() -> int:
    src = FakeSegmentSource(seg_dur=1.0, seg_bytes=100, gap_at=GAP_SEGMENTS)
    ring = SegmentRing(RingConfig(max_bytes=10**9))   # demo 不聚焦淘汰
    cm = ClipManager(ring, ClipConfig(r_pre=5.0, r_post=5.0))
    pe = sorted(PERSON_EVENTS)
    pi = 0
    manifests = []
    print("回放 0–35s:录像段流 + person_observation 事件(蒸汽期无事件)\n")

    now = 0.0
    while now <= 35.0 + 1e-9:
        for seg in src.poll(now):
            ring.add(seg)
            manifests += _tag(cm.on_segment(seg))
        while pi < len(pe) and pe[pi][0] <= now + 1e-9:
            ts, kind, eid = pe[pi]; pi += 1
            if kind == "open":
                cm.on_person_open(eid, ts)
                print(f"  t={ts:5.1f}s  person OPEN  {eid}  → pin 前卷 [{ts - 5:.0f},{ts:.0f}] + 滚动")
            else:
                cm.on_person_close(eid, ts)
                print(f"  t={ts:5.1f}s  person CLOSE {eid}  → 后卷至 {ts + 5:.0f}s 收尾")
        for m in _tag(cm.tick(now)):
            manifests.append(m)
        ring.prune(now)
        now = round(now + 1.0, 3)

    print("\n生成的证据片段(ClipManifest):")
    for m in manifests:
        print(f"  {m.event_id}: status={m.evidence_status:12} "
              f"segs={m.segments[0]}..{m.segments[-1]}({len(m.segments)}) "
              f"gaps={m.gaps} lost={m.lost_segments}")

    by_id = {m.event_id: m for m in manifests}
    ok = (len(manifests) == 2
          and by_id["po-000001"].evidence_status == "complete"
          and by_id["po-000002"].evidence_status == "partial")
    print(f"\n结论:{'✅ 真人产 clip(A 完整 / B 缺口=partial);蒸汽期不产 clip' if ok else '⚠️ 异常'}")
    return 0 if ok else 1


def _tag(mans):
    for m in mans:
        print(f"  >>> CLIP finalize {m.event_id}  status={m.evidence_status}  "
              f"{len(m.segments)} 段")
    return list(mans)


if __name__ == "__main__":
    sys.exit(main())

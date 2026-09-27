#!/usr/bin/env python3
"""离线回放 —— P1a 运动门控 + 人体确认整链(纯逻辑,不依赖板子/numpy)。

合成两幕,验两条必经路径(ADR-0001 ⑥):
  幕一「蒸汽」:一直有 motion,没人(偶发区外误检)→ motion 有 episode,但**零 person_observation**。
  幕二「真人」:motion + person 在 ROI → person_observation OPEN;人走(蒸汽维持 motion)→
             person_left CLOSE;motion 再停 → motion episode 收尾。

  python3 scripts/replay_confirm.py
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from motion.episode import EpisodeStateMachine, EpisodeConfig    # noqa: E402
from vision.confirm import PersonConfirmer, ConfirmConfig         # noqa: E402
from vision.person_detector import MockPersonDetector, PersonBox  # noqa: E402
from roi.mask import RoiMask                                      # noqa: E402

ROI = RoiMask([(100, 100), (300, 100), (300, 300), (100, 300)])
IN_ROI = PersonBox(180, 180, 220, 260, 0.92)
OUT_ROI = PersonBox(0, 0, 40, 40, 0.80)
FPS = 15


def build_trace():
    """[(label, moving, score, boxes), ...]。两幕:蒸汽 → 真人。"""
    tr = []
    # 幕一 蒸汽:40 帧 moving + 偶发区外误检,再 35 帧静止
    for i in range(40):
        tr.append(("steam", True, 0.06, [OUT_ROI] if i % 7 == 0 else []))
    tr += [("steam", False, 0.0, [])] * 35
    # 幕二 真人:person 在 ROI 25 帧,离开(motion 仍在)15 帧,再 35 帧静止收尾
    for _ in range(25):
        tr.append(("person", True, 0.25, [IN_ROI]))
    for _ in range(15):
        tr.append(("person", True, 0.08, []))        # 人走了,蒸汽维持 motion
    tr += [("person", False, 0.0, [])] * 35
    return tr


def main() -> int:
    ep = EpisodeStateMachine(EpisodeConfig(n_enter=4, n_exit=30))
    cf = PersonConfirmer(ConfirmConfig(k_window=5, m_confirm=3, person_exit_frames=15))
    trace = build_trace()
    dt = 1.0 / FPS
    print(f"回放 {len(trace)} 帧(合成:蒸汽幕 → 真人幕)@ {FPS}fps\n")

    motion_ev, person_ev = [], []
    cur_motion_id = None
    t = 0.0
    for label, moving, score, boxes in trace:
        for e in ep.update(round(t, 6), moving, score):
            motion_ev.append(e)
            if e["event_kind"] == "open":
                cur_motion_id = e["event_id"]
                print(f"  t={t:6.2f}s [{label:6}] motion OPEN  {e['event_id']}")
            else:
                print(f"  t={t:6.2f}s [{label:6}] motion CLOSE {e['event_id']} "
                      f"dur={e['duration_s']}s")
        active = ep.active
        det = ROI.filter_boxes(MockPersonDetector(default=boxes).detect(None)) if active else []
        for e in cf.update(round(t, 6), active, det, motion_event_id=cur_motion_id):
            person_ev.append(e)
            if e["event_kind"] == "open":
                print(f"  t={t:6.2f}s [{label:6}]   >>> PERSON_OBSERVATION OPEN {e['event_id']} "
                      f"conf={e['confidence']} motion_ref={e.get('motion_ref')}")
            else:
                print(f"  t={t:6.2f}s [{label:6}]   <<< PERSON_OBSERVATION CLOSE {e['event_id']} "
                      f"dur={e['duration_s']}s by={e['closed_by']}")
        t += dt

    n_motion = sum(1 for e in motion_ev if e["event_kind"] == "open")
    n_person = sum(1 for e in person_ev if e["event_kind"] == "open")
    print(f"\nmotion episode: {n_motion}  |  person_observation: {n_person}")
    # 结论:两个 motion episode(蒸汽+真人),但只有真人幕产 1 个 person_observation
    ok = (n_motion == 2 and n_person == 1
          and all(e["type"] == "person_observation" for e in person_ev)
          and all("intrusion" not in e["type"] for e in person_ev))
    print(f"结论:{'✅ 蒸汽不产 person(门控生效);真人产 person_observation' if ok else '⚠️ 路径异常'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

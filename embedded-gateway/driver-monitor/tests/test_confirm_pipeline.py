#!/usr/bin/env python3
"""P1a 端到端(离线,纯标准库):P0 motion episode 门控 → 人体检测 → ROI → 确认。

验两条必经路径(ADR-0001):
  - 蒸汽:motion 有、person 无(或在 ROI 外)→ **零 person_observation**。
  - 真人:motion + person 在 ROI → person_observation OPEN;motion 闭合 → CLOSE。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from motion.episode import EpisodeStateMachine, EpisodeConfig    # noqa: E402
from vision.confirm import PersonConfirmer, ConfirmConfig         # noqa: E402
from vision.person_detector import MockPersonDetector, PersonBox  # noqa: E402
from roi.mask import RoiMask                                      # noqa: E402

ROI = RoiMask([(100, 100), (300, 100), (300, 300), (100, 300)])   # 居中方形
IN_ROI = PersonBox(180, 180, 220, 260, 0.9)                       # 中心 (200,220) 内
OUT_ROI = PersonBox(0, 0, 40, 40, 0.9)                            # 中心 (20,20) 外


def run_gated(trace, *, dt=1 / 15.0,
              ep_cfg=EpisodeConfig(n_enter=4, n_exit=30),
              cf_cfg=ConfirmConfig(k_window=5, m_confirm=3, person_exit_frames=15)):
    """trace: [(moving:bool, score:float, boxes:list[PersonBox]), ...]。
    返回 (motion_events, person_events)。人体检测仅在 motion 活跃时跑(门控)。"""
    ep = EpisodeStateMachine(ep_cfg)
    cf = PersonConfirmer(cf_cfg)
    motion_ev, person_ev = [], []
    cur_motion_id = None
    t = 0.0
    for moving, score, boxes in trace:
        for e in ep.update(t, moving, score):
            motion_ev.append(e)
            if e["event_kind"] == "open":
                cur_motion_id = e["event_id"]
        active = ep.active
        # 门控:motion 活跃才跑「NPU」(Mock),否则不检测
        det = MockPersonDetector(default=boxes).detect(None) if active else []
        det = ROI.filter_boxes(det)
        person_ev += cf.update(round(t, 6), active, det, motion_event_id=cur_motion_id)
        t = round(t + dt, 6)
    return motion_ev, person_ev


def test_steam_path_motion_but_no_person():
    """蒸汽:一直有 motion,没人 → motion 有 episode,但 person_observation 为零。"""
    trace = [(True, 0.05, [])] * 40 + [(False, 0.0, [])] * 35
    motion_ev, person_ev = run_gated(trace)
    assert any(e["event_kind"] == "open" for e in motion_ev), "应有 motion episode"
    assert person_ev == [], f"蒸汽不应产 person_observation,得到 {person_ev}"


def test_steam_with_spurious_box_outside_roi_still_no_person():
    """更刁:蒸汽期检测器偶发把区外物体当人 → ROI 过滤掉 → 仍零 person_observation。"""
    trace = [(True, 0.05, [OUT_ROI])] * 40 + [(False, 0.0, [])] * 35
    _, person_ev = run_gated(trace)
    assert person_ev == [], person_ev


def test_person_path_emits_person_observation():
    """真人:motion + person 在 ROI → person_observation OPEN;motion 闭合 → CLOSE。"""
    trace = [(True, 0.2, [IN_ROI])] * 40 + [(False, 0.0, [])] * 35
    motion_ev, person_ev = run_gated(trace)
    kinds = [e["event_kind"] for e in person_ev]
    assert "open" in kinds and "close" in kinds, kinds
    opens = [e for e in person_ev if e["event_kind"] == "open"]
    assert opens[0]["type"] == "person_observation"
    assert opens[0].get("motion_ref"), "应关联门控 motion episode"


def test_person_only_counts_inside_roi():
    """人只在 ROI 外走动(motion + 区外框)→ 不确认(等价蒸汽路径)。"""
    trace = [(True, 0.2, [OUT_ROI])] * 40 + [(False, 0.0, [])] * 35
    _, person_ev = run_gated(trace)
    assert person_ev == [], person_ev


def test_gating_no_detection_before_motion_opens():
    """motion 未 OPEN(不足 n_enter)时不跑检测、不确认。"""
    # 只 3 帧 moving(<n_enter=4),之后静止:motion 从不 OPEN
    trace = [(True, 0.2, [IN_ROI])] * 3 + [(False, 0.0, [IN_ROI])] * 40
    motion_ev, person_ev = run_gated(trace)
    assert all(e["event_kind"] != "open" for e in motion_ev)
    assert person_ev == []


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

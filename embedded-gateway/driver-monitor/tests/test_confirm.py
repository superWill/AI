#!/usr/bin/env python3
"""运动门控 + 人体确认 状态机单测(纯标准库)。

验证 ADR-0001 ⑥ 硬约束:
  - 只产 person_observation,永不产 intrusion/confirmed。
  - 未达 M 阈值不升级、不改分类(没有「疑似有人」中间态)。
  - motion 门控:无 motion 不确认;motion 闭合未确认 → 不上报。
  - CLOSE = 人消失或 motion 闭合先到者;force_close 收尾。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from vision.confirm import PersonConfirmer, ConfirmConfig, ConfirmState  # noqa: E402
from vision.person_detector import PersonBox                              # noqa: E402


def _c(**over):
    return PersonConfirmer(ConfirmConfig(**over))


def _P(score=0.9):
    return [PersonBox(180, 180, 220, 260, score)]


def _drive(c, seq, dt=0.1, t0=0.0):
    """seq: [(motion_active, person_boxes), ...] → 逐帧 update。返回全部事件。"""
    events, t = [], t0
    for motion, boxes in seq:
        events += c.update(round(t, 6), motion, boxes)
        t += dt
    return events


def test_no_motion_no_confirmation():
    c = _c(k_window=5, m_confirm=3)
    ev = _drive(c, [(False, _P())] * 10)            # 有人但无 motion 门控
    assert ev == [], ev
    assert c.state == ConfirmState.IDLE


def test_motion_without_person_never_opens():
    """蒸汽路径:motion 一直活跃,但没人 → 零 person_observation。"""
    c = _c(k_window=5, m_confirm=3)
    ev = _drive(c, [(True, [])] * 40 + [(False, [])] * 5)
    assert ev == [], ev
    assert c.state == ConfirmState.IDLE


def test_person_confirmed_after_m_of_k():
    c = _c(k_window=5, m_confirm=3)
    # 前 2 帧见人:不够 M=3,不确认
    ev = _drive(c, [(True, _P()), (True, _P())])
    assert ev == [] and c.state == ConfirmState.MOTION_TENTATIVE
    # 第 3 帧见人:窗内 3/? ≥ 3 → 确认
    ev = _drive(c, [(True, _P())], t0=0.2)
    assert len(ev) == 1 and ev[0]["event_kind"] == "open"
    assert c.confirmed


def test_open_ts_start_is_first_person_sighting():
    c = _c(k_window=5, m_confirm=3)
    ev = _drive(c, [(True, _P())] * 3, dt=0.1, t0=0.0)
    assert ev[0]["ts_start"] == 0.0, ev[0]["ts_start"]   # 首次见人,非确认帧(0.2)


def test_flicker_below_m_does_not_confirm():
    """闪烁误检:窗内见人不足 M → 不确认(不确定不改分类)。"""
    c = _c(k_window=5, m_confirm=3)
    # 模式:见/不见/不见/见/不见 … 窗内最多 2/5 < 3
    seq = [(True, _P()), (True, []), (True, []), (True, _P()), (True, [])] * 4
    ev = _drive(c, seq)
    assert ev == [], ev
    assert c.state == ConfirmState.MOTION_TENTATIVE


def test_close_on_motion_closed():
    c = _c(k_window=5, m_confirm=3)
    _drive(c, [(True, _P())] * 3)                   # OPEN
    ev = _drive(c, [(False, [])], t0=0.3)           # motion 闭合 → CLOSE
    assert len(ev) == 1 and ev[0]["event_kind"] == "close"
    assert ev[0]["closed_by"] == "motion_closed"
    assert c.state == ConfirmState.IDLE


def test_close_on_person_left_while_motion_continues():
    """人走了但蒸汽维持 motion → 人消失先到,发 person_left(不把蒸汽尾巴算成人在)。"""
    c = _c(k_window=5, m_confirm=3, person_exit_frames=15)
    _drive(c, [(True, _P())] * 3, dt=0.1, t0=0.0)   # OPEN,最后见人 t=0.2
    # motion 继续但没人 15 帧 → person_left CLOSE
    ev = _drive(c, [(True, [])] * 15, t0=0.3)
    close = [e for e in ev if e["event_kind"] == "close"]
    assert len(close) == 1 and close[0]["closed_by"] == "person_left"
    assert close[0]["ts_end"] == 0.2, close[0]["ts_end"]   # 最后见人时刻,非缺席帧


def test_reentry_opens_new_observation_same_motion():
    """人走后同一 motion 内又进人 → 开新 person_observation(新 event_id)。"""
    c = _c(k_window=5, m_confirm=3, person_exit_frames=5)
    ev1 = _drive(c, [(True, _P())] * 3, t0=0.0)          # OPEN po-1
    ev1 += _drive(c, [(True, [])] * 5, t0=0.3)           # person_left CLOSE po-1
    ev2 = _drive(c, [(True, _P())] * 3, t0=0.8)          # 再进人 → OPEN po-2
    ids = [e["event_id"] for e in ev1 + ev2]
    opens = [e for e in ev1 + ev2 if e["event_kind"] == "open"]
    assert opens[0]["event_id"] == "po-000001"
    assert opens[1]["event_id"] == "po-000002"
    assert c.confirmed


def test_force_close_only_when_confirmed():
    c = _c(k_window=5, m_confirm=3)
    assert c.force_close(1.0) is None               # IDLE
    _drive(c, [(True, _P()), (True, _P())])         # 暂定期(未确认)
    assert c.force_close(2.0) is None               # 暂定期无已确认观测
    _drive(c, [(True, _P())], t0=0.2)               # 确认
    ev = c.force_close(9.0, "shutdown")
    assert ev is not None and ev["closed_by"] == "shutdown"


def test_only_person_observation_never_intrusion():
    c = _c(k_window=5, m_confirm=3)
    ev = _drive(c, [(True, _P())] * 3 + [(False, [])])
    assert ev, "应有 open+close"
    for e in ev:
        assert e["type"] == "person_observation", e["type"]
        assert "intrusion" not in e["type"] and "confirmed" not in e["type"]


def test_motion_ref_stamped_when_provided():
    c = _c(k_window=5, m_confirm=3)
    events = []
    t = 0.0
    for _ in range(3):
        events += c.update(t, True, _P(), motion_event_id="ep-000007"); t += 0.1
    events += c.update(t, False, [], motion_event_id="ep-000007")
    for e in events:
        assert e.get("motion_ref") == "ep-000007", e


def test_peak_confidence_tracked():
    c = _c(k_window=5, m_confirm=3)
    events = _drive(c, [(True, _P(0.6)), (True, _P(0.95)), (True, _P(0.7))]
                    + [(False, [])])
    close = [e for e in events if e["event_kind"] == "close"][0]
    assert close["peak_confidence"] == 0.95, close["peak_confidence"]


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

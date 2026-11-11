#!/usr/bin/env python3
"""通知升级状态机单测(纯标准库)—— ADR-0001 ② 硬约束。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.escalate import NotificationEscalator, EscalateConfig   # noqa: E402


def _esc(**over):
    return NotificationEscalator(EscalateConfig(**over))


def test_notify_starts_at_l1():
    e = _esc(timeouts=(60.0, 180.0))
    ev = e.notify("po-1", now=0.0)
    assert ev["notify_level"] == 1 and ev["action"] == "notify"


def test_no_escalate_before_timeout():
    e = _esc(timeouts=(60.0, 180.0))
    e.notify("po-1", now=0.0)
    assert e.tick(now=30.0) == []                     # 未超 T1
    assert e.level_of("po-1") == 1


def test_escalates_after_timeout():
    e = _esc(timeouts=(60.0, 180.0), max_level=3)
    e.notify("po-1", now=0.0)
    out = e.tick(now=61.0)                             # 超 T1 → L2
    assert out and out[0]["notify_level"] == 2 and out[0]["action"] == "escalate"
    assert e.tick(now=61.0 + 181.0)[0]["notify_level"] == 3   # 超 T2 → L3


def test_ack_stops_escalation():
    e = _esc(timeouts=(60.0,))
    e.notify("po-1", now=0.0)
    r = e.ack("po-1", now=10.0)
    assert r["action"] == "resolved"
    assert e.tick(now=100.0) == []                    # 已 ack,不再升
    assert e.ack("po-1", now=20.0) is None            # 重复 ack 无效


def test_caps_at_max_level():
    e = _esc(timeouts=(10.0, 10.0), max_level=2)
    e.notify("po-1", now=0.0)
    e.tick(now=11.0)                                   # L2
    assert e.tick(now=100.0) == []                    # 到顶不再升
    assert e.level_of("po-1") == 2


def test_notification_has_no_event_classification_field():
    """结构不变量:通知事件只带 notify_level,没有事件分类字段 → 无法升级分类/火警。"""
    e = _esc()
    for ev in [e.notify("po-1", 0.0)] + e.tick(now=1e9):
        assert "classification" not in ev
        assert "event_kind" not in ev
        assert "fire" not in str(ev).lower()
        assert "notify_level" in ev


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

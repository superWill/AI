#!/usr/bin/env python3
"""SegmentRing 单测(纯标准库)—— 淘汰序/地板/两阶段确认/健康告警。

覆盖 7 条中的:#2 pre-roll 地板 · #3 pin 不误删+告警 · #4 custody 不授权/delivery 才授权。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.ring import SegmentRing, RingConfig                  # noqa: E402
from record.segment_source import SegmentRecord                  # noqa: E402


def _seg(i, bytes=100, gap=False):
    return SegmentRecord(i, float(i), float(i + 1), f"/rec/{i}.mp4", bytes, gap)


def _ring(**over):
    return SegmentRing(RingConfig(**over))


def _statuses(health):
    return [h["status"] for h in health]


def test_prune_preserves_preroll_floor():
    """#2 环形淘汰保 pre-roll 地板:最近 R_pre 秒的段一律不淘汰。"""
    r = _ring(max_bytes=350, pre_roll_floor_s=5.0)
    for i in range(10):
        r.add(_seg(i))                               # 段 0..9,共 1000B
    evicted, health = r.prune(now=10.0)              # floor_ts=5 → 段 5..9 受保护
    kept = {s for s in range(10) if s in r}
    assert {5, 6, 7, 8, 9} <= kept, kept             # 地板内全保留
    assert any(s not in r for s in range(5))          # 有旧段被淘汰
    assert "over_cap_pinned" in _statuses(health)    # 地板撑到超上限 → 告警


def test_undelivered_pinned_never_evicted_and_alarms():
    """#3 pin 段(未 delivery)永不误删,逼上限发健康告警。"""
    r = _ring(max_bytes=150, pre_roll_floor_s=5.0)
    for i in range(7):
        r.add(_seg(i))                               # 700B
    r.pin(0, "po-1"); r.pin(1, "po-1")               # 段 0,1 pin(未 delivery)
    evicted, health = r.prune(now=7.0)               # floor_ts=2 → 段 0,1 在地板外但被 pin
    assert 0 in r and 1 in r                          # pin 段幸存
    assert "over_cap_pinned" in _statuses(health)
    assert 0 not in [e.seg_id for e in evicted]


def test_custody_does_not_authorize_delete_but_delivery_does():
    """#4 custody_ack 不授权淘汰;delivery_ack 才授权。"""
    r = _ring(max_bytes=150, pre_roll_floor_s=0.0)   # 关地板,聚焦 pin 语义
    for i in range(3):
        r.add(_seg(i))                               # 300B
    r.pin(0, "po-1"); r.pin(1, "po-1")
    r.prune(now=3.0)
    assert 0 in r and 1 in r, "未确认 → pin 段留存"
    r.mark_custody("po-1")                            # 仅 custody
    r.prune(now=3.0)
    assert 0 in r and 1 in r, "custody 不授权删,pin 段仍留存"
    r.mark_delivered("po-1")                          # delivery
    r.prune(now=3.0)
    assert 0 not in r, "delivery 后 pin 段获淘汰资格,被淘汰"


def test_eviction_order_delivered_low_before_high():
    """淘汰序 tier2:已 delivery 的低优先段先于高优先段被淘汰(两段都 pin,排除 tier1 干扰)。"""
    r = _ring(max_bytes=150, pre_roll_floor_s=0.0)
    r.add(_seg(0)); r.add(_seg(1))                   # 200B,需淘 1 段
    r.pin(0, "lowE", priority="low")
    r.pin(1, "highE", priority="high")
    r.mark_delivered("lowE"); r.mark_delivered("highE")
    evicted, _ = r.prune(now=2.0)
    assert [e.seg_id for e in evicted] == [0], "低优先段应先淘汰"
    assert 1 in r, "高优先段应保留"


def test_unpinned_evicted_before_pinned():
    """淘汰序 tier1:未 pin 普通段先于任何 pin 段被淘汰。"""
    r = _ring(max_bytes=250, pre_roll_floor_s=0.0)
    for i in range(3):
        r.add(_seg(i))
    r.pin(0, "E"); r.mark_delivered("E")             # 0 已 delivery pin,可淘但优先级低于"未 pin"
    evicted, _ = r.prune(now=3.0)
    assert 1 in [e.seg_id for e in evicted] or 2 in [e.seg_id for e in evicted]
    assert 0 in r, "未 pin 的 1/2 先淘,pin 段 0 后淘"


def test_mark_lost_is_explicit_not_silent():
    r = _ring(max_bytes=10**9)
    r.add(_seg(0))
    health = r.mark_lost(0)
    assert 0 not in r
    assert _statuses(health) == ["evidence_loss"]     # 显式损失信号,非静默


def test_event_metadata_gc_after_segments_gone():
    """防泄漏:某事件的 pin 段全部离开 ring(delivery 后淘汰 / 丢失)→ 其元数据被清。"""
    r = _ring(max_bytes=150, pre_roll_floor_s=0.0)
    r.add(_seg(0)); r.add(_seg(1))
    r.pin(0, "po-x", priority="high"); r.pin(1, "po-x")
    r.mark_delivered("po-x")
    assert "po-x" in r._event_priority and "po-x" in r._delivered
    r.prune(now=2.0)                                 # 300B>150 → 淘汰 po-x 的段
    r.mark_lost(1) if 1 in r else None               # 确保两段都离场
    assert "po-x" not in r._event_priority, "元数据应随最后一段离场被清"
    assert "po-x" not in r._delivered


def test_disk_pressure_health_once():
    r = _ring(max_bytes=1000, disk_warn_frac=0.9)
    h = []
    for i in range(8):                               # 800B < 900 阈值
        h += r.add(_seg(i))
    assert "disk_pressure" not in _statuses(h)
    h2 = r.add(_seg(8))                              # 900B ≥ 900 → 告警
    assert "disk_pressure" in _statuses(h2)
    h3 = r.add(_seg(9))                              # 已报过 → 去重,不再报
    assert "disk_pressure" not in _statuses(h3)


def test_write_stall_health():
    r = _ring(max_bytes=10**9, write_stall_s=6.0)
    r.add(_seg(0))                                   # last_add_ts=1.0
    _, h = r.prune(now=5.0)                          # 4s < 6 → 不报
    assert "write_stall" not in _statuses(h)
    _, h2 = r.prune(now=8.0)                         # 7s ≥ 6 → 报一次
    assert "write_stall" in _statuses(h2)


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

#!/usr/bin/env python3
"""RetentionGC 单测(纯标准库,注入时钟)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.retention import (                                  # noqa: E402
    RetentionGC, RetentionConfig, InMemoryRetentionStore)


def _statuses(health):
    return [h["status"] for h in health]


# ---- 红线①:未上传绝不回收 ----

def test_never_evict_unuploaded_even_if_very_old():
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=10.0, stuck_warn_s=5.0))
    gc.note_created("k1", "first_frame", now=0.0)
    evictable, health = gc.collect(now=100000.0)               # 极久之后
    assert evictable == []                                     # 未上传 → 绝不回收
    assert "evidence_stuck" in _statuses(health)               # 但要告警


def test_stuck_reported_once():
    gc = RetentionGC(RetentionConfig(stuck_warn_s=5.0))
    gc.note_created("k1", "frame", now=0.0)
    assert "evidence_stuck" in _statuses(gc.collect(now=10.0)[1])
    assert "evidence_stuck" not in _statuses(gc.collect(now=11.0)[1])   # 不重复报


# ---- 保留时间窗 ----

def test_uploaded_within_window_not_evictable():
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=3600.0))
    gc.note_created("k1", "first_frame", now=0.0)
    gc.note_uploaded("k1", now=0.0)
    assert gc.collect(now=1000.0)[0] == []                     # 窗内不删


def test_uploaded_past_window_evictable():
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=3600.0))
    gc.note_created("k1", "first_frame", now=0.0)
    gc.note_uploaded("k1", now=0.0)
    assert gc.collect(now=3600.0)[0] == ["k1"]                 # 到期可删


# ---- require_delivered:更严 ----

def test_require_delivered_gates_eviction():
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=10.0, require_delivered=True))
    gc.note_created("k1", "first_frame", now=0.0)
    gc.note_uploaded("k1", now=0.0)
    assert gc.collect(now=100.0)[0] == []                      # 已上传过窗,但未投递 → 不删
    gc.note_delivered("k1", now=50.0)
    assert gc.collect(now=100.0)[0] == ["k1"]                  # 投递后 → 可删


# ---- forget + 无记录的 note 安全 ----

def test_forget_stops_tracking():
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=0.0))
    gc.note_created("k1", "frame", now=0.0)
    gc.note_uploaded("k1", now=0.0)
    ev, _ = gc.collect(now=1.0)
    assert ev == ["k1"] and gc.tracked_count == 1
    gc.forget(ev)
    assert gc.tracked_count == 0 and gc.state_of("k1") is None


def test_note_upload_without_create_is_noop():
    gc = RetentionGC()
    gc.note_uploaded("ghost", now=0.0)                          # 无 note_created → 无副作用
    gc.note_delivered("ghost", now=0.0)
    assert gc.tracked_count == 0


# ---- 持久化:跨重启重建跟踪表 ----

def test_persistence_reloads_tracking_across_restart():
    store = InMemoryRetentionStore()
    gc1 = RetentionGC(RetentionConfig(retention_after_upload_s=100.0), store=store)
    gc1.note_created("k1", "first_frame", now=0.0)
    gc1.note_uploaded("k1", now=10.0)
    gc1.checkpoint()                                   # 落盘

    # —— 重启:同 store 新建 ——
    gc2 = RetentionGC(RetentionConfig(retention_after_upload_s=100.0), store=store)
    assert gc2.tracked_count == 1
    r = gc2.state_of("k1")
    assert r is not None and r.uploaded_at == 10.0     # 上传状态挺过重启
    assert gc2.collect(now=50.0)[0] == []              # 窗内不删
    assert gc2.collect(now=200.0)[0] == ["k1"]         # 到期可删


def test_forget_persists_removal():
    store = InMemoryRetentionStore()
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=0.0), store=store)
    gc.note_created("k1", "frame", now=0.0)
    gc.note_uploaded("k1", now=0.0)
    ev, _ = gc.collect(now=1.0)
    gc.forget(ev)
    # 重启后不应再出现
    assert RetentionGC(store=store).tracked_count == 0


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

#!/usr/bin/env python3
"""WorkOrderCache 单测(纯标准库)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.workorder_cache import WorkOrderCache, WorkOrderWindow   # noqa: E402


def test_empty_before_update():
    c = WorkOrderCache(ttl_s=100)
    assert c.status(now=0.0) == "empty"
    assert c.covering(5.0) is None


def test_fresh_and_covering():
    c = WorkOrderCache(ttl_s=100)
    c.update("v1", as_of_ts=0.0, windows=[WorkOrderWindow("w1", 10.0, 20.0)])
    assert c.status(now=50.0) == "fresh"
    w = c.covering(15.0)
    assert w is not None and w.window_id == "w1"
    assert c.covering(25.0) is None                  # 窗外


def test_expired_after_ttl():
    c = WorkOrderCache(ttl_s=100)
    c.update("v1", as_of_ts=0.0, windows=[WorkOrderWindow("w1", 10.0, 20.0)])
    assert c.status(now=101.0) == "expired"


def test_update_replaces_version():
    c = WorkOrderCache(ttl_s=100)
    c.update("v1", 0.0, [WorkOrderWindow("w1", 0.0, 10.0)])
    c.update("v2", 5.0, [WorkOrderWindow("w2", 100.0, 200.0)])   # 撤销旧窗
    assert c.version == "v2"
    assert c.covering(5.0) is None                   # 旧窗已失效
    assert c.covering(150.0) is not None


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

#!/usr/bin/env python3
"""SpoolStore 单测(纯标准库,真磁盘临时目录 + 内存替身)。"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.spool_store import SpoolStore, InMemorySpoolStore, _frame, _unframe


def test_frame_unframe_roundtrip():
    header, data = {"key": "k", "kind": "first_frame", "occurred_at": 1.5}, b"\x89PNG\x00\xff"
    h2, d2 = _unframe(_frame(header, data))
    assert h2 == header and d2 == data


def test_disk_save_load_remove():
    d = tempfile.mkdtemp()
    try:
        s = SpoolStore(d)
        s.save("driver-monitor/events/po-1/first_frame.png",
               {"key": "driver-monitor/events/po-1/first_frame.png", "kind": "first_frame"},
               b"bytes-1")
        loaded = s.load_all()
        assert len(loaded) == 1
        header, data = loaded[0]
        assert header["key"].endswith("first_frame.png") and data == b"bytes-1"
        s.remove("driver-monitor/events/po-1/first_frame.png")
        assert s.load_all() == []
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_corrupt_file_quarantined_not_loaded():
    d = tempfile.mkdtemp()
    try:
        s = SpoolStore(d)
        with open(os.path.join(d, "bad.spool"), "wb") as f:
            f.write(b"\x00\x00\x00\xfftruncated-garbage")   # 头长超过体
        assert s.load_all() == []                            # 不当正常记录加载
        assert os.path.exists(os.path.join(d, "bad.spool.corrupt"))  # 隔离,不静默丢
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_inmemory_store_parity():
    s = InMemorySpoolStore()
    s.save("k1", {"key": "k1", "kind": "frame"}, b"x")
    assert [h["key"] for h, _ in s.load_all()] == ["k1"]
    s.remove("k1")
    assert s.load_all() == []


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

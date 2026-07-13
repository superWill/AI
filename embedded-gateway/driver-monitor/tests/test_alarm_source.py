#!/usr/bin/env python3
"""报警源单测(纯标准库)。"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.alarm_source import FakeAlarmSource, FileAlarmSource, AlarmEvent  # noqa: E402


def test_fake_source_fire_and_drain_once():
    s = FakeAlarmSource("smoke-1")
    assert s.poll(now=0.0) == []
    s.fire(now=10.0)
    evs = s.poll(now=11.0)
    assert len(evs) == 1 and evs[0].source_id == "smoke-1" and evs[0].occurred_at == 10.0
    assert s.poll(now=12.0) == []                         # 取走后清空,不重复


def test_file_source_edge_trigger():
    d = tempfile.mkdtemp()
    try:
        trig = os.path.join(d, "alarm.trigger")
        s = FileAlarmSource(trig, source_id="smoke-2")
        assert s.poll(now=0.0) == []                      # 无文件 → 无报警
        open(trig, "w").close()                           # touch 模拟烟感
        evs = s.poll(now=5.0)
        assert len(evs) == 1 and evs[0].source_id == "smoke-2"
        assert not os.path.exists(trig)                   # 消费后删(边沿)
        assert s.poll(now=6.0) == []                      # 不重复触发
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

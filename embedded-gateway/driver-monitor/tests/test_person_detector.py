#!/usr/bin/env python3
"""人体检测 Mock + PersonBox 单测(纯标准库)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from vision.person_detector import (PersonBox, MockPersonDetector,   # noqa: E402
                                    PersonDetector)


def test_person_box_center():
    b = PersonBox(10, 20, 30, 60, 0.8)
    assert b.center == (20.0, 40.0)


def test_mock_is_a_person_detector():
    assert isinstance(MockPersonDetector(), PersonDetector)


def test_mock_follows_schedule_then_default():
    a = [PersonBox(0, 0, 1, 1, 0.9)]
    b = [PersonBox(2, 2, 3, 3, 0.7)]
    det = MockPersonDetector(schedule=[a, [], b], default=[])
    assert det.detect(None) == a
    assert det.detect(None) == []
    assert det.detect(None) == b
    assert det.detect(None) == []                   # 耗尽 → default
    assert det.detect(None) == []


def test_mock_default_when_no_schedule():
    d = [PersonBox(0, 0, 5, 5, 1.0)]
    det = MockPersonDetector(default=d)
    assert det.detect(None) == d
    assert det.detect("ignored-rgb") == d           # 忽略像素


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

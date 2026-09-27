#!/usr/bin/env python3
"""四级运营分类器单测(纯标准库)—— ADR-0001 ⑥ 硬约束。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.classify import PersonClassifier, Presence           # noqa: E402
from uplink.workorder_cache import WorkOrderCache, WorkOrderWindow  # noqa: E402


def _cache(windows=(), version="v1", as_of=0.0, ttl=100.0):
    c = WorkOrderCache(ttl_s=ttl)
    if windows:
        c.update(version, as_of, list(windows))
    return c


def _person(eid="po-1", ts_start=15.0):
    return {"type": "person_observation", "event_kind": "open",
            "event_id": eid, "ts_start": ts_start}


def test_within_window_is_expected_with_version():
    c = _cache([WorkOrderWindow("w1", 10.0, 20.0)])
    r = PersonClassifier(c).classify(_person(ts_start=15.0), now=50.0)
    assert r["classification"] == Presence.EXPECTED
    assert r["window_id"] == "w1" and r["cache_version"] == "v1"
    assert r["as_of_ts"] == 0.0


def test_outside_window_is_suspected():
    c = _cache([WorkOrderWindow("w1", 10.0, 20.0)])
    r = PersonClassifier(c).classify(_person(ts_start=30.0), now=50.0)
    assert r["classification"] == Presence.SUSPECTED


def test_expired_cache_degrades_to_unverified():
    c = _cache([WorkOrderWindow("w1", 10.0, 20.0)], as_of=0.0, ttl=100.0)
    r = PersonClassifier(c).classify(_person(ts_start=15.0), now=200.0)   # 过期
    assert r["classification"] == Presence.UNVERIFIED
    assert "expired" in r["reason"]


def test_empty_cache_is_unverified():
    r = PersonClassifier(_cache()).classify(_person(), now=1.0)
    assert r["classification"] == Presence.UNVERIFIED
    assert "empty" in r["reason"]


def test_never_emits_confirmed_intrusion():
    """跨所有情形:分类器绝不产 confirmed_intrusion。"""
    cases = [
        _cache([WorkOrderWindow("w1", 10.0, 20.0)]),   # expected
        _cache([WorkOrderWindow("w1", 10.0, 20.0)]),   # suspected(用窗外 ts)
        _cache(),                                       # unverified
    ]
    tss = [15.0, 30.0, 15.0]
    for c, ts in zip(cases, tss):
        r = PersonClassifier(c).classify(_person(ts_start=ts), now=50.0)
        assert r["classification"] != "confirmed_intrusion"
        assert r["classification"] in (Presence.EXPECTED, Presence.UNVERIFIED,
                                       Presence.SUSPECTED)


def test_does_not_mutate_person_event():
    c = _cache([WorkOrderWindow("w1", 10.0, 20.0)])
    ev = _person(ts_start=15.0)
    before = dict(ev)
    r = PersonClassifier(c).classify(ev, now=50.0)
    assert ev == before, "分类是叠加,绝不改底层 person_observation"
    assert r["person_observation_ref"] == ev["event_id"]


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

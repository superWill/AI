#!/usr/bin/env python3
"""EventEnvelope 单测(纯标准库)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.envelope import EventEnvelope                        # noqa: E402


def _person(kind="open", eid="po-000001", ts_start=6.0):
    return {"type": "person_observation", "event_kind": kind,
            "event_id": eid, "ts_start": ts_start, "confidence": 0.9}


def test_open_and_close_get_distinct_msg_keys_same_event_id():
    """OPEN 与 CLOSE 共享 event_id,但 msg_key 不同 → 两条都投递,不互相当重复删。"""
    o = EventEnvelope.from_event(_person("open"))
    c = EventEnvelope.from_event(_person("close"))
    assert o.event_id == c.event_id == "po-000001"
    assert o.msg_key != c.msg_key
    assert o.msg_key == "po-000001:open" and c.msg_key == "po-000001:close"


def test_priority_mapping():
    assert EventEnvelope.from_event(_person()).priority_class == "high"
    m = EventEnvelope.from_event({"type": "motion_episode", "event_kind": "open",
                                  "event_id": "ep-1", "ts_start": 1.0})
    assert m.priority_class == "low"


def test_occurred_at_and_evidence():
    e = EventEnvelope.from_event(_person(ts_start=6.0),
                                 evidence_ref={"evidence_status": "partial", "segments": [1, 2]})
    assert e.occurred_at == 6.0
    assert e.evidence_status == "partial"
    assert e.evidence_ref["segments"] == [1, 2]


def test_default_evidence_pending():
    assert EventEnvelope.from_event(_person()).evidence_status == "pending"


def test_to_dict_shape():
    d = EventEnvelope.from_event(_person()).to_dict()
    for k in ("event_id", "msg_key", "kind", "occurred_at", "priority_class",
              "payload", "evidence_status", "origin_board", "schema_version"):
        assert k in d, k


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

#!/usr/bin/env python3
"""FakeUplinkTransport 单测(纯标准库)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.transport import FakeUplinkTransport, UplinkTransport   # noqa: E402
from uplink.envelope import EventEnvelope                           # noqa: E402


def _env(eid="po-1", phase="open"):
    return EventEnvelope.from_event({"type": "person_observation", "event_kind": phase,
                                     "event_id": eid, "ts_start": 1.0})


def test_is_transport():
    assert isinstance(FakeUplinkTransport(), UplinkTransport)


def test_offline_publish_returns_none():
    tx = FakeUplinkTransport(online=False)
    assert tx.publish(_env()) is None
    tx.set_online(True)
    assert tx.publish(_env()) is not None


def test_auto_acks_feed_inbox():
    tx = FakeUplinkTransport(auto_custody=True, auto_delivery=True)
    tx.publish(_env("po-1"))
    kinds = sorted(m.kind for m in tx.poll())
    assert kinds == ["custody_ack", "delivery_ack"]
    assert tx.poll() == []                            # 拉过即清


def test_platform_idempotent_dedup():
    tx = FakeUplinkTransport(auto_custody=True)
    e = _env("po-1")
    tx.publish(e); tx.publish(e); tx.publish(e)       # 重复投递
    assert tx.publish_attempts == 3
    assert tx.unique_received == {"po-1:open"}         # 平台只“收”一次
    assert len([m for m in tx.poll() if m.kind == "custody_ack"]) == 1


def test_manual_ack_feed():
    tx = FakeUplinkTransport()
    tx.feed_custody_ack("po-1:open")
    tx.feed_delivery_ack("po-1:open")
    kinds = [m.kind for m in tx.poll()]
    assert "custody_ack" in kinds and "delivery_ack" in kinds


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

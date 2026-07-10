#!/usr/bin/env python3
"""MediaOutbox 单测(纯标准库,注入可控 uploader,不发网络)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.media_outbox import (                               # noqa: E402
    MediaOutbox, MediaOutboxConfig, MediaOutboxState, MediaUpload)
from uplink.oss_media import MediaUploadError, FakeMediaUploader  # noqa: E402
from uplink.spool_store import InMemorySpoolStore                # noqa: E402


class _FakeUp:
    """可控上传桩:online/offline、4xx 抛错、记录上传顺序。"""

    def __init__(self, online=True, fail_4xx=False, base="https://b.oss/"):
        self.online = online
        self.fail_4xx = fail_4xx
        self.base = base
        self.order: list[str] = []

    def object_url(self, key):
        return self.base + key

    def put(self, key, data, content_type="image/png"):
        if self.fail_4xx:
            raise MediaUploadError(403, key)
        if not self.online:
            return None
        self.order.append(key)
        return self.object_url(key)


def _k(event, name):
    return f"driver-monitor/events/{event}/{name}.png"


# ---- 成功上传 + 回调 ----

def test_enqueue_then_pump_uploads_and_calls_back():
    got = []
    ob = MediaOutbox(_FakeUp(), on_uploaded=got.append)
    key = _k("po-1", "first_frame")
    ob.enqueue(key, b"png", "first_frame", occurred_at=100.0, now=100.0, ref="po-1")
    assert ob.pending_count == 1
    ob.pump(now=100.0)
    assert ob.pending_count == 0
    assert ob.state_of(key) == MediaOutboxState.UPLOADED
    assert len(got) == 1 and isinstance(got[0], MediaUpload)
    assert got[0].url == "https://b.oss/" + key and got[0].ref == "po-1"


# ---- 幂等 ----

def test_idempotent_enqueue():
    ob = MediaOutbox(_FakeUp())
    key = _k("po-1", "first_frame")
    ob.enqueue(key, b"png", "first_frame", 100.0, 100.0)
    assert ob.enqueue(key, b"png", "first_frame", 100.0, 100.0) == []   # 在队 → 忽略
    ob.pump(100.0)
    assert ob.enqueue(key, b"png", "first_frame", 100.0, 100.0) == []   # 已上传 → 忽略
    assert ob.pending_count == 0


# ---- 离线:留队重试,resend_after_s 前不重试 ----

def test_offline_stays_queued_and_retries_after_interval():
    up = _FakeUp(online=False)
    ob = MediaOutbox(up, MediaOutboxConfig(resend_after_s=30.0))
    key = _k("po-1", "first_frame")
    ob.enqueue(key, b"png", "first_frame", 0.0, 0.0)
    ob.pump(now=0.0)                                   # 离线 → 留队
    assert ob.pending_count == 1
    up.online = True
    ob.pump(now=10.0)                                  # 距上次尝试 10s < 30s → 不重试
    assert ob.pending_count == 1 and up.order == []
    ob.pump(now=30.0)                                  # 到点 → 上传
    assert ob.pending_count == 0 and up.order == [key]


# ---- 优先级:first_frame > frame > clip,同级旧先 ----

def test_priority_order_first_frame_before_frame_before_clip():
    up = _FakeUp()
    ob = MediaOutbox(up)
    ob.enqueue(_k("po-1", "clip"), b"x", "clip", occurred_at=3.0, now=3.0)
    ob.enqueue(_k("po-1", "frame-001"), b"x", "frame", occurred_at=2.0, now=2.0)
    ob.enqueue(_k("po-1", "first_frame"), b"x", "first_frame", occurred_at=1.0, now=1.0)
    ob.pump(now=5.0)
    assert up.order == [_k("po-1", "first_frame"),
                        _k("po-1", "frame-001"),
                        _k("po-1", "clip")]


# ---- 容量:非 first_frame 超限淘旧(发告警);first_frame 永不淘 ----

def test_cap_drops_oldest_cappable_but_never_first_frame():
    ob = MediaOutbox(_FakeUp(online=False), MediaOutboxConfig(cappable_cap=2))
    ob.enqueue(_k("po-1", "clip"), b"x", "clip", 1.0, 1.0)          # c1
    ob.enqueue(_k("po-2", "clip"), b"x", "clip", 2.0, 2.0)          # c2
    health = ob.enqueue(_k("po-3", "clip"), b"x", "clip", 3.0, 3.0)  # 超 cap → 淘最旧 c1
    assert any(h["status"] == "media_dropped" for h in health)
    assert ob.state_of(_k("po-1", "clip")) is None                 # c1 被淘
    # first_frame 不计入 cappable,永不被淘
    ob.enqueue(_k("po-9", "first_frame"), b"x", "first_frame", 9.0, 9.0)
    assert ob.state_of(_k("po-9", "first_frame")) == MediaOutboxState.QUEUED


# ---- 4xx:标失败,发健康告警,不重试 ----

def test_4xx_marks_failed_and_not_retried():
    ob = MediaOutbox(_FakeUp(fail_4xx=True))
    key = _k("po-1", "first_frame")
    ob.enqueue(key, b"x", "first_frame", 0.0, 0.0)
    health = ob.pump(now=0.0)
    assert any(h["status"] == "media_upload_failed" for h in health)
    assert ob.state_of(key) == MediaOutboxState.FAILED
    assert ob.pending_count == 0
    assert ob.enqueue(key, b"x", "first_frame", 0.0, 0.0) == []     # 已失败 → 幂等忽略


# ---- 积压告警 ----

def test_backlog_health_emitted_once():
    ob = MediaOutbox(_FakeUp(online=False), MediaOutboxConfig(max_backlog=1))
    ob.enqueue(_k("po-1", "first_frame"), b"x", "first_frame", 0.0, 0.0)
    ob.enqueue(_k("po-2", "first_frame"), b"x", "first_frame", 0.0, 0.0)
    h1 = ob.pump(now=0.0)
    assert any(h["status"] == "media_backlog" for h in h1)
    h2 = ob.pump(now=0.0)                                # 不重复报
    assert not any(h["status"] == "media_backlog" for h in h2)


# ---- sink 协议:put_media 优先(带 kind/occurred_at/ref) ----

class _MediaSink:
    """实现 put_media 的 sink(如 RelayUploader);验证 MediaOutbox 传全上下文。"""

    def __init__(self):
        self.calls = []

    def put_media(self, key, data, content_type, kind, occurred_at, ref):
        self.calls.append((key, kind, occurred_at, ref))
        return "url://" + key


def test_put_media_sink_used_with_full_context():
    s = _MediaSink()
    ob = MediaOutbox(s)
    ob.enqueue("k1", b"x", "first_frame", occurred_at=3.0, now=0.0, ref="po-1")
    ob.pump(now=0.0)
    assert s.calls == [("k1", "first_frame", 3.0, "po-1")]     # 全上下文透传
    assert ob.state_of("k1") == MediaOutboxState.UPLOADED


# ---- 跨重启持久化(store) ----

def test_persistence_survives_restart_and_clears_after_upload():
    store = InMemorySpoolStore()
    key = _k("po-1", "first_frame")
    # 板子离线入队 → 落盘
    ob1 = MediaOutbox(FakeMediaUploader(online=False), store=store)
    ob1.enqueue(key, b"png", "first_frame", occurred_at=0.0, now=0.0, ref="po-1")
    ob1.pump(now=0.0)                                  # 离线 → 留队(仍在盘上)
    assert ob1.pending_count == 1
    assert len(store.load_all()) == 1                  # 已落盘

    # —— 模拟重启:丢掉 ob1,用同一个 store 新建 ——
    up = FakeMediaUploader(online=True)
    ob2 = MediaOutbox(up, store=store)
    assert ob2.pending_count == 1                      # 从盘重建了未上传的证据
    assert ob2.pending_keys() == [key]
    ob2.pump(now=100.0)                                # 联网 → 上传
    assert up.get(key) == b"png"
    assert ob2.pending_count == 0 and store.load_all() == []   # 上传后删盘

    # —— 再次重启:上传过的不再加载 ——
    ob3 = MediaOutbox(FakeMediaUploader(), store=store)
    assert ob3.pending_count == 0


def test_persistence_restored_entry_retries_immediately():
    store = InMemorySpoolStore()
    key = _k("po-1", "frame-001")
    MediaOutbox(FakeMediaUploader(online=False), store=store).enqueue(
        key, b"x", "frame", occurred_at=5.0, now=5.0, ref="po-1")
    up = FakeMediaUploader(online=True)
    ob = MediaOutbox(up, store=store)                  # 重启后
    ob.pump(now=6.0)                                   # 无需等 resend_after_s,立即重试
    assert up.get(key) == b"x"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

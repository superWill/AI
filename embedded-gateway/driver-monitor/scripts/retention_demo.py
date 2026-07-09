#!/usr/bin/env python3
"""保留期 GC 演示:上传成功→留保留窗→到期回收本地副本;未上传→绝不回收 + 告警。

接线:截帧 note_created → MediaOutbox.on_uploaded → note_uploaded → 周期 collect 回收。
纯逻辑,注入时钟,无网络。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from record.retention import RetentionGC, RetentionConfig
from uplink.media_outbox import MediaOutbox
from uplink.oss_media import FakeMediaUploader, event_media_key

PREFIX, EVENT = "driver-monitor", "po-000123"


def main() -> int:
    gc = RetentionGC(RetentionConfig(retention_after_upload_s=100.0, stuck_warn_s=50.0))
    clock = {"t": 0.0}
    up = FakeMediaUploader()
    outbox = MediaOutbox(up, on_uploaded=lambda mu: gc.note_uploaded(mu.key, clock["t"]))

    # 3 帧正常:截帧 note_created + 入队
    for i, t in enumerate([0.0, 5.0, 10.0]):
        key = event_media_key(PREFIX, EVENT, f"frame-{i:03d}")
        gc.note_created(key, "frame", now=t)
        outbox.enqueue(key, b"png", "frame", occurred_at=t, now=t)
    # 1 帧"卡住":note_created 但上传一直失败(此处不入队,模拟传不出去)
    orphan = event_media_key(PREFIX, EVENT, "frame-orphan")
    gc.note_created(orphan, "frame", now=0.0)

    # t=10:pump 上传那 3 帧 → on_uploaded → note_uploaded(t=10)
    clock["t"] = 10.0
    outbox.pump(now=10.0)
    print(f"[t=10] 上传 3 帧,跟踪 {gc.tracked_count} 条(含 1 卡住帧)")

    for now in (10.0, 60.0, 120.0):
        ev, health = gc.collect(now)
        print(f"[t={now:>5}] 可回收={[k.split('/')[-1] for k in ev]}  "
              f"告警={[h['status'] for h in health]}")
        gc.forget(ev)

    print(f"\n最终跟踪 {gc.tracked_count} 条 = 那个卡住帧(未上传,红线:永不回收,只告警)")
    assert gc.tracked_count == 1                       # 卡住帧从未被回收
    print("OK: 上传→留窗→到期回收;未上传→绝不回收+evidence_stuck 告警")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

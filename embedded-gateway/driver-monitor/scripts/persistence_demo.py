#!/usr/bin/env python3
"""跨重启持久化演示:未上传的证据落盘,进程"崩溃"重启后从盘重建并补传。

用真磁盘 SpoolStore(临时目录);阶段1 离线入队→落盘,丢掉 outbox 模拟崩溃,
阶段2 用同一目录新建 outbox→从盘重建→联网补传→删盘。
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.media_outbox import MediaOutbox
from uplink.oss_media import FakeMediaUploader, event_media_key
from uplink.spool_store import SpoolStore

PREFIX, EVENT = "driver-monitor", "po-000123"


def _spool_files(d):
    return sorted(f for f in os.listdir(d) if f.endswith(".spool"))


def main() -> int:
    spool_dir = tempfile.mkdtemp(prefix="dm-spool-")
    try:
        # ---- 阶段1:板子离线 —— 截帧入队落盘,然后"崩溃" ----
        print(f"[阶段1] 落盘目录 {spool_dir}")
        ob1 = MediaOutbox(FakeMediaUploader(online=False), store=SpoolStore(spool_dir))
        for i, t in enumerate([0.0, 5.0, 10.0]):
            key = event_media_key(PREFIX, EVENT, f"frame-{i:03d}")
            ob1.enqueue(key, b"png-" + str(i).encode(), "frame", occurred_at=t, now=t, ref=EVENT)
            ob1.pump(now=t)                            # 离线 → 留队(落盘)
        print(f"  入队 3 帧,{ob1.pending_count} 在队,磁盘 {len(_spool_files(spool_dir))} 个 .spool")
        del ob1                                        # 模拟进程崩溃(内存队列全丢)
        print("  ── 进程崩溃(丢掉内存队列)──")

        # ---- 阶段2:重启 —— 同目录新建,从盘重建,联网补传 ----
        up = FakeMediaUploader(online=True)
        ob2 = MediaOutbox(up, store=SpoolStore(spool_dir))
        print(f"[阶段2] 重启:从盘重建 {ob2.pending_count} 帧(证据挺过崩溃)")
        ob2.pump(now=100.0)                            # 联网 → 补传
        print(f"  补传后:{ob2.pending_count} 在队,磁盘 {len(_spool_files(spool_dir))} 个 .spool,"
              f"已上传 {len(up.puts)} 帧")

        assert len(up.puts) == 3 and ob2.pending_count == 0
        assert len(_spool_files(spool_dir)) == 0       # 上传后删盘
        print("\nOK: 未上传证据落盘→崩溃→重启从盘重建→补传→删盘,跨重启不丢")
        return 0
    finally:
        shutil.rmtree(spool_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

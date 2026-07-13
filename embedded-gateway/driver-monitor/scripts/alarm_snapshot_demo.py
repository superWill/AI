#!/usr/bin/env python3
"""RK3506 报警抓拍链离线演示:报警 → 抓快照 → 板子侧 spool(ship 到代理→OSS),含代理下线留队。

纯标准库,注入 fake 源/快照/relay。真机把 Fake 换成 HttpSnapshotGrabber + MediaRelayClient(见 alarm_snapshot_rk3506.py)。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.alarm_source import FakeAlarmSource
from alarm.snapshot import FakeSnapshotGrabber
from alarm.pipeline import AlarmSnapshotPipeline
from uplink.media_outbox import MediaOutbox
from uplink.media_relay import RelayUploader
from uplink.oss_media import oss_object_url

PREFIX = "driver-monitor"
ENDPOINT, BUCKET = "oss-cn-hangzhou.aliyuncs.com", "ubuntu-oss-313"


class ToggleLink:
    """模拟板子→代理链路开关(真实现=MediaRelayClient→本地HTTP)。"""
    def __init__(self, online=False):
        self.online = online
        self.received = []

    def ship(self, shipment):
        if not self.online:
            return False
        self.received.append(shipment.key)
        return True


def main() -> int:
    link = ToggleLink(online=False)                      # 代理先下线
    shipped = []
    sink = RelayUploader(link, lambda k: oss_object_url(ENDPOINT, BUCKET, k))
    spool = MediaOutbox(sink, on_uploaded=lambda mu: shipped.append(mu.key))
    alarm = FakeAlarmSource("smoke-1")
    snap = FakeSnapshotGrabber(jpeg=b"\xff\xd8\xff\xe0" + b"scene" * 200)   # 假现场帧
    pipe = AlarmSnapshotPipeline(alarm, snap, spool, prefix=PREFIX,
                                 on_captured=lambda e, k, s: print(f"  抓拍 {e}: {s} bytes → 入队"))

    # ---- 阶段1:代理下线 —— 烟感响,抓图入队,ship 不出去留队 ----
    print("[阶段1] 代理下线 —— 烟感报警,抓图入板子队列(证据不丢)")
    alarm.fire(now=100.0)
    for h in pipe.tick(now=100.0):
        print("  健康:", h["status"])
    spool.pump(now=100.0)                                # 代理下线 → 留队
    print(f"  阶段1 末:{spool.pending_count} 张在队,{len(shipped)} 已 ship(代理下线,应为 0)")

    # ---- 阶段2:代理上线 —— pump 补传 ----
    print("[阶段2] 代理上线 —— pump 存储转发")
    link.online = True
    spool.pump(now=200.0)
    print(f"  ship 到代理:{[k.split('/')[-1] for k in link.received]}")
    print(f"  阶段2 末:{spool.pending_count} 在队,{len(shipped)} 已 ship")

    # ---- 阶段3:相机离线时的告警 ----
    print("[阶段3] 相机离线 —— 抓图失败发告警,不静默")
    snap.online = False
    alarm.fire(now=300.0)
    hs = pipe.tick(now=300.0)
    print("  健康:", [h["status"] for h in hs])

    assert len(shipped) == 1 and spool.pending_count == 0
    assert any(h["status"] == "alarm_snapshot_failed" for h in hs)
    print("\nOK: 报警→抓图→入队→(代理下线留队)→上线补传;相机离线→告警不静默")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

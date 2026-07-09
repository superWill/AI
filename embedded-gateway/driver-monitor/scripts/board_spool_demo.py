#!/usr/bin/env python3
"""板子侧 spool 演示:代理下线时截帧留在板子本地队列不丢,代理上线后 pump 补传。

板子侧 spool = MediaOutbox(RelayUploader→代理) —— 和代理侧 MediaOutbox(→OSS)同构,两级存储转发。
本 demo 用开关模拟代理链路(真实现是 MediaRelayClient→本地 HTTP,见 media_relay_demo.py)。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from capture.keyframe import KeyframeThrottle, KeyframeConfig
from uplink.oss_media import event_media_key, oss_object_url
from uplink.media_outbox import MediaOutbox
from uplink.media_relay import RelayUploader

PREFIX = "driver-monitor"
ENDPOINT, BUCKET = "oss-cn-hangzhou.aliyuncs.com", "ubuntu-oss-313"


def fake_png(tag):
    return b"\x89PNG\r\n\x1a\n" + tag.encode()


class ToggleLink:
    """模拟板子→代理链路开关(真实现 = MediaRelayClient→HTTP)。"""

    def __init__(self, online=False):
        self.online = online
        self.received = []

    def ship(self, shipment):
        if not self.online:
            return False
        self.received.append(shipment.key)
        return True


def main() -> int:
    event_id = "po-000123"
    link = ToggleLink(online=False)                     # 代理先下线
    shipped = []
    sink = RelayUploader(link, lambda k: oss_object_url(ENDPOINT, BUCKET, k))
    spool = MediaOutbox(sink, on_uploaded=lambda mu: shipped.append(mu.key))
    throttle = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0, max_frames_per_event=4))

    # ---- 阶段1:代理下线 —— 截帧入板子队列,pump 推不出去,留队不丢 ----
    print("[阶段1] 代理下线 —— 截帧入板子本地队列(证据不丢)")
    for t in range(0, 26):
        cap = throttle.offer(event_id, now=float(t))
        if cap is not None:
            kind = "first_frame" if cap.is_first else "frame"
            key = event_media_key(PREFIX, event_id, cap.name)
            spool.enqueue(key, fake_png(cap.name), kind, occurred_at=float(t), now=float(t),
                          ref=event_id)
            print(f"  t={t:>2}  截帧入队 {cap.name}")
        spool.pump(now=float(t))                        # 代理下线 → ship 失败 → 留队
    throttle.close(event_id)
    print(f"  阶段1 末:{spool.pending_count} 帧在板子队列,{len(shipped)} 已推(代理下线,应为 0)")

    # ---- 阶段2:代理上线 —— pump 补传,first_frame 优先 ----
    print("[阶段2] 代理上线 —— pump 补传(first_frame 优先)")
    link.online = True
    spool.pump(now=100.0)
    print(f"  推送顺序:{[k.split('/')[-1] for k in link.received]}")
    print(f"  阶段2 末:{spool.pending_count} 帧在队,{len(shipped)} 已推")

    assert spool.pending_count == 0
    assert len(shipped) == 4
    assert link.received[0].endswith("first_frame.png")
    print("\nOK: 代理下线→板子留队不丢→上线补传→first_frame 优先 —— 板子侧 spool 落地")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

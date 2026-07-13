#!/usr/bin/env python3
"""RK3506 报警抓拍入口 —— 收烟感 → 抓相机快照 → 板子侧 spool ship 到代理(→OSS)。

在 RK3506 上跑(无外网,ship 到有网代理)。烟感 MVP 用触发文件(`touch $ALARM_TRIGGER` 模拟),
真硬件把 FileAlarmSource 换成 DI/Modbus/LoRa 源即可。相机快照走雄迈 webcapture.jpg(实测)。

env:
  CAM_SNAPSHOT_URL   默认 http://192.168.1.217/webcapture.jpg?command=snap&channel=0
  CAM_USER / CAM_PASS  相机 Basic 凭证(默认 admin / 空)
  AGENT_HOST / AGENT_PORT  代理(media_agent)地址,默认 192.168.1.2:8890
  OSS_ENDPOINT / OSS_BUCKET  用于预算最终 OSS URL(非秘密)
  SPOOL_DIR          板子侧落盘队列,默认 /tmp/dm-alarm-spool
  ALARM_TRIGGER      触发文件,默认 /tmp/alarm.trigger
  PREFIX             OSS key 前缀,默认 driver-monitor
  POLL_INTERVAL      轮询/pump 间隔秒,默认 1.0
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.alarm_source import FileAlarmSource
from alarm.snapshot import HttpSnapshotGrabber, SnapshotConfig
from alarm.pipeline import AlarmSnapshotPipeline
from uplink.media_outbox import MediaOutbox
from uplink.media_relay import MediaRelayClient, RelayUploader
from uplink.oss_media import oss_object_url
from uplink.spool_store import SpoolStore


def build(env=None):
    """按 env 组装。返回 (pipeline, spool, interval)。可测。"""
    env = env if env is not None else os.environ
    cam_url = env.get("CAM_SNAPSHOT_URL",
                      "http://192.168.1.217/webcapture.jpg?command=snap&channel=0")
    endpoint = env.get("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    bucket = env.get("OSS_BUCKET", "ubuntu-oss-313")
    prefix = env.get("PREFIX", "driver-monitor")
    interval = float(env.get("POLL_INTERVAL", "1.0"))

    snapshot = HttpSnapshotGrabber(SnapshotConfig(
        url=cam_url, username=env.get("CAM_USER", "admin"), password=env.get("CAM_PASS", "")))
    relay = MediaRelayClient(env.get("AGENT_HOST", "192.168.1.2"),
                             int(env.get("AGENT_PORT", "8890")))
    sink = RelayUploader(relay, lambda k: oss_object_url(endpoint, bucket, k))
    spool = MediaOutbox(sink, store=SpoolStore(env.get("SPOOL_DIR", "/tmp/dm-alarm-spool")),
                        on_uploaded=lambda mu: print(f"[ship] {mu.key} → 代理", flush=True))
    alarm = FileAlarmSource(env.get("ALARM_TRIGGER", "/tmp/alarm.trigger"))
    pipe = AlarmSnapshotPipeline(alarm, snapshot, spool, prefix=prefix,
                                 on_captured=lambda e, k, s: print(f"[抓拍] {e} {s}B → 入队", flush=True))
    return pipe, spool, interval


def main() -> int:
    pipe, spool, interval = build()
    print(f"[rk3506] 报警抓拍入口启动;touch {os.environ.get('ALARM_TRIGGER', '/tmp/alarm.trigger')} 触发报警。Ctrl-C 停。",
          flush=True)
    try:
        while True:
            now = time.time()
            for h in pipe.tick(now):
                print(f"[健康] {h['status']}: {h['detail']}", flush=True)
            spool.pump(now)
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

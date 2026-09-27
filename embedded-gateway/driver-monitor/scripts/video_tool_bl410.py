#!/usr/bin/env python3
"""BL410(RK3568)视频工具服务入口 —— 视频统一收到本板,对外 HTTP API 供 RK3506/平台调。

在 BL410 上跑。抓帧走雄迈 webcapture.jpg;OSS egress 走 agent 一跳(board→lobster→OSS,板无外网);
直播走本板已固化的 go2rtc;视觉 analyze 走 RKNN(当前留桩,给了 RKNN_MODEL 才建骨架)。

env:
  CAM_SNAPSHOT_URL   默认 http://192.168.1.217/webcapture.jpg?command=snap&channel=0
  CAM_USER / CAM_PASS  相机 Basic 凭证(默认 admin / 空)
  AGENT_HOST / AGENT_PORT  lobster media_agent(默认 192.168.1.2:8890;BL410 经有线到 lobster enp3s0)
  OSS_ENDPOINT / OSS_BUCKET  预算最终 OSS URL(非秘密)
  GO2RTC_BASE        直播基址,默认 http://192.168.1.227:1984(lobster 转发,手机可达)
  DEFAULT_CAM        go2rtc stream 名,默认 cam
  PREFIX             OSS key 前缀,默认 driver-monitor
  SPOOL_DIR          板子侧落盘队列,默认 /tmp/dm-video-spool
  LISTEN_HOST / LISTEN_PORT  服务监听,默认 0.0.0.0 / 8891
  POLL_INTERVAL      pump 间隔秒,默认 2.0
  RKNN_MODEL         给了则建 RknnVisionAnalyzer 骨架,否则 StubVisionAnalyzer
"""
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from alarm.snapshot import HttpSnapshotGrabber, SnapshotConfig
from uplink.media_outbox import MediaOutbox
from uplink.media_relay import MediaRelayClient, RelayUploader
from uplink.oss_media import oss_object_url
from uplink.spool_store import SpoolStore
from video.analyze import RknnVisionAnalyzer, StubVisionAnalyzer
from video.service import VideoToolService, build_http_server, run_pump_loop


def build(env=None):
    """按 env 组装。返回 (service, outbox, listen, interval)。可测。"""
    env = env if env is not None else os.environ
    cam_url = env.get("CAM_SNAPSHOT_URL",
                      "http://192.168.1.217/webcapture.jpg?command=snap&channel=0")
    endpoint = env.get("OSS_ENDPOINT", "oss-cn-hangzhou.aliyuncs.com")
    bucket = env.get("OSS_BUCKET", "ubuntu-oss-313")
    prefix = env.get("PREFIX", "driver-monitor")

    grabber = HttpSnapshotGrabber(SnapshotConfig(
        url=cam_url, username=env.get("CAM_USER", "admin"), password=env.get("CAM_PASS", "")))
    relay = MediaRelayClient(env.get("AGENT_HOST", "192.168.1.2"),
                             int(env.get("AGENT_PORT", "8890")))
    url_for = lambda k: oss_object_url(endpoint, bucket, k)   # noqa: E731
    sink = RelayUploader(relay, url_for)
    outbox = MediaOutbox(sink, store=SpoolStore(env.get("SPOOL_DIR", "/tmp/dm-video-spool")))

    model = env.get("RKNN_MODEL", "").strip()
    analyzer = RknnVisionAnalyzer(model) if model else StubVisionAnalyzer()

    service = VideoToolService(
        grabber, outbox, analyzer, url_for,
        go2rtc_base=env.get("GO2RTC_BASE", "http://192.168.1.227:1984"),
        default_cam=env.get("DEFAULT_CAM", "cam"), prefix=prefix)
    listen = (env.get("LISTEN_HOST", "0.0.0.0"), int(env.get("LISTEN_PORT", "8891")))
    interval = float(env.get("POLL_INTERVAL", "2.0"))
    return service, outbox, listen, interval


def main() -> int:
    service, outbox, (host, port), interval = build()
    httpd, lock = build_http_server(service, host, port)
    stop = threading.Event()
    pump = threading.Thread(target=run_pump_loop, args=(outbox, lock),
                            kwargs={"interval_s": interval, "stop": stop}, daemon=True)
    pump.start()
    print(f"[video-tool] 监听 http://{host}:{port} "
          f"(analyzer={service.analyzer.model}, go2rtc={service.go2rtc_base}); Ctrl-C 停。",
          flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

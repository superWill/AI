#!/usr/bin/env python3
"""上传代理入口 —— 在有网节点(跳板/ECS)上跑:收板子推来的证据 → 持久化落盘 → 传 OSS。

把已验证的件拧成一个可部署服务:
  MediaReceiver(收) → MediaOutbox(store=SpoolStore, 持久化) → AliyunOSSUploader(传 OSS)
  + build_agent_server(HTTP 收包) + run_pump_loop(后台补传)

env:
  OSS_ENDPOINT/OSS_BUCKET/OSS_ACCESS_KEY_ID/OSS_ACCESS_KEY_SECRET  凭证(缺则用 Fake 本地演示)
  AGENT_HOST(默认 0.0.0.0) / AGENT_PORT(默认 8890) / AGENT_SPOOL_DIR(默认 /tmp/dm-agent-spool)
  AGENT_PUMP_INTERVAL(秒,默认 2.0)
部署:systemd/init 拉起本脚本即可;凭证走环境,勿入库。Ctrl-C 停。
"""
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.oss_media import AliyunOSSUploader, FakeMediaUploader
from uplink.media_outbox import MediaOutbox
from uplink.media_relay import MediaReceiver, build_agent_server, run_pump_loop
from uplink.spool_store import SpoolStore


def build_agent(env=None):
    """按 env 组装代理。返回 (httpd, lock, outbox, uploader, interval)。可测(port=0)。"""
    env = env if env is not None else os.environ
    host = env.get("AGENT_HOST", "0.0.0.0")
    port = int(env.get("AGENT_PORT", "8890"))
    spool_dir = env.get("AGENT_SPOOL_DIR", "/tmp/dm-agent-spool")
    interval = float(env.get("AGENT_PUMP_INTERVAL", "2.0"))
    if env.get("OSS_ENDPOINT"):
        uploader = AliyunOSSUploader.from_env(env)
    else:
        uploader = FakeMediaUploader()                 # 无凭证:本地演示
    outbox = MediaOutbox(uploader, store=SpoolStore(spool_dir),
                         on_uploaded=lambda mu: print(f"[agent] ✔ {mu.kind} {mu.key}", flush=True))
    httpd, lock = build_agent_server(MediaReceiver(outbox), host=host, port=port)
    return httpd, lock, outbox, uploader, interval


def main() -> int:
    httpd, lock, outbox, uploader, interval = build_agent()
    port = httpd.server_address[1]
    print(f"[agent] 监听 :{port},spool 持久化,pump 每 {interval}s → {type(uploader).__name__}",
          flush=True)
    stop = threading.Event()
    threading.Thread(target=run_pump_loop, args=(outbox, lock),
                     kwargs={"interval_s": interval, "stop": stop}, daemon=True).start()
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

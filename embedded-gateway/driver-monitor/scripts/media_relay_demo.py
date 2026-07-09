#!/usr/bin/env python3
"""板子→代理→OSS 全链路演示:采集机(无外网)经本地 HTTP 把关键帧推给代理,代理跑 MediaOutbox 传 OSS。

  板子(截帧,只够得着代理) ──本地 HTTP──▶ 代理(MediaReceiver→MediaOutbox) ──公网──▶ OSS

默认假 OSS(离线可跑);--live 代理侧走真 OSS(需 OSS_* 环境变量)。端口绑不了则跳过。
"""
import os
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from capture.keyframe import KeyframeThrottle, KeyframeConfig
from uplink.oss_media import FakeMediaUploader, AliyunOSSUploader, event_media_key
from uplink.media_outbox import MediaOutbox
from uplink.media_relay import MediaShipment, MediaRelayClient, MediaReceiver, build_agent_server
from uplink.envelope import EventEnvelope

PREFIX = "driver-monitor"


def fake_png(tag: str) -> bytes:
    return b"\x89PNG\r\n\x1a\n" + tag.encode()


def main() -> int:
    live = "--live" in sys.argv
    event_id = "po-000123"

    # ---- 代理侧:MediaReceiver → MediaOutbox → OSS ----
    if live:
        uploader = AliyunOSSUploader.from_env()
        print(f"[agent] 真 OSS: {uploader.c.bucket} @ {uploader.c.endpoint}")
    else:
        uploader = FakeMediaUploader(base_url="https://demo.oss-cn-hangzhou.aliyuncs.com")
    uploaded: dict[str, str] = {}

    def on_uploaded(mu):
        uploaded[mu.key] = mu.url
        print(f"      [agent] ✔ {mu.kind:<11} 上传 → {mu.key.split('/')[-1]}")

    outbox = MediaOutbox(uploader, on_uploaded=on_uploaded)
    receiver = MediaReceiver(outbox)
    try:
        httpd, lock = build_agent_server(receiver, host="127.0.0.1", port=0)
    except OSError:
        print("跳过:无法绑定本地端口(受限沙箱)")
        return 0
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    print(f"[agent] 代理在 127.0.0.1:{port} 收证据 → MediaOutbox → OSS")

    # ---- 板子侧:无外网,只把证据推给代理 ----
    throttle = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0, max_frames_per_event=4))
    client = MediaRelayClient("127.0.0.1", port, timeout_s=3.0)
    print("[board] 事件进行 —— 截帧经本地 HTTP 推给代理(板子不碰公网)")
    for t in range(0, 26):
        cap = throttle.offer(event_id, now=float(t))
        if cap is None:
            continue
        kind = "first_frame" if cap.is_first else "frame"
        key = event_media_key(PREFIX, event_id, cap.name)
        ok = client.ship(MediaShipment(key, kind, float(t), event_id, fake_png(cap.name)))
        print(f"  t={t:>2}  截帧→代理 {cap.name:<12} {'ok' if ok else '代理不可达(留存重试)'}")
    throttle.close(event_id)

    # ---- 代理 pump:证据推 OSS ----
    print("[agent] pump → OSS")
    with lock:
        outbox.pump(now=100.0)
    httpd.shutdown()

    # ---- 板子回填 envelope:key 确定性,板子自己就能算 URL,不必等上传 ----
    first_key = event_media_key(PREFIX, event_id, "first_frame")
    frame_urls = sorted(u for k, u in uploaded.items() if k != first_key)
    env = EventEnvelope.from_event(
        {"type": "person_observation", "event_kind": "open",
         "event_id": event_id, "ts_start": 1783072803.0, "confidence": 0.91},
        thumbnail_ref=uploader.object_url(first_key),
        evidence_ref={"frames": frame_urls,
                      "evidence_status": "uploaded" if first_key in uploaded else "pending"})
    d = env.to_dict()
    print("[board] envelope 回填(thumbnail_ref 用确定性 URL,不依赖上传完成)")
    print("  thumbnail_ref =", d["thumbnail_ref"])
    print("  evidence_status =", d["evidence_ref"]["evidence_status"], "· 已上传", len(uploaded), "帧")

    assert len(uploaded) == 4 and first_key in uploaded
    print("\nOK: 板子(无外网)→本地HTTP→代理MediaOutbox→OSS 全链路自洽")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

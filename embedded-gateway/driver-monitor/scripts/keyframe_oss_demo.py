#!/usr/bin/env python3
"""关键帧节流 → MediaOutbox 异步存储转发 → OSS → 回填 envelope 的端到端演示。

演示"截帧≠上传"的解耦:
  - 截帧只 enqueue(快、本地),**不阻塞检测循环**;上传由 MediaOutbox 后台 pump 异步做。
  - 板子离线时帧留队不丢;联网后 pump 按优先级(first_frame 先)补传(存储转发)。
  - on_uploaded 回调把 evidence_status pending→uploaded。

纯标准库,默认离线(FakeMediaUploader,演示存储转发);--live 走真 OSS(需 OSS_* 环境变量)。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from capture.keyframe import KeyframeThrottle, KeyframeConfig
from uplink.oss_media import FakeMediaUploader, AliyunOSSUploader, event_media_key
from uplink.media_outbox import MediaOutbox
from uplink.envelope import EventEnvelope

PREFIX = "driver-monitor"


def fake_png(tag: str) -> bytes:
    """占位:真实现用 png_writer.write_png(decoded_rgb) 得到 PNG 字节。"""
    return b"\x89PNG\r\n\x1a\n" + tag.encode()


def main() -> int:
    live = "--live" in sys.argv
    throttle = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0, max_frames_per_event=4))
    if live:
        uploader = AliyunOSSUploader.from_env()          # 真 OSS
        print(f"[live] 真 OSS: {uploader.c.bucket} @ {uploader.c.endpoint}")
    else:
        uploader = FakeMediaUploader(
            base_url="https://demo.oss-cn-hangzhou.aliyuncs.com",
            online=False)                                # 先离线,演示存储转发

    event_id = "po-000123"
    first_key = event_media_key(PREFIX, event_id, "first_frame")
    uploaded: dict[str, str] = {}                        # key → url(on_uploaded 回填)
    evidence_status = {"v": "pending"}

    def on_uploaded(mu):                                 # MediaUpload
        uploaded[mu.key] = mu.url
        if mu.key == first_key:                          # first_frame 到位即可标 uploaded
            evidence_status["v"] = "uploaded"
        print(f"      ✔ {mu.kind:<11} 上传确认 → evidence_status={evidence_status['v']}")

    outbox = MediaOutbox(uploader, on_uploaded=on_uploaded)

    # ---- 阶段1:事件进行 + 板子离线 —— 截帧只入队,pump 尝试但传不出去 ----
    print("[阶段1] 事件进行" + ("" if live else " · 板子离线") + " —— 截帧入队(不阻塞检测)")
    for t in range(0, 26):
        cap = throttle.offer(event_id, now=float(t))
        if cap is not None:
            kind = "first_frame" if cap.is_first else "frame"
            key = event_media_key(PREFIX, event_id, cap.name)
            outbox.enqueue(key, fake_png(cap.name), kind,
                           occurred_at=float(t), now=float(t), ref=event_id)
            print(f"  t={t:>2}  截帧入队 {cap.name}")
        outbox.pump(now=float(t))                        # 后台驱动(离线→留队)
    throttle.close(event_id)
    print(f"  阶段1 末:{outbox.pending_count} 帧在队,{len(uploaded)} 已上传,"
          f"evidence_status={evidence_status['v']}")

    # ---- 阶段2:板子联网 —— pump 存储转发,按优先级 first_frame 先 ----
    print("[阶段2] " + ("继续 pump" if live else "板子联网")
          + " —— 存储转发补传(first_frame 优先)")
    if not live:
        uploader.set_online(True)
    outbox.pump(now=100.0)
    print(f"  阶段2 末:{outbox.pending_count} 帧在队,{len(uploaded)} 已上传")

    # ---- 阶段3:回填 envelope ----
    frame_urls = sorted(u for k, u in uploaded.items() if k != first_key)
    envelope = EventEnvelope.from_event(
        {"type": "person_observation", "event_kind": "open",
         "event_id": event_id, "ts_start": 1783072803.0, "confidence": 0.91},
        thumbnail_ref=uploaded.get(first_key),
        evidence_ref={"frames": frame_urls, "evidence_status": evidence_status["v"]})
    d = envelope.to_dict()
    print("[阶段3] envelope 回填")
    print("  thumbnail_ref =", d["thumbnail_ref"])
    print("  evidence_ref  =", d["evidence_ref"])

    assert outbox.pending_count == 0
    assert d["thumbnail_ref"] == uploader.object_url(first_key)
    assert evidence_status["v"] == "uploaded"
    print("\nOK: 截帧→入队→(离线留队)→pump 补传→回填 —— 解耦落地,离线不丢,first_frame 优先")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# --- 真机上线清单 ---
# export OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com OSS_BUCKET=... \
#        OSS_ACCESS_KEY_ID=... OSS_ACCESS_KEY_SECRET=...   # 勿入库
# uploader = AliyunOSSUploader.from_env()                   # 换掉 FakeMediaUploader
# 帧编码: from util.png_writer import write_png  (需 numpy 解码帧)
# 板端无外网时: enqueue 落本地/内存,pump 在有网时补传;真 durable 需持久化队列。

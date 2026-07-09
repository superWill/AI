#!/usr/bin/env python3
"""关键帧节流 → OSS 上传 → 回填 envelope 的离线端到端演示(纯标准库,无网络/无凭证)。

真机切换只需两点(见文件尾注释):
  1. FakeMediaUploader → AliyunOSSUploader.from_env()
  2. 占位 PNG 字节 → util.png_writer.write_png(np_frame) 编码真解码帧
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from capture.keyframe import KeyframeThrottle, KeyframeConfig
from uplink.oss_media import FakeMediaUploader, AliyunOSSUploader, event_media_key
from uplink.envelope import EventEnvelope

PREFIX = "driver-monitor"


def fake_png(tag: str) -> bytes:
    """占位:真实现用 png_writer.write_png(decoded_rgb) 得到 PNG 字节。"""
    return b"\x89PNG\r\n\x1a\n" + tag.encode()


def main() -> int:
    live = "--live" in sys.argv
    throttle = KeyframeThrottle(KeyframeConfig(min_interval_s=5.0, max_frames_per_event=4))
    if live:
        uploader = AliyunOSSUploader.from_env()          # 真 OSS(需环境变量)
        print(f"[live] 上传到 {uploader.c.bucket} @ {uploader.c.endpoint}")
    else:
        uploader = FakeMediaUploader(base_url="https://demo.oss-cn-hangzhou.aliyuncs.com")

    event_id = "po-000123"
    first_url = None
    frame_urls: list[str] = []
    uploaded_keys: list[str] = []                        # 本地追踪,不依赖上传器内部

    # 模拟事件持续 26 秒,每秒一帧(节流5s,封顶4):
    # 出帧于 t=0/5/10/15,t=20 触顶后不再出 → 恰好 4 帧
    for t in range(0, 26):
        cap = throttle.offer(event_id, now=float(t))
        if cap is None:
            continue
        key = event_media_key(PREFIX, event_id, cap.name)
        url = uploader.put(key, fake_png(cap.name))          # 离线时返回 None → 上层重试
        if url is None:
            print(f"  t={t:>2}  {cap.name:<12} 离线,留队重试")
            continue
        print(f"  t={t:>2}  {cap.name:<12} → {url}")
        uploaded_keys.append(key)
        if cap.is_first:
            first_url = url
        else:
            frame_urls.append(url)

    throttle.close(event_id)

    # 回填 envelope:first_frame → thumbnail_ref;代表帧 → evidence_ref["frames"]
    ev = {"type": "person_observation", "event_kind": "open",
          "event_id": event_id, "ts_start": 1783072803.0, "confidence": 0.91}
    envelope = EventEnvelope.from_event(
        ev,
        thumbnail_ref=first_url,
        evidence_ref={"frames": frame_urls, "evidence_status": "partial"},
    )
    d = envelope.to_dict()
    print("\nenvelope.thumbnail_ref =", d["thumbnail_ref"])
    print("envelope.evidence_ref  =", d["evidence_ref"])
    print("uploaded objects       =", uploaded_keys)

    assert d["thumbnail_ref"] == uploader.object_url(
        event_media_key(PREFIX, event_id, "first_frame"))
    assert len(uploaded_keys) == 4                            # 封顶 4 帧
    print("\nOK: 截帧→上传→回填 链路自洽")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# --- 真机上线清单 ---
# export OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com OSS_BUCKET=... \
#        OSS_ACCESS_KEY_ID=... OSS_ACCESS_KEY_SECRET=...   # 勿入库
# uploader = AliyunOSSUploader.from_env()                   # 换掉 FakeMediaUploader
# 帧编码: from util.png_writer import write_png  (需 numpy 解码帧)
# 板端无外网时: put() 返回 None → 由 DurableOutbox/证据环存储转发,联网即补传。

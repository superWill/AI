#!/usr/bin/env python3
"""OSS 真机上传自检 —— 从环境读凭证,上传一张 1x1 PNG,验证端到端。

用法(凭证放环境变量,勿写进代码/勿入库):
  set -a; . ~/dm-oss.env; set +a       # 该文件含 4 个 OSS_* 变量,在仓库外
  python3 scripts/oss_live_check.py

成功即打印 object URL,去 OSS 控制台 → ubuntu-oss-313 → 文件管理 可预览该图。
"""
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from uplink.oss_media import AliyunOSSUploader, MediaUploadError, event_media_key


def _make_png(w: int = 64, h: int = 64, rgb=(0, 150, 136)) -> bytes:
    """程序生成合法 PNG(8-bit RGB,纯标准库)。比脆弱的 base64 常量可靠。"""
    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    idat = zlib.compress((b"\x00" + bytes(rgb) * w) * h, 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat) + chunk(b"IEND", b""))


TINY_PNG = _make_png()


def main() -> int:
    try:
        up = AliyunOSSUploader.from_env()
    except RuntimeError as e:
        print("环境未配好:", e)
        print("请先: set -a; . ~/dm-oss.env; set +a")
        return 2

    key = event_media_key(up.c.key_prefix, "_healthcheck", "ping")
    print(f"目标 bucket={up.c.bucket} endpoint={up.c.endpoint}")
    print(f"上传 key={key} ({len(TINY_PNG)} bytes) …")
    try:
        url = up.put(key, TINY_PNG, "image/png")
    except MediaUploadError as e:
        print(f"上传被拒 status={e.status} —— 多半是凭证/权限/桶名错(4xx),不是网络问题")
        return 3
    if url is None:
        print("上传返回 None —— 断网/超时/5xx,属暂时性,可重试")
        return 4
    print("OK 上传成功:", url)
    print(f"去 OSS 控制台 → {up.c.bucket} → 文件管理 → {key} 可在线预览")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""磁盘落地的 spool store —— 让 MediaOutbox 的队列挺过重启(未上传证据不因重启丢)。

- **原子写**:tmp + fsync + os.replace,断电不留半截文件。
- **帧格式**:4 字节 BE 头长 + JSON 头(key/kind/occurred_at/ref/content_type/enqueued_at) + 原始字节。
- **损坏文件不静默丢**:解析失败的 .spool 重命名为 .corrupt 隔离(人可查),不当正常记录加载。
- 纯标准库;`InMemorySpoolStore` 为测试/无盘替身,接口一致。

跨重启幂等:靠"上传成功即从 store 删文件 → 重启不再加载"。极端下(删文件失败)重启可能重传,
但 key 确定性、OSS 覆盖写,重传无害(只浪费一次)。
"""
from __future__ import annotations

import hashlib
import json
import os
import struct


def _frame(header: dict, data: bytes) -> bytes:
    hb = json.dumps(header, ensure_ascii=False).encode("utf-8")
    return struct.pack(">I", len(hb)) + hb + data


def _unframe(blob: bytes) -> tuple[dict, bytes]:
    if len(blob) < 4:
        raise ValueError("blob too short")
    hlen = struct.unpack(">I", blob[:4])[0]
    if 4 + hlen > len(blob):
        raise ValueError("truncated header")
    header = json.loads(blob[4:4 + hlen].decode("utf-8"))
    return header, blob[4 + hlen:]


class SpoolStore:
    def __init__(self, directory: str):
        self.dir = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, key: str) -> str:
        name = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return os.path.join(self.dir, name + ".spool")

    def save(self, key: str, header: dict, data: bytes) -> None:
        path = self._path(key)
        tmp = path + ".tmp"
        with open(tmp, "wb") as f:
            f.write(_frame(header, data))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)                       # 原子:要么旧要么新,无半截

    def remove(self, key: str) -> None:
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass

    def load_all(self) -> list[tuple[dict, bytes]]:
        out: list[tuple[dict, bytes]] = []
        for fn in sorted(os.listdir(self.dir)):
            if not fn.endswith(".spool"):
                continue
            path = os.path.join(self.dir, fn)
            try:
                with open(path, "rb") as f:
                    header, data = _unframe(f.read())
                if "key" not in header:
                    raise ValueError("no key in header")
            except (ValueError, OSError):
                os.replace(path, path + ".corrupt")  # 隔离,不静默丢
                continue
            out.append((header, data))
        return out


class InMemorySpoolStore:
    """测试/无盘替身:内存字典,接口同 SpoolStore。"""

    def __init__(self):
        self._d: dict[str, tuple[dict, bytes]] = {}

    def save(self, key: str, header: dict, data: bytes) -> None:
        self._d[key] = (dict(header), data)

    def remove(self, key: str) -> None:
        self._d.pop(key, None)

    def load_all(self) -> list[tuple[dict, bytes]]:
        return [(dict(h), d) for h, d in self._d.values()]

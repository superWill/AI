#!/usr/bin/env python3
"""保留期 GC —— 纯逻辑。按「上传/投递状态 + 保留时间窗」决定本地证据副本何时可删。

与 SegmentRing 正交互补:
  - SegmentRing:按**容量**淘汰 clip 段(over max_bytes 才淘,未投递 pin 段永不删)。
  - RetentionGC:按**时间窗 + 上传状态**回收本地副本(帧/clip 皆可),容量没超也到期回收。

三条不可破的红线:
  1. **绝不回收未上传的证据** —— 本地副本是它上云前的唯一凭据,丢了就没了。
  2. 上传成功后再留 `retention_after_upload_s`(复查/补投缓冲窗),过窗才可删。
  3. 未上传却超龄(`stuck_warn_s`)→ 发 evidence_stuck 告警,**不静默久留**。

云侧保留由 OSS 生命周期规则(按前缀/天数自动过期)承担,零代码、需 PutBucketLifecycle 权限,
与本模块(管**本地**副本)互补;本模块不删 OSS 对象。

用法:note_created(截帧时)→ note_uploaded(接 MediaOutbox.on_uploaded)→ [note_delivered(平台确认)]
→ 周期 collect(now) 拿可删 key,删本地文件后 forget()。纯逻辑零 I/O,可离线单测。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass
class RetentionConfig:
    retention_after_upload_s: float = 3600.0   # 上传成功后本地再留多久才可删(缓冲/复查窗)
    require_delivered: bool = False            # True 则还需平台 delivered 才可删(更严)
    stuck_warn_s: float = 1800.0               # 未上传却超此龄 → evidence_stuck 告警
    max_tracked: int = 5000                    # 跟踪上限;超则告警(不丢记录——丢=忘掉未上传证据)


@dataclass
class _Rec:
    kind: str
    created_at: float
    uploaded_at: float | None = None
    delivered_at: float | None = None


class RetentionStore:
    """跟踪表落盘(JSON,原子写)。只存元数据(无字节),故一个小文件即可。"""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def load(self) -> dict:
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, ValueError):
            return {}

    def save(self, records: dict) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.path)


class InMemoryRetentionStore:
    """测试替身。"""

    def __init__(self):
        self._d: dict = {}

    def load(self) -> dict:
        return dict(self._d)

    def save(self, records: dict) -> None:
        self._d = dict(records)


class RetentionGC:
    def __init__(self, config: RetentionConfig | None = None, store=None):
        """store:可选 RetentionStore —— 传入则跟踪表落盘,重启重建(丢=停止GC非丢证据,次要)。"""
        self.cfg = config or RetentionConfig()
        self._store = store
        self._recs: dict[str, _Rec] = {}
        self._stuck_reported: set[str] = set()
        self._over_tracked_reported = False
        if store is not None:
            self._load()

    def _load(self) -> None:
        for key, r in self._store.load().items():
            self._recs[key] = _Rec(
                kind=r.get("kind", "frame"), created_at=r.get("created_at", 0.0),
                uploaded_at=r.get("uploaded_at"), delivered_at=r.get("delivered_at"))

    def checkpoint(self) -> None:
        """把跟踪表落盘(collect/forget 末尾自动调;也可显式调)。"""
        if self._store is None:
            return
        self._store.save({k: {"kind": r.kind, "created_at": r.created_at,
                              "uploaded_at": r.uploaded_at, "delivered_at": r.delivered_at}
                          for k, r in self._recs.items()})

    # ---- 生命周期事件 ----
    def note_created(self, key: str, kind: str, now: float) -> None:
        if key not in self._recs:
            self._recs[key] = _Rec(kind=kind, created_at=now)

    def note_uploaded(self, key: str, now: float) -> None:
        r = self._recs.get(key)
        if r is not None and r.uploaded_at is None:
            r.uploaded_at = now

    def note_delivered(self, key: str, now: float) -> None:
        r = self._recs.get(key)
        if r is not None and r.delivered_at is None:
            r.delivered_at = now

    # ---- 回收判定 ----
    def collect(self, now: float) -> tuple[list[str], list[dict]]:
        """返回 (可删本地副本的 key, 健康信号)。只回收已上传(+可选已投递)且过保留窗的;
        绝不回收未上传的;未上传超龄发 evidence_stuck。"""
        evictable: list[str] = []
        health: list[dict] = []
        for key, r in self._recs.items():
            if r.uploaded_at is not None:
                past_window = now - r.uploaded_at >= self.cfg.retention_after_upload_s
                delivered_ok = (not self.cfg.require_delivered) or r.delivered_at is not None
                if past_window and delivered_ok:
                    evictable.append(key)
                continue
            # 未上传:红线①绝不回收;检查是否卡住
            if now - r.created_at >= self.cfg.stuck_warn_s and key not in self._stuck_reported:
                self._stuck_reported.add(key)
                health.append(self._health(
                    "evidence_stuck",
                    f"{key} 未上传已 {round(now - r.created_at, 1)}s", now))
        health += self._tracked_health(now)
        self.checkpoint()                              # 落盘(捕获 note_* 更新)
        return evictable, health

    def forget(self, keys) -> None:
        """本地副本已删,停止跟踪。"""
        for k in keys:
            self._recs.pop(k, None)
            self._stuck_reported.discard(k)
        self.checkpoint()                              # 落盘(捕获移除)

    # ---- 健康:跟踪量 ----
    def _tracked_health(self, now: float) -> list[dict]:
        over = len(self._recs) > self.cfg.max_tracked
        if over and not self._over_tracked_reported:
            self._over_tracked_reported = True
            return [self._health("retention_over_tracked",
                                 f"tracked {len(self._recs)} > {self.cfg.max_tracked}", now)]
        if not over:
            self._over_tracked_reported = False
        return []

    def _health(self, status: str, detail: str, ts: float) -> dict:
        return {"type": "retention_health", "status": status,
                "detail": detail, "ts": round(ts, 3)}

    # ---- 只读 ----
    def state_of(self, key: str) -> _Rec | None:
        return self._recs.get(key)

    @property
    def tracked_count(self) -> int:
        return len(self._recs)

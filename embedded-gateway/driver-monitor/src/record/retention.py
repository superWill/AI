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


class RetentionGC:
    def __init__(self, config: RetentionConfig | None = None):
        self.cfg = config or RetentionConfig()
        self._recs: dict[str, _Rec] = {}
        self._stuck_reported: set[str] = set()
        self._over_tracked_reported = False

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
        return evictable, health

    def forget(self, keys) -> None:
        """本地副本已删,停止跟踪。"""
        for k in keys:
            self._recs.pop(k, None)
            self._stuck_reported.discard(k)

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

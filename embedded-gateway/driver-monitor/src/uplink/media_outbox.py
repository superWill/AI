#!/usr/bin/env python3
"""媒体存储转发 outbox —— 纯逻辑。截帧≠上传:把关键帧字节异步推 OSS,不阻塞检测循环。

与 DurableOutbox(元数据两阶段托管)平级、同构,但**上传无 broker ack**——MediaUploader.put()
返回 URL 即确认。故状态更简单:
  QUEUED ─put=url→ UPLOADED(终态,回调 on_uploaded)
         ─put=None(离线/5xx)→ 留队,resend_after_s 后重试(存储转发)
         ─put 抛 MediaUploadError(4xx 凭证/权限/桶错)→ FAILED(终态,不重试,发健康告警)

- 优先级:first_frame > 代表帧(frame) > clip。补投序=优先级高先 → 原始 occurred_at 旧先。
- 幂等:按 OSS key 去重;已上传/在队/已失败的 key 重复 enqueue 忽略。
- 禁止静默丢失:first_frame 永不淘汰;非 first_frame 超容量**淘旧但发 media_dropped**,非静默。
- 隔离:本模块零 I/O、零网络,靠注入的 uploader(鸭子类型 put/object_url);可完全离线单测。

注意:`_entries` 为**内存态**,重启即失;跨重启 durable 需配持久化(本地证据环 pin + 落盘队列),
非本模块职责。大 clip 目前按字节入队;未来应改惰性引用(路径+按需读),避免内存驻留 MB 级数据。
"""
from __future__ import annotations

from dataclasses import dataclass

from uplink.oss_media import MediaUploadError


class MediaOutboxState:
    QUEUED = "queued"
    UPLOADED = "uploaded"
    FAILED = "failed"


# 媒体种类 → 优先级 rank(发送/淘汰排序)。first_frame 最高且永不淘汰。
_MEDIA_RANK = {"first_frame": 2, "frame": 1, "clip": 0}
_PROTECTED = "first_frame"


@dataclass
class MediaOutboxConfig:
    resend_after_s: float = 30.0        # 一次上传失败(离线/5xx)后重试间隔
    max_backlog: int = 500              # 未上传条数超此 → backlog 告警
    oldest_age_warn_s: float = 300.0    # 最旧未上传年龄超此 → 告警
    cappable_cap: int = 200             # 非 first_frame 未上传上限,超则淘旧(发告警,非静默)


@dataclass
class _MediaEntry:
    key: str
    data: bytes
    content_type: str
    kind: str
    occurred_at: float                  # 事件原始发生时间,补投永不冒充
    ref: object                         # 调用方关联句柄(event_id / envelope),回调时带回
    state: str
    enqueued_at: float
    last_attempt_ts: float = -1e18
    attempts: int = 0
    priority_rank: int = 0


@dataclass(frozen=True)
class MediaUpload:
    """上传成功回执,喂给 on_uploaded(据此把 evidence_status pending→uploaded)。"""
    key: str
    url: str
    kind: str
    ref: object


class MediaOutbox:
    def __init__(self, uploader, config: MediaOutboxConfig | None = None,
                 on_uploaded=None):
        """uploader:鸭子类型(put/object_url)。on_uploaded(MediaUpload):上传确认回调。"""
        self.uploader = uploader
        self.cfg = config or MediaOutboxConfig()
        self._on_uploaded = on_uploaded
        self._entries: dict[str, _MediaEntry] = {}   # key → entry(仅 QUEUED)
        self._uploaded_keys: set[str] = set()          # 已上传 key(幂等)
        self._failed_keys: set[str] = set()            # 4xx 永久失败 key(幂等,不重试)
        self._backlog_reported = False

    # ---- 入队(幂等) ----
    def enqueue(self, key: str, data: bytes, kind: str, occurred_at: float,
                now: float, *, content_type: str = "image/png",
                ref: object = None) -> list[dict]:
        if key in self._uploaded_keys or key in self._entries or key in self._failed_keys:
            return []                                   # 已上传/在队/已失败 → 幂等忽略
        self._entries[key] = _MediaEntry(
            key=key, data=data, content_type=content_type, kind=kind,
            occurred_at=occurred_at, ref=ref, state=MediaOutboxState.QUEUED,
            enqueued_at=now, priority_rank=_MEDIA_RANK.get(kind, 0))
        return self._cap_cappable(now)

    # ---- 驱动:上传 due + 健康 ----
    def pump(self, now: float) -> list[dict]:
        health: list[dict] = []
        health += self._send_due(now)
        health += self._backlog_health(now)
        return health

    def _send_due(self, now: float) -> list[dict]:
        health: list[dict] = []
        due = [e for e in self._entries.values()
               if e.attempts == 0
               or now - e.last_attempt_ts >= self.cfg.resend_after_s]
        # 补投序:first_frame 先(rank 降序)→ 原始 occurred_at 旧先
        due.sort(key=lambda e: (-e.priority_rank, e.occurred_at))
        for e in due:
            try:
                url = self.uploader.put(e.key, e.data, e.content_type)
            except MediaUploadError as ex:
                self._entries.pop(e.key, None)          # 4xx 永久错:移出队,不重试
                self._failed_keys.add(e.key)
                health.append(self._health(
                    "media_upload_failed", f"{e.key} status={ex.status}", now))
                continue
            if url is None:                             # 离线/5xx → 留队重试(存储转发)
                e.attempts += 1
                e.last_attempt_ts = now
                continue
            self._entries.pop(e.key, None)              # 成功:移出队
            self._uploaded_keys.add(e.key)
            if self._on_uploaded is not None:
                self._on_uploaded(MediaUpload(e.key, url, e.kind, e.ref))
        return health

    # ---- 容量:非 first_frame 超限淘汰(发告警,非静默) ----
    def _cap_cappable(self, now: float) -> list[dict]:
        cappable = [e for e in self._entries.values() if e.kind != _PROTECTED]
        if len(cappable) <= self.cfg.cappable_cap:
            return []
        cappable.sort(key=lambda e: (e.priority_rank, e.occurred_at))  # 最低优先+最旧先淘
        drop = cappable[0]
        self._entries.pop(drop.key, None)
        return [self._health(
            "media_dropped",
            f"cappable over cap {self.cfg.cappable_cap}, dropped {drop.key}", now)]

    # ---- 健康:积压 / 最旧年龄 ----
    def _backlog_health(self, now: float) -> list[dict]:
        pending = list(self._entries.values())
        oldest_age = max((now - e.enqueued_at for e in pending), default=0.0)
        over = (len(pending) > self.cfg.max_backlog
                or oldest_age > self.cfg.oldest_age_warn_s)
        if over and not self._backlog_reported:
            self._backlog_reported = True
            return [self._health(
                "media_backlog",
                f"{len(pending)} pending, oldest {round(oldest_age, 1)}s", now)]
        if not over:
            self._backlog_reported = False
        return []

    def _health(self, status: str, detail: str, ts: float) -> dict:
        return {"type": "media_uplink_health", "status": status,
                "detail": detail, "ts": round(ts, 3)}

    # ---- 只读 ----
    def state_of(self, key: str) -> str | None:
        if key in self._uploaded_keys:
            return MediaOutboxState.UPLOADED
        if key in self._failed_keys:
            return MediaOutboxState.FAILED
        e = self._entries.get(key)
        return e.state if e else None

    @property
    def pending_count(self) -> int:
        return len(self._entries)

    def pending_keys(self) -> list[str]:
        return list(self._entries.keys())

#!/usr/bin/env python3
"""四级运营分类器 —— 纯逻辑。person_observation → 运营语义叠加。ADR-0001 ⑥。

把视觉板的 `person_observation`(事实)结合缓存工单窗,给运营层一个**叠加分类**:
| 分类 | 触发 |
|---|---|
| `expected_presence`    | 缓存内有覆盖 occurred 的**有效**窗(带 version/as_of;**不证明身份**) |
| `unverified_presence`  | 授权上下文缺失/过期/不可访问 → **默认降级** |
| `suspected_intrusion`  | 窗口外出现 |

不变量(硬约束,写进测试):
  - **`confirmed_intrusion` 永不由本层产生**(只来自人工确认或被指定的独立安防系统)。
  - **不确定 → `unverified_presence`**,绝不编造 expected,绝不冒充分类。
  - **缓存过期/缺失 → `unverified_presence`**,不假装完成授权判断。
  - 分类是**运营叠加**,绝不改底层 person_observation 事实(输出独立事件,引用 event_id)。
"""
from __future__ import annotations

from datetime import datetime, timezone


class Presence:
    EXPECTED = "expected_presence"
    UNVERIFIED = "unverified_presence"
    SUSPECTED = "suspected_intrusion"


class PersonClassifier:
    def __init__(self, cache):
        self.cache = cache

    def classify(self, person_event: dict, now: float) -> dict:
        """person_event:person_observation dict(含 event_id, ts_start)。
        返回**独立的分类叠加事件**,不修改 person_event。"""
        event_id = person_event.get("event_id")
        occurred = person_event.get("ts_start", person_event.get("ts", now))
        status = self.cache.status(now)

        extra: dict = {}
        if status in ("empty", "expired"):
            level = Presence.UNVERIFIED                     # 诚实降级,不假装授权判断
            reason = f"auth_context_unavailable:{status}"
        else:
            win = self.cache.covering(occurred)
            if win is not None:
                level = Presence.EXPECTED
                reason = "within_workorder_window"
                extra = {"window_id": win.window_id,
                         "cache_version": self.cache.version,
                         "as_of_ts": self.cache.as_of_ts}    # 可能因平台撤销而 stale
            else:
                level = Presence.SUSPECTED                   # 窗口外出现(天花板,人工裁决升 confirmed)
                reason = "outside_workorder_window"
                extra = {"cache_version": self.cache.version,
                         "as_of_ts": self.cache.as_of_ts}

        ev = {
            "type": "presence_classification",
            "classification": level,
            "reason": reason,
            "person_observation_ref": event_id,             # 引用,不改底层事实
            "occurred_at": occurred,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        ev.update(extra)
        return ev

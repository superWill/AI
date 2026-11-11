#!/usr/bin/env python3
"""上行传输接口 + 离线 Fake —— 把 MQTT broker 隔在硬件外。真 paho-mqtt 留 P2c-b。

`UplinkTransport` 把「发一条包 / 收 ack 回执」抽象掉;DurableOutbox 只依赖它,不碰网络。
`FakeUplinkTransport` 可脚本化模拟:在线/断网、自动或手动回 custody/delivery ack、
平台按 msg_key 幂等去重(重复投递不重复接收)。
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class Inbound:
    """入站回执/更新。kind: custody_ack | delivery_ack | cache_update | connection。"""
    kind: str
    msg_key: str | None = None
    data: dict | None = None


class UplinkTransport(abc.ABC):
    @abc.abstractmethod
    def publish(self, envelope) -> str | None:
        """发一条包。返回本地句柄;断网/失败返回 None(上层据此存储转发重试)。"""

    @abc.abstractmethod
    def poll(self) -> list[Inbound]:
        """拉入站回执(custody_ack/delivery_ack/…)。"""


class FakeUplinkTransport(UplinkTransport):
    """离线传输桩。平台按 msg_key 幂等去重。"""

    def __init__(self, online: bool = True,
                 auto_custody: bool = False, auto_delivery: bool = False):
        self.online = online
        self.auto_custody = auto_custody
        self.auto_delivery = auto_delivery
        self._published: list = []            # 每次 publish 尝试(含重复)
        self._received: set[str] = set()       # 平台已收 msg_key(幂等去重)
        self._inbox: list[Inbound] = []

    def publish(self, envelope) -> str | None:
        if not self.online:
            return None
        self._published.append(envelope)
        first = envelope.msg_key not in self._received   # 幂等:重复投递只首次“接收”
        self._received.add(envelope.msg_key)
        if first and self.auto_custody:
            self._inbox.append(Inbound("custody_ack", envelope.msg_key))
        if first and self.auto_delivery:
            self._inbox.append(Inbound("delivery_ack", envelope.msg_key))
        return f"msg-{len(self._published)}"

    def poll(self) -> list[Inbound]:
        out, self._inbox = self._inbox, []
        return out

    # ---- 测试/联调驱动 ----
    def feed_custody_ack(self, msg_key: str) -> None:
        self._inbox.append(Inbound("custody_ack", msg_key))

    def feed_delivery_ack(self, msg_key: str) -> None:
        self._inbox.append(Inbound("delivery_ack", msg_key))

    def set_online(self, online: bool) -> None:
        self.online = online

    @property
    def publish_attempts(self) -> int:
        return len(self._published)

    @property
    def unique_received(self) -> set[str]:
        return set(self._received)

#!/usr/bin/env python3
"""报警触发源 —— 抽象"烟感响了"这个事件。纯逻辑,注入时钟可测。

RK3506 侧真实源:DI/GPIO 干接点、Modbus 寄存器、LoRa 上报(见 lora 接入)。
本模块给抽象 + 两个 MVP 可用实现:
- FakeAlarmSource:脚本化 fire(),供单测/仿真。
- FileAlarmSource:触发文件出现即报警(`touch <file>` 模拟烟感),板上手动验证方便,真硬件替换它。
"""
from __future__ import annotations

import abc
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AlarmEvent:
    source_id: str                 # 哪个烟感
    occurred_at: float             # 报警发生时间(原始,补投永不冒充)
    kind: str = "smoke"


class AlarmSource(abc.ABC):
    @abc.abstractmethod
    def poll(self, now: float) -> list[AlarmEvent]:
        """返回自上次 poll 以来的新报警事件(去抖/边沿由实现负责)。"""


class FakeAlarmSource(AlarmSource):
    """脚本化:fire() 排入一个报警,poll() 取走。供测试/仿真。"""

    def __init__(self, source_id: str = "smoke-1"):
        self.source_id = source_id
        self._pending: list[AlarmEvent] = []

    def fire(self, now: float, kind: str = "smoke") -> None:
        self._pending.append(AlarmEvent(self.source_id, now, kind))

    def poll(self, now: float) -> list[AlarmEvent]:
        out, self._pending = self._pending, []
        return out


class FileAlarmSource(AlarmSource):
    """触发文件存在即报警一次(边沿:处理后删文件)。`touch <path>` 模拟烟感,真硬件替换本类。"""

    def __init__(self, trigger_path: str, source_id: str = "smoke-1"):
        self.trigger_path = trigger_path
        self.source_id = source_id

    def poll(self, now: float) -> list[AlarmEvent]:
        if not os.path.exists(self.trigger_path):
            return []
        try:
            os.remove(self.trigger_path)           # 边沿:消费后删,避免重复触发
        except FileNotFoundError:
            return []
        return [AlarmEvent(self.source_id, now, "smoke")]

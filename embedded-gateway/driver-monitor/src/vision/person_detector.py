#!/usr/bin/env python3
"""人体检测器接口 + 离线 Mock。真 RKNN 实现(yolov5n/yolov8n 量化)留 P1b。

视觉安防 P1:P0 的 motion episode 只说「画面在动」,这里回答「动的是不是人」。
接口与后端解耦——`detect(rgb) -> [PersonBox]`;上层(confirm)只吃框,不关心是 RKNN 还是 Mock。

不变量(ADR-0001 ⑥):本层只产**人体检测框(事实)**,不产 person_present 长状态、不产 intrusion。
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class PersonBox:
    """一个人体检测框,像素坐标 + 置信度。"""
    x1: float
    y1: float
    x2: float
    y2: float
    score: float = 1.0

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


class PersonDetector(abc.ABC):
    """人体检测后端接口。detect 吃一帧 RGB,吐 0..N 个 PersonBox。"""

    @abc.abstractmethod
    def detect(self, rgb) -> list[PersonBox]:
        ...


class MockPersonDetector(PersonDetector):
    """离线 Mock:按预定脚本逐帧吐框,忽略像素。用于离线联调/回归。

    schedule:list[list[PersonBox]],第 i 次 detect() 返回 schedule[i];耗尽后返回 default。
    default:脚本用完后的兜底(默认空)。
    """

    def __init__(self, schedule: list[list[PersonBox]] | None = None,
                 default: list[PersonBox] | None = None):
        self._schedule = list(schedule or [])
        self._default = list(default or [])
        self._i = 0

    def detect(self, rgb) -> list[PersonBox]:
        if self._i < len(self._schedule):
            boxes = self._schedule[self._i]
            self._i += 1
            return list(boxes)
        return list(self._default)

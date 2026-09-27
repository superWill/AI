#!/usr/bin/env python3
"""视觉分析接口 + RKNN 留桩 —— 把"看懂画面"抽象成 agent 可调的一步。

RK3506 无 NPU:拍得到、看不懂;理解这步放 RK3568(本板 NPU/RKNN)或云 VLM。
本模块只定契约 + 留桩,接入真模型时只换实现,service 不动:
  - StubVisionAnalyzer:恒返回 not_implemented(明确不静默假装有结果)。
  - RknnVisionAnalyzer:接真 RKNN 的骨架(载模型/跑推理待填),未载模型也返回 not_implemented。
纯标准库;VisionResult 可 JSON 序列化,供值守 agent 消费 / 并入告警。
"""
from __future__ import annotations

import abc
from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class Detection:
    """单个检测框。bbox 坐标口径(归一化 vs 像素)接模型时定。"""
    label: str
    score: float
    bbox: list = field(default_factory=list)        # [x1,y1,x2,y2]


@dataclass(frozen=True)
class VisionResult:
    """结构化视觉结论。status 明确区分"未接入"与"真结果",不含糊。"""
    status: str                                      # "ok" | "not_implemented" | "error"
    model: str = ""
    detections: list = field(default_factory=list)  # list[Detection] 或 list[dict]
    summary: str = ""
    ref: object = None

    def to_dict(self) -> dict:
        return asdict(self)


class VisionAnalyzer(abc.ABC):
    model = "abstract"

    @abc.abstractmethod
    def analyze(self, jpeg: bytes, *, ref=None) -> VisionResult:
        """输入一帧 JPEG,返回结构化视觉结论。"""


class StubVisionAnalyzer(VisionAnalyzer):
    """留桩:不推理,恒返回 not_implemented。RKNN 未接入时占位,让契约先跑通。"""
    model = "stub"

    def analyze(self, jpeg: bytes, *, ref=None) -> VisionResult:
        return VisionResult(
            status="not_implemented", model=self.model, detections=[],
            summary="RKNN 视觉推理未接入(留桩);拍/传已通,理解待接模型", ref=ref)


class RknnVisionAnalyzer(VisionAnalyzer):
    """接真 RKNN 模型的骨架。当前不载模型(_ready=False)→返回 not_implemented,不假装有结果。

    接入步骤(留给后续):
      1. 预置 rknn-toolkit-lite2 runtime(板上 RKNPU/RKNN 已确认在);
      2. __init__ 载 .rknn 模型 + labels,置 _ready=True;
      3. analyze:JPEG →(MPP/RGA 解码+缩放)→ RKNN infer → 后处理 → Detection 列表。
    检测目标(烟雾/火焰/跑冒滴漏/液位…)选定后再填,service/契约不变。
    """
    model = "rknn"

    def __init__(self, model_path: str, labels=None):
        self.model_path = model_path
        self.labels = list(labels or [])
        self._ready = False                          # 载模型成功后置 True;当前留桩
        self._rt = None

    def analyze(self, jpeg: bytes, *, ref=None) -> VisionResult:
        if not self._ready:
            return VisionResult(
                status="not_implemented", model=self.model, detections=[],
                summary=f"RKNN 模型未加载(骨架): {self.model_path}", ref=ref)
        raise NotImplementedError("RKNN 推理待接入")   # _ready=True 但没实现 → 显式报错,不静默

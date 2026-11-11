#!/usr/bin/env python3
"""人脸疲劳视觉管线:全帧 → RetinaFace 检测 → 人脸 ROI → PFLD98 → EAR/MAR。

把两个 rknn 串起来,处理两套分辨率与坐标映射:
  - RetinaFace 在 320 letterbox 上检测,框映射回全帧。
  - 从全帧裁人脸 ROI,resize 112 喂 PFLD;98 点在 ROI 内,需要时映射回全帧用于叠图。
EAR/MAR 是比值,在 ROI(112)空间直接算,scale 无关。
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from vision.retinaface import RetinaFaceRKNN
from vision.pfld import PFLDLandmarkRKNN, features_from_pfld
from util.imgproc import letterbox, crop_with_margin, resize_bilinear


class FacePipeline:
    def __init__(self, retina_path: str, pfld_path: str, *, det_size: int = 320,
                 pfld_size: int = 112, margin: float = 0.25):
        self.det = RetinaFaceRKNN(retina_path, model_size=(det_size, det_size))
        self.pfld = PFLDLandmarkRKNN(pfld_path, size=pfld_size)
        self.det_size = det_size
        self.pfld_size = pfld_size
        self.margin = margin

    def process(self, full_rgb: np.ndarray) -> Optional[dict]:
        """全帧 RGB → {box, score, landmarks98(全帧坐标), ear, mar} 或 None(无脸)。"""
        lb, scale, padx, pady = letterbox(full_rgb, self.det_size)
        face = self.det.infer(lb)
        if face is None:
            return None
        # 框:320 letterbox → 全帧
        bx = face["box"]
        x1 = (bx[0] - padx) / scale; y1 = (bx[1] - pady) / scale
        x2 = (bx[2] - padx) / scale; y2 = (bx[3] - pady) / scale
        box_full = [x1, y1, x2, y2]

        crop, ox, oy, _, _ = crop_with_margin(full_rgb, box_full, self.margin)
        if crop.size == 0 or crop.shape[0] < 8 or crop.shape[1] < 8:
            return None
        ch, cw = crop.shape[:2]
        face112 = resize_bilinear(crop, self.pfld_size, self.pfld_size)
        lm = self.pfld.infer(face112)                       # (98,2) in 112 space
        feats = features_from_pfld(lm)                      # EAR/MAR 在 112 空间算

        # 98 点 → 全帧坐标(叠图/调试用)
        lm_full = np.empty_like(lm)
        lm_full[:, 0] = ox + lm[:, 0] * (cw / self.pfld_size)
        lm_full[:, 1] = oy + lm[:, 1] * (ch / self.pfld_size)

        return {"box": box_full, "score": face["score"],
                "landmarks98": lm_full, "landmarks98_roi": lm,
                "ear": feats["ear"], "mar": feats["mar"]}

    def release(self) -> None:
        self.det.release()
        self.pfld.release()

#!/usr/bin/env python3
"""yolov8n 人体检测后处理(DFL 解码 + person-only 过滤 + NMS)单测——纯 numpy,不需要 rknnlite/板子。"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from vision.yolov8_person import decode_person_boxes, DFL_BINS, STRIDES, PERSON_CLASS_ID  # noqa: E402


def _one_hot_dfl_logits(dist_left, dist_top, dist_right, dist_bottom, h, w, row, col):
    """构造 DFL box 张量(1,64,h,w),让 (row,col) 格子四边 softmax 期望值精确等于给定整数 bin。"""
    box = np.full((1, 4 * DFL_BINS, h, w), -20.0, dtype=np.float32)   # 极负 → softmax≈0
    for k, d in enumerate((dist_left, dist_top, dist_right, dist_bottom)):
        box[0, k * DFL_BINS + d, row, col] = 20.0                     # one-hot 峰值 → softmax≈1
    return box


def _branch(h, w, row, col, dist, person_score, other_score=0.0):
    box = _one_hot_dfl_logits(*dist, h, w, row, col)
    cls = np.zeros((1, 80, h, w), dtype=np.float32)                    # 背景格子全 0,只填目标格子
    cls[0, :, row, col] = other_score
    cls[0, PERSON_CLASS_ID, row, col] = person_score
    score_sum = np.ones((1, 1, h, w), dtype=np.float32)                # decode 忽略此张量
    return box, cls, score_sum


def _synthetic_outputs(peak_branch_idx, row, col, dist, person_score, other_score=0.0):
    """3 个 branch,grid 依次 4x4/2x2/1x1(H*W 严格递减,配 decode 里按 size 排序的假设)。
    只在 peak_branch_idx 那个 branch 的 (row,col) 放峰值,其余全 0 分(过滤掉)。"""
    grids = [(4, 4), (2, 2), (1, 1)]
    outputs = []
    for i, (h, w) in enumerate(grids):
        if i == peak_branch_idx:
            box, cls, ss = _branch(h, w, row, col, dist, person_score, other_score)
        else:
            box, cls, ss = _branch(h, w, 0, 0, (0, 0, 0, 0), 0.0, 0.0)
        outputs.extend([box, cls, ss])
    return outputs


def test_decode_finds_single_person_box_at_expected_location():
    # stride=8 branch,格子 (row=1,col=1),四边 dist 都是 2 bin。
    outputs = _synthetic_outputs(peak_branch_idx=0, row=1, col=1, dist=(2, 2, 2, 2), person_score=0.9)
    dets = decode_person_boxes(outputs, model_size=(32, 32), conf_thresh=0.25, nms_thresh=0.45)
    assert dets.shape == (1, 5)
    stride = STRIDES[0]
    grid_cx, grid_cy = 1, 1
    x1 = (grid_cx + 0.5 - 2) * stride
    y1 = (grid_cy + 0.5 - 2) * stride
    x2 = (grid_cx + 0.5 + 2) * stride
    y2 = (grid_cy + 0.5 + 2) * stride
    assert np.allclose(dets[0, :4], [x1, y1, x2, y2], atol=1e-2)
    assert dets[0, 4] > 0.8


def test_decode_below_threshold_returns_empty():
    outputs = _synthetic_outputs(peak_branch_idx=0, row=0, col=0, dist=(1, 1, 1, 1), person_score=0.1)
    dets = decode_person_boxes(outputs, model_size=(32, 32), conf_thresh=0.25, nms_thresh=0.45)
    assert dets.shape == (0, 5)


def test_decode_ignores_non_person_class_confidence():
    # person 通道低分,其它 79 类通道全部高分——不应该被当成检测。
    outputs = _synthetic_outputs(peak_branch_idx=1, row=0, col=0, dist=(1, 1, 1, 1),
                                  person_score=0.05, other_score=0.95)
    dets = decode_person_boxes(outputs, model_size=(32, 32), conf_thresh=0.25, nms_thresh=0.45)
    assert dets.shape == (0, 5)


def test_decode_picks_higher_score_branch():
    outputs = _synthetic_outputs(peak_branch_idx=2, row=0, col=0, dist=(3, 3, 3, 3), person_score=0.6)
    dets = decode_person_boxes(outputs, model_size=(32, 32), conf_thresh=0.25, nms_thresh=0.45)
    assert dets.shape == (1, 5)
    assert dets[0, 4] > 0.5


if __name__ == "__main__":
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)} passed")

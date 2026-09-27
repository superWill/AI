#!/usr/bin/env python3
"""ROI 掩膜单测(纯标准库;to_bitmap 段需 numpy,无则 skip)。"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "src"))

from roi.mask import RoiMask                                   # noqa: E402
from vision.person_detector import PersonBox                   # noqa: E402


# 一个居中方形 ROI:(100,100)-(300,300)
SQUARE = [(100, 100), (300, 100), (300, 300), (100, 300)]


def test_empty_polygon_is_whole_frame():
    m = RoiMask()
    assert not m.enabled
    assert m.contains_point(0, 0) and m.contains_point(9999, 9999)
    boxes = [PersonBox(0, 0, 10, 10)]
    assert m.filter_boxes(boxes) == boxes           # 不过滤


def test_point_inside_outside():
    m = RoiMask(SQUARE)
    assert m.enabled
    assert m.contains_point(200, 200)               # 正中
    assert not m.contains_point(50, 200)            # 左外
    assert not m.contains_point(200, 400)           # 下外


def test_box_center_in_roi_kept_outside_dropped():
    m = RoiMask(SQUARE)
    inside = PersonBox(180, 180, 220, 260, 0.9)     # 中心 (200,220) 内
    outside = PersonBox(0, 0, 40, 40, 0.9)          # 中心 (20,20) 外
    kept = m.filter_boxes([inside, outside])
    assert kept == [inside]


def test_polygon_needs_three_points():
    try:
        RoiMask([(0, 0), (1, 1)])
        assert False, "应拒绝 <3 点多边形"
    except ValueError:
        pass


def test_from_dict():
    m = RoiMask.from_dict({"polygon": [[100, 100], [300, 100], [200, 300]]})
    assert m.enabled and len(m.polygon) == 3


def test_to_bitmap_numpy_optional():
    try:
        import numpy as np
    except ImportError:
        print("  skip to_bitmap(无 numpy)")
        return
    m = RoiMask(SQUARE)
    bm = m.to_bitmap(400, 400)
    assert bm.shape == (400, 400) and bm.dtype == np.bool_
    assert bm[200, 200] and not bm[10, 10]          # 区内/区外
    # 空多边形 → 全 True
    assert RoiMask().to_bitmap(20, 20).all()


def test_to_bitmap_matches_scalar_on_nonsquare_concave():
    """非方形尺寸 + 凹多边形(L 形):向量化 to_bitmap 须逐像素等于标量 contains_point。
    非方形 (h≠w) 能抓住 w/h 转置;凹形能抓住射线法水平/垂直边的漏判。"""
    try:
        import numpy as np
    except ImportError:
        print("  skip to_bitmap parity(无 numpy)")
        return
    L_SHAPE = [(2, 2), (12, 2), (12, 6), (6, 6), (6, 14), (2, 14)]   # 凹 L
    m = RoiMask(L_SHAPE)
    h, w = 18, 14                                    # 非方形,故意 h≠w
    bm = m.to_bitmap(w, h)
    assert bm.shape == (h, w)
    mism = [(x, y) for y in range(h) for x in range(w)
            if bool(bm[y, x]) != m.contains_point(x + 0.5, y + 0.5)]
    assert not mism, f"向量化与标量不一致于 {mism[:5]}"


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); n += 1; print(f"  ok  {name}")
    print(f"\n{n} passed")

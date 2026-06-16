#!/usr/bin/env python3
"""donateacry 天花板探测实验（严格按婴儿 uuid 组切分，杜绝同婴儿泄漏）。

实验 B: hungry vs rest 二分类   -> ROC AUC / balanced acc
实验 C: hungry/tired/discomfort 三分类 -> 混淆矩阵 / per-class F1
对照: 多数类基线。模型: 标准化 + 逻辑回归(class_weight=balanced)。
"""
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMB = os.path.join(ROOT, "data", "work", "embeddings.npz")


def run_cv(X, y, groups, name, n_splits=5):
    print(f"\n{'=' * 60}\n实验: {name}  (StratifiedGroupKFold {n_splits} 折, 按 uuid 分组)")
    classes = np.unique(y)
    oof_pred = np.empty(len(y), dtype=object)
    oof_prob = np.zeros((len(y), len(classes)))
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=42)
    for tr, te in skf.split(X, y, groups):
        clf = make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=5000, C=0.1),
        )
        clf.fit(X[tr], y[tr])
        oof_pred[te] = clf.predict(X[te])
        oof_prob[te] = clf.predict_proba(X[te])

    oof_pred = oof_pred.astype(str)
    bacc = balanced_accuracy_score(y, oof_pred)
    macro_f1 = f1_score(y, oof_pred, average="macro")
    majority = max(np.bincount(np.searchsorted(classes, y))) / len(y)
    print(f"balanced acc = {bacc:.3f} | macro F1 = {macro_f1:.3f} | 多数类基线 acc = {majority:.3f}")
    if len(classes) == 2:
        pos = classes[1]
        auc = roc_auc_score((y == pos).astype(int), oof_prob[:, 1])
        print(f"ROC AUC ({pos}) = {auc:.3f}")
    print("\n混淆矩阵 (行=真值, 列=预测):", classes.tolist())
    print(confusion_matrix(y, oof_pred, labels=classes))
    print(classification_report(y, oof_pred, labels=classes, digits=3, zero_division=0))
    return bacc, macro_f1


def main() -> None:
    d = np.load(EMB, allow_pickle=False)
    X, labels, uuids = d["X_mean"], d["labels"], d["uuids"]
    print(f"样本 {len(labels)} 条, 维度 {X.shape[1]}, 独立婴儿(uuid) {len(set(uuids.tolist()))}")
    print(f"零样本 YAMNet 哭声分数: 中位数 {np.median(d['cry_score']):.3f}, "
          f">0.5 占比 {(d['cry_score'] > 0.5).mean():.1%}  (验证这些片段确实是哭声)")

    # 实验 B: hungry vs rest
    y_bin = np.where(labels == "hungry", "hungry", "rest")
    run_cv(X, y_bin, uuids, "B) hungry vs rest")

    # 实验 C: 三分类(样本量>20 的类)
    keep = np.isin(labels, ["hungry", "tired", "discomfort"])
    run_cv(X[keep], labels[keep], uuids[keep], "C) hungry/tired/discomfort 三分类")


if __name__ == "__main__":
    main()

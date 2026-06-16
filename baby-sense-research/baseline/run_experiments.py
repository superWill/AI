#!/usr/bin/env python3
"""一键跑全部 baseline 实验(MFCC + 逻辑回归, 严格组切分)。

A) L1 哭声检测: donateacry 哭声 vs ESC-50 环境音
B) L3 hungry vs rest 二分类
C) L3 hungry/tired/discomfort 三分类
所有实验按"婴儿/录音来源"组切分, 杜绝同源泄漏。
"""
import csv
import glob
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score, roc_auc_score)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from features import feature_vector
from metrics import l1_cv, print_l1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MANIFEST = os.path.join(DATA, "work", "manifest.csv")
ESC = os.path.join(DATA, "ESC-50-master")
CACHE = os.path.join(DATA, "work", "feats_mfcc.npz")


def build_features():
    if os.path.exists(CACHE):
        d = np.load(CACHE, allow_pickle=True)
        return {k: d[k] for k in d.files}

    # donateacry
    rows = list(csv.DictReader(open(MANIFEST)))
    cry_X, cry_label, cry_uuid = [], [], []
    for i, r in enumerate(rows):
        cry_X.append(feature_vector(os.path.join(DATA, r["path"])))
        cry_label.append(r["label"])
        cry_uuid.append(r["uuid"])
        if (i + 1) % 100 == 0:
            print(f"  donateacry {i + 1}/{len(rows)}")

    # ESC-50
    meta = list(csv.DictReader(open(os.path.join(ESC, "meta", "esc50.csv"))))
    esc_X, esc_cat, esc_fold = [], [], []
    for i, m in enumerate(meta):
        esc_X.append(feature_vector(os.path.join(ESC, "audio", m["filename"])))
        esc_cat.append(m["category"])
        esc_fold.append(m["fold"])
        if (i + 1) % 500 == 0:
            print(f"  esc {i + 1}/{len(meta)}")

    out = dict(
        cry_X=np.array(cry_X), cry_label=np.array(cry_label), cry_uuid=np.array(cry_uuid),
        esc_X=np.array(esc_X), esc_cat=np.array(esc_cat), esc_fold=np.array(esc_fold),
    )
    np.savez(CACHE, **out)
    print(f"特征已缓存 -> {CACHE}")
    return out


def cv(X, y, groups, n_splits=5):
    classes = np.unique(y)
    pred = np.empty(len(y), dtype=object)
    prob = np.zeros((len(y), len(classes)))
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=42)
    for tr, te in skf.split(X, y, groups):
        clf = make_pipeline(StandardScaler(),
                            LogisticRegression(class_weight="balanced", max_iter=5000, C=0.5))
        clf.fit(X[tr], y[tr])
        pred[te] = clf.predict(X[te])
        prob[te] = clf.predict_proba(X[te])
    return classes, pred.astype(str), prob


def report(name, y, classes, pred, prob):
    print(f"\n{'=' * 64}\n{name}")
    bacc = balanced_accuracy_score(y, pred)
    mf1 = f1_score(y, pred, average="macro")
    maj = np.bincount(np.searchsorted(classes, y)).max() / len(y)
    line = f"balanced_acc={bacc:.3f}  macro_F1={mf1:.3f}  多数类基线={maj:.3f}"
    if len(classes) == 2:
        pos = 1
        auc = roc_auc_score((y == classes[pos]).astype(int), prob[:, pos])
        line += f"  ROC_AUC={auc:.3f}"
    print(line)
    print("混淆矩阵 行=真值 列=预测:", classes.tolist())
    print(confusion_matrix(y, pred, labels=classes))
    print(classification_report(y, pred, labels=classes, digits=3, zero_division=0))


def main():
    f = build_features()
    cry_X, labels, uuids = f["cry_X"], f["cry_label"], f["cry_uuid"]
    print(f"\ndonateacry {len(labels)} 条, 维度 {cry_X.shape[1]}, "
          f"独立婴儿 {len(set(uuids.tolist()))}")

    # A) L1 哭声 vs 环境音（按折评估 + 修正的低误报召回）
    X = np.concatenate([cry_X, f["esc_X"]])
    esc_pos = (f["esc_cat"] == "crying_baby").astype(int)
    y = np.concatenate([np.ones(len(cry_X), int), esc_pos])
    groups = np.concatenate([uuids, np.char.add("esc_", f["esc_fold"].astype(str))])
    print_l1("A) L1 哭声检测 [MFCC]: donateacry+ESC婴儿哭 vs 49类环境音",
             l1_cv(X, y, groups))

    # B) hungry vs rest
    yb = np.where(labels == "hungry", "hungry", "rest")
    cls, pred, prob = cv(cry_X, yb, uuids)
    report("B) L3 hungry vs rest (二分类)", yb, cls, pred, prob)

    # C) 三分类
    keep = np.isin(labels, ["hungry", "tired", "discomfort"])
    cls, pred, prob = cv(cry_X[keep], labels[keep], uuids[keep])
    report("C) L3 hungry/tired/discomfort (三分类)", labels[keep], cls, pred, prob)


if __name__ == "__main__":
    main()

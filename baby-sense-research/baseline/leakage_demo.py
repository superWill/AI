#!/usr/bin/env python3
"""泄漏对照: 证明文献高分多来自"同一婴儿跨训练/测试集"的信息泄漏。

同一份数据、同一模型, 只改交叉验证的切分方式:
  - 随机分层(StratifiedKFold):     同一婴儿的多条哭声可同时进训练和测试 -> 虚高
  - 按婴儿分组(StratifiedGroupKFold): 测试婴儿训练时完全没见过 -> 真实泛化
两者差距 = 泄漏带来的"假准确率"。
"""
import os

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, f1_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "data", "work", "feats_mfcc.npz")


def evaluate(X, y, groups, splitter, use_groups):
    pred = np.empty(len(y), dtype=object)
    args = (X, y, groups) if use_groups else (X, y)
    for tr, te in splitter.split(*args):
        clf = make_pipeline(StandardScaler(),
                            LogisticRegression(class_weight="balanced", max_iter=5000, C=0.5))
        clf.fit(X[tr], y[tr])
        pred[te] = clf.predict(X[te])
    pred = pred.astype(str)
    return balanced_accuracy_score(y, pred), f1_score(y, pred, average="macro")


def main():
    d = np.load(CACHE, allow_pickle=True)
    X, labels, uuids = d["cry_X"], d["cry_label"], d["cry_uuid"]
    keep = np.isin(labels, ["hungry", "tired", "discomfort"])
    X, y, g = X[keep], labels[keep], uuids[keep]
    n_baby = len(set(g.tolist()))
    print(f"三分类样本 {len(y)} 条, 来自 {n_baby} 个婴儿, chance balanced_acc=0.333\n")

    rand = StratifiedKFold(5, shuffle=True, random_state=42)
    grp = StratifiedGroupKFold(5, shuffle=True, random_state=42)
    bacc_r, f1_r = evaluate(X, y, g, rand, False)
    bacc_g, f1_g = evaluate(X, y, g, grp, True)

    print(f"{'切分方式':<28}{'balanced_acc':>14}{'macro_F1':>12}")
    print(f"{'随机分层(有泄漏, 似文献)':<24}{bacc_r:>14.3f}{f1_r:>12.3f}")
    print(f"{'按婴儿分组(无泄漏, 真实)':<24}{bacc_g:>14.3f}{f1_g:>12.3f}")
    print(f"\n泄漏虚高: balanced_acc +{bacc_r - bacc_g:.3f}, macro_F1 +{f1_r - f1_g:.3f}")
    print("结论: 随机切分的分数主要来自'认出是同一个宝宝',而非'听懂需求'。")


if __name__ == "__main__":
    main()

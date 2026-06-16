#!/usr/bin/env python3
"""评估工具：低误报区间的召回计算（修正乐观偏差）。

关键修正：
  "recall @ FPR ≤ target" 的产品语义是——在不突破误报预算的前提下能达到的最高召回。
  正确值 = 满足 fpr ≤ target 的所有工作点中 tpr 的最大值
        = 最大的 fpr ≤ target 处的 tpr   (np.searchsorted(..., side='right') - 1)

  旧代码用 searchsorted(fpr, target)(side='left') 取"第一个 fpr ≥ target 的点"，
  该点 fpr 往往 > target（已突破预算），导致召回被高估。

此外按折分别计算再报 mean±std：
  - 避免把各折(各自独立标准化+LR)的概率池化后算单条 ROC 带来的校准不一致；
  - 暴露方差——对"夜间少误报"判断，方差比单点值更重要。
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def recall_at_fpr(y_true, score, target_fpr: float) -> float:
    """保守：满足 fpr ≤ target_fpr 的最高召回（不突破误报预算）。"""
    fpr, tpr, _ = roc_curve(y_true, score)
    idx = np.searchsorted(fpr, target_fpr, side="right") - 1
    return 0.0 if idx < 0 else float(tpr[idx])


def recall_at_fpr_optimistic(y_true, score, target_fpr: float) -> float:
    """旧(乐观)算法，仅用于对照展示：第一个 fpr ≥ target 的点，可能已突破预算。"""
    fpr, tpr, _ = roc_curve(y_true, score)
    idx = int(np.searchsorted(fpr, target_fpr, side="left"))
    idx = min(idx, len(tpr) - 1)
    return float(tpr[idx])


def make_clf():
    return make_pipeline(
        StandardScaler(),
        LogisticRegression(class_weight="balanced", max_iter=5000, C=0.5),
    )


def l1_cv(X, y, groups, n_splits=5, targets=(0.01, 0.05), random_state=42):
    """L1 二分类按折评估。返回 pooled AUC 与每折 AUC / recall@fpr 的 mean,std。"""
    y = np.asarray(y, dtype=int)
    skf = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    oof = np.full(len(y), np.nan)
    fold_auc = []
    fold_recall = {t: [] for t in targets}
    fold_recall_opt = {t: [] for t in targets}
    for tr, te in skf.split(X, y, groups):
        clf = make_clf()
        clf.fit(X[tr], y[tr])
        p = clf.predict_proba(X[te])[:, 1]
        oof[te] = p
        fold_auc.append(roc_auc_score(y[te], p))
        for t in targets:
            fold_recall[t].append(recall_at_fpr(y[te], p, t))
            fold_recall_opt[t].append(recall_at_fpr_optimistic(y[te], p, t))
    return {
        "pooled_auc": float(roc_auc_score(y, oof)),
        "fold_auc": (float(np.mean(fold_auc)), float(np.std(fold_auc))),
        "recall": {t: (float(np.mean(fold_recall[t])), float(np.std(fold_recall[t]))) for t in targets},
        "recall_optimistic": {t: float(np.mean(fold_recall_opt[t])) for t in targets},
        "oof": oof,
    }


def print_l1(name: str, r: dict, targets=(0.01, 0.05)) -> None:
    print(f"\n{'=' * 64}\n{name}")
    print(f"AUC: pooled={r['pooled_auc']:.4f}  每折={r['fold_auc'][0]:.4f}±{r['fold_auc'][1]:.4f}")
    for t in targets:
        m, s = r["recall"][t]
        opt = r["recall_optimistic"][t]
        print(f"召回@FPR{int(t*100)}% (修正,保守) = {m:.3f}±{s:.3f}   "
              f"[旧乐观算法={opt:.3f}, 差 {opt - m:+.3f}]")

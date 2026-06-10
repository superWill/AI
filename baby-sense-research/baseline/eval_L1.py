#!/usr/bin/env python3
"""实验 A — L1 哭声检测基准: donateacry 哭声 vs ESC-50 环境音。

两条线:
  1) 零样本: 直接用 YAMNet 的 Baby cry/Crying/Whimper 类分数当检测器(不训练)
  2) 训练:   YAMNet embedding + 逻辑回归
组切分: 哭声按婴儿 uuid, ESC-50 按官方 fold, 杜绝泄漏。
输出 AUC 与低误报区间的召回(对应"整夜少误报"的产品验收口径)。
"""
import csv
import glob
import os
import subprocess

import numpy as np
import soundfile as sf
import tensorflow as tf
import tensorflow_hub as hub
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ESC = os.path.join(DATA, "ESC-50-master")
ESC16K = os.path.join(DATA, "work", "esc16k")
CRY_EMB = os.path.join(DATA, "work", "embeddings.npz")
OUT = os.path.join(DATA, "work", "esc_embeddings.npz")

CRY_CLASSES = {"Baby cry, infant cry", "Crying, sobbing", "Whimper"}


def transcode_esc() -> list[dict]:
    meta = list(csv.DictReader(open(os.path.join(ESC, "meta", "esc50.csv"))))
    os.makedirs(ESC16K, exist_ok=True)
    for r in meta:
        dst = os.path.join(ESC16K, r["filename"])
        if not os.path.exists(dst):
            subprocess.run(
                ["ffmpeg", "-v", "error", "-y", "-i",
                 os.path.join(ESC, "audio", r["filename"]),
                 "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", dst],
                check=True, capture_output=True)
    return meta


def extract(meta: list[dict]) -> None:
    if os.path.exists(OUT):
        return
    model = hub.load("https://tfhub.dev/google/yamnet/1")
    names = [r["display_name"]
             for r in csv.DictReader(tf.io.gfile.GFile(model.class_map_path().numpy()))]
    cry_idx = [i for i, n in enumerate(names) if n in CRY_CLASSES]
    X, score = [], []
    for i, r in enumerate(meta):
        wav, sr = sf.read(os.path.join(ESC16K, r["filename"]), dtype="float32")
        s, e, _ = model(wav)
        X.append(e.numpy().mean(axis=0))
        score.append(float(s.numpy()[:, cry_idx].max()))
        if (i + 1) % 400 == 0:
            print(f"  esc {i + 1}/{len(meta)}")
    np.savez(OUT, X=np.array(X), cry_score=np.array(score),
             category=np.array([r["category"] for r in meta]),
             fold=np.array([r["fold"] for r in meta]))


def main() -> None:
    meta = transcode_esc()
    extract(meta)
    esc = np.load(OUT)
    cry = np.load(CRY_EMB)

    # 正样本: donateacry 全部 + ESC crying_baby; 负样本: 其余 49 类
    esc_pos = esc["category"] == "crying_baby"
    X = np.concatenate([cry["X_mean"], esc["X"]])
    y = np.concatenate([np.ones(len(cry["X_mean"])), esc_pos.astype(float)])
    zs = np.concatenate([cry["cry_score"], esc["cry_score"]])
    groups = np.concatenate([cry["uuids"],
                             np.char.add("escfold_", esc["fold"].astype(str))])

    auc_zs = roc_auc_score(y, zs)
    fpr, tpr, _ = roc_curve(y, zs)
    print(f"\n[零样本 YAMNet] AUC = {auc_zs:.4f} | "
          f"召回@FPR1% = {tpr[np.searchsorted(fpr, 0.01)]:.3f} | "
          f"召回@FPR5% = {tpr[np.searchsorted(fpr, 0.05)]:.3f}")

    oof = np.zeros(len(y))
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    for tr, te in skf.split(X, y, groups):
        clf = make_pipeline(StandardScaler(),
                            LogisticRegression(class_weight="balanced",
                                               max_iter=5000, C=0.1))
        clf.fit(X[tr], y[tr])
        oof[te] = clf.predict_proba(X[te])[:, 1]
    auc = roc_auc_score(y, oof)
    fpr, tpr, _ = roc_curve(y, oof)
    print(f"[训练 logreg ] AUC = {auc:.4f} | "
          f"召回@FPR1% = {tpr[np.searchsorted(fpr, 0.01)]:.3f} | "
          f"召回@FPR5% = {tpr[np.searchsorted(fpr, 0.05)]:.3f}")


if __name__ == "__main__":
    main()

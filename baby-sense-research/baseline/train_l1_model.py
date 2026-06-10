#!/usr/bin/env python3
"""L1 哭声检测——产品级训练（可导出端侧）。

与 baseline 探针(sklearn logreg)的区别：这里训 Keras 小头，可导出 TFLite/CoreML。
结构：YAMNet(冻结) 输出的 1024 维 embedding → Dense(64,relu) → Dropout → Dense(1,sigmoid)

流程：
  1) 读缓存 embedding（哭声 + ESC-50 环境音）
  2) 按婴儿/ESC-fold 组切分留出测试集（杜绝泄漏）
  3) class_weight 平衡，训练 Keras 头
  4) 评估 AUC + 保守口径低误报召回
  5) 保存 SavedModel + 导出 TFLite（端侧分类头）

前置：已跑过 extract_embeddings.py 与 eval_L1.py(生成 esc_embeddings.npz)。
运行：data/.venv-arm/bin/python baseline/train_l1_model.py
"""
import os

import numpy as np
import tensorflow as tf
from sklearn.model_selection import StratifiedGroupKFold

from metrics import recall_at_fpr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "data", "work")
OUT_DIR = os.path.join(WORK, "l1_model")


def load_data():
    cry = np.load(os.path.join(WORK, "embeddings.npz"), allow_pickle=True)
    esc = np.load(os.path.join(WORK, "esc_embeddings.npz"), allow_pickle=True)
    X = np.concatenate([cry["X_mean"], esc["X"]]).astype("float32")
    y = np.concatenate([
        np.ones(len(cry["X_mean"])),
        (esc["category"] == "crying_baby").astype(float),
    ]).astype("float32")
    groups = np.concatenate([
        cry["uuids"],
        np.char.add("escfold_", esc["fold"].astype(str)),
    ])
    return X, y, groups


def build_head(dim: int) -> tf.keras.Model:
    m = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(dim,)),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-3),
              loss="binary_crossentropy",
              metrics=[tf.keras.metrics.AUC(name="auc")])
    return m


def main():
    X, y, groups = load_data()
    print(f"样本 {len(y)} (正 {int(y.sum())} / 负 {int((1-y).sum())}), 维度 {X.shape[1]}")

    # 留出一折当测试集（其余训练），按组切分
    skf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    tr, te = next(skf.split(X, y, groups))

    n_pos, n_neg = y[tr].sum(), (1 - y[tr]).sum()
    cw = {0: len(y[tr]) / (2 * n_neg), 1: len(y[tr]) / (2 * n_pos)}

    model = build_head(X.shape[1])
    model.fit(X[tr], y[tr], validation_data=(X[te], y[te]),
              epochs=30, batch_size=64, class_weight=cw, verbose=0,
              callbacks=[tf.keras.callbacks.EarlyStopping(
                  monitor="val_auc", mode="max", patience=6,
                  restore_best_weights=True)])

    prob = model.predict(X[te], verbose=0).ravel()
    auc = tf.keras.metrics.AUC()(y[te], prob).numpy()
    print(f"\n[测试折] AUC={auc:.4f}  "
          f"召回@FPR1%(保守)={recall_at_fpr(y[te], prob, 0.01):.3f}  "
          f"召回@FPR5%(保守)={recall_at_fpr(y[te], prob, 0.05):.3f}")

    # 保存 + 导出 TFLite（端侧分类头；端侧前接 YAMNet 出 embedding）
    os.makedirs(OUT_DIR, exist_ok=True)
    model.export(os.path.join(OUT_DIR, "saved_model"))
    conv = tf.lite.TFLiteConverter.from_saved_model(os.path.join(OUT_DIR, "saved_model"))
    conv.optimizations = [tf.lite.Optimize.DEFAULT]   # 动态范围量化
    tfl = conv.convert()
    path = os.path.join(OUT_DIR, "l1_head.tflite")
    with open(path, "wb") as f:
        f.write(tfl)
    print(f"已导出 TFLite: {path}  ({len(tfl)/1024:.1f} KB)")
    print("→ iOS 用 coremltools 从 saved_model 导 .mlpackage；端侧推理 = YAMNet→此头。")


if __name__ == "__main__":
    main()

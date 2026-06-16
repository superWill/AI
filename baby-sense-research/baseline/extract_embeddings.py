#!/usr/bin/env python3
"""用 YAMNet (AudioSet 预训练, Apache 2.0) 提取每条音频的 embedding。

输出 data/work/embeddings.npz:
  X_mean  (N,1024) 帧 embedding 均值池化
  X_max   (N,1024) 最大池化
  cry_score (N,)   YAMNet 零样本"婴儿哭声"分数(相关类取帧最大)
  + labels/uuids/ages/sources/paths
"""
import csv
import os

import numpy as np
import soundfile as sf
import tensorflow as tf
import tensorflow_hub as hub

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
MANIFEST = os.path.join(DATA, "work", "manifest.csv")
OUT = os.path.join(DATA, "work", "embeddings.npz")

CRY_CLASSES = {"Baby cry, infant cry", "Crying, sobbing", "Whimper"}


def main() -> None:
    model = hub.load("https://tfhub.dev/google/yamnet/1")
    class_names = [
        r["display_name"]
        for r in csv.DictReader(tf.io.gfile.GFile(model.class_map_path().numpy()))
    ]
    cry_idx = [i for i, n in enumerate(class_names) if n in CRY_CLASSES]
    print(f"零样本哭声类索引: {dict((class_names[i], i) for i in cry_idx)}")

    rows = list(csv.DictReader(open(MANIFEST)))
    X_mean, X_max, cry_score = [], [], []
    for i, r in enumerate(rows):
        wav, sr = sf.read(os.path.join(DATA, r["path"]), dtype="float32")
        assert sr == 16000, r["path"]
        scores, embeddings, _ = model(wav)
        X_mean.append(embeddings.numpy().mean(axis=0))
        X_max.append(embeddings.numpy().max(axis=0))
        cry_score.append(float(scores.numpy()[:, cry_idx].max()))
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(rows)}")

    np.savez(
        OUT,
        X_mean=np.array(X_mean), X_max=np.array(X_max),
        cry_score=np.array(cry_score),
        labels=np.array([r["label"] for r in rows]),
        uuids=np.array([r["uuid"] for r in rows]),
        ages=np.array([r["age"] for r in rows]),
        sources=np.array([r["source"] for r in rows]),
        paths=np.array([r["path"] for r in rows]),
    )
    print(f"已保存 {len(rows)} 条 embedding -> {OUT}")


if __name__ == "__main__":
    main()

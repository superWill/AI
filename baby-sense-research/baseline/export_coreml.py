#!/usr/bin/env python3
"""M1c: 导出端侧 Core ML 模型 + 黄金一致性参考。

产物(写入 app-ios/):
  BabyTriage/ML/YAMNetEmbedding.mlpackage   mel patches [N,96,64] -> embeddings [N,1024]
  BabyTriage/ML/CryHead.mlpackage           embedding [1,1024] -> cry_prob [1,1]
  BabyTriage/ML/melmatrix.bin               257x64 float32 mel 权重(烘焙, 保证端侧与训练一致)
  Tests/Fixtures/golden_*.wav + golden.json 黄金音频与期望概率(hub 全管线参考)

设计: 端侧 Swift 只做 STFT幅度谱(vDSP) × 烘焙mel矩阵 + log, 卷积栈交给 CoreML——
避免转换 TF 的 FFT 算子(coremltools 风险点)。

运行: data/.venv-arm/bin/python baseline/export_coreml.py
"""
import json
import os
import shutil
import sys

import numpy as np
import soundfile as sf
import tensorflow as tf
import tf_keras
import tensorflow_hub as hub
import coremltools as ct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "baseline", "yamnet_src"))
import params as yamnet_params          # noqa: E402  (vendored, Apache 2.0)
import yamnet as yamnet_model           # noqa: E402

DATA = os.path.join(ROOT, "data")
APP = os.path.join(ROOT, "app-ios")
ML_DIR = os.path.join(APP, "BabyTriage", "ML")
FIXTURE_DIR = os.path.join(APP, "Tests", "Fixtures")
H5 = os.path.join(DATA, "work", "yamnet", "yamnet.h5")
HEAD_SAVEDMODEL = os.path.join(DATA, "work", "l1_model", "saved_model")


def build_core_model(frames_model):
    """从官方 frames 模型中抽出 patches->embeddings 的卷积核心(复用已加载权重)。
    上游用 tf_keras(Keras2 兼容包), 切层也必须用 tf_keras 类型。"""
    layers_list = frames_model.layers
    reshape_idx = next(i for i, l in enumerate(layers_list)
                       if isinstance(l, tf_keras.layers.Reshape))
    gap_idx = next(i for i, l in enumerate(layers_list)
                   if isinstance(l, tf_keras.layers.GlobalAveragePooling2D))
    inp = tf_keras.Input(shape=(96, 64), name="mel_patches")
    x = inp
    for l in layers_list[reshape_idx:gap_idx + 1]:
        x = l(x)
    return tf_keras.Model(inp, x, name="yamnet_core")


def main():
    os.makedirs(ML_DIR, exist_ok=True)
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    p = yamnet_params.Params()

    # 1) 官方 frames 模型 + 权重
    frames = yamnet_model.yamnet_frames_model(p)
    frames.load_weights(H5)
    core = build_core_model(frames)
    print("core 模型就绪:", core.input_shape, "->", core.output_shape)

    # 2) mel 矩阵烘焙(与 TF 完全一致)
    mel_mat = tf.signal.linear_to_mel_weight_matrix(
        num_mel_bins=64, num_spectrogram_bins=257, sample_rate=16000,
        lower_edge_hertz=125.0, upper_edge_hertz=7500.0).numpy().astype(np.float32)
    mel_mat.tofile(os.path.join(ML_DIR, "melmatrix.bin"))
    print("melmatrix.bin:", mel_mat.shape)

    # 3) 转 Core ML —— 用单个 concrete function(多签名 SavedModel 不被 ct 支持)
    @tf.function(input_signature=[tf.TensorSpec([None, 96, 64], tf.float32, name="mel_patches")])
    def core_fn(x):
        return core(x)

    n = ct.RangeDim(lower_bound=1, upper_bound=64, default=8)
    emb_ml = ct.convert(
        [core_fn.get_concrete_function()], source="tensorflow",
        # IO 强制 fp32(权重仍 fp16): iOS 端喂 Float32 MLMultiArray 不被误读
        inputs=[ct.TensorType(name="mel_patches", shape=(n, 96, 64), dtype=np.float32)],
        outputs=[ct.TensorType(dtype=np.float32)],
        compute_precision=ct.precision.FLOAT16,
        minimum_deployment_target=ct.target.iOS17)
    emb_path = os.path.join(ML_DIR, "YAMNetEmbedding.mlpackage")
    shutil.rmtree(emb_path, ignore_errors=True)
    emb_ml.save(emb_path)
    print("saved", emb_path)

    head_loaded = tf.saved_model.load(HEAD_SAVEDMODEL)

    @tf.function(input_signature=[tf.TensorSpec([1, 1024], tf.float32, name="embedding")])
    def head_fn_conv(x):
        return head_loaded.serve(x)

    head_ml = ct.convert(
        [head_fn_conv.get_concrete_function()], source="tensorflow",
        inputs=[ct.TensorType(name="embedding", shape=(1, 1024))],
        compute_precision=ct.precision.FLOAT32,
        minimum_deployment_target=ct.target.iOS17)
    head_path = os.path.join(ML_DIR, "CryHead.mlpackage")
    shutil.rmtree(head_path, ignore_errors=True)
    head_ml.save(head_path)
    print("saved", head_path)

    # 4) 黄金参考: hub 全管线(波形→embedding均值→头) 为真值
    hub_model = hub.load("https://tfhub.dev/google/yamnet/1")
    head_fn = tf.saved_model.load(HEAD_SAVEDMODEL)

    import csv as _csv
    manifest = os.path.join(DATA, "work", "manifest.csv")
    rows = list(_csv.DictReader(open(manifest)))
    cry_path = os.path.join(DATA, rows[0]["path"])           # 一条真哭声(donateacry, ODbL 可再分发)

    # 负样本用合成噪声(种子固定): 无 license 负担(ESC-50 为 NC 不能进仓库)
    rng = np.random.default_rng(7)
    noise_wav = (rng.standard_normal(16000 * 5) * 0.1).astype(np.float32)

    golden = []
    for tag, src in [("cry", cry_path), ("noise", None)]:
        if src is None:
            wav = noise_wav
        else:
            wav, sr = sf.read(src, dtype="float32")
            if wav.ndim > 1:
                wav = wav.mean(axis=1)
        wav = wav[: 16000 * 5]                                # 5s 足够
        dst = os.path.join(FIXTURE_DIR, f"golden_{tag}.wav")
        sf.write(dst, wav, 16000)

        _, emb, _ = hub_model(wav)
        pooled = tf.reduce_mean(emb, axis=0, keepdims=True)
        prob = float(head_fn.serve(tf.cast(pooled, tf.float32)).numpy().ravel()[0])

        # 同时验证 core 抽取路径 == hub (训练侧自洽)
        frames_out = frames(wav)
        emb2 = frames_out[1]
        pooled2 = tf.reduce_mean(emb2, axis=0, keepdims=True)
        prob2 = float(head_fn.serve(tf.cast(pooled2, tf.float32)).numpy().ravel()[0])

        golden.append({"file": f"golden_{tag}.wav", "expected_prob": round(prob, 4)})
        print(f"{tag}: hub_prob={prob:.4f}  frames_prob={prob2:.4f}  (应接近)")

    with open(os.path.join(FIXTURE_DIR, "golden.json"), "w") as f:
        json.dump(golden, f, ensure_ascii=False, indent=2)
    print("golden.json written")


if __name__ == "__main__":
    main()

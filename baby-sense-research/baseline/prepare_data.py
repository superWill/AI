#!/usr/bin/env python3
"""donateacry 数据准备：优先用原始桶的高质量音源，统一转 16kHz mono WAV。

清洗版(KTH)保留了原始文件名，借此把"已验证是哭声"的清单映射回原始桶：
  - iOS 原始 CAF 是 16kHz ADPCM —— 原生带宽，首选
  - Android 原始 3GP 是 AMR-NB 8kHz —— 与清洗版等价，上采样到 16k
  - 两边都找不到才回退用清洗版 8kHz wav

输出:
  data/work/wav16k/<label>/<name>.wav
  data/work/manifest.csv  (path,label,uuid,gender,age,source)
仅依赖标准库 + ffmpeg。
"""
import csv
import glob
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
CORPUS = os.path.join(DATA, "donateacry-corpus")
CLEANED = os.path.join(CORPUS, "donateacry_corpus_cleaned_and_updated_data")
IOS = os.path.join(CORPUS, "donateacry-ios-upload-bucket")
ANDROID = os.path.join(CORPUS, "donateacry-android-upload-bucket")
OUT = os.path.join(DATA, "work", "wav16k")
MANIFEST = os.path.join(DATA, "work", "manifest.csv")


def ffmpeg_to_16k(src: str, dst: str) -> bool:
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", src,
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", dst],
        capture_output=True,
    )
    if r.returncode != 0:
        print(f"  转码失败 {os.path.basename(src)}: {r.stderr.decode()[:120]}", file=sys.stderr)
        return False
    return True


def main() -> None:
    ios_index = {os.path.basename(p): p for p in glob.glob(os.path.join(IOS, "*.caf"))}
    android_index = {os.path.basename(p): p for p in glob.glob(os.path.join(ANDROID, "*.3gp"))}

    rows = []
    stats = {"ios_caf_16k": 0, "android_3gp_8k": 0, "cleaned_wav_8k": 0, "fail": 0}
    for wav in sorted(glob.glob(os.path.join(CLEANED, "*", "*.wav"))):
        label = os.path.basename(os.path.dirname(wav))
        stem = os.path.basename(wav)[:-4]
        parts = stem.split("-")
        uuid = "-".join(parts[0:5])
        gender, age = parts[-3], parts[-2]

        if stem + ".caf" in ios_index:
            src, source = ios_index[stem + ".caf"], "ios_caf_16k"
        elif stem + ".3gp" in android_index:
            src, source = android_index[stem + ".3gp"], "android_3gp_8k"
        else:
            src, source = wav, "cleaned_wav_8k"

        dst_dir = os.path.join(OUT, label)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, stem + ".wav")
        if not os.path.exists(dst) and not ffmpeg_to_16k(src, dst):
            stats["fail"] += 1
            continue
        stats[source] += 1
        rows.append({"path": os.path.relpath(dst, DATA), "label": label,
                     "uuid": uuid, "gender": gender, "age": age, "source": source})

    os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
    with open(MANIFEST, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "label", "uuid", "gender", "age", "source"])
        w.writeheader()
        w.writerows(rows)

    print(f"manifest: {len(rows)} 条 -> {MANIFEST}")
    print("音源构成:", stats)


if __name__ == "__main__":
    main()

# baby-sense-research — 婴儿哭声短时分析助手

定位（PRD v0.4）：宝宝哭了 → 家长打开 App 录 5–15s → 本地分析 → **帮家长快速记录、分析哭声强度、按步骤排查原因，并积累个性化反馈**。**v1 不下任何 ML 判断**（不报原因、不报要不要紧），只给可测量事实 + 上下文 + 排查清单 + 反馈。

## TL;DR 能力边界（自有数据实测）

| 能力 | v1 角色 | 实测 / 状态 |
|---|---|---|
| **L1 → 录音质量检查** | ✅ v1 用 | 哭声/非哭声 AUC 0.999（公开数据）；判"是不是哭声/吵不吵/够不够/太远" |
| **强度/持续测量（DSP）** | ✅ v1 用 | 直接测，无模型、永远准；**强度≠严重程度，中性呈现** |
| **L2 痛/要不要紧** | ⏸ 后置 | 未测、无数据；待自采(疫苗场景客观真值)，AUC≥0.90 才上 |
| **L3 原因（饿/困/不适）** | ⏸ 后置 | 三分类 0.290~0.315 **≈随机**；公开数据做不到，靠反馈闭环攒数据 |

> ⚠️ L1 强结果基于公开数据（donateacry 近场哭声 + ESC-50 干净 5s 噪声片段），**不等于真实家庭场景已解决**——真实远场手机麦、电视/人声/宠物/白噪声未测，见 [`baseline/实验结果.md`](baseline/实验结果.md)「尚未验证」。

产品决策见 [`婴儿哭声感知-方案与PRD.md`](婴儿哭声感知-方案与PRD.md)（PRD v0.4）；工程见 [`技术方案.md`](技术方案.md)（v0.3）；结果页设计见 [`v1-结果页文案与交互.md`](v1-结果页文案与交互.md)；**使用闭环（建议→动作→结果→更准）见 [`闭环与建议引擎设计.md`](闭环与建议引擎设计.md)**；数据见 [`数据清单.md`](数据清单.md)。

## 目录结构

```
baby-sense-research/
├── README.md                      ← 本文件
├── requirements-mfcc.txt          ← MFCC 实验依赖（零编译，秒装）
├── requirements-yamnet.txt        ← YAMNet 实验依赖（需 arm64 + setuptools<81）
├── 婴儿哭声感知-方案与PRD.md        ← 产品方案 / PRD v0.2
├── 数据清单.md                     ← 已抓数据 + license + 质量盘点
├── baseline/
│   ├── features.py                ← 零依赖 MFCC 特征（numpy/scipy）
│   ├── metrics.py                 ← 低误报召回(保守口径) + 按折 mean±std 评估
│   ├── prepare_data.py            ← donateacry 转码 16k + 生成 manifest
│   ├── run_experiments.py         ← MFCC 版 L1 + L3（一键）
│   ├── leakage_demo.py            ← 随机切分 vs 按婴儿切分 泄漏对照
│   ├── extract_embeddings.py      ← YAMNet embedding 提取（哭声）
│   ├── train_eval.py              ← YAMNet 版 L3
│   ├── eval_L1.py                 ← YAMNet 版 L1（含 ESC embedding 提取）
│   ├── train_l1_model.py          ← L1 产品训练：Keras 头 + 导出 TFLite（可端侧）
│   └── 实验结果.md                 ← 全部数字 + 解读 + 评估修正说明
└── data/                          ← 数据与 venv，已 .gitignore（不入库）
    ├── donateacry-corpus/         ← git clone（见下）
    ├── ESC-50-master/             ← 下载解压（见下）
    ├── work/                      ← 中间产物：manifest.csv / *.npz 特征缓存
    ├── .venv/                     ← MFCC venv
    └── .venv-arm/                 ← YAMNet venv（arm64）
```

## 数据放哪、怎么拿（data/ 不入库）

```bash
cd baby-sense-research/data

# 1) donateacry（ODbL，可商用）—— 稀疏拉取，省带宽
git clone --depth 1 --filter=blob:none --sparse https://github.com/gveres/donateacry-corpus.git
cd donateacry-corpus
git sparse-checkout set donateacry_corpus_cleaned_and_updated_data \
    donateacry-ios-upload-bucket donateacry-android-upload-bucket
cd ..

# 2) ESC-50（CC BY-NC，仅实验，勿进商用模型）—— 环境噪声负样本
curl -L -o esc50.zip https://github.com/karolpiczak/ESC-50/archive/master.zip
unzip -q esc50.zip       # 得到 ESC-50-master/
```

## 复现实验

### A. MFCC baseline（推荐先跑，零编译、几分钟）

```bash
cd baby-sense-research
uv venv data/.venv --python 3.12         # 或 python -m venv
uv pip install --python data/.venv/bin/python -r requirements-mfcc.txt
# 需要 ffmpeg：brew install ffmpeg

data/.venv/bin/python baseline/prepare_data.py      # 转码 + manifest（第一次必跑）
data/.venv/bin/python baseline/run_experiments.py   # L1 + L3（首次提特征并缓存到 work/）
data/.venv/bin/python baseline/leakage_demo.py      # 泄漏对照
```

### B. YAMNet 确认实验（可选，需 arm64 Python）

```bash
cd baby-sense-research
# ⚠️ 必须 arm64 原生 Python（x86/Rosetta 跑 TF 会 AVX 崩溃）
uv python install 3.12
uv venv data/.venv-arm --python 3.12 --python-preference only-managed
uv pip install --python data/.venv-arm/bin/python -r requirements-yamnet.txt

data/.venv-arm/bin/python baseline/extract_embeddings.py   # 提哭声 embedding → work/embeddings.npz
data/.venv-arm/bin/python baseline/train_eval.py           # YAMNet 版 L3
data/.venv-arm/bin/python baseline/eval_L1.py              # YAMNet 版 L1（首次会提 2000 条 ESC embedding）
```

### C. L1 产品模型训练 + 导出端侧（M1 起点）

```bash
# 需先跑过 B 的 extract_embeddings.py 和 eval_L1.py（生成两个 npz）
data/.venv-arm/bin/python baseline/train_l1_model.py
# → 训 Keras 分类头(可导出) → 评估 → 导出 data/work/l1_model/l1_head.tflite (~67KB)
# → iOS 再用 coremltools 从 saved_model 导 .mlpackage
# 端侧推理 = YAMNet(出 1024d embedding) → 此分类头(出哭声概率)
```

> 跑前确保已跑过 A 的 `prepare_data.py`（YAMNet 脚本复用其 manifest）。

## 评估口径（重要）

- **严格按婴儿/ESC-fold 组切分**（StratifiedGroupKFold）：同一宝宝的多条哭声不跨训练/测试，杜绝泄漏。随机切分会虚高（见 `leakage_demo.py`）。
- **低误报召回 = 保守口径**：`recall@FPR≤t` 取满足 fpr≤t 的最高召回（`searchsorted(...,side='right')-1`），不突破误报预算；并报**按折 mean±std** 暴露方差。详见 `baseline/metrics.py` 与实验结果文档「评估方法修正」。

## 常见坑

| 现象 | 原因 / 解法 |
|---|---|
| TF `AVX instructions not available` | 用了 x86 Python（/usr/local 或 Rosetta）。改用 arm64 原生 Python。 |
| `No module named 'pkg_resources'` | setuptools≥82 删了它。`pip install "setuptools<81"`。 |
| `sr=44100` assert / 采样率不符 | `features.py` 已内置重采样；确保用最新版。 |
| ffmpeg not found | `brew install ffmpeg`。 |

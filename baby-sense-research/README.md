# baby-sense-research — 婴儿哭声感知可行性验证

验证"从婴儿声音判断需求"能否做成 App，并用自有数据实测能力边界。

## TL;DR 结论

| 能力 | 公开数据实测 | 能不能做 |
|---|---|---|
| **L1 哭声检测**（哭没哭） | YAMNet 训练 AUC 0.999、召回 1.000±0.000 @5%误报 | ✅ 公开数据上很强，方向可行 |
| **L2 痛/非痛** | 未测（无可商用公开痛苦标签） | 待自采（疫苗场景客观真值） |
| **L3 意图**（饿/困/不适） | 三分类 0.290~0.315，**≈随机** | ⛔ 公开数据做不到，靠 App 反馈闭环攒数据 |

> ⚠️ L1 的强结果基于公开数据（donateacry 近场哭声 + ESC-50 干净 5s 噪声片段），**不等于真实家庭夜间场景已解决**。真实远场手机麦、连续底噪、电视/人声/宠物/白噪声等均未测——见 [`baseline/实验结果.md`](baseline/实验结果.md) 的「尚未验证」。

完整方案与产品决策见 [`婴儿哭声感知-方案与PRD.md`](婴儿哭声感知-方案与PRD.md)；工程实现见 [`技术方案.md`](技术方案.md)；数据盘点见 [`数据清单.md`](数据清单.md)。

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

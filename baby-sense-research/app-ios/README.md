# BabyTriage — 哭闹排查助手 iOS（M1a ✅ M1b-1 ✅ M1c ✅）

> 先骨架后模型。当前状态：
> - **M1a ✅** 完整本地闭环（建议→动作→追问→档案→历史影响下次排序），验收 11/11
> - **M1a.5 ✅** 手感验收（截图巡游 12 屏，4 条标准全过）
> - **M1b-1 ✅** 真录音（AVAudioEngine→16k mono，15s 自动停）+ 质量检测（时长/音量/SNR 纯 DSP）+ 强度/停顿比
> - **M1c ✅ 端侧模型已接入**："是不是宝宝哭声"由 **YAMNet+训练头(Core ML)** 真判定：
>   - `ML/YAMNetEmbedding.mlpackage`（6.2MB，权重fp16/IO fp32）+ `ML/CryHead.mlpackage`（268KB）+ `ML/melmatrix.bin`（烘焙 mel 矩阵，保证端侧与训练逐位一致）
>   - Swift 前端 `MelFrontend`（vDSP 幅度谱×烘焙mel）→ `CryDetector`（CoreML 两段推理+均值池化）
>   - **黄金一致性测试**：同一音频 端侧 vs 训练端(hub) 概率差 <0.1（实测哭声 0.975 vs 0.985，噪声一致）；模型层拒识噪声(<0.3)
>   - 不像哭声 → `notCry` →"录到的声音不太像宝宝的哭声"引导重录/手动
>   - 重新导出：`data/.venv-arm/bin/python baseline/export_coreml.py`
> - **M1d ✅ 可选音频捐赠/隐私授权**：反馈完成后**单独同意**（每段一次、默认不捐）；同意才把会话内暂存样本压成 AAC 存本机 `donations/` 待上传队列（**无云端、不联网、不自动上传**）；手动记录/质量不合格不询问；未捐赠音频随会话丢弃；档案页可查看并**一键全删**
> - 待做（M1 后）：M1b-2 尖锐度谱特征（可选）、云端上传协议(届时统一 Opus/AAC)、Android 移植
>
> 测试/UI 自动化仍用 Mock（`-uitest`），真录音真模型只在正常运行生效——回归 **24/24** 全绿（7 闭环 + 5 捐赠 + 3 黄金 + 5 DSP + 4 UI）。
> ⚠️ 转换坑位记录：coremltools 转 fp16 模型默认 IO 也是 fp16，iOS 端喂 Float32 MLMultiArray 会被按字节误读输出全零——必须 `dtype=np.float32` 强制 IO fp32（脚本已处理）。

## 跑起来

```bash
cd baby-sense-research/app-ios
xcodegen generate          # 生成 BabyTriage.xcodeproj（已 gitignore，不入库）
open BabyTriage.xcodeproj  # Xcode 选 iPhone 模拟器 Run
# 或命令行:
xcodebuild -project BabyTriage.xcodeproj -scheme BabyTriage \
  -destination 'platform=iOS Simulator,name=iPhone 15' build
```

要求：Xcode 15+（iOS 17 SDK，SwiftData）、xcodegen（`brew install xcodegen`）。

## 已实现（M1a 清单）

| 模块 | 文件 | 说明 |
|---|---|---|
| 数据链(核心资产) | `Models.swift` | SwiftData：`BabyProfile / CryRecord / CryContext / Suggestion / ActionAttempt / Outcome / NextSuggestionReason` |
| 模拟分析 | `CryAnalyzer.swift` | 协议 `CryAnalyzing` + `MockCryAnalyzer`（返回 quality/cry_confidence/intensity/noise；每5次1次"太吵"验证重录路径）。**M1b 换真实现只动这文件** |
| 规则排序引擎 | `SuggestionEngine.swift` | 输入=距喂奶/时间段/危险症状 + 该宝宝历史有效率/最近无效；输出=top3+可解释理由；危险症状→升级。`nextReason()` 生成「下次建议依据」 |
| 流程状态机 | `FlowState.swift` | S1→S8/SE 全闭环；"先手动记录"S1→S4；"更严重"→SE |
| 8 屏 UI | `TriageFlowView.swift` | 与 `v1-页面流原型.md` 一一对应（含评审定稿的 S1） |
| 档案页 | `ProfileView.swift` | ② 的 4 区块，真实聚合自本地记录（概览/有效排行/时段/下次依据） |
| 5min 追问 | `FollowUpNotifier.swift` | 本地通知（非后台音频）；选「我先试」即排定，早反馈则取消 |

- 本地存储 SwiftData，**不上云**；M1a 不录真音频（模拟），自然不保存音频。
- 已验证：模拟器编译通过 + 启动运行（S1 渲染正确、通知权限按预期弹出）。

## 自动化验收（已全绿 ✅ 11/11）

评审 5 条验收已固化为测试，随时回归：

```bash
xcodebuild -project BabyTriage.xcodeproj -scheme BabyTriage \
  -destination 'platform=iOS Simulator,name=iPhone 15' test
```

| 验收条目 | 逻辑层(单元) | UI层(模拟器实点) |
|---|---|---|
| 1 正常闭环全链路 | `testNormalLoopPersistsFullChain` ✅ | `testNormalLoopEndToEnd` ✅ |
| 2 历史促排+理由"最近对宝宝有效 n/m" | `testEffectiveHistoryPromotesAndExplains` ✅ | （多轮UI易碎,由真人体验) |
| 3 无效降权+理由"最近几次效果不明显" | `testIneffectiveHistoryDemotesAndExplains` ✅ | 同上 |
| 4 危险升级(发热→就医,不给建议) | `testDangerSymptomEscalatesImmediately` + `testWorseOutcomeEscalates` ✅ | `testDangerEscalation` ✅ |
| 5 手动记录分支走完闭环 | `testManualPathCompletesLoop` ✅ | `testManualPathEndToEnd` ✅ |
| 补:太吵→引导重录 | `testNoisyRecordingBlocksAnalysis` ✅ | `testNoisyRecordingGuidesRetry` ✅ |

> UI 测试用 `-uitest` 启动参数关闭通知弹窗与持续动画(保证自动化稳定)；`-forceNoisy` 可强制"太吵"分支。

## 闭环验收路径（模拟器里手点）

1. 记一次 → 开始录音 → 停止 → 看到"是宝宝的哭声 + 强度中等"（约每5次出现"没太听清→重录"）
2. 上下文选 `>3h / 刚睡醒 / 都没有` → 建议第1条应为"喂奶(距上次喂奶已超3小时)"
3. 选「我先试这个」→ 通知已排（5min）→ "现在就反馈" → 选「已缓解」
4. 档案卡显示 动作/结果/「下次排序依据：夜里+距喂奶超3小时时，喂奶往前排」
5. 切到"宝宝档案"Tab：本周次数+1、喂奶进入有效排行、区块4出现该依据
6. 再走一遍选「没变化」→ 依据变为降权；上下文勾"发热"→ 直接升级就医页
7. 重复几次后回到第2步：**喂奶的排序理由会变成"最近对宝宝有效 n/m 次"——闭环影响下一次建议，M1a 目标达成**

## 路线

```
M1a 本地闭环工程(本目录, ✅) → M1b 真音频分析(录音5–15s/质量检测/DSP强度) 
→ M1c 端侧模型导出(YAMNet→CoreML, 黄金集一致性) → M1d 可选捐赠/隐私授权
```
Android(Room/Kotlin) 待 iOS 骨架验证后按同一数据模型移植。

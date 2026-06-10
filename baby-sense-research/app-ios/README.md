# BabyTriage — 哭闹排查助手 iOS（M1a 无模型可跑版）

> 先骨架后模型：M1a 用**模拟分析器**把完整产品闭环跑通——App 真正"记住并影响下一次建议"。模型(M1b/M1c)后接，接口已留好。

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

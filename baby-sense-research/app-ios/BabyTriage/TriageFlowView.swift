import SwiftUI
import SwiftData

// 完整闭环流程 S1→S8 / SE。与 v1-页面流原型.md 一一对应。

struct TriageFlowView: View {
    let baby: BabyProfile
    @Environment(\.modelContext) private var modelContext
    @State private var flow = FlowState()

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Label("哭闹排查助手", systemImage: "stroller")
                    .font(.footnote).foregroundStyle(.secondary)
                Spacer()
                Text(flow.stageLabel)
                    .font(.footnote).foregroundStyle(.tertiary)
            }
            .padding(.horizontal)
            .padding(.top, 8)

            Group {
                switch flow.step {
                case .record: RecordHome(flow: flow)
                case .recording: RecordingScreen(flow: flow)
                case .analysis: AnalysisScreen(flow: flow)
                case .context: ContextScreen(flow: flow, baby: baby, modelContext: modelContext)
                case .suggest: SuggestScreen(flow: flow)
                case .trying: TryingScreen(flow: flow)
                case .followUp: FollowUpScreen(flow: flow)
                case .archived: ArchivedScreen(flow: flow, baby: baby)
                case .escalated: EscalatedScreen(flow: flow)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
    }
}

// S1 录音首页 —— 评审定稿: 开始录音主按钮 + 先手动记录兜底
private struct RecordHome: View {
    @Bindable var flow: FlowState
    var body: some View {
        VStack(spacing: 0) {
            Spacer()
            Text("录一小段哭声").font(.title3.weight(.medium))
            Text("靠近宝宝，录 5–15 秒")
                .font(.subheadline).foregroundStyle(.secondary)
                .padding(.top, 4)

            Button { flow.startRecording() } label: {
                Image(systemName: "mic.fill")
                    .font(.system(size: 40))
                    .frame(width: 116, height: 116)
                    .background(Color.accentColor.opacity(0.12), in: Circle())
            }
            .accessibilityLabel("开始录音")
            .padding(.top, 30)
            Text("开始录音")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Color.accentColor)
                .padding(.top, 10)

            Text("音频仅在本机分析，默认不上传")
                .font(.caption).foregroundStyle(.tertiary)
                .padding(.top, 22)

            Button("先手动记录") { flow.manualEntry() }
                .font(.subheadline).foregroundStyle(.secondary)
                .padding(.top, 16)
            Spacer()
        }
    }
}

// S2 录音中 —— 方块停止键
private struct RecordingScreen: View {
    @Bindable var flow: FlowState
    @State private var pulse = false
    // 持续动画会让 XCUITest 等待 app 空闲而卡住, UI 测试模式下静止
    private let animated = !ProcessInfo.processInfo.arguments.contains("-uitest")

    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            HStack(spacing: 5) {
                ForEach(0..<6, id: \.self) { i in
                    Capsule()
                        .fill(Color.accentColor)
                        .frame(width: 5, height: pulse ? 34 : 10)
                        .animation(animated
                            ? .easeInOut(duration: 0.5).repeatForever().delay(Double(i) * 0.12)
                            : nil, value: pulse)
                }
            }
            .frame(height: 40)
            Text(flow.elapsedSec > 0 ? "正在仔细听… 已录 \(flow.elapsedSec)s" : "正在仔细听…")
                .font(.subheadline).foregroundStyle(.secondary)
                .monospacedDigit()

            Button { flow.stopRecording() } label: {
                Image(systemName: "stop.fill")
                    .font(.system(size: 22))
                    .frame(width: 64, height: 64)
                    .background(.quaternary, in: Circle())
            }
            .accessibilityLabel("停止录音")
            .padding(.top, 12)
            Text("停止").font(.caption).foregroundStyle(.tertiary)
            Spacer()
        }
        .onAppear { if animated { pulse = true } }
    }
}

// S3 分析结果 —— 质量检查 + 中性读数; 不合格 → 按原因给具体引导
private struct AnalysisScreen: View {
    @Bindable var flow: FlowState

    private var hintText: String {
        switch flow.analysis?.recordingQuality {
        case .tooShort: "录得有点短，至少录 3–5 秒。\n没听清就不分析——不给你瞎说。"
        case .tooFar: "声音有点轻，可能离得远——靠近一点再录。\n没听清就不分析——不给你瞎说。"
        case .tooNoisy: "背景有点吵，换个安静点的位置试试。\n没听清就不分析——不给你瞎说。"
        case .notCry: "录到的声音不太像宝宝的哭声（可能是说话声或环境音）。\n拿不准就不分析——不给你瞎说。"
        default: "可能背景有点吵、离得有点远，或录得太短了。\n没听清就不分析——不给你瞎说。"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            if let a = flow.analysis, a.recordingQuality == .ok {
                Label("是宝宝的哭声 · 录音清晰", systemImage: "checkmark.circle.fill")
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(.green)

                VStack(alignment: .leading, spacing: 6) {
                    HStack(spacing: 14) {
                        Label(a.intensityLabel, systemImage: "waveform")
                        Label("约 \(Int(a.durationSec)) 秒\(a.hasPauses ? " · 有停顿" : "")",
                              systemImage: "clock")
                    }
                    .font(.subheadline)
                    Text("强度只是音量，不代表严重程度")
                        .font(.caption).foregroundStyle(.tertiary)
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 10))

                Button("下一步：补充情况 →") { flow.proceedToContext() }
                    .buttonStyle(.borderedProminent)
                    .frame(maxWidth: .infinity)
            } else if flow.analysis?.recordingQuality == .micDenied {
                Label("没拿到麦克风权限", systemImage: "mic.slash")
                    .font(.subheadline.weight(.medium))
                Text("可以在 设置 > 隐私 里打开麦克风权限；\n现在也可以先手动记录这次哭闹。")
                    .font(.subheadline).foregroundStyle(.secondary)
                Button("先手动记录") { flow.manualEntry() }
                    .buttonStyle(.borderedProminent)
            } else {
                Label("这段没太听清", systemImage: "mic.slash")
                    .font(.subheadline.weight(.medium))
                Text(hintText)
                    .font(.subheadline).foregroundStyle(.secondary)
                Button("靠近些，重录") { flow.startRecording() }
                    .buttonStyle(.borderedProminent)
                Button("先手动记录") { flow.manualEntry() }
                    .foregroundStyle(.secondary)
            }
            Spacer()
        }
        .padding()
    }
}

// S4 上下文 —— 危险症状直跳 SE
private struct ContextScreen: View {
    @Bindable var flow: FlowState
    let baby: BabyProfile
    let modelContext: ModelContext

    private let feedOptions: [(String, Int?)] = [("<1h", 40), ("1–3h", 120), (">3h", 200)]
    private let symptoms = ["发热", "呕吐", "呼吸异常", "都没有"]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("补充几项（可跳过）").font(.subheadline.weight(.medium))
            Text("越准，建议排序越靠谱").font(.caption).foregroundStyle(.tertiary)

            Text("距上次喂奶").font(.caption).foregroundStyle(.secondary)
            HStack {
                ForEach(feedOptions, id: \.0) { opt in
                    ChipButton(title: opt.0, selected: flow.feedChoice == opt.1) {
                        flow.feedChoice = opt.1
                    }
                }
            }

            Text("状态").font(.caption).foregroundStyle(.secondary)
            HStack {
                ChipButton(title: "刚睡醒", selected: flow.justWoke) { flow.justWoke = true }
                ChipButton(title: "没睡", selected: !flow.justWoke) { flow.justWoke = false }
            }

            Text("伴随症状").font(.caption).foregroundStyle(.secondary)
            HStack {
                ForEach(symptoms, id: \.self) { s in
                    ChipButton(title: s, selected: flow.symptomChoice == s) {
                        flow.symptomChoice = s
                    }
                }
            }

            Button("看排查建议 →") {
                flow.submitContext(modelContext: modelContext, baby: baby)
            }
            .buttonStyle(.borderedProminent)
            .frame(maxWidth: .infinity)
            .padding(.top, 8)
            Spacer()
        }
        .padding()
    }
}

private struct ChipButton: View {
    let title: String
    let selected: Bool
    let action: () -> Void
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.caption)
                .padding(.horizontal, 10).padding(.vertical, 6)
                .background(selected ? Color.accentColor.opacity(0.15) : .clear,
                            in: RoundedRectangle(cornerRadius: 8))
                .overlay(RoundedRectangle(cornerRadius: 8)
                    .strokeBorder(selected ? Color.accentColor : Color.secondary.opacity(0.4),
                                  lineWidth: 0.7))
        }
        .foregroundStyle(selected ? Color.accentColor : .secondary)
    }
}

// S5 排查建议 —— 排序+理由, 每条「我先试这个」
private struct SuggestScreen: View {
    @Bindable var flow: FlowState

    private var sortedSuggestions: [Suggestion] {
        let items: [Suggestion] = flow.record?.suggestions ?? []
        return items.sorted { $0.rank < $1.rank }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("建议按这个顺序试").font(.subheadline.weight(.medium))
            Text("依据：本次情况 + 这个宝宝的历史")
                .font(.caption).foregroundStyle(.tertiary)

            ForEach(sortedSuggestions) { s in
                Button { flow.choose(action: s.action) } label: {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("\(s.rank) · \(s.action.label)").font(.subheadline.weight(.medium))
                        Text(s.reason).font(.caption).foregroundStyle(.secondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(10)
                    .overlay(RoundedRectangle(cornerRadius: 10)
                        .strokeBorder(.secondary.opacity(0.3), lineWidth: 0.7))
                }
                .foregroundStyle(.primary)
                .accessibilityIdentifier("suggestion-\(s.rank)")
            }
            Text("选一个先试 →（其余作备选）")
                .font(.caption).foregroundStyle(.tertiary)
            Spacer()
        }
        .padding()
    }
}

// S6 已记下 —— 真实 5min 本地通知已排; 调试按钮即时跳转
private struct TryingScreen: View {
    @Bindable var flow: FlowState
    var body: some View {
        VStack(spacing: 12) {
            Spacer()
            Image(systemName: "checkmark.circle")
                .font(.system(size: 36)).foregroundStyle(.green)
            Text("好，去试试「\(flow.chosenAction?.label ?? "")」")
                .font(.headline)
            Text("约 5 分钟后，我会轻轻问你一句：有没有缓解。")
                .font(.subheadline).foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 30)
            Button("现在就反馈") { flow.step = .followUp }
                .buttonStyle(.bordered)
                .padding(.top, 16)
            Spacer()
        }
    }
}

// S7 追问 —— 缓解程度四档
private struct FollowUpScreen: View {
    @Bindable var flow: FlowState
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("刚才试了「\(flow.chosenAction?.label ?? "")」")
                .font(.subheadline.weight(.medium))
            Text("宝宝现在怎么样了？").font(.subheadline).foregroundStyle(.secondary)

            ForEach(Relief.allCases, id: \.self) { r in
                Button { flow.answerFollowUp(relief: r) } label: {
                    Label(r.label, systemImage: icon(for: r))
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .padding(10)
                        .overlay(RoundedRectangle(cornerRadius: 10)
                            .strokeBorder(r == .worse ? Color.orange : .secondary.opacity(0.3),
                                          lineWidth: 0.7))
                }
                .foregroundStyle(r == .worse ? Color.orange : .primary)
            }
            Spacer()
        }
        .padding()
    }

    private func icon(for r: Relief) -> String {
        switch r {
        case .resolved: "face.smiling"
        case .some: "face.dashed"
        case .none: "minus.circle"
        case .worse: "exclamationmark.triangle"
        }
    }
}

// S8 档案卡 —— 闭环沉淀: 记录/动作/结果/下次排序依据
private struct ArchivedScreen: View {
    @Bindable var flow: FlowState
    let baby: BabyProfile
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("已存入宝宝档案", systemImage: "folder.badge.plus")
                .font(.subheadline.weight(.medium))

            if let rec = flow.record {
                VStack(spacing: 8) {
                    row("本次哭声", rec.quality == .manual
                        ? "手动记录 · \(time(rec.ts))"
                        : "\(intensityText(rec.intensity)) · \(Int(rec.durationSec))s · \(time(rec.ts))")
                    row("上下文", contextText(rec.context))
                    row("处理动作", rec.action?.action.label ?? "—")
                    row("结果", rec.outcome?.relief.label ?? "—")
                }
                .padding(12)
                .overlay(RoundedRectangle(cornerRadius: 10)
                    .strokeBorder(.secondary.opacity(0.3), lineWidth: 0.7))

                if let reason = rec.nextReason {
                    VStack(alignment: .leading, spacing: 3) {
                        Label("下次排序依据", systemImage: "arrow.up.arrow.down")
                            .font(.caption).foregroundStyle(Color.accentColor)
                        Text(reason.text).font(.caption)
                            .foregroundStyle(Color.accentColor)
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.accentColor.opacity(0.1),
                                in: RoundedRectangle(cornerRadius: 10))
                }
            }

            Button("完成 · 再记一次") { flow.reset() }
                .buttonStyle(.borderedProminent)
                .frame(maxWidth: .infinity)
            Spacer()
        }
        .padding()
    }

    private func row(_ k: String, _ v: String) -> some View {
        HStack {
            Text(k).font(.caption).foregroundStyle(.secondary)
            Spacer()
            Text(v).font(.caption)
        }
    }
    private func time(_ d: Date) -> String {
        d.formatted(date: .omitted, time: .shortened)
    }
    private func intensityText(_ v: Double) -> String {
        v < 0.4 ? "强度较低" : v < 0.7 ? "强度中等" : "强度较高"
    }
    private func contextText(_ c: CryContext?) -> String {
        guard let c else { return "—" }
        var parts: [String] = []
        if let m = c.sinceFeedMin { parts.append(m >= 180 ? "距喂奶>3h" : "距喂奶\(m)分") }
        if c.justWoke { parts.append("刚睡醒") }
        return parts.isEmpty ? "未填写" : parts.joined(separator: " · ")
    }
}

// SE 升级就医 —— App 收手
private struct EscalatedScreen: View {
    @Bindable var flow: FlowState
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Label("建议尽快找医生", systemImage: "exclamationmark.triangle.fill")
                .font(.subheadline.weight(.medium)).foregroundStyle(.orange)
            Text(flow.escalationMessage)
                .font(.subheadline)
                .padding(12)
                .background(Color.orange.opacity(0.12),
                            in: RoundedRectangle(cornerRadius: 10))
            Text("这种情况别再靠 App 猜——已为你记录本次（含你选的情况）。")
                .font(.caption).foregroundStyle(.secondary)
            Button("我知道了 · 回首页") { flow.reset() }
                .buttonStyle(.bordered)
                .frame(maxWidth: .infinity)
            Spacer()
        }
        .padding()
    }
}

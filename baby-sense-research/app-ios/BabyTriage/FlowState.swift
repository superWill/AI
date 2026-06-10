import Foundation
import SwiftData
import Observation

// 单次排查会话状态机: S1录音 → S2录音中 → S3分析 → S4上下文 → S5建议
//   → S6已记下(等追问) → S7追问 → S8档案卡 ; 危险/恶化 → SE升级
// "先手动记录" 从 S1 直跳 S4。

enum FlowStep {
    case record, recording, analysis, context, suggest, trying, followUp, archived, escalated
}

@Observable
final class FlowState {
    var step: FlowStep = .record
    var stageLabel: String {
        switch step {
        case .record, .recording: "1/6 录音"
        case .analysis: "2/6 分析"
        case .context: "3/6 上下文"
        case .suggest: "4/6 建议"
        case .trying, .followUp: "5/6 追问"
        case .archived: "6/6 档案"
        case .escalated: "已升级"
        }
    }

    var analyzer: CryAnalyzing = MockCryAnalyzer()

    // 会话内暂存
    var analysis: CryAnalysis?
    var isManual = false
    var record: CryRecord?
    var chosenAction: CareAction?
    var escalationMessage = ""

    // S4 上下文选择
    var feedChoice: Int? = 200          // 分钟; nil=未选
    var justWoke = true
    var diaperRecent = false
    var symptomChoice: String = "都没有"

    func startRecording() { step = .recording }

    func stopRecording() {
        let a = analyzer.analyze(durationSec: Double.random(in: 6...14))
        analysis = a
        isManual = false
        step = .analysis
    }

    func manualEntry() {
        analysis = nil
        isManual = true
        step = .context
    }

    func proceedToContext() { step = .context }

    func submitContext(modelContext: ModelContext, baby: BabyProfile) {
        let ctx = CryContext(
            sinceFeedMin: feedChoice,
            sinceSleepMin: justWoke ? 5 : nil,
            sinceDiaperMin: diaperRecent ? 20 : 120,
            justWoke: justWoke,
            daypart: .of(.now),
            symptoms: symptomChoice == "都没有" ? [] : [symptomChoice]
        )

        let rec: CryRecord
        if let a = analysis {
            rec = CryRecord(durationSec: a.durationSec, intensity: a.intensity,
                            noiseLevel: a.noiseLevel, cryConfidence: a.cryConfidence,
                            quality: a.recordingQuality)
        } else {
            rec = CryRecord(durationSec: 0, intensity: 0, noiseLevel: 0,
                            cryConfidence: 0, quality: .manual)
        }
        rec.context = ctx
        baby.records.append(rec)
        modelContext.insert(rec)
        record = rec

        switch SuggestionEngine.decide(context: ctx, history: baby.records) {
        case .escalate(let msg):
            escalationMessage = msg
            rec.nextReason = NextSuggestionReason(kind: .escalate, text: "出现危险症状 → 直接升级就医提醒")
            step = .escalated
        case .suggestions(let ranked):
            rec.suggestions = ranked.enumerated().map { i, r in
                Suggestion(rank: i + 1, action: r.action, reason: r.reason)
            }
            step = .suggest
        }
    }

    func choose(action: CareAction) {
        chosenAction = action
        record?.suggestions.first { $0.action == action }?.chosen = true
        record?.action = ActionAttempt(action: action)
        FollowUpNotifier.schedule(action: action.label, after: 300)
        step = .trying
    }

    func answerFollowUp(relief: Relief) {
        FollowUpNotifier.cancel()
        guard let rec = record, let ctx = rec.context, let action = chosenAction else { return }
        rec.outcome = Outcome(relief: relief)
        rec.nextReason = SuggestionEngine.nextReason(action: action, relief: relief, context: ctx)
        if relief == .worse {
            escalationMessage = "试了「\(action.label)」后反而更严重——别再继续排查，建议尽快联系医生或就医。"
            step = .escalated
        } else {
            step = .archived
        }
    }

    func reset() {
        step = .record
        analysis = nil
        isManual = false
        record = nil
        chosenAction = nil
        escalationMessage = ""
        symptomChoice = "都没有"
    }
}

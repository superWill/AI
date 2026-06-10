import XCTest
import SwiftData
@testable import BabyTriage

// M1a 验收(逻辑层): 对应评审 5 条验收标准。
// 1 正常闭环 / 2 历史促排 / 3 无效降权 / 4 危险升级 / 5 手动记录分支

@MainActor
final class AcceptanceTests: XCTestCase {


    private func makeMockFlow(failEveryN: Int = 0) -> FlowState {
        let flow = FlowState()
        flow.analyzer = MockCryAnalyzer(failEveryN: failEveryN)
        flow.recorder = MockAudioRecorder()
        return flow
    }

    private func makeWorld() throws -> (ModelContext, BabyProfile) {
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        let container = try ModelContainer(for: BabyProfile.self, configurations: config)
        let ctx = ModelContext(container)
        let baby = BabyProfile(name: "测试宝",
                               birthDate: Calendar.current.date(byAdding: .month, value: -3, to: .now)!)
        ctx.insert(baby)
        return (ctx, baby)
    }

    private func seedHistory(_ baby: BabyProfile, action: CareAction, relief: Relief, times: Int) {
        for i in 0..<times {
            let rec = CryRecord(ts: .now.addingTimeInterval(Double(-i) * 3600),
                                durationSec: 10, intensity: 0.5, noiseLevel: 0.1,
                                cryConfidence: 0.95, quality: .ok)
            rec.context = CryContext(sinceFeedMin: 200, sinceSleepMin: nil, sinceDiaperMin: 120,
                                     justWoke: false, daypart: .night, symptoms: [])
            rec.action = ActionAttempt(action: action)
            rec.outcome = Outcome(relief: relief)
            baby.records.append(rec)
        }
    }

    // 验收 1: 正常闭环 —— 录音→上下文→建议→选动作→反馈已缓解→档案链完整
    func testNormalLoopPersistsFullChain() throws {
        let (ctx, baby) = try makeWorld()
        let flow = makeMockFlow()

        flow.startRecording()
        flow.stopRecording()
        XCTAssertEqual(flow.step, .analysis)
        XCTAssertEqual(flow.analysis?.recordingQuality, .ok)

        flow.proceedToContext()
        flow.feedChoice = 200
        flow.symptomChoice = "都没有"
        flow.submitContext(modelContext: ctx, baby: baby)
        XCTAssertEqual(flow.step, .suggest)

        let rec = try XCTUnwrap(flow.record)
        XCTAssertEqual(rec.suggestions.count, 3)
        XCTAssertNotNil(rec.context)

        let first = rec.suggestions.sorted { $0.rank < $1.rank }[0]
        XCTAssertEqual(first.action, .feed, "距喂奶>3h 时第一条应为喂奶")
        XCTAssertTrue(first.reason.contains("3 小时"))

        flow.choose(action: .feed)
        flow.answerFollowUp(relief: .resolved)
        XCTAssertEqual(flow.step, .archived)

        XCTAssertEqual(rec.action?.action, .feed)
        XCTAssertEqual(rec.outcome?.relief, .resolved)
        let reason = try XCTUnwrap(rec.nextReason)
        XCTAssertEqual(reason.kind, .promote)
        XCTAssertTrue(reason.text.contains("喂奶"))
        XCTAssertEqual(baby.records.count, 1)
    }

    // 验收 2: 历史促排 —— 多次"已缓解"后, 排序靠前且理由含"最近对宝宝有效"
    func testEffectiveHistoryPromotesAndExplains() throws {
        let (_, baby) = try makeWorld()
        seedHistory(baby, action: .feed, relief: .resolved, times: 3)

        let ctx = CryContext(sinceFeedMin: 200, sinceSleepMin: nil, sinceDiaperMin: 120,
                             justWoke: false, daypart: .night, symptoms: [])
        guard case .suggestions(let ranked) = SuggestionEngine.decide(context: ctx, history: baby.records) else {
            return XCTFail("不应升级")
        }
        XCTAssertEqual(ranked.first?.action, .feed)
        XCTAssertTrue(ranked.first!.reason.contains("最近对宝宝有效 3/3 次"),
                      "理由应包含历史有效率, 实际: \(ranked.first!.reason)")
    }

    // 验收 3: 无效降权 —— 多次"没变化"后, 不再排第一且理由解释清楚
    func testIneffectiveHistoryDemotesAndExplains() throws {
        let (_, baby) = try makeWorld()
        seedHistory(baby, action: .feed, relief: .none, times: 3)

        let ctx = CryContext(sinceFeedMin: 200, sinceSleepMin: nil, sinceDiaperMin: 120,
                             justWoke: true, daypart: .night, symptoms: [])
        guard case .suggestions(let ranked) = SuggestionEngine.decide(context: ctx, history: baby.records) else {
            return XCTFail("不应升级")
        }
        XCTAssertNotEqual(ranked.first?.action, .feed,
                          "连续无效后喂奶不应再排第一")
        let feedEntry = ranked.first { $0.action == .feed }
        if let feedEntry {
            XCTAssertTrue(feedEntry.reason.contains("最近几次效果不明显"),
                          "降权理由要讲清楚, 实际: \(feedEntry.reason)")
        }
    }

    // 验收 4: 危险升级 —— 勾发热直接升级, 不给建议
    func testDangerSymptomEscalatesImmediately() throws {
        let (ctx, baby) = try makeWorld()
        let flow = makeMockFlow()
        flow.manualEntry()
        flow.symptomChoice = "发热"
        flow.submitContext(modelContext: ctx, baby: baby)

        XCTAssertEqual(flow.step, .escalated)
        XCTAssertTrue(flow.escalationMessage.contains("发热"))
        XCTAssertTrue(flow.record?.suggestions.isEmpty ?? false, "升级时不应继续给排查建议")
        XCTAssertEqual(flow.record?.nextReason?.kind, .escalate)
    }

    // 验收 4b: 反馈"更严重"也升级
    func testWorseOutcomeEscalates() throws {
        let (ctx, baby) = try makeWorld()
        let flow = makeMockFlow()
        flow.startRecording(); flow.stopRecording(); flow.proceedToContext()
        flow.symptomChoice = "都没有"
        flow.submitContext(modelContext: ctx, baby: baby)
        flow.choose(action: .feed)
        flow.answerFollowUp(relief: .worse)

        XCTAssertEqual(flow.step, .escalated)
        XCTAssertEqual(flow.record?.nextReason?.kind, .escalate)
    }

    // 验收 5: 手动记录分支 —— 不录音也能完整走完, 档案标记 manual
    func testManualPathCompletesLoop() throws {
        let (ctx, baby) = try makeWorld()
        let flow = makeMockFlow()
        flow.manualEntry()
        XCTAssertEqual(flow.step, .context)
        flow.symptomChoice = "都没有"
        flow.submitContext(modelContext: ctx, baby: baby)
        XCTAssertEqual(flow.step, .suggest)

        let rec = try XCTUnwrap(flow.record)
        XCTAssertEqual(rec.quality, .manual)
        XCTAssertFalse(rec.suggestions.isEmpty)

        flow.choose(action: .hold)
        flow.answerFollowUp(relief: .some)
        XCTAssertEqual(flow.step, .archived)
        XCTAssertEqual(rec.outcome?.relief, .some)
        XCTAssertEqual(rec.nextReason?.kind, .promote)
    }

    // 补充: 录音质量不合格 → 不进入后续流程
    func testNoisyRecordingBlocksAnalysis() throws {
        let flow = makeMockFlow(failEveryN: 1)   // 每次都"太吵"
        flow.startRecording()
        flow.stopRecording()
        XCTAssertEqual(flow.analysis?.recordingQuality, .tooNoisy)
    }
}

import XCTest
import SwiftData
@testable import BabyTriage

// M1d 验收: 捐赠 = 单独同意; 默认不落盘; 手动/不合格不询问; 可全删。

@MainActor
final class DonationTests: XCTestCase {

    override func setUp() { DonationWriter.deleteAll() }
    override func tearDown() { DonationWriter.deleteAll() }

    private func makeWorld() throws -> (ModelContext, BabyProfile) {
        let config = ModelConfiguration(isStoredInMemoryOnly: true)
        let container = try ModelContainer(for: BabyProfile.self, configurations: config)
        let ctx = ModelContext(container)
        let baby = BabyProfile(name: "测试宝",
                               birthDate: Calendar.current.date(byAdding: .month, value: -3, to: .now)!)
        ctx.insert(baby)
        return (ctx, baby)
    }

    private func completedFlow(_ ctx: ModelContext, _ baby: BabyProfile) -> FlowState {
        let flow = FlowState()
        flow.analyzer = MockCryAnalyzer(failEveryN: 0)
        flow.recorder = MockAudioRecorder()
        flow.startRecording(); flow.stopRecording(); flow.proceedToContext()
        flow.symptomChoice = "都没有"
        flow.submitContext(modelContext: ctx, baby: baby)
        flow.choose(action: .feed)
        flow.answerFollowUp(relief: .resolved)
        return flow
    }

    func testConsentSavesFileAndStatus() throws {
        let (ctx, baby) = try makeWorld()
        let flow = completedFlow(ctx, baby)

        XCTAssertTrue(flow.donationOffered, "合格录音+反馈后应询问捐赠")
        flow.donate()

        let donation = try XCTUnwrap(flow.record?.donation)
        XCTAssertEqual(donation.status, .savedPending)
        XCTAssertNotNil(donation.fileName)
        XCTAssertEqual(DonationWriter.pendingFiles().count, 1, "同意后应有一个本机文件")
        XCTAssertTrue(flow.lastSamples.isEmpty, "捐赠后内存样本应清空")
        XCTAssertFalse(flow.donationOffered, "决定后不再询问")
    }

    func testDeclineLeavesNoFile() throws {
        let (ctx, baby) = try makeWorld()
        let flow = completedFlow(ctx, baby)
        flow.declineDonation()

        XCTAssertEqual(flow.record?.donation?.status, .declined)
        XCTAssertEqual(DonationWriter.pendingFiles().count, 0, "拒绝不应落盘任何音频")
        XCTAssertTrue(flow.lastSamples.isEmpty)
    }

    func testManualPathNeverOffersDonation() throws {
        let (ctx, baby) = try makeWorld()
        let flow = FlowState()
        flow.analyzer = MockCryAnalyzer(failEveryN: 0)
        flow.recorder = MockAudioRecorder()
        flow.manualEntry()
        flow.symptomChoice = "都没有"
        flow.submitContext(modelContext: ctx, baby: baby)
        flow.choose(action: .hold)
        flow.answerFollowUp(relief: .some)

        XCTAssertFalse(flow.donationOffered, "手动记录无音频, 不应询问捐赠")
    }

    func testNoisyRecordingKeepsNoSamples() throws {
        let flow = FlowState()
        flow.analyzer = MockCryAnalyzer(failEveryN: 1)    // 必"太吵"
        flow.recorder = MockAudioRecorder()
        flow.startRecording(); flow.stopRecording()
        XCTAssertTrue(flow.lastSamples.isEmpty, "不合格录音不暂存样本")
    }

    func testResetDiscardsUndonatedSamples() throws {
        let (ctx, baby) = try makeWorld()
        let flow = completedFlow(ctx, baby)
        XCTAssertFalse(flow.lastSamples.isEmpty)
        flow.reset()
        XCTAssertTrue(flow.lastSamples.isEmpty, "未捐赠音频应随会话丢弃")
        XCTAssertEqual(DonationWriter.pendingFiles().count, 0)
    }
}

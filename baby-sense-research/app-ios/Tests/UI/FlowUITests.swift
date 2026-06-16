import XCTest

// M1a 验收(UI层): 在模拟器里真实点完闭环。每个 test 独立冷启动。

final class FlowUITests: XCTestCase {

    override func setUp() {
        continueAfterFailure = false
    }

    private func launch(extra: [String] = []) -> XCUIApplication {
        let app = XCUIApplication()
        app.launchArguments = ["-uitest"] + extra
        app.launch()
        return app
    }

    // 验收 1: 正常闭环 录音→分析→上下文→建议→我先试→反馈→档案
    func testNormalLoopEndToEnd() {
        let app = launch()
        XCTAssertTrue(app.staticTexts["录一小段哭声"].waitForExistence(timeout: 5))

        app.buttons["开始录音"].tap()
        XCTAssertTrue(app.buttons["停止录音"].waitForExistence(timeout: 3))
        app.buttons["停止录音"].tap()

        XCTAssertTrue(app.staticTexts["是宝宝的哭声 · 录音清晰"].waitForExistence(timeout: 3))
        app.buttons["下一步：补充情况 →"].tap()

        XCTAssertTrue(app.staticTexts["补充几项（可跳过）"].waitForExistence(timeout: 3))
        app.buttons["看排查建议 →"].tap()

        XCTAssertTrue(app.staticTexts["建议按这个顺序试"].waitForExistence(timeout: 3))
        app.buttons["suggestion-1"].tap()

        XCTAssertTrue(app.buttons["现在就反馈"].waitForExistence(timeout: 3))
        app.buttons["现在就反馈"].tap()
        app.buttons["已缓解"].tap()

        XCTAssertTrue(app.staticTexts["已存入宝宝档案"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.staticTexts["下次排序依据"].exists)
        app.buttons["完成 · 再记一次"].tap()
        XCTAssertTrue(app.staticTexts["录一小段哭声"].waitForExistence(timeout: 3))
    }

    // 验收 4: 危险升级 —— 勾发热 → 直接就医页, 不出建议
    func testDangerEscalation() {
        let app = launch()
        app.buttons["先手动记录"].tap()
        XCTAssertTrue(app.buttons["发热"].waitForExistence(timeout: 3))
        app.buttons["发热"].tap()
        app.buttons["看排查建议 →"].tap()

        XCTAssertTrue(app.staticTexts["建议尽快找医生"].waitForExistence(timeout: 3))
        XCTAssertFalse(app.staticTexts["建议按这个顺序试"].exists)
        app.buttons["我知道了 · 回首页"].tap()
        XCTAssertTrue(app.staticTexts["录一小段哭声"].waitForExistence(timeout: 3))
    }

    // 验收 5: 手动记录分支 —— 不录音走完闭环, 档案显示"手动记录"
    func testManualPathEndToEnd() {
        let app = launch()
        app.buttons["先手动记录"].tap()
        XCTAssertTrue(app.staticTexts["补充几项（可跳过）"].waitForExistence(timeout: 3))
        app.buttons["看排查建议 →"].tap()
        app.buttons["suggestion-1"].tap()
        app.buttons["现在就反馈"].tap()
        app.buttons["没变化"].tap()

        XCTAssertTrue(app.staticTexts["已存入宝宝档案"].waitForExistence(timeout: 3))
        let manualMark = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '手动记录'")).firstMatch
        XCTAssertTrue(manualMark.exists, "档案应标记手动记录")
    }

    // 补充: 太吵 → 引导重录, 不瞎说
    func testNoisyRecordingGuidesRetry() {
        let app = launch(extra: ["-forceNoisy"])
        app.buttons["开始录音"].tap()
        app.buttons["停止录音"].tap()
        XCTAssertTrue(app.staticTexts["这段没太听清"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.buttons["靠近些，重录"].exists)
    }

    // 验收 2/3 的 UI 侧验证(历史影响排序)在单元测试覆盖;
    // UI 层连续多轮操作易碎, 留给真人体验验收。
}

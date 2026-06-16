import XCTest

// M1a.5 手感验收用截图巡游: 走 3 轮闭环喂历史 → 截关键屏。
// 仅在 TOUR=1 时运行(避免拖慢日常回归)。

final class ScreenshotTourTests: XCTestCase {

    private var app: XCUIApplication!

    override func setUpWithError() throws {
        try XCTSkipUnless(ProcessInfo.processInfo.environment["TOUR"] == "1")
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["-uitest"]
        app.launch()
    }

    private func snap(_ name: String) {
        let a = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        a.name = name
        a.lifetime = .keepAlways
        add(a)
    }

    private func oneLoop(outcome: String, viaRecording: Bool) {
        if viaRecording {
            app.buttons["开始录音"].tap()
            app.buttons["停止录音"].tap()
            _ = app.buttons["下一步：补充情况 →"].waitForExistence(timeout: 3)
            app.buttons["下一步：补充情况 →"].tap()
        } else {
            app.buttons["先手动记录"].tap()
        }
        _ = app.buttons["看排查建议 →"].waitForExistence(timeout: 3)
        app.buttons["看排查建议 →"].tap()
        _ = app.buttons["suggestion-1"].waitForExistence(timeout: 3)
        app.buttons["suggestion-1"].tap()
        app.buttons["现在就反馈"].tap()
        app.buttons[outcome].tap()
        _ = app.buttons["完成 · 再记一次"].waitForExistence(timeout: 3)
        app.buttons["完成 · 再记一次"].tap()
        _ = app.staticTexts["录一小段哭声"].waitForExistence(timeout: 3)
    }

    func testTour() {
        XCTAssertTrue(app.staticTexts["录一小段哭声"].waitForExistence(timeout: 5))
        snap("01-S1-录音首页")

        app.buttons["开始录音"].tap()
        snap("02-S2-录音中")
        app.buttons["停止录音"].tap()
        XCTAssertTrue(app.staticTexts["是宝宝的哭声 · 录音清晰"].waitForExistence(timeout: 3))
        snap("03-S3-分析结果")
        app.buttons["下一步：补充情况 →"].tap()
        snap("04-S4-上下文")
        app.buttons["看排查建议 →"].tap()
        XCTAssertTrue(app.staticTexts["建议按这个顺序试"].waitForExistence(timeout: 3))
        snap("05-S5-建议-首轮")
        app.buttons["suggestion-1"].tap()
        snap("06-S6-已记下")
        app.buttons["现在就反馈"].tap()
        snap("07-S7-追问")
        app.buttons["已缓解"].tap()
        XCTAssertTrue(app.staticTexts["已存入宝宝档案"].waitForExistence(timeout: 3))
        snap("08-S8-档案卡")
        app.buttons["完成 · 再记一次"].tap()
        _ = app.staticTexts["录一小段哭声"].waitForExistence(timeout: 3)

        // 再喂 2 轮"喂奶已缓解" → 历史促排可见
        oneLoop(outcome: "已缓解", viaRecording: false)
        oneLoop(outcome: "已缓解", viaRecording: false)

        app.buttons["先手动记录"].tap()
        app.buttons["看排查建议 →"].tap()
        XCTAssertTrue(app.staticTexts["建议按这个顺序试"].waitForExistence(timeout: 3))
        snap("09-S5-建议-有历史后")
        app.buttons["suggestion-1"].tap()
        app.buttons["现在就反馈"].tap()
        app.buttons["没变化"].tap()
        _ = app.buttons["完成 · 再记一次"].waitForExistence(timeout: 3)
        snap("10-S8-档案卡-没变化")
        app.buttons["完成 · 再记一次"].tap()

        // 危险升级
        app.buttons["先手动记录"].tap()
        app.buttons["发热"].tap()
        app.buttons["看排查建议 →"].tap()
        XCTAssertTrue(app.staticTexts["建议尽快找医生"].waitForExistence(timeout: 3))
        snap("11-SE-升级就医")
        app.buttons["我知道了 · 回首页"].tap()

        // 档案页
        app.tabBars.buttons["宝宝档案"].tap()
        XCTAssertTrue(app.staticTexts["对你家宝宝最近有效"].waitForExistence(timeout: 3))
        snap("12-档案页")
    }
}

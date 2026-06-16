import Foundation
import UserNotifications

// 5 分钟延迟追问: 本地通知(非后台音频,合规无碍)。温和、可忽略。

enum FollowUpNotifier {
    static let id = "followup.relief"

    /// UI 测试模式下禁用(避免系统权限弹窗干扰自动化)
    static var enabled = !ProcessInfo.processInfo.arguments.contains("-uitest")

    static func requestAuthorization() {
        guard enabled else { return }
        UNUserNotificationCenter.current()
            .requestAuthorization(options: [.alert, .sound]) { _, _ in }
    }

    static func schedule(action: String, after seconds: TimeInterval) {
        guard enabled else { return }
        let content = UNMutableNotificationContent()
        content.title = "刚才宝宝怎么样了？"
        content.body = "试了「\(action)」之后，有没有缓解？点开轻轻告诉我一声。"
        content.sound = .default
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: max(seconds, 1), repeats: false)
        let req = UNNotificationRequest(identifier: id, content: content, trigger: trigger)
        UNUserNotificationCenter.current().add(req)
    }

    static func cancel() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [id])
    }
}

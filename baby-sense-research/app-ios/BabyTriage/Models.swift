import Foundation
import SwiftData

// 数据链(产品核心资产):
// CryRecord -> CryContext -> Suggestion -> ActionAttempt -> Outcome
//           -> NextSuggestionReason -> (聚合) BabyProfile -> 影响下一次 Suggestion 排序

@Model
final class BabyProfile {
    var name: String
    var birthDate: Date
    @Relationship(deleteRule: .cascade) var records: [CryRecord] = []

    init(name: String, birthDate: Date) {
        self.name = name
        self.birthDate = birthDate
    }

    var ageMonths: Int {
        Calendar.current.dateComponents([.month], from: birthDate, to: .now).month ?? 0
    }
}

enum RecordingQuality: String, Codable {
    case ok, tooNoisy, tooShort, tooFar
    case manual          // "先手动记录"路径,无音频
}

@Model
final class CryRecord {
    var ts: Date
    var durationSec: Double
    var intensity: Double          // 0–1, 纯测量;UI 必须中性呈现(强度≠严重)
    var noiseLevel: Double         // 0–1
    var cryConfidence: Double      // L1 质量检查输出(M1a 为模拟)
    var qualityRaw: String
    @Relationship(deleteRule: .cascade) var context: CryContext?
    @Relationship(deleteRule: .cascade) var suggestions: [Suggestion] = []
    @Relationship(deleteRule: .cascade) var action: ActionAttempt?
    @Relationship(deleteRule: .cascade) var outcome: Outcome?
    @Relationship(deleteRule: .cascade) var nextReason: NextSuggestionReason?

    init(ts: Date = .now, durationSec: Double, intensity: Double,
         noiseLevel: Double, cryConfidence: Double, quality: RecordingQuality) {
        self.ts = ts
        self.durationSec = durationSec
        self.intensity = intensity
        self.noiseLevel = noiseLevel
        self.cryConfidence = cryConfidence
        self.qualityRaw = quality.rawValue
    }

    var quality: RecordingQuality { RecordingQuality(rawValue: qualityRaw) ?? .ok }
}

enum Daypart: String, Codable, CaseIterable {
    case morning, afternoon, evening, night
    static func of(_ date: Date) -> Daypart {
        switch Calendar.current.component(.hour, from: date) {
        case 6..<12: .morning
        case 12..<18: .afternoon
        case 18..<22: .evening
        default: .night
        }
    }
    var label: String {
        switch self {
        case .morning: "早上"; case .afternoon: "下午"
        case .evening: "傍晚"; case .night: "夜里"
        }
    }
}

@Model
final class CryContext {
    var sinceFeedMin: Int?
    var sinceSleepMin: Int?
    var sinceDiaperMin: Int?
    var justWoke: Bool
    var daypartRaw: String
    var symptoms: [String]         // 命中 dangerSymptoms 即触发升级

    static let dangerSymptoms: Set<String> = ["发热", "呕吐", "呼吸异常", "精神差"]

    init(sinceFeedMin: Int?, sinceSleepMin: Int?, sinceDiaperMin: Int?,
         justWoke: Bool, daypart: Daypart, symptoms: [String]) {
        self.sinceFeedMin = sinceFeedMin
        self.sinceSleepMin = sinceSleepMin
        self.sinceDiaperMin = sinceDiaperMin
        self.justWoke = justWoke
        self.daypartRaw = daypart.rawValue
        self.symptoms = symptoms
    }

    var daypart: Daypart { Daypart(rawValue: daypartRaw) ?? .night }
    var hasDanger: Bool { !Set(symptoms).isDisjoint(with: Self.dangerSymptoms) }
}

enum CareAction: String, Codable, CaseIterable {
    case feed, burp, diaper, soothe, hold, temperature
    var label: String {
        switch self {
        case .feed: "喂奶"; case .burp: "拍嗝"; case .diaper: "换尿布"
        case .soothe: "哄睡"; case .hold: "抱抱安抚"; case .temperature: "量体温"
        }
    }
}

@Model
final class Suggestion {
    var rank: Int
    var actionRaw: String
    var reason: String             // 给家长看的排序理由(可解释)
    var chosen: Bool

    init(rank: Int, action: CareAction, reason: String, chosen: Bool = false) {
        self.rank = rank
        self.actionRaw = action.rawValue
        self.reason = reason
        self.chosen = chosen
    }

    var action: CareAction { CareAction(rawValue: actionRaw) ?? .hold }
}

@Model
final class ActionAttempt {
    var actionRaw: String
    var ts: Date

    init(action: CareAction, ts: Date = .now) {
        self.actionRaw = action.rawValue
        self.ts = ts
    }

    var action: CareAction { CareAction(rawValue: actionRaw) ?? .hold }
}

enum Relief: String, Codable, CaseIterable {
    case resolved, some, none, worse
    var label: String {
        switch self {
        case .resolved: "已缓解"; case .some: "有一点缓解"
        case .none: "没变化"; case .worse: "更严重"
        }
    }
    var effective: Bool { self == .resolved || self == .some }
}

@Model
final class Outcome {
    var reliefRaw: String
    var ts: Date

    init(relief: Relief, ts: Date = .now) {
        self.reliefRaw = relief.rawValue
        self.ts = ts
    }

    var relief: Relief { Relief(rawValue: reliefRaw) ?? .none }
}

enum ReasonKind: String, Codable {
    case promote    // 下次同类情况该动作往前排
    case demote     // 下次降权
    case escalate   // 升级就医,不再排查
}

@Model
final class NextSuggestionReason {
    var kindRaw: String
    var text: String               // 档案页「下次建议依据」直接展示

    init(kind: ReasonKind, text: String) {
        self.kindRaw = kind.rawValue
        self.text = text
    }

    var kind: ReasonKind { ReasonKind(rawValue: kindRaw) ?? .promote }
}

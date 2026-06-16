import Foundation

// 规则排序引擎(无 ML)。输入: 上下文(距喂奶/时间段/危险症状) + 该宝宝历史(最近有效率/无效率)。
// 输出: 排序后的建议 + 每条可解释理由 —— 这就是档案页「下次建议依据」的来源。

struct RankedSuggestion {
    var action: CareAction
    var score: Double
    var reason: String
}

enum TriageDecision {
    case escalate(message: String)              // 危险症状 → 不排查,直接就医
    case suggestions([RankedSuggestion])        // 正常 → top3
}

struct ActionStats {
    var attempts = 0
    var effective = 0
    var recentReliefs: [Relief] = []            // 最近在前
    var rate: Double { attempts == 0 ? 0 : Double(effective) / Double(attempts) }
    /// 最近 3 次中 ≥2 次 没变化/更严重 → 视为"最近无效"
    var recentlyIneffective: Bool {
        let r = recentReliefs.prefix(3).filter { !$0.effective }
        return recentReliefs.count >= 2 && r.count >= 2
    }
}

struct SuggestionEngine {

    static func stats(for records: [CryRecord]) -> [CareAction: ActionStats] {
        var s: [CareAction: ActionStats] = [:]
        for rec in records.sorted(by: { $0.ts > $1.ts }) {
            guard let action = rec.action?.action, let relief = rec.outcome?.relief else { continue }
            var st = s[action] ?? ActionStats()
            st.attempts += 1
            if relief.effective { st.effective += 1 }
            st.recentReliefs.append(relief)
            s[action] = st
        }
        return s
    }

    static func decide(context: CryContext, history: [CryRecord]) -> TriageDecision {
        if context.hasDanger {
            let syms = context.symptoms.filter { CryContext.dangerSymptoms.contains($0) }
            return .escalate(message: "宝宝哭闹 + \(syms.joined(separator: "、"))——尤其 3 月龄内任何发热，建议立即就医。这种情况别再靠排查。")
        }

        let stats = stats(for: history)
        var scored: [RankedSuggestion] = []

        for action in CareAction.allCases where action != .temperature {
            var score = 1.0
            var reasons: [String] = []

            switch action {
            case .feed:
                if let m = context.sinceFeedMin, m >= 180 {
                    score += 2.0; reasons.append("距上次喂奶已超 \(m / 60) 小时")
                } else if let m = context.sinceFeedMin, m < 60 {
                    score -= 1.0; reasons.append("刚喂过不久")
                }
            case .diaper:
                if let m = context.sinceDiaperMin, m < 30 {
                    score -= 1.5; reasons.append("刚换过尿布")
                } else {
                    score += 0.5; reasons.append("还没检查过")
                }
            case .soothe:
                if context.justWoke { score += 0.8; reasons.append("刚睡醒，可能没睡够") }
                if context.daypart == .night { score += 0.5 }
            case .burp:
                if let m = context.sinceFeedMin, m < 45 {
                    score += 1.0; reasons.append("刚喂完，可能需要拍嗝")
                }
            case .hold:
                score += 0.2
            case .temperature:
                break
            }

            if let st = stats[action] {
                if st.attempts >= 3, st.rate >= 0.6 {
                    score += st.rate
                    reasons.append("最近对宝宝有效 \(st.effective)/\(st.attempts) 次")
                }
                if st.recentlyIneffective {
                    score -= 1.2
                    reasons.append("最近几次效果不明显")
                }
            }

            // 最多展示两条理由(上下文 + 历史), 历史理由是"个性化在生效"的证据
            let reason = reasons.isEmpty ? "常规排查项" : reasons.prefix(2).joined(separator: "；")
            scored.append(RankedSuggestion(action: action, score: score, reason: reason))
        }

        let top = scored.sorted { $0.score > $1.score }.prefix(3)
        return .suggestions(Array(top))
    }

    /// 闭环最后一步: 由 动作+结果+上下文 生成「下次建议依据」(档案页展示, 下次排序生效)
    static func nextReason(action: CareAction, relief: Relief, context: CryContext) -> NextSuggestionReason {
        switch relief {
        case .resolved, .some:
            let when = context.daypart == .night ? "夜里" : context.daypart.label
            var cond = when
            if let m = context.sinceFeedMin, m >= 180 { cond += " + 距喂奶超 3 小时" }
            return NextSuggestionReason(kind: .promote,
                text: "\(cond)时，「\(action.label)」往前排（本次有效）")
        case .none:
            return NextSuggestionReason(kind: .demote,
                text: "「\(action.label)」这次没用 → 下次同类情况降权，优先换别的办法")
        case .worse:
            return NextSuggestionReason(kind: .escalate,
                text: "试了「\(action.label)」后更严重 → 已提示就医，下次同类情况优先提醒留意症状")
        }
    }
}

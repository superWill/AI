import SwiftUI
import SwiftData

// ② 宝宝档案页 —— 少做图表,多做"下次有帮助的记忆"。
// 4 区块: 概览 / 有效办法排行 / 时段规律 / 下次建议依据。全部为本地规则统计,无 ML。

struct ProfileView: View {
    let baby: BabyProfile

    var body: some View {
        ScrollView {
            VStack(spacing: 14) {
                overviewCard
                effectivenessCard
                daypartCard
                nextBasisCard
                Text("仅供参考，不能替代医生 · 不做健康评分/发育判断")
                    .font(.caption2).foregroundStyle(.tertiary)
            }
            .padding()
        }
    }

    private var records: [CryRecord] { baby.records.sorted { $0.ts > $1.ts } }

    private var weekRecords: [CryRecord] {
        let cutoff = Calendar.current.date(byAdding: .day, value: -7, to: .now) ?? .now
        return records.filter { $0.ts >= cutoff }
    }

    private var stats: [CareAction: ActionStats] { SuggestionEngine.stats(for: records) }

    private var mostEffective: CareAction? {
        stats.filter { $0.value.attempts >= 2 }
            .max { $0.value.rate < $1.value.rate }?.key
    }

    // 区块1 概览
    private var overviewCard: some View {
        card {
            HStack(spacing: 10) {
                Circle().fill(Color.accentColor.opacity(0.15))
                    .frame(width: 40, height: 40)
                    .overlay(Text(String(baby.name.prefix(1)))
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(Color.accentColor))
                VStack(alignment: .leading, spacing: 1) {
                    Text("\(baby.name) · \(baby.ageMonths) 月龄")
                        .font(.subheadline.weight(.medium))
                    Text(records.first.map { "最近记录：\($0.ts.formatted(date: .omitted, time: .shortened))" } ?? "还没有记录")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Spacer()
            }
            HStack(spacing: 10) {
                metric("本周哭闹", "\(weekRecords.count) 次")
                metric("最近最有效", mostEffective?.label ?? "待积累")
            }
        }
    }

    // 区块2 有效办法排行 —— 只说"对你家宝宝有效",不说原因
    private var effectivenessCard: some View {
        card {
            VStack(alignment: .leading, spacing: 2) {
                Text("对你家宝宝最近有效").font(.subheadline.weight(.medium))
                Text("只看有没有用，不猜原因").font(.caption).foregroundStyle(.tertiary)
            }
            let ranked = stats.filter { $0.value.attempts > 0 }
                .sorted { $0.value.rate > $1.value.rate }
            if ranked.isEmpty {
                Text("用几次之后，这里会告诉你什么办法最管用。")
                    .font(.caption).foregroundStyle(.secondary)
            } else {
                ForEach(ranked, id: \.key) { action, st in
                    VStack(spacing: 3) {
                        HStack {
                            Text(action.label).font(.caption)
                            Spacer()
                            Text("\(st.effective) / \(st.attempts) 次有效")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                        GeometryReader { geo in
                            ZStack(alignment: .leading) {
                                Capsule().fill(.quaternary)
                                Capsule()
                                    .fill(st.rate >= 0.5 ? Color.green.opacity(0.7) : Color.gray.opacity(0.5))
                                    .frame(width: geo.size.width * st.rate)
                            }
                        }
                        .frame(height: 6)
                    }
                }
            }
        }
    }

    // 区块3 时段规律 —— 轻量提示,非曲线
    private var daypartCard: some View {
        card {
            Text("什么时候更常哭").font(.subheadline.weight(.medium))
            let counts = Dictionary(grouping: records) { $0.context?.daypart ?? .night }
                .mapValues(\.count)
            if records.isEmpty {
                Text("记录多了之后，这里会出现宝宝的哭闹时段规律。")
                    .font(.caption).foregroundStyle(.secondary)
            } else {
                let top = counts.max { $0.value < $1.value }
                if let top {
                    Label("\(top.key.label) 最多（\(top.value) 次）",
                          systemImage: top.key == .night ? "moon" : "sun.max")
                        .font(.caption)
                }
                HStack(spacing: 2) {
                    ForEach(Daypart.allCases, id: \.self) { d in
                        let c = counts[d] ?? 0
                        let maxC = max(counts.values.max() ?? 1, 1)
                        Rectangle()
                            .fill(Color.accentColor.opacity(0.15 + 0.6 * Double(c) / Double(maxC)))
                            .frame(height: 8)
                    }
                }
                .clipShape(Capsule())
                HStack {
                    ForEach(Daypart.allCases, id: \.self) { d in
                        Text(d.label).font(.caption2).foregroundStyle(.tertiary)
                            .frame(maxWidth: .infinity)
                    }
                }
            }
        }
    }

    // 区块4 下次建议依据 —— 把排序逻辑讲给家长
    private var nextBasisCard: some View {
        card {
            Text("下次 App 会这样排序").font(.subheadline.weight(.medium))
            // 升级政策由下方固定行统一表达, 最近依据只列促排/降权, 避免重复
            let reasons = records.compactMap(\.nextReason)
                .filter { $0.kind != .escalate }.prefix(3)
            if reasons.isEmpty {
                Text("完成一次完整记录后，这里会告诉你下次建议为什么这么排。")
                    .font(.caption).foregroundStyle(.secondary)
            } else {
                ForEach(Array(reasons.enumerated()), id: \.offset) { _, r in
                    HStack(alignment: .top, spacing: 7) {
                        Image(systemName: icon(for: r.kind))
                            .font(.caption)
                            .foregroundStyle(color(for: r.kind))
                        Text(r.text).font(.caption)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            HStack(alignment: .top, spacing: 7) {
                Image(systemName: "exclamationmark.triangle")
                    .font(.caption).foregroundStyle(.orange)
                Text("若有发热 / 呼吸异常 → 不排查，直接升级就医提醒")
                    .font(.caption)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func icon(for k: ReasonKind) -> String {
        switch k {
        case .promote: "arrow.up"
        case .demote: "arrow.down"
        case .escalate: "exclamationmark.triangle"
        }
    }
    private func color(for k: ReasonKind) -> Color {
        switch k {
        case .promote: .green
        case .demote: .secondary
        case .escalate: .orange
        }
    }

    private func metric(_ label: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.headline)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(.quaternary.opacity(0.4), in: RoundedRectangle(cornerRadius: 10))
    }

    @ViewBuilder
    private func card(@ViewBuilder content: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 10, content: content)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(14)
            .overlay(RoundedRectangle(cornerRadius: 12)
                .strokeBorder(.secondary.opacity(0.25), lineWidth: 0.7))
    }
}

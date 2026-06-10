import SwiftUI
import SwiftData

@main
struct BabyTriageApp: App {
    var body: some Scene {
        WindowGroup {
            RootView()
        }
        .modelContainer(for: [BabyProfile.self])
    }
}

struct RootView: View {
    @Environment(\.modelContext) private var modelContext
    @Query private var babies: [BabyProfile]

    var body: some View {
        Group {
            if let baby = babies.first {
                TabView {
                    TriageFlowView(baby: baby)
                        .tabItem { Label("记一次", systemImage: "mic") }
                    ProfileView(baby: baby)
                        .tabItem { Label("宝宝档案", systemImage: "folder") }
                }
            } else {
                ProgressView()
            }
        }
        .onAppear {
            if babies.isEmpty {
                let b = BabyProfile(name: "宝宝",
                                    birthDate: Calendar.current.date(byAdding: .month, value: -3, to: .now) ?? .now)
                modelContext.insert(b)
            }
            FollowUpNotifier.requestAuthorization()
        }
    }
}

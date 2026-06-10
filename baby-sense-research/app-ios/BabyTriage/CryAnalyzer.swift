import Foundation

// M1a: 模拟分析器把闭环跑通; M1b: 换成真实现(DSP 强度/SNR + YAMNet 质量检查),
// 上层零改动 —— 这是"先骨架后模型"顺序成立的接口边界。

struct CryAnalysis {
    var recordingQuality: RecordingQuality
    var cryConfidence: Double      // 0–1
    var intensity: Double          // 0–1, RMS 归一(模拟)
    var noiseLevel: Double         // 0–1, SNR 反向(模拟)
    var durationSec: Double
    var hasPauses: Bool
}

protocol CryAnalyzing {
    func analyze(durationSec: Double) -> CryAnalysis
}

struct MockCryAnalyzer: CryAnalyzing {
    /// 偶尔返回不合格,验证“引导重录”路径也能走通
    var failEveryN: Int = 5
    private static var counter = 0

    func analyze(durationSec: Double) -> CryAnalysis {
        Self.counter += 1
        if failEveryN > 0, Self.counter % failEveryN == 0 {
            return CryAnalysis(recordingQuality: .tooNoisy, cryConfidence: 0.3,
                               intensity: 0.2, noiseLevel: 0.9,
                               durationSec: durationSec, hasPauses: false)
        }
        var rng = SystemRandomNumberGenerator()
        let intensity = Double.random(in: 0.35...0.85, using: &rng)
        return CryAnalysis(recordingQuality: .ok,
                           cryConfidence: Double.random(in: 0.9...0.99, using: &rng),
                           intensity: intensity,
                           noiseLevel: Double.random(in: 0.05...0.3, using: &rng),
                           durationSec: durationSec,
                           hasPauses: Bool.random(using: &rng))
    }
}

extension CryAnalysis {
    var intensityLabel: String {
        switch intensity {
        case ..<0.4: "强度较低"
        case ..<0.7: "强度中等"
        default: "强度较高"
        }
    }
}

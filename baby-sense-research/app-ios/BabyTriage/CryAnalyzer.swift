import Foundation

// M1b-1: 真实质量检测 + DSP 测量(无模型)。
// RealCryQualityAnalyzer = 时长/音量/信噪比 质量闸门 + RMS强度/停顿比;
// cryConfidence 暂用 ZCR 启发式占位 —— M1c 换 YAMNet/CoreML 时只动这一处。
// MockCryAnalyzer 供 -uitest 与单元测试(确定性, 不依赖真声音)。

struct CryAnalysis {
    var recordingQuality: RecordingQuality
    var cryConfidence: Double      // 0–1 (M1b 为启发式, M1c 换模型)
    var intensity: Double          // 0–1, RMS 归一 —— UI 必须中性呈现
    var noiseLevel: Double         // 0–1
    var durationSec: Double
    var hasPauses: Bool
}

protocol CryAnalyzing {
    func analyze(samples: [Float], sampleRate: Double) -> CryAnalysis
}

// MARK: - 真实现 (M1b-1 质量闸门 + M1c 模型哭声判定)

struct RealCryQualityAnalyzer: CryAnalyzing {
    /// M1c: CoreML 哭声检测器; nil 时回退 ZCR 启发式(测试合成信号 / 模型缺失)
    var detector: CryDetecting? = CryDetector.shared
    /// 低于此概率判 notCry(取保守值, 黄金集: 哭声0.97+/噪声0.0001)
    var cryThreshold: Double = 0.5

    func analyze(samples: [Float], sampleRate: Double) -> CryAnalysis {
        let duration = Double(samples.count) / sampleRate
        let frameLen = Int(sampleRate * 0.1)              // 100ms 帧
        guard frameLen > 0, samples.count >= frameLen else {
            return fail(.tooShort, duration: duration)
        }

        // 每帧 RMS + 过零率
        var rms: [Double] = []
        var zcr: [Double] = []
        var i = 0
        while i + frameLen <= samples.count {
            var sum = 0.0
            var crossings = 0
            var prev = samples[i]
            for j in i..<(i + frameLen) {
                let v = samples[j]
                sum += Double(v) * Double(v)
                if (v >= 0) != (prev >= 0) { crossings += 1 }
                prev = v
            }
            rms.append((sum / Double(frameLen)).squareRoot())
            zcr.append(Double(crossings) / Double(frameLen))
            i += frameLen
        }

        let sorted = rms.sorted()
        let noiseFloor = sorted[Int(Double(sorted.count) * 0.2)]
        let p90 = sorted[min(Int(Double(sorted.count) * 0.9), sorted.count - 1)]
        let peak = sorted.last ?? 0

        // 质量闸门(对应 v1 文案: 太短 / 太远 / 太吵)
        if duration < 3 { return fail(.tooShort, duration: duration) }
        if peak < 0.02 { return fail(.tooFar, duration: duration) }
        let snrDb = 20 * log10((p90 + 1e-9) / (noiseFloor + 1e-9))
        if snrDb < 8 { return fail(.tooNoisy, duration: duration, noise: noiseFloor) }

        // 测量(无对错): 活跃帧强度 + 停顿比
        let activeThresh = max(0.015, noiseFloor * 2.5)
        let activeIdx = rms.indices.filter { rms[$0] > activeThresh }
        let meanActive = activeIdx.isEmpty ? 0
            : activeIdx.map { rms[$0] }.reduce(0, +) / Double(activeIdx.count)
        let intensity = min(1.0, meanActive / 0.25)

        var hasPauses = false
        if let first = activeIdx.first, let last = activeIdx.last, last > first {
            let span = last - first + 1
            let inactive = span - activeIdx.count
            hasPauses = Double(inactive) / Double(span) > 0.15
        }

        // M1c: 真模型判定"是不是婴儿哭声"(YAMNet+训练头, 端侧 CoreML)
        let cryConfidence: Double
        if let prob = detector?.cryProbability(samples: samples) {
            cryConfidence = prob
            if prob < cryThreshold {
                return CryAnalysis(recordingQuality: .notCry, cryConfidence: prob,
                                   intensity: intensity, noiseLevel: min(1.0, noiseFloor / 0.05),
                                   durationSec: duration, hasPauses: hasPauses)
            }
        } else {
            // 回退: ZCR 启发式(仅模型不可用时)
            let activeZcr = activeIdx.isEmpty ? 0
                : activeIdx.map { zcr[$0] }.reduce(0, +) / Double(activeIdx.count)
            cryConfidence = (0.03...0.14).contains(activeZcr) ? 0.85 : 0.55
        }

        return CryAnalysis(recordingQuality: .ok,
                           cryConfidence: cryConfidence,
                           intensity: intensity,
                           noiseLevel: min(1.0, noiseFloor / 0.05),
                           durationSec: duration,
                           hasPauses: hasPauses)
    }

    private func fail(_ q: RecordingQuality, duration: Double, noise: Double = 0) -> CryAnalysis {
        CryAnalysis(recordingQuality: q, cryConfidence: 0, intensity: 0,
                    noiseLevel: min(1.0, noise / 0.05), durationSec: duration, hasPauses: false)
    }
}

// MARK: - Mock (UI 测试 / 单元测试)

struct MockCryAnalyzer: CryAnalyzing {
    /// >0 时每 N 次返回一次"太吵", 验证重录路径
    var failEveryN: Int = 5
    private static var counter = 0

    func analyze(samples: [Float], sampleRate: Double) -> CryAnalysis {
        Self.counter += 1
        let forceNoisy = ProcessInfo.processInfo.arguments.contains("-forceNoisy")
        if forceNoisy || (failEveryN > 0 && Self.counter % failEveryN == 0) {
            return CryAnalysis(recordingQuality: .tooNoisy, cryConfidence: 0.3,
                               intensity: 0.2, noiseLevel: 0.9,
                               durationSec: 8, hasPauses: false)
        }
        let dur = samples.isEmpty ? Double.random(in: 6...14)
                                  : Double(samples.count) / sampleRate
        return CryAnalysis(recordingQuality: .ok,
                           cryConfidence: Double.random(in: 0.9...0.99),
                           intensity: Double.random(in: 0.35...0.85),
                           noiseLevel: Double.random(in: 0.05...0.3),
                           durationSec: dur,
                           hasPauses: Bool.random())
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

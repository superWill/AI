import XCTest
@testable import BabyTriage

// M1b-1 验收: 真实质量检测(纯 DSP)的确定性测试 —— 合成信号, 不依赖真录音。

final class QualityAnalyzerTests: XCTestCase {

    private let sr: Double = 16_000
    // detector: nil —— 本组测的是 DSP 质量闸门, 合成正弦不该被模型(M1c)拦截
    private let analyzer = RealCryQualityAnalyzer(detector: nil)

    // 确定性伪随机(LCG), 保证测试可复现
    private struct LCG {
        var state: UInt64 = 42
        mutating func next() -> Float {
            state = state &* 6364136223846793005 &+ 1442695040888963407
            return Float(Double(state >> 33) / Double(UInt32.max)) * 2 - 1
        }
    }

    private func sine(freq: Double, seconds: Double, amp: Float) -> [Float] {
        (0..<Int(seconds * sr)).map { amp * Float(sin(2 * .pi * freq * Double($0) / sr)) }
    }

    private func noise(seconds: Double, amp: Float, rng: inout LCG) -> [Float] {
        (0..<Int(seconds * sr)).map { _ in amp * rng.next() }
    }

    /// 哭声样式: 1s 哭(450Hz) + 0.7s 停, 循环
    private func cryPattern(seconds: Double, amp: Float, noiseAmp: Float) -> [Float] {
        var rng = LCG()
        var out: [Float] = []
        while Double(out.count) / sr < seconds {
            out += sine(freq: 450, seconds: 1.0, amp: amp)
            out += noise(seconds: 0.7, amp: noiseAmp, rng: &rng)
        }
        return Array(out.prefix(Int(seconds * sr)))
    }

    func testTooShortRejected() {
        let a = analyzer.analyze(samples: sine(freq: 450, seconds: 1.5, amp: 0.4), sampleRate: sr)
        XCTAssertEqual(a.recordingQuality, .tooShort)
    }

    func testTooQuietRejectedAsTooFar() {
        let a = analyzer.analyze(samples: sine(freq: 450, seconds: 6, amp: 0.005), sampleRate: sr)
        XCTAssertEqual(a.recordingQuality, .tooFar)
    }

    func testNoisyRejected() {
        var rng = LCG()
        let bursts = cryPattern(seconds: 8, amp: 0.25, noiseAmp: 0.001)
        let loud = noise(seconds: 8, amp: 0.20, rng: &rng)
        let mixed = zip(bursts, loud).map(+)
        let a = analyzer.analyze(samples: mixed, sampleRate: sr)
        XCTAssertEqual(a.recordingQuality, .tooNoisy)
    }

    func testGoodCryAcceptedWithMeasures() {
        let a = analyzer.analyze(samples: cryPattern(seconds: 8, amp: 0.4, noiseAmp: 0.001),
                                 sampleRate: sr)
        XCTAssertEqual(a.recordingQuality, .ok)
        XCTAssertEqual(a.durationSec, 8, accuracy: 0.2)
        XCTAssertTrue(a.hasPauses, "1s哭/0.7s停的样式应检出停顿")
        XCTAssertGreaterThan(a.intensity, 0.2)
        XCTAssertLessThan(a.noiseLevel, 0.3)
    }

    func testIntensityMonotonic() {
        let soft = analyzer.analyze(samples: cryPattern(seconds: 6, amp: 0.08, noiseAmp: 0.001),
                                    sampleRate: sr)
        let loud = analyzer.analyze(samples: cryPattern(seconds: 6, amp: 0.5, noiseAmp: 0.001),
                                    sampleRate: sr)
        XCTAssertEqual(soft.recordingQuality, .ok)
        XCTAssertEqual(loud.recordingQuality, .ok)
        XCTAssertLessThan(soft.intensity, loud.intensity, "更响的哭声强度读数应更高")
    }
}

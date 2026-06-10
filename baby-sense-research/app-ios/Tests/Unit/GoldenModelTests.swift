import XCTest
import AVFoundation
@testable import BabyTriage

// M1c 黄金一致性: 同一段音频, 端侧(Swift mel + CoreML) 输出 ≈ 训练端(TF hub 全管线)。
// golden.json 由 baseline/export_coreml.py 生成; 期望: 哭声≈0.985, 噪声≈0.0001。

final class GoldenModelTests: XCTestCase {

    private struct Golden: Decodable { let file: String; let expected_prob: Double }

    private func loadGolden() throws -> [Golden] {
        let bundle = Bundle(for: GoldenModelTests.self)
        let url = try XCTUnwrap(bundle.url(forResource: "golden", withExtension: "json"),
                                "golden.json 应打进测试 bundle")
        return try JSONDecoder().decode([Golden].self, from: Data(contentsOf: url))
    }

    private func loadWav(_ name: String) throws -> [Float] {
        let bundle = Bundle(for: GoldenModelTests.self)
        let base = (name as NSString).deletingPathExtension
        let url = try XCTUnwrap(bundle.url(forResource: base, withExtension: "wav"))
        let file = try AVAudioFile(forReading: url)
        let fmt = AVAudioFormat(commonFormat: .pcmFormatFloat32,
                                sampleRate: file.fileFormat.sampleRate,
                                channels: 1, interleaved: false)!
        let buf = AVAudioPCMBuffer(pcmFormat: fmt,
                                   frameCapacity: AVAudioFrameCount(file.length))!
        try file.read(into: buf)
        XCTAssertEqual(file.fileFormat.sampleRate, 16_000, "黄金音频应为 16k")
        return Array(UnsafeBufferPointer(start: buf.floatChannelData![0],
                                         count: Int(buf.frameLength)))
    }

    func testModelsLoadable() throws {
        XCTAssertTrue(MelFrontend.available, "melmatrix.bin 应在 app bundle")
        XCTAssertNotNil(CryDetector.shared, "两个 mlpackage 应编译进 app bundle")
    }

    // 端侧概率 vs 训练端黄金值(容差含 fp16 量化 + 前端微差, python 预演差 0.011)
    func testGoldenConsistency() throws {
        let detector = try XCTUnwrap(CryDetector.shared)
        for g in try loadGolden() {
            let samples = try loadWav(g.file)
            let prob = try XCTUnwrap(detector.cryProbability(samples: samples),
                                     "\(g.file) 推理不应失败")
            XCTAssertEqual(prob, g.expected_prob, accuracy: 0.1,
                           "\(g.file): 端侧=\(prob) 训练端=\(g.expected_prob)")
        }
    }

    // 语义验收: 真哭声放行; 噪声被拒(白噪声会先撞 DSP 的 SNR 闸门=tooNoisy,
    // 这正是闸门顺序的正确行为——能通过 SNR 的非哭声才轮到模型判 notCry)
    func testAnalyzerAcceptsCryRejectsNoise() throws {
        let analyzer = RealCryQualityAnalyzer()   // 用真 detector
        let cry = analyzer.analyze(samples: try loadWav("golden_cry.wav"), sampleRate: 16_000)
        XCTAssertEqual(cry.recordingQuality, .ok)
        XCTAssertGreaterThan(cry.cryConfidence, 0.7)

        let noise = analyzer.analyze(samples: try loadWav("golden_noise.wav"), sampleRate: 16_000)
        XCTAssertNotEqual(noise.recordingQuality, .ok, "噪声不应被当成可分析的哭声")

        // 模型层语义: 绕过 DSP 闸门直接问模型, 噪声 cry 概率应极低
        let det = try XCTUnwrap(CryDetector.shared)
        let prob = try XCTUnwrap(det.cryProbability(samples: try loadWav("golden_noise.wav")))
        XCTAssertLessThan(prob, 0.3, "模型不应把噪声认成哭声")
    }
}

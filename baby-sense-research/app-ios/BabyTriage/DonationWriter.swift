import Foundation
import AVFAudio

// M1d 捐赠文件管理: 仅在用户单独同意后, 把会话内暂存的 16k 样本
// 压缩为 AAC(m4a) 存入沙盒 donations/ 目录(待上传队列)。
// 云端未建: 不联网、不自动上传; 档案页可一键全删。
// (PRD 提到 Opus; iOS 原生编码器无 Opus, 用 AAC 等效——上传协议定型时再统一)

enum DonationWriter {

    static var directory: URL {
        let base = FileManager.default.urls(for: .applicationSupportDirectory,
                                            in: .userDomainMask)[0]
        let dir = base.appendingPathComponent("donations", isDirectory: true)
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir
    }

    /// 样本 → AAC m4a; 返回文件名
    @discardableResult
    static func save(samples: [Float], sampleRate: Double = 16_000) throws -> String {
        let name = UUID().uuidString + ".m4a"
        let url = directory.appendingPathComponent(name)

        let fmt = AVAudioFormat(commonFormat: .pcmFormatFloat32, sampleRate: sampleRate,
                                channels: 1, interleaved: false)!
        let settings: [String: Any] = [
            AVFormatIDKey: kAudioFormatMPEG4AAC,
            AVSampleRateKey: sampleRate,
            AVNumberOfChannelsKey: 1,
            AVEncoderBitRateKey: 32_000,
        ]
        let file = try AVAudioFile(forWriting: url, settings: settings)
        let buf = AVAudioPCMBuffer(pcmFormat: fmt,
                                   frameCapacity: AVAudioFrameCount(samples.count))!
        samples.withUnsafeBufferPointer { src in
            buf.floatChannelData![0].update(from: src.baseAddress!, count: samples.count)
        }
        buf.frameLength = AVAudioFrameCount(samples.count)
        try file.write(from: buf)
        return name
    }

    static func pendingFiles() -> [URL] {
        (try? FileManager.default.contentsOfDirectory(at: directory,
                                                      includingPropertiesForKeys: nil)) ?? []
    }

    static func deleteAll() {
        for f in pendingFiles() { try? FileManager.default.removeItem(at: f) }
    }
}

import Foundation
import AVFAudio

// M1b-1 真录音: AVAudioEngine → 16kHz mono Float32, 仅内存, 最长 15s 自动停。
// -uitest / 单元测试 用 MockAudioRecorder, 不触发麦克风权限。

protocol AudioRecording: AnyObject {
    var onAutoStop: (() -> Void)? { get set }
    /// 申请权限并开始; completion(true)=已在录
    func requestPermissionAndStart(completion: @escaping (Bool) -> Void)
    /// 停止并返回 (16k mono 样本, 采样率)
    func stop() -> ([Float], Double)
}

final class MockAudioRecorder: AudioRecording {
    var onAutoStop: (() -> Void)?
    func requestPermissionAndStart(completion: @escaping (Bool) -> Void) { completion(true) }
    func stop() -> ([Float], Double) {
        ([Float](repeating: 0, count: 10 * 16_000), 16_000)   // 10s 静音占位
    }
}

final class RealAudioRecorder: AudioRecording {
    var onAutoStop: (() -> Void)?

    private let engine = AVAudioEngine()
    private let targetRate: Double = 16_000
    private let maxSeconds: Double = 15
    private var samples: [Float] = []
    private let lock = NSLock()
    private var converter: AVAudioConverter?
    private var autoStopped = false

    func requestPermissionAndStart(completion: @escaping (Bool) -> Void) {
        AVAudioApplication.requestRecordPermission { [weak self] granted in
            DispatchQueue.main.async {
                guard granted, let self else { return completion(false) }
                do { try self.startEngine(); completion(true) }
                catch { completion(false) }
            }
        }
    }

    private func startEngine() throws {
        samples.removeAll()
        autoStopped = false

        let session = AVAudioSession.sharedInstance()
        try session.setCategory(.record, mode: .measurement)
        try session.setActive(true)

        let input = engine.inputNode
        let inFmt = input.outputFormat(forBus: 0)
        guard let outFmt = AVAudioFormat(commonFormat: .pcmFormatFloat32,
                                         sampleRate: targetRate, channels: 1,
                                         interleaved: false),
              let conv = AVAudioConverter(from: inFmt, to: outFmt) else {
            throw NSError(domain: "rec", code: -1)
        }
        converter = conv

        input.installTap(onBus: 0, bufferSize: 2048, format: inFmt) { [weak self] buf, _ in
            guard let self, let conv = self.converter else { return }
            let ratio = self.targetRate / inFmt.sampleRate
            let cap = AVAudioFrameCount(Double(buf.frameLength) * ratio) + 16
            guard let out = AVAudioPCMBuffer(pcmFormat: outFmt, frameCapacity: cap) else { return }
            var fed = false
            var err: NSError?
            conv.convert(to: out, error: &err) { _, status in
                if fed { status.pointee = .noDataNow; return nil }
                fed = true; status.pointee = .haveData; return buf
            }
            guard err == nil, let ch = out.floatChannelData?[0] else { return }

            self.lock.lock()
            self.samples.append(contentsOf: UnsafeBufferPointer(start: ch, count: Int(out.frameLength)))
            let full = Double(self.samples.count) / self.targetRate >= self.maxSeconds
            let shouldFire = full && !self.autoStopped
            if shouldFire { self.autoStopped = true }
            self.lock.unlock()

            if shouldFire { DispatchQueue.main.async { self.onAutoStop?() } }
        }
        engine.prepare()
        try engine.start()
    }

    func stop() -> ([Float], Double) {
        engine.inputNode.removeTap(onBus: 0)
        engine.stop()
        try? AVAudioSession.sharedInstance().setActive(false, options: .notifyOthersOnDeactivation)
        lock.lock(); let s = samples; samples = []; lock.unlock()
        return (s, targetRate)
    }
}

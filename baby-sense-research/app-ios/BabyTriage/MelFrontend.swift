import Foundation
import Accelerate

// YAMNet 前端的 Swift 复刻(与训练端逐位对齐):
//   hann(periodic,400) → |rfft512| 幅度谱 → × melmatrix.bin(烘焙,257×64) → log(+0.001)
//   → 96帧 patch, hop 48; 不足一个 patch 时补零
// 烘焙 mel 矩阵 = tf.signal.linear_to_mel_weight_matrix 原值, 消除两端实现差。

enum MelFrontend {
    static let sampleRate = 16_000.0
    static let winLen = 400          // 25ms
    static let hop = 160             // 10ms
    static let fftLen = 512
    static let bins = 257
    static let melBands = 64
    static let patchFrames = 96
    static let patchHop = 48
    static let logOffset: Float = 0.001

    private static let window: [Float] = (0..<winLen).map {
        0.5 - 0.5 * cos(2 * .pi * Float($0) / Float(winLen))   // periodic hann(与 tf 一致)
    }

    private static let melMatrix: [Float] = {
        guard let url = Bundle.main.url(forResource: "melmatrix", withExtension: "bin"),
              let data = try? Data(contentsOf: url) else { return [] }
        return data.withUnsafeBytes { Array($0.bindMemory(to: Float.self)) }   // 257*64
    }()

    static var available: Bool { melMatrix.count == bins * melBands }

    /// 波形 → [N, 96, 64] log-mel patches(展平)
    static func patches(from samples: [Float]) -> (data: [Float], count: Int)? {
        guard available, samples.count >= winLen else { return nil }

        let setup = vDSP_DFT_zrop_CreateSetup(nil, vDSP_Length(fftLen), .FORWARD)
        guard let setup else { return nil }
        defer { vDSP_DFT_DestroySetup(setup) }

        var inReal = [Float](repeating: 0, count: fftLen / 2)
        var inImag = [Float](repeating: 0, count: fftLen / 2)
        var outReal = [Float](repeating: 0, count: fftLen / 2)
        var outImag = [Float](repeating: 0, count: fftLen / 2)
        var frame = [Float](repeating: 0, count: fftLen)
        var mags = [Float](repeating: 0, count: bins)

        var logmel: [Float] = []          // T * 64
        var t = 0
        var i = 0
        while i + winLen <= samples.count {
            // 加窗 + 补零到 512
            for j in 0..<winLen { frame[j] = samples[i + j] * window[j] }
            for j in winLen..<fftLen { frame[j] = 0 }

            // 实数 DFT(zrop): 偶数下标→real, 奇数→imag; 输出含 2× 缩放
            frame.withUnsafeBufferPointer { fp in
                inReal.withUnsafeMutableBufferPointer { re in
                    inImag.withUnsafeMutableBufferPointer { im in
                        var split = DSPSplitComplex(realp: re.baseAddress!, imagp: im.baseAddress!)
                        fp.baseAddress!.withMemoryRebound(to: DSPComplex.self, capacity: fftLen / 2) {
                            vDSP_ctoz($0, 2, &split, 1, vDSP_Length(fftLen / 2))
                        }
                    }
                }
            }
            vDSP_DFT_Execute(setup, inReal, inImag, &outReal, &outImag)

            // 幅度 |X|: 还原数学定义需 ×0.5; 打包格式 imag[0]=Nyquist
            mags[0] = abs(outReal[0]) * 0.5
            mags[bins - 1] = abs(outImag[0]) * 0.5
            for k in 1..<(fftLen / 2) {
                mags[k] = 0.5 * (outReal[k] * outReal[k] + outImag[k] * outImag[k]).squareRoot()
            }

            // × mel 矩阵 (257 → 64) + log
            for m in 0..<melBands {
                var acc: Float = 0
                for k in 0..<bins { acc += mags[k] * melMatrix[k * melBands + m] }
                logmel.append(Foundation.log(acc + logOffset))
            }
            t += 1
            i += hop
        }

        // 切 patch: 96 帧 / hop 48; 不足补零
        var out: [Float] = []
        var n = 0
        if t >= patchFrames {
            var j = 0
            while j + patchFrames <= t {
                out.append(contentsOf: logmel[(j * melBands)..<((j + patchFrames) * melBands)])
                n += 1
                j += patchHop
            }
        } else {
            out = logmel + [Float](repeating: Foundation.log(logOffset),
                                   count: (patchFrames - t) * melBands)
            n = 1
        }
        return (out, n)
    }
}

import Foundation
import CoreML

// M1c 端侧哭声检测: MelFrontend → YAMNetEmbedding.mlpackage(逐patch 1024维)
//                  → 均值池化 → CryHead.mlpackage → cry 概率。
// 与训练端同一权重(YAMNet官方 h5 + baseline/train_l1_model.py 训的头),
// 一致性由 GoldenModelTests 用黄金音频把关。

protocol CryDetecting {
    func cryProbability(samples: [Float]) -> Double?
}

final class CryDetector: CryDetecting {
    static let shared: CryDetector? = CryDetector()

    private let embModel: MLModel
    private let headModel: MLModel

    init?() {
        guard let embURL = Bundle.main.url(forResource: "YAMNetEmbedding", withExtension: "mlmodelc"),
              let headURL = Bundle.main.url(forResource: "CryHead", withExtension: "mlmodelc"),
              let emb = try? MLModel(contentsOf: embURL),
              let head = try? MLModel(contentsOf: headURL),
              MelFrontend.available else { return nil }
        embModel = emb
        headModel = head
    }

    func cryProbability(samples: [Float]) -> Double? {
        guard let (patchData, n) = MelFrontend.patches(from: samples), n > 0 else { return nil }

        guard let inArr = try? MLMultiArray(shape: [NSNumber(value: n), 96, 64],
                                            dataType: .float32) else { return nil }
        patchData.withUnsafeBufferPointer { src in
            inArr.dataPointer.bindMemory(to: Float.self, capacity: patchData.count)
                .update(from: src.baseAddress!, count: patchData.count)
        }

        guard let embOut = try? embModel.prediction(
                from: MLDictionaryFeatureProvider(dictionary: ["mel_patches": inArr])),
              let embArr = embOut.featureValue(for: embOut.featureNames.first ?? "")?.multiArrayValue
        else { return nil }

        // 均值池化 [n,1024] → [1,1024]
        guard let pooled = try? MLMultiArray(shape: [1, 1024], dataType: .float32) else { return nil }
        let e = embArr.dataPointer.bindMemory(to: Float.self, capacity: n * 1024)
        let p = pooled.dataPointer.bindMemory(to: Float.self, capacity: 1024)
        for d in 0..<1024 {
            var acc: Float = 0
            for r in 0..<n { acc += e[r * 1024 + d] }
            p[d] = acc / Float(n)
        }

        guard let headOut = try? headModel.prediction(
                from: MLDictionaryFeatureProvider(dictionary: ["embedding": pooled])),
              let prob = headOut.featureValue(for: headOut.featureNames.first ?? "")?.multiArrayValue
        else { return nil }
        return Double(truncating: prob[0])
    }
}

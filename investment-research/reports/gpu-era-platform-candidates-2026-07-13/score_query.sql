WITH candidate_scores(company, archetype, score, evidence, confidence) AS (
  VALUES
    ('NVIDIA', 'Microsoft型平台', 9.4, 'CUDA开发生态、全云覆盖与企业软件栈', 'MED'),
    ('NVIDIA', 'Intel型算力标准', 9.8, 'GPU、NVLink、网络与整机系统规模', 'HIGH'),
    ('OpenAI', 'Microsoft型平台', 9.0, '模型、API、ChatGPT、Codex与开发者入口', 'MED'),
    ('OpenAI', 'Intel型算力标准', 3.5, '自研芯片刚起步且采用多芯片策略', 'LOW'),
    ('Microsoft', 'Microsoft型平台', 8.7, 'Azure、Foundry、Office、GitHub与企业分发', 'HIGH'),
    ('Microsoft', 'Intel型算力标准', 4.5, 'Maia已部署但主要服务内部云', 'MED'),
    ('Alphabet', 'Microsoft型平台', 8.3, 'Gemini、Vertex、Android、Workspace与Cloud', 'MED'),
    ('Alphabet', 'Intel型算力标准', 6.5, '十年TPU路线但主要通过Google Cloud交付', 'MED'),
    ('Amazon', 'Microsoft型平台', 7.8, 'AWS、Bedrock与企业云采购入口', 'MED'),
    ('Amazon', 'Intel型算力标准', 6.8, 'Trainium部署规模大但局限AWS', 'MED'),
    ('AMD', 'Microsoft型平台', 5.5, 'ROCm改善但生态控制力有限', 'MED'),
    ('AMD', 'Intel型算力标准', 7.8, '商用第二供应商与CPU/GPU组合', 'MED'),
    ('Meta', 'Microsoft型平台', 6.8, 'PyTorch、Llama与大众应用分发', 'MED'),
    ('Meta', 'Intel型算力标准', 4.2, 'MTIA规模扩大但主要内部使用', 'LOW'),
    ('Broadcom', 'Microsoft型平台', 3.5, '不控制通用开发者接口', 'HIGH'),
    ('Broadcom', 'Intel型算力标准', 7.2, '定制ASIC、网络与多客户设计能力', 'MED')
)
SELECT company, archetype, score, evidence, confidence
FROM candidate_scores;

# 内存墙：谁可能推倒它——三条路线的调研与记分

日期：2026-11-04
前置：本日 `notes/2026-11-04-ai-roadmaps-who-drew-them.md` 的推论——AI 进程里最深的物理墙是「搬数据比算数据贵 100 倍」的内存墙。本笔记回答：谁在推、推到哪、什么时候可能倒。
方法：三路并行调研（堆叠/内存厂路线、光与新架构路线、软件路线），一手 = P、二手 = S，2026-02 后事实全部网页核实。详细逐条出处见各节表格末尾「来源」。

---

## 一、结论

**到 2028 年没有人推倒它；它正在被绕过去，而不是被推倒。** `[INFERRED, MED-HIGH]`

1. **带宽/算力比在恶化，不是在改善。** 英伟达自己的路线：每 FP4 FLOP 的字节数 B200 0.8 → Rubin 0.44 → Rubin Ultra 0.32，每代掉约 45%。HBM 没有在追，只是勉强守住 Rubin 这条线。`[COMPUTED, HIGH]`
2. **内存厂的路线是「管理」墙：** HBM4 → 4E → 5，每比特能耗到 2028 约 ÷2、到 2030 约 ÷3；混合键合被推迟（JEDEC 把封装高度上限从 775 放宽到 900–1000 µm，等于撤掉了做混合键合的压力）；4F² 三星 2028 量产、真 3D DRAM 约 2030；美光说 4F²「不在路线图上」。**唯一真正减少搬运字节数的路线是存内计算（PIM），而它没有一个数据中心客户。**
3. **光没有在 2028 年前碰到内存。** 机架内 NVLink 到 2028 年 Feynman 之前全是铜；Celestial 的光学 HBM 池化 2027 年底才有首笔收入；光计算全球营收最高水位是 RMB 1,900 万（曦智）。光在 2026–28 年做的是机架之间的交换机。
4. **真正在绕墙的是系统层：按字节住在哪里重新分工。** 解码的 FFN 放进片上 SRAM（Groq 3 LPX，每芯片 150 TB/s，英伟达 $200 亿买的就是这个）、注意力和 KV 留在 HBM、预填充放到 GDDR/HBM4 CPX、Dynamo 调度。英伟达的路线图不是在破墙，是在承认墙并重新切分负载。
5. **软件已经吃掉了最大的那几口。** KV 缓存每 token 字节数三年 ÷450（MLA → DSA → CSA/HCA，全部 DeepSeek），权重到 FP4，MoE 稀疏比在 25–33× 处**平台化**。到 2028 年固定能力下还有 3–8× 的空间，但推理模型的 token 膨胀（前沿运行成本每年涨 3–18×）把它吃掉大半，**每个有用答案的净字节数 2028 年前只能降 1–3×**。软件把带宽问题转成了容量 + 互连问题。
6. **因此「推墙的人」按概率排**：① 英伟达（同时拥有 SRAM/HBM/GDDR 三层 + 调度器，2026 下半年就出货）；② Google（TPU 8i 每 FLOP 字节数是 Rubin 的 2 倍 + OCS 光交换 + 模型协同设计，但封闭）；③ Marvell（Celestial 光学 HBM 池化 + Lumentum 激光器，2028–30 的期权）；④ 三星（唯一有 16 层 VS-DRAM 硅片 + 自家基底的内存厂，2028–30）。**内存墙最可能的终局不是一个人推倒，是「墙还在，但大家不再从墙那里走」。**

---

## 二、三条路线的现状

### A. 堆叠 / 内存厂路线

| 项 | 现状（2026-11） | 判定 |
|---|---|---|
| HBM4 | SK 海力士「量产与出货全面展开」，Q4'26 量和收入超 HBM3E；三星 2026-02 通过英伟达/AMD 认证首发（1c DRAM + 自家 4nm 基底，10.7 Gb/s）；美光 11 Gb/s、>2.8 TB/s/stack，Rubin 量产 | 出货中 |
| HBM4E | SK 海力士 12 层样品（2026-06）：48 GB、16 Gb/s ≈ 4 TB/s/stack、能效 +20%，**仍是 MR-MUF 不是混合键合**，2027 量产；三星 12 层样品 2026-05 | 样品 |
| 混合键合 | 两家韩厂 HBM4/4E 都留在 TC/MR-MUF；「最早」16 层 HBM4E 或 20 层 HBM5；SK 海力士：只在良率 90–98% + 3–5 年寿命时采用；JEDEC 讨论 HBM5 高度 900→1000 µm | 推迟 |
| 每比特能耗 | 无厂商公布 pJ/bit；按厂商相对值复合：HBM3E ≈3.5–4 → HBM4E ≈1.7–2 pJ/bit `[COMPUTED, LOW-MED]`；对照：TSMC 有源 D2D 0.36 pJ/b、Intel Foveros Direct <0.05 | 2030 ≈ ÷3 |
| 定制 HBM / 基底逻辑 | TSMC+GUC C-HBM4E：基底 N3P、0.75 V、12.8 GT/s（2027）；Marvell 定制 HBM 声称接口功耗 −70%、腾出 25% XPU 面积——**降的是接口能耗（约占 HBM 能耗 1/3），不减少搬运字节** | 2027 |
| 3D DRAM | 三星：10a 用 4F²+VCT（IGZO），2026 开发 → 2027 认证 → **2028 量产**，密度 +30–50%；VLSI 2026 有 16 层 VS-DRAM 论文（无密度/成本数字）；真 3D「从 10d 起」≈2030。SK 海力士：先延长 6F²，4F²「看经济性」无日期。**美光：4F²「不在路线图上」，20 年研究没找到可持续路径**。SAIMEMORY（软银+Intel+力积电）ZAM：原型 2027、商用 2030 | 2028–30 |
| DRAM 直接堆在 GPU 上 | HBM 仍用微凸点接中介层；TSMC 要求供应商 ~5 µm 凸点、2H28 量产（S，LOW）；无任何已核实的 2026 公告；1–2 kW 逻辑芯片上堆 DRAM 的热问题无厂商给出日期 | 无 |
| PIM | 三星 LPDDR5X-PIM（Hot Chips 2026）：内部 614 GB/s vs 外部 76.8 GB/s（8×），Llama-3.1-8B 3× tok/s，定位边缘；SK 海力士 AiMX 展品；HBM-PIM（2021）从未规模出货。原因：无标准编程模型、功耗突发、超大厂只买 JEDEC 标准件 | 无 DC 客户 |
| 替代内存 | Vera CPU 16× SOCAMM2 LPDDR5X 1.5 TB/1.2 TB/s（出货）；**Rubin CPX（GDDR7 预填充）在 GTC 2026 从路线图消失**，被 Groq 3 LPX 取代，郭明錤称改成 168 GB HBM4 版 2027（LOW）；CXL 池化仍在试点；MRAM/FeRAM/ReRAM 与 2030 前的带宽墙无关 | — |
| 带宽/FLOP（×10⁻³ B/s per FLOP/s） | FP8：H100 1.69 → B200 1.78 → Rubin 1.11（−38%）；FP4：B200 0.89 → GB300 0.53 → Rubin 0.55 → Rubin Ultra ~0.5 | **平到更差** |
| 中国 | CXMT HBM3 量产目标滑坡，良率 10–30%；DRAM 份额 8→10%；华为 950DT 配 HiZQ 2.0（144 GB、4 TB/s，S）无独立核实 | 落后两代 |
| 产能 / 售罄 | SK 海力士「HBM/DRAM 售罄至 2029」，LTA 覆盖 2027–28 产能 >50%，M15X 2026 底满产，龙仁 2027-02 搬入设备；三星 P5 提前半年开工（~2030 运营）；美光 FY26 capex $273.7 亿、ID1 2027、ID2 2028、广岛 HBM 2028；份额 Q2'26：SK 50% / 三星 33% / 美光 18% | 短缺到 2029–30 |

**路线 A 判定**：2028 年两项指标（≥3× 每字节能耗或 ≥3× 带宽/FLOP）都做不到；2030 年每字节能耗 ≈ ÷3 可能（HBM5 + N3 基底 + 混合键合），带宽/FLOP 仍 <1.5×。三星是唯一有 3D 硅片 + 自家基底 + 份额上升的内存厂，排第一；SK 海力士第二（更稳，天花板更低）；美光不是推墙的人。

### B. 光 / 新架构路线

| 项 | 现状（2026-11） | 判定 |
|---|---|---|
| Celestial AI → Marvell | 2025-12 宣布，$32.5 亿首付 + 最高 $22.5 亿 earnout（累计收入 ≥$5 亿 / >$20 亿），2026-02 交割。Photonic Fabric：16 Tb/s 单向/芯粒，2.4 pJ/bit 电 + 0.7 pJ/bit 激光，chip-to-memory <200 ns，EAM 调制器耐 >85°C。「被一家一线超大厂选中做下一代 XPU 扩展网络」，AWS 拿 100 万股认股权。**收入从 FY28 下半年（≈2027 年底）开始，Q4 FY28 $5 亿年化、Q4 FY29 $10 亿** | 2027 底首收入 |
| Ayar Labs | 2026-03 E 轮 $5 亿、估值 $37.5 亿（英伟达/AMD/联发科）；<5 pJ/bit；2024 底出货 ~1.5 万件；无 2026 客户/量 | 小批量 |
| Lightmatter | 估值 $44 亿（2024-10），无 2026 新融资；自家路线：NPO 2026 → CPO 2027 → 光子中介层 2028 → **Envise 光计算「2030+」**；加入 NVLink Fusion；无具名客户 | 转向互连 |
| 其他 | Xscape（8 波长激光，$81M A 轮）、Enlightra（梳状激光，2027 试产）、Nubis 被 Ciena $2.7 亿收购、Avicena（microLED，无量产） | 早期 |
| 英伟达 CPO | Spectrum-X 以太网光子交换机 2026-08「全面量产」（TSMC COUPE，激光器少 4×、功耗 −5×）；Quantum-X 小批量；**2026-03 投 Lumentum $20 亿 + Coherent $20 亿**并签多年采购 | 交换机，非内存 |
| 英伟达光 NVLink | GTC 2026：Rubin NVL72 铜；Rubin Ultra Kyber NVL144（2027）铜，NVL576 仅机架间 CPO；**Feynman（2028）NVL1152 首次「铜 + CPO 同时扩展」**。NVLink6 官网 3.0 TB/s/GPU（GTC 说的 3.6）——静悄悄下修 | 机架内铜到 2028 |
| Broadcom | TH6-Davisson 102.4T CPO 出货（2025-10）；TH7 200T 流片；**激光器「需求远超供给」，InP 产能「翻三倍以上」**；AI 收入 FY26 $580 亿 → FY27 ~$1,150 亿 → FY28 ~$2,300 亿；Anthropic：Ironwood 1 GW（2026）/ TPU 8i 5 GW（2027）/ +10 GW（2028） | 激光器是瓶颈 |
| TSMC COUPE | 一代 1.6T 2026 量产，二代 6.4T 2027 | 按期 |
| **SRAM 路线：Groq 3 LPX（英伟达）** | 2025-12 英伟达 ~$200 亿非独占授权 + 创始人入职；GTC 2026：LP30 ~500 MB SRAM、**150 TB/s/芯片**、1.2 PF FP8、三星 4nm；256 LPU/机架、128 GB SRAM、640 TB/s；**注意力-FFN 分离**（Rubin 跑注意力/KV，LPU 跑 FFN/MoE，Dynamo 调度）；「每 MW 吞吐 35×」（厂商口径）；2026 下半年出货（未核实）；LP35（Rubin Ultra）、LP40（Feynman） | 2026H2 |
| Cerebras | 2026-05 IPO（$185，募 $63.8 亿）；2025 收入 $5.1 亿（两客户 86%）；FY26 核心收入指引 $8.55–8.65 亿；CS-4：3 片 WSE-3 Turbo、**44 GB SRAM/片自 2024 年未变**、129.6 PB/s；tokens/$ 比 GB200 贵（$0.75 vs $0.50/M）——快，不便宜 | 快不便宜 |
| d-Matrix / Etched / Positron / SambaNova / Tenstorrent | d-Matrix Raptor（DRAM 堆在 SRAM 计算片上）2026 底流片、2027Q4 可用，加入 NVLink Fusion；Etched $103 亿估值、「>$10 亿预订」、**无出货确认**；Positron Asimov 2027H2（LPDDR5X 无 HBM）；SambaNova $110 亿；Tenstorrent $62 亿。2026 真实收入：Cerebras ≫ SambaNova（~$1 亿）> 其余 | 2027H2 前无新增量 |
| 超大厂自研 | Google TPU 8t（216 GB、6.5 TB/s、9,600 芯片超级 pod、2 PB HBM）/ 8i（288 GB、8.6 TB/s、价格性能 +80%）；AWS Trainium3 GA（144 GB、4.9 TB/s），Trainium4 HBM 带宽 4×；**Microsoft Maia 300（2026-10）：288 GB HBM4、18 TB/s、13.8 PF FP4，每 FP4 FLOP 字节数 1.30 = 公开最高**，HBM「提前 5 年订」；Meta MTIA 400/450/500，3 GW 到 2028 | 字节/FLOP：Maia 300 1.30 > TPU 8i 0.85 > Trainium3 ~0.97 > Rubin 0.44 > Rubin Ultra 0.32 |
| 光计算 | Lightmatter Envise 2030+；曦智港股 IPO 首日 +383%、市值 ~$100 亿，**2025 收入 RMB 1.06 亿、光计算 H1'26 仅 RMB 1,910 万**；Q.ANT NPU 2 出货给欧洲三家 HPC；Mythic 无 2026 消息 | 无实质营收 |
| 资本流向 | 2025–26 大额：Marvell–Celestial $32.5 亿+、Nvidia–Groq ~$200 亿、Nvidia→Lumentum/Coherent $40 亿、Marvell–Lumentum EV $1,150 亿、Ayar $5 亿、Cerebras IPO、SambaNova $10 亿、Etched $3 亿、Positron $8.75 亿、Tenstorrent $15 亿。**在位者买的是激光器和 SRAM 解码引擎，零美元投向光计算** | — |

**路线 B 判定**：2028 年前能提供 ≥3× 系统级缓解的是**英伟达自己**（LPX + Dynamo + CPX），不是光子厂商；Google TPU 8i + OCS 第二（OCS 是拓扑不是内存带宽）；Marvell（Celestial + Lumentum）是 2028–30 唯一拥有「光学 HBM 池化硅片 + 自有激光厂 + 一线客户设计中标」的组合；Lightmatter/Ayar/曦智 2030 前不构成变量。

### C. 软件路线

| 项 | 数字 | 状态 |
|---|---|---|
| KV 缓存每 token 字节 | 2023 MHA（GPT-3 结构）4.7 MB → Llama-2-70B GQA 320 KB → DeepSeek V3 MLA 70 KB（FP8 ≈35 KB）→ **V4-Pro CSA/HCA ≈10 KB（bf16）、FP8/FP4 ≈5 KB**；累计 ÷450–900 | 部署 |
| 2026 开源前沿的注意力结构 | Kimi K3：93 层中 69 层线性注意力（KDA）+ 24 层 MLA；Qwen3.8：69 线性 + 23 全注意力（3:1）；V4：CSA（4× 序列压缩）+ HCA（128×）交替 | 部署 |
| 权重精度 | FP8 训练（V3，2024-12）→ **FP4 前沿部署**：V4-Pro 专家 FP4（≈800 GB）、Kimi K3 MXFP4 QAT（2.8T ≈1.4 TB）、Qwen3.8 NVFP4；英伟达 NVFP4 预训练 12B/10T token 与 FP8 持平；三值 BitNet 仅 2B 级 | FP4 到位 |
| MoE 稀疏比（总/激活） | Mixtral 3.6× → V3 18× → Llama 4 24× → Kimi K2 31× → V4-Pro 33× / K3 27× / Qwen3.8 25× ——**2026 年平台化在 25–33×**；MoE 减的是 FLOPs 和把成本转到 HBM 容量 + 互连（EP），批量服务下几乎所有专家每步都被触碰，**字节节省来自批处理不是稀疏** | 平台 |
| 解码技巧 | EAGLE-3 批量 1 时 6.5×、批量 ≥24 时 1.3×；MTP（V3 接受率 85–90%，~1.8×；Qwen3.8 2.4×）；扩散 LM（Mercury 3 宣称 1,068 tok/s，OpenRouter 实测 160–254）非前沿质量 | 批量下 1.3–2× |
| 服务系统 | MLPerf v6.0（2026-04）同一 GB300 NVL72 六个月：DeepSeek-R1 2,907 → 8,064 tok/s/GPU（2.77×，一次性成熟，非稳态；Lambda 跨硬件控制只归软件 ~9%）；SemiAnalysis 实测 V4-Pro FP4 在 GB300：$0.07/M token 峰值吞吐；DeepSeek 2025-02 披露**前缀缓存命中 56.3%**（唯一一手）；Anthropic 缓存命中价 $0.25 vs 基价 $10（40×） | 部署 |
| 固定能力价格 | GPT-4 级 2023 $30/$60 → 2026 $0.10–0.40/M 输出（150–600×）；Epoch：中位 50×/年；Gundlach 等（2026-03）：固定基准价格每年 ÷5–10，剔硬件后算法 ≈3×/年，**但前沿模型运行成本每年涨 3–18×**（更大模型 + 推理 token） | 两条曲线反向 |
| 反趋势 | Artificial Analysis：Grok 4.6 xhigh 一题 7,500 万 token（$1.04）vs GPT-6 Astra 440 万 token（$0.93）——相近 $/题下 token 量差 17×；**推理强度取代 $/token 成为成本主变量** | — |
| 天花板 | 权重：Allen-Zhu 约 2 bit/参数知识容量，FP4（含缩放 4.25 bit）只剩 ~1.5–2×；KV：已在 128× 序列压缩，再有 2–5× 就会伤召回；算法效率 ≈3×/年（Epoch 自己说单一速率「没意义」） | 大口已吃完 |

**路线 C 判定**：固定能力下 2028 年前软件还能把每 token 字节数降 3–8×（KV 2–4×、权重 1.3–2×、投机/MTP 1.5–2×、缓存命中 56→75% ≈1.3×）；**每个有用答案净降 1–3×，前沿 agent 负载可能持平**。软件把带宽墙转成容量墙 + 互连墙——对 HBM 容量字节数是利好，对带宽/token 增速是温和利空。推手：DeepSeek（架构，三代 KV 开源）、英伟达（服务栈，Dynamo/TRT-LLM/FA4）；Google DeepMind 封闭、不可知。

---

## 三、合成：墙会怎么「消失」

三路放在一起看，内存墙的解法不是一项技术，是**字节的重新分址**：

```
2024（Blackwell）   全部字节住在 HBM：权重 + KV + 上下文
2026（Rubin + LPX） FFN 权重 → 片上 SRAM（150 TB/s）；KV/注意力 → HBM；预填充 → GDDR/HBM4 CPX；Dynamo 分派
2027（Rubin Ultra） HBM4E 1 TB/GPU、带宽/FLOP 继续降；Celestial 光学 HBM 池化首收入；三星 4F² 认证
2028（Feynman）     定制 HBM + 3D 堆叠 + 机架间 CPO；三星 4F² 量产；混合键合进 16 层 HBM4E（若良率达标）
2030                HBM5 + 混合键合 + N3 基底 ≈ 每字节能耗 ÷3；真 3D DRAM 首批；光学内存池化成为标准件
```

每一步都没有「推倒」墙（带宽/FLOP 仍在降），每一步都让更少的字节需要穿过墙。**所以「墙倒那天」不存在，存在的是「墙变得不重要的那几年」，大约 2028–2030。**

### 对上一条讨论的修正

- 我在 11-04 聊天里说「光互连吃的是从现在到墙倒那几年的肉，墙倒那天是它利润率顶点」——前半句成立，后半句的前提（有一个「墙倒那天」）不成立。更准确：光在 2026–28 年吃的是**机架间交换**的肉（Spectrum-X/TH6），**光学内存**要到 2028–30 才是营收，而那时它面对的是 SRAM 解码引擎已经分走了一半需求的市场。
- 「内存厂在墙倒前吃肉、墙倒后失势」——因为墙不倒而是被绕，**HBM 的短缺和定价权比「墙倒」剧本持续得更久**（售罄至 2029、LTA 锁 2027–28 过半产能），但增长的驱动从「带宽」转向「容量字节数」（FP4 的 800 GB 权重要常驻、KV 要池化）。

---

## 四、记分：谁最可能推（绕）墙

| 排名 | 谁 | 凭什么 | 时间 | 物理限制 | 置信 |
|---|---|---|---|---|---|
| 1 | **英伟达** | 唯一同时拥有三层内存（SRAM/HBM/GDDR）+ 调度器 + $200 亿买来的 SRAM 引擎；LPX 2026H2 出货 | 2026–28 | SRAM 密度（500 MB/片）迫使 256 芯片分片；机架内铜到 2028 | HIGH 出货 / MED ≥3× 系统级 |
| 2 | **Google** | TPU 8i 字节/FLOP 是 Rubin 2 倍；OCS 唯一量产的光子织网；Gemini 与芯片协同设计；Anthropic 5 GW 承诺 | 2026–27 | OCS 是拓扑不是带宽；HBM4 供给 | HIGH 量产 / LOW「光学内存」 |
| 3 | **Marvell（Celestial + Lumentum）** | 唯一的光学 HBM 池化硅片（16 Tb/s、<200 ns、3.1 pJ/bit）+ 自有激光厂 + 一线客户中标 | 首收入 2027 底，$10 亿年化 2029 | 激光器可靠性/供给、EAM 在 3 kW 封装里的热、光子中介层良率 | MED |
| 4 | **三星** | 唯一有 16 层 VS-DRAM 硅片 + 4F² 10a 2028 量产 + 自家 4nm/2nm 基底 + 份额 21→33% | 2028–30 | 1c/10a 良率；VS-DRAM 位成本能否在 2030 前打败 6F² | MED-LOW |
| 5 | **DeepSeek** | 三代 KV 架构开源（÷450），唯一披露缓存命中率的实验室 | 持续 | KV 再压伤召回；算力受限 | HIGH 过去 / MED 未来 |
| 6 | SK 海力士 | HBM 龙头，但路线最保守（6F² 延长、混合键合设门槛） | 2029 HBM5 | 自设 90–98% 良率门槛 | MED |
| 7 | Microsoft Maia 300 | 公开最高字节/FLOP 1.30 | 2027，仅内用 | HBM 提前 5 年订 | MED |
| — | 美光 | 份额跌到 18%、无 3D 程序、基底外包 | — | 产能 2027–28 | 不是推墙者 |
| — | Lightmatter / Ayar / 曦智 / Q.ANT | 2030 前无具名客户或无实质营收 | 2030+ | — | LOW |

---

## 五、对组合的含义与开奖日

- **NVDA**：论点加强——它不是「等墙倒的人」，是绕墙路线的拥有者。11/18 看 LPX/Dynamo 的任何量化数据（每 MW token）。
- **MRVL**：Lumentum 交易的逻辑与本笔记一致（光学内存 2028–30 的期权 + 激光器稀缺）；但本笔记也说明在那之前 SRAM 引擎会先分走一半解码需求，Celestial 的 $10 亿年化目标（2029）是证伪线。
- **MU / SKHY（不持有）**：「墙倒内存厂失势」的剧本不成立，短缺持续到 2029–30；但增长驱动从带宽转到容量，估值逻辑要换。
- **CRWV / ORCL（算力出租层）**：2028 年前不会被「每 token 成本崩塌」打到，它们的风险仍是融资结构（⑥-a/⑥-c），不是技术替代。
- **四触发器**：本笔记不改变读数（0/4）。

**开奖日 / 证伪条件**
1. 2026Q4–2027Q1：Groq 3 LPX 实际出货 + 第三方 tokens/MW 数据 → 若 ≥3× 对 VR NVL72 成立，排名 1 坐实；若延期或 <1.5×，SRAM 路线降级。
2. 2027-03 GTC：Feynman 的定制 HBM/3D 规格与字节/FLOP；NVLink7 是否再次下修。
3. 2027 年底：Celestial 首笔收入与具名一线客户；Marvell 若 FY28 没有 Celestial 收入 → 排名 3 失效。
4. 2027：三星 10a/4F² 认证通过与否；SK 海力士 16 层 HBM4E 是否上混合键合。
5. 2027：DeepSeek V5 级 KV 字节/token 是否再 ÷3 而召回不降；AA 的 $/题曲线是否继续被推理 token 抵消。
6. 任何一家超大厂宣布 DRAM 直接混合键合在加速器芯片上并给出量产日期 → 整张表重排。

**我不知道的**：各厂 pJ/bit 一手数（全是相对值复合）；Groq 3 LPX 是否已出货；Celestial 的客户是谁；三星 VS-DRAM 的位成本；Google 内部的 KV/服务栈。

---

## 六、来源（主要）

- 堆叠：SK 海力士 Q3'26（koreatimes 2026-10-28）、HBM4E 样品（trendforce 2026-06-18）、SEMI 面板（heraldcorp 2026-09-20）；三星 ISSCC 2026 15.6（via SemiAnalysis）、VLSI 2026 T5.1（mynavi）；美光 FQ4'26 8-K（sec.gov 0000723125-26-000018）、DeBoer（trendforce p=65842）；Counterpoint 2026-09-02；JEDEC 775→1000 µm（trendforce 2026-07-07）；SAIMEMORY ZAM（convergedigest）；Nvidia GB300/VR NVL72 官网规格。
- 光/架构：Marvell–Celestial PR + 10-K（sec.gov 1835632）；Celestial Hot Chips 2025（convergedigest）；Marvell Q1 FY27（convergedigest）；Ayar E 轮（businesswire 2026-03-03）；Lightmatter llms.txt；Nvidia Spectrum-X 量产（storagereview）、Lumentum/Coherent 投资（siliconangle 2026-03-02）、GTC 2026（SemiAnalysis、technews）、nvidia.com/nvlink；Broadcom TH6 PR + Q3 FY26 transcript；Groq 3 LPX（storagereview、theregister）；Cerebras Q2'26 8-K（sec.gov 2021728）；d-Matrix Raptor（nextplatform）；Google TPU 8（hpcwire、servethehome）；Maia 200/300（techcommunity、notebookcheck）；曦智 IPO（caixin）。
- 软件：DeepSeek V3.2（arXiv 2512.02556）、V4（HF 模型卡、arXiv 2606.19348、vllm.ai 博客）、推理系统披露（github open-infra-index）；Kimi K3、Qwen3.8 模型卡/vLLM recipe；NVFP4 预训练（arXiv 2509.25149）；BitNet（arXiv 2504.12285）；EAGLE-3（arXiv 2503.01840）；MLPerf v6.0（developer.nvidia.com）；SemiAnalysis InferenceX 2026-05-27；Gundlach 等「Price of Progress」（arXiv 2511.23455）；Epoch 推理价格趋势；Anthropic 定价页。

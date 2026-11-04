# 模拟物理世界：世界模型 / 神经模拟器的公司、卡点与可投性

日期：2026-11-04
起因：用户判断「接下来发展的应该是模拟物理世界的游戏，也就是 Meta 放弃的」。本笔记核三件事：Meta 放弃的到底是什么；谁在攻这个方向、卡在哪；公开市场有没有标的。
方法：一路调研 + Meta 单独核。P = 一手，S = 二手；2026-02 后事实网页核实。

---

## 一、先纠正前提：Meta 放弃的是什么 `[KNOWN, HIGH]`

| 时间 | 事件 | 放弃的层 |
|---|---|---|
| 2025-10 | 超级智能实验室裁约 600 人（FAIR/产品 AI/基建），做 LLM 的 TBD Lab 未动 | **开放式长周期世界模型研究线** |
| 2025-11-19 | LeCun 宣布离开 | 同上 |
| 2026-01 | Reality Labs 裁约 10%（~1,500 人），转向可穿戴，关闭工作室 | 元宇宙产品 |
| 2026-03 | 再裁约 700 人，「从元宇宙创作转向」 | 元宇宙产品 |
| 2026-06-15 | Horizon Worlds VR 关闭（后部分收回，保留 Quest 现有内容） | 元宇宙产品 |
| 保留 | V-JEPA 2 权重（2025-06）；但 **V-JEPA 2.1 是 AMI Labs 发的，不是 Meta** | — |

结论：Meta 同时退出了「作为研究的世界模型」和「作为产品表面的元宇宙」，2026 年没有任何 Meta 世界模型产品。**这个方向被它的前首席科学家带出去单独做了**（AMI Labs，$10.3 亿种子，$35 亿投前，2026-03），LeCun 对 BBC 说年底前打磨、工业应用「希望」2027，无产品无客户。

所以用户的判断「Meta 放弃的方向」成立，但要补一句：放弃它的是 Meta，接手的是 LeCun + 一批融了 $30 亿以上的初创公司 + Google/Nvidia。

---

## 二、谁在做（按「真实卡点 × 有没有收入」排）

### A. 前沿实验室（初创公司要追赶的基准）

| 谁 | 最新 | 卡点自述 | 状态 |
|---|---|---|---|
| **Google Genie 4**（2026-10-27，P） | 首个带原生音频的实时世界模型；可在模拟中途用文字改场景；Gemini 3.8 Flash 当「导演」逐帧检查；Apptronik Apollo 下棋演示 | 博客自己承认「长会话中物体恒存性会漂移」；**没公布帧率/分辨率/延迟**；一致性约 2 分钟（二手，是 Genie 3 的两倍） | 仅信任测试者 |
| **Nvidia Cosmos 3 + Isaac Lab 3.0 + Newton**（GTC 2026-03 / 台北 2026-06，P） | Cosmos 3 = 推理专家 + 生成专家的混合 transformer，全模态含动作；GR00T N2 预览；FANUC/ABB/安川/KUKA（200 万台机器人装机）接 Omniverse；「Cosmos 联盟」6 家 | 自称开源模型里 Physics-IQ/PAI-Bench 第一 | 开源，无收入数字 |
| **OpenAI** | **2026-03-24 关闭 Sora 消费应用和 API**，理由是转向机器人/世界模拟；下载量 11 月到 2 月跌 66% | 无任何模拟产品或演示 | 只有声明 |
| **Tesla World Simulator** | 一个动作条件的生成视频网络，FSD 和 Optimus 共用，「泛化到室内」 | 零公开指标 | 内部 |

### B. 初创公司

| 公司 | 攻的卡点 | 证据 | 融资 | 状态 |
|---|---|---|---|---|
| **World Labs**（李飞飞） | **持久性靠显式 3D 状态**（高斯泼溅世界），不靠视频记忆——唯一绕开漂移问题的可信路线 | Marble 2025-11 GA；World API 2026-01；R2S2R（2026-07-28，P）：ALOHA 装箱策略**零真实数据**迁移，5 个策略各自主 1 小时；**只声称保留排序，不给成功率** | $10 亿（2026-02，Autodesk $2 亿，Nvidia/AMD）；估值谈 ~$50 亿 | 产品 + API，收入未披露 |
| **Decart** | **实时延迟 + 商品算力**（自研推理栈 DOS） | Oasis 3（2026-06，P）：22 fps @ 512×768、<200 ms、三路同步相机、动作条件，面向自动驾驶，跑在 B200 上；「无限长」但无记忆指标 | $3 亿（2026-05，~$40 亿；Nvidia/Adobe/丰田） | **有收入**（DOS 授权，自称盈利，未审计）；传 $60–70 亿被收购（未核） |
| **Odyssey**（Oliver Cameron） | 实时 + 物理 | Odyssey-3 预览（2026-10）：自报 Physics-IQ 66.1 未复现；Odyssey 2 **每个 API 用户要一张 H200** | $3.1 亿 B 轮（2026-06，$14.5 亿；Amazon/AMD/GV） | 演示；单位经济极差 |
| **Runway** | 世界模型当**策略评估器** | GWM-Robotics：8 个策略的模拟 vs 真实 Pearson 0.95（排序不是绝对值，P） | $3.15 亿 E 轮（2026-02，$53 亿） | 视频产品 + 机器人评估 beta |
| **Wayve**（Alex Kendall） | **安全论证能接受的闭环验证** | GAIA-4（2026-08，P）：生成相机 + 雷达（多普勒），「轨道上的世界」vs 反应式智能体，干预的反事实回放；**用于验证不用于训练数据**；无真实-模拟相关系数 | ~$12 亿（2026-02，$86 亿；奔驰/Stellantis/日产/微软/Nvidia/软银） | 日产 ProPILOT FY2027、Uber 东京试点 2026 底 |
| **Waabi** | 全在模拟里开发验证 | 「Waabi Driver 主要在 Waabi World 里开发和验证」；Uber ≥25,000 辆 | $7.5 亿 C 轮（2026-01，Khosla） | 无人商业化未确认 |
| **Applied Intuition** | 不是神经模拟，是**确定性/日志回放** | ARR 估 $8.3 亿（2025，~2×，毛利 ~80%，Sacra 估）；国防线对 Anduril | $150 亿（2025-06）；2026-10 传 ≥$300 亿报价未成交 | **唯一有九位数收入的模拟公司** |
| Helm.ai | 生成式模拟 | 12 个月 $7,000 万签约合同，「走向盈亏平衡」 | — | 合同 |
| Lightwheel（光轮智能） | 模拟数据生产 | 自报 Q1 2026 ~$1 亿订单；宇树 H1 在吉利工厂 100 模拟 : 1 真实轨迹；与 Nvidia 共建 Newton（三星线缆机器人） | RMB 10 亿（2026-03） | 中国最好的模拟数据收入证据 |
| Skild / Physical Intelligence / Generalist / Genesis AI | 模拟的**消费者**，不是建造者 | Skild 在 Isaac Lab 预训练（$140 亿）；PI 是 VLA 没有模拟产品（$110 亿，谈 $200 亿）；Generalist 用 Cosmos 合成数据（$20 亿）；Genesis AI 谈 $5 亿未交割 | — | 不算模拟公司 |
| **AMI Labs**（LeCun） | 物理世界模型作为下一代预训练底座 | V-JEPA 2.1；无产品无客户 | $10.3 亿种子（2026-03，$35 亿投前） | 2027「希望」有工业应用 |
| 生成式游戏引擎（微软 Muse/WHAM、Dynamics Lab Mirage、Etched Oasis 1） | 可玩的神经游戏 | Muse ≤2 分钟、2025 后无更新；Mirage 2 控制不稳、2026 无消息；**2026 年没有任何商业可玩的神经游戏**，全是研究预览 | — | 停滞 |

### C. 中国

| 谁 | 事实 | 性质 |
|---|---|---|
| **群核 Manycore（0068.HK）** | 2026-04-17 上市，首日 +144%，市值 ~HK$316 亿；H1 2026 收入 ¥4.05 亿 +1.5%，**经营亏损 ¥8,200 万**，AI 新产品收入 ¥3,100 万（<8%），**SpatialVerse 订单 ¥680 万** | 酷家乐是业务，世界模型是叙事 |
| 昆仑万维 Matrix-Game | 3.5（2026-07）：5B、720p 20 fps 单卡、1 分钟记忆、开源；**4.0（2026-10-15）：混合架构——游戏引擎持有状态、视频模型渲染**，480p/60 fps/<150 ms（RTX 5090） | 开源演示，股价跟发布跳 |
| 腾讯 HY-World 2.0 | 2026-04 开源，输出 mesh/3DGS 进 Unity/UE | 无变现 |
| 极佳视界 GigaAI | 2026 年 3–6 月融 ~¥35 亿，自称投后 ~$30 亿；GigaWorld-1 自报 WorldArena 第一；否认港股 IPO | 演示 |
| 影眸 Rodin | 数亿元（2026-06），80% 海外，客户字节/Unity/Figma/Canva | **3D 资产生成，不是模拟** |
| MiniMax / 阶跃 / 商汤 / 智源 | 无 2026 世界模型产品 | 营销 |

---

## 三、卡点：2026 年的证据说什么 `[KNOWN, HIGH]`

| 卡点 | 2026 证据 | 判定 |
|---|---|---|
| **(a) 物理一致性** | WorldBench（arXiv 2601.21282，v2 2026-08）：「所有测试的 SOTA 视频世界模型都缺乏真实交互所需的物理一致性」；WoW-World-Eval 最高物理一致性 68/100；**Physics-IQ Verified（2026-06）发现原基准 57.6% 样本要修、模型排名变动（Kendall τ=0.46）——基准本身不可靠** | 未解 |
| **(b) 长周期记忆** | Genie 3 ~1 分钟 → Genie 4 ~2 分钟且自认漂移；Matrix-Game 3.5 1 分钟；Muse 2 分钟；WoW 长周期规划 17/100。**没有人演示过「小时」级。** 2026 年的集体答案是混合架构：把状态交回经典引擎（Matrix-Game 4.0、Roblox、Unity CEO）——**这是撤退不是解决** | 最远 |
| **(c) 实时** | Decart 22 fps@512×768 <200 ms；昆仑 60 fps@480p <150 ms（混合）；Roblox 内部 16 fps@832×480；Genie 3 24 fps@720p；Odyssey 一用户一张 H200 | 720p+ 多用户实时在经济上未解 |
| **(d) 模拟到真实** | 全领域**只有一个干净的绝对数**：零样本世界-动作模型在 Franka 上 35% 平均成功率（800 合成演示/任务，CVPR'26 workshop）；其余全是相对增益（WoVR +22.3 分）或排序相关（Runway 0.95）或自报（Skild 60–80%，Lightwheel 100:1） | 几乎没有可比数据 |
| **(e) 评测** | Physics-IQ、WorldBench、WoW、WorldScore、WorldArena、PAI-Bench、RoboArena——**没有一个 2026 共享榜单让 Genie/Cosmos/Odyssey/Decart 同台**，前沿实验室不提交 | 无法横比 |

---

## 四、经济学：谁在付钱

- **付钱的顺序**：自动驾驶 OEM/robotaxi（Applied ~$8.3 亿、Wayve–日产/Uber、Helm $7,000 万、Decart 面向 AV）≫ 机器人实验室（Lightwheel $1 亿订单、Nvidia 伙伴名单）≫ 国防（Applied）≫ **游戏工作室（外部支出 ≈ 零；Roblox/Unity/腾讯自建或开源）**。
- **有收入的神经模拟公司**：Decart（未审计）、Lightwheel（订单）、Helm（合同）。World Labs / Odyssey / Runway 机器人线 / AMI：无披露收入。
- **两派论点**：「世界模型是下一个预训练底座」（LeCun、李飞飞「From Words to Worlds」）vs「视频模型放大就是世界模型」（Google Genie 4、Nvidia「生成式训练设施」、OpenAI 关了消费端 Sora 但留了团队）。**Sutton 在 WAIC 2026 拆了像素模拟派的台**：世界模型是状态转移的「知识」，「我不认为我们需要物理模拟」。
- **2026 年的市场裁决**：资本两边都投（上半年世界模型初创 >$30 亿），**客户去了确定性/混合的验证器**（Applied、Wayve GAIA-4「验证不训练」）。

### 对用户「物理世界的游戏」判断的修正 `[INFERRED, MED-HIGH]`
- 方向对：模拟物理世界是 LLM 之后最明确的新底座之争，钱和人都在往这里去。
- 「游戏」这个载体错了：**2026 年没有一个商业可玩的神经游戏**，游戏工作室外部支出接近零；付钱的是自动驾驶和机器人，用途是**验证和合成数据**，不是娱乐。Genie 4 的演示对象是机器人（Apollo），不是玩家。
- 技术上最远的那一步（长周期记忆 + 接触物理）恰好是「游戏」最需要的——所以游戏会是这个方向**最后**成熟的应用，不是最先。

---

## 五、可投性 `[INFERRED, MED]`

**没有上市的纯标的。**

| 层 | 标的 | 真实性 |
|---|---|---|
| 收费站 | **NVDA**（Cosmos 3 / Isaac Lab / Newton / Omniverse；上面每家初创都在它的 GPU 和框架上训练；联盟 6 家） | 真资产，但对 P&L 不可见 |
| 最强模型 | **GOOGL**（Genie 4） | 真资产，零变现 |
| 内部使用 | TSLA（不可核）、RBLX（内部 16 fps + Cube 4D，产品相邻）、0700.HK（HY-World 开源无变现）、MSFT（Muse 休眠） | 真但小 |
| 间接股权 | ADSK（World Labs $2 亿）、AMZN（Odyssey/Decart/PI + AWS）、AMD（AMD Ventures 在 World Labs/Odyssey/Runway/Luma）、日产/Uber（Wayve/Waabi） | 四舍五入 |
| 叙事载体 | **0068.HK 群核**（SpatialVerse ¥680 万订单 vs HK$316 亿市值）、**300418 昆仑万维**（开源演示拉股价）、U Unity（Project Genie 发布当天下跌，「追赶世界模型」） | 不是 |
| 未来 IPO 管道 | Applied Intuition（$300 亿报价）、Wayve（$86 亿）、Skild（$140 亿）、PI（$110–200 亿）、Decart（传被收购） | **第一批带审计模拟收入的 S-1 会来自这里** |

**判定**
1. 2028 年前最可能真正解掉一个难题的三家：**Wayve**（OEM 安全论证能接受的多模态闭环验证，GAIA-4 已被当测量工具、OEM 出钱）、**Decart**（商品成本上的持续实时交互模拟，护城河是推理栈且已变现）、**World Labs**（用显式 3D 状态做持久性，唯一绕开视频漂移的路线）。Applied Intuition 是最确定的生意，但它解的不是神经问题。
2. 离解决最远的：**2 分钟以上的长周期记忆 + 接触/流体物理一致性**。最好的基准分 17–68/100，Google 自己承认漂移，行业 2026 年的办法是把状态还给经典引擎。模拟到真实只有一个绝对数（35%）。
3. 公开市场的诚实答案：**通过本来就持有的 NVDA 和 GOOGL 持有这个主题**，间接股权当零，不碰群核/昆仑这类叙事载体，等 Applied Intuition / Wayve 的 S-1——那是第一次能看到审计过的模拟收入。

### 写进 forward-direction-plan 的一行
T6 模拟物理世界：方向成立、载体（游戏）未到、公开市场无纯标的；通过 NVDA/GOOGL 持有；盯 Applied/Wayve S-1；群核/昆仑/Unity 不进清单。

---

## 六、我不知道的

Genie 4 的帧率/分辨率；Decart 被收购是否属实及对价；Genesis AI 的 $5 亿是否交割；松延/宇树的模拟栈；Dynamics Lab 2026 状态；World Labs 和 Odyssey 的真实收入。

## 七、来源（主要）
Google Genie 4 博客（deepmind.google 2026-10-27）· Nvidia GTC 2026 新闻稿 / Cosmos 3（investor.nvidia.com 2026-06-01）· Engadget/9to5 Sora 关闭（2026-03-24）· Reuters via StreetInsider（Meta 600 人）· eWeek（Reality Labs 1,500 人）· TechSpot（Horizon Worlds）· TechCrunch AMI（2026-03-09）· World Labs R2S2R 博客（2026-07-28）· Bloomberg World Labs（2026-01-23）· Decart Oasis 3（decart.ai 2026-06-10）· SiliconANGLE Decart $3 亿 · TechCrunch Odyssey（2026-06-17）· Runway E 轮 + GWM-Robotics 研究页 · Wayve GAIA-4（wayve.ai 2026-08-03）· eWeek Wayve $12 亿 · CP24 Waabi · Kyodo Applied F 轮 · Sacra Applied 估算 · Robot Report Helm · EqualOcean Lightwheel · 同花顺 群核 H1 / 昆仑 Matrix-Game 4.0 · cntechpost HY-World 2.0 · arXiv 2601.21282 / 2601.04137 / 2606.18943 / 2606.31101 / 2602.13977 · Roblox newsroom 2026-02 · KuCoin Sutton WAIC 2026 · Fortune 2026-05-20。

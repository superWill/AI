# driver-monitor — 单路 IVG-G4H 离线疲劳驾驶预警

> 目标平台:**BL412B-SOM412**(RK3568J / 4×A55@1.8G / 4GB / 32GB eMMC / 1 TOPS NPU / Ubuntu 20.04)。  
> 摄像头:**IVG-G4H**(GK7205V210)IP 机,经 Ethernet/RTSP 接入,不接 X23/Y 板。  
> 方案与阶段:见 `../docs/bl412b-drowsiness-detection-claude-handoff.md`。  
> 本目录与供热网关 `../heating/` **完全隔离**,不动任何热源安全控制逻辑。

> **视觉安防复用(换热站/消防站)**:同一视觉栈正被复用为「人员安防 + 火情可视复核」。
> 能力与权限边界见 [`docs/adr/0001-vision-security-boundaries.md`](docs/adr/0001-vision-security-boundaries.md)。
> - **P0**(`src/motion/`):运动检测 + episode 状态机,只产 `motion_episode` 事实。
> - **P1a**(`src/vision/confirm.py`+`person_detector.py`+`src/roi/`,离线已落地):**运动门控**
>   人体确认(NPU 只在有动静时跑)+ K/M 时间持久性 + ROI,把 motion 升级为 `person_observation`。
>   蒸汽(有 motion 无 person)不产事件;真人产 `person_observation`。
> - **P2a**(`src/record/`,离线已落地):录像段环形存储 + 事件→片段映射。证据不静默覆盖
>   (淘汰序:未 pin→已 delivery→未确认 pin 段永不删)、pre-roll 地板、两阶段确认(custody≠delivery)、
>   evidence_status(core 段丢=unavailable / 缺口=partial)。person_observation 事件挂回证据引用。
> - **P2c-a**(`src/uplink/`,离线已落地):事件上行纯逻辑——自足事件包、durable outbox
>   两阶段托管(custody≠delivery,幂等/优先级/存储转发)、四级运营分类(缓存工单窗,不确定→
>   unverified、永不 confirmed)、通知升级(只升通知等级)。设计见 [`docs/design/p2c-uplink.md`](docs/design/p2c-uplink.md)。
> - **P1b 进行中**(`src/vision/yolov8_person.py`):yolov8n 后处理(DFL box 解码 + person-only
>   过滤 + NMS)照 rknn_model_zoo 写完,纯 numpy 离线可测(4 tests,不需要 rknnlite/板子)。
>   `.rknn` 模型已转换(Docker x86_64 + rknn-toolkit2 2.3.2,COCO 官方 20 图 INT8 校准)并部署上板,
>   `RKNNLite` load/init/inference 板上验证通过(2026-07-03)。**待做:真实摄像头检出效果 + 吞吐基准
>   (测时摄像头断电,恢复供电后测)**;IR 夜间召回实测(ADR F3)在此之后。
> - **待做**:P2b(splitmuxsink 实机录像接入 `SegmentSource`);P2c-b(paho-mqtt 接 `UplinkTransport`);
>   P2c-c(platform 契约对接:topic/QoS/ack 语义/工单缓存下发,见设计文档 §11)。
>
> 视觉**只到 `person_observation`(事实)**,永不产 intrusion/confirmed;不确定只升优先级不改分类。

## 架构(目标态)

```text
IVG-G4H RTSP H.264/265
 → camera-worker(RTSP/解码/重连/帧时间戳)
 → vision-worker(RGA 预处理 + RKNN 人脸检测/关键点;模型健康)
 → drowsiness-engine(EAR/MAR/PERCLOS/头姿 → 时间窗 → 状态机)   ← 已实现,纯逻辑
 → event-adapter(蜂鸣/HMI/本地日志/MQTT 事件)
```

四进程隔离是**目标态**(视频/AI 失败不阻塞其它循环)。当前 `scripts/run_live.py` 是**单进程多阶段**
原型:推理异常已收敛为 MODEL_FAULT、流错误触发重连,但尚未拆成独立进程。连续视频帧不进点表/MQTT
遥测;密码不进代码/Git/日志。

## 目录

| 路径 | 内容 | 现状 |
|---|---|---|
| `src/drowsiness/engine.py` | 疲劳状态机(EAR/MAR/PERCLOS/头姿 → 时间窗 → 状态机) | ✅ 实现 + **11 tests** |
| `src/vision/features.py` | 关键点 → EAR/MAR/近似头姿(纯数学,CPU 侧) | ✅ 实现 + **7 tests** |
| `src/event/adapter.py` | 事件去抖/周期重报 + JSONL 日志 + 可插拔 sink | ✅ 实现 + **6 tests** |
| `src/motion/episode.py` | **视觉安防 P0** — motion episode 迟滞状态机(纯逻辑,OPEN/CLOSE/强制收尾) | ✅ 实现 + **16 tests** |
| `src/motion/detector.py` | **视觉安防 P0** — 滑动平均背景差运动检测(numpy) | ✅ 实现 + **5 tests(需 numpy)** |
| `src/motion/pipeline.py` | **视觉安防 P0** — 单摄粘合(detector+episode+相机健康+cam_id),多摄的处理单元 | ✅ 实现 + **7 tests** |
| `scripts/replay.py` | 离线回放/联调(特征轨迹 → 整链 → 状态时间线+事件) | ✅ 跑通(合成剧本触发 alarm 并恢复) |
| `scripts/replay_motion.py` | **视觉安防 P0** — 合成帧回放(空场→白块横穿→空场,验 OPEN/CLOSE) | ✅ 跑通(需 numpy) |
| `scripts/run_motion_live.py` | **视觉安防 P0** — 实机入口:单/多摄 RTSP→运动检测→episode→存证(无需模型/NPU) | ⏳ 待上板取证 |
| `src/vision/person_detector.py` | **视觉安防 P1a** — 人体检测接口 + 离线 Mock | ✅ 实现 + **4 tests** |
| `src/vision/yolov8_person.py` | **视觉安防 P1b** — yolov8n 真 RKNN 人体检测(DFL 解码+person-only 过滤+NMS,纯 numpy 离线可测) | ⏳ 实现 + **4 tests**,模型已上板 load/init/inference 通,**真机检出+吞吐待测**(摄像头断电) |
| `src/roi/mask.py` | **视觉安防 P1a** — 每摄多边形 ROI 掩膜(过滤区外框/运动) | ✅ 实现 + **6 tests** |
| `src/vision/confirm.py` | **视觉安防 P1a** — 运动门控 + 人体确认(K/M 持久性)升级状态机 → person_observation | ✅ 实现 + **12 tests** |
| `scripts/replay_confirm.py` | **视觉安防 P1a** — 两幕回放(蒸汽不产 person / 真人产 person_observation) | ✅ 跑通(+ 5 端到端 tests) |
| `src/record/segment_source.py` | **视觉安防 P2a** — 录像段接口 + 离线 Fake(真 splitmuxsink 留 P2b) | ✅ 实现 + **5 tests** |
| `src/record/ring.py` | **视觉安防 P2a** — 段环形存储:淘汰序/pre-roll 地板/两阶段确认/健康告警 | ✅ 实现 + **9 tests** |
| `src/record/clip.py` | **视觉安防 P2a** — 事件→段区间映射 + ClipManifest(evidence_status) | ✅ 实现 + **8 tests** |
| `scripts/replay_record.py` | **视觉安防 P2a** — 录制回放(真人产 clip / 缺口=partial / 蒸汽不产 clip) | ✅ 跑通(+ 5 端到端 tests) |
| `src/uplink/envelope.py` · `transport.py` | **视觉安防 P2c-a** — 自足事件包 + 上行传输接口 + 离线 Fake | ✅ 实现 + **10 tests** |
| `src/uplink/outbox.py` | **视觉安防 P2c-a** — durable 上行 outbox:两阶段托管/幂等/优先级/存储转发/健康 | ✅ 实现 + **12 tests** |
| `src/uplink/classify.py` · `workorder_cache.py` · `escalate.py` | **视觉安防 P2c-a** — 四级运营分类 + 工单缓存 + 通知升级 | ✅ 实现 + **16 tests** |
| `scripts/replay_uplink.py` | **视觉安防 P2c-a** — 上行回放(分类/两阶段托管/断网存储转发/通知升级) | ✅ 跑通(+ 5 端到端 tests) |
| `scripts/check_platform.sh` | **P0** 实机能力取证(RKNN/MPP/RGA 是否可用) | ✅ 板上验证过(RKNN/MPP/RGA 库齐全) |
| `scripts/rtsp_probe.py` | **P1** 摄像头 RTSP 探测(codec/分辨率/fps + soak) | ✅ 可发板子跑 |
| `src/camera/gst_source.py` | **P1** GStreamer MPP 硬解 RTSP 取流封装 | ✅ 板上验证过(真机取流) |
| `src/vision/retinaface.py` | **P3** RetinaFace(mobilenet)RKNPU 推理 + 后处理(人脸框+5 关键点) | ✅ 板上验证过(真机 90% 检出率) |
| `src/vision/pfld.py` | **P3** PFLD98 稠密关键点(EAR/MAR 用,当前 Path A 未接入) | ✅ 实现,未接入 run_live.py |
| `src/vision/pipeline.py` | **P3** FacePipeline(RetinaFace 整合) | ✅ 板上验证过 |
| `scripts/run_live.py` | **P3** 整链实时入口:RTSP→MPP 硬解→RetinaFace→头姿→疲劳状态机→事件落地 | ✅ 板上端到端跑通(90% 检出率) |
| `scripts/landmarks_test.py`·`decode_probe.py`·`capture_burst.py`·`snapshot.py` | 板上调试/标定工具 | ✅ 可发板子跑 |
| `config/*.example.json` | 阈值 / 摄像头配置示例(无真实密码) | ✅ |
| `models/RetinaFace_mobile320.rknn`·`pfld_landmark_rk3568.rknn` | RKNN 模型产物(gitignore,已手动部署到板子) | ✅ 板上已验证可推理 |
| `models/yolov8n.rknn` | P1b 人体检测模型(rk3568 INT8,4.8MB) | ✅ 已转换 + 已部署上板,推理链路验证通过 |

**已验证的部分(2026-07-03 板上实机):** P0(RKNN/MPP/RGA 齐全)+ P0.5(RKNNLite load/init/inference 全通)
+ P1(RTSP 真机取流)+ P3(RetinaFace 端到端,摆正摄像头角度后 90% 检出率,124 帧稳定无崩溃)。
离线部分:疲劳(特征换算 + 状态机 + 事件落地 + 离线回放)+ 视觉安防 P0/P1a/P1b(后处理)/P2a/P2c-a,
共 **156 tests** 全绿(151 纯标准库 + 5 需 numpy)。P1b 卡模型转换(见上),P2/P4/P5 见下方阶段进度。

## 快速验证(Mac,无需板子)

```bash
# 纯逻辑测试(标准库,任意 python3):疲劳链 + 视觉安防 P0 episode + P1a 门控/确认
for t in test_engine test_features test_event_adapter \
         test_motion_episode test_motion_pipeline \
         test_roi_mask test_person_detector test_confirm test_confirm_pipeline \
         test_segment_source test_segment_ring test_clip_manager test_record_pipeline \
         test_envelope test_workorder_cache test_classify test_escalate \
         test_uplink_transport test_outbox test_uplink_pipeline; do
  python3 tests/$t.py
done
python3 scripts/replay.py --events      # 合成疲劳剧本走一遍整链(清醒→困倦→微睡→恢复)
python3 scripts/replay_confirm.py       # P1a 两幕:蒸汽不产 person / 真人产 person_observation
python3 scripts/replay_record.py        # P2a 录制:真人产 clip / 缺口=partial / 蒸汽不产 clip
python3 scripts/replay_uplink.py        # P2c-a 上行:分类/两阶段托管/断网存储转发/通知升级

# 视觉安防 P0 中依赖 numpy 的部分(运动检测 + 帧回放)——用带 numpy 的解释器
python3.10 tests/test_motion_detector.py
python3.10 scripts/replay_motion.py --evidence /tmp/motion-evidence   # 白块横穿 → OPEN/CLOSE + 存证 PNG
```

## 视觉安防 P0 上板(BL412B,需摄像头)

一台 BL412 + 摄像头即可跑,**不需要模型 / 不用 NPU**(运动检测是纯 numpy;人体确认是 P1)。

```bash
# 单摄(密码走环境变量,不写盘)
export CAM_RTSP='rtsp://admin:@192.168.1.217:554/user=admin&password=&channel=1&stream=1.sdp'
python3 scripts/run_motion_live.py --seconds 60 --evidence ~/motion-evidence

# 多摄:每路一根线程,各自独立背景模型 + episode,一路故障不拖垮其它路
python3 scripts/run_motion_live.py --seconds 120 \
    --cam front=rtsp://admin:@192.168.1.217:554/... \
    --cam yard=rtsp://admin:@192.168.1.218:554/...
```

现场先看两件事:**①RTSP 是否稳定出帧**(帧计数在涨);**②真实场景误报率**(蒸汽/指示灯/
夜视抖动会不会狂发 OPEN)。误报高就调 `--diff / --fg-ratio / --n-enter` 或加 ROI 屏蔽(后续)。

> **多摄是 ADR-0001 单摄 MVP 的扩展**:硬件切分(④)针对的是「视觉板 vs 认证消防链板」的
> 故障隔离,与几路摄像头正交。多摄仍需记录**每路各自的覆盖盲区**(`无告警 ≠ 无人`)。

## 发到 BL412B 上跑

```bash
# 1) 整目录拷到板子(示例,实际 IP/账号待确认)
rsync -av --exclude __pycache__ ./ user@192.168.1.110:~/driver-monitor/

# 2) P0 取证(板子上)
ssh user@192.168.1.110 'cd ~/driver-monitor && bash scripts/check_platform.sh'
#   → 生成 docs/p0-platform-*.txt,据此判 RKNN/MPP/RGA 是否齐备

# 3) P1 摄像头(板子上,密码走环境变量,不写盘)
export CAM_RTSP='rtsp://admin:***@192.168.1.110:554/0'
python3 scripts/rtsp_probe.py                 # 主码流 codec/分辨率/fps
python3 scripts/rtsp_probe.py --soak 1800     # 30 分钟连拉,记断流/重连
```

## 阶段进度(对照 handoff §4)

- **P0** 实机能力取证 — ✅ 板上验证(librknnrt.so/librockchip_mpp.so.1/librga.so.2 + /dev/mpp_service 齐全)
- **P0.5** NPU spike — ✅ 2026-07-03 板上验证(RKNNLite load_rknn+init_runtime+inference 全通,
  librknnrt 2.3.2/Driver 0.9.8/target rk3568)
- **P1** 摄像头 + RTSP — ✅ 板上验证(IVG-G4H H.265 子码流真机取流,GStreamer MPP 硬解)
- **P2** CPU 基线 — 跳过(直接上 P3 NPU 推理,未单独测 CPU 基线性能)
- **P3** 迁移 RKNN(RetinaFace,**非 MediaPipe**) — ✅ 2026-07-03 板上端到端跑通,摆正摄像头俯角后
  检出率 90%(112/124 帧),状态机全程稳定无异常转移。PFLD 稠密关键点已实现但未接入 run_live.py
  (当前 Path A 只用 RetinaFace 5 点做头姿,EAR/MAR 待后续接稠密关键点)
- **P4** 疲劳状态机接入实时特征 — ✅ run_live.py 里已接(Path A:仅头姿信号驱动状态机)
- **P5** 可靠性(白天/夜间/遮挡 + 24h)— 待(IR 夜间召回见 P1b ADR F3)

**P1b(人体检测,安防复用轨道)单独进度**:后处理代码 + 单测 + 模型转换/上板推理验证全部完成,
待真机检出效果与吞吐基准(摄像头恢复供电后测)。

## 能力现状与性能门禁(2026-07-03 与外部评审对齐的共识)

已实现:ROI(`src/roi/mask.py`,7 tests)· RetinaFace 320 单模型链路(实测 ~8.3 fps)。
未实现:RGA 硬件预处理(两条路径都是 CPU 缩放:run_live 走 GStreamer videoscale,
yolov8_person 走 numpy)· 目标跟踪 · 越线方向 · 停留时长 · 人数统计。
UNKNOWN:YOLOv8n 640 真机吞吐(像素量是 320 的 4 倍,8.3 fps 不能外推)· 双模型并发性能
· 与正常业务共存时的隔离能力。

**门禁:先完成 YOLOv8n 单模型板端基准(检出+fps+CPU/内存/温度),再决定是否接双模型和 RGA;
在此之前不新增分析算法模块(跟踪/越线/停留/人数)。**

## 红线

不改热源安全逻辑;不提交密码/RTSP URL;不假设 RKNN/MPP/RGA 可用(用命令证明);实测前不承诺帧率;视频流不进 MQTT 遥测主题。

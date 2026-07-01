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
> - **待做**:P1b(yolov5n/8n 量化 rknn 接入 `PersonDetector`、IR 夜间召回实测,ADR F3);
>   P2(四级分类上行,依赖 RK3506 缓存与 MQTT)。
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
| `src/vision/person_detector.py` | **视觉安防 P1a** — 人体检测接口 + 离线 Mock(真 RKNN 留 P1b) | ✅ 实现 + **4 tests** |
| `src/roi/mask.py` | **视觉安防 P1a** — 每摄多边形 ROI 掩膜(过滤区外框/运动) | ✅ 实现 + **6 tests** |
| `src/vision/confirm.py` | **视觉安防 P1a** — 运动门控 + 人体确认(K/M 持久性)升级状态机 → person_observation | ✅ 实现 + **12 tests** |
| `scripts/replay_confirm.py` | **视觉安防 P1a** — 两幕回放(蒸汽不产 person / 真人产 person_observation) | ✅ 跑通(+ 5 端到端 tests) |
| `scripts/check_platform.sh` | **P0** 实机能力取证(RKNN/MPP/RGA 是否可用) | ✅ 可发板子跑 |
| `scripts/rtsp_probe.py` | **P1** 摄像头 RTSP 探测(codec/分辨率/fps + soak) | ✅ 可发板子跑 |
| `config/*.example.json` | 阈值 / 摄像头配置示例(无真实密码) | ✅ |
| `src/vision/`(RKNN 推理) `src/camera/`(RTSP/MPP/RGA) | 需板子的 worker | ⏳ 待 P0/P1 取证后写(P3) |
| `models/` | onnx 源 + rknn 产物 | ⏳ P3(rknn 大文件 gitignore) |

**已实现的是"不依赖板子的全部"**:疲劳(特征换算 + 状态机 + 事件落地 + 离线回放)+ 视觉安防 P0(运动检测 + episode 状态机 + 帧回放),共 **81 tests** 全绿(76 纯标准库 + 5 需 numpy)。需要板子的只剩 RTSP 取流 + RKNN/MPP/RGA 推理(P0/P1 取证后才写,避免盲猜)。

## 快速验证(Mac,无需板子)

```bash
# 纯逻辑测试(标准库,任意 python3):疲劳链 + 视觉安防 P0 episode + P1a 门控/确认
for t in test_engine test_features test_event_adapter \
         test_motion_episode test_motion_pipeline \
         test_roi_mask test_person_detector test_confirm test_confirm_pipeline; do
  python3 tests/$t.py
done
python3 scripts/replay.py --events      # 合成疲劳剧本走一遍整链(清醒→困倦→微睡→恢复)
python3 scripts/replay_confirm.py       # P1a 两幕:蒸汽不产 person / 真人产 person_observation

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

- **P0** 实机能力取证 — 脚本就绪,待上板子跑出报告
- **P0.5** NPU spike(model_zoo 样例)— 待板子(证明 NPU 链路活,再建管线)
- **P1** 摄像头 + RTSP — 脚本就绪,待接线/上电/取证
- **P2** CPU 基线 — 待 P0/P1
- **P3** 迁移 RKNN(RetinaFace/SCRFD + PFLD,**非 MediaPipe**,后者不能干净转 RKNN)— 待
- **P4** 疲劳状态机接入实时特征 — 核心引擎已就绪,待接 vision 输出
- **P5** 可靠性(白天/夜间/遮挡 + 24h)— 待

## 红线

不改热源安全逻辑;不提交密码/RTSP URL;不假设 RKNN/MPP/RGA 可用(用命令证明);实测前不承诺帧率;视频流不进 MQTT 遥测主题。

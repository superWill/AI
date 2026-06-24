# driver-monitor — 单路 IVG-G4H 离线疲劳驾驶预警

> 目标平台:**BL412B-SOM412**(RK3568J / 4×A55@1.8G / 4GB / 32GB eMMC / 1 TOPS NPU / Ubuntu 20.04)。  
> 摄像头:**IVG-G4H**(GK7205V210)IP 机,经 Ethernet/RTSP 接入,不接 X23/Y 板。  
> 方案与阶段:见 `../docs/bl412b-drowsiness-detection-claude-handoff.md`。  
> 本目录与供热网关 `../heating/` **完全隔离**,不动任何热源安全控制逻辑。

## 架构(目标态)

```text
IVG-G4H RTSP H.264/265
 → camera-worker(RTSP/解码/重连/帧时间戳)
 → vision-worker(RGA 预处理 + RKNN 人脸检测/关键点;模型健康)
 → drowsiness-engine(EAR/MAR/PERCLOS/头姿 → 时间窗 → 状态机)   ← 已实现,纯逻辑
 → event-adapter(蜂鸣/HMI/本地日志/MQTT 事件)
```

四进程隔离:视频/AI 失败不阻塞其它循环;连续视频帧不进点表/MQTT 遥测;密码不进代码/Git/日志。

## 目录

| 路径 | 内容 | 现状 |
|---|---|---|
| `src/drowsiness/engine.py` | 疲劳状态机(EAR/MAR/PERCLOS/头姿 → 时间窗 → 状态机) | ✅ 实现 + **11 tests** |
| `src/vision/features.py` | 关键点 → EAR/MAR/近似头姿(纯数学,CPU 侧) | ✅ 实现 + **7 tests** |
| `src/event/adapter.py` | 事件去抖/周期重报 + JSONL 日志 + 可插拔 sink | ✅ 实现 + **6 tests** |
| `scripts/replay.py` | 离线回放/联调(特征轨迹 → 整链 → 状态时间线+事件) | ✅ 跑通(合成剧本触发 alarm 并恢复) |
| `scripts/check_platform.sh` | **P0** 实机能力取证(RKNN/MPP/RGA 是否可用) | ✅ 可发板子跑 |
| `scripts/rtsp_probe.py` | **P1** 摄像头 RTSP 探测(codec/分辨率/fps + soak) | ✅ 可发板子跑 |
| `config/*.example.json` | 阈值 / 摄像头配置示例(无真实密码) | ✅ |
| `src/vision/`(RKNN 推理) `src/camera/`(RTSP/MPP/RGA) | 需板子的 worker | ⏳ 待 P0/P1 取证后写(P3) |
| `models/` | onnx 源 + rknn 产物 | ⏳ P3(rknn 大文件 gitignore) |

**已实现的是"不依赖板子的全部"**:特征换算 + 状态机 + 事件落地 + 离线回放,共 **24 tests** 全绿。需要板子的只剩 RTSP 取流 + RKNN/MPP/RGA 推理(P0/P1 取证后才写,避免盲猜)。

## 快速验证(Mac,无需板子)

```bash
for t in test_engine test_features test_event_adapter; do python3 tests/$t.py; done   # 24 passed
python3 scripts/replay.py --events      # 合成疲劳剧本走一遍整链(清醒→困倦→微睡→恢复)
```

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

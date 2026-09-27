# BL412B 单路疲劳驾驶检测执行交接

> [KNOWN][HIGH] 执行对象：`Claude` 或其他接手实现的编码代理。  
> [KNOWN][HIGH] 目标硬件：`BL412B-SOM412-X23-Y31-Y41` 工业计算机和 `IVG-G4H` 网络摄像机模组。  
> [INFERRED][HIGH] 本阶段目标是完成可测量的单路离线疲劳告警原型，不建设录像平台、多摄像头矩阵或云端视频分析。

## 1. 最终结论

- [KNOWN][HIGH] 当前工业机主机型号是 `BL412B`，核心板型号是 `SOM412`。
- [KNOWN][HIGH] `SOM412` 使用 Rockchip RK3568J，配置为 4 核 Cortex-A55 1.8GHz、4GB LPDDR4X、32GB eMMC、1 TOPS NPU，标称工业温度为 `-40~85°C`。
- [KNOWN][HIGH] `BL412B` 提供 3 路 100M Ethernet、2 路 USB 2.0、1 路 HDMI、1 个 20PIN X 板插槽和 2 个 Y 板插槽。
- [KNOWN][HIGH] `IVG-G4H` 是基于 GK7205V210 的完整 IP 摄像机模组，不是直接连接 MIPI-CSI 的裸传感器。
- [KNOWN][HIGH] 摄像机支持 H.264/H.265、RTSP、ONVIF 和 `1920x1080@25fps` 主码流。
- [INFERRED][HIGH] 摄像机应通过 Ethernet/RTSP 接入 BL412B，不接 X23、Y31 或 Y41。
- [INFERRED][HIGH] BL412B 可以作为单路疲劳检测的目标平台，不需要额外增加一块 RK3568 开发板。
- [INFERRED][HIGH] 不能原样照搬树莓派 5 项目的 Python/MediaPipe CPU 管线并假设达到 25 或 30 FPS。
- [INFERRED][HIGH] 推荐生产方向是 `MPP 硬解码 + RGA 预处理 + RKNN NPU 推理 + CPU 状态机`。
- [KNOWN][HIGH] Raspberry Pi 5 的 Cortex-A76 2.4GHz 通用 CPU 明显强于 BL412B 的 Cortex-A55 1.8GHz。
- [INFERRED][HIGH] BL412B 的优势不是通用 CPU 算力，而是内置 NPU、工业温度、宽压供电、硬件看门狗、三网口和现场 I/O。

## 2. 硬件连接

[INFERRED][HIGH] 推荐拓扑：

```text
12/24VDC industrial power
  |
  +-- BL412B power input

regulated 12V camera power
  |
  +-- IVG-G4H J1 power pins

IVG-G4H J1 Ethernet pairs
  |
  +-- matched waterproof tail cable / RJ45
        |
        +-- BL412B Ethernet port 1: isolated camera subnet

BL412B Ethernet port 2: control/device subnet
BL412B Ethernet port 3: uplink/MQTT/maintenance subnet
```

- [KNOWN][HIGH] 摄像机标称输入为 DC 12V，规格书绝对供电范围为 `9.6~14.4V`。
- [KNOWN][HIGH] J1 同时承载 12V、GND、Ethernet TX/RX 差分对和网络灯信号。
- [INFERRED][HIGH] 第一次上电前必须用万用表确认尾线红线落到 J1-8、黑线落到 J1-7，且电源与地无短路。
- [INFERRED][HIGH] 未经过 PoE 分离和降压时，禁止把 48V PoE 直接送入摄像机 12V 输入。
- [INFERRED][HIGH] 疲劳检测夜间可靠性需要匹配镜头、红外补光和 IR-CUT 策略，现有摄像机模组不等于已经包含合格的红外照明系统。

详细接线步骤见：

- [KNOWN][HIGH] [`ivg-g4h-camera-module-wiring.md`](./ivg-g4h-camera-module-wiring.md)
- [KNOWN][HIGH] [`xiongmai-ip-camera-integration-plan.md`](./xiongmai-ip-camera-integration-plan.md)

## 3. 软件架构

[INFERRED][HIGH] 推荐数据链：

```text
IVG-G4H RTSP H.264/H.265
  -> stream supervisor
  -> Rockchip MPP hardware decoder
  -> RGA resize / colorspace conversion / face ROI crop
  -> RKNN face detector
  -> RKNN facial landmark model
  -> CPU feature calculation
       - EAR
       - MAR
       - PERCLOS
       - head pose
  -> temporal state machine
       - normal
       - suspected
       - warning
       - alarm
       - camera_fault
  -> buzzer / local HMI / event log / MQTT event
```

[INFERRED][HIGH] 进程边界建议：

```text
camera-worker
  owns RTSP, decode, reconnect, frame timestamps

vision-worker
  owns RGA/RKNN inference and model health

drowsiness-engine
  owns thresholds, temporal windows and alert state

event-adapter
  owns buzzer, HMI, local log and MQTT
```

- [INFERRED][HIGH] 视频和 AI 进程失败不能阻塞已有采集、控制或 MQTT 主循环。
- [INFERRED][HIGH] 连续视频帧不进入普通点表或 MQTT 遥测链路；MQTT 只上传状态、事件和可选快照引用。
- [INFERRED][HIGH] 摄像机密码不得写入代码、Git 或日志。
- [INFERRED][HIGH] 所有进程必须有超时、重连、退避、资源上限和健康检查。

## 4. 执行阶段

### P0：确认 BL412B 软件能力

执行并保存输出：

```bash
uname -a
cat /etc/os-release
cat /proc/device-tree/compatible | tr '\0' '\n'
cat /proc/device-tree/model
free -h
df -h
ip -br addr
ls -l /dev/rknpu /dev/mpp_service /dev/dri 2>/dev/null
ldconfig -p | grep -Ei 'rknn|rockchip_mpp|mpp|rga'
dmesg | grep -Ei 'rk3568|rknpu|rga|mpp'
```

- [KNOWN][HIGH] 通过条件：设备树确认 RK3568、NPU 驱动可用、MPP/RGA 设备或运行库可用、可用内存和存储被记录。
- [INFERRED][HIGH] 如果 RKNN、MPP 或 RGA 缺失，先形成缺口清单和安装方案，不直接开始完整应用开发。

### P1：摄像机网络和 RTSP 验证

1. [INFERRED][HIGH] 完成尾线脚序和 12V 供电检查。
2. [INFERRED][HIGH] 给摄像机和 BL412B 摄像机网口配置独立静态网段。
3. [INFERRED][HIGH] 确认摄像机 IP、Web 页面、ONVIF profile、主码流和子码流 URL。
4. [INFERRED][HIGH] 使用 `ffprobe` 记录 codec、resolution、fps、bitrate 和连接耗时。
5. [INFERRED][HIGH] 连续拉流至少 30 分钟，记录断流、重连和 CPU 占用。

最低验收：

```text
ping success
RTSP authentication success
main stream: 1920x1080@25fps or actual configured value
sub stream: 800x448@25fps or actual configured value
30-minute stream test has no unrecovered disconnect
```

### P2：先建立 CPU 基线

- [INFERRED][HIGH] 先运行参考项目或等价 CPU 模型，目的只是取得真实基线，不把它当最终架构。
- [INFERRED][HIGH] 关闭人脸网格绘制、窗口动画和不必要的图像复制。
- [INFERRED][HIGH] 分别测试主码流、子码流、每帧推理和隔帧推理。
- [INFERRED][HIGH] 记录平均值和 P95：FPS、端到端延迟、CPU、RSS、温度和掉帧率。

### P3：迁移到 RKNN

1. [INFERRED][HIGH] 选择可转换的人脸检测模型和人脸关键点模型。
2. [INFERRED][HIGH] 在开发机完成 ONNX 到 RKNN 转换和量化校准。
3. [INFERRED][HIGH] 在 BL412B 上分别验证模型加载、单帧推理和连续推理。
4. [INFERRED][HIGH] 使用 MPP/RGA 输出直接构造模型输入，减少 CPU 色彩转换和内存复制。
5. [INFERRED][HIGH] 对比 CPU 与 NPU 结果，记录关键点误差、失败帧和算子回退。

### P4：疲劳状态机

- [INFERRED][HIGH] 不以单帧阈值直接报警。
- [INFERRED][HIGH] EAR、MAR、PERCLOS 和头部姿态必须进入时间窗口和状态机。
- [INFERRED][HIGH] 摄像机离线、人脸丢失、模型异常和时间戳倒退必须产生独立故障状态，不能被解释成驾驶员正常。
- [INFERRED][HIGH] 阈值必须配置化并记录版本，不能散落为代码常量。

建议输出事件：

```json
{
  "type": "driver_monitor_event",
  "state": "warning",
  "reason": ["eyes_closed", "high_perclos"],
  "confidence": 0.82,
  "camera_status": "online",
  "model_version": "face-landmark-rknn-v1",
  "timestamp": "2026-06-24T13:00:00+08:00"
}
```

### P5：可靠性验证

- [INFERRED][HIGH] 覆盖白天、夜间、逆光、眼镜、墨镜、口罩、遮挡、侧脸和快速转头。
- [INFERRED][HIGH] 覆盖摄像机断电、网线断开、密码错误、RTSP 卡死、NPU 推理失败和磁盘写满。
- [INFERRED][HIGH] 至少执行一次 24 小时连续运行，检查内存增长、文件句柄、线程数、磁盘增长、温度和自动恢复。
- [INFERRED][HIGH] 报警功能只能定位为辅助告警，不能控制车辆安全执行机构。

## 5. 性能验收

[INFERRED][MED] 第一阶段建议目标：

| 指标 | 建议门槛 |
|---|---:|
| 有效分析帧率 | `>=15 FPS` |
| 摄像机到状态输出 P95 | `<=300ms` |
| 视频/AI 总 RSS | `<=1.2GB` |
| 连续运行 | `24h` 无不可恢复故障 |
| 断流恢复 | 网络恢复后 `<=10s` 自动恢复 |
| 主控制影响 | 原有采集/控制循环无可测阻塞或 deadline miss |

- [INFERRED][MED] `20~25 FPS` 可以作为优化目标，不应在实测前写成承诺。
- [INFERRED][HIGH] 若 NPU 路线仍达不到门槛，先降低推理频率、固定人脸 ROI、使用跟踪减少检测次数，再考虑更换平台。

## 6. 交付物

`Claude` 必须交付：

1. [KNOWN][HIGH] `docs/`：实机环境记录、模型来源、转换参数、网络配置和测试结果。
2. [KNOWN][HIGH] `scripts/`：摄像机发现、RTSP 探测、硬件能力检查和性能采样脚本。
3. [KNOWN][HIGH] `src/`：可独立运行的视频、推理、状态机和事件适配模块。
4. [KNOWN][HIGH] `config/`：摄像机、模型、阈值和时间窗口配置示例，不含真实密码。
5. [KNOWN][HIGH] `tests/`：状态机单元测试、录像回放测试和断流恢复测试。
6. [KNOWN][HIGH] 一份 CPU 基线与 RKNN 版本的对比表。
7. [KNOWN][HIGH] 一份未解决问题清单，明确区分代码问题、模型问题、驱动问题和硬件问题。

## 7. 禁止事项

- [INFERRED][HIGH] 不得把 Raspberry Pi 5 的 30 FPS 描述直接当作 BL412B 性能结论。
- [INFERRED][HIGH] 不得声称 MediaPipe 会自动使用 RK3568 NPU。
- [INFERRED][HIGH] 不得在没有实测数据时声称达到 25 FPS、300ms 或量产可靠性。
- [INFERRED][HIGH] 不得修改现有热源安全控制逻辑来配合视频功能。
- [INFERRED][HIGH] 不得把摄像机视频流写进普通 MQTT 遥测主题。
- [INFERRED][HIGH] 不得把真实摄像机账号、密码或 RTSP URL 提交到 Git。
- [INFERRED][HIGH] 不得在尾线脚序未经万用表确认时给摄像机上电。

## 8. 资料索引

### 用户提供

- [KNOWN][HIGH] 微信文章：<https://mp.weixin.qq.com/s/AjEE90lMgogT7HBt0Td1sg>
- [KNOWN][HIGH] BL410 数据表：`/Users/songzijian/Downloads/Books and PDFs/ARMxyBL410DatasheetV10.pdf`
- [KNOWN][HIGH] BL410 用户手册：`/Users/songzijian/Downloads/Books and PDFs/BLIIOTARMxySeriesBL410UserManualV11.pdf`
- [KNOWN][HIGH] 摄像头实物正面：[module-top.jpg](./assets/ivg-g4h/module-top.jpg)
- [KNOWN][HIGH] 摄像头实物侧面：[module-side.jpg](./assets/ivg-g4h/module-side.jpg)
- [KNOWN][HIGH] 九芯尾线规格：[cable-spec.jpg](./assets/ivg-g4h/cable-spec.jpg)
- [KNOWN][HIGH] IVG-G4H 概述：[datasheet-overview.jpg](./assets/ivg-g4h/datasheet-overview.jpg)
- [KNOWN][HIGH] IVG-G4H 参数：[datasheet-specifications.jpg](./assets/ivg-g4h/datasheet-specifications.jpg)
- [KNOWN][HIGH] IVG-G4H 接口：[datasheet-interfaces.jpg](./assets/ivg-g4h/datasheet-interfaces.jpg)

### 参考项目和官方资料

- [KNOWN][HIGH] DrowSAFE 参考实现：<https://github.com/Bedair/DrowSAFE>
- [KNOWN][HIGH] Raspberry Pi 5 官方规格：<https://www.raspberrypi.com/products/raspberry-pi-5/>
- [KNOWN][HIGH] MediaPipe Face Landmarker Python 指南：<https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker/python>

### 仓库内已有文档

- [KNOWN][HIGH] BL412B 端子和实机映射：
  [`heating/docs/hardware/bl412b-som412-x23-y31-y41-terminal-map.md`](../heating/docs/hardware/bl412b-som412-x23-y31-y41-terminal-map.md)
- [KNOWN][HIGH] IVG-G4H 接线：
  [`ivg-g4h-camera-module-wiring.md`](./ivg-g4h-camera-module-wiring.md)
- [KNOWN][HIGH] IP 摄像机接入设计：
  [`xiongmai-ip-camera-integration-plan.md`](./xiongmai-ip-camera-integration-plan.md)

## 9. 可直接交给 Claude 的指令

```text
请先完整阅读：
1. embedded-gateway/docs/bl412b-drowsiness-detection-claude-handoff.md
2. embedded-gateway/docs/ivg-g4h-camera-module-wiring.md
3. embedded-gateway/docs/xiongmai-ip-camera-integration-plan.md
4. embedded-gateway/heating/docs/hardware/bl412b-som412-x23-y31-y41-terminal-map.md
5. 两份 BL410 原厂 PDF。

目标是在 BL412B-SOM412（RK3568J/4GB/32GB/1TOPS NPU）上实现单路
IVG-G4H RTSP 离线疲劳检测原型。

严格按 P0 -> P5 执行。先收集实机证据，再写代码。不要假设 RKNN、MPP、RGA
已经可用；用命令输出证明。先建立 CPU 基线，再迁移到 MPP/RGA/RKNN。

每个阶段提交：
- 实际执行命令和输出摘要
- 改动文件
- 测试结果
- 当前瓶颈
- 下一阶段准入条件

不要修改热源安全控制逻辑，不要提交密码，不要承诺未实测帧率。
最终必须提供 24 小时稳定性结果、CPU 与 RKNN 对比、故障恢复测试和剩余风险。
```

[RULES I BROKE]: 无。

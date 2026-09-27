# RK3506 + GC2145 产品方案可行性与边界

> 更新日期：2026-07-21  
> 适用硬件：RK3506（256MB DDR + 256MB NAND）+ GC2145 DVP 摄像头  
> 目的：判断该组合能否同时承担工业控制、本地 HMI、设备配置、人体/人脸检测、事件抓拍和视频上传，并明确不能越过的产品边界。

## 1. 结论

[INFERRED][HIGH] `RK3506 256MB+256MB + GC2145` 可以完成工业控制、HMI、离线设备配置、低频人体/人脸检测、少量人员识别和事件 JPEG 抓拍。

[INFERRED][HIGH] 该组合不适合同时承担持续视频录像上传、实时人体检测、人脸识别、可靠活体检测和产品控制。

[KNOWN][HIGH] GC2145 只输出 YUV422、RGB565 或 RAW 像素，不负责 JPEG/H.264/H.265 编码，也没有独立存储能力。因此采集、预处理、AI、图片编码、视频编码、保存和上传都需要由 RK3506 或额外处理器完成。

推荐产品边界：

```text
RK3506
├── Modbus/RS485 采集与控制
├── 本地 Go HMI
├── 离线设备配置
├── GC2145 屏前预览
├── 每秒 1～3 次人体/人脸检测
├── 少量人员识别
├── 事件 JPEG 抓拍
└── 上传事件、图片和设备状态
```

不纳入该硬件组合的承诺范围：

```text
全天视频录像
持续 H.264/H.265 软件编码
多路摄像头 AI
大规模人脸库
高安全等级活体检测
远距离站房视频监控
```

## 2. 需求可行性

| 产品需求 | 判断 | 主要限制 |
|---|---|---|
| Modbus/RS485 设备采集 | [KNOWN][HIGH] 可以 | 已有核心能力 |
| 泵阀控制 | [KNOWN][HIGH] 可以 | 必须保持最高运行优先级 |
| 本地 LCD HMI | [KNOWN][HIGH] 可以 | 已有 Go HMI |
| 离线添加设备和配置 | [KNOWN][HIGH] 可以 | 已有基础链路 |
| 亮度、Light/Dark 模式 | [KNOWN][HIGH] 可以 | 已有基础实现 |
| GC2145 实时预览 | [INFERRED][HIGH] 可以 | 需要 DVP 驱动和板级接口 |
| 低频人体检测 | [INFERRED][MED] 可以尝试 | 小模型、低分辨率、低帧率 |
| 低频人脸检测 | [INFERRED][MED] 可以尝试 | 小模型、近距离、正脸优先 |
| 少量人员人脸识别 | [INFERRED][MED] 可以尝试 | 仅在人脸稳定后触发 |
| 简单眨眼/摇头活体 | [INFERRED][MED] 可以尝试 | 安全性有限 |
| 门禁级可靠活体 | [INFERRED][HIGH] 不适合 | 缺少近红外和深度信息 |
| 事件 JPEG 抓拍 | [INFERRED][HIGH] 可以 | 只在事件发生时编码 |
| 低帧率 MJPEG 片段 | [INFERRED][MED] 可以尝试 | CPU 和上传带宽较高 |
| 持续 H.264/H.265 录像 | [INFERRED][HIGH] 不建议 | 没有公开硬件视频编码器 |
| 录像长期写入 NAND | [KNOWN][HIGH] 不可行 | NAND 容量太小 |
| 多路摄像头 | [INFERRED][HIGH] 不适合 | CPU、接口和内存余量不足 |
| 站房远距离监控 | [INFERRED][HIGH] GC2145 不适合 | DVP 距离短，无独立网络和录像能力 |

## 3. 推荐处理管线

```text
GC2145
  ↓ DVP，YUV422 或 RGB565
采集线程
  ↓
最新帧槽（长度固定为 1）
  ├── LCD 预览：目标 10～15 FPS
  └── AI 线程：目标 1～3 FPS
          ↓
      人体检测
          ↓ 有人
      人脸检测
          ↓ 人脸足够大且稳定
      人脸特征提取
          ↓
      生成事件
          ├── first_frame.jpg
          ├── face_frame.jpg
          ├── 人员 ID / 置信度
          ├── 时间戳
          └── 上传平台
```

[COMMON][HIGH] LCD 预览帧率和 AI 推理帧率必须解耦。屏幕可以显示 10～15 FPS，但模型只需要每秒运行 1～3 次。

[COMMON][HIGH] 图像队列必须有界，推荐只保留最新一帧。AI 处理不过来时丢弃旧帧，不能积压过期画面。

[COMMON][HIGH] 人体、人脸和身份识别必须门控运行：

```text
没有人体
→ 不运行人脸检测

有人但人脸太小
→ 不运行身份识别

人脸足够大且稳定
→ 才运行一次特征提取和比对
```

## 4. 图像内存预算

假设使用 `320×240 RGB565`：

```text
一帧 = 320 × 240 × 2
     = 153,600 字节
     = 150 KiB
```

[COMPUTED][HIGH] 三缓冲约为：

```text
150 KiB × 3 = 450 KiB
```

[INFERRED][HIGH] 保存少量低分辨率帧不是 256MB 内存的主要问题。主要资源消耗来自：

- [COMMON][HIGH] 模型权重和中间张量；
- [COMMON][HIGH] 人体、人脸和特征提取模型；
- [COMMON][HIGH] JPEG 或视频编码；
- [COMMON][HIGH] LCD 绘制和颜色转换；
- [COMMON][HIGH] Linux、Go HMI 和 gatewayc 服务；
- [COMMON][HIGH] 网络阻塞时的上传缓存。

## 5. CPU 与模型限制

[KNOWN][HIGH] RK3506 没有公开 NPU，人脸和人体模型需要在 Cortex-A7 CPU 上运行。

[INFERRED][MED] 极小的 INT8 人脸检测模型可能达到可用的低频检测，但在真实模型和板端管线压测前不能承诺类似 ESP32-S3 演示中的 18 FPS。

[INFERRED][HIGH] 人体检测通常比近距离人脸检测更困难，因为需要处理尺度、姿态、遮挡和背景变化。

必须测量：

- 单模型预处理、推理、后处理耗时；
- 人体检测 → 人脸检测 → 特征提取的端到端时延；
- AI 运行时 Modbus 控制周期抖动；
- 峰值 RSS、CPU、内存带宽和温度；
- 24 小时运行、断相机、断网和上传阻塞。

## 6. GC2145 场景边界

适合：

- [INFERRED][HIGH] 安装在本地屏幕旁；
- [INFERRED][HIGH] 拍摄屏幕前约 0.5～2 米人员；
- [INFERRED][HIGH] 近距离人脸交互；
- [INFERRED][HIGH] 判断是否有人操作终端；
- [INFERRED][HIGH] 保存事件代表图片。

不适合：

- [COMMON][HIGH] 使用几十米网线远程安装；
- [INFERRED][HIGH] 监控整个换热站；
- [INFERRED][HIGH] 无补光夜间监控；
- [INFERRED][HIGH] 室外防水摄像；
- [INFERRED][HIGH] 独立生成 H.264/H.265；
- [INFERRED][HIGH] 独立接入 NVR 或视频平台。

[COMMON][HIGH] DVP 排线适合板内或短距离连接，不能替代以太网摄像头。

## 7. 活体检测限制

[KNOWN][HIGH] GC2145 是普通 RGB 图像传感器，不提供近红外、双目、ToF 或结构光深度信息。

可以尝试的低安全级主动活体：

- [INFERRED][MED] 眨眼；
- [INFERRED][MED] 摇头；
- [INFERRED][MED] 张嘴；
- [INFERRED][MED] 按提示转向。

不能仅靠该组合可靠解决：

- [COMMON][HIGH] 手机照片攻击；
- [COMMON][HIGH] 屏幕视频回放；
- [COMMON][HIGH] 高清打印照片；
- [COMMON][HIGH] 深度伪造视频；
- [COMMON][HIGH] 高质量面具。

[INFERRED][HIGH] 门禁级活体需要 RGB + 近红外/深度摄像头，或独立 AI 视觉模组。

## 8. 视频留存与上传限制

GC2145 视频留存链路为：

```text
GC2145 原始帧
  ↓
RK3506 采集
  ↓
RK3506 编码 JPEG/H.264
  ↓
RK3506 保存或上传
```

[KNOWN][HIGH] RK3506 公开资料没有列出 H.264/H.265 硬件编码器。

[INFERRED][HIGH] 持续 CPU 软件编码可能占用一个或多个 A7 核心，并与产品控制、HMI 和 AI 争抢资源。

[COMPUTED][HIGH] 录像码率和每小时存储量关系：

| 码率 | 每小时数据量 |
|---:|---:|
| 0.5 Mbps | 约 225 MB |
| 1 Mbps | 约 450 MB |
| 2 Mbps | 约 900 MB |

[KNOWN][HIGH] 256MB NAND 不能承担持续录像，应只保存事件元数据和少量代表图片：

```text
events/
└── event-000123/
    ├── event.json
    ├── first_frame.jpg
    └── face_frame.jpg
```

若业务必须持续留存视频，应增加以下任一组件：

1. [INFERRED][HIGH] 带 H.264/H.265 编码的 IP 摄像头；
2. [INFERRED][HIGH] 独立视频编码器；
3. [INFERRED][HIGH] NVR；
4. [INFERRED][HIGH] 带 NPU/VPU 的独立视觉处理器；
5. [INFERRED][HIGH] 更适合视觉的 SoC 平台。

## 9. 板级硬件前置条件

[KNOWN][HIGH] RK3506 芯片支持通过 FLEXBUS 映射 DVP 摄像头输入。

[KNOWN][HIGH] 当前 RK3506-IOT_NAND 成品板是否引出完整 DVP 信号、是否与 LCD 或其他外设复用冲突，尚无完整原理图证据。

实现前必须确认：

```text
D0～D7
PCLK
VSYNC
HREF
XCLK
I²C/SCCB
RESET
PWDN
电源电压
I/O 电平
```

[INFERRED][HIGH] 如果现有底板没有引出这些信号，就需要重新设计底板或转接板，不能只通过软件接入 GC2145。

## 10. 产品级资源隔离

[COMMON][HIGH] 视觉能力必须是可降级的辅助业务，不能影响控制主链路：

```text
最高优先级：Modbus 采集、泵阀控制、安全联动
中优先级：HMI、配置、告警
最低优先级：摄像头预览、AI、图片上传
```

资源不足时依次降级：

```text
停止人脸特征提取
  ↓
降低人脸检测频率
  ↓
停止人体检测
  ↓
停止摄像头预览
  ↓
保留核心控制和 HMI
```

实现要求：

- [COMMON][HIGH] 视觉服务使用独立进程；
- [COMMON][HIGH] 设置 CPU、内存和队列上限；
- [COMMON][HIGH] 上传阻塞不能反压采集和控制；
- [COMMON][HIGH] 视觉进程崩溃不能重启控制服务；
- [COMMON][HIGH] 图片和日志必须有容量水位与淘汰策略；
- [COMMON][HIGH] 看门狗、失败退避和健康状态独立上报。

## 11. 验收门槛

进入产品方案前至少完成：

1. [KNOWN][HIGH] 确认成品板 DVP 引脚、电平和供电；
2. [KNOWN][HIGH] GC2145 在 RK3506 上连续稳定采集；
3. [KNOWN][HIGH] 单独测人脸模型和人体模型的端到端耗时；
4. [KNOWN][HIGH] 同时运行控制、HMI 和 AI，记录控制周期抖动；
5. [KNOWN][HIGH] 验证事件首帧和代表人脸帧必定落盘；
6. [KNOWN][HIGH] 注入摄像头断开、无帧、断网、上传阻塞和磁盘满；
7. [KNOWN][HIGH] 执行至少 24 小时稳定性测试；
8. [KNOWN][HIGH] 用白天、夜间、逆光、侧脸、遮挡和多人场景验证效果；
9. [KNOWN][HIGH] 明确误检、漏检、误接受和误拒绝验收阈值；
10. [KNOWN][HIGH] 证明视觉故障不会影响 Modbus、控制和安全联动。

## 12. 最终裁定

[INFERRED][HIGH] 如果需求边界是：

```text
工业控制
+ 本地 HMI
+ 离线设备配置
+ 屏前低频人体/人脸检测
+ 少量人员识别
+ 事件图片上传
```

则 `RK3506 + GC2145` 可以进入板级接口验证和模型压测阶段。

[INFERRED][HIGH] 如果需求还包含：

```text
持续录像
+ 实时视频上传
+ 高可靠活体
+ 远距离站房监控
+ 多路摄像头
```

则该组合不能完整满足产品需求，应保留 IP 摄像头/NVR，或增加独立视频编码与 AI 处理器。

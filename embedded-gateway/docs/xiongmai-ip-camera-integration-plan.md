# 雄迈 IP 摄像头接入方案

> 用途：把雄迈 / XM 系列网络摄像头作为网关的“视频感知设备”接入 RK3506 或同类 Linux 工业网关。  
> 状态：接入设计草案。最终参数以摄像头铭牌、Web 配置页、ONVIF 返回结果和现场抓包为准。  
> 适用范围：优先面向 IP 摄像头；BNC 同轴模拟摄像头不直接接入网关，需先经 DVR/NVR 或采集器转换。

---

## 1. 接入目标

第一阶段不要追求“视频平台全功能”，先把四件事做稳：

1. 网关能发现或配置摄像头。
2. 网关能判断摄像头在线、离线、鉴权失败、拉流失败。
3. 本地 HMI 能显示摄像头状态和预览入口。
4. 上行平台能收到摄像头设备状态、告警和快照类元数据。

视频流本身可以本地预览或转发，但不要把连续视频流塞进现有点表和 MQTT 遥测主链路。MQTT 只发状态、事件、快照地址、告警摘要等轻量数据。

## 2. 推荐硬件拓扑

优先选择支持 ONVIF + RTSP 的 IP 摄像头。

```text
PoE / 12V IP 摄像头
        |
        | Ethernet
        v
PoE 交换机 / 普通交换机
        |
        v
RK3506 工业网关
        |
        +--> 本地 HMI 预览 / 状态展示
        +--> MQTT 上报状态和事件
```

采购和接线建议：

| 摄像头形态 | 推荐接法 | 注意事项 |
|---|---|---|
| RJ45 + DC12V | 12V 适配器供电 + 网线进交换机 | 电源常见圆头 `5.5*2.1mm`，室外要防水盒 |
| PoE 摄像头 | PoE 交换机或 PoE 注入器 | 确认 `802.3af/at`，不要把 48V PoE 直接接 DC12V 圆口 |
| RJ45 + DC12V + PoE | 优先 PoE，减少布线 | 若改用 DC12V，要保留网线数据链路 |
| Wi-Fi 摄像头 | 只建议实验验证 | 工业现场优先有线，Wi-Fi 只做非关键辅助画面 |
| BNC 同轴头 | 先接 DVR/NVR，再由网关接 DVR/NVR 的 RTSP/ONVIF | 不能当普通网络摄像头直接插 RK3506 |

## 3. 软件边界

摄像头要作为一种独立的以太网业务设备接入，而不是当成 AI/DI/Modbus 点位。

```text
camera_adapter
  - ONVIF discovery / manual config
  - RTSP probe
  - snapshot capture
  - stream health check
        |
        v
device registry
  - online/offline/auth_failed/stream_failed
        |
        v
runtime snapshot
  - camera status
  - last frame time
  - last event time
        |
        +--> HMI WebSocket
        +--> MQTT telemetry/events
        +--> local log
```

建议新增或预留模块职责：

| 模块 | 职责 |
|---|---|
| `drivers/camera` | RTSP 探测、ONVIF 能力读取、截图、拉流健康检查 |
| `core/device_registry` | 维护摄像头设备记录、在线状态、最后成功时间 |
| `core/media_store` | 保存短期快照、缩略图、事件图片，设置容量上限和清理策略 |
| `app/hmi` | 摄像头列表、在线状态、预览入口、错误提示 |
| `app/communication` | 上报摄像头状态、事件、快照引用，不上传连续视频 |

## 4. 数据模型建议

设备记录：

```json
{
  "id": "cam-001",
  "name": "站房入口摄像头",
  "type": "ip_camera",
  "vendor": "xiongmai",
  "interface_kind": "ethernet",
  "ip": "192.168.10.64",
  "onvif_port": 8899,
  "rtsp_port": 554,
  "status": "online",
  "quality": "good",
  "last_seen_at": 1799900000,
  "last_stream_at": 1799900000
}
```

运行快照：

```json
{
  "type": "camera_snapshot",
  "device_id": "cam-001",
  "status": "online",
  "stream_status": "ok",
  "resolution": "1920x1080",
  "codec": "H264",
  "fps": 15,
  "snapshot_path": "/media/camera/cam-001/latest.jpg",
  "updated_at": 1799900010
}
```

状态枚举建议：

| 状态 | 含义 | HMI 行为 |
|---|---|---|
| `online` | ONVIF 或 RTSP 探测成功 | 正常显示 |
| `offline` | IP 不通或端口不可达 | 置灰，保留最后快照 |
| `auth_failed` | 用户名/密码错误 | 显示需配置认证 |
| `stream_failed` | 设备在线但 RTSP 拉流失败 | 显示在线但无视频 |
| `unsupported` | 非 IP 摄像头或协议不支持 | 提示需要 DVR/NVR 或人工配置 |

## 5. 最小验证流程

拿到摄像头后按这个顺序验证，先网络后视频：

1. 确认供电：`DC12V` 或 `PoE`。
2. 确认网关和摄像头同网段，能 `ping` 通。
3. 扫描端口：重点看 `80/8080`、`554`、`8899`、ONVIF 相关端口。
4. 用 ONVIF 工具读取设备信息和媒体 profile。
5. 用 `ffprobe` 或 `ffplay` 验证 RTSP 主码流、子码流。
6. 用网关程序保存一张快照。
7. 断网、断电、改错密码，验证状态是否正确降级。

常见 RTSP 地址需要以实际设备为准，雄迈类设备常见形态可能类似：

```text
rtsp://user:password@CAMERA_IP:554/user=USER&password=PASSWORD&channel=1&stream=0.sdp
rtsp://user:password@CAMERA_IP:554/user=USER&password=PASSWORD&channel=1&stream=1.sdp
```

不要把这些模板写死为唯一格式。正确做法是优先从 ONVIF media profile 获取流地址；获取不到时再允许手工配置 RTSP URL。

## 6. HMI 展示建议

摄像头卡片不要和温度、压力、泵阀点位混在一个点表卡片里。建议单独做“视频设备”分组。

| 字段 | 展示方式 |
|---|---|
| 摄像头名称 / 位置 | 例如“站房入口”“换热机组上方” |
| 在线状态 | 在线、离线、鉴权失败、拉流失败 |
| 最后画面 | 最近一次快照，离线后保留但标注时间 |
| 预览入口 | 本地 HMI 打开低码率子码流 |
| 事件 | 移动侦测、遮挡、拉流恢复、离线恢复 |

HMI 只默认拉子码流，避免 RK3506 和浏览器端负载过高。主码流用于取证、截图或外部平台，不作为常驻预览默认流。

## 7. MQTT 上报建议

MQTT 上报轻量状态，不上传连续视频。

设备状态：

```json
{
  "type": "camera_status",
  "device_id": "cam-001",
  "status": "online",
  "stream_status": "ok",
  "ip": "192.168.10.64",
  "last_seen_at": 1799900000,
  "last_stream_at": 1799900000
}
```

事件上报：

```json
{
  "type": "camera_event",
  "device_id": "cam-001",
  "event": "stream_failed",
  "severity": "warning",
  "snapshot_ref": "cam-001/2026-06-20T10-15-00.jpg",
  "timestamp": 1799900010
}
```

## 8. 可靠性与安全要点

- 摄像头离线不能影响热源控制、消防联动或主采集循环。
- RTSP 拉流必须单独线程 / 进程隔离，超时后重启，不要卡死主程序。
- 保存快照要有容量上限，例如按设备保留最近 N 张或最近 N 天。
- 摄像头账号密码必须放本地安全配置，不写进代码和 Git。
- 禁止默认开放公网访问摄像头 Web 页面或 RTSP 端口。
- 初次接入后修改默认密码，关闭不需要的 P2P 云服务和 UPnP。
- 对弱网络现场，要用子码流、低帧率、断线重连和退避重试。

## 9. 分阶段实施

| 阶段 | 目标 | 验收标准 |
|---|---|---|
| P0 台架验证 | 一台摄像头手工配置 RTSP | HMI 显示在线状态和最新快照 |
| P1 设备化 | 摄像头进入设备注册表 | 断电/断网/密码错误都有准确状态 |
| P2 ONVIF | 自动读取设备信息和 stream URL | 不手填 URL 也能拉取子码流 |
| P3 本地预览 | HMI 低码率预览 | 预览不拖慢主 HMI 和采集循环 |
| P4 事件联动 | 移动侦测/离线恢复上报 | MQTT 和本地日志都有事件记录 |
| P5 工程化 | 多摄像头、容量限制、权限控制 | 长时间运行不内存泄漏、不占满磁盘 |

## 10. 当前最建议的落地路线

先买或使用一台支持 ONVIF + RTSP 的有线 IP 摄像头，采用：

```text
PoE 摄像头 + PoE 交换机 + RK3506 同网段 + ONVIF 发现 + RTSP 子码流预览
```

项目里先实现“设备状态 + 快照 + 低码率预览”，等这条链路稳定后，再考虑录像、AI 识别、云端视频平台或多摄像头矩阵。

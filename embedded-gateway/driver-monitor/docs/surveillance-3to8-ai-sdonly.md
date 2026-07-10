# 安防监控部署方案：3–8 路 · AI 检测 · 无 NVR（SD 卡录像）

> 场景参数（已确认）：**3–8 路摄像头 · 要 AI 检测（人体/人脸）· 不加 NVR，连续录像只用摄像头 SD 卡**。
> 管线内部细节见 [`edge-video-processing-pipeline.md`](edge-video-processing-pipeline.md)；本文只讲**这套部署怎么落**。
> 更新日期：2026-07-10。

## 0. 一句话方案

**摄像头主码流录到各自 SD 卡（连续录像本地兜底），子码流给视觉盒做人体/人脸检测，只在检测到事件时把关键帧 + 短 clip 经上传代理传 OSS。** 连续录像本地、事件证据上云——两条路分开。**RK3506 在这套里没有角色**（无 VPU/NPU、224MB，干不了视频）。

## 1. 拓扑

```
3–8 台 IP 摄像头(双码流 + SD 卡槽 + H.265)
   ├─ 主码流 ─► 各自 SD 卡(循环覆盖,连续录像)          ← 本地,不上云
   └─ 子码流(RTSP,~640×360) ─►
                    视觉盒(RK3568 类,VPU + NPU)
                    取流 → MPP 解码 → YOLO 人体 → RetinaFace 人脸 → 事件状态机 → 截关键帧
                         │ 事件元数据 + 关键帧 + 短 clip  (本地 HTTP ship;盒子无外网)
                         ▼
                    上传代理(有网节点,双网卡)
                    media_agent: MediaOutbox(SpoolStore) → OSS    +    MQTT → 云(告警)
                         ▼
                OSS(事件证据,presign 临时链接给人看) + 手机/平台(告警)
```

**核心原则**：连续录像（大、本地、SD/未来 NVR）与事件证据（小、上云、OSS）**分离**；视频字节永不经过 RK3506。

## 2. 设备清单（BOM）

| # | 设备 | 数量 | 要点 |
|---|---|---|---|
| 1 | IP 摄像头（双码流 + SD 卡槽 + H.265 + 本地录像） | 3–8 | 主码流录卡、子码流给 AI；海康/大华/雄迈等 |
| 2 | 监控级 microSD 卡 | 每台 1 张 | **256–512GB 高耐久**（WD Purple / 海康监控卡，勿用普通消费卡） |
| 3 | 视觉盒（RK3568 类，**RKNN NPU + MPP VPU**） | **1（≤4 路）/ 2（6–8 路或要低延迟）** | BL410 若确有 VPU/NPU 可复用；**RK3506 不行** |
| 4 | 上传代理节点（有网、双网卡） | 1 | 小龙虾类或小工控机；跑 `media_agent` |
| 5 | 云 | — | 阿里云 OSS `ubuntu-oss-313` + 可选 MQTT broker（阿里云 IoT / EMQX）收告警 |

## 3. 存储三层

| 层 | 存哪 | 容量/说明 |
|---|---|---|
| **连续录像**（7×24 主码流） | 摄像头 SD 卡 | 1080p H.265 ~2–4 Mbps ≈ 1–2 GB/小时/路；256GB ≈ 7–14 天/路、512GB ≈ 2–4 周/路，循环覆盖 |
| **事件证据**（关键帧 + 短 clip） | **OSS** | 只在检测到人时上传，量极小、持久；presign 出临时链接给人看 |
| **告警元数据**（事件、人数、置信度、证据 URL） | MQTT → 云/手机 | 事件即推 |

## 4. 一次事件走完全程

1. 视觉盒子码流检出人 → 事件状态机 `IDLE→TENTATIVE`，**同时立即截 first_frame**。
2. K/M 多帧确认 → `PERSON_PRESENT`，事件 OPEN。
3. 期间按节流截代表帧；每帧 → 板子侧 spool `enqueue` → ship 到代理（本地 HTTP）。
4. 代理 `MediaOutbox` 传 OSS，`on_uploaded` 把 `evidence_status` pending→uploaded。
5. 人离开 → 事件 CLOSE；可从摄像头主码流/盒子环形缓冲取事件前后一小段 clip 一并上传。
6. 告警元数据（带 OSS presign URL）经 MQTT 推手机/平台。
7. **盒子/代理离线或崩溃**：证据留本地队列（落盘），联网/重启后按原始时间序补传，**绝不静默丢**。

## 5. 我们现成代码接哪（均已真机验证）

| 位置 | 组件 | 说明 |
|---|---|---|
| 视觉盒 | `capture.keyframe.KeyframeThrottle` | 事件 OPEN 立即 first_frame，期间节流截代表帧 |
| 视觉盒 | `uplink.media_outbox.MediaOutbox(RelayUploader→代理, store=SpoolStore)` | 板子侧 spool：ship 到代理，代理下线留队重试，落盘跨重启 |
| 视觉盒 | driver-monitor vision 管线（YOLO 人体 + RetinaFace 人脸，RKNN） | 检测 |
| 代理 | `scripts/media_agent.py` | `MediaReceiver → MediaOutbox(SpoolStore) → AliyunOSSUploader`，env 配置，可 systemd 拉起 |
| 看证据 | `oss_media.AliyunOSSUploader.presign_get` | 私有桶对象临时可访问 URL |

**已验证**：纯标准库、板上 python3.8.10 跑 14 测试全绿零改动；OSS/R2 上传真机 200 + presign 无鉴权 GET 200；板子→代理→OSS 全链、跨重启不丢。

## 6. 无 NVR + 只用 SD 卡：四个坑（要认）

1. **SD 卡是易坏点**：单卡消费级易损。缓解——**事件证据已上 OSS**，某台 SD 坏了**事件片段云上还在**，只丢那段连续录像。这正是"事件上云"补 SD 不可靠的价值；但长期保连续录像 SD-only 终不如 NVR 稳。
2. **单卡容量 = 保留期短**：1 个月以上连续录像，256GB 不够，需 512GB/1TB 卡或最终加 NVR。
3. **无集中回放**：连续录像逐台调（厂家 App）；事件证据有 OSS 集中看，连续流无统一入口。
4. **AI 多路 = NPU 时间片轮询**：一个盒带 8 路，每路分析帧率降、人进画面到告警延迟变长。**3–4 路一个盒较从容；6–8 路且要低延迟上 2 个盒或降每路帧率**——必须压测（单 RetinaFace 320 实测 8.3fps，唯一实测数字）。

## 7. 按路数的具体建议

- **3–4 路**：1 个视觉盒 + 每台 256GB 卡，够用。
- **6–8 路**：2 个视觉盒（各带 3–4 路）或接受每路低帧率；卡按保留期 256–512GB。
- **代理**：小龙虾类有网节点即可（已验证能到 OSS）。

## 8. 压测清单（多摄像头 AI 必做，见 edge-video §19）

1. 单路子码流 + MPP 长时间稳定取流。
2. YOLOv8n 单模型真实人体召回和吞吐（白天/夜间/逆光/遮挡）。
3. YOLO + RetinaFace 门控串行吞吐（人进画面→事件 OPEN 端到端延迟）。
4. 目标路数并发/轮询下：CPU、NPU、内存、磁盘 I/O、温度。
5. 断网、摄像头重启、代理下线、进程崩溃、24h soak——验证证据不丢、补传正确。
6. 记录**每路实际分析帧率和最坏发现延迟**，写进验收口径（不能只说"接了几路"）。

## 9. NVR-ready

本方案是 **NVR-ready** 的：哪天嫌 SD-only 不稳/保留期短，**加一台 NVR 收所有主码流即可**，视觉盒 + 代理 + OSS 那套照旧——NVR 只补"连续录像"这一层，其余不动。

## 10. 视觉盒确认：BL410 = RK3568，直接可用（2026-07-10 上板实测）

**BL410（hostname BL410-bliiot，实为 TL3568-EVM 模组）= RK3568，视觉盒能力全就绪，无需另购设备：**

| 能力 | 证据 |
|---|---|
| SoC RK3568 | `/proc/device-tree/compatible` = `rockchip,rk3568`；4 核 A55 + 3.8G RAM |
| NPU（0.8 TOPS） | `fde40000.npu` + **RKNPU 驱动 v0.9.8** + `/dev/dri/renderD129` |
| RKNN 运行时 | `/usr/lib/librknnrt.so`(v2.3.2) + **rknnlite python3.8 API**（板上直接跑模型） |
| VPU 硬解 | `/dev/mpp_service` + `librockchip_mpp.so.1`（H.264/H.265） |
| RGA 预处理 | `/dev/rga` + `librga.so.2` |
| 取流 | `gst-launch-1.0`（无 ffmpeg） |

同时 python3.8.10 已验证跑我们纯标准库管线 14 测试全绿。**故视觉盒直接用 BL410**，检测（YOLO 人体 + RetinaFace 人脸，RKNN+MPP+RGA）与上传管线（KeyframeThrottle + 板子侧 spool）同板跑。容量：单 RetinaFace 320 ~8.3fps，3–4 路较从容、6–8 路需 2 块或降帧率。

## 11. 待确认 / 下一步

- 视觉盒检测管线接 live RTSP（需真摄像头 + gst）与真帧编码（`write_png`）——上板阶段做。
- 代理侧 OSS 凭证下发方式（环境变量 / 文件）与 systemd 自启。
- 摄像头选型确认支持子码流 + 本地录像 + RTSP 标准。
- 网络：板子段（enp3s0 192.168.1.x）与 WiFi LAN 子网重叠，回程路由脆（Mac DHCP 变即失效）；长期宜把板子段挪出 192.168.1.x（需改板子 IP，谨慎）。

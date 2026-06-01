# 热源边缘控制网关调研对比报告

> 用途：供暖公司热源控制、数据采集、能耗优化、现场展示、远程运维、视频事件监测方案调研。  
> 结论版本：2026-06-01  
> 推荐结论：基础控制优先采用 `RK3506 + MCU`；需要较完整边缘网关能力采用 `RK3568 + MCU`；只有本地多路视频 AI 分析才考虑 `RK3588 + MCU`。

## 1. 汇报摘要

热源控制场景的核心目标不是单纯追求高算力，而是稳定采集、可靠控制、安全保护、低成本部署和可远程运维。

推荐产品分层：

| 产品档位 | 推荐硬件 | 适用场景 | 核心理由 |
|---|---|---|---|
| 标准版热源控制终端 | `RK3506 + MCU` | 数据采集、本地 HMI、MQTT 上传、普通控制、MCU 安全兜底 | 成本低、功耗低、足够稳定 |
| 增强版边缘网关 | `RK3568 + MCU` | 多协议接入、本地规则引擎、SQLite 缓存、较完整 Web UI、轻量视频预览/轻量 AI | 资源更充足，可承载 Node/Go/Python 边缘应用 |
| 高配视频 AI 边缘主机 | `RK3588 + MCU` | 5 路视频本地 AI 分析、录像缓存、复杂 Web 管理、Docker 多服务 | 算力强，但成本、功耗、散热、系统复杂度明显上升 |

建议第一阶段不要把控制系统和视频 AI 强绑在同一硬件上。更稳妥的架构是：

```text
RK3506/RK3568：热源控制、采集、HMI、MQTT、事件上报
MCU：急停、超温、超压、看门狗、安全输出
智能摄像头/NVR/平台：视频检测、录像、回放
```

如果明确要求“5 路视频都在本地做人形/入侵/烟火分析”，再升级到 RK3588。

## 2. 系统总架构

建议把现场系统拆成四层：

```text
现场设备层
  传感器、热量表、电表、压力/温度、泵阀、摄像头、DAQ、MCU

边缘控制层
  RK3506 / RK3568 / RK3588
  负责采集、展示、普通控制、缓存、联网、平台通信

安全保护层
  MCU
  负责急停、超温、超压、看门狗、RK 死机保护、安全继电器

平台层
  MQTT Broker、业务平台、数据存储、视频平台、告警、报表、远程运维
```

职责边界：

| 模块 | 主要职责 | 是否硬实时 | 失效后果 | 建议实现 |
|---|---|---:|---|---|
| RK 主控 | 采集、HMI、联网、普通控制、策略优化 | 否 | 可降级运行 | Linux 应用 |
| MCU | 急停、安全保护、看门狗、继电器兜底 | 是 | 必须进入安全状态 | 裸机/RTOS 固件 |
| 平台 | 远程监控、报表、运维、录像管理 | 否 | 本地继续运行 | 云/机房服务器 |
| 摄像头/NVR | 视频编码、事件检测、录像 | 否 | 视频功能降级 | 智能摄像头/NVR/视频平台 |

## 3. 协议与设备角色对比

这些名词容易混在一起，实际应分成四类：

```text
设备：MCU、DAQ、热量表、PLC、摄像头
通道：串口、RS485、USB、以太网、CAN
现场协议：Modbus、OPC UA、厂家私有协议、MCU 自定义协议
平台协议：MQTT、HTTP/HTTPS、WebSocket
```

### 3.1 总览对比

| 名称 | 本质 | 常见连接 | 主要用途 | 在本项目中的位置 | 优先级 |
|---|---|---|---|---|---|
| Modbus RTU | 工业现场协议 | RS485/串口 | 热表、电表、变频器、IO 模块 | 现场设备到 RK | 高 |
| Modbus TCP | 工业现场协议 | 以太网 TCP | PLC、网关、仪表 | 现场设备到 RK | 高 |
| MQTT | 平台消息协议 | TCP/IP | 心跳、数据、报警、命令下发 | RK 到平台 | 高 |
| OPC UA | 工业数据互操作协议 | TCP/IP | PLC/SCADA/工厂系统集成 | 大客户或既有 PLC 场景 | 中/后置 |
| 串口/UART/RS485 | 通信通道 | TTL/RS232/RS485 | MCU、仪表、私有协议 | 设备/MCU 到 RK | 高 |
| DAQ | 数据采集硬件 | USB/以太网/SDK | AI/DI/AO 采集 | 传感器到 RK | 原型高，量产待定 |
| MCU | 微控制器硬件 | UART/RS485/CAN/SPI | 安全保护、看门狗、继电器 | 安全协处理器 | 最高 |

### 3.2 Modbus

Modbus 是工业现场最常见的设备协议。Modbus Organization 的介绍说明，Modbus 是应用层协议，可运行在 RS232、RS485、以太网 TCP/IP 等底层网络上。

两种常用形态：

| 类型 | 物理层 | 典型设备 | 优点 | 注意点 |
|---|---|---|---|---|
| Modbus RTU | RS485 | 热量表、电表、变频器、IO 模块 | 抗干扰、现场常见、成本低 | 需要处理波特率、站号、CRC、总线冲突 |
| Modbus TCP | 以太网 | PLC、网关、以太网仪表 | 调试方便、速度快、布线清晰 | 依赖网络稳定性 |

在热源场景中的典型点位：

```text
供水温度
回水温度
供水压力
回水压力
瞬时流量
累计热量
泵频率
泵运行状态
阀门开度
电表功率
```

实现建议：

```text
RK3506/RK3568 上实现 Modbus client
按点表轮询寄存器
统一换算为工程量
写入 latest.json / SQLite / MQTT payload
```

### 3.3 MQTT

MQTT 是设备和平台之间的轻量消息协议。MQTT 官网说明其为 OASIS 标准，采用发布/订阅模式，适合低带宽、不稳定网络和受限设备。

常见角色：

```text
RK 设备端：MQTT client
平台服务器：MQTT broker
平台业务系统：另一个 MQTT client / 后端消费者
```

典型 Topic：

```text
heat/{device_id}/heartbeat
heat/{device_id}/telemetry
heat/{device_id}/alarm
heat/{device_id}/status
heat/{device_id}/command
heat/{device_id}/ota
```

典型 payload：

```json
{
  "device_id": "heat-rk3506-001",
  "ts": "2026-06-01T10:00:00+08:00",
  "points": {
    "supply_temp": 62.3,
    "return_temp": 48.1,
    "pressure": 0.42
  }
}
```

资源消耗：

| 实现 | 资源占用 | 适用阶段 |
|---|---|---|
| C/C++ libmosquitto / Paho C | 低，常见为 MB 级以内到少量 MB | 量产推荐 |
| Go MQTT client | 中低，单二进制部署方便 | RK3506/RK3568 可用 |
| Python paho-mqtt | 中，Python 运行时会占更多内存 | 原型验证 |
| Node MQTT | 中高，依赖 Node 运行时 | RK3568 以上更合适 |

结论：MQTT client 不需要上 RK3568，RK3506 足够；如果本地还要跑 MQTT broker、多协议网关和复杂缓存，RK3568 更合适。

### 3.4 OPC UA

OPC UA 是面向工业系统互联的数据协议。OPC Foundation 说明其是平台无关、面向服务的架构，整合 OPC Classic 功能，并提供更安全、可扩展的方案。

适合：

```text
对接 PLC
对接 SCADA
对接大型工厂已有工业软件
需要结构化数据模型
需要标准安全机制
```

不适合第一阶段作为主线：

```text
协议较重
开发调试成本高
小板资源占用比 Modbus/MQTT 高
供暖热源现场很多设备仍以 Modbus/RS485 为主
```

建议：第一阶段优先 Modbus + MQTT；OPC UA 作为大客户/既有 PLC 系统的可选插件。

### 3.5 串口、RS485、CAN

串口不是协议，而是通道。上面可以跑：

```text
Modbus RTU
MCU 自定义协议
厂家私有协议
ASCII 命令
二进制帧
```

通道对比：

| 通道 | 特点 | 适合场景 |
|---|---|---|
| UART TTL | 简单、板内短距离 | RK 与 MCU 板内通信 |
| RS485 | 抗干扰、远距离、多从站 | 热表、电表、IO 模块、现场总线 |
| RS232 | 老设备常见 | 旧仪表/旧工控设备 |
| CAN | 实时性和抗干扰好 | 多控制器、强可靠控制网络 |

建议：

```text
RK ↔ MCU：UART TTL 或 RS485
现场仪表：RS485 Modbus RTU
复杂控制网络：预留 CAN
```

### 3.6 DAQ4212 / DAQ 设备

DAQ 是数据采集硬件，不是协议。DAQ4212 适合把模拟量/数字量快速接入系统。

在本项目中的定位：

```text
压力/温度变送器
        ↓
DAQ4212
        ↓ USB 厂家 SDK
RK
        ↓
统一点位 / HMI / MQTT
```

优点：

```text
原型验证快
AI/DI 能力现成
不必先自研采集板
```

风险：

```text
依赖厂家 SDK
USB vendor-specific，不能当普通串口
量产成本和供货要评估
ARM32/ARM64 库兼容性要确认
```

建议：

```text
原型阶段：使用 DAQ4212 快速验证采集逻辑
量产阶段：评估自研 MCU/ADC/隔离 IO 板，降低成本和供应链风险
```

### 3.7 MCU

MCU 是安全协处理器，不是通信协议。

建议 MCU 负责：

```text
急停输入
超温/超压保护
漏水/烟感/门禁等安全输入
继电器安全输出
RK 心跳看门狗
RK 死机后进入安全模式
最小报警状态上报
```

RK 负责：

```text
普通控制策略
HMI
采集
联网
MQTT
日志
远程配置
```

控制边界：

```text
普通控制：RK 决策，MCU 执行/监督
紧急保护：MCU 直接决策，不等待 RK
```

## 4. RK3506 / RK3568 / RK3588 对比

### 4.1 能力对比

| 平台 | 定位 | 适合功能 | 不适合功能 |
|---|---|---|---|
| RK3506 | 轻量嵌入式 Linux 控制器 | 采集、HMI、MQTT client、Modbus、MCU 通信、简单 HTTP | Docker、多服务后端、多路视频 AI、大数据库 |
| RK3568 | 中档边缘网关 | 较完整 Web UI、Node/Go 后端、SQLite、规则引擎、多协议网关、轻量 AI/视频预览 | 5 路本地视频 AI 高负载 |
| RK3588 | 高性能边缘 AI 主机 | 多路视频分析、复杂 AI、Docker、多服务、边缘服务器 | 成本敏感、低功耗控制终端 |

公开资料参考：

- RK3506 官方资料显示其面向低功耗嵌入式场景，具备 Cortex-A7 与 M0 等资源，适合轻量控制与网关类应用。
- RK3568 公开资料中包含 NPU 资源，适合中档边缘计算、工业网关、轻量 AI 场景。
- RK3588 官方/公开资料标称 6 TOPS NPU，面向高性能 AI、多媒体和边缘计算场景。

### 4.2 成本与复杂度

公开开发板/核心板价格会随渠道变化，但量级差异明确：

| 平台 | 成本趋势 | 额外成本 |
|---|---|---|
| RK3506 | 低 | 存储/内存较小，系统简单 |
| RK3568 | 中 | 更大内存/eMMC，散热和系统复杂度适中 |
| RK3588 | 高 | 8GB/16GB 内存、SSD/大 eMMC、散热、电源、PCB 和软件维护成本显著增加 |

成本不是只看芯片，还包括：

```text
内存容量
eMMC/SSD
电源设计
散热
PCB 层数
系统镜像维护
驱动适配
量产测试
售后运维
```

### 4.3 场景选择

| 需求 | RK3506 | RK3568 | RK3588 |
|---|---:|---:|---:|
| Modbus 采集 | 适合 | 适合 | 适合 |
| DAQ SDK 采集 | 适合，但需确认 ARM32/库兼容 | 适合 | 适合 |
| MCU 安全协同 | 适合 | 适合 | 适合 |
| MQTT client | 适合 | 适合 | 适合 |
| 本地 HMI | 轻量 HMI | 完整 HMI | 复杂 HMI |
| Node/Go 边缘后端 | 只建议轻量 Go 单进程 | 适合 | 适合 |
| SQLite 缓存 | 小规模 | 适合 | 适合 |
| Docker | 不建议 | 可评估 | 适合 |
| 1-2 路轻量视频预览 | 不建议 | 可做 | 适合 |
| 5 路事件录像，不本地 AI | 不直接处理，交给摄像头/平台 | 可本地缓存 | 适合 |
| 5 路本地 AI 视频分析 | 不适合 | 吃紧 | 推荐 |

## 5. 视频监测方案对比

需求：有人进出设备间时录像并上传。

### 5.1 不做本地 AI，只做事件录像

推荐方案：

```text
智能 IP 摄像头 / NVR 检测人形或移动
        ↓
RK 接收事件或平台接收事件
        ↓
平台拉取/保存录像
        ↓
RK 上传热源侧状态和告警
```

适合硬件：

```text
RK3506 + MCU
```

优点：

```text
控制系统稳定
成本低
视频和控制解耦
摄像头/NVR 负责视频编码和录像
```

### 5.2 本地轻量视频预览/缓存

适合硬件：

```text
RK3568 + MCU
```

适合：

```text
少量画面预览
事件短视频缓存
断网后补传
低帧率轻量分析
```

### 5.3 本地 5 路视频 AI 分析

适合硬件：

```text
RK3588 + MCU
```

适合：

```text
5 路人形检测
烟火识别
人员闯入
设备间异常行为
本地录像切片
复杂 Web 管理
```

建议：不要让视频 AI 影响安全控制。即使用 RK3588，也保留 MCU 做安全兜底。

## 6. 软件部署形态

### 6.1 RK3506 推荐部署

```text
/userdata/energy-agent/
├── energy-agent        # Go/C/C++ 单进程，或轻量 Python 原型
├── adapters/
├── config/
├── web/
├── data/
└── logs/
```

推荐能力：

```text
采集
MCU 通信
MQTT client
简单 HTTP API
本地 HMI 静态页面
小型缓存
```

不推荐：

```text
Docker
完整 Node 后端
大规模本地数据库
复杂视频分析
```

### 6.2 RK3568 推荐部署

```text
/opt/energy-edge/
├── backend/            # Go/Node/Python
├── frontend/           # Web UI
├── adapters/
├── data/               # SQLite
├── logs/
└── services/
```

可承载：

```text
较完整边缘网关
多协议插件
规则引擎
SQLite 历史数据
本地 HMI
MQTT client / 可选 broker
轻量视频预览
```

### 6.3 RK3588 推荐部署

```text
Docker / systemd 多服务
视频 AI 推理服务
录像缓存服务
边缘 API 服务
HMI / 管理后台
MQTT / HTTP / WebSocket
```

注意：

```text
需要认真设计散热
需要更大内存和存储
需要完整 OTA/运维方案
软件复杂度接近边缘服务器
```

## 7. 产品建议

### 7.1 标准版：热源控制终端

推荐：

```text
RK3506 + MCU
```

功能：

```text
Modbus/DAQ/MCU 采集
本地轻量 HMI
MQTT 心跳/数据/报警
普通控制
MCU 安全保护
摄像头事件由摄像头/平台处理
```

适合：

```text
大规模铺设
成本敏感
以热源控制为主
视频只是辅助事件
```

### 7.2 增强版：热源边缘网关

推荐：

```text
RK3568 + MCU
```

功能：

```text
完整 Web UI
多协议适配
规则引擎
本地 SQLite 缓存
轻量视频预览/缓存
更复杂运维
```

适合：

```text
中心站房
协议多
需要本地自治能力
需要更强现场可视化
```

### 7.3 高配版：视频 AI 边缘主机

推荐：

```text
RK3588 + MCU
```

功能：

```text
5 路本地视频 AI
录像切片
复杂边缘服务
Docker
更复杂 HMI
```

适合：

```text
高价值站点
强视频 AI 需求
网络不稳定但要求本地分析
预算充足
```

## 8. 落地路线

建议分四阶段：

```text
Phase 1：RK3506 + MCU + 本地 HMI + MQTT 心跳
  目标：跑通主链路、设备在线、基础展示

Phase 2：Modbus / DAQ4212 / MCU 适配器
  目标：真实数据采集、点位模型、报警展示

Phase 3：平台联动
  目标：MQTT 数据上传、命令下发、远程配置、断网缓存

Phase 4：视频事件
  目标：摄像头/NVR/平台事件录像，必要时评估 RK3568/RK3588
```

第一版原则：

```text
不要先上重平台
不要先上 Docker
不要让视频 AI 影响安全控制
先把采集、控制、心跳、安全边界做扎实
```

## 9. 风险与待确认项

| 风险 | 说明 | 建议动作 |
|---|---|---|
| DAQ SDK 兼容 | DAQ4212 SDK 可能依赖特定 CPU 架构和动态库 | 确认 ARM32/ARM64 库，优先在目标板实测 |
| 现场协议碎片化 | 各厂家寄存器、倍率、字节序不同 | 建立点表模板和协议适配器 |
| RK3506 存储小 | `/userdata` 空间有限 | 控制日志和缓存，必要时外接存储 |
| 视频影响控制稳定性 | 视频解码/AI 会占用 CPU/内存/网络 | 控制和视频解耦，或升级硬件 |
| MQTT 断网数据堆积 | 网络不稳时缓存可能撑爆磁盘 | 限量队列、优先级、过期策略 |
| MCU/RK 责任不清 | 可能导致安全动作依赖 Linux | MCU 独立处理急停/超压/看门狗 |

## 10. 推荐结论

推荐领导层决策：

```text
1. 标准热源控制终端采用 RK3506 + MCU。
2. 控制安全能力必须由 MCU 兜底，不能完全依赖 Linux。
3. MQTT、Modbus、DAQ、HMI 均可在 RK3506 上做轻量实现。
4. 如果需要完整边缘网关能力，升级到 RK3568。
5. 只有明确要求 5 路本地视频 AI 分析，才上 RK3588。
6. 视频事件录像优先由智能摄像头/NVR/平台完成，RK 只接事件和联动。
```

建议当前产品路线：

```text
标准版：RK3506 + MCU + MQTT + Modbus/DAQ + 轻量 HMI
增强版：RK3568 + MCU + 完整边缘网关 + 轻量视频
高配版：RK3588 + MCU + 多路视频 AI
```

## 参考资料

- Modbus Organization — Modbus Specifications: https://www.modbus.org/modbus-specifications
- Modbus Organization — Introduction to Modbus: https://www.modbus.org/introduction-to-modbus
- MQTT.org — MQTT FAQ / OASIS standard description: https://mqtt.org/faq/
- MQTT.org — MQTT Specification: https://mqtt.org/mqtt-specification/
- Eclipse Paho MQTT Clients: https://eclipse.dev/paho/downloads/
- OPC Foundation — Unified Architecture: https://opcfoundation.org/developer-tools/specifications-unified-architecture
- OPC Foundation — What is OPC: https://opcfoundation.org/about/what-is-opc/
- Rockchip RK3506 product page: https://www.rock-chips.com/a/en/products/RK35_Series/2025/1208/2126.html
- Waveshare/Luckfox Core3506 reference board: https://www.waveshare.com/core3506.htm
- Rockchip RK3588 product/spec references: https://rockchips.net/product/rk3588/ and https://www.rock-chips.com/a/en/products/RK35_Series/2022/0926/1660.html

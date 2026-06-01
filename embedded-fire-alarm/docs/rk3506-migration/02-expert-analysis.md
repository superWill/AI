# Expert Analysis

## Product Positioning

建议把产品定义为：

> 新一代可配置消防报警/联动控制主机平台，兼容传统二总线现场设备，提供嵌入式 HMI、内置网关、主机互联、远程运维，并预留安防/视频 AI 扩展能力。

不要定义为“把单片机换成 RK3506”。客户买的不是芯片，而是：

- 定制快：不同项目的界面、点表、联动逻辑、设备类型可以配置化。
- 维护省：现场人员少时，能自动诊断、导出报告、远程协助。
- 扩展强：消防基础上叠加安防、视频、事件复盘、设备健康度。
- 合规稳：消防核心功能不因联网、AI、HMI 改动而失效。

## Why MCU Customization Is Expensive

现有单片机方案的痛点通常来自：

- UI 按坐标硬编码，换屏幕/换布局/换客户需求都要改固件。
- 按键逻辑、菜单、点表、联动逻辑固化在程序里。
- 现场调试依赖工程师和串口/专用工具。
- 日志、升级、远程诊断能力弱。
- 一旦客户要“多语言、图形化、联网、导出报表、摄像头”等能力，MCU 开发效率明显下降。

嵌入式平台的价值是把这些变成配置、页面和服务，而不是每次改底层固件。

## Proposed Architecture

```text
┌────────────────────────────────────────────────────────────┐
│ RK3506 Linux / Application Layer                           │
│ - HMI / Web UI / local display                             │
│ - point table editor / project configuration               │
│ - logs / reports / remote maintenance                      │
│ - Ethernet gateway / RS485 host interconnect               │
│ - optional video capture + AI assisted analysis            │
└──────────────┬─────────────────────────────────────────────┘
               │ IPC / shared memory / UART / SPI
┌──────────────▼─────────────────────────────────────────────┐
│ Real-time Safety Controller                                │
│ - two-wire bus polling and timing                          │
│ - alarm state acquisition                                  │
│ - interlock output critical path                           │
│ - watchdog / degraded mode                                 │
│ - hardware key/manual priority path                        │
└──────────────┬─────────────────────────────────────────────┘
               │
┌──────────────▼─────────────────────────────────────────────┐
│ Field Layer                                                │
│ - two-wire detectors/modules                               │
│ - relay outputs / feedback inputs                          │
│ - power, battery, short/open diagnostics                   │
└────────────────────────────────────────────────────────────┘
```

可选实现：

1. RK3506 Cortex-M0 跑实时安全控制，Cortex-A7/Linux 跑 HMI 和上层服务。
2. RK3506 + 外置小 MCU，外置 MCU 负责二总线和联动硬实时链路。
3. RK3506 只做 HMI/网关，原 MCU 保留作为安全控制内核，作为第一代低风险迁移方案。

最推荐先做第 3 种或第 2 种，降低认证和现场风险。等二总线、联动、故障处理充分验证后，再评估是否把更多实时功能收敛到 RK3506 内部。

## Business Expansion Ideas

### Near-term Add-ons

- 图形化点表配置：楼层、区域、设备地址、设备类型、安装位置。
- 联动逻辑配置器：把“烟感 + 手报 -> 声光/卷帘/风机/电梯”等规则做成可审计配置。
- 调试助手：自动扫描设备、地址冲突检测、缺失设备提示。
- 维护报告：导出故障、屏蔽、报警、复位、操作记录。
- 远程协助：网关内置，允许授权后远程查看状态和日志。

### Differentiating Add-ons

- 视频联动复核：火警区域对应摄像头画面自动弹出。
- 2 路视频采集 + 辅助分析：烟雾/火焰/人员滞留/通道占用，仅作为辅助提示。
- 巡检模式：提示人员按区域测试探测器、手报、声光、反馈。
- 设备健康度：根据误报率、故障率、离线次数评估设备质量。
- 多主机 RS485 互联：跨楼层/厂区主机事件同步和集中显示。

## Fire-domain Boundaries

必须保持边界：

- AI 不能替代国标规定的火警判定链路。
- 视频分析不能作为唯一火警触发源进入强制联动。
- 远程操作不能绕过本机权限、钥匙开关和联动优先级。
- 网络、云、网关故障不能导致本机报警和联动失效。
- HMI 崩溃时，硬件指示灯、蜂鸣器、关键按键、联动输出仍应工作。

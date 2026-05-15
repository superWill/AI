# Core Board + Custom Carrier Bring-up Flow

> 状态：流程梳理  
> 场景：公司购买核心板 / 主板，自研底板 / 载板 / carrier board。  
> 目标：明确从硬件资料准备、底板设计、系统适配、烧录、应用集成到量产的完整流程。

## 1. 基本概念

购买核心板后，公司自己设计底板，本质上是在做：

```text
核心板 / 主板 / SoM
        |
        v
自研底板 / 载板 / Carrier Board
        |
        v
完整工业控制设备
```

核心板通常提供：

- CPU / SoC
- DDR
- eMMC / NAND / Flash
- PMIC 或部分电源
- 基础启动能力

底板负责把核心板能力变成产品接口：

- 电源输入
- 调试串口
- 网口
- USB
- 显示屏
- 触摸
- RS485 / CAN
- DI / DO / AI / AO
- 继电器
- 工业端子
- 防护、电源隔离、结构连接

## 2. 烧录到底烧什么

烧录不是只烧自己写的 APP，而是烧一套设备系统。

典型系统分层：

```text
BootROM            芯片内部固化，不能改
Bootloader         U-Boot / vendor loader
Kernel             Linux 内核
Device Tree        硬件描述，适配自研底板
RootFS             Ubuntu / Buildroot / Yocto 文件系统
Drivers            网口、屏幕、GPIO、RS485、CAN 等驱动
Application        热能控制后端、HMI、配置、systemd 服务
Data               点表、参数、数据库、运行日志
```

不同阶段的“烧录”对象不同：

| 阶段 | 通常烧录内容 | 说明 |
|---|---|---|
| 早期验证 | 厂家完整镜像 | 先证明核心板能启动 |
| 底板 bring-up | Bootloader / Kernel / DTB / RootFS | 适配电源、网口、屏幕、GPIO 等 |
| 应用开发 | 不烧录，直接部署 APP | `scp` + `install.sh` + `systemctl restart` |
| 量产 | 完整系统镜像 | 镜像里包含 OS、驱动、APP、默认配置 |
| OTA | 应用包或系统分区 | 根据升级策略决定 |

简单判断：

```text
只改应用逻辑 -> 部署 APP
改底板硬件引脚 -> 改设备树 / 驱动，重新烧系统
做出厂设备 -> 烧完整量产镜像
```

## 3. 第一阶段：向厂家索要资料

自研底板前必须先拿到资料。

### 3.1 硬件资料

向核心板厂家索要：

```text
核心板原理图
核心板 PCB 封装 / 连接器定义
核心板引脚定义表
底板参考原理图
底板参考 PCB
电源输入范围和电源时序
启动模式说明
调试串口说明
USB OTG / MASKROM / RECOVERY 说明
网口设计参考
显示接口设计参考
GPIO 复用表
ESD / TVS / EMC 推荐设计
```

### 3.2 软件资料

向厂家索要：

```text
BSP / SDK
Linux kernel source
U-Boot source
Device Tree DTS
RootFS 构建方式
预编译镜像
烧录工具
烧录文档
分区表
恢复模式 / MASKROM 进入方法
驱动补丁
出厂测试工具
```

### 3.3 必问问题

```text
核心板推荐供电电压、电流、纹波要求？
哪些电源由核心板自带，哪些必须底板提供？
调试串口电平是 3.3V TTL 还是 RS232？
网口是否核心板内置 PHY？
屏幕接口支持哪些分辨率和时序？
GPIO 是否 3.3V 容忍？是否有 1.8V IO？
启动介质是 eMMC、NAND、TF 还是 SPI Flash？
是否支持双分区 A/B OTA？
是否提供量产烧录工具？
```

## 4. 第二阶段：底板最小硬件设计

第一版底板不要一口气做满，先确保能启动、能救砖、能调试。

最小必需模块：

```text
DC 输入
电源保护
核心板供电
RESET 按键
BOOT / MASKROM / RECOVERY 按键
调试串口
USB OTG / 烧录口
至少 1 路以太网
状态 LED
必要的安装孔和连接器
```

第一版建议保留测试点：

```text
VIN
5V
3.3V
1.8V
RESET
BOOT_MODE
UART_TX/RX
关键 GPIO
RS485 A/B
CAN H/L
```

## 5. 第三阶段：工业接口设计

热能控制设备通常需要现场 IO，不能把现场线缆直接接 SoC GPIO。

### 5.1 DI 数字量输入

用途：

```text
烟感报警
水流开关
压力开关
门磁
故障反馈
手自动状态
泵运行反馈
```

推荐硬件结构：

```text
现场 24V / 干接点
        |
        v
限流 / 滤波 / TVS
        |
        v
光耦隔离
        |
        v
GPIO / 扩展 IO
```

需要确认：

```text
DI 是干接点输入还是湿接点输入
公共端是 COM、GND 还是 24V
输入电压范围
是否需要断线检测
是否需要隔离电源
```

### 5.2 DO 数字量输出

用途：

```text
声光报警器
风机启停
继电器
电磁阀
联动输出
```

推荐硬件结构：

```text
GPIO / 扩展 IO
        |
        v
光耦 / 驱动芯片
        |
        v
继电器 / MOSFET
        |
        v
输出端子
```

需要确认：

```text
输出是继电器还是晶体管
最大电压 / 电流
是否干接点输出
是否需要续流二极管
是否需要保险丝和 TVS
```

### 5.3 RS485 / CAN

RS485：

```text
SoC UART
  -> RS485 transceiver
  -> TVS / 共模电感 / 终端电阻
  -> A/B 端子
```

CAN：

```text
SoC CAN
  -> CAN transceiver
  -> TVS / 终端电阻
  -> CANH/CANL 端子
```

工业现场建议优先考虑隔离版收发器。

### 5.4 AI / AO

热能场景可能需要：

```text
4-20mA
0-10V
PT100 / PT1000
NTC
脉冲输入
```

这些通常不能直接接 SoC，需要：

```text
ADC
隔离
采样电阻
运放
滤波
保护
校准
```

## 6. 第四阶段：软件适配

自研底板后，Linux 要知道硬件怎么接。

通常需要改：

```text
Device Tree DTS
Kernel config
驱动参数
U-Boot 环境
RootFS 配置
应用配置
```

典型适配项：

| 外设 | 软件适配 |
|---|---|
| 网口 | PHY 类型、RGMII/RMII、reset GPIO、时钟 |
| 串口 | UART 复用、波特率、RS485 DE/RE 控制 |
| CAN | pinmux、bitrate、transceiver enable |
| 屏幕 | 分辨率、时序、背光 PWM、触摸 I2C/USB |
| DI/DO | GPIO 编号、输入极性、输出极性、去抖 |
| USB | Host/Device 模式、供电开关 |
| LED/按键 | GPIO key / LED 设备树节点 |

## 7. 第五阶段：第一次上电 bring-up

第一次上电建议按顺序来。

### 7.1 不插核心板检查底板

```text
检查短路
检查 VIN 到 GND 阻抗
检查 DC-DC 输出
检查 5V / 3.3V / 1.8V
检查电源纹波
检查上电时序
```

### 7.2 插核心板限流上电

```text
使用可调电源限流
观察启动电流
看电源 LED
摸温升
看调试串口日志
```

### 7.3 串口启动日志

必须先看到：

```text
BootROM / Loader
U-Boot
Kernel
RootFS login
```

如果串口没日志，优先查：

```text
电源
RESET
BOOT 模式
串口 TX/RX 是否接反
串口电平
波特率
```

## 8. 第六阶段：烧录与恢复

必须设计一条救砖路径。

常见方式：

```text
USB OTG 烧录
MASKROM 模式
RECOVERY 模式
TF 卡启动
串口控制 U-Boot
网络 TFTP 启动
```

烧录前要确认：

```text
烧录工具
固件格式
分区表
loader
update.img
boot.img
rootfs.img
dtb
```

建议流程：

```text
1. 用厂家开发板验证烧录工具
2. 用厂家参考底板验证烧录工具
3. 自研底板进入 MASKROM / Loader
4. 烧厂家原始镜像
5. 确认能启动
6. 再烧改过的 DTB / Kernel
7. 最后做完整量产镜像
```

## 9. 第七阶段：应用集成

在系统跑通后，再集成热能控制应用。

当前应用形态可参考：

```text
Nginx
  - /              -> HMI
  - /api/          -> 后端 API
  - /ws            -> 实时事件

systemd
  - 控制后端服务
  - kiosk 浏览器服务

APP
  - 能源管控 HMI
  - 接口事件提示
  - 设备点表
```

部署方式：

```text
开发阶段：scp 发布包 + install.sh
试产阶段：做离线安装包
量产阶段：打入完整系统镜像
```

量产镜像应包含：

```text
应用文件
systemd 服务
Nginx 配置
默认点表
默认参数
日志目录
数据目录
kiosk 自启动
```

## 10. 第八阶段：接口测试

### 10.1 网口

```bash
ip -br link
cat /sys/class/net/eth1/carrier
ping -c 3 192.168.1.20
```

### 10.2 USB

```bash
dmesg -wT | grep -Ei 'usb|ttyUSB|storage'
lsusb
ls /dev/ttyUSB*
```

### 10.3 DI 输入

```text
短接 DI 与 COM
观察 GPIO / 输入状态变化
检查软件事件
检查 HMI 提示
```

### 10.4 DO 输出

```text
软件置位输出
万用表测继电器 / 输出端子变化
接小负载测试
再接真实负载
```

### 10.5 RS485 / CAN

```text
接 USB-RS485 / CAN 分析仪
发测试帧
看收发方向
看终端电阻
看错误计数
```

## 11. 第九阶段：可靠性测试

至少做：

```text
冷启动
热启动
反复断电
网线插拔
USB 插拔
长时间运行
高低温
电源波动
输出带负载
通信异常
数据库掉电保护
日志写入寿命
```

热能控制重点：

```text
断网自治运行
传感器故障进入安全状态
超温保护
低压补水
泵阀联锁
手自动切换
本地屏异常不影响控制
```

## 12. 第十阶段：量产准备

量产前需要固化：

```text
硬件版本号
PCB 版本号
BOM
测试点定义
出厂测试程序
烧录镜像版本
序列号写入方式
MAC 地址写入方式
默认配置
恢复出厂方法
升级方法
问题追踪表
```

建议每台设备出厂记录：

```text
SN
MAC
硬件版本
系统镜像版本
APP 版本
测试时间
测试人员
DI/DO 测试结果
RS485/CAN 测试结果
网口/USB/屏幕测试结果
老化测试结果
```

## 13. 推荐项目推进顺序

```text
1. 厂家开发板跑通系统和应用
2. 梳理全部现场接口和端子定义
3. 画自研底板第一版，只做最小可运行闭环
4. 上电 bring-up，串口进系统
5. 调通网口、USB、屏幕
6. 调通 DI/DO
7. 调通 RS485/CAN
8. 改 DTS / 驱动 / 配置
9. 集成热能控制 APP
10. 做整机测试
11. 做第二版底板修正
12. 做量产镜像和出厂测试流程
```

## 14. 当前结论

1. 如果只买核心板，自研底板，工作重点不只是写 APP，还包括电源、调试、烧录、恢复、外设、电气保护和系统适配。
2. 烧录通常烧的是完整系统镜像，APP 只是其中一层。
3. 自研底板后最容易变的是 Device Tree 和驱动配置。
4. 第一版底板优先保证：能供电、能串口、能烧录、能联网、能显示。
5. 工业 DI/DO 不要直接接 SoC GPIO，必须做隔离和保护。
6. 热能控制应用最终应打入量产镜像，并通过 systemd / Nginx / kiosk 开机自启动。

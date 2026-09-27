# BL412B-SOM412-X23-Y31-Y41 Terminal Map

> 设备型号：`BL412B-SOM412-X23-Y31-Y41`  
> 工作电压：`12~24VDC`  
> 固件：Ubuntu 20.04  
> 默认 ETH1 IP：`192.168.1.110`

## 0. 已确认硬件基线

以下配置来自北莱原厂 `ARMxy BL410 Series Datasheet V1.0` 和
`ARMxy Series BL410 User Manual V1.1` 的型号选型表，不是根据
`aarch64` 架构或外观推测：

| 层级 | 当前型号 | 已确认配置 |
|---|---|---|
| 主机 | `BL412B` | 3 路 10/100M Ethernet、2 路 USB 2.0 Host、1 路 HDMI、1 个 20PIN X 板插槽、2 个 Y 板插槽，`48 x 83 x 110mm` |
| 核心板 | `SOM412` | Rockchip RK3568J、4 核 Cortex-A55、1.8GHz、1 TOPS NPU、4GB LPDDR4X、32GB eMMC、工业级 `-40~85°C` |
| X 板 | `X23` | 4 路 RS232/RS485、4 路 DI、4 路 DO |
| Y1 板 | `Y31` | 4 路单端 AI，支持 `0~20mA` / `4~20mA` |
| Y2 板 | `Y41` | 4 路 AO，支持 `0~20mA` / `4~20mA` |

因此，当前设备不是待确认的泛化 ARM 工业机，而是已经确认的
`RK3568J + 4GB RAM + 32GB eMMC + 1 TOPS NPU` 工业计算机。

BL410 系列原厂资料还给出以下平台能力：

| 能力 | 原厂规格 | 对当前设备的意义 |
|---|---|---|
| GPU | Mali-G52-2EE | 可承担图形显示，但不应替代 NPU 做主要神经网络推理 |
| 视频 | H.264/H.265 最高 4K@60 解码、1080p@60 编码 | 单路 1080p 网络摄像机硬件解码在芯片能力范围内 |
| HDMI | 最高 4096x2160@60 | 可接本地显示器；与摄像机输入链路无关 |
| 网络 | 3 路 100M RJ45，自适应 MDI/MDIX | 可规划摄像机、控制网和上联网分口；实际隔离方式由系统网络配置决定 |
| 看门狗 | 独立硬件看门狗 | 适合无人值守恢复；量产前需验证当前驱动和喂狗策略 |
| RTC | 外置 RTC | 可用于断网事件时间戳；需配置系统时钟同步 |
| 供电 | 12~24VDC，反接保护 | 摄像机仍需按其规格独立供电或使用合规 PoE 方案 |

原厂数据表把 `Encoder`/`Decoder` 标签和后面的英文能力描述写反。
本文按能力描述和 RK3568 平台能力记录为“4K@60 解码、1080p@60 编码”，
不沿用错误标签。

## 1. 型号含义

```text
BL412B   ARM 工业计算机主机型号
SOM412   RK3568J / 4GB LPDDR4X / 32GB eMMC 工业级核心板
X23      X 系列 I/O 板
Y31      Y 系列 I/O 板，4 路模拟量输入
Y41      Y 系列 I/O 板，4 路模拟量输出
```

## 2. 厂家绑定项

下面这些接口、命令和命名方式是当前 BL412B / 北莱工业机平台绑定项，不应当当成通用 Linux 标准接口：

| 项目 | 示例 | 绑定说明 | 迁移影响 |
|---|---|---|---|
| 工业机型号 | `BL412B-SOM412-X23-Y31-Y41` | 主机和扩展板组合来自厂家选型 | 换机器或换扩展板后端子数量、顺序、能力可能变化 |
| X/Y 扩展板命名 | `X23`、`Y31`、`Y41` | 厂家的 I/O 模块型号 | 其他厂家通常不会使用这套命名 |
| X23 端子映射 | `DI1` 在端子 7，`DO4` 在端子 2 | 端子号和功能由厂家硬件定义 | 换模块后必须重新查手册或实测 |
| Y31 通道映射 | `slot 1 channel 1` = `Y31 AI1` | `slot.channel` 是厂家工具的寻址方式 | 不能假设其他平台也用 `1.1`、`1.2` |
| Y41 通道映射 | `slot 2 channel 1` = `Y41 AO1` | `slot 2` 对应当前这台机器上的 Y41 | 板卡顺序变化时 `2.1` 可能不再是 AO1 |
| Y 系列工具 | `/usr/sbin/ioy show`、`/usr/sbin/ioy set 2.1 12` | 厂家提供的 Y 系列 AI/AO 命令行工具 | 其他 Linux 设备通常没有 `ioy` |
| DI/DO sysfs | `/sys/class/beilai/DI1/data`、`/sys/class/beilai/DO4/data` | 厂家驱动暴露的 sysfs 节点，`beilai` 是厂商相关命名 | 换平台后路径和读写方式可能完全不同 |
| DO 控制方式 | `echo 1 > /sys/class/beilai/DO4/data` | 当前驱动用 `data` 文件控制开关量输出 | 其他驱动可能使用 GPIO、Modbus、PLC API 或专用 SDK |
| 串口映射 | X23 `ttyS7-A/B` -> `/dev/ttyS7` | 当前系统镜像和硬件连线给出的设备名 | 不同内核、设备树或板卡上 `/dev/ttyS*` 可能变化 |
| 默认网络地址 | ETH1 `192.168.1.110` | 当前设备调试配置 | 现场网络或恢复出厂后可能不同 |

相对通用的部分：

```text
RS485 A/B、DI/DO、4~20mA、0~20mA、0~10V、Modbus RTU、stty 这些概念是工业控制通用概念。
但具体端子号、Linux 设备文件、sysfs 路径、ioy 命令参数，都是当前厂家平台和当前配置绑定的。
```

当前常用厂家命令：

```bash
# 查看 Y31/Y41 当前 AI/AO 配置和值
/usr/sbin/ioy show

# 读 Y31 第 1 路 AI，当前设备上是 slot 1 channel 1
/usr/sbin/ioy get 1.1

# 设置 Y41 第 1 路 AO，当前 4t20 模式下 12 表示 12mA，不是 12V
/usr/sbin/ioy set 2.1 12

# 读 X23 DI1
cat /sys/class/beilai/DI1/data

# 控制 X23 DO4，也就是 X23 端子 2
echo 1 > /sys/class/beilai/DO4/data
echo 0 > /sys/class/beilai/DO4/data
```

## 3. X23 端子

X23 是 20PIN 模块，包含：

```text
4 路 DI
4 路 DO
4 路 RS485/RS232
```

端子定义：

| 端子号 | 名称 | 类型 | 功能 | 电压/信号说明 |
|---:|---|---|---|---|
| 1 | `DI4` | 数字量输入 | 开关量输入 4 | 对 `COM` 做干接点检测，类似 DI1 |
| 2 | `DO4` | 数字量输出 | 开关量输出 4 | 输出点，不是输入；不要接门磁 |
| 3 | `DI3` | 数字量输入 | 开关量输入 3 | 对 `COM` 做干接点检测，类似 DI1 |
| 4 | `DO3` | 数字量输出 | 开关量输出 3 | 输出点，不是输入；不要接门磁 |
| 5 | `DI2` | 数字量输入 | 开关量输入 2 | 对 `COM` 做干接点检测，类似 DI1 |
| 6 | `DO2` | 数字量输出 | 开关量输出 2 | 输出点，不是输入；不要接门磁 |
| 7 | `DI1` | 数字量输入 | 开关量输入 1 | 实测 `DI1-COM` 约 `5V`；短接到 COM 后状态变化 |
| 8 | `DO1` | 数字量输出 | 开关量输出 1 | 输出点，可控制外部继电器/负载，需按 DO 规格接线 |
| 9 | `GND` | 地 | 湿接点/电源参考地 | 0V 参考地 |
| 10 | `POWER` | 电源相关 | X23 电源相关端 | 实测 `POWER-GND` 约 `1V`，当前不能给 KHKJ 供电 |
| 11 | `COM` | DI 公共端 | DI 干接点公共端 | 门磁直连时接这里 |
| 12 | `GND` | 地 | 信号地/485 参考地 | 0V 参考地，RS485 设备建议共地 |
| 13 | `ttyS9-A` | RS485/RS232 | `/dev/ttyS9` A 线 | RS485 差分信号，不是电源 |
| 14 | `ttyS9-B` | RS485/RS232 | `/dev/ttyS9` B 线 | RS485 差分信号，不是电源 |
| 15 | `ttyS8-A` | RS485/RS232 | `/dev/ttyS8` A 线 | RS485 差分信号，不是电源 |
| 16 | `ttyS8-B` | RS485/RS232 | `/dev/ttyS8` B 线 | RS485 差分信号，不是电源 |
| 17 | `ttyS7-A` | RS485/RS232 | `/dev/ttyS7` A 线 | 实测 `A-B` 约 `0.6V`，正常；不能供电 |
| 18 | `ttyS7-B` | RS485/RS232 | `/dev/ttyS7` B 线 | 实测 `A-B` 约 `0.6V`，正常；不能供电 |
| 19 | `ttyS0-A` | RS485/RS232 | `/dev/ttyS0` A 线 | RS485 差分信号，不是电源 |
| 20 | `ttyS0-B` | RS485/RS232 | `/dev/ttyS0` B 线 | RS485 差分信号，不是电源 |

注意：

```text
ttySX-A / ttySX-B 表示一对 RS485 线。
如果配置成 RS232，则按手册中 RX/TX 的对应说明使用。
COM 是 DI 干接点公共端。
GND 用于 DI 湿接点或信号地。
```

## 4. 门磁接入

普通电控门磁通常是干接点开关，不输出电压。可以直接接 X23 的 DI。

推荐先接 DI1：

```text
门磁一根线 -> X23 端子 7：DI1
门磁另一根线 -> X23 端子 11：COM
```

然后在系统里读：

```bash
cat /sys/class/beilai/DI1/data
```

如果门磁靠近/远离时 `data` 在 `0/1` 之间变化，说明接入成功。

不要把门磁接到：

```text
Y31 AI
Y41 AO
DO1~DO4
POWER
```

## 5. KBDD-0400 模块接入

如果使用 KBDD-0400 这类 RS485/Modbus 输入模块，则走 X23 的 RS485 端子。

X23 上的 4 组 RS485/RS232 端子和 Linux 设备文件对应关系：

| X23 端子 | 丝印/名称 | Linux 设备 |
|---:|---|---|
| 13 / 14 | `ttyS9-A` / `ttyS9-B` | `/dev/ttyS9` |
| 15 / 16 | `ttyS8-A` / `ttyS8-B` | `/dev/ttyS8` |
| 17 / 18 | `ttyS7-A` / `ttyS7-B` | `/dev/ttyS7` |
| 19 / 20 | `ttyS0-A` / `ttyS0-B` | `/dev/ttyS0` |

手册说明：

```text
ttySX-A 和 ttySX-B 表示一对 RS485 线。
例如 ttyS0-A / ttyS0-B 对应 Linux 设备 /dev/ttyS0。
```

任选一组，例如 `ttyS7`：

```text
KBDD-0400 485A -> X23 端子 17：ttyS7-A
KBDD-0400 485B -> X23 端子 18：ttyS7-B
KBDD-0400 GND  -> X23 端子 12：GND，建议连接
```

KBDD-0400 还需要单独供电：

```text
KBDD-0400 VIN+ -> 外部 12/24V +
KBDD-0400 GND  -> 外部 12/24V -
```

系统里确认串口存在：

```bash
ls -l /dev/ttyS0 /dev/ttyS7 /dev/ttyS8 /dev/ttyS9
```

当前设备已确认存在：

```text
/dev/ttyS0
/dev/ttyS7
/dev/ttyS8
/dev/ttyS9
```

设置串口参数，示例按 `9600 8N1`：

```bash
stty -F /dev/ttyS7 9600 cs8 -cstopb -parenb -ixon -ixoff -crtscts
```

如果模块说明书写的是 `115200 8N1`，则改成：

```bash
stty -F /dev/ttyS7 115200 cs8 -cstopb -parenb -ixon -ixoff -crtscts
```

485 的 A/B 如果接反，通常不会烧设备，但会通信失败。可以交换 A/B 再试。

KBDD-0400 如果是 Modbus RTU 输入模块，后续需要确认：

```text
设备地址
波特率
校验位
功能码
DI 状态寄存器地址
```

## 6. Y31 端子

Y31 是 10PIN 模块，4 路单端模拟量输入：

```text
4xAI, single-ended, 0~20mA / 4~20mA
```

端子定义：

| 端子号 | 名称 | 类型 | 功能 | 电压/信号说明 |
|---:|---|---|---|---|
| 1 | `AI1+` | 模拟量输入 | 电流输入 1 正 | `0~20mA` 或 `4~20mA` 输入，不是电压输入 |
| 2 | `AI1-` | 模拟量输入 | 电流输入 1 负 | 与 `AI1+` 组成第 1 路电流采集 |
| 3 | `AI2+` | 模拟量输入 | 电流输入 2 正 | `0~20mA` 或 `4~20mA` 输入 |
| 4 | `AI2-` | 模拟量输入 | 电流输入 2 负 | 与 `AI2+` 组成第 2 路电流采集 |
| 5 | `GND` | 地 | 模拟地 | 0V 参考地 |
| 6 | `GND` | 地 | 模拟地 | 0V 参考地 |
| 7 | `AI3+` | 模拟量输入 | 电流输入 3 正 | `0~20mA` 或 `4~20mA` 输入 |
| 8 | `AI3-` | 模拟量输入 | 电流输入 3 负 | 与 `AI3+` 组成第 3 路电流采集 |
| 9 | `AI4+` | 模拟量输入 | 电流输入 4 正 | `0~20mA` 或 `4~20mA` 输入 |
| 10 | `AI4-` | 模拟量输入 | 电流输入 4 负 | 与 `AI4+` 组成第 4 路电流采集 |

适合接：

```text
4~20mA 压力传感器
4~20mA 温度变送器
0~20mA 工业模拟量信号
```

不适合直接接：

```text
门磁干接点
普通开关
RS485 设备
0~10V 电压型传感器
```

## 7. Y41 端子

Y41 是 10PIN 模块，4 路模拟量输出：

```text
4xAO, 0~20mA / 4~20mA
```

端子定义：

| 端子号 | 名称 | 类型 | 功能 | 电压/信号说明 |
|---:|---|---|---|---|
| 1 | `AO1+` | 模拟量输出 | 电流输出 1 正 | `0~20mA` 或 `4~20mA` 输出 |
| 2 | `AO1-` | 模拟量输出 | 电流输出 1 负 | 与 `AO1+` 组成第 1 路电流输出 |
| 3 | `AO2+` | 模拟量输出 | 电流输出 2 正 | `0~20mA` 或 `4~20mA` 输出 |
| 4 | `AO2-` | 模拟量输出 | 电流输出 2 负 | 与 `AO2+` 组成第 2 路电流输出 |
| 5 | `/` | 未用 | 不接 | 无功能 |
| 6 | `/` | 未用 | 不接 | 无功能 |
| 7 | `AO3+` | 模拟量输出 | 电流输出 3 正 | `0~20mA` 或 `4~20mA` 输出 |
| 8 | `AO3-` | 模拟量输出 | 电流输出 3 负 | 与 `AO3+` 组成第 3 路电流输出 |
| 9 | `AO4+` | 模拟量输出 | 电流输出 4 正 | `0~20mA` 或 `4~20mA` 输出 |
| 10 | `AO4-` | 模拟量输出 | 电流输出 4 负 | 与 `AO4+` 组成第 4 路电流输出 |

适合接：

```text
4~20mA 阀门控制
4~20mA 变频器给定
0~20mA 模拟控制输入
```

不适合接：

```text
门磁
压力传感器输出
RS485
普通 DI 输入
```

## 8. 当前建议

门磁优先直接接 X23：

```text
DI1：X23 端子 7
COM：X23 端子 11
```

压力传感器如果是 `4~20mA` 型，可以不用 DAQ4212，直接接 Y31：

```text
压力传感器信号 + -> Y31 AI1+
压力传感器信号 - -> Y31 AI1-
```

如果压力传感器是 `0~10V` 或 `0.5~4.5V` 电压型，则不能直接接 Y31，需要继续用 DAQ4212，或更换成电压输入型 Y33/Y34 板卡。

## 9. 2026-05-22 实测记录

### 9.1 KHDQ-0400 门磁输入

KHDQ-0400 是 RS485 / Modbus 数字量输入模块，不是模拟量模块。它的 RS485 接到 X23 后，工业机通过串口读模块内部寄存器；门磁实际接在 KHDQ-0400 的输入端。

```text
X23 17 ttyS7-A -> KHDQ-0400 485A
X23 18 ttyS7-B -> KHDQ-0400 485B
X23 12 GND     -> KHDQ-0400 GND，建议连接

KHDQ-0400 VIN+ -> 外部 12/24V +
KHDQ-0400 GND  -> 外部 12/24V -

门磁一端 -> KHDQ-0400 IN1
门磁一端 -> KHDQ-0400 COM
```

术语：

```text
IN1 = Input 1，第 1 路输入端。
COM = Common，输入公共端。
```

`X23 17/18` 只负责 RS485 通信，不表示门磁接在工业机第 17/18 路输入。实测 KHDQ-0400 的 485A/485B 间约 `0.5~0.6V`，这是正常 RS485 空闲差分电压，不能作为供电使用。

当前已验证读法：

```bash
python3 /root/modbus_rtu_probe.py \
  --port /dev/ttyS7 \
  --baud 9600 \
  --slave 1 \
  --function 3 \
  --address 0x22 \
  --quantity 1 \
  --timeout 0.5
```

持续观察并拆出 4 路 DI：

```bash
while true; do
  v=$(python3 /root/modbus_rtu_probe.py --port /dev/ttyS7 --baud 9600 --slave 1 --function 3 --address 0x22 --quantity 1 --timeout 0.5 | sed -n 's/.*registers=\[\([0-9]*\)\].*/\1/p')
  python3 -c "v=int('$v'); print(f'raw={v} hex=0x{v:04X} DI1={v&1} DI2={(v>>1)&1} DI3={(v>>2)&1} DI4={(v>>3)&1}')"
  sleep 0.5
done
```

实测门磁靠近/远离时 `DI1` 在 `0/1` 变化，说明门磁接在 KHDQ-0400 第 1 路输入：

```text
raw=61472 hex=0xF020 DI1=0 DI2=0 DI3=0 DI4=0
raw=61473 hex=0xF021 DI1=1 DI2=0 DI3=0 DI4=0
```

### 9.2 SBWZ-2280 温度变送器接 Y31

照片中的 SBWZ-2280 端子定义按面板丝印理解为：

```text
左上 = 1 = 4-20mA+
右上 = 2 = 4-20mA-
左下 = 3 = 24VDC+
右下 = 4 = 24VDC-

5 / 6 / 7 / 8 = RTD/TC 温度探头输入端
```

不能把 24V 电源接到 `1/2`。`1/2` 是 4-20mA 输出端，`3/4` 是变送器供电端。

本次实测跑通的回路接法：

```text
DR-45-24 +V       -> SBWZ-2280 端子 3：24VDC+
SBWZ-2280 端子 4：24VDC- -> Y31 端子 1：AI1+
Y31 端子 2：AI1- -> DR-45-24 -V
```

这个接法让 `DR-45-24 +V -> SBWZ -> Y31 AI1 -> DR-45-24 -V` 形成 4-20mA 电流回路。Y31 是电流输入，所以不需要 250Ω 电阻。

如果用 DAQ4212 读这个变送器，则必须在 4-20mA 回路中增加采样电阻，例如：

```text
4mA  x 250Ω = 1V
20mA x 250Ω = 5V
```

因为 DAQ4212 的 AI 读的是电压，不是电流。没有采样电阻时，DAQ4212 AI0 读到接近 `0V` 是正常现象，不能代表温度。

Y31 读取命令：

```bash
/usr/sbin/ioy get 1.1
```

按 `4-20mA -> 0-100degC` 换算：

```bash
while true; do
  ma=$(/usr/sbin/ioy get 1.1)
  awk -v ma="$ma" 'BEGIN {
    temp=(ma-4)/(20-4)*100;
    printf "Y31 AI1=%.6f mA, temp=%.2f degC\n", ma, temp;
  }'
  sleep 0.5
done
```

实测输出：

```text
Y31 AI1=8.182507 mA, temp=26.14 degC
Y31 AI1=9.485810 mA, temp=34.29 degC
```

常温约 `26degC`，用手捂探头后升至约 `34degC`，说明变送器、Y31 输入和换算链路已跑通。

## 10. 网络摄像机与本地视觉 AI

当前 `BL412B-SOM412` 可以作为单路网络摄像机视觉分析主机。摄像机应通过
Ethernet/RTSP 接入，不接 X23/Y31/Y41，也不需要额外增加一块 RK3568 开发板。

推荐物理连接：

```text
12/24VDC power supply
  |
  +-- BL412B power input
  |
  +-- camera 12V input (按摄像机规格独立稳压/保护)

camera RJ45/adapter
  |
  +-- BL412B Ethernet port 1: camera subnet

BL412B Ethernet port 2: control/device subnet
BL412B Ethernet port 3: uplink/MQTT/maintenance subnet
```

推荐软件数据链：

```text
RTSP H.264/H.265
  -> Rockchip MPP hardware decode
  -> RGA resize/crop
  -> RKNN face detection / facial landmark model on NPU
  -> CPU computes EAR / MAR / PERCLOS / head pose / alert state
  -> local alarm, HMI, event log and MQTT
```

能力判断：

- 单路 `1920x1080@25fps` H.264/H.265 输入低于平台标称解码上限。
- 1 TOPS NPU 可以作为轻量人脸检测和关键点模型的验证目标，但资料不足以证明目标帧率，最终帧率、精度和温升必须实测。
- 原始 Python + MediaPipe CPU 路线不会自动使用 RK3568 NPU，不能因为设备含 NPU 就假设性能达标。
- 面向量产应使用 MPP/RGA/RKNN 数据链，避免 CPU 软解码和整帧图像的多次内存复制。
- 100M Ethernet 对单路摄像机码流足够，但摄像机网、控制网和上联网应尽量分口，避免广播和视频突发流量干扰控制通信。
- 疲劳检测属于辅助告警，不能替代车辆安全控制；夜间红外、眼镜、遮挡、逆光、网络断开和模型失效必须进入验收用例。

当前还需要在实机确认的软件条件：

```bash
cat /proc/device-tree/compatible | tr '\0' '\n'
ls -l /dev/rknpu /dev/mpp_service /dev/dri 2>/dev/null
ldconfig -p | grep -Ei 'rknn|rockchip_mpp|rga'
dmesg | grep -Ei 'rknpu|rga|mpp'
```

判定标准：

| 检查项 | 通过条件 | 不通过时的影响 |
|---|---|---|
| SoC 设备树 | 出现 `rockchip,rk3568` | 镜像或设备树身份异常，需要厂家确认 |
| NPU 驱动 | `/dev/rknpu` 存在且无驱动错误 | 无法使用 RKNN NPU，只能退回 CPU |
| MPP | 设备节点和运行库可用 | RTSP 只能软解码，CPU 压力明显增加 |
| RGA | 驱动和运行库可用 | 缩放/色彩转换落到 CPU，增加复制和延迟 |
| RKNN runtime | 能加载目标 `.rknn` 并完成推理 | 模型转换完成也无法在设备执行 |

## 11. 原厂资料

本文件的主机、SOM、接口和平台能力基线来自：

1. `ARMxyBL410DatasheetV10.pdf`
   - 标题：`ARMxy Embedded Computer Datasheet - ARMxy BL410 Series`
   - 版本：V1.0
   - 重点页：PDF 第 3 页产品概述、第 5~6 页软硬件规格、第 9~10 页主机和 SOM 型号表
2. `BLIIOTARMxySeriesBL410UserManualV11.pdf`
   - 标题：`ARMxy Series Embedded Computers - BL410 User Manual`
   - 版本：V1.1
   - 日期：2026-03-19
   - 重点页：PDF 第 6~8 页技术规格、第 9~11 页主机/SOM/X/Y 选型、第 26~33 页网络、HDMI、看门狗和 RTC

原始文件当前保存在开发机：

```text
/Users/songzijian/Downloads/Books and PDFs/ARMxyBL410DatasheetV10.pdf
/Users/songzijian/Downloads/Books and PDFs/BLIIOTARMxySeriesBL410UserManualV11.pdf
```

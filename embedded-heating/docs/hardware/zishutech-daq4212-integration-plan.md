# ZishuTech DAQ4212 Integration Plan

> 状态：接入计划  
> 设备：紫鼠科技 DAQ-4212，属于 DAQ-4210/4211/4212 系列  
> BL410 USB 路径：`2-1.3`  
> 用途：把 USB 数据采集器接入热能控制系统，读取 AI/DI，并在 HMI 展示和提示。
> 当前资料包：`daq4211_python.rar`、`ug0015-daq-4211-user-guide_ver-a.pdf`、`daq4210_step.rar`

## 1. 当前识别结果

BL410 已经能识别 USB 设备：

```text
USB path: 2-1.3
Bus/Device: Bus 002 Device 006
Vendor ID: a614
Product ID: 0004
Manufacturer: ZishuTech
Product: ZishuTech USB2.0 DAQ Device
Serial: 0372508001
Speed: 12 Mbps
USB class: ff / vendor specific
```

确认命令：

```bash
lsusb
cat /sys/bus/usb/devices/2-1.3/manufacturer
cat /sys/bus/usb/devices/2-1.3/product
cat /sys/bus/usb/devices/2-1.3/serial
cat /sys/bus/usb/devices/2-1.3/idVendor
cat /sys/bus/usb/devices/2-1.3/idProduct
cat /sys/bus/usb/devices/2-1.3:1.0/uevent
```

注意：当前没有生成这些通用设备节点：

```text
/dev/ttyUSB0
/dev/ttyACM0
/dev/hidraw0
```

所以它不是普通串口设备，也不是标准 HID 设备。要采集 AI/DI/AO，必须使用厂家 SDK 或 USB 协议。

## 2. 官网公开资料

官网产品页：

```text
https://www.zishutech.com/?products=daq-4210-8%E9%80%9A%E9%81%9316%E4%BD%8D%E6%AD%A3%E4%BA%A4%E7%BC%96%E7%A0%81%E5%90%8C%E6%AD%A5%E9%87%87%E9%9B%86%E5%8D%A1
```

注意：你现场看到的型号是 `DAQ-4212`。厂家官网公开页面和下载项目前按 `DAQ-4210` 系列归档，后续拿 SDK/手册时需要向厂家确认 `DAQ-4212` 和 `DAQ-4210` 的协议/API/通道能力是否完全兼容。

官网公开描述：

| 项目 | 规格 |
|---|---|
| 产品 | DAQ-4210/4211/4212 系列，现场设备按 DAQ-4212 处理 |
| 接口 | USB + 以太网双接口 |
| 供电 | USB 总线供电或外部 DC 12V/24V |
| AI | 8 路模拟量输入，16 bit，单端输入 |
| AI 量程 | `±5V` / `±10V` |
| AI 采样 | 最高 200 KSa/s，所有通道同步采样 |
| AO | 1 路模拟量输出，12 bit，`±10V` |
| DIO | 4 路可配置输入输出 |
| 其他 | 1 路正交编码计数器，1 路 PWM，和 DIO 共用引脚 |

官网可下载项：

```text
DAQ-4210采集卡用户手册
DAQ-4210采集卡编程范例 Python
DAQ-4210采集卡编程范例 Qt C
DAQ-4210采集卡编程范例 Qt C++
DAQ-4210采集卡编程范例 Labview
DAQ-4210采集卡编程范例 Matlab
DAQ-4210采集卡编程范例 VS2015 C#
DAQ-4210采集卡编程范例 VS2015 C++
DAQ-4210固件 V1.11.1.4
DAQ-4210结构 step 模型
```

优先下载：

```text
1. DAQ-4210采集卡用户手册
2. DAQ-4210采集卡编程范例 Python
3. DAQ-4210采集卡编程范例 Qt C
4. DAQ-4210采集卡编程范例 Qt C++
```

## 3. 当前资料包结论

已经拿到的压缩包可以直接作为 BL410 接入的起点。

### 3.1 `daq4211_python.rar`

解压后关键内容：

```text
python/example_daq4211.py
python/libdaq2/libdaq2.py
python/libdaq2/linux-arm64.tar.gz
python/libdaq2/linux-arm32.tar.gz
python/libdaq2/linux-x86_64.tar.gz
python/libdaq2/MS32/daqlib2.dll
python/libdaq2/MS64/daqlib2.dll
```

其中 `linux-arm64.tar.gz` 是关键，里面有 BL410 可用的 ARM64 动态库：

```text
linux-arm64/libdaqlib.so.2.10.1
linux-arm64/libdaqlib.so.2.10
linux-arm64/libdaqlib.so.2
linux-arm64/libdaqlib.so
linux-arm64/ZishuTech_daq.rules
linux-arm64/install.sh
linux-arm64/uninstall.sh
linux-arm64/readme
```

`libdaqlib.so.2.10.1` 文件类型：

```text
ELF 64-bit LSB shared object, ARM aarch64
```

结论：

```text
厂家已经提供 Linux ARM64 SDK。
BL410 不需要先逆向 USB 协议。
下一步可以直接把 Python 示例和 linux-arm64 动态库拷到 BL410 跑。
```

### 3.2 `ug0015-daq-4211-user-guide_ver-a.pdf`

手册是 DAQ-4211 硬件手册，但对 DAQ-4212 接入仍有参考价值。关键参数：

| 模块 | 信息 |
|---|---|
| 总线 | USB2.0 12 Mbps + 100M 以太网 |
| 供电 | USB 供电，或外部 12V/24V |
| AI | 8 路单端模拟量输入 |
| AI 分辨率 | 16 bit |
| AI 量程 | `±5V` / `±10V` |
| AI 输入阻抗 | `1 MΩ` |
| AI 保护 | `±15V` |
| AO | 1 路模拟量输出，`±10V` |
| AO 分辨率 | 12 bit |
| DIO | 4 路可配置输入/输出 |
| DIO 电平 | 3.3V CMOS，兼容 TTL 输入 |
| DIO 输入范围 | `0-3.3V` |
| DIO 输出电流 | 每路最大 `10mA` |

重要接线规则：

```text
AI0~AI7 是单端模拟量输入。
所有被测信号的 GND 必须接到采集卡 GND。
DIO 是 3.3V 逻辑，不要直接接 12V/24V 工业信号。
烟感、开关量、继电器反馈如果是干接点/24V 信号，需要先做隔离或电平转换。
```

### 3.3 `daq4210_step.rar`

这个包里是结构模型：

```text
DAQ4210.STEP
```

用途：

```text
给机械结构、安装孔位、外壳布局、底板/机箱设计使用。
不参与软件采集。
```

## 4. 需要向厂家确认的问题

BL410 是 ARM64 / AArch64 Linux，不能直接使用 Windows SDK 或 x86 Linux 动态库。

向厂家确认：

```text
是否支持 Linux ARM64 / AArch64？
是否提供 libusb 版本 SDK？
是否提供 .so 动态库？
动态库是否有 aarch64 版本？
是否提供 .h 头文件？
是否提供 Python 示例？
Python 示例是否依赖 pyusb / ctypes / 厂商 .so？
是否提供纯 USB 协议文档？
是否需要 udev 规则？
是否支持 Ubuntu 20.04 / Linux 5.10？
AI/DI/AO API 分别是什么？
量程、采样率、通道使能如何配置？
采集数据的单位换算公式是什么？
DAQ-4212 是否直接使用 DAQ-4211 Python SDK？
DAQ-4212 在 libdaq2.py 里应该用 DAQ4211 类还是 DAQ4210 类？
DAQ-4212 的 AI 最高采样率到底是 50KSa/s 还是 200KSa/s？
```

必须拿到的最小资料：

```text
用户手册
C/C++ 示例
Linux ARM64 SDK 或 USB 协议
AI 读取接口说明
DI 读取接口说明
AO 输出接口说明
错误码说明
```

## 5. 接入路线选择

### 5.1 优先路线：厂家 Linux ARM64 SDK

适合情况：

```text
厂家提供 aarch64 libzishudaq.so
厂家提供 .h 头文件
厂家提供 Linux 示例
```

集成方式：

```text
vendor/zishutech/
  include/
  lib/aarch64/
  examples/

backend/app/services/zishutech_daq.py
backend/app/core/point_mapper.py
```

优点：最快、风险最低。

当前资料包已经满足这条路线。

### 5.2 次选路线：厂家提供 USB 协议，自己用 libusb

适合情况：

```text
厂家没有 ARM64 SDK
但提供 USB 控制命令、端点、数据格式、校验方式
```

BL410 已有：

```text
/lib/aarch64-linux-gnu/libusb-1.0.so.0
```

但如果要编译 C 程序，还需要头文件：

```text
libusb-1.0/libusb.h
```

设备离线时需要提前准备离线包，或在开发机交叉编译后把可执行文件拷过去。

### 5.3 不推荐路线：Windows SDK

如果厂家只给 Windows DLL / VS 示例：

```text
不能直接跑在 BL410 上
```

此时需要继续向厂家要 Linux ARM64 SDK 或协议文档。

## 6. BL410 上的验证流程

### 6.0 本次实际处理结果

已经在 BL410 上完成 SDK 部署和只读验证。

实际设备环境：

```text
CPU 架构：aarch64
Python：3.8.10
USB 设备：a614:0004
设备名称：DAQ-4212
序列号：0372508001
固件版本：1.13.1.1
```

已安装内容：

```text
/opt/energy-control/vendor/zishutech/python
/usr/local/lib/daqlib2/libdaqlib.so
/usr/local/lib/daqlib2/libdaqlib.so.2
/usr/local/lib/daqlib2/libdaqlib.so.2.10
/usr/local/lib/daqlib2/libdaqlib.so.2.10.1
/etc/udev/rules.d/ZishuTech_daq.rules
```

厂家 `libdaq2.py` 默认用了 Python 3.10 的类型标注写法，例如 `bytes|str`。BL410 当前是 Python 3.8，所以已在设备上的文件中增加：

```python
from __future__ import annotations
```

位置：

```text
/opt/energy-control/vendor/zishutech/python/libdaq2/libdaq2.py
```

本次只读测试脚本：

```text
/opt/energy-control/vendor/zishutech/python/daq4212_read_once.py
```

仓库内也保留了一份：

```text
embedded-heating/tools/zishutech/daq4212_read_once.py
```

压力读取/换算脚本：

```text
/opt/energy-control/vendor/zishutech/python/daq4212_pressure_read.py
```

仓库内也保留了一份：

```text
embedded-heating/tools/zishutech/daq4212_pressure_read.py
```

运行命令：

```bash
cd /opt/energy-control/vendor/zishutech/python
LD_LIBRARY_PATH=/usr/local/lib/daqlib2:$LD_LIBRARY_PATH python3 daq4212_read_once.py
```

实际输出：

```text
device_count=1
sn=0372508001
name=DAQ-4212
model=DAQ-4212
AI0=0.000458V
AI1=0.000763V
AI2=0.000763V
AI3=0.000458V
AI4=0.000458V
AI5=0.000458V
AI6=0.000458V
AI7=0.000458V
DI=[0, 0, 0, 0]
```

压力传感器测试命令，按 `AI0`、`0-10V -> 0-1.6MPa` 示例换算：

```bash
cd /opt/energy-control/vendor/zishutech/python
LD_LIBRARY_PATH=/usr/local/lib/daqlib2:$LD_LIBRARY_PATH python3 daq4212_pressure_read.py \
  --channel 0 \
  --v-min 0 \
  --v-max 10 \
  --p-min 0 \
  --p-max 1.6 \
  --unit MPa \
  --count 5 \
  --interval 0.5
```

当前实际输出显示 `AI0` 约 `0.0005V`，换算后约等于 `0MPa`：

```text
AI0=0.000458V pressure=0.000073MPa
AI0=0.000763V pressure=0.000122MPa
```

同时 `AI0~AI7` 都接近 `0V`，说明 DAQ SDK 可以读取，但 DAQ 输入端目前没有收到压力传感器的有效电压信号。

结论：

```text
DAQ-4212 已能被 SDK 正常识别。
DAQ4211 Python 类可以打开 DAQ-4212。
AI0~AI7 单次读取可用。
DIO0~DIO3 输入读取可用。
还没有测试 AO 输出和 DIO 输出，因为它们会主动输出电压/电平，需要接线确认后再做。
```

压力传感器排查顺序：

```text
1. 确认压力传感器输出类型：0-10V、0.5-4.5V、1-5V，还是 4-20mA。
2. 如果是电压型，信号线接 AIx，传感器 GND/电源负极必须和 DAQ 的 GND 相连。
3. 如果是 4-20mA 电流型，DAQ 不能直接读电流，需要加采样电阻转换成电压。
4. 常用 250Ω 电阻：4-20mA -> 1-5V，再按 1-5V 换算压力。
5. 用万用表直接量 AIx 对 DAQ GND 的电压；如果万用表也是 0V，优先查供电/接线/传感器输出。
6. 如果万用表有电压但 DAQ 读 0V，优先查 AI 通道号、GND、量程配置和端子接触。
```

### 6.1 确认设备在线

```bash
lsusb
cat /sys/bus/usb/devices/2-1.3/product
cat /sys/bus/usb/devices/2-1.3/serial
```

预期：

```text
ZishuTech USB2.0 DAQ Device
0372508001
```

### 6.2 拷贝 SDK 到 BL410

在 Mac 上：

```bash
cd /Users/songzijian/Downloads
scp daq4211_python.rar root@192.168.1.110:/tmp/
```

在 BL410 上：

```bash
cd /tmp
mkdir -p /opt/energy-control/vendor/zishutech
cd /opt/energy-control/vendor/zishutech
bsdtar -xf /tmp/daq4211_python.rar
cd python/libdaq2
tar -xzf linux-arm64.tar.gz
```

如果 BL410 没有 `bsdtar/unrar`，就在 Mac 上先解压，再拷贝目录：

```bash
scp -r /private/tmp/zishu_daq_extract/python root@192.168.1.110:/opt/energy-control/vendor/zishutech/
```

最终目录应类似：

```text
/opt/energy-control/vendor/zishutech/python/example_daq4211.py
/opt/energy-control/vendor/zishutech/python/libdaq2/libdaq2.py
/opt/energy-control/vendor/zishutech/python/libdaq2/linux-arm64/libdaqlib.so.2
```

### 6.3 安装动态库和 udev 规则

在 BL410 上：

```bash
cd /opt/energy-control/vendor/zishutech/python/libdaq2/linux-arm64
chmod +x install.sh uninstall.sh
./install.sh
echo 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/daqlib2' >> /root/.bashrc
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/daqlib2
ldconfig
```

`ZishuTech_daq.rules` 内容：

```text
ACTION=="add",SUBSYSTEM=="usb", ATTR{idVendor}=="a614", ATTR{idProduct}=="0004", SYMLINK+="ZISHU-DAQ",GROUP="users", MODE="0666"
```

它的作用是给 `a614:0004` 设备加权限，并创建 `/dev/ZISHU-DAQ` 软链接。

### 6.4 先跑枚举测试

先不要接真实传感器，只测试能否打开设备：

```bash
cd /opt/energy-control/vendor/zishutech/python
python3 -m libdaq2.libdaq2
```

预期能看到：

```text
detect 1 device attached to PC
device index 0 sn:0372508001,name:...,model:...
```

### 6.5 跑厂家示例

厂家示例入口：

```bash
cd /opt/energy-control/vendor/zishutech/python
python3 example_daq4211.py
```

注意：

```text
libdaq2.py 当前只有 DAQ4210 和 DAQ4211 类，没有 DAQ4212 类。
DAQ4211 类包含 ADC、DIO、DAC，和 DAQ-4212 的基础采集需求匹配。
如果厂家确认 DAQ-4212 与 DAQ-4211 SDK 兼容，就先用 DAQ4211 类。
如果运行时报型号不匹配，再换 DAQ4210 类或向厂家要 DAQ-4212 的新版 libdaq2.py。
```

### 6.6 跑最小采集

先只做三件事：

```text
1. 枚举设备
2. 读取一次 AI0~AI7
3. 读取一次 DI0~DI3
```

示例输出期望：

```text
device: DAQ4212 serial=0372508001
AI0=0.012 V
AI1=0.008 V
...
DI0=0
DI1=1
```

### 6.7 验证接线

AI 输入：

```text
先用安全低压信号源测试，例如 0V / 1V / 2V。
不要直接接高压或不确定信号。
```

DI 输入：

```text
先用干接点短接测试。
确认 DI0 状态从 0 -> 1 或 1 -> 0。
```

AO 输出：

```text
先不接负载。
用万用表测 AO 对 GND。
从 0V 小步变化到 1V / 2V。
确认输出正常后再接真实设备。
```

## 7. 热能控制点位映射

先定义点位，不要把 SDK API 直接散落到业务逻辑里。

建议初始映射：

| DAQ 通道 | 热能点位 | 类型 | 单位 |
|---|---|---|---|
| `AI0` | 一次侧供水温度 | AI | `degC` |
| `AI1` | 一次侧回水温度 | AI | `degC` |
| `AI2` | 二次侧供水温度 | AI | `degC` |
| `AI3` | 二次侧回水温度 | AI | `degC` |
| `AI4` | 二次侧供水压力 | AI | `MPa` |
| `AI5` | 二次侧回水压力 | AI | `MPa` |
| `DI0` | 烟感报警 | DI | `0/1` |
| `DI1` | 水流开关 | DI | `0/1` |
| `DI2` | 循环泵运行反馈 | DI | `0/1` |
| `DI3` | 故障输入 | DI | `0/1` |
| `AO0` | 阀门开度输出 | AO | `V` 或 `%` |

传感器换算单独配置：

```json
{
  "AI4": {
    "name": "secondary_supply_pressure",
    "inputRange": "0-10V",
    "engineeringRange": "0-1.6MPa",
    "scale": 0.16,
    "offset": 0
  }
}
```

## 8. 软件结构建议

```text
backend/
  app/
    services/
      zishutech_daq.py          # SDK 封装，只负责读写 DAQ-4212
    core/
      point_mapper.py           # 通道值 -> 热能点位
      acquisition_loop.py       # 周期采集
      interface_events.py       # 接入/断开提示
    api/
      points.py                 # 查询点位
      daq.py                    # 设备状态/调试 API
```

不要让控制逻辑直接调用厂家 SDK。建议隔一层：

```text
厂家 SDK
  -> zishutech_daq driver
  -> point_mapper
  -> acquisition_loop
  -> control state machine
  -> HMI / alarm / output
```

## 9. HMI 展示

当前 HMI 已有接口事件提示。DAQ 接入成功后可以推送：

```js
window.tecPushInterfaceEvent({
  kind: "usb",
  action: "add",
  name: "DAQ4212",
  detail: "检测到紫鼠科技 DAQ-4212，序列号 0372508001"
});
```

真实后端接入后，建议通过 WebSocket 推：

```json
{
  "type": "interface_event",
  "kind": "usb",
  "action": "add",
  "name": "DAQ4212",
  "detail": "检测到紫鼠科技 DAQ-4212，开始采集 AI/DI"
}
```

点位数据推送：

```json
{
  "type": "point_snapshot",
  "points": {
    "primary_supply_temp": 72.4,
    "secondary_supply_pressure": 0.32,
    "smoke_alarm": 0
  }
}
```

## 10. systemd 集成

后续采集服务可以独立成：

```text
energy-acquisition.service
```

职责：

```text
检测 DAQ 是否在线
周期读取 AI/DI
写入本地缓存/数据库
通过 WebSocket 或本地 API 提供给 HMI
设备断开时推送告警
```

服务文件示例：

```ini
[Unit]
Description=Energy Acquisition Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/energy-control
Environment=LD_LIBRARY_PATH=/opt/energy-control/vendor/zishutech/lib
ExecStart=/opt/energy-control/bin/energy-acquisition
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## 11. 验收标准

第一阶段验收：

```text
BL410 能识别 a614:0004
采集服务能枚举 DAQ-4212
能读取 AI0~AI7 原始电压
能读取 DI0~DI3 状态
拔掉 USB 后 HMI 提示设备断开
重新插入后 HMI 提示设备接入
```

第二阶段验收：

```text
AI 通道能按传感器量程换算成温度/压力
DI 通道能显示烟感/水流/故障状态
数据能进入 HMI 点表
采集异常不会影响安全状态机
```

第三阶段验收：

```text
采集服务开机自启
长期运行 24 小时无异常
USB 插拔 20 次能自动恢复
断电重启后自动恢复采集
```

## 12. 当前待办

1. 下载官网用户手册和 Python / Qt C / Qt C++ 示例。
2. 判断示例是否能在 Linux ARM64 上运行。
3. 如果不能，向厂家索要 Linux ARM64 SDK 或 USB 协议。
4. 在 BL410 上跑最小示例：枚举设备、读 AI、读 DI。
5. 把 SDK 封装成 `zishutech_daq` 驱动层。
6. 建立 DAQ 通道到热能点位的映射。
7. 通过 WebSocket 推送给 HMI。
8. 做 USB 断开/重连恢复逻辑。

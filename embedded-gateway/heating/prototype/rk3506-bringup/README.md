# HD-RK3506-IOT 板级验证（串口 / 蓝牙 / WiFi）

> 对象：**HD-RK3506-IOT V1.2** 工业机（万象，核心板 HD-RK3506J-256）
> 系统：Buildroot，Linux 6.1.118，armv7l，root/root，eth0 默认 `192.168.1.10`
> 本目录脚本：
> - `loopback_test.py` 串口自环 · `wifi.py` WiFi 配置
> - `modbus_demo.py` Modbus 协议演示(虚拟串口) · `modbus_rtu.py` 真串口主/从
> - `modbus_sim.py`+`sim_config.json` 配置驱动模拟器(多从站+故障注入,网关陪练)
> - `gateway.py`+`gateway_config.json` 三层网关骨架(采集→队列→上云)
> 配套：[嵌入式常识清单](../../docs/embedded-common-sense.md) · [成长路径](../../docs/embedded-expert-growth-path.md)
> 协议/架构延伸：[Modbus/RS485 基础](../../docs/protocols/fieldbus-modbus-rs485-basics.md) · [网关可靠性与性能](../../docs/architecture/gateway-reliability-and-performance.md)

## Modbus 采集 → 网关骨架(已在板子实测)
```
配置驱动模拟器(104:USB-TTL)  ──真串口──►  网关骨架(板子:ttyS1)
  modbus_sim.py 多从站+故障注入            gateway.py 轮询→队列→上云
```
- 真串口接线:`ttyS1_TX(pin8)→对端RX`、`对端TX→ttyS1_RX(pin10)`、`GND→pin9`(跨机必接)。
- 验证过:多设备轮询、工程量换算、质量码、故障隔离+退避、离线设备每轮仍上报、`clock_sync` 标记时间可信度。
- 真上线:模拟器换成真表(USB-RS485);`gateway.py` uploader 的 print 换成 [`gateway_mqtt.py`](../cloud-gateway-mqtt/gateway_mqtt.py) 的 publish;配 systemd 掉电自启。
- ⚠️ 板子无 RTC,重启时间乱(常识 §11):需 NTP 或上电向云/上位机校时,否则 `clock_sync=unsynced`。

这份文档的价值不在"结论是通的"，而在**排查路径**——一个放反的短接帽卡了我们半天，
代码/查手册 AI 几秒就给了，真正难的是物理世界里的常识。整个过程没瞎改一行代码。

---

## 一、串口自环测试

### 目标
验证工业机自己的某个 UART（收发驱动 + IO 矩阵 + 物理排针）整条链路通不通。
方法：把这个 UART 的 **TXD↔RXD 物理短接**，自己发的字节应原样回到自己的 RX。

### 板子串口现状
| ttyS | 控制器 | 设备树 | 用途 |
|---|---|---|---|
| ttyFIQ0 | — | console | **调试控制台，别动**（板上 `TXD/RXD/GND` 3针口） |
| ttyS1 | ff0b0000 | okay | 板载 UART1 → 40Pin 排针 **8脚=TX / 10脚=RX** |
| ttyS2 | ff0c0000 | okay | UART2 → 排针 11/12 |
| ttyS3 | ff0d0000 | okay | UART3 → 排针 13/15 |
| ttyS4 | ff0e0000 | okay | UART4（RM_IO30/31） |

> 设备树里 ttyS1–4 全部 `okay`、**都不是 RS485**（无 `rs485-enabled-at-boot-time`、无方向控制 RTS）。

### 怎么测（以 ttyS1 为例）
1. **接线**（👤 物理）：用**母对母杜邦线**把 40Pin 排针的 **8 号孔 ↔ 10 号孔**直接连起来。
2. 跑脚本（🤖）：
   ```bash
   python3 loopback_test.py /dev/ttyS1            # 只测 ttyS1 @115200
   python3 loopback_test.py                       # 不带参数=轮测 ttyS1..S4
   python3 loopback_test.py /dev/ttyUSB0 9600     # 指定口+波特率
   ```
3. 看结果：
   ```
   /dev/ttyS1 @ 115200: ✅自环通过  发=b'LOOPBACK-35428' 收=b'LOOPBACK-35428'
   ```
   - `✅自环通过` = 这个口 TX↔RX 短接着，硬件+驱动全通
   - `❌无回读`   = 没短接（正常，没跳线的口都这样）/ 短错脚 / 接触不良
   - `⚠️回读不一致` = 通是通了但字节错 → 波特率不对 / 干扰 / 接触不良

脚本是**纯标准库**（termios），板子上没 pyserial 也能跑。

---

## 二、排查实录：一个放反的短接帽

第一次轮测，4 个口**全部 `❌无回读`**。下面是怎么一步步焊死病因的——**这才是要学的部分**。

### 第 1 步：分层定位，别跳层
不是上来就改代码，而是按 `物理 → 驱动 → 应用` 分层。先确认软件这层：
4 个口 `stty` 都能正常打开、配置 → **驱动层没问题**。

### 第 2 步：用"仪器"焊死，别猜
没有逻辑分析仪，就用内核自带的串口字节计数器当仪器：
```bash
cat /proc/tty/driver/serial | grep -E "^[1-4]:"
# 发送前： 1: ... tx:30 rx:0
# 发送后： 1: ... tx:45 rx:0     ← tx 涨了(我发的字节真出去了)，rx 始终 0(没回来)
```
**这一步定性了：软件在发、物理没回。问题铁定在物理层，不在代码。** 省掉了所有"改代码瞎试"。

### 第 3 步：查事实，确认引脚真的对
怀疑"是不是引脚没路由 / 是 RS485"。查设备树 + pinmux：
```bash
cat /sys/kernel/debug/pinctrl/*/pinmux-pins | grep -iE "uart|serial"
# pin 17 (gpio0-17): ff0b0000.serial ... rm-io17-uart1-tx   ← 排针 8 脚 = ttyS1 TX
# pin 16 (gpio0-16): ff0b0000.serial ... rm-io16-uart1-rx   ← 排针 10 脚 = ttyS1 RX
```
**IO 矩阵确实把 UART1 路由到了 8/10 脚，引脚定义没错。** 排除了软件和路由，只剩接插件。

### 第 4 步：真凶是短接帽（现场常识）
看手册才发现两个坑叠在一起：

| 排针 | 间距 | 形态 |
|---|---|---|
| BOOT/MASKROM（烧录用） | **2mm** | 2PIN 单排 |
| 40Pin IO 扩展排针 | **2.54mm** | 双排 |

- **坑① 间距不同**：烧录用的是 2mm 短接帽，套到 2.54mm 排针上接触不良。
- **坑② 方向放反**：40Pin 编号奇数一排、偶数一排，**8 和 10 在同一排、左右相邻**：
  ```
  列:  1   2   3   4   5
  奇排: 1   3   5   7   9
  偶排: 2   4   6  [8] [10]     ← 8、10 同排相邻，帽子要"顺这排放平"
  ```
  直觉竖着扣（横跨两排）短到的是同一列的 **7-8 或 9-10**，不是 8-10。

**改用母对母杜邦线插 8、10 两孔 → `✅自环通过`**：
```
发送前  tx:45 rx:0  →  发送后  tx:60 rx:15    rx 第一次开始涨，发收一字不差
```

### 复盘一句话
> 代码和查手册 AI 几秒搞定；卡住你的是**接插件的间距/排序/方向**这种物理常识。
> 排查靠的是 **分层 + 仪器(计数器) + 查事实**，不是改代码。对应常识清单 §3 §4 §5 §10。

---

## 三、蓝牙 / WiFi 状态（实测可用）

模组：**Realtek RTL8723DU**（WiFi+BT 二合一，走 USB，`lsusb` 见 `0bda:d723`）。

| | 状态 | 证据 |
|---|---|---|
| **蓝牙** | ✅ 开机即通 | `hci0 UP RUNNING`，BlueZ 5.77，固件 `rtl8723d_fw.bin` 已加载；扫到 4 个周边设备 |
| **WiFi** | ✅ 硬件就绪、未连网 | `wlan0` 存在，rfkill 未拦(soft=0)；扫到 8 个 2.4G 热点；连 AP 用 `wpa_supplicant` |

工具：`bluetoothctl / wpa_supplicant / hostapd / hciattach / rtk_hciattach` 都有（缺 `iw`、`btmgmt`）。

### 蓝牙扫描
```bash
bluetoothctl power on
timeout 12 bluetoothctl --timeout 10 scan on
bluetoothctl devices            # 列出扫到的设备
# 配对：bluetoothctl → pair <MAC> → connect <MAC>
```

### WiFi 扫描 / 连接
```bash
ip link set wlan0 up
wpa_supplicant -B -i wlan0 -c <(printf 'ctrl_interface=/var/run/wpa_supplicant\nupdate_config=1\n')
wpa_cli -i wlan0 scan && sleep 5 && wpa_cli -i wlan0 scan_results   # 扫附近热点
# 连接：
wpa_cli -i wlan0 add_network
wpa_cli -i wlan0 set_network 0 ssid '"你的WiFi名"'
wpa_cli -i wlan0 set_network 0 psk '"你的密码"'
wpa_cli -i wlan0 enable_network 0
udhcpc -i wlan0                 # 拿 IP
```

> 注意：RTL8723D 是**单频 2.4GHz**，连不上 5G 的 AP 是正常现象。

### 可复用脚本 `wifi.py`（wpa_cli 后端，纯标准库）
把上面这堆裸命令封成网关可调用的模块，沿用 ClawHarbor `network.js` 的 4 函数契约：
```bash
python3 wifi.py status                       # 上行/SSID/信号/IP/外网/DNS
python3 wifi.py scan                          # 扫热点(信号+加密类型)
python3 wifi.py connect <SSID> <密码>         # 关联+DHCP+写入CONF(开机自连)
python3 wifi.py forget <SSID>
python3 wifi.py status --json                 # 给上层程序调用
```
实测全通过：scan/connect/DHCP/上外网 ✅；**密码用 PBKDF2 算成 PSK 哈希**再写入，
明文不进命令行也不进配置；连上即 `save_config` 落盘，重启自连。

### 为什么不用 NetworkManager？（板子给的答案）
这块板查下来：**无 `nmcli`/NetworkManager/connman、非 systemd（busybox init）、无包管理器（opkg/apt/apk 都没有）**，
只有 `wpa_supplicant v2.10` + 厂商 `S36wifibt-init.sh`。
- NM 不是 `pip install` 能装的系统守护进程，要 glib+dbus+一堆依赖、还基本得配 systemd；
  buildroot 要加它得**重编固件**，不是运行时能装的。
- 这种 MCU 级网关**本就该用 `wpa_supplicant`+`wpa_cli`+`udhcpc`**——更轻、已在板上。
> 这也解释了 ClawHarbor（x86 Ubuntu 桌面 + systemd + NM）的 `nmcli` 代码为何搬不过来：
> **不是一个量级的设备。搬"接口设计"，不搬"实现代码"。**

### 配网（首次） vs 运行（每次开机）——别混在一起
- **运行态**（无人值守）：读配置自动连 + 重试退避 + 有线优先回退，**绝不扫描、不等人确认**。
- **配网态**（装机有人）：才"扫描→选 SSID→填密码"，且通过 **BLE 配网 / hostapd 开 AP + 网页** 让人
  在手机上确认，而不是卡在网关代码里等。预置配置文件是最省事的批量做法。

---

## 四、连接方式备忘（怎么进这块板子）
现场没显示器，靠网络进：本机 → 跳板机 `192.168.1.227`(user) → 工业机 `192.168.1.10`(root/root)。
若 227 ping 不通工业机，多半是 227 接工业机的网口缺主机路由：
```bash
sudo ip route add 192.168.1.10/32 dev enp3s0      # enp3s0=227 上接工业机的有线口
```

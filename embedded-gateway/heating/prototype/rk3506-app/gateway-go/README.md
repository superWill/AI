# gateway-go · 网关核心 Python → Go 增量迁移

面向**量产**的网关核心语言迁移。策略:**增量、可对拍验证、安全件最后迁**——不做大爆炸重写。
背景与权衡见 git 历史的对比讨论;边缘 vs 云端分层见 [`docs/architecture/device-onboarding-paths.md`](../../../docs/architecture/device-onboarding-paths.md)。

## 为什么迁 Go(量产视角)
- 单**静态二进制 1.9 MB**(strip 后),对比 Python 解释器 + stdlib 占 **31 MB** flash;
- 静态类型,出厂前拦运行时错;启动快;吃满 3 核 Cortex-A7;单制品 OTA。
- 硬实时/安全在 MCU(C),不在本层;本层 GC 无碍。

## 迁移进度

| 组件 | Python 源 | 状态 | 验证 |
|---|---|---|---|
| **配置编译器** | `compiler.py` | ✅ 完成 | compile 4 产物语义对拍一致 + 坏草稿报错逐字一致 + **RK3506 实跑产物一致** |
| **配置适配层** | `loader.py` | ✅ 完成 | app_config 语义对拍一致 + **RK3506 跑完整 compile→load 流水线,产物与 Python 一致** |
| **MQTT 上送/下发** | `cloud-gateway-mqtt/gateway_mqtt.py` | ✅ 完成 | 单测 + **ECS 端到端**(遥测→mosquitto→ingest→PG)+ **断网缓存补传**(seq 连续无洞/replay)+ RK3506 armv7l 实跑;迁移中修正 `IsConnected`→`IsConnectionOpen`(原写法断网会静默丢数据) |
| **仿真数据源** | `app.py` 的 `SimSource` | ✅ 完成 | 时钟可注入,与 Python 固定时刻对拍:**12 个相位全一致**(sin+银行家舍入)+ RK3506 armv7l == Mac Python |
| **Modbus 协议核心** | `app.py` 的 `_crc`/请求帧/应答解析 | ✅ 完成 | **逐字节对拍** Python:CRC16/读写请求帧字节级一致 + 解析(正常/crc/异常/超时)语义一致 + 单测 + RK3506 armv7l == Mac |
| **Modbus 轮询状态机** | `ModbusSource.poll` 故障退避(招2/招5) | ✅ 完成 | 注入读结果+时钟,脚本化序列**逐步对拍** Python(离线判定/几何退避/恢复/int·float 格式化)+ RK3506 == Mac |
| **Modbus 串口传输** | `ModbusSource._txn` / termios(x/sys/unix) | ✅ 完成 | **板上 pty 真串口端到端**:Go 读模拟从站 == app.py 真实 ModbusSource(偏移/数量正确 + 静默→timeout 一致) |
| 控制/安全逻辑(对拍) | `app.py` safety_check + Controller | 🟡 **对拍验证通过(含双端闭环),未切生产** | L1 决策(含多小数 reason 逐字一致)+ L2 SimSource 闭环 + L3 单pty写值 + **L3 双端完整闭环**(板上两端 /dev/pts 桥接:Controller→FC06写→从站→轮询回读→confirm,confirmed/timeout 两结局 Go==Python),均与 app.py 真实实现对拍一致。⚠️ **接真实设备 / 替换生产控制器 仍未做**(需授权) |
| **运行时状态容器** | `app.py` 的 `Runtime` | ✅ 完成 | 时钟可注入,脚本化 ops 对拍 app.py 真实 Runtime:快照/事件(上限20,新→旧)/指令(上限50,view 取10)/telemetry seq+设备列表/看门狗时戳;含上限与顺序场景 + armv7l==Mac |
| 运行时外壳其余(轨A) | `app.py` 的 HTTP/REST/SSE、三个 loop、main() 装配、内置 MqttClient | ⬜ 进行中 | 装配成可替 `python3 app.py` 的 Go 网关 daemon(sim→板上对拍) |
| HMI | `hmi_lvgl`(C/LVGL) | — | 已是原生,不在迁移范围 |

- `compiler.py` + `loader.py` → **单个 `gatewayc` 二进制(1.9 MB)+ 子命令**(`compile`/`load`)。
- `gateway_mqtt.py` → **`gateway-mqtt` 二进制(armv7l 5.1 MB,含 paho)**,守护进程。

## 这是什么 / 不是什么(诚实边界)
- **是**:网关的**核心逻辑 + 运行时状态**(配置/采集/控制/安全/MQTT/Runtime)已逐组件移植,**均与 app.py 真实实现对拍一致 + RK3506 实跑**。
- **不是**:① 还没装配成一个能替 `python3 app.py` 的 Go 网关 daemon(HTTP/REST/SSE、三个 loop、main 装配、内置 MqttClient 统一 —— 轨 A 进行中);② **从未接真实设备、从未替换生产控制器**(轨 B,需显式授权 + 真机影子并行等闸门)。Python 仍是唯一生产实现。

## 构建 / 验证

```sh
# 本机构建
go build -o gatewayc .

# 编译草稿 → 产物（对照 compiler.py，flag 任意顺序）
./gatewayc compile samples/heating_draft.json --out build_go
# 产物 → app.py 运行配置（对照 loader.py）
./gatewayc load build_go --emit-app-config app_config.json

# 与 Python 对拍(对象不看键序 / 数组多重集 / 数字按值)
python3 ../compiler.py samples/heating_draft.json --out build_py
python3 compare.py build_py build_go            # 4 产物: 全部一致 ✅
# app_config 对拍：分别用 loader.py / gatewayc load 出配置再比

# 控制器 L1 决策 + L2 SimSource 闭环对拍（调用 app.py 真实实现）
GOCACHE=/tmp/rk3506-go-cache python3 controller_harness.py

# L3 在 RK3506 上只接虚拟 PTY，不碰 /dev/ttyS*
python3 controller_l3_board.py ./gatewayc-arm ../app.py

# 交叉编译到 RK3506(armv7l) + strip
GOOS=linux GOARCH=arm GOARM=7 go build -ldflags="-s -w" -o gatewayc-arm .
# 上板跑完整流水线:scp gatewayc-arm root@<板子IP>:/tmp && ./gatewayc-arm compile ... && ./gatewayc-arm load ...
```

## 文件
| 文件 | 作用 |
|---|---|
| `compiler.go` | `Validate` + `Compile` + 4 个 `build*`(对照 compiler.py) |
| `loader.go` | `LoadRuntimeCfg`(对照 loader.py) |
| `sim.go` | `SimSource` 仿真源(对照 app.py),时钟可注入 |
| `modbus.go` | Modbus 协议核心:CRC16 / 请求帧 / 应答解析(对照 app.py ModbusSource) |
| `modbus_poll.go` | Modbus 轮询故障退避状态机(读结果+时钟可注入) |
| `serial_linux.go` / `serial_other.go` | Modbus 串口传输(Linux termios via x/sys;非 Linux 给 stub) |
| `controller.go` | `safety_check + Controller` 决策链，依赖注入，尚未接生产执行器 |
| `controller_case.go` / `controller_harness.py` | 脚本化运行 Go Controller，并与 `app.py` 真实 Controller 对拍 |
| `controller_l3_board.py` / `modbus_write_harness.py` | 板上 PTY 对拍 Python/Go 的写值映射、FC06 帧与回显确认 |
| `controller_loop.go` / `controller_loop_other.go` | **双端完整闭环 L3** 的 Go 端:串口轮询 + Apply + 回读 confirm(Linux;非 Linux stub) |
| `pty_link.py` / `modbus_slave_on.py` / `controller_loop_harness.py` / `controller_l3_loop_board.py` | 双端 pty 桥 + 开路径从站 + Python 闭环 + 板上编排对拍 |
| `runtime.go` / `runtime_case.go` | 运行时状态容器 `Runtime`(对照 app.py)+ 脚本化对拍 runner |
| `runtime_view.go` | 数据源 `{addr: sample}` → Controller/HMI 使用的稳定有序 `devices[]` 快照 |
| `modbus_write.go` | `point_id + value + control_map` → `addr/reg/register_value`，银行家舍入对齐 Python |
| `main.go` | CLI 子命令:`compile` / `load` / `simpoll` / `modbusframe` / `modbuspoll` / `modbusread` / `modbuswrite` / `controllercase` / `simcontrolcase` / `controllerloop` / `runtimecase` |
| `mqtt/gateway_mqtt.go` | 云↔网关 MQTT 守护进程(对照 gateway_mqtt.py),`go build ./mqtt` |
| `*_test.go` | 单测:MQTT 逻辑 / Modbus CRC·帧·解析 |
| `*_harness.py` / `compare.py` / `*_scenario.json` | 对拍工具(调用 Python 真实代码作参照) |

## 原则(沿用 Python 版)
- 纯函数、零外部依赖(仅 Go 标准库);
- 校验在编译期,运行时不再解释草稿;
- **任何迁移组件,先在 RK3506 上跑通 + 与 Python 对拍一致,才算完成**(见 heating `CLAUDE.md`)。

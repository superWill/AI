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
| 控制/安全逻辑(对拍) | `app.py` safety_check + Controller | 🟡 **对拍验证通过,未切生产** | L1 决策(含多小数 reason 与 Python 逐字一致)+ L2 SimSource 闭环 + L3 **单 pty 写值**(板上 armv7l,FC06 帧逐字节一致、银行家舍入一致),均与 app.py 真实 Controller 对拍一致。⚠️ 仅对拍:**双端完整闭环 / 接真实设备 / 替换生产控制器 均未做** |
| HMI | `hmi_lvgl`(C/LVGL) | — | 已是原生,不在迁移范围 |

- `compiler.py` + `loader.py` → **单个 `gatewayc` 二进制(1.9 MB)+ 子命令**(`compile`/`load`)。
- `gateway_mqtt.py` → **`gateway-mqtt` 二进制(armv7l 5.1 MB,含 paho)**,守护进程。

## 这是什么 / 不是什么
- **是**:`config_draft.json → 4 产物`(point_registry / poll_plan / display_model / safety_policy)的纯函数编译器,逐函数对照 `compiler.py`,错误串逐字一致。
- **不是**:还没碰运行时、采集、控制、安全执行。那些按上表顺序、并行验证后再迁。

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
| `runtime_view.go` | 数据源 `{addr: sample}` → Controller/HMI 使用的稳定有序 `devices[]` 快照 |
| `modbus_write.go` | `point_id + value + control_map` → `addr/reg/register_value`，银行家舍入对齐 Python |
| `main.go` | CLI 子命令:`compile` / `load` / `simpoll` / `modbusframe` / `modbuspoll` / `modbusread` |
| `mqtt/gateway_mqtt.go` | 云↔网关 MQTT 守护进程(对照 gateway_mqtt.py),`go build ./mqtt` |
| `*_test.go` | 单测:MQTT 逻辑 / Modbus CRC·帧·解析 |
| `*_harness.py` / `compare.py` / `*_scenario.json` | 对拍工具(调用 Python 真实代码作参照) |

## 原则(沿用 Python 版)
- 纯函数、零外部依赖(仅 Go 标准库);
- 校验在编译期,运行时不再解释草稿;
- **任何迁移组件,先在 RK3506 上跑通 + 与 Python 对拍一致,才算完成**(见 heating `CLAUDE.md`)。

# RK3506 供热网关应用(集成 keystone)

把分散的 bringup demo 收敛成**一个应用**:一份"点表快照 + 设备注册表",同时喂
本地触摸屏、Web 管理界面、MQTT 上云、控制闭环。纯标准库,零依赖(连 MQTT、socket.io
都是自实现的,板子上不用 pip 装任何东西)。

```
数据源(sim 内置仿真 / modbus 真串口) ─► 统一快照 + 注册表(app.py 内核)
     │
     ├─ 本地触摸屏  drm_hmi_v4.py + dashboard.py   (DRM 直写,多页 + 触摸控制)
     ├─ Web 界面    nexus_server.py + nexus-dist/   (真 nexus-edge-os 前端 + 适配)
     ├─ MQTT 上云    station/{id}/telemetry · heartbeat
     └─ 控制闭环      下发设定值 → 安全校验 → 写回源 → 反馈收敛 → 回显
```

## 两个界面,一份数据

| 界面 | 跑在哪 | 是什么 |
|---|---|---|
| **本地触摸屏** | 板子物理 LCD(800×480,Goodix 触摸) | `drm_hmi_v4` 直写 DRM 的 edge-os 风格仪表盘,**侧栏可点切页**:总览/监控/设备/控制/设置,控制页 [−][+] 按钮下发设定值。中文用 GNU Unifont 点阵(`cjk_font.py`),无浏览器/无字体库。 |
| **Web 管理界面** | 浏览器(PC/手机) `:8092` | `nexus_server` 托管**真 nexus-edge-os 前端**(`nexus-dist/`),Python 后端实现它要的 REST + 自实现 socket.io 实时。板子(armv7l/无 Node)跑不了 edge-os 的 Node 后端,故只搬前端 + 适配。 |

> 两个界面读同一份 `/api/snapshot`;`nexus_server` 既服务 Web 前端,也服务 `/api/snapshot` 给触摸屏。

## 文件

| 文件 | 作用 |
|---|---|
| `app.py` | 内核:数据源(sim/modbus)、统一快照+注册表、控制器(安全校验)、stdlib MQTT、stdlib HTTP/REST/SSE。可独立跑(轻量后端),也被 nexus_server 复用 |
| `app_config.json` | 设备/点位/MQTT/控制映射。每点位同时带 sim(base/swing)和 modbus(reg/scale)字段 |
| `nexus_server.py` | Web 后端:托管 nexus-edge-os 前端 + REST(/api/login /init /tags/write /command…)+ 自实现 socket.io(Engine.IO v4 polling)推 tag-change/node-change/system-metrics |
| `nexus-dist/` | nexus-edge-os 已构建前端(来自 `Coding/apps/apps/edge-os/frontend/dist`) |
| `dashboard.py` | 触摸屏渲染器:多页(总览/监控/设备/控制/设置)→ 800×480 RGB 帧 + 按钮命中区。`__main__` 可渲染 PNG 预览 |
| `cjk_font.py` | GNU Unifont 点阵子集(中文显示,随 dashboard 文案重新生成) |
| `drm_hmi_v4.py` | 本地触摸屏主程序:读 `/api/snapshot` → dashboard.render → blit DRM;读 `/dev/input/event0` 触摸 → 切页/下发控制 |
| `drm_hmi_v2.py` `drm_hmi_v3.py` | 早期 LCD(v2 ASCII、v3 图形无触摸),已被 v4 取代,留作参考 |
| `sim_104.py` `sim_104_config.json` | 104 现场陪练:扩展 Modbus 模拟器(8类设备 + 写寄存器 + 设定值收敛) |
| `tools/serial_bridge.py` | 测试用 pty 虚拟串口对,本机把模拟器和网关接起来 |
| `deploy/` | `S99gateway`(busybox 自启)、`install.sh`(板上安装)、`push.sh`(经 .104 跳板推送) |

## 本地跑(任意机器,sim 源)

```bash
# Web 界面(真 edge-os 前端):
python3 nexus_server.py --config app_config.json --dist nexus-dist --port 8092
#   浏览器 http://127.0.0.1:8092/  (随便填账号登录)

# 触摸屏渲染器单页预览(出 PNG):
python3 dashboard.py control      # → /tmp/dash_control.png

# 控制/快照 REST:
curl -s http://127.0.0.1:8092/api/snapshot
curl -X POST http://127.0.0.1:8092/api/command -H 'Content-Type: application/json' \
     -d '{"point_id":"valve_open_sp","value":80}'
```

可控点位:`valve_open_sp`(0–100%)、`pump_freq_sp`(0–50Hz,≈流速)、
`sec_supply_temp_sp`(20–75℃),均经 `app.py` 的 `SAFE_RANGES` 校验。

## 接真串口陪练(104 当模拟器)

```bash
# 104(USB-TTL): 扩展模拟器
python3 sim_104.py /dev/ttyUSB0 sim_104_config.json
# 板子(ttyS1): nexus_server 切 modbus 源
python3 nexus_server.py --config app_config.json --source modbus --serial /dev/ttyS1
```
本机无硬件验证:`tools/serial_bridge.py` 建两个互联 pty,把模拟器和网关接起来,
走的是和真串口完全相同的 Modbus 帧/CRC/超时/写应答代码路径。

## 部署到板子(开机第一屏)

```bash
sh deploy/push.sh        # Mac 上(需 sshpass,或 NO_SSHPASS=1 用免密)
```
推送后:`/userdata/rk3506-app`,自启 `/etc/init.d/S99zz-gateway`(排在厂家 LVGL 之后,
启动前清掉 lv_demo/旧 energy-hmi 抢屏)。重启后第一屏即触摸仪表盘,Web 在 `:8092`。

> **nexus-dist 是另一个仓库(edge-os)的前端构建产物**;若 `nexus-dist/` 不在,
> 从 `Coding/apps/apps/edge-os/frontend/dist` 复制一份即可。

## 验证状态(均已实测)

- ✅ sim/modbus 两源、REST/SSE、控制闭环、安全拒绝(Mac + pty 虚拟串口端到端)
- ✅ MQTT 上行 + 平台下发控制 + command_reply(自写 mini-broker)
- ✅ nexus-edge-os 前端 + 自实现 socket.io 实时(Mac + 板子双端)
- ✅ 触摸屏多页仪表盘 + 中文点阵(板子自渲染 PNG 回传确认);Goodix 触摸坐标 1:1
- ✅ 真板子部署 + busybox 开机自启(重启实测第一屏自动起)
- ⏳ 物理 tap 用户确认;edge-os 高级页(SCADA/规则/AI/北向)后端先返空;真鉴权

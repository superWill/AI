# 替换范围 + 生产化缺口 + 路线(诚实版)

> 触发:评审指出「Go 已基本替代 app.py 核心,但还不能替代板上完整 Python 生产系统」。
> 本文把范围钉死、把 P0 门槛列清,作为轨 B 之后的工作基准。**不再迁普通业务代码**。

## 1. 替换范围(关键澄清)
**`gatewayc` 替代的是 app.py 的「网关核心」,不是 `nexus_server.py` 的完整生产系统。**

| 能力 | 归属 |
|---|---|
| 采集 / 控制 / 安全 / Runtime / MQTT / HTTP 核心(health·snapshot·SSE·command·event·静态)/ 三 loop | ✅ Go(gatewayc) |
| edge-os 前端适配 + Socket.IO | ⛔ 仍 Python(nexus_server) |
| 登录 / Bearer 鉴权 | ⛔ 仍 Python |
| 配置 draft/compile/**activate/rollback** 接口 | ⛔ 仍 Python(nexus_server 的版本化激活链,见 runtime-activate-reload-*) |
| `/api/tags/write`·`/api/init` 等前端兼容接口 | ⛔ 仍 Python |
| 板载 LCD(drm_hmi_v4) | ⛔ 原生 C/Python,不在迁移范围 |

**采纳方案(评审推荐,确认为方向):Go 负责核心网关,Python 暂留 Nexus/HMI/配置管理适配层。**

### 1a. 集成皱褶(评审未点到,但绕不过)
`nexus_server.py` 现在 **`from app import Runtime/SimSource/ModbusSource/Controller`,把核心内嵌在同进程**。
Go 转正后 nexus **不能再内嵌 app.py**——必须改为经 `gatewayc` 的 **HTTP(/api/snapshot·/api/command)+ MQTT** 取数/下发。
即「Go 核心 + Python 适配层」不是零成本共存,需要把 nexus 从「内嵌核心」重构成「gatewayc 的客户端」。这是边界工作的一部分,须单列。

## 2. P0 阻塞(替换生产前必须清)
1. **真实现场影子 14 天**:✅ 真机影子**已起**(本会话,armv7,RSS 平台 ~7.3MB,决策对拍一致)——但**数据是 sim、跑了几分钟、非 14 天、无真实设备**。仍需:真实设定值调整 / 设备离线 / 网络中断 / 昼夜 / 资源稳定性。见 [`track-b-shadow-plan.md`](track-b-shadow-plan.md)。
2. **真实执行器写入**:⛔ 从未向真泵/阀/变频器写寄存器(只 pty/模拟从站闭环)。影子通过后需台架或单站灰度验地址/寄存器/比例/反馈/联锁。
3. **生产安装/启停脚本仍启 Python**:⛔ `deploy/S99gateway:25` 起 nexus_server + drm_hmi_v4;`deploy/install.sh` 不装 gatewayc。需正式 Go 安装/启停/版本切换/健康检查/一键回退。
4. **缺进程崩溃自动拉起**:⛔ 现 busybox nohup,退出无人重启。Go 切生产前需 busybox supervisor 循环 / 硬件看门狗联动 / 等效监督。

## 3. 进入灰度前还缺
- 单站灰度方案:Python/Go 可快速切换。
- 启动健康门:采集 + HTTP + MQTT + 关键设备正常才算 Go 启动成功。
- 自动回滚条件:崩溃 / 采集停滞 / 关键点位异常 / MQTT 长期离线。
- Go/Python 版本化安装目录 + 原子 active 指针(可复用 nexus 已有的 versions/active 机制)。
- 灰度期日志 / 指标 / 现场验收报告。

## 4. 非迁移差异,但生产前应处理
- HTTP `/api/command` 无真实鉴权。
- gatewayc MQTT 无 TLS / 设备证书接入。
- MQTT 遥测缓存仅内存,进程重启丢(需 FileStore 或落盘队列)。
- `valid_until` 失联回退未落实。
- OTA / 签名校验 / 失败回滚未做。

## 5. 完成度判断(认同评审)
- 目标=「替代 app.py 核心」:**~85–90%**(剩的多是生产装配/监督/回退脚本 + 真实影子,非核心代码)。
- 目标=「替代板上完整 Python 生产系统」:**~60–70%**,主缺口=Nexus/HMI 兼容边界 + 生产部署 + 真实影子浸泡 + 单站灰度回退。

## 6. 正确路线(不再迁业务代码)
真实板影子 14 天(覆盖真实设定值/离线/断网/昼夜/资源)
→ 定 Go↔Nexus 边界并把 nexus 重构成 gatewayc 客户端(§1a)
→ 生产安装 + 双版本原子切换/回退 + 进程监督 + 启动健康门
→ 单站受控灰度(真实执行器首次写,可秒回 Python)
→ 现场验收 → 才替换 Python。

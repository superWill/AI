# 轨 A 验收记录(里程碑冻结)

> Python→Go 网关核心迁移「轨 A:整机可替代 `python3 app.py`」的验收快照。
> 验收对象 = 本分支 `feat/heating-gateway-go-migration` 的干净 `HEAD`。
> 轨 B(真机影子并行→灰度)见 [`track-b-shadow-plan.md`](track-b-shadow-plan.md),**未执行,需显式授权**。

## 验收基线
- 提交:`6cf8307`(分支较 `main` 多 13 个提交)
- 日期:2026-06-23
- 方式:`git worktree add HEAD` 干净检出重跑——**不依赖任何未提交工作树改动**

## 干净 HEAD 可复现(Mac)

| 项 | 命令 | 结果 |
|---|---|---|
| 构建 | `go build -o gatewayc .` | ✅ |
| 并发/单测 | `go test -race ./...` | ✅ `ok gatewayc` + `ok gatewayc/mqtt`(含 Modbus CRC/帧/解析、MQTT 缓存逻辑) |
| 量产制品 | `GOOS=linux GOARCH=arm GOARM=7 ... -ldflags="-s -w"` | ✅ armv7 静态 **5.75 MB** |
| 控制/安全对拍 | `controller_harness.py --go-bin ./gatewayc` | ✅ **6/6**:fallback_and_write_failure · rate_and_interlock · feedback_confirmed · feedback_timeout · multidecimal_reasons · sim_source_closed_loop |
| 运行时对拍 | `runtime_harness.py --go-bin ./gatewayc` | ✅ **2/2**:basic · caps |
| 编译器对拍 | `compiler.py` vs `gatewayc compile` + `compare.py` | ✅ 4 产物全一致 |
| 仿真源对拍 | `sim_harness.py` vs `gatewayc simpoll`(12 相位) | ✅ **12/12** 一致(sin+银行家舍入) |

## 硬件/ECS 在环(已验证,需对应环境,不在 Mac 复现)
- **RK3506 armv7l 实跑**:compile→load 流水线产物与 Python 一致;`--source modbus` 经串口轮询 pty 从站读数正确;双端 pty 完整闭环(Controller→FC06 写→从站→回读 confirm,confirmed/timeout 两结局 Go==Python)。
- **ECS MQTT 上行**:Go daemon vs `app.py` 同跑,telemetry/heartbeat 帧结构一致;隔离掐 daemon 链路 9s(订阅者全程在线)→ seq 连续无洞、缓存帧标 `replay:true`、断网瞬间帧靠 PUBACK 失败收进缓存。
- **ECS MQTT 下行**:property/set 订阅放进 OnConnect;首连竞态(daemon 先于 broker 起)+ 断线重连两场景,云端命令均被收到并回 command_reply。

## 准确边界(不夸大)
- **MQTT 投递 = 至少一次**:内存环形缓存,超 `buffer_max` 丢最旧、**进程重启丢缓存**;QoS1 PUBACK 不确定时可能重复。即「进程存活、缓存未满窗口内 seq 连续无洞,平台须按 seq 去重」。跨重启不丢需 paho FileStore + `CleanSession=false`(未启用)。
- **仅证明「测试环境等价」**,尚未证明「现场长期等价」——后者是轨 B 影子运行的目的。
- **从未接真实设备、从未替换生产控制器**:Python 仍是唯一生产执行,Go 全程并行旁路。

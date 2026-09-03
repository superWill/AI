# 轨 B 阶段一:只读影子并行(设计草案,未执行)

> 状态:**仅设计与评审,未执行,需用户显式授权才动手。**
> 前置:轨 A 已冻结验收([`track-a-acceptance.md`](track-a-acceptance.md))。
> 本阶段只做「只读影子」,**不含**灰度/切流——灰度是后续独立阶段,另行评审。

## 0. 为什么需要这一阶段
轨 A 只证明了「**测试环境等价**」(对拍 + pty + ECS)。它没证明 Go 在**真实现场、长时间、真实工况波动**下与 Python 等价。影子并行用最低风险拿到这个证据:Go 跟着真实数据跑,只观察、只对比,**不碰任何执行器**。

## 1. 硬不变量(代码层强制,非口头约定)
| 不变量 | 强制方式 |
|---|---|
| **Go 禁止写寄存器** | 影子构建用 `//go:build shadow` tag,串口层 `Write`/`BuildWriteRegister` 的发送路径替换为 `panic("shadow: register write forbidden")`;FC06/FC16 编码可保留(用于对比意图),但**物理发送函数被去除**。 |
| **Go 禁止接管控制输出** | `Controller.Write` 注入 `shadowExecutor`:只记录「打算写 point=X value=Y」到影子日志,**return 不触碰总线**。无任何代码路径能从 Go 到达执行器。 |
| **Python 继续唯一生产执行** | app.py 不改、不停;它仍是 RS485 唯一主站、唯一写设定值者。Go 进程对 app.py **零依赖、零干扰**(见 §2 总线问题)。 |
| **可一键停** | Go 影子是独立 systemd unit(`gatewayc-shadow`),`systemctl stop` 即彻底消失;停它对生产**无副作用**(它本就不在控制回路里)。 |

## 2. 正面处理:RS485 单主总线冲突
RS485 总线**只能有一个主站**。app.py(Python)正在轮询,Go **不得**同时主动轮询同一总线——双主必冲突。两条合规取数路径:

- **2A 软件喂数(先行,零硬件改动)**:app.py(`--shadow-tap` / `--shadow-sock`)把每轮原始采样(`{addr: sample}`,寄存器原值 + 质量码)经本地 IPC 旁路出来;Go 影子消费,驱动自己的 **Runtime + Controller 决策**做对比。两条传输已实现:
  - **localhost MQTT**(`_shadow/samples`)——有 broker 时,且能同时订 `property/set` 做**决策对账**;
  - **unix datagram**(`--shadow-sock`/`--samples-sock`)——板上无 broker 的兜底,best-effort 不阻塞生产;仅 view/资源对比(无命令流)。
  - 覆盖:Runtime/控制决策(MQTT 模式)/告警/资源占用。
  - 不覆盖:Go 自己的 Modbus 主站采集(那段已在 pty + 板上验证,此处不重复冒险)。
- **2B 被动嗅探(可选增强,需接线)**:第二路 UART **仅接 RX** 到 RS485 收发器,listen-only 抓 app.py 的请求帧 + 从站应答帧,用 Go 的 `ParseReadHolding` 重建采样。物理上无 TX,等价不变量天然成立。
  - 覆盖:额外验证 Go Modbus 解析对真实总线时序的鲁棒性。

阶段一**先做 2A**;2B 作为可选项,接线方案需另核实硬件(标「待核实」,不臆造引脚)。

## 3. 对比维度与判据
影子与生产**同源数据**,逐周期对比并落盘:

| 维度 | 对比内容 | 容差 / 判据 |
|---|---|---|
| 采集值 | 每点位 `v`(标定后) | 数值相等(浮点 6 位);质量码 `q` 完全一致 |
| 状态 | 设备 offline/在线、退避计数、watchdog age | 一致(允许 1 周期相位差) |
| 告警 | 事件流 kind/action(feedback_timeout、联锁、离线…) | 集合一致;时序允许 ≤1 周期偏移 |
| 控制决策 | Go「打算写」的 point/value/status(accepted/blocked_by_safety/blocked_by_interlock/rate…)vs Python 实际决策 | **逐条一致**(这是影子最关键的指标:证明 Go 的安全/联锁判定与 Python 现场一致) |
| 资源占用 | RSS、CPU%、FD 数、采集→上送端到端时延 | Go 不劣于设定阈值(见 §5);记录分布而非单点 |

采集方法:影子每周期把自身 View + 决策写 `shadow_diff.jsonl`;旁置比对器读两侧时间对齐后出差异报告 + 每日汇总。

## 4. 浸泡周期与停止条件
- **浸泡周期**:连续 **≥14 天**真实运行(覆盖工作日/周末、昼夜温度循环、至少一次现场设定值调整与一次设备异常/离线事件)。期间不得有未解释的 diff。
- **停止条件(命中即停影子、归零重查,不带病前进)**:
  1. 控制决策出现**任一条**不一致(最高优先级——安全语义分歧)。
  2. 采集值/质量码分歧率 > 0.1%(排除已知相位差后)。
  3. 告警集合分歧(漏报或多报)。
  4. Go RSS 持续 > 阈值 或 OOM、崩溃、FD 泄漏。
  5. 发现任何 Go→执行器的代码路径(不变量被破坏)。
- **回滚方式**:`systemctl stop gatewayc-shadow && systemctl disable gatewayc-shadow`。因影子不在控制回路,停它**不需要**回滚生产、不影响供热。这正是只读阶段的价值。

## 5. 资源阈值(待实测校准,先给占位)
- RSS:< 40 MB(待核实——armv7 上 paho + 运行时实测后定);
- CPU:稳态 < 单核 10%;
- 端到端(采集→上送)时延:与 Python 同量级,不长于其 1.5×。
> 阈值现为占位,**进入阶段一第一天先实测建基线**再固化,不拿猜测值当门槛。

## 6. 阶段一交付物
1. `//go:build shadow` 影子构建 + `shadowExecutor`(写被 panic 封死)+ 不变量单测(断言无写路径)。
2. app.py 旁路出数的最小改动(2A)——**这是唯一对生产代码的改动,需单独 plan + 评审**。
3. 比对器 + 每日 diff 报告。
4. 14 天浸泡报告:diff 率、资源曲线、命中的停止条件(若有)。

## 6b. 阶段一进展(2026-06)
- ✅ **Go 影子 + 写封死 + 不变量测试**已落(`gateway_shadow.go` / `shadow_test.go`,`gatewayc shadow`)。
- ✅ **比对器**`shadow_compare.py`(板外只读对账)已落。
- ✅ **app.py 只读旁路**(2A,`--shadow-tap`,默认关)已落并经真程序验证。
- ✅ **ECS 全链路 dry-run**(真 app.py `--shadow-tap` + `gatewayc shadow` + 比对器,8 设备 sim):
  注入 3 条命令(2 放行 + 1 越界),**决策对账 3/3 一致**(`decision_diffs:0`、`pending:0`)、
  `view_diffs:0`(tol 0.5)、Go 影子 RSS ~5–7 MB(amd64)。
- ⏳ **待板子物理接入**(USB 网卡 en12 当前未连):上板跑真实影子、armv7 RSS 基线、14 天浸泡。
  接入后:Mac 跑 `scripts/setup_rk3506_macos_route.sh` → 板上 `app.py --shadow-tap` + `gatewayc-arm shadow` →
  板外 `shadow_compare.py --http http://192.168.1.10:8092`。

## 7. 明确不做(本阶段边界)
- 不写任何寄存器、不接管控制、不切流、不灰度。
- 不改 app.py 控制逻辑(仅加只读旁路出数,且需单独评审)。
- 阶段一通过 ≠ 可上线;灰度是**下一个**需独立授权与评审的阶段。

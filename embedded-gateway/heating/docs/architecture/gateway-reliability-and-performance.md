# 网关可靠性与性能(不卡死 + 提吞吐)

> 从"能跑通"到"敢上线"的核心。**卡死=可靠性问题,性能=吞吐/延迟问题,分开治。**
> 相关:[分级运行循环](runtime-loops.md) · [Modbus/RS485 基础](../protocols/fieldbus-modbus-rs485-basics.md) · [常识清单 §4 §5 §7 §9](../embedded-common-sense.md) · 上传缓冲雏形见 [`gateway_mqtt.py`](../../prototype/cloud-gateway-mqtt/gateway_mqtt.py)

---

## 1. 先分清:主站 vs 从站,两种循环模型

| 角色 | 循环模型 | 像什么 |
|---|---|---|
| **从站 / server** | **被动**:死循环阻塞等请求,来了才应答 | Web 服务器等请求 |
| **主站 / master** | **主动**:按自己节奏轮询,发了等回复(超时) | 你拿手机刷接口 |

- **从站是独立设备**(温度表等),它固件自己跑"永远在听"的循环,不在你网关代码里。
- **你的网关对下是主站**:不需要"被动等"的线程,而是一个**独占串口的轮询循环**。
- **网关对上当 Modbus-TCP server 暴露数据给 SCADA 时**,那一面是从站,才有监听线程在等。

```python
# 网关主站轮询循环(真实形态)
while True:
    for 表 in 仪表列表:                       # 挨个点名(polling)
        req = build_read_holding(表.addr, 0, 2)
        ser.write(req)
        resp = read_with_timeout(ser, 1.0)    # 等回复,超时=这台掉线
        if resp: 表.温度 = parse(resp)
        else:    表.标记掉线()
    time.sleep(5)
```
> 铁律:RS485 半双工,**只能一个线程独占一条总线顺序轮询**,绝不能多线程同时往一条总线发(撞车)。

---

## 2. 为什么会卡死——根因

1. **阻塞调用没超时**(最常见):串口 read 永久阻塞、socket connect/publish 阻塞、DNS 阻塞——任一不超时,整循环吊死。
2. **一个慢/坏设备拖垮整轮**:一台掉线的表每轮花满超时(1s×重试),10 台坏的=每轮卡 10s+。
3. **采集与上传耦合**:循环里"采→发→采",网络一卡,采集也停。
4. **真死锁/驱动卡住**,无人 recovery。

## 3. 治卡死(可靠性)——5 招

1. **所有 I/O 必须带超时,永不无限阻塞**(串口 `timeout=`、socket `settimeout()`、connect 超时、DNS 超时)。这是铁律。
2. **故障隔离:坏设备短路掉**——连续超时 N 次→标记离线→**降频轮询(退避)**,别每轮花满超时等它。
3. **解耦:采集/上传分线程,中间队列缓冲**——网络卡了采集照常往队列塞(满了落盘=离线缓冲),恢复后补传;一边堵不拖死另一边。
4. **看门狗兜底**——软件喂狗超时→重启进程;`systemd WatchdogSec + Restart=always`;无 systemd 用硬件 `/dev/watchdog`,程序彻底死也能复位。
5. **把每个外部依赖都当"它一定会挂"来写**:网络/DNS/串口/设备,全部超时+重试+降级到安全默认。

## 4. 提性能(吞吐/延迟)——按收益排序

1. **批量读(第一性价比)**:Modbus 一帧最多读 **125 个连续寄存器**,别一个寄存器一帧。相邻点合并→帧数砍 10 倍→速度涨 10 倍。
2. **分级轮询**:温度 5s、状态字 30s、配置 5min,按重要性/变化速度分频。
3. **多条总线并行**(突破半双工瓶颈):挂太多从站就拆多条 RS485(板子 `ttyS1~ttyS4`),每条一个独立轮询线程并行。**并行只能跨总线,同一总线内绝不能并行。**
4. **提波特率**:9600→115200 直接快十倍(线质量/设备支持的前提下)。
5. **能上 Modbus-TCP 就比 RTU 快**:全双工、可并发多请求/多连接。
6. **异步/事件驱动(`select`/`asyncio`)**:一个线程管多串口+网络,省线程开销和锁。

---

## 5. 架构:行业标准三层(把上面串起来)

```
┌── 采集层 ──┐     ┌─ 缓冲层 ─┐     ┌── 上传层 ──┐
│ ttyS1 poller│push │  队列    │pull │ MQTT 上云   │
│ ttyS2 poller│───► │ +落盘缓冲 │───► │ (断网补传)  │
│ (各自超时   │     │ +时间戳   │     │ (TLS)       │
│  退避/隔离) │     │ +质量码   │     │             │
└─────────────┘     └──────────┘     └─────────────┘
        ↑各线程喂狗 ── 看门狗 ── 卡死就重启 ──↑
```
**三层解耦 + 每层超时 + 队列缓冲 + 看门狗兜底** = 不卡死、可扩展的网关骨架。

---

## 6. 已在 app.py 落地的招式(阶段6 实战)

文档讲完要落到代码。下面对到 [`prototype/rk3506-app/app.py`](../../prototype/rk3506-app/app.py):

| 招 | 落地点 | 实现 |
|---|---|---|
| 招1 处处超时(精化) | `ModbusSource.poll` | 读每设备 `timeout_ms`(缺省回退全局),坏设备探测轮也便宜 |
| 招5 重试 | `ModbusSource.read_holding(…, retries)` | `timeout`/`crc` 错才重试;`exception` 是设备明确拒绝(真应答),不重试 |
| **招2 故障隔离+退避** | `ModbusSource.dev_state` + `poll` | 连续失败 `offline_after` 次→离线;之后按 `backoff_base_s` 几何退避(封顶 `backoff_max_s`)**降频探测,未到期本轮不碰总线**;一次成功即复位回每轮轮询 |
| **招4 看门狗** | `Runtime.mark_alive` + `watchdog_loop` | 采集每轮喂"存活时间戳";`watchdog_loop` 仅采集新鲜才喂 `/dev/watchdog`,停滞 > `stale_limit_s` 停喂(硬件复位)+ 记 critical;off-board 无硬件狗时退化为只软件告警 |
| 可观测 | `/api/health` | 暴露 `collector_age_ms`、`devices_offline`、每设备 `fails`/`next_retry_s` |

配置见 `app_config.json` 的 `reliability` / `watchdog` 块与每设备 `timeout_ms`/`retries`。

**验证(硬件在环精神,Mac+pty 无需真板子)**:`prototype/rk3506-app/tests/reliability_soak.py`
经 `serial_bridge`(pty 对)接 `sim_104`(注入 `offline`/`bad_crc`)与 `app.py --source modbus`,
断言:坏设备判离线、好设备不受影响、**退避使坏设备被探测次数 << 好设备**(实测 10s 内坏 #8 仅 2 次 vs 好 #1 七次)、
故障清除后自动恢复、看门狗停滞告警+恢复。**11/11 通过**。

> 尚未做(板上链路):`deploy/S99gateway` 仍是 `nohup` 无 respawn——进程死了没人拉起。
> 看门狗的"自杀重启"要靠监督者补齐:`systemd Restart=always + WatchdogSec`,或 S99 加 `while true; do …; done` 守护。

---

## 一句话总结
- **不卡死** = 处处超时 + 故障隔离 + 采集/上传解耦 + 看门狗兜底。
- **提性能** = 批量读 + 分级轮询 + 多总线并行 + 提波特率。
- **两条铁律**:任何 I/O 都要能超时;同一条半双工总线内只能串行,并行只能跨总线。

# 云↔网关 MQTT（2 天落地）

RK3506(Linux) 侧的云通信客户端。实现 [MQTT 协议草案](../../docs/protocols/mqtt-protocol-draft.md) 与
[数据接口契约](../../docs/protocols/upstream-platform-data-contract.md) 已定的 topic。

```
云/broker  ──MQTT──  RK3506 (本客户端)  ──UART/firebus──  MCU  ── 现场
```

## 一、准备（5 分钟）

```bash
pip install paho-mqtt
# 本地装 mosquitto 做 broker（Day1 用）
#   macOS:  brew install mosquitto
#   Debian: sudo apt-get install mosquitto mosquitto-clients
cp config.example.json config.json     # 按需改 device_id
```

## 二、Day 1 — 本地打通闭环

**三个终端**：

```bash
# 终端 A：起 broker
mosquitto -v

# 终端 B：订阅所有上行，看网关吐什么（眼见为实）
mosquitto_sub -t 'station/#' -v

# 终端 C：跑网关
python3 gateway_mqtt.py --config config.json -v
```

✅ **Day1 验收**：终端 B 每 30s 看到一帧 `station/stn-001/telemetry`（带 `ts/seq/points{v,q}`）+ 每 60s 一帧 heartbeat。

**测下行设定值**（再开一个终端）：

```bash
mosquitto_pub -t 'station/stn-001/property/set' -m '{
  "command_id":"set-001","command_type":"set_point",
  "payload":{"sec_supply_temp_target":50.0,"valid_until":1717290000000}}'
```

→ 网关收到、过安全校验、回 `command_reply`（终端 B 可见 `status:accepted`）。
把 target 改成 `90` 再发一次 → 应回 `blocked_by_safety`（验证安全边界生效）。

## 三、Day 2 — 上云 + 容错

1. **上云**：`config.json` 把 `broker_host/port` 改成云端，填 `username/password`；用 TLS 就把 `tls:true` + 证书路径。
2. **断网补传自测**（核心验收）：
   ```bash
   # 网关运行中，杀掉 broker 终端 A，等 1~2 分钟，再重启 mosquitto -v
   ```
   ✅ **Day2 验收**：断网期间网关日志显示 `offline, buffered seq=…`；broker 一回来，终端 B 看到一批 `"replay":true` 的补传帧，**`seq` 连续无洞、`ts` 是原始采样时刻**。
3. **常驻**：装成 systemd 服务，掉电自启（见下）。

### systemd（RK3506 上）

```ini
# /etc/systemd/system/gateway-mqtt.service
[Unit]
Description=Heating cloud-gateway MQTT
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /opt/gw/gateway_mqtt.py --config /opt/gw/config.json
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now gateway-mqtt
```

## 四、唯一要你填的地方

`gateway_mqtt.py` 里三个 stub，接真实现场即可：

| 函数 | 干什么 | 接什么 |
|---|---|---|
| `read_points()` | 返回点表快照 `{point_id:{v,q}}` | MCU UART 帧 / 共享内存 / 本地 DB |
| `clock_sync_state()` | 时钟同步状态 | chrony/ntp 状态 |
| `safety_check()` | 设定值安全校验 | `tec_safety` 限值/联锁 |

其余（连接、重连、缓存补传、seq、回传）都已写好。

## 五、常识检查点（AI 最容易在这翻车）

1. 连不上先 `telnet <broker> 1883` / `ping`，再怀疑代码。
2. 别只看"发出去了"——用 `mosquitto_sub` **真订阅看到内容**。
3. **没做断网补传 = 没做完**，现场网络一定会断。
4. 时间戳是**采样时刻**、不是发送时刻（补传尤其）。
5. AI 生成的每段你都要能讲清"为什么"，否则不许合入。

## 待办（Day2 之后）

- [ ] 缓存改文件落盘（当前为内存 deque，进程重启会丢）；按非功能要求定容量
- [ ] `seq` 持久化（重启后不从 0 起）
- [ ] 执行回传补 `success + achieved`（待 `tec_control` 控制环回调）
- [ ] 接入上游优化平台时按 [数据契约](../../docs/protocols/upstream-platform-data-contract.md) 对齐 device_id 拓扑命名

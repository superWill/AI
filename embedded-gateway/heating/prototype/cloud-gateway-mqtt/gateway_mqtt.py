#!/usr/bin/env python3
"""RK3506 云↔网关 MQTT 客户端（Day1/Day2 骨架）。

实现 docs/protocols 里已定的 topic 契约：
  上行  station/{device_id}/telemetry   周期遥测（ts/seq/points{v,q}）
  上行  station/{device_id}/heartbeat   在线心跳
  上行  station/{device_id}/alarm       报警
  上行  station/{device_id}/command_reply  设定值执行回传
  下行  station/{device_id}/property/set    平台/云下发设定值

特性：
  - 配置化 broker（默认本地 mosquitto），用户名密码 + 可选 TLS
  - seq 单调递增；断网时本地缓存遥测，恢复后按 seq 补传（replay:true，保留原始 ts）
  - 下发设定值经本地安全校验 stub，冲突回 blocked_by_safety
  - 数据源 read_points() 是 stub —— 接你们的 UART/firebus 真实采集即可

依赖： pip install paho-mqtt
运行： python3 gateway_mqtt.py --config config.json
"""

from __future__ import annotations

import argparse
import collections
import json
import logging
import signal
import ssl
import sys
import threading
import time

import paho.mqtt.client as mqtt

log = logging.getLogger("gateway")


# --------------------------------------------------------------------------- #
# 数据源 —— 这是唯一需要你填的地方：接真实采集（UART/firebus → 点表）
# --------------------------------------------------------------------------- #
def read_points() -> dict:
    """返回当前点表快照：{point_id: {"v": value, "q": quality}}。

    q 取值（见数据契约 §2.2）：good / stale / bad / est / manual。
    TODO: 替换为从 MCU UART 帧 / 共享内存 / 数据库读取的真实值。
    """
    # —— 假数据，跑通链路用；接真实源后删掉 ——
    return {
        "pri_supply_temp": {"v": 78.4, "q": "good"},
        "pri_return_temp": {"v": 45.1, "q": "good"},
        "pri_flow": {"v": 32.7, "q": "good"},
        "pri_valve_feedback": {"v": 61.0, "q": "good"},
        "sec_supply_temp": {"v": 52.3, "q": "good"},
        "sec_return_temp": {"v": 41.8, "q": "good"},
        "outdoor_temp": {"v": -3.2, "q": "good"},
    }


def clock_sync_state() -> str:
    """时钟同步状态：synced / holdover / unsynced（见契约 §2.1）。
    TODO: 接 chrony/ntp 状态；现在先固定返回。
    """
    return "synced"


# --------------------------------------------------------------------------- #
# 安全校验 stub —— 平台只能给设定值，绝不越过本地安全分层（契约 §8）
# --------------------------------------------------------------------------- #
def safety_check(command_type: str, payload: dict) -> tuple[bool, str]:
    """返回 (allowed, reason)。冲突即拒绝并回 blocked_by_safety。
    TODO: 接 tec_safety 的限值/联锁校验。
    """
    target = payload.get("sec_supply_temp_target")
    if target is not None and not (20.0 <= target <= 75.0):
        return False, f"sec_supply_temp_target {target} out of safe range [20,75]"
    return True, ""


# --------------------------------------------------------------------------- #
# 网关客户端
# --------------------------------------------------------------------------- #
class Gateway:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.device_id = cfg["device_id"]
        self.base = f"station/{self.device_id}"
        self.seq = 0
        self.seq_lock = threading.Lock()
        # 断网缓存：环形缓冲，满了丢最旧（容量见配置）
        self.buffer = collections.deque(maxlen=cfg.get("buffer_max", 5000))
        self.stop = threading.Event()

        api = getattr(mqtt, "CallbackAPIVersion", None)
        if api:  # paho-mqtt 2.x
            self.client = mqtt.Client(api.VERSION2, client_id=cfg["client_id"])
        else:    # paho-mqtt 1.x
            self.client = mqtt.Client(client_id=cfg["client_id"])

        if cfg.get("username"):
            self.client.username_pw_set(cfg["username"], cfg.get("password", ""))
        if cfg.get("tls", False):
            self.client.tls_set(
                ca_certs=cfg.get("ca_certs"),
                certfile=cfg.get("certfile"),
                keyfile=cfg.get("keyfile"),
                cert_reqs=ssl.CERT_REQUIRED,
            )

        # 自动重连：1s 起，指数退避到 30s
        self.client.reconnect_delay_set(min_delay=1, max_delay=30)
        # 遗嘱：网关掉线时 broker 替它发离线心跳
        self.client.will_set(f"{self.base}/heartbeat",
                             json.dumps({"device_id": self.device_id, "online": False}),
                             qos=1, retain=False)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _next_seq(self) -> int:
        with self.seq_lock:
            self.seq += 1
            return self.seq

    # -- 回调 (兼容 paho 1.x / 2.x：rc 始终是 userdata 后第二个位置参数) -------- #
    def _on_connect(self, client, userdata, *args, **kwargs):
        rc = args[1] if len(args) > 1 else 0
        if rc == 0:
            log.info("connected to broker, subscribing %s/property/set", self.base)
            client.subscribe(f"{self.base}/property/set", qos=1)
        else:
            log.warning("connect failed rc=%s", rc)

    def _on_message(self, client, userdata, msg):
        log.info("downlink %s: %s", msg.topic, msg.payload[:200])
        try:
            cmd = json.loads(msg.payload)
        except Exception as exc:
            log.error("bad command json: %s", exc)
            return
        self._handle_setpoint(cmd)

    # -- 下发设定值处理 + 回传 ------------------------------------------------ #
    def _handle_setpoint(self, cmd: dict):
        command_id = cmd.get("command_id", "")
        ctype = cmd.get("command_type", "set_point")
        payload = cmd.get("payload", {})

        allowed, reason = safety_check(ctype, payload)
        if not allowed:
            self._reply(command_id, "blocked_by_safety", {}, reason)
            log.warning("setpoint blocked: %s", reason)
            return

        # TODO: 把目标值交给本地气候补偿+PID（tec_control）执行；这里先回 accepted
        self._reply(command_id, "accepted", {}, "")
        log.info("setpoint accepted: %s", payload)
        # 执行后应再回 success + achieved（实际达到值），由控制环回调触发。

    def _reply(self, command_id: str, status: str, achieved: dict, reason: str):
        frame = {
            "command_id": command_id,
            "ts": int(time.time() * 1000),
            "status": status,
            "achieved": achieved,
            "reason": reason,
        }
        self.client.publish(f"{self.base}/command_reply", json.dumps(frame), qos=1)

    # -- 上行 ----------------------------------------------------------------- #
    def _build_telemetry(self, replay: bool = False, ts: int | None = None) -> dict:
        return {
            "device_id": self.device_id,
            "ts": ts if ts is not None else int(time.time() * 1000),
            "clock_sync": clock_sync_state(),
            "seq": self._next_seq(),
            "points": read_points(),
            **({"replay": True} if replay else {}),
        }

    def _publish_telemetry(self):
        frame = self._build_telemetry()
        if self.client.is_connected():
            self._flush_buffer()
            self.client.publish(f"{self.base}/telemetry", json.dumps(frame), qos=1)
        else:
            self.buffer.append(frame)   # 断网：缓存原始采样帧（保留原始 ts）
            log.debug("offline, buffered seq=%s (buffer=%d)", frame["seq"], len(self.buffer))

    def _flush_buffer(self):
        """重连后按 seq 顺序补传，标 replay:true、保留原始 ts。"""
        while self.buffer and self.client.is_connected():
            frame = self.buffer.popleft()
            frame["replay"] = True
            self.client.publish(f"{self.base}/telemetry", json.dumps(frame), qos=1)
        if not self.buffer:
            log.info("backfill complete")

    def _publish_heartbeat(self):
        if self.client.is_connected():
            hb = {"device_id": self.device_id, "online": True,
                  "ts": int(time.time() * 1000), "buffer": len(self.buffer)}
            self.client.publish(f"{self.base}/heartbeat", json.dumps(hb), qos=0)

    def publish_alarm(self, alarm_id: str, message: str):
        frame = {"device_id": self.device_id, "ts": int(time.time() * 1000),
                 "alarm_id": alarm_id, "message": message}
        self.client.publish(f"{self.base}/alarm", json.dumps(frame), qos=1)

    # -- 主循环 --------------------------------------------------------------- #
    def run(self):
        host = self.cfg["broker_host"]
        port = self.cfg.get("broker_port", 1883)
        log.info("connecting %s:%s as %s", host, port, self.device_id)
        self.client.connect_async(host, port, keepalive=self.cfg.get("keepalive", 30))
        self.client.loop_start()

        t_tele = self.cfg.get("telemetry_interval", 30)
        t_hb = self.cfg.get("heartbeat_interval", 60)
        next_tele = next_hb = time.monotonic()

        while not self.stop.is_set():
            now = time.monotonic()
            if now >= next_tele:
                self._publish_telemetry()
                next_tele = now + t_tele
            if now >= next_hb:
                self._publish_heartbeat()
                next_hb = now + t_hb
            time.sleep(0.2)

        self.client.loop_stop()
        self.client.disconnect()
        log.info("stopped, %d frames left in buffer", len(self.buffer))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    with open(args.config) as fh:
        cfg = json.load(fh)

    gw = Gateway(cfg)
    signal.signal(signal.SIGINT, lambda *_: gw.stop.set())
    signal.signal(signal.SIGTERM, lambda *_: gw.stop.set())
    gw.run()


if __name__ == "__main__":
    sys.exit(main())

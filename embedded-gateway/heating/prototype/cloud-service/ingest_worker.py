#!/usr/bin/env python3
"""云端 ingest worker：订阅 mosquitto 的 station/# 上行，落库 PostgreSQL。

消费 docs/protocols/upstream-platform-data-contract.md 的 MQTT 契约：
  telemetry      → 展开 points 写 telemetry 窄表（补传帧靠唯一键幂等）
  heartbeat      → 更新 station.online + 写 heartbeat
  alarm          → 写 alarm
  command_reply  → 仅日志（执行回传，测试期不入库）

设计：
  - paho loop_forever() 自带断线重连；DB 断了则丢弃当前帧并记日志，下帧重试。
  - 单连接、单线程消费，足够测试机吞吐；批量 execute_values 减少往返。

依赖： pip install paho-mqtt psycopg2-binary
运行： python3 ingest_worker.py --config config.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import psycopg2
from psycopg2.extras import execute_values

log = logging.getLogger("ingest")


def ts_from_ms(ms) -> datetime:
    """Unix 毫秒 → 带时区 datetime（UTC）。坏值回退到当前时刻。"""
    try:
        return datetime.fromtimestamp(int(ms) / 1000.0, tz=timezone.utc)
    except (TypeError, ValueError):
        return datetime.now(timezone.utc)


def as_float(v):
    """点值尽量转 float；非数值（bool/字符串/None）存 NULL，质量码仍保留。"""
    try:
        if isinstance(v, bool):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None


class Ingestor:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.conn = None

    # ---- DB ----------------------------------------------------------------
    def db(self):
        """惰性连接 + 断线自愈。"""
        if self.conn is not None and self.conn.closed == 0:
            return self.conn
        self.conn = psycopg2.connect(self.cfg["dsn"])
        self.conn.autocommit = True
        log.info("PostgreSQL connected")
        return self.conn

    # ---- handlers ----------------------------------------------------------
    def on_telemetry(self, dev: str, p: dict):
        ts = ts_from_ms(p.get("ts"))
        seq = p.get("seq")
        replay = bool(p.get("replay"))
        clock_sync = p.get("clock_sync")
        points = p.get("points", {})
        if seq is None or not points:
            return

        rows = [
            (dev, ts, seq, metric, as_float(pv.get("v")),
             pv.get("q", "good"), replay, clock_sync)
            for metric, pv in points.items()
        ]
        with self.db().cursor() as cur:
            execute_values(
                cur,
                "INSERT INTO telemetry "
                "(device_id, ts, seq, metric, value, quality, replay, clock_sync) "
                "VALUES %s ON CONFLICT (device_id, seq, metric) DO NOTHING",
                rows,
            )
            # 补传帧不刷新 last_seq（避免 seq 倒退判定混乱）
            cur.execute(
                "INSERT INTO station (device_id, last_seen, last_seq, online) "
                "VALUES (%s, now(), %s, true) "
                "ON CONFLICT (device_id) DO UPDATE SET "
                "  last_seen = now(), online = true, "
                "  last_seq  = GREATEST(COALESCE(station.last_seq, 0), excluded.last_seq)",
                (dev, seq if not replay else 0),
            )
        tag = "replay" if replay else "live"
        log.debug("telemetry %s seq=%s pts=%d (%s)", dev, seq, len(rows), tag)

    def on_heartbeat(self, dev: str, p: dict):
        ts = ts_from_ms(p.get("ts"))
        online = bool(p.get("online", True))
        buffer = p.get("buffer")
        with self.db().cursor() as cur:
            cur.execute(
                "INSERT INTO heartbeat (device_id, ts, online, buffer) "
                "VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
                (dev, ts, online, buffer),
            )
            cur.execute(
                "INSERT INTO station (device_id, last_seen, online) "
                "VALUES (%s, now(), %s) "
                "ON CONFLICT (device_id) DO UPDATE SET last_seen = now(), online = %s",
                (dev, online, online),
            )

    def on_alarm(self, dev: str, p: dict):
        ts = ts_from_ms(p.get("ts"))
        with self.db().cursor() as cur:
            cur.execute(
                "INSERT INTO alarm (device_id, ts, alarm_id, message) "
                "VALUES (%s, %s, %s, %s)",
                (dev, ts, p.get("alarm_id"), p.get("message")),
            )
        log.info("ALARM %s %s: %s", dev, p.get("alarm_id"), p.get("message"))

    def on_reply(self, dev: str, p: dict):
        log.info("command_reply %s cmd=%s status=%s",
                 dev, p.get("command_id"), p.get("status"))

    def on_event(self, dev: str, p: dict):
        """station/{id}/event 状态突变 → device_event（设备状态源头之一）。"""
        ts = ts_from_ms(p.get("ts"))
        with self.db().cursor() as cur:
            cur.execute(
                "INSERT INTO device_event (device_id, ts, equip, from_state, to_state, source) "
                "VALUES (%s, %s, %s, %s, %s, 'event') ON CONFLICT DO NOTHING",
                (dev, ts, p.get("equip"), p.get("from_state"), p.get("to_state")),
            )
        log.debug("event %s %s %s->%s", dev, p.get("equip"),
                  p.get("from_state"), p.get("to_state"))

    HANDLERS = {
        "telemetry": on_telemetry,
        "heartbeat": on_heartbeat,
        "alarm": on_alarm,
        "command_reply": on_reply,
        "event": on_event,
    }

    # ---- MQTT callbacks ----------------------------------------------------
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("station/#", qos=1)
            log.info("MQTT connected, subscribed station/#")
        else:
            log.error("MQTT connect failed rc=%s", rc)

    def on_message(self, client, userdata, msg):
        parts = msg.topic.split("/")            # station/{dev}/{type}
        if len(parts) < 3:
            return
        dev, mtype = parts[1], parts[2]
        handler = self.HANDLERS.get(mtype)
        if handler is None:
            return
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            handler(self, dev, data)
        except json.JSONDecodeError:
            log.warning("bad json on %s", msg.topic)
        except psycopg2.Error as e:
            log.error("db error on %s: %s", msg.topic, e)
            if self.conn is not None:
                try:
                    self.conn.close()
                except Exception:
                    pass
                self.conn = None                # 下帧重连


def offline_sweep(cfg: dict):
    """后台线程：把 last_seen 超过 3×上送周期 的站标记离线（无元数据按 30s）。
    用独立连接（psycopg2 连接非线程安全，不与消息处理共用）。"""
    while True:
        time.sleep(30)
        try:
            con = psycopg2.connect(cfg["dsn"])
            con.autocommit = True
            with con.cursor() as cur:
                cur.execute(
                    "UPDATE station SET online = false "
                    "WHERE online AND last_seen < now() - "
                    "(COALESCE((SELECT report_interval_s FROM station_meta "
                    "          WHERE device_id = station.device_id), 30) * 3) "
                    "* interval '1 second'")
            con.close()
        except psycopg2.Error as e:
            log.warning("offline sweep: %s", e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.json")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    with open(args.config) as f:
        cfg = json.load(f)

    ing = Ingestor(cfg)
    client = mqtt.Client(client_id=cfg.get("client_id", "cloud-ingest"))
    if cfg.get("username"):
        client.username_pw_set(cfg["username"], cfg.get("password", ""))
    if cfg.get("tls"):
        client.tls_set(ca_certs=cfg.get("ca_certs"))
    client.on_connect = ing.on_connect
    client.on_message = ing.on_message
    client.connect(cfg.get("broker_host", "127.0.0.1"),
                   cfg.get("broker_port", 1883),
                   cfg.get("keepalive", 60))
    threading.Thread(target=offline_sweep, args=(cfg,), daemon=True).start()
    log.info("ingest worker up (+offline sweep)")
    client.loop_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)

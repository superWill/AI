-- 云端测试机 · PostgreSQL 库结构
-- 消费 docs/protocols/upstream-platform-data-contract.md 定义的 MQTT 上行契约。
-- 设计取向：窄表(long format)，每帧每点一行，Grafana 直接画；补传帧靠唯一键幂等。

-- ---------------------------------------------------------------------------
-- 站点注册表：device_id 唯一标识一个站/网关，平台据此拼拓扑
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS station (
    device_id   text PRIMARY KEY,
    name        text,
    first_seen  timestamptz NOT NULL DEFAULT now(),
    last_seen   timestamptz,
    last_seq    bigint,
    online      boolean      NOT NULL DEFAULT false
);

-- ---------------------------------------------------------------------------
-- 遥测窄表：一帧 telemetry 的每个 point 落一行
--   ts        采样时刻（来自帧里的 Unix ms，非入库时刻）
--   quality   good/stale/bad/est/manual（契约 §2.2）
--   replay    补传帧标志（断网恢复后回灌）
-- 唯一键 (device_id, seq, metric) 保证补传幂等：同 seq 同点重复插入直接忽略。
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS telemetry (
    device_id   text             NOT NULL,
    ts          timestamptz      NOT NULL,
    seq         bigint           NOT NULL,
    metric      text             NOT NULL,
    value       double precision,
    quality     text             NOT NULL,
    replay      boolean          NOT NULL DEFAULT false,
    clock_sync  text,
    ingested_at timestamptz      NOT NULL DEFAULT now(),
    CONSTRAINT telemetry_uq UNIQUE (device_id, seq, metric)
);

-- Grafana 主查询路径：某站某点按时间取序列
CREATE INDEX IF NOT EXISTS telemetry_dev_metric_ts
    ON telemetry (device_id, metric, ts DESC);
-- 留存清理路径
CREATE INDEX IF NOT EXISTS telemetry_ts
    ON telemetry (ts);

-- ---------------------------------------------------------------------------
-- 小时聚合表：报表/长留用。原始表只留近 N 天，聚合表长期保留（体积小）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS telemetry_hourly (
    device_id text         NOT NULL,
    hour      timestamptz  NOT NULL,
    metric    text         NOT NULL,
    avg_value double precision,
    min_value double precision,
    max_value double precision,
    n         integer,
    PRIMARY KEY (device_id, hour, metric)
);

-- ---------------------------------------------------------------------------
-- 报警表（station/{id}/alarm）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alarm (
    id          bigserial PRIMARY KEY,
    device_id   text         NOT NULL,
    ts          timestamptz  NOT NULL,
    alarm_id    text,
    message     text,
    ingested_at timestamptz  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS alarm_dev_ts ON alarm (device_id, ts DESC);

-- ---------------------------------------------------------------------------
-- 心跳表（station/{id}/heartbeat）：在线状态 + 断网缓冲深度
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS heartbeat (
    device_id text        NOT NULL,
    ts        timestamptz NOT NULL,
    online    boolean,
    buffer    integer,
    PRIMARY KEY (device_id, ts)
);

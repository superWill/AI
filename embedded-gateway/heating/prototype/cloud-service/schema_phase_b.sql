-- 阶段 B · 报表口径层（在 schema.sql 基础上新增）
-- 对应 docs/product/heating-cloud-admin-spec.md §3.1/3.2/3.3/3.4/3.5/3.6
-- 幂等：可重复执行。

-- ---------------------------------------------------------------------------
-- 3.1 站点元数据（报表前置：面积/设计参数/上送周期/改造日期）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS station_meta (
    device_id              text PRIMARY KEY,
    heat_area_m2           double precision,          -- 供热面积（硬必填）
    building_count         integer,
    household_count        integer,
    design_pri_supply_temp double precision,
    design_pri_return_temp double precision,
    design_sec_supply_temp double precision,
    design_sec_return_temp double precision,
    design_load_kw         double precision,
    report_interval_s      integer NOT NULL DEFAULT 30, -- 应收帧基准
    retrofit_date          date,                       -- 节能"改造前后"基线，可空
    commissioned_date      date,
    updated_at             timestamptz NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- 3.2 指标字典：区分瞬时/累计 + 单位与中文名
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metric_def (
    metric   text PRIMARY KEY,
    kind     text NOT NULL DEFAULT 'instant',   -- instant | accumulator
    unit     text,
    label_cn text
);

INSERT INTO metric_def (metric, kind, unit, label_cn) VALUES
  ('pri_supply_temp',   'instant',     'degC', '一次供水温度'),
  ('pri_return_temp',   'instant',     'degC', '一次回水温度'),
  ('pri_flow',          'instant',     'm3/h', '一次流量'),
  ('pri_valve_feedback','instant',     '%',    '一次阀位反馈'),
  ('sec_supply_temp',   'instant',     'degC', '二次供水温度'),
  ('sec_return_temp',   'instant',     'degC', '二次回水温度'),
  ('sec_flow',          'instant',     'm3/h', '二次流量'),
  ('circ_pump_freq_fb', 'instant',     'Hz',   '循环泵频率'),
  ('refill_pressure',   'instant',     'MPa',  '补水压力'),
  ('outdoor_temp',      'instant',     'degC', '室外温度'),
  ('heat_total',        'accumulator', 'GJ',   '站级累计供热量'),
  ('refill_total',      'accumulator', 'm3',   '累计补水量')
ON CONFLICT (metric) DO UPDATE
SET kind = excluded.kind, unit = excluded.unit, label_cn = excluded.label_cn;

-- ---------------------------------------------------------------------------
-- 3.3 累计量日结（cron 生成）：当日首末值差分
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meter_daily (
    device_id text        NOT NULL,
    day       date        NOT NULL,
    metric    text        NOT NULL,
    first_val double precision,
    last_val  double precision,
    delta     double precision,        -- last - first；<0 视为换表/回零
    rollover  boolean NOT NULL DEFAULT false,
    PRIMARY KEY (device_id, day, metric)
);

-- ---------------------------------------------------------------------------
-- 3.4 天气日表（cron 生成）：室外温日均 + 度日数 HDD（基准 18℃）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_daily (
    device_id   text NOT NULL,
    day         date NOT NULL,
    outdoor_avg double precision,
    hdd         double precision,       -- max(0, 18 - outdoor_avg)
    PRIMARY KEY (device_id, day)
);

-- ---------------------------------------------------------------------------
-- 3.6 设备状态事件（ingest 从 station/{id}/event 写 + 报表派生兜底）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS device_event (
    id         bigserial PRIMARY KEY,
    device_id  text        NOT NULL,
    ts         timestamptz NOT NULL,
    equip      text,                    -- circ_pump / refill_pump / valve / gateway
    from_state text,
    to_state   text,
    source     text,                    -- event | derived
    CONSTRAINT device_event_uq UNIQUE (device_id, ts, equip, to_state)
);
CREATE INDEX IF NOT EXISTS device_event_dev_ts ON device_event (device_id, ts DESC);

-- 设备状态日聚合（cron 生成）：运行时长/启停/故障
CREATE TABLE IF NOT EXISTS device_status_daily (
    device_id    text NOT NULL,
    day          date NOT NULL,
    equip        text NOT NULL,
    run_minutes  double precision,
    start_count  integer,
    fault_count  integer,
    PRIMARY KEY (device_id, day, equip)
);

-- ---------------------------------------------------------------------------
-- 3.5 报警生命周期扩展（在 alarm 表加列，幂等）
-- ---------------------------------------------------------------------------
ALTER TABLE alarm ADD COLUMN IF NOT EXISTS status     text NOT NULL DEFAULT 'active';
ALTER TABLE alarm ADD COLUMN IF NOT EXISTS acked_at   timestamptz;
ALTER TABLE alarm ADD COLUMN IF NOT EXISTS acked_by   text;
ALTER TABLE alarm ADD COLUMN IF NOT EXISTS cleared_at timestamptz;
ALTER TABLE alarm ADD COLUMN IF NOT EXISTS cleared_ts timestamptz;   -- 现场解除时刻（算处理时长用）

-- ---------------------------------------------------------------------------
-- 站点元数据种子（模拟站 stn-001..008，验证报表口径用；真实部署在后管维护）
--   面积 5万起阶梯；stn-003/006 设改造日期，用于"改造前后"对比验证
-- ---------------------------------------------------------------------------
INSERT INTO station_meta
  (device_id, heat_area_m2, building_count, household_count,
   design_pri_supply_temp, design_pri_return_temp,
   design_sec_supply_temp, design_sec_return_temp,
   design_load_kw, report_interval_s, retrofit_date, commissioned_date)
SELECT
  'stn-' || lpad(g::text, 3, '0'),
  50000 + g*5000, 10 + g, 800 + g*60,
  85, 55, 50, 40,
  3000 + g*200, 5,
  CASE WHEN g IN (3,6) THEN DATE '2026-01-15' ELSE NULL END,
  DATE '2025-10-01'
FROM generate_series(1, 8) g
ON CONFLICT (device_id) DO NOTHING;

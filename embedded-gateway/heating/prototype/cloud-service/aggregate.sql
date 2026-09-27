-- 阶段 B · 聚合作业：原始遥测 → 报表口径层
-- 由 cron 每小时/每日跑（也可手动跑做验证）。全部幂等（ON CONFLICT 刷新）。
-- 口径见 docs/product/heating-cloud-admin-spec.md §4。

-- ===========================================================================
-- 1) meter_daily —— 累计量当日首末差分（热量/补水）。绝不求和。
--    delta<0 视为换表/回零，置 rollover。覆盖最近 2 天补迟到数据。
-- ===========================================================================
INSERT INTO meter_daily (device_id, day, metric, first_val, last_val, delta, rollover)
SELECT device_id, day, metric, first_val, last_val,
       last_val - first_val AS delta,
       (last_val - first_val) < 0 AS rollover
FROM (
    SELECT DISTINCT
        t.device_id,
        (t.ts AT TIME ZONE 'Asia/Shanghai')::date AS day,
        t.metric,
        first_value(t.value) OVER w AS first_val,
        last_value(t.value)  OVER w AS last_val
    FROM telemetry t
    JOIN metric_def m ON m.metric = t.metric AND m.kind = 'accumulator'
    WHERE t.quality = 'good' AND t.value IS NOT NULL
      AND t.ts >= now() - interval '2 days'
    WINDOW w AS (
        PARTITION BY t.device_id, (t.ts AT TIME ZONE 'Asia/Shanghai')::date, t.metric
        ORDER BY t.ts
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
) s
ON CONFLICT (device_id, day, metric) DO UPDATE
SET first_val = excluded.first_val, last_val = excluded.last_val,
    delta = excluded.delta, rollover = excluded.rollover;

-- ===========================================================================
-- 2) weather_daily —— 室外温日均 + 度日数 HDD（基准 18℃）
-- ===========================================================================
INSERT INTO weather_daily (device_id, day, outdoor_avg, hdd)
SELECT device_id,
       (ts AT TIME ZONE 'Asia/Shanghai')::date AS day,
       avg(value) AS outdoor_avg,
       greatest(0, 18 - avg(value)) AS hdd
FROM telemetry
WHERE metric = 'outdoor_temp' AND quality = 'good' AND value IS NOT NULL
  AND ts >= now() - interval '2 days'
GROUP BY device_id, (ts AT TIME ZONE 'Asia/Shanghai')::date
ON CONFLICT (device_id, day) DO UPDATE
SET outdoor_avg = excluded.outdoor_avg, hdd = excluded.hdd;

-- ===========================================================================
-- 3) device_status_daily —— 循环泵运行时长/启停 + 故障数
--    运行判据：circ_pump_freq_fb > 5Hz（§9 默认，可调）。
--    run_minutes ≈ 运行采样数 × 上送周期；start_count = 停→运行 跃迁数。
--    fault_count 取自当日该站报警条数。
-- ===========================================================================
INSERT INTO device_status_daily (device_id, day, equip, run_minutes, start_count, fault_count)
SELECT
    s.device_id, s.day, 'circ_pump' AS equip,
    count(*) FILTER (WHERE s.running) * COALESCE(sm.report_interval_s, 30) / 60.0 AS run_minutes,
    count(*) FILTER (WHERE s.running AND NOT COALESCE(s.prev_running, s.running)) AS start_count,
    COALESCE(a.fault_count, 0) AS fault_count
FROM (
    SELECT device_id,
           (ts AT TIME ZONE 'Asia/Shanghai')::date AS day,
           value > 5 AS running,
           lag(value > 5) OVER (PARTITION BY device_id ORDER BY ts) AS prev_running
    FROM telemetry
    WHERE metric = 'circ_pump_freq_fb' AND quality = 'good' AND value IS NOT NULL
      AND ts >= now() - interval '2 days'
) s
LEFT JOIN station_meta sm ON sm.device_id = s.device_id
LEFT JOIN (
    SELECT device_id, (ts AT TIME ZONE 'Asia/Shanghai')::date AS day, count(*) AS fault_count
    FROM alarm WHERE ts >= now() - interval '2 days'
    GROUP BY device_id, (ts AT TIME ZONE 'Asia/Shanghai')::date
) a ON a.device_id = s.device_id AND a.day = s.day
GROUP BY s.device_id, s.day, sm.report_interval_s, a.fault_count
ON CONFLICT (device_id, day, equip) DO UPDATE
SET run_minutes = excluded.run_minutes,
    start_count = excluded.start_count,
    fault_count = excluded.fault_count;

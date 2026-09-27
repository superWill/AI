-- 报表④：报警与数据质量统计（spec §4.4）
-- 用法： psql ... -v from='2026-06-22 00:00+08' -v to='2026-06-23 00:00+08' -f reports/report_data_quality.sql
\echo ==== 数据完整率（实收帧/应收帧；应收=时长/上送周期）====
WITH frames AS (
    SELECT device_id, count(DISTINCT seq) AS got, min(ts) AS t0, max(ts) AS t1
    FROM telemetry
    WHERE ts BETWEEN :'from' AND :'to' AND NOT replay
    GROUP BY device_id
)
SELECT f.device_id AS 站点, f.got AS 实收帧,
       round((extract(epoch FROM (f.t1 - f.t0)) / sm.report_interval_s + 1)::numeric, 0) AS 应收帧,
       round((100.0 * f.got
              / NULLIF(extract(epoch FROM (f.t1 - f.t0)) / sm.report_interval_s + 1, 0))::numeric, 1) AS 完整率pct
FROM frames f JOIN station_meta sm ON sm.device_id = f.device_id
ORDER BY f.device_id;

\echo ==== 坏点率（非 good 占比）====
SELECT device_id AS 站点,
       count(*) AS 总点数,
       round((100.0 * count(*) FILTER (WHERE quality <> 'good') / count(*))::numeric, 2) AS 坏点率pct
FROM telemetry
WHERE ts BETWEEN :'from' AND :'to'
GROUP BY device_id ORDER BY device_id;

\echo ==== 在线状态（当前）====
SELECT device_id AS 站点, online AS 在线, last_seen AS 最后心跳
FROM station ORDER BY device_id;

\echo ==== 报警统计（次数 / 已解除 / 平均处理分钟）====
SELECT device_id AS 站点,
       count(*) AS 报警数,
       count(*) FILTER (WHERE status = 'cleared') AS 已解除,
       round(avg(extract(epoch FROM (cleared_ts - ts)) / 60)
             FILTER (WHERE cleared_ts IS NOT NULL)::numeric, 1) AS 平均处理分钟
FROM alarm
WHERE ts BETWEEN :'from' AND :'to'
GROUP BY device_id ORDER BY device_id;

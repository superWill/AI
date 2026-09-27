-- 云端测试机 · 定时维护：小时聚合 + 原始数据留存清理
-- 由 cron 每小时跑一次（见 deploy/cloud-maintenance.cron）。
-- 幂等：重复跑同一小时只会刷新聚合值，不会重复累计。

-- 1) 小时聚合：把最近 2 小时的 good 质量原始点滚成 telemetry_hourly
--    （覆盖 2 小时是为了补上跨小时边界 / 补传迟到的数据）
INSERT INTO telemetry_hourly (device_id, hour, metric, avg_value, min_value, max_value, n)
SELECT device_id,
       date_trunc('hour', ts) AS hour,
       metric,
       avg(value),
       min(value),
       max(value),
       count(*)
FROM   telemetry
WHERE  quality = 'good'
  AND  value IS NOT NULL
  AND  ts >= date_trunc('hour', now()) - interval '2 hours'
GROUP  BY device_id, date_trunc('hour', ts), metric
ON CONFLICT (device_id, hour, metric) DO UPDATE
SET avg_value = excluded.avg_value,
    min_value = excluded.min_value,
    max_value = excluded.max_value,
    n         = excluded.n;

-- 2) 留存清理：测试机磁盘小，原始遥测只留 30 天，心跳只留 7 天。
--    聚合表 telemetry_hourly 不删（体积小、报表要用）。
--    改留存周期就改这里的 interval。
DELETE FROM telemetry WHERE ts < now() - interval '30 days';
DELETE FROM heartbeat WHERE ts < now() - interval '7 days';
DELETE FROM alarm     WHERE ts < now() - interval '90 days';

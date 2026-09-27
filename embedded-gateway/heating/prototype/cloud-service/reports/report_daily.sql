-- 报表①：运行工况 + 设备状态日报（spec §4.1）
-- 用法： psql ... -v station=stn-001 -v day=2026-06-22 -f reports/report_daily.sql
\echo ==== 工况字段（当日 均/极值，仅 good，含设计偏离）====
SELECT m.label_cn AS 指标, m.unit AS 单位,
       round(avg(t.value)::numeric, 2) AS 均值,
       round(min(t.value)::numeric, 2) AS 最小,
       round(max(t.value)::numeric, 2) AS 最大,
       count(*)                        AS 样本数
FROM telemetry t
JOIN metric_def m ON m.metric = t.metric AND m.kind = 'instant'
WHERE t.device_id = :'station' AND t.quality = 'good'
  AND (t.ts AT TIME ZONE 'Asia/Shanghai')::date = :'day'
GROUP BY m.metric, m.label_cn, m.unit
ORDER BY m.metric;

\echo ==== 一/二次温差 Δt（计算列）====
SELECT round((avg(value) FILTER (WHERE metric='pri_supply_temp')
            - avg(value) FILTER (WHERE metric='pri_return_temp'))::numeric,2) AS 一次Δt,
       round((avg(value) FILTER (WHERE metric='sec_supply_temp')
            - avg(value) FILTER (WHERE metric='sec_return_temp'))::numeric,2) AS 二次Δt
FROM telemetry
WHERE device_id = :'station' AND quality='good'
  AND (ts AT TIME ZONE 'Asia/Shanghai')::date = :'day';

\echo ==== 设备状态（循环泵：运行/启停/故障）====
SELECT equip AS 设备,
       round(run_minutes::numeric,1) AS 运行分钟,
       start_count AS 启停次数,
       fault_count AS 故障数
FROM device_status_daily
WHERE device_id = :'station' AND day = :'day';

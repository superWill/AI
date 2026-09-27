-- 报表②：热量/能耗结算（spec §4.2）
-- 累计量用 meter_daily 的 delta 求和（差分口径），排除换表(rollover)日。
-- 用法： psql ... -v station=stn-001 -v ym=2026-06 -f reports/report_settlement.sql
\echo ==== 期间供热量 / 补水量 / 单位面积耗热 ====
SELECT md.device_id AS 站点,
       round(sum(md.delta) FILTER (WHERE md.metric='heat_total')::numeric, 3)   AS 供热量_GJ,
       round(sum(md.delta) FILTER (WHERE md.metric='refill_total')::numeric, 2) AS 补水量_m3,
       sm.heat_area_m2 AS 面积_m2,
       CASE WHEN sm.heat_area_m2 > 0
            THEN round((sum(md.delta) FILTER (WHERE md.metric='heat_total')
                        / sm.heat_area_m2 * 1000)::numeric, 3)
       END AS 单位面积耗热_MJ每m2
FROM meter_daily md
JOIN station_meta sm ON sm.device_id = md.device_id
WHERE md.device_id = :'station'
  AND to_char(md.day, 'YYYY-MM') = :'ym'
  AND NOT md.rollover
GROUP BY md.device_id, sm.heat_area_m2;

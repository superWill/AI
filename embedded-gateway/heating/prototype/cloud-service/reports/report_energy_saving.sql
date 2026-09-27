-- 报表③：节能效果对比（spec §4.3）
-- 归一化耗热 = 期间供热量GJ / (面积 × ΣHDD)，消除冷暖年差异。
-- 单期计算；对比"改造前后/同比"= 取两个时间段各跑一次再比。
-- 用法： psql ... -v station=stn-001 -v from=2026-06-01 -v to=2026-06-30 -f reports/report_energy_saving.sql
WITH heat AS (
    SELECT device_id, day, sum(delta) AS heat_gj
    FROM meter_daily
    WHERE metric = 'heat_total' AND NOT rollover
    GROUP BY device_id, day
)
SELECT h.device_id AS 站点,
       round(sum(h.heat_gj)::numeric, 3) AS 供热量_GJ,
       round(sum(w.hdd)::numeric, 2)     AS 累计HDD,
       sm.heat_area_m2                   AS 面积_m2,
       sm.retrofit_date                  AS 改造日期,
       round((sum(h.heat_gj) / (sm.heat_area_m2 * NULLIF(sum(w.hdd), 0)) * 1e6)::numeric, 4)
            AS 归一化耗热_kJ每m2每HDD
FROM heat h
JOIN weather_daily w  ON w.device_id = h.device_id AND w.day = h.day
JOIN station_meta  sm ON sm.device_id = h.device_id
WHERE h.device_id = :'station'
  AND h.day BETWEEN :'from'::date AND :'to'::date
GROUP BY h.device_id, sm.heat_area_m2, sm.retrofit_date;

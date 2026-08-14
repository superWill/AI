-- Reproduce the report's 2030 NVIDIA revenue and valuation scenarios.
WITH scenarios(
  scenario, core_ai_dc_b, physical_ai_training_b, physical_ai_edge_b,
  gaming_other_b, net_margin, pe
) AS (
  VALUES
    ('悲观', 340.0, 25.0, 8.0, 47.0, 0.43, 22.0),
    ('基准', 500.0, 55.0, 25.0, 70.0, 0.48, 28.0),
    ('乐观', 690.0, 100.0, 70.0, 90.0, 0.51, 32.0)
), calculated AS (
  SELECT *,
    core_ai_dc_b + physical_ai_training_b + physical_ai_edge_b + gaming_other_b AS revenue_b,
    physical_ai_training_b + physical_ai_edge_b AS physical_ai_b
  FROM scenarios
)
SELECT
  scenario,
  revenue_b,
  physical_ai_b,
  physical_ai_b / revenue_b AS physical_ai_share,
  revenue_b * net_margin AS net_income_b,
  revenue_b * net_margin * pe / 1000.0 AS market_cap_t,
  revenue_b * net_margin * pe / 24.3 AS price_per_share
FROM calculated;

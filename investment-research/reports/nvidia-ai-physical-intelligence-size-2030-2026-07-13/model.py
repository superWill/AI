"""Reproduce the 2030 NVIDIA scenario sizing used in the companion report."""

from __future__ import annotations

from dataclasses import dataclass


CURRENT_REVENUE_RUN_RATE_B = 91.0 * 4
CURRENT_MARKET_CAP_T = 5.109
YEARS_TO_2030 = 4.5
SHARES_B = 24.3


@dataclass(frozen=True)
class Scenario:
    name: str
    core_ai_dc_b: float
    physical_ai_training_b: float
    physical_ai_edge_b: float
    gaming_other_b: float
    net_margin: float
    pe: float


SCENARIOS = (
    Scenario("悲观", 340, 25, 8, 47, 0.43, 22),
    Scenario("基准", 500, 55, 25, 70, 0.48, 28),
    Scenario("乐观", 690, 100, 70, 90, 0.51, 32),
)


def calculate(scenario: Scenario) -> dict[str, float | str]:
    revenue_b = (
        scenario.core_ai_dc_b
        + scenario.physical_ai_training_b
        + scenario.physical_ai_edge_b
        + scenario.gaming_other_b
    )
    physical_ai_b = scenario.physical_ai_training_b + scenario.physical_ai_edge_b
    net_income_b = revenue_b * scenario.net_margin
    market_cap_t = net_income_b * scenario.pe / 1_000
    return {
        "scenario": scenario.name,
        "revenue_b": revenue_b,
        "physical_ai_b": physical_ai_b,
        "physical_ai_share": physical_ai_b / revenue_b,
        "revenue_cagr_from_q2_run_rate":
            (revenue_b / CURRENT_REVENUE_RUN_RATE_B) ** (1 / YEARS_TO_2030) - 1,
        "net_income_b": net_income_b,
        "market_cap_t": market_cap_t,
        "price_per_share": market_cap_t * 1_000 / SHARES_B,
        "annualized_return_from_current_market_cap":
            (market_cap_t / CURRENT_MARKET_CAP_T) ** (1 / YEARS_TO_2030) - 1,
    }


if __name__ == "__main__":
    for scenario in SCENARIOS:
        print(calculate(scenario))

# Source and methodology notes

## Reporting job

- Question: What annual revenue, earnings, and equity value could NVIDIA reach by 2030 as current AI infrastructure and embodied intelligence develop?
- Audience: product stakeholders / public-equity research reader.
- Main horizon: calendar 2030 annual run-rate; 2035 is directional only.
- Boundary: NVIDIA revenue only. Robot hardware, labor savings, cloud-service resale, and total robotics output are excluded.

## Required report structure mapping

1. Title → `title`
2. Executive Summary → `executive_summary`
3. Key findings with visual evidence → `baseline`, `scenario_interpretation`, `physical_ai_role`, `valuation`
4. Recommended next steps → `monitoring`
5. Further questions → `questions`
6. Caveats and assumptions → `caveats`

## Market boundary and anti-double-counting rule

- Core AI data center excludes data-center revenue explicitly attributed to physical-AI training and simulation.
- Physical-AI training and simulation is a subset of data-center demand, separated only to show its contribution.
- Physical-AI edge includes robot and autonomous-machine compute modules plus related automotive/edge revenue.
- Gaming, professional visualization, and other edge revenue are grouped together.
- Software is not added as a separate revenue pool because it is often monetized through hardware and systems; adding it separately would risk double counting.

## Evidence inventory, as of 2026-07-13

- NVIDIA Q1 FY2027 results: revenue $81.615B, data-center revenue $75.2B, Q2 revenue guide $91B ±2%.
- NVIDIA FY2026 results: revenue $215.938B, GAAP net income $120.067B.
- NVIDIA Q1 FY2027 10-Q: diluted weighted-average shares 24.391B.
- IFR World Robotics 2025: 542,076 industrial robots installed in 2024; 4,663,698 operational stock; more than 700,000 annual installations expected by 2028.
- NVIDIA Jetson Thor release: more than 2M robotics developers, 150+ ecosystem partners, 7,000+ Jetson Orin customers.
- Current market-cap reference: $5.109T in July 2026 from CompaniesMarketCap; this is a secondary market-data source.

## Scenario assumptions

- 2030 revenue: $420B / $650B / $950B.
- Normalized net margin: 43% / 48% / 51%.
- Terminal P/E: 22x / 28x / 32x.
- Static share count for price illustration: 24.3B; future repurchases and dilution are not modeled.
- Physical-AI attributable revenue: $33B / $80B / $170B.
- 2035 direction: $0.6T–$1.8T annual revenue, with a base case near $1.1T. This is not used in the valuation calculation.

## Chart map

- `revenue_composition`: Composition / stacked bar. Question: what creates each 2030 revenue scenario? Fields: scenario, segment, revenue_b. Supports the claim that core AI remains the main engine even when physical AI scales.
- `valuation_scenarios`: Comparison / bar. Question: what equity value follows from scenario earnings and multiples? Fields: scenario, market_cap_t. Supports the valuation range, with zero baseline.

## Validation notes

- All scenario subtotals reconcile to total revenue.
- Net income equals revenue multiplied by normalized net margin.
- Market cap equals net income multiplied by P/E.
- Price per share uses a static 24.3B share denominator and therefore is an illustration, not a target price.
- The model is structurally auditable but assumption-sensitive. Validation status: Share with caveats.

[RULES I BROKE]: none.

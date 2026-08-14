# Validation Report

## Overall Assessment: Share with caveats

[KNOWN] Question reviewed: the 2030 revenue, earnings, physical-AI contribution, and valuation scale that NVIDIA could reach as current AI infrastructure and embodied intelligence develop.

## Methodology Review

[KNOWN] The model measures NVIDIA-recognizable revenue rather than total robot sales or customer economic value.

[KNOWN] Core AI data-center revenue excludes the physical-AI training and simulation line, preventing that revenue from being counted twice.

[FRAME] Scenario assumptions remain judgmental because NVIDIA does not disclose a physical-AI revenue segment and reliable 2030 robot unit or edge-compute ASP forecasts do not exist.

## Issues Found

1. [KNOWN] Severity: Medium — Physical-AI revenue attribution is not directly disclosed; the $33B–$170B range is model-based.
2. [KNOWN] Severity: Medium — Terminal P/E and normalized net margin jointly dominate valuation; neither is observable today for 2030.
3. [KNOWN] Severity: Low — The static 24.3B share count ignores future repurchases and dilution, so per-share values are illustrations.
4. [KNOWN] Severity: Low — Current market capitalization uses a secondary market-data source and changes daily.

## Calculation Spot-Checks

- [COMPUTED] Revenue subtotals: verified — $340B+$25B+$8B+$47B=$420B; $500B+$55B+$25B+$70B=$650B; $690B+$100B+$70B+$90B=$950B.
- [COMPUTED] Base net income: verified — $650B×48%=$312B.
- [COMPUTED] Base market capitalization: verified — $312B×28=$8.736T.
- [COMPUTED] Base static per-share value: verified — $8.736T/24.3B=$359.51.
- [COMPUTED] Revenue CAGR: verified — from $364B to $420B/$650B/$950B over 4.5 years equals 3.2%/13.8%/23.8%.
- [COMPUTED] Base margin sensitivity: verified — $650B×5 percentage points×28=$0.91T of equity value.

## Visualization Review

[KNOWN] Both bar charts use zero baselines, explicit units, neutral titles, and adjacent interpretation.

[KNOWN] The portable HTML verifier passed at 1,440px and 390px viewports with no horizontal overflow or external network calls.

## Required Caveats for Stakeholders

- [FRAME] Treat all scenario outputs as conditional results, not forecasts or price targets.
- [INFERRED] The model is suitable for identifying what must be true for the current valuation, but not for choosing a position without a separate downside, probability, and portfolio analysis. Confidence: HIGH.
- [KNOWN] The Jupyter notebook could not be executed because the environment lacks the `jupyter` module; `model.py` and `scenario_query.sql` were executed successfully and reproduce the calculations.

[RULES I BROKE]: none.

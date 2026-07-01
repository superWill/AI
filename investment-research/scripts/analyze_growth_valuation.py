from __future__ import annotations

import pandas as pd
import yfinance as yf


TICKERS = [
    "AAPL", "ADBE", "INTU", "GOOGL", "ETN", "AVGO", "AMAT",
    "LRCX", "MU", "QCOM", "CEG", "GEV", "PDD",
]

CATEGORY = {
    "AAPL": "secular", "ADBE": "secular", "INTU": "secular",
    "GOOGL": "secular", "PDD": "secular/high-risk",
    "AVGO": "hybrid/acquisitive", "QCOM": "hybrid/cyclical",
    "AMAT": "cyclical", "LRCX": "cyclical", "MU": "cyclical",
    "ETN": "industrial", "CEG": "power", "GEV": "industrial/turnaround",
}


def scalar(statement: pd.DataFrame, row: str) -> float | None:
    if statement.empty or row not in statement.index:
        return None
    values = pd.to_numeric(statement.loc[row], errors="coerce").dropna()
    return float(values.iloc[0]) if not values.empty else None


def annual_series(statement: pd.DataFrame, row: str, n: int = 5) -> list[float]:
    if statement.empty or row not in statement.index:
        return []
    values = pd.to_numeric(statement.loc[row], errors="coerce").dropna()
    return [float(value) for value in values.iloc[:n]]


def cagr(newest: float | None, oldest: float | None, years: int) -> float | None:
    if newest is None or oldest is None or newest <= 0 or oldest <= 0 or years <= 0:
        return None
    return (newest / oldest) ** (1 / years) - 1


def fmt_sequence(values: list[float]) -> str:
    return ",".join(f"{value:.2f}" for value in values)


rows: list[dict[str, object]] = []
for symbol in TICKERS:
    ticker = yf.Ticker(symbol)
    info = ticker.info
    annual_income = ticker.income_stmt
    annual_cashflow = ticker.cash_flow
    ttm_income = ticker.ttm_income_stmt
    ttm_cashflow = ticker.ttm_cash_flow

    price = float(ticker.fast_info["last_price"])
    market_cap = float(ticker.fast_info["market_cap"])
    ttm_eps = scalar(ttm_income, "Diluted EPS") or info.get("trailingEps")
    ttm_fcf = scalar(ttm_cashflow, "Free Cash Flow")
    eps = annual_series(annual_income, "Diluted EPS", 4)
    annual_fcf = annual_series(annual_cashflow, "Free Cash Flow", 4)
    annual_shares = annual_series(annual_income, "Diluted Average Shares", 4)
    fcf_per_share = [
        fcf / shares for fcf, shares in zip(annual_fcf, annual_shares) if shares > 0
    ]

    eps_cagr = cagr(eps[0], eps[3], 3) if len(eps) >= 4 else None
    fcfps_cagr = cagr(fcf_per_share[0], fcf_per_share[3], 3) if len(fcf_per_share) >= 4 else None
    quote_currency = info.get("currency")
    financial_currency = info.get("financialCurrency")
    currency_match = not financial_currency or quote_currency == financial_currency
    calculated_pe = price / ttm_eps if ttm_eps and ttm_eps > 0 and currency_match else None
    trailing_pe = calculated_pe or info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    historical_growth_price = trailing_pe / (eps_cagr * 100) if trailing_pe and eps_cagr and eps_cagr > 0 else None
    fcf_yield = (
        ttm_fcf / market_cap
        if ttm_fcf is not None and market_cap > 0 and currency_match
        else None
    )

    yoy = [eps[i] / eps[i + 1] - 1 for i in range(len(eps) - 1) if eps[i + 1] != 0]
    monotonic = len(eps) >= 4 and all(eps[i] >= eps[i + 1] for i in range(len(eps) - 1))
    sign_change = len(eps) >= 2 and any(eps[i] * eps[i + 1] <= 0 for i in range(len(eps) - 1))
    growth_range = (max(yoy) - min(yoy)) if yoy else None
    positive_eps = [value for value in eps if value > 0]
    median_eps = float(pd.Series(positive_eps).median()) if positive_eps else None
    median_eps_pe = price / median_eps if median_eps and currency_match else None

    rows.append({
        "ticker": symbol,
        "category": CATEGORY[symbol],
        "price": price,
        "quote_currency": quote_currency,
        "financial_currency": financial_currency,
        "currency_match": currency_match,
        "ttm_eps": ttm_eps,
        "ttm_pe": trailing_pe,
        "forward_pe": forward_pe,
        "eps_3y_cagr": eps_cagr,
        "fcfps_3y_cagr": fcfps_cagr,
        "backward_pe_growth": historical_growth_price,
        "price_to_4y_median_positive_eps": median_eps_pe,
        "ttm_fcf_yield": fcf_yield,
        "eps_monotonic": monotonic,
        "eps_sign_change": sign_change,
        "eps_growth_range": growth_range,
        "eps_sequence_new_to_old": fmt_sequence(eps),
        "fcfps_sequence_new_to_old": fmt_sequence(fcf_per_share),
    })

result = pd.DataFrame(rows)
output_path = "data/growth-valuation-screen-2026-06-30.csv"
result.to_csv(output_path, index=False)

display = result.copy()
for column in ["price", "ttm_eps", "ttm_pe", "forward_pe", "backward_pe_growth", "price_to_4y_median_positive_eps"]:
    display[column] = display[column].map(lambda x: "" if pd.isna(x) else f"{x:.2f}")
for column in ["eps_3y_cagr", "fcfps_3y_cagr", "ttm_fcf_yield", "eps_growth_range"]:
    display[column] = display[column].map(lambda x: "" if pd.isna(x) else f"{x * 100:.1f}%")
print(display.to_string(index=False))

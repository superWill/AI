#!/usr/bin/env python3
"""Quantify contemporaneous and forward-looking market sentiment relationships."""

from __future__ import annotations

import csv
import math
import statistics
from datetime import datetime
from pathlib import Path


DATA_FILES = {
    "spx": Path("/private/tmp/sp500_sentiment.csv"),
    "vix": Path("/private/tmp/vix_cboe_history.csv"),
    "hy": Path("/private/tmp/hyoas_sentiment.csv"),
    "real10": Path("/private/tmp/real10_sentiment.csv"),
}


def read_series(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        is_cboe_vix = reader.fieldnames[0] == "DATE"
        date_field = "DATE" if is_cboe_vix else "observation_date"
        value_field = "CLOSE" if is_cboe_vix else reader.fieldnames[1]
        result = {}
        for row in reader:
            raw = row[value_field]
            if raw not in ("", "."):
                date = row[date_field]
                if is_cboe_vix:
                    date = datetime.strptime(date, "%m/%d/%Y").date().isoformat()
                result[date] = float(raw)
        return result


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    size = len(vector)
    augmented = [matrix[i][:] + [vector[i]] for i in range(size)]
    for column in range(size):
        pivot = max(range(column, size), key=lambda row: abs(augmented[row][column]))
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        if abs(divisor) < 1e-12:
            raise ValueError("Singular matrix")
        augmented[column] = [value / divisor for value in augmented[column]]
        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                augmented[row][j] - factor * augmented[column][j]
                for j in range(size + 1)
            ]
    return [augmented[i][-1] for i in range(size)]


def ols(y: list[float], predictors: list[list[float]]) -> dict[str, object]:
    design = [[1.0] + row for row in predictors]
    columns = len(design[0])
    xtx = [[sum(row[i] * row[j] for row in design) for j in range(columns)] for i in range(columns)]
    xty = [sum(row[i] * target for row, target in zip(design, y)) for i in range(columns)]
    beta = solve(xtx, xty)
    fitted = [sum(coef * value for coef, value in zip(beta, row)) for row in design]
    mean_y = statistics.fmean(y)
    sse = sum((target - estimate) ** 2 for target, estimate in zip(y, fitted))
    sst = sum((target - mean_y) ** 2 for target in y)
    r2 = 1.0 - sse / sst
    adjusted = 1.0 - (1.0 - r2) * (len(y) - 1) / (len(y) - columns)
    return {"beta": beta, "fitted": fitted, "r2": r2, "adjusted_r2": adjusted}


def percentile(values: list[float], value: float) -> float:
    return 100.0 * sum(item <= value for item in values) / len(values)


def main() -> None:
    series = {name: read_series(path) for name, path in DATA_FILES.items()}
    dates = sorted(set(series["spx"]) & set(series["vix"]))
    rows = []
    for previous, current in zip(dates, dates[1:]):
        rows.append(
            {
                "date": current,
                "ret": 100.0 * math.log(series["spx"][current] / series["spx"][previous]),
                "vix": series["vix"][current],
                "dvix": series["vix"][current] - series["vix"][previous],
            }
        )

    y = [row["ret"] for row in rows]
    same_vix = ols(y, [[row["dvix"]] for row in rows])

    macro_rows = []
    macro_dates = sorted(set(series["spx"]) & set(series["vix"]) & set(series["real10"]))
    for previous, current in zip(macro_dates, macro_dates[1:]):
        macro_rows.append(
            {
                "ret": 100.0 * math.log(series["spx"][current] / series["spx"][previous]),
                "dvix": series["vix"][current] - series["vix"][previous],
                "dreal_bp": 100.0 * (series["real10"][current] - series["real10"][previous]),
            }
        )
    macro_y = [row["ret"] for row in macro_rows]
    same_vix_real = ols(macro_y, [[row["dvix"], row["dreal_bp"]] for row in macro_rows])
    same_real = ols(macro_y, [[row["dreal_bp"]] for row in macro_rows])

    extended = []
    hy_dates = sorted(set(series["spx"]) & set(series["vix"]) & set(series["real10"]) & set(series["hy"]))
    for previous, current in zip(hy_dates, hy_dates[1:]):
        extended.append(
            {
                "date": current,
                "ret": 100.0 * math.log(series["spx"][current] / series["spx"][previous]),
                "dvix": series["vix"][current] - series["vix"][previous],
                "dreal_bp": 100.0 * (series["real10"][current] - series["real10"][previous]),
                "dhy_bp": 100.0 * (series["hy"][current] - series["hy"][previous]),
            }
        )
    extended_model = ols(
        [row["ret"] for row in extended],
        [[row["dvix"], row["dreal_bp"], row["dhy_bp"]] for row in extended],
    )
    extended_y = [row["ret"] for row in extended]
    extended_vix = ols(extended_y, [[row["dvix"]] for row in extended])
    extended_real = ols(extended_y, [[row["dreal_bp"]] for row in extended])
    extended_hy = ols(extended_y, [[row["dhy_bp"]] for row in extended])
    extended_vix_real = ols(
        extended_y, [[row["dvix"], row["dreal_bp"]] for row in extended]
    )
    extended_vix_hy = ols(
        extended_y, [[row["dvix"], row["dhy_bp"]] for row in extended]
    )

    forward_y = [rows[index + 1]["ret"] for index in range(len(rows) - 1)]
    forward_x = [[rows[index]["vix"], rows[index]["dvix"]] for index in range(len(rows) - 1)]
    forward_model = ols(forward_y, forward_x)

    train_indices = [i for i, row in enumerate(rows[:-1]) if row["date"] < "2023-01-01"]
    test_indices = [i for i, row in enumerate(rows[:-1]) if row["date"] >= "2023-01-01"]
    trained = ols([forward_y[i] for i in train_indices], [forward_x[i] for i in train_indices])
    beta = trained["beta"]
    predictions = [beta[0] + sum(beta[j + 1] * forward_x[i][j] for j in range(2)) for i in test_indices]
    actuals = [forward_y[i] for i in test_indices]
    train_mean = statistics.fmean([forward_y[i] for i in train_indices])
    oos_r2 = 1.0 - sum((a - p) ** 2 for a, p in zip(actuals, predictions)) / sum((a - train_mean) ** 2 for a in actuals)

    horizon_results = []
    for horizon in (1, 5, 21, 63):
        horizon_y = [
            100.0 * math.log(series["spx"][rows[index + horizon]["date"]] / series["spx"][rows[index]["date"]])
            for index in range(len(rows) - horizon)
        ]
        vix_level_model = ols(horizon_y, [[rows[index]["vix"]] for index in range(len(rows) - horizon)])
        vix_change_model = ols(horizon_y, [[rows[index]["dvix"]] for index in range(len(rows) - horizon)])
        month_end_indices = [
            index
            for index in range(len(rows) - horizon)
            if rows[index]["date"][:7] != rows[index + 1]["date"][:7]
        ]
        month_end_model = ols(
            [horizon_y[index] for index in month_end_indices],
            [[rows[index]["vix"]] for index in month_end_indices],
        )
        horizon_results.append(
            (horizon, len(horizon_y), vix_level_model["r2"], vix_change_model["r2"], len(month_end_indices), month_end_model["r2"])
        )

    month_ends = []
    for index, row in enumerate(rows):
        if index + 21 >= len(rows):
            continue
        current_month = row["date"][:7]
        next_month = rows[index + 1]["date"][:7] if index + 1 < len(rows) else ""
        if current_month != next_month:
            forward_21 = 100.0 * math.log(
                series["spx"][rows[index + 21]["date"]] / series["spx"][row["date"]]
            )
            month_ends.append((row["vix"], forward_21))

    buckets = [("<15", -math.inf, 15), ("15–20", 15, 20), ("20–30", 20, 30), ("≥30", 30, math.inf)]
    bucket_results = []
    for label, lower, upper in buckets:
        values = [ret for vix, ret in month_ends if lower <= vix < upper]
        bucket_results.append(
            {
                "bucket": label,
                "n": len(values),
                "mean": statistics.fmean(values),
                "median": statistics.median(values),
                "positive": 100.0 * sum(value > 0 for value in values) / len(values),
            }
        )

    shocks = [row for row in rows if row["dvix"] >= 5.0]
    shock_indices = [index for index, row in enumerate(rows) if row["dvix"] >= 5.0 and index + 21 < len(rows)]
    shock_same = [rows[index]["ret"] for index in shock_indices]
    shock_next = [rows[index + 1]["ret"] for index in shock_indices]
    shock_21 = [
        100.0 * math.log(series["spx"][rows[index + 21]["date"]] / series["spx"][rows[index]["date"]])
        for index in shock_indices
    ]

    latest_vix_date = max(series["vix"])
    latest_vix = series["vix"][latest_vix_date]
    sample_vix = [value for date, value in series["vix"].items() if dates[0] <= date <= latest_vix_date]
    print(f"CORE_WINDOW={rows[0]['date']}..{rows[-1]['date']} N={len(rows)}")
    print(f"LATEST_VIX_DATE={latest_vix_date} LATEST_VIX={latest_vix:.2f} PERCENTILE={percentile(sample_vix, latest_vix):.1f}")
    print(f"SAME_DAY_VIX_R2={same_vix['r2']:.4f} BETA_DVIX={same_vix['beta'][1]:.4f}")
    print(f"SAME_DAY_REAL_R2={same_real['r2']:.4f} BETA_REAL_BP={same_real['beta'][1]:.4f}")
    print(f"SAME_DAY_VIX_REAL_R2={same_vix_real['r2']:.4f} ADJ={same_vix_real['adjusted_r2']:.4f}")
    print(f"EXTENDED_WINDOW={extended[0]['date']}..{extended[-1]['date']} N={len(extended)}")
    print(f"EXTENDED_FULL_R2={extended_model['r2']:.4f} ADJ={extended_model['adjusted_r2']:.4f} BETAS={extended_model['beta']}")
    print(
        "EXTENDED_NESTED_R2="
        f"VIX:{extended_vix['r2']:.4f},REAL:{extended_real['r2']:.4f},"
        f"HY:{extended_hy['r2']:.4f},VIX_REAL:{extended_vix_real['r2']:.4f},"
        f"VIX_HY:{extended_vix_hy['r2']:.4f},FULL:{extended_model['r2']:.4f}"
    )
    print(f"NEXT_DAY_IN_SAMPLE_R2={forward_model['r2']:.5f} ADJ={forward_model['adjusted_r2']:.5f}")
    print(f"NEXT_DAY_OOS_R2_2023_PLUS={oos_r2:.5f} TEST_N={len(test_indices)}")
    print("FORWARD_HORIZON_R2")
    for result in horizon_results:
        print(
            f"H={result[0]} N={result[1]} VIX_LEVEL={result[2]:.5f} "
            f"DVIX={result[3]:.5f} MONTH_END_N={result[4]} MONTH_END_VIX_LEVEL={result[5]:.5f}"
        )
    print("MONTH_END_VIX_BUCKETS")
    for result in bucket_results:
        print(result)
    print(f"VIX_PLUS_5_SHOCKS_RAW_N={len(shocks)} USABLE_N={len(shock_indices)}")
    print(f"SHOCK_SAME_MEAN={statistics.fmean(shock_same):.3f} MEDIAN={statistics.median(shock_same):.3f}")
    print(f"SHOCK_NEXT_MEAN={statistics.fmean(shock_next):.3f} MEDIAN={statistics.median(shock_next):.3f}")
    print(f"SHOCK_21D_MEAN={statistics.fmean(shock_21):.3f} MEDIAN={statistics.median(shock_21):.3f} POS={100*sum(v>0 for v in shock_21)/len(shock_21):.1f}")


if __name__ == "__main__":
    main()

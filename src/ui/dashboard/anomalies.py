import pandas as pd


def flag_daily_anomalies(
    daily_energy: pd.Series,
    history_days: int = 28,
    minimum_history: int = 3,
    threshold: float = 3.0,
) -> pd.DataFrame:
    """Flag daily outliers against recent readings from the same weekday."""
    if history_days < 7:
        raise ValueError("history_days must be at least 7")
    if minimum_history < 1:
        raise ValueError("minimum_history must be at least 1")
    if threshold <= 0:
        raise ValueError("threshold must be greater than 0")
    if not isinstance(daily_energy.index, pd.DatetimeIndex):
        raise ValueError("daily_energy must have a DatetimeIndex")

    values = pd.to_numeric(daily_energy, errors="coerce").astype(float)
    values = values.replace([float("inf"), float("-inf")], float("nan"))
    medians = pd.Series(float("nan"), index=values.index, dtype=float)
    deviations = pd.Series(float("nan"), index=values.index, dtype=float)

    for position, timestamp in enumerate(values.index):
        cutoff = timestamp - pd.Timedelta(days=history_days)
        history = values.iloc[:position]
        history = history[
            (history.index >= cutoff)
            & (history.index.dayofweek == timestamp.dayofweek)
        ].dropna()
        if len(history) < minimum_history:
            continue

        median = float(history.median())
        medians.iloc[position] = median
        deviations.iloc[position] = float((history - median).abs().median())

    margin = threshold * 1.4826 * deviations
    lower_bound = medians - margin
    upper_bound = medians + margin
    is_anomaly = (
        medians.notna()
        & values.notna()
        & ((values < lower_bound) | (values > upper_bound))
    )

    return pd.DataFrame(
        {
            "consumption_kwh": values,
            "median_kwh": medians,
            "lower_bound_kwh": lower_bound,
            "upper_bound_kwh": upper_bound,
            "is_anomaly": is_anomaly,
        },
        index=daily_energy.index,
    )

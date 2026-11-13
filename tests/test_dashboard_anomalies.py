import pandas as pd
import pytest

from ui.dashboard.anomalies import flag_daily_anomalies


def test_flags_spike_against_previous_same_weekdays():
    readings = [100.0] * 28
    readings[0], readings[7], readings[14], readings[21] = 100, 102, 98, 101
    readings.append(250)
    readings = pd.Series(
        readings,
        index=pd.date_range("2026-01-01", periods=29),
    )

    result = flag_daily_anomalies(readings)

    assert result["is_anomaly"].sum() == 1
    assert bool(result["is_anomaly"].iloc[-1])
    assert result.iloc[-1]["median_kwh"] == 100.5


def test_does_not_flag_inside_same_weekday_robust_range():
    readings = [100.0] * 28
    readings[0], readings[7], readings[14], readings[21] = 100, 102, 98, 101
    readings.append(104)
    readings = pd.Series(
        readings,
        index=pd.date_range("2026-01-01", periods=29),
    )

    result = flag_daily_anomalies(readings)

    assert not result["is_anomaly"].any()


def test_requires_minimum_history_and_handles_missing_values():
    readings = [float("nan")] * 29
    readings[0] = readings[7] = readings[14] = readings[21] = 10
    readings[28] = 100
    readings = pd.Series(readings, index=pd.date_range("2026-01-01", periods=29))

    result = flag_daily_anomalies(readings)

    assert result["median_kwh"].iloc[:21].isna().all()
    assert bool(result["is_anomaly"].iloc[-1])


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"history_days": 6}, "history_days"),
        ({"minimum_history": 0}, "minimum_history"),
        ({"threshold": 0}, "threshold"),
    ],
)
def test_rejects_invalid_detection_settings(kwargs, message):
    with pytest.raises(ValueError, match=message):
        flag_daily_anomalies(pd.Series([1, 2, 3]), **kwargs)

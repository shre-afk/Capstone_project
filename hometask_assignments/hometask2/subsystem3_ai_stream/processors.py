"""Prepare streaming energy signals for the advisor using the shared ABC.

These processors apply explicit rules, not learned anomaly detection. They can
feed a later LangChain advisor without making a model call for every reading.
"""

from copy import deepcopy
from math import isfinite
from numbers import Real

from ..subsystem2_stream.processors import StreamProcessor


def _nonnegative(value, label):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or value < 0:
        raise ValueError(f"{label} must be a finite, nonnegative number")
    return float(value)


class AdvisorSignalFilter(StreamProcessor):
    """Keep significant after-hours use or power above a configured rule threshold."""

    DEFAULT_HIGH_POWER_KW = {"home": 3.0, "business": 80.0, "public": 20.0}

    def __init__(self, min_power_kw=0.8, high_power_kw=None):
        self.min_power_kw = _nonnegative(min_power_kw, "minimum power")
        thresholds = self.DEFAULT_HIGH_POWER_KW if high_power_kw is None else high_power_kw
        if not isinstance(thresholds, dict) or set(thresholds) != set(self.DEFAULT_HIGH_POWER_KW):
            raise ValueError("provide high-power thresholds for home, business, and public")
        self.high_power_kw = {
            kind: _nonnegative(value, f"{kind} high-power threshold")
            for kind, value in thresholds.items()
        }

    def process(self, reading):
        _nonnegative(reading.kwh, "interval energy")
        power = _nonnegative(reading.power_kw, "average power")
        if reading.building_type not in self.high_power_kw:
            raise ValueError("unknown building type")
        if not isinstance(reading.extras.get("after_hours"), bool):
            raise ValueError("run AfterHoursFlagger before the advisor filter")

        # Clear derived state when the same object is reconsidered with new rules.
        for key in ("advisor_reasons", "advisor_context", "advisor_message"):
            reading.extras.pop(key, None)
        if power < self.min_power_kw:
            return None
        reasons = []
        if reading.extras["after_hours"]:
            reasons.append("after_hours")
        if power >= self.high_power_kw[reading.building_type]:
            reasons.append("high_power")
        if not reasons:
            return None
        reading.extras["advisor_reasons"] = reasons
        return reading


class EnergyInsightTransformer(StreamProcessor):
    """Transform retained signals into factual context and investigation suggestions."""

    def process(self, reading):
        reasons = reading.extras.get("advisor_reasons")
        if not isinstance(reasons, list) or not reasons or any(
                reason not in ("after_hours", "high_power") for reason in reasons):
            raise ValueError("run AdvisorSignalFilter before the insight transformer")
        if reading.interval_start is None:
            raise ValueError("the signal needs an interval start")
        metrics = {
            "energy_kwh": _nonnegative(reading.kwh, "interval energy"),
            "power_kw": _nonnegative(reading.power_kw, "average power"),
            "cost_eur": _nonnegative(reading.extras.get("eur"), "estimated cost"),
            "co2_kg": _nonnegative(reading.extras.get("co2_kg"), "estimated emissions"),
        }
        suggestions = []
        if "after_hours" in reasons:
            suggestions.append("Review equipment schedules and standby loads outside opening hours.")
        if "high_power" in reasons:
            suggestions.append("Compare the interval with historical demand and scheduled equipment operation.")
        reading.extras["advisor_context"] = {
            "building": reading.building,
            "building_type": reading.building_type,
            "meter_column": reading.column,
            "interval_start": reading.interval_start.isoformat(),
            "interval_end": reading.ts.isoformat(),
            "timezone": "Europe/Berlin",
            **metrics,
            "after_hours": reading.extras["after_hours"],
            "reasons": deepcopy(reasons),
            "suggestions": suggestions,
            "assessment": "Rule-based signal; the cause is not established by this interval alone.",
        }
        labels = ", ".join(reason.replace("_", " ") for reason in reasons)
        reading.extras["advisor_message"] = (
            f"{reading.building}, {reading.interval_start:%H:%M}–{reading.ts:%H:%M}: "
            f"{metrics['energy_kwh']:.3f} kWh, {metrics['power_kw']:.2f} kW, "
            f"EUR {metrics['cost_eur']:.2f}, {metrics['co2_kg']:.2f} kg CO2. "
            f"Flagged: {labels}. {' '.join(suggestions)}"
        )
        return reading

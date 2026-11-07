"""Run from the repository root:

python -m hometask_assignments.hometask2.subsystem3_ai_stream.demo
"""

from ..subsystem2_stream.processors import (
    AfterHoursFlagger, CostCarbonCalculator, InactiveMeterFilter,
    IntervalCalculator, LoadBalanceTracker, PlausibilityFilter, ThresholdFilter,
)
from ..subsystem2_stream.stream import MeterStream, replay_feed
from .processors import AdvisorSignalFilter, EnergyInsightTransformer


def main():
    balance = LoadBalanceTracker()
    energy_pipeline = (
        InactiveMeterFilter()
        | IntervalCalculator()
        | PlausibilityFilter()
        | ThresholdFilter(min_kw=0.8)
        | CostCarbonCalculator()
        | AfterHoursFlagger()
        | balance
    )
    advisor_pipeline = AdvisorSignalFilter() | EnergyInsightTransformer()
    source = MeterStream(replay_feed())
    counts = {"retained": 0, "signals": 0}

    def retained_readings():
        # The data pipeline updates balances before the advisor selects signals.
        for reading in energy_pipeline.run(source):
            counts["retained"] += 1
            yield reading

    print("Data pipeline:", energy_pipeline)
    print("Advisor pipeline:", advisor_pipeline)
    print("Historical replay; configured demonstration rules, no live AI call.\n")
    for reading in advisor_pipeline.run(retained_readings()):
        counts["signals"] += 1
        print(reading.extras["advisor_message"])

    print(f"\nInput readings: {source.count}")
    print(f"Retained energy intervals: {counts['retained']}")
    print(f"Dropped by the data pipeline: {source.count - counts['retained']}")
    print(f"Advisor signals: {counts['signals']}")
    print(f"Retained intervals without advisor flags: {counts['retained'] - counts['signals']}")
    print("\nRetained-interval balances, computed before advisor selection:")
    for building, totals in balance.balances.items():
        print(f"{building}: {totals['kwh']:.3f} kWh; EUR {totals['eur']:.2f}; "
              f"{totals['co2_kg']:.2f} kg CO2; "
              f"after-hours {totals['after_hours_kwh']:.3f} kWh")


if __name__ == "__main__":
    main()

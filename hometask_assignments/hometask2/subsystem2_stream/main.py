
if __package__:
    from .processors import (AfterHoursFlagger, CostCarbonCalculator, InactiveMeterFilter,
                             IntervalCalculator, LoadBalanceTracker, PlausibilityFilter,
                             ThresholdFilter)
    from .stream import MeterStream, replay_feed
else:
    from processors import (AfterHoursFlagger, CostCarbonCalculator, InactiveMeterFilter,
                            IntervalCalculator, LoadBalanceTracker, PlausibilityFilter,
                            ThresholdFilter)
    from stream import MeterStream, replay_feed
 
balance = LoadBalanceTracker()          # kept in a variable so can be read at the end
 
pipeline = (InactiveMeterFilter()
            | IntervalCalculator()
            | PlausibilityFilter()
            | ThresholdFilter(min_kw=0.8)
            | CostCarbonCalculator()
            | AfterHoursFlagger()
            | balance)
 
print("pipeline:", pipeline, "\n")
 
stream = MeterStream(replay_feed())
kept = 0
for reading in pipeline.run(stream):
    print(reading)
    kept += 1
 
print(f"\n{stream.count} readings came in, {kept} got through, {stream.count - kept} were dropped\n")
print("Retained-interval totals (after usage filtering):")
print(f"{'building':<11}{'kWh':>8}{'EUR':>8}{'CO2 kg':>8}{'after-hours':>13}")
for building, b in balance.balances.items():
    share = b["after_hours_kwh"] / b["kwh"]
    print(f"{building:<11}{b['kwh']:>8.2f}{b['eur']:>8.2f}{b['co2_kg']:>8.2f}{share:>12.0%}")

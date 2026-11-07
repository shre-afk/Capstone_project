"""The processing steps"""
 
from abc import ABC, abstractmethod
from datetime import timedelta
 
# the same numbers as the capstone's config.toml
INTERVAL = timedelta(minutes=15)
MAX_KWH_PER_INTERVAL = {"home": 5.0, "business": 100.0, "public": 50.0}
EUR_PER_KWH = 0.30
CO2_KG_PER_KWH = 0.38
 
 
class StreamProcessor(ABC):
    """take one reading, return it (maybe changed) or None to drop it"""
 
    @abstractmethod
    def process(self, reading):
        pass
 
    def __or__(self, other):
        """step_a | step_b  ->  a Pipeline that runs a first, then b"""
        return Pipeline([self, other])
 
    __add__ = __or__        # so  step_a + step_b  works too
 
    def run(self, stream):
        """GENERATOR:- push every reading through process() and yield the survivors"""
        for reading in stream:
            result = self.process(reading)
            if result is not None:
                yield result
 
 
class Pipeline(StreamProcessor):
    """A chain of steps that itself behaves like ONE step"""
 
    def __init__(self, steps):
        self.steps = []
        for step in steps:
            if isinstance(step, Pipeline):
                self.steps.extend(step.steps)   # flatten (a | b) | c into a, b, c
            else:
                self.steps.append(step)
 
    def process(self, reading):
        for step in self.steps:
            reading = step.process(reading)
            if reading is None:
                return None
        return reading
 
    def __repr__(self):
        return " | ".join(type(step).__name__ for step in self.steps)
 
 
# ---------------- filters: like opsd.to_intervals() and opsd.validate() ----------------
 
class InactiveMeterFilter(StreamProcessor):
    """Drop readings from meters that sent nothing (totals.dropna() in the capstone)"""
 
    def process(self, reading):
        if reading.total_kwh is None:
            return None
        return reading
 
 
class IntervalCalculator(StreamProcessor):
    """Counter -> kWh and kW of the last 15 min, only if the previous value is exactly 15 min old"""
 
    def __init__(self):
        self.last_seen = {}          # column -> (time, counter)
 
    def process(self, reading):
        previous = self.last_seen.get(reading.column)
        self.last_seen[reading.column] = (reading.ts, reading.total_kwh)
        if previous is None:
            return None                              # first value: nothing to compare with yet
        previous_ts, previous_total = previous
        if reading.ts - previous_ts != INTERVAL:
            return None                              # a gap: can't say which 15 min it belongs to
        reading.interval_start = previous_ts
        reading.kwh = round(reading.total_kwh - previous_total, 3)
        reading.power_kw = round(reading.kwh * 4, 2)  # kWh in 15 min x 4 = kW (as in get_latest)
        return reading
 
 
class PlausibilityFilter(StreamProcessor):
    """0 <= kWh <= the limit for this building type, exactly like opsd.validate()"""
 
    def __init__(self, limits=MAX_KWH_PER_INTERVAL):
        self.limits = limits
 
    def process(self, reading):
        if 0 <= reading.kwh <= self.limits[reading.building_type]:
            return reading
        return None
 
 
class ThresholdFilter(StreamProcessor):
    """Drop sub-threshold readings: a building drawing less power than min_kw is on standby"""
 
    def __init__(self, min_kw):
        self.min_kw = min_kw
 
    def process(self, reading):
        if reading.power_kw < self.min_kw:
            return None
        return reading
 
 
# ---------------- transforms: like calc.py ----------------
 
class CostCarbonCalculator(StreamProcessor):
    """Euros and kg of CO2 for this reading (calc.cost_eur and calc.co2_kg)"""
 
    def __init__(self, eur_per_kwh=EUR_PER_KWH, kg_per_kwh=CO2_KG_PER_KWH):
        self.eur_per_kwh = eur_per_kwh
        self.kg_per_kwh = kg_per_kwh
 
    def process(self, reading):
        reading.extras["eur"] = round(reading.kwh * self.eur_per_kwh, 2)
        reading.extras["co2_kg"] = round(reading.kwh * self.kg_per_kwh, 2)
        return reading
 
 
def is_open(building_type, ts):
    """Opening hours, same rules as Home / Business / PublicBuilding in models.py"""
    if building_type == "home":
        return 6 <= ts.hour < 23
    if building_type == "business":
        return ts.weekday() < 5 and 7 <= ts.hour < 19
    return ts.weekday() < 5 and 7 <= ts.hour < 17
 
 
class AfterHoursFlagger(StreamProcessor):
    """Classify aligned quarter-hour intervals by their starting time.

    The counter timestamp is the end of the interval: 18:45–19:00 is still
    within a business's opening hours, while 19:00–19:15 is after hours.
    """
 
    def process(self, reading):
        if reading.interval_start is None:
            raise ValueError("calculate interval energy before flagging after-hours use")
        reading.extras["after_hours"] = not is_open(reading.building_type, reading.interval_start)
        return reading
 
 
class LoadBalanceTracker(StreamProcessor):
    """Running energy balance per building: kWh, EUR, CO2 and after-hours kWh so far"""
 
    def __init__(self):
        self.balances = {}          # building -> {"kwh": ..., "eur": ..., ...}
 
    def process(self, reading):
        b = self.balances.setdefault(reading.building,
                                     {"kwh": 0.0, "eur": 0.0, "co2_kg": 0.0, "after_hours_kwh": 0.0})
        b["kwh"] = round(b["kwh"] + reading.kwh, 3)
        b["eur"] = round(b["eur"] + reading.extras["eur"], 2)
        b["co2_kg"] = round(b["co2_kg"] + reading.extras["co2_kg"], 2)
        if reading.extras["after_hours"]:
            b["after_hours_kwh"] = round(b["after_hours_kwh"] + reading.kwh, 3)
        return reading

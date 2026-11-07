"""A small stream framework: filter meter events and calculate carbon equivalents."""

from abc import ABC, abstractmethod
from math import isfinite


class StreamProcessor(ABC):
    @abstractmethod
    def process(self, reading):
        """Return a processed result, or None to discard a reading."""

    def __or__(self, other):
        if not isinstance(other, StreamProcessor):
            return NotImplemented
        return Pipeline([self, other])

    def run(self, stream):
        for reading in stream:
            result = self.process(reading)
            if result is not None:
                yield result


class Pipeline(StreamProcessor):
    def __init__(self, steps):
        self.steps = steps

    def process(self, reading):
        for step in self.steps:
            reading = step.process(reading)
            if reading is None:
                return None
        return reading


class PowerFilter(StreamProcessor):
    def __init__(self, min_power_kw=0.8):
        if not isfinite(min_power_kw) or min_power_kw < 0:
            raise ValueError('minimum power must be finite and nonnegative')
        self.min_power_kw = min_power_kw

    def process(self, reading):
        if (reading.active and isfinite(reading.power_kw)
                and reading.power_kw >= self.min_power_kw):
            return reading
        return None


class CarbonTransformer(StreamProcessor):
    def process(self, reading):
        # Each event represents average power during a 15-minute interval.
        energy_kwh = reading.power_kw * 0.25
        return {
            'building': reading.building,
            'power_kw': reading.power_kw,
            'energy_kwh': round(energy_kwh, 3),
            'co2_kg': round(energy_kwh * 0.38, 3),
        }

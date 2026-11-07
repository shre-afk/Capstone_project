"""Meter events, an explicit iterator, and a small simulated event generator."""


class MeterReading:
    def __init__(self, building, power_kw, active=True):
        self.building = building
        self.power_kw = power_kw
        self.active = active


class MeterStream:
    def __init__(self, source):
        self._source = iter(source)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._source)


def sample_readings():
    yield MeterReading('Home 1', 4.0)
    yield MeterReading('Home 1', 0.2)                # Below the power threshold.
    yield MeterReading('Office 1', 8.0, active=False)
    yield MeterReading('Office 1', 8.0)
    yield MeterReading('Home 1', 0.8)                # Exactly at the threshold.

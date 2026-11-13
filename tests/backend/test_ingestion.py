"""test_ingestion.py - turning OPSD meter totals into clean readings

Only the small helper functions are tested here
Small hand-made data, no CSV file
"""

import pandas as pd

from backend.ingestion import opsd


def test_meter_totals_become_energy_per_15_minutes():
    # a meter counts up like a car's odometer
    # the energy used = this total minus the one before
    times = pd.date_range("2016-01-01 10:00", periods=4, freq="15min", tz="UTC")
    totals = pd.Series([10.0, 10.5, 11.5, 11.75], index=times)

    used = opsd.to_intervals(totals)

    # 10.5 - 10.0 / 11.5 - 10.5 / 11.75 - 11.5
    assert list(used) == [0.5, 1.0, 0.25]


def test_impossible_values_are_rejected():
    # negative energy or more than the limit can't be real
    used = pd.Series([-0.1, 2.0, 5.0, 9.0])

    good, rejected = opsd.validate(used, max_kwh=5.0)

    # the limit itself (5.0) is still allowed
    assert list(good) == [2.0, 5.0]
    assert rejected == 2


def test_config_block_becomes_a_building():
    # one [[buildings]] block from config.toml
    entry = {"name": "Home 1", "type": "home", "column": "COL_A", "floor_area_m2": 140}

    building = opsd.build_from_config(entry)

    assert building.name == "Home 1"
    assert building.building_type == "home"

    # the meter remembers which CSV column it reads
    assert building.meters()[0].source == "COL_A"

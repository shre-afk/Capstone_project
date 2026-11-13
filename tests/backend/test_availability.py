"""Availability uses stored electricity timestamps, with Berlin month boundaries."""

import json
from unittest.mock import Mock

import pandas as pd
import pytest

from advisor.tools import get_data_availability
from backend.analysis import api
from backend.db import database
from backend.models import EnergyMeter, Home, Meter, Zone


@pytest.fixture
def home(empty_db):
    building = Home("Availability home", 100)
    building.add_zone(Zone("Main")).add_meter(EnergyMeter())
    database.save_building(empty_db, building)
    return building


def store(con, meter, times):
    database.save_readings(con, meter.id, pd.Series(0.0, index=times))


def test_existing_building_without_readings_has_no_available_months(home):
    result = api.get_data_availability(home.id)
    assert result["status"] == "no_data"
    assert result["building_name"] == home.name
    assert result["months"] == []
    assert result["available_month_count"] == 0
    assert result["fully_covered_month_count"] == 0
    assert result["first_stored_interval_start"] is None
    assert result["latest_stored_interval_start"] is None


def test_unknown_building_is_rejected(empty_db):
    with pytest.raises(ValueError, match="Unknown building"):
        api.get_data_availability(23931)


@pytest.mark.parametrize("start, end, expected", [
    ("2016-02-01", "2016-03-01", 2784),
    ("2016-03-01", "2016-04-01", 2972),
    ("2016-10-01", "2016-11-01", 2980),
])
def test_full_month_coverage_handles_leap_year_and_dst(empty_db, home, start, end, expected):
    times = pd.date_range(start, end, freq="15min", inclusive="left", tz="Europe/Berlin")
    store(empty_db, home.meters()[0], times)

    result = get_data_availability.invoke({"building_id": home.id})
    month = result["months"][0]
    assert result["available_month_count"] == 1
    assert result["fully_covered_month_count"] == 1
    assert month["stored_intervals"] == expected
    assert month["expected_intervals"] == expected
    assert month["completeness"] == 1.0
    assert month["full_month"]
    assert result["latest_stored_interval_end_exclusive"] == pd.Timestamp(end, tz="Europe/Berlin").isoformat()
    json.dumps(result, allow_nan=False)


def test_months_use_berlin_dates_and_do_not_fill_missing_months(empty_db, home):
    times = pd.to_datetime([
        "2016-01-31T22:45:00Z",  # January 31, 23:45 Berlin
        "2016-01-31T23:00:00Z",  # February 1, 00:00 Berlin
        "2016-03-31T22:00:00Z",  # April 1, 00:00 Berlin
    ], utc=True)
    store(empty_db, home.meters()[0], times)

    result = api.get_data_availability(home.id)
    assert [month["month"] for month in result["months"]] == ["2016-01", "2016-02", "2016-04"]
    assert result["available_month_count"] == 3
    assert result["fully_covered_month_count"] == 0
    assert all(month["stored_intervals"] == 1 for month in result["months"])
    assert all(not month["full_month"] for month in result["months"])
    assert result["first_stored_interval_start"] == "2016-01-31T23:45:00+01:00"
    assert result["latest_stored_interval_start"] == "2016-04-01T00:00:00+02:00"


def test_duplicate_times_across_zones_count_once_and_other_kinds_are_excluded(empty_db, home):
    home.add_zone(Zone("Second")).add_meter(EnergyMeter())
    home.zones[0].add_meter(Meter("gas", "kWh"))
    database.save_building(empty_db, home)
    electricity_times = pd.date_range("2016-02-01", periods=4, freq="15min", tz="Europe/Berlin")
    for meter in home.meters("electricity"):
        store(empty_db, meter, electricity_times)
    store(empty_db, home.meters("gas")[0], pd.date_range("2016-01-01", periods=4, freq="15min", tz="Europe/Berlin"))

    result = api.get_data_availability(home.id)
    assert len(result["months"]) == 1
    assert result["months"][0]["month"] == "2016-02"
    assert result["months"][0]["stored_intervals"] == 4
    assert result["months"][0]["completeness"] == round(4 / 2784, 4)


def test_agent_registers_availability_tool(monkeypatch):
    from advisor import agent

    assemble = Mock()
    monkeypatch.setattr(agent, "create_agent", assemble)
    monkeypatch.setattr(agent, "get_model", Mock())
    agent.get_agent()
    assert "get_data_availability" in [tool.name for tool in assemble.call_args.kwargs["tools"]]

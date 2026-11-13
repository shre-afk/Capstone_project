"""test_api.py - the service layer the dashboard and the advisor use

All tests use the fake office from conftest.py
- week 1 = 348 kWh
- week 2 = 294 kWh
"""

import pytest

from backend.analysis import api

# start included, end excluded
WEEK1 = ("2016-03-07", "2016-03-14")
WEEK2 = ("2016-03-14", "2016-03-21")


def test_list_buildings(office):
    buildings = api.list_buildings()

    assert len(buildings) == 1
    assert buildings[0]["name"] == "Test Office"
    assert buildings[0]["type"] == "business"


def test_kpis_of_week_1(office):
    # *WEEK1 unpacks the pair into start, end
    kpis = api.get_kpis(office, *WEEK1)

    assert kpis["energy_kwh"] == 348.0
    assert kpis["cost_eur"] == 104.4        # 348 x 0.30
    assert kpis["completeness"] == 1.0      # no reading is missing


def test_daily_chart_data(office):
    daily = api.get_timeseries(office, *WEEK1, freq="1D")["Whole building"]

    # Monday to Friday 60 kWh each
    # Saturday and Sunday 24 kWh each
    assert list(daily) == [60.0, 60.0, 60.0, 60.0, 60.0, 24.0, 24.0]


def test_savings_of_week_2(office):
    # week 2 is compared with the week just before it
    savings = api.get_savings(office, *WEEK2)

    assert savings["previous_kwh"] == 348.0
    assert savings["saved_kwh"] == 54.0     # 348 - 294
    assert savings["change_pct"] == -15.5


def test_saving_energy_at_night_raises_the_score(office):
    # week 2 used less energy while closed
    # - the score must reward that
    week_1 = api.get_score(office, *WEEK1)
    week_2 = api.get_score(office, *WEEK2)

    assert week_2["score"] > week_1["score"]
    assert week_1["grade"] in ["A", "B", "C", "D", "E"]


def test_unknown_building_gives_a_clear_error(office):
    # match= also checks the wording of the message
    with pytest.raises(ValueError, match="Unknown building"):
        api.get_kpis(99, *WEEK1)

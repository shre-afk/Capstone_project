"""api.py - Service Layer of the Database & Analysis section (ONE door to our data)
v0 - functions return hard-coded example data in the agreed shape so @team can build on it now

@team the Dashboard and the AI Advisor call ONLY these functions and never the database
- building_id = an int from list_buildings()
- start, end = a date & time --> w/o a time zone = Berlin local time

- units: energy -> kWh | power -> kW | money -> EUR | CO2 -> kg
- times come back in Berlin local time
"""

import pandas as pd

from backend import settings

# Which buildings exist
def list_buildings():
    return [
        {"id": 1, "name": "Home 1", "type": "home", "floor_area_m2": 140.0},
        {"id": 4, "name": "Business 1", "type": "business", "floor_area_m2": 2500.0},
    ]


# What is happening right now (per zone)
def get_latest(building_id):
    return {
        "last_reading": "2016-12-01T09:15:00+01:00",
        "power_kw": 38.4,
        "zones": [{"zone": "Whole building", "power_kw": 38.4}],
    }


# How much energy, EUR, CO2 in a period
def get_kpis(building_id, start, end):
    # eui -> energy-use intensity (kWh per m2)
    # completeness -> share of expected readings that exist
    return {
        "energy_kwh": 19850.4, "cost_eur": 5955.12, "co2_kg": 7543.2,
        "eui_kwh_m2_yr": 96.6, "period_days": 30.0, "completeness": 0.998,
    }


# Energy per hour/day, one column per zone (ready for a chart)
def get_timeseries(building_id, start, end, freq="1h"):
    first = pd.Timestamp(start, tz=settings.LOCAL_TZ)
    last = pd.Timestamp(end, tz=settings.LOCAL_TZ)

    # builds a list of timestamps from start to end for every freq
    index = pd.date_range(first, last, freq=freq, inclusive="left", name="ts")

    # rows are times, one column per zone
    return pd.DataFrame({"Whole building": 27.5}, index=index)


# How much did we save comparing this period v/s the period (same length) just before
def get_savings(building_id, start, end):
    return {
        "energy_kwh": 19850.4, "previous_kwh": 21012.9, "saved_kwh": 1162.5,
        "saved_eur": 348.75, "saved_co2_kg": 441.8, "change_pct": -5.5,
    }


# Sustainability score 0-100 and grade A-E
def get_score(building_id, start, end):
    return {
        "score": 61.2, "grade": "C", "intensity_points": 53.4, "after_hours_points": 72.9,
        "eui_kwh_m2_yr": 96.6, "benchmark_kwh_m2_yr": 100,
        "after_hours_energy_share": 0.174, "closed_time_share": 0.643,
    }



# Expected energy per hour for the next days
def get_forecast(building_id, days=7):
    first = pd.Timestamp("2016-12-01 00:00", tz=settings.LOCAL_TZ)
    index = pd.date_range(first, periods=days * 24, freq="h")
    
    return pd.DataFrame({"forecast_kwh": 27.5}, index=index)




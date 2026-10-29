"""api.py - Service Layer of the Database & Analysis section (ONE door to our data)
v0 - functions return hard-coded example data in the agreed shape so @team can build on it now
v1 - functions return correct data

@team the Dashboard and the AI Advisor call ONLY these functions and never the database
- building_id = an int from list_buildings()
- start, end = a date & time --> w/o a time zone = Berlin local time

- units: energy -> kWh | power -> kW | money -> EUR | CO2 -> kg
- times come back in Berlin local time
"""
from contextlib import closing

import pandas as pd

from backend import settings
from backend.analysis import calc
from backend.db import database
from backend.models import make_building


# ---------- INTERNAL FUNCTIONS (@team DO NOT CALL THESE) ----------

def _local(ts):
    """make any time = Berlin time"""
    ts = pd.Timestamp(ts)
    if ts.tzinfo is None:
        # no time zone -> Berlin Time
        return ts.tz_localize(settings.LOCAL_TZ)
    else:
        # already has time zone -> show same moment on Berlin clock
        return ts.tz_convert(settings.LOCAL_TZ)


def _building(con, building_id):
    """Database row -> Home / Business / PublicBuilding object
        Unknown id -> ValueError
    """
    row = database.load_building(con, building_id)
    if row is None:
        raise ValueError(f"Unknown building id {building_id}")

    building_type = row["type"]
    name = row["name"]
    floor_area = row["floor_area_m2"]

    return make_building(building_type, name, floor_area)


def _readings(building_id, start, end):
    """-> (building, readings table in (local time: start, end))"""
    start = _local(start)
    end = _local(end)
    if start >= end:
        raise ValueError(f"start ({start}) must be before end ({end})")

    # open database; 'closing' shuts it again automatically even after an error
    with closing(database.connect()) as con:
        building = _building(con, building_id)
        df = database.load_readings(con, building_id, start, end)

    # database times = UTC --> show them on Berlin clock
    df["ts"] = df["ts"].dt.tz_convert(settings.LOCAL_TZ)    # dt -> reach time functions of a whole column of times

    return building, df, start, end


def _energy(building_id, start, end):
    """-> sum(kWh per 15-min interval) of building with all zones from start to end"""
    building, df, start, end = _readings(building_id, start, end)

    # one row per zone per time -> add the zones together: one value at a time
    rows_by_time = df.groupby("ts")
    kwh = rows_by_time["value"].sum()

    return building, kwh, start, end


def _days(start, end):
    """Length of period in days"""
    duration = end - start
    one_day = pd.Timedelta(days=1)

    return (duration / one_day)





# ---------- CORE FUNCTIONS (@team USE THESE) ----------

# Which buildings exist
def list_buildings():
    """-> List of building dicts: id, name, type, floor_area_m2"""
    with closing(database.connect()) as con:
        buildings = database.list_buildings(con)

    return buildings


# What is happening right now (per zone)
def get_latest(building_id):
    """-> Newest reading time, total_power (kW) & power per zone"""
    # ONLY check if building exists
    with closing(database.connect()) as con:
        _building(con, building_id)

        # Ask for newest reading from last (incl) to last+15min (excl)
        last = database.latest_ts(con, building_id)
        if last is None:        # no readings yet -> empty answer, same shape
            return {
                "last_reading": None, 
                "power_kw": 0.0, 
                "zones": []
            }

        next_interval = last + pd.Timedelta("15min")
        df = database.load_readings(con, building_id, last, next_interval)

    # Find power for each zone
    zones = []
    for row in df.itertuples(): # loop over table row by row
        power = row.value * 4   # kWh in 15-min x 4 = kW
        zones.append({"zone": row.zone, "power_kw": round(power, 2)})

    # Find combined power from all zones
    total_power = 0
    for zone in zones:
        total_power += zone["power_kw"]

    last_berlin = last.tz_convert(settings.LOCAL_TZ)
    return {
        "last_reading": last_berlin.isoformat(),
        "power_kw": round(total_power, 2),
        "zones": zones,
    }


# How much energy, EUR, CO2 in a period
def get_kpis(building_id, start, end):
    """-> dict of headline numbers for one building & period"""
    building, kwh, start, end = _energy(building_id, start, end)
    
    days = _days(start, end)
    energy = calc.total_kwh(kwh)

    prices = settings.CONFIG["prices"]
    eur_per_kwh = prices["eur_per_kwh"]
    co2_per_kwh = prices["co2_kg_per_kwh"]

    cost = calc.cost_eur(energy, eur_per_kwh)
    co2 = calc.co2_kg(energy, co2_per_kwh)

    readings_we_have = len(kwh)
    # completeness -> share of raw data used
    data_portion = calc.completeness(readings_we_have, days)

    # eui -> energy-use intensity (kWh per m2)
    eui = calc.eui_per_year(energy, building.floor_area_m2, days)
    
    return {
        "energy_kwh": energy,
        "cost_eur": cost,
        "co2_kg": co2,
        "eui_kwh_m2_yr": eui,
        "period_days": round(days, 2),
        "completeness": data_portion,
    }


# Energy per hour/day, one column per zone (data for chart plot)
def get_timeseries(building_id, start, end, freq="1h"):
    """-> table: one row per hour/day, one column per zone, kWh values"""
    building, df, start, end = _readings(building_id, start, end)

    # long table (ts, zone, value) -> wide table: one column per zone
    wide = df.pivot_table(index="ts", columns="zone", values="value", aggfunc="sum")   # aggfunc="sum" => if 2 rows land in same cell, add them

    # 15-min rows -> hourly/daily buckets (bucket w/o data = empty Not 0)
    # resample = turn 15-min rows into hourly rows + add values (if at least 1 value available)
    per_bucket = wide.resample(freq).sum(min_count=1)
     
    return per_bucket.round(3) 


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




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


# Available historical electricity dates
def get_data_availability(building_id):
    """Stored electricity dates and monthly timestamp coverage in Berlin time."""
    with closing(database.connect()) as con:
        building = _building(con, building_id)
        times = database.reading_timestamps(con, building_id).tz_convert(settings.LOCAL_TZ)

    months = []
    for month, count in times.strftime("%Y-%m").value_counts(sort=False).items():
        start = pd.Timestamp(f"{month}-01", tz=settings.LOCAL_TZ)
        end = start + pd.DateOffset(months=1)
        expected = int((end - start) / pd.Timedelta(minutes=15))
        months.append({
            "month": month,
            "start": start.isoformat(),
            "end_exclusive": end.isoformat(),
            "stored_intervals": int(count),
            "expected_intervals": expected,
            "completeness": round(int(count) / expected, 4),
            "full_month": int(count) == expected,
        })

    return {
        "status": "ok" if len(times) else "no_data",
        "building_id": building_id,
        "building_name": building.name,
        "measurement": "grid_import",
        "timezone": settings.LOCAL_TZ,
        "first_stored_interval_start": times[0].isoformat() if len(times) else None,
        "latest_stored_interval_start": times[-1].isoformat() if len(times) else None,
        "latest_stored_interval_end_exclusive": (
            (times[-1] + pd.Timedelta(minutes=15)).isoformat() if len(times) else None
        ),
        "available_month_count": len(months),
        "fully_covered_month_count": sum(month["full_month"] for month in months),
        "months": months,
        "notes": [
            "Only months with stored electricity readings are listed; a listed month may be partial.",
            "Coverage counts distinct timestamps with at least one electricity-meter reading; it does not verify every zone.",
            "Stored readings may include reconstructed source intervals; coverage does not establish source quality.",
        ],
    }


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


# How much energy, EUR, CO2 in a period (KPI = Key Performance Indicator)
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


def _usage_intervals(building_id, start, end):
    """Complete building totals on a regular 15-minute grid, preserving gaps."""
    building, df, start, end = _readings(building_id, start, end)
    if any(ts.minute % 15 or ts.second or ts.microsecond or ts.nanosecond
           for ts in (start, end)):
        raise ValueError("Usage analysis requires boundaries aligned to 15-minute intervals")

    expected = pd.date_range(start, end, freq="15min", inclusive="left")
    if df.empty:
        energy = pd.Series(float("nan"), index=expected, dtype=float)
    else:
        zones = df.pivot_table(index="ts", columns="zone", values="value", aggfunc="sum")
        zones = zones.reindex(expected)
        # If an observed zone is missing, do not count its partial building total.
        energy = zones.sum(axis=1, min_count=len(zones.columns))
    return building, energy, start, end


def _usage_metrics(energy):
    """Observed energy and coverage, preserving missing readings."""
    expected = len(energy)
    observed = int(energy.count())
    total = float(energy.sum()) if observed or expected == 0 else None
    return {
        "energy_kwh": round(total, 3) if total is not None else None,
        "average_power_kw": round(total / (observed / 4), 3) if observed else None,
        "expected_intervals": expected,
        "observed_intervals": observed,
        "completeness": round(observed / expected, 4) if expected else None,
    }


def get_peak_usage(building_id, start, end, top_n=5):
    """Rank complete hourly/calendar-day import buckets in Berlin time."""
    if not 1 <= top_n <= 10:
        raise ValueError("top_n must be between 1 and 10")
    building, energy, start, end = _usage_intervals(building_id, start, end)
    coverage = _usage_metrics(energy)
    if coverage["observed_intervals"] == 0:
        return {"status": "no_data", "building_id": building_id,
                "message": "No readings exist for this building in the requested period."}

    # Four observed quarters are required for each full hour.
    hourly = energy.resample("1h").sum(min_count=4)
    daily = energy.resample("1D").sum(min_count=1)
    day_counts = energy.notna().astype(int).resample("1D").sum()
    # Calendar days have 92, 96 or 100 quarter-hours across Berlin DST changes.
    expected_day_counts = pd.Series([
        len(pd.date_range(day, day + pd.DateOffset(days=1), freq="15min", inclusive="left"))
        for day in daily.index
    ], index=daily.index)
    daily = daily.where(day_counts == expected_day_counts)
    complete_hours = hourly.dropna()
    complete_days = daily.dropna()
    profile = complete_hours.groupby(complete_hours.index.hour).agg(["mean", "count"])
    profile = profile.sort_values("mean", ascending=False, kind="stable").head(top_n)

    return {
        "status": "ok" if not complete_hours.empty else "insufficient_data",
        "building_id": building_id, "building_name": building.name,
        "measurement": "grid_import",
        "period": {"start": start.isoformat(), "end_exclusive": end.isoformat(),
                   "timezone": settings.LOCAL_TZ},
        "coverage": coverage,
        "complete_hours": len(complete_hours), "excluded_hours": int(hourly.isna().sum()),
        "complete_days": len(complete_days), "excluded_days": int(daily.isna().sum()),
        "top_hours": [
            {"start": ts.isoformat(), "end_exclusive": (ts + pd.Timedelta(hours=1)).isoformat(),
             "energy_kwh": round(float(value), 3), "average_power_kw": round(float(value), 3)}
            for ts, value in complete_hours.nlargest(top_n).items()
        ],
        "top_days": [
            {"start": ts.isoformat(), "end_exclusive": (ts + pd.DateOffset(days=1)).isoformat(),
             "energy_kwh": round(float(value), 3),
             "duration_hours": (ts + pd.DateOffset(days=1) - ts) / pd.Timedelta(hours=1)}
            for ts, value in complete_days.nlargest(top_n).items()
        ],
        "highest_average_clock_hours": [
            {"hour_of_day": int(hour), "mean_hourly_kwh": round(float(row["mean"]), 3),
             "complete_hours_used": int(row["count"])}
            for hour, row in profile.iterrows()
        ],
        "notes": [
            "Only complete hours and complete calendar days are ranked; boundary buckets may be excluded.",
            "Peaks are the highest observed complete buckets, not guaranteed full-period peaks if data is missing.",
            "Hourly power is an average over one hour, not instantaneous or 15-minute maximum demand.",
            "Clock-hour means describe observed complete hours; DST days may be 23 or 25 hours long.",
            "Coverage checks currently observed zones; source interpolation flags are unavailable.",
            "High usage alone does not establish an anomaly or equipment fault.",
        ],
    }


# How much did we save comparing this period v/s the period (same length) just before
def get_savings(building_id, start, end):
    """-> energy_now vs energy_before (same period)"""
    # Energy of THIS period
    building, kwh_now, start, end = _energy(building_id, start, end)

    # period before (same length)
    length = end - start
    before_start = start - length

    # Energy of period BEFORE
    building, kwh_before, _, _ = _energy(building_id, before_start, start)


    # Totals & Difference
    energy_now = calc.total_kwh(kwh_now)
    energy_before = calc.total_kwh(kwh_before)
    energy_saved = round(energy_before - energy_now, 2)     # +ve = used less | -ve = used more
    change_percent = calc.change_pct(energy_now, energy_before)

    # Worth of saving
    prices = settings.CONFIG["prices"]
    saved_eur = calc.cost_eur(energy_saved, prices["eur_per_kwh"])
    saved_co2 = calc.co2_kg(energy_saved, prices["co2_kg_per_kwh"])

    return {
        "energy_kwh": energy_now,
        "previous_kwh": energy_before,
        "saved_kwh": energy_saved,
        "saved_eur": saved_eur,
        "saved_co2_kg": saved_co2,
        "change_pct": change_percent,
    }


# Sustainability score 0-100 and grade A-E
def get_score(building_id, start, end):
    """Sustainability score 0-100 & Grade A-E"""

    building, kwh, start, end = _energy(building_id, start, end)
    if kwh.empty:
        raise ValueError(f"No readings for building {building_id} in this period")

    # P1: Intensity
    energy = calc.total_kwh(kwh)
    days = _days(start, end)

    eui = calc.eui_per_year(energy, building.floor_area_m2, days)
    benchmark = settings.CONFIG["benchmarks"][building.building_type]   # e.g. "business" -> 100
    
    intensity = calc.intensity_points(eui, benchmark)


    # P2: After-hours
    energy_share, time_share = calc.after_hours(kwh, building.is_open)
    after_hours = calc.after_hours_points(energy_share, time_share)

    # Combine with the weights from config.toml
    parts = {"intensity": intensity, "after_hours": after_hours}
    weights = settings.CONFIG["score"]["weights"]
    score = calc.sustainability_score(parts, weights)

    grd = calc.grade(score)

    return {
        "score": score,
        "grade": grd,
        "intensity_points": intensity,
        "after_hours_points": after_hours,
        "eui_kwh_m2_yr": eui,
        "benchmark_kwh_m2_yr": benchmark,
        "after_hours_energy_share": round(energy_share, 3),
        "closed_time_share": round(time_share, 3),
    }



# Expected energy per hour for the next days
def get_forecast(building_id, days=7):
    """-> table: one row per future hour, column forecast_kwh"""

    # Find the newest reading (and check id exists)
    with closing(database.connect()) as con:
        _building(con, building_id)     # unknown id -> ValueError
        last = database.latest_ts(con, building_id)

    if last is None:
        raise ValueError(f"No readings for building {building_id}")

    # Load the last 4 weeks, up including newest reading
    four_weeks_ago = last - pd.Timedelta(weeks=4)
    just_after_last = last + pd.Timedelta("15min")  # end is excluded -> +15 min keeps 'last'
    building, kwh, _, _ = _energy(building_id, four_weeks_ago, just_after_last)

    # 15-min values -> hourly values (drop hours w/ no data -> avoid spoiling average)
    hourly = kwh.resample("1h").sum(min_count=1)
    hourly = hourly.dropna()


    forecast = calc.forecast_same_hour(hourly, days=days)

    # Series data -> one-column table
    return forecast.to_frame()



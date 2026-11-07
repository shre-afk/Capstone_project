"""opsd.py - loads the OPSD household dataset into our database
    RUN IT ONCE ->> Run: python -m backend.ingestion.opsd
"""

import pandas as pd

from backend import settings
from backend.db import database
from backend.models import EnergyMeter, Zone, make_building

INTERVAL = pd.Timedelta("15min")

# Load selected meter columns indexed by UTC timestamp.
def read_opsd(csv_path, columns):
    """Read selected columns; meter values are cumulative kWh."""
    df = pd.read_csv(csv_path, usecols = ["utc_timestamp", *columns])

    df["utc_timestamp"] = pd.to_datetime(df["utc_timestamp"], utc=True)
    df = df.set_index("utc_timestamp")
    return df

# Convert cumulative meter totals to interval consumption.
def to_intervals(totals):
    """Convert cumulative meter totals to 15-minute kWh values."""
    totals = totals.dropna()

    energy_used = totals.diff()

    # Keep differences only when readings are 15 minutes apart.
    times = totals.index.to_series()
    time_gap = times.diff()

    is_one_step = time_gap == INTERVAL
    energy_used = energy_used[is_one_step]
    energy_used.index = energy_used.index - INTERVAL

    return energy_used


# Reject negative or implausibly high readings.
def validate(used, max_kwh):
    """Return valid readings and the number rejected."""
    ok = (used >= 0) & (used <= max_kwh)
    good_values = used[ok]
    num_rejected = int((~ok).sum())
    return good_values, num_rejected


# Build a building, zone, and meter from its configuration.
def build_from_config(entry):
    """Convert a buildings config entry to a building with one meter."""
    building_type = entry["type"]
    name = entry["name"]
    floor_area = entry["floor_area_m2"]
    csv_column = entry["column"]

    building = make_building(building_type, name, floor_area)
    zone = Zone("Whole building")
    building.add_zone(zone)
    meter = EnergyMeter(source=csv_column)
    zone.add_meter(meter)

    return building


# Prepare validated interval readings for one building and date range.
def prepare(raw, entry, start, end):
    """Return valid 15-minute kWh values and the number rejected."""
    column_name = entry["column"]
    totals = raw[column_name]

    energy_used = to_intervals(totals)

    # Use a start-inclusive, end-exclusive range.
    after_start = energy_used.index >= start
    before_end = energy_used.index < end
    energy_used = energy_used[after_start & before_end]

    building_type = entry["type"]
    all_limits = settings.CONFIG["validation"]["max_kwh_per_interval"]
    max_kwh = all_limits[building_type]

    good_values, num_rejected = validate(energy_used, max_kwh)

    return good_values, num_rejected


# Load the configured historical data into the database.
def run():
    data_settings = settings.CONFIG["data"]
    all_buildings = settings.CONFIG["buildings"]

    start = pd.Timestamp(data_settings["start"], tz=settings.LOCAL_TZ)
    stop = pd.Timestamp(data_settings["replay_from"], tz=settings.LOCAL_TZ)

    csv_file = settings.ROOT / data_settings["csv_path"]
    columns_needed = []
    for entry in all_buildings:
        columns_needed.append(entry["column"])

    print(f"Reading {data_settings['csv_path']} ...")
    raw = read_opsd(csv_file, columns_needed)

    con = database.connect()
    database.create_tables(con)

    for entry in all_buildings:
        building = build_from_config(entry)
        database.save_building(con, building)

        good_values, num_rejected = prepare(raw, entry, start, stop)

        meter = building.meters("electricity")[0]
        added = database.save_readings(con, meter.id, good_values)

        print(f"{building.name:<11} id={building.id} {added:6d} new readings {num_rejected} rejected")

    con.close()
    print("Done ->", settings.DB_PATH)

# Run the import only when invoked as a module or script.
if __name__ == "__main__":
    run()

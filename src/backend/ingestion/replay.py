"""replay.py - makes the historical data "live" --> feeds one 15-min reading at a time
 
Run:  python -m backend.ingestion.replay      
      (stop with Ctrl+C, start again to continue)
"""

import time

import pandas as pd

from backend import settings
from backend.db import database
from backend.ingestion import opsd

def run(pause = None):
    # ----- settings -----
    data_settings = settings.CONFIG["data"]
    all_buildings = settings.CONFIG["buildings"]

    # seconds to wait bet. 2 readings: from config.toml unless given
    if pause is None:
        pause = data_settings["replay_seconds"]

    start = pd.Timestamp(data_settings["replay_from"], tz=settings.LOCAL_TZ)
    end = pd.Timestamp(data_settings["end"], tz=settings.LOCAL_TZ)


    # ----- Read CSV (same as opsd.py) -----
    csv_file = settings.ROOT / data_settings["csv_path"]
    columns_needed = []
    for entry in all_buildings:
        columns_needed.append(entry["column"])
    raw = opsd.read_opsd(csv_file, columns_needed)

    con = database.connect()


    # ----- Prepare Dec readings for every meter -----
    upcoming = {}                                     # meter id -> December readings
    for entry in all_buildings:
        building = opsd.build_from_config(entry)
        database.save_building(con, building)         # buildings already exist -> just fills in the ids
        good_values, num_rejected = opsd.prepare(raw, entry, start, end)
        meter = building.meters()[0]
        upcoming[meter.id] = good_values


    # ----- Which times still have to be sent -----
    all_times = set()
    for readings in upcoming.values():
        for ts in readings.index:
            all_times.add(ts)

    stamps = sorted(all_times)  # oldest first

    # skip what is already in database (continue after Ctrl+C)
    last = database.latest_ts(con)
    if last is not None:
        stamps = [ts for ts in stamps if ts > last]

    print(f"Replaying {len(stamps)} intervals, one every {pause} s. Ctrl+C to stop.")


    # ----- Send one time slot after another -----
    try:
        for ts in stamps:
            for meter_id, readings in upcoming.items():
                if ts in readings.index:                # this meter has a value at this time
                    one_reading = readings.loc[[ts]]    # [[ ]] -> stays a 1-row series
                    database.save_readings(con, meter_id, one_reading)

            berlin_time = ts.tz_convert(settings.LOCAL_TZ)
            print("live:", berlin_time.strftime("%a %d %b %Y %H:%M"))
            time.sleep(pause)

    except KeyboardInterrupt:
        print("Replay stopped")

    finally:
        con.close()


if __name__ == "__main__":
    run()

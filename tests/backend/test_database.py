"""test_database.py - saving and loading with SQLite

Every test that asks for empty_db gets a brand-new database (see conftest.py)
"""

import pandas as pd

from backend.db import database
from backend.models import EnergyMeter, Home, Zone


def make_home():
    """A home with one zone and one meter - not saved yet"""
    home = Home("Test Home", 120)
    zone = home.add_zone(Zone("Whole building"))
    zone.add_meter(EnergyMeter(source="col"))
    return home


def three_readings():
    """Readings at 00:00, 00:15 and 00:30 on 1 January 2016 (Berlin time)"""
    times = pd.date_range("2016-01-01", periods=3, freq="15min", tz="Europe/Berlin")
    return pd.Series([0.1, 0.2, 0.3], index=times)


def test_times_are_stored_as_utc_text():
    # Berlin is one hour ahead of UTC in winter
    # so midnight in Berlin = 23:00 UTC the evening before
    midnight = pd.Timestamp("2016-01-01 00:00", tz="Europe/Berlin")
    assert database.ts_text(midnight) == "2015-12-31T23:00:00Z"


def test_saving_a_building_gives_it_an_id(empty_db):
    home = make_home()
    database.save_building(empty_db, home)

    # the id comes from the database
    assert home.id is not None
    assert len(database.list_buildings(empty_db)) == 1


def test_the_same_reading_is_never_saved_twice(empty_db):
    home = make_home()
    database.save_building(empty_db, home)
    meter_id = home.meters()[0].id

    # first time - 3 new rows
    assert database.save_readings(empty_db, meter_id, three_readings()) == 3

    # second time - 0 new rows
    # INSERT OR IGNORE skips readings that already exist
    assert database.save_readings(empty_db, meter_id, three_readings()) == 0


def test_loading_includes_start_but_not_end(empty_db):
    home = make_home()
    database.save_building(empty_db, home)
    database.save_readings(empty_db, home.meters()[0].id, three_readings())

    # ask for 00:00 up to 00:30
    # the reading at 00:30 is the end, so it is left out
    start = pd.Timestamp("2016-01-01 00:00", tz="Europe/Berlin")
    end = pd.Timestamp("2016-01-01 00:30", tz="Europe/Berlin")
    table = database.load_readings(empty_db, home.id, start, end)

    assert list(table["value"]) == [0.1, 0.2]

"""conftest.py - shared test helpers (fixtures)

pytest reads this file by itself
A test asks for a fixture by using its name as a parameter, e.g. def test_x(office)

Nothing here touches the real energy.db
Every test gets its own empty database in a temporary folder
"""

import pandas as pd
import pytest

from backend import settings
from backend.db import database
from backend.models import Business, EnergyMeter, Zone


@pytest.fixture
def empty_db(tmp_path, monkeypatch):
    """A new, empty database just for one test"""

    # tmp_path = a temporary folder that pytest deletes afterwards
    # monkeypatch points the whole backend at the test database
    # - also every connection that api.py opens by itself
    monkeypatch.setattr(settings, "DB_PATH", str(tmp_path / "test.db"))

    con = database.connect()
    database.create_tables(con)
    yield con           # the test runs here
    con.close()         # clean up when the test is done


@pytest.fixture
def office(empty_db):
    """A fake office with two weeks of readings -> gives back its building id

    Numbers chosen so every result can be worked out by hand
    - 1000 m2, open Monday to Friday 07:00-19:00
    - open: 1.0 kWh every 15 min
    - closed: 0.25 kWh in week 1, 0.125 kWh in week 2 (lights switched off at night)
    - week 1 = 348 kWh
    - week 2 = 294 kWh
    """

    # one building -> one zone -> one electricity meter
    building = Business("Test Office", 1000)
    zone = building.add_zone(Zone("Whole building"))
    zone.add_meter(EnergyMeter(source="fake"))
    database.save_building(empty_db, building)

    # 14 days x 96 quarter hours, starting Monday 7 March 2016
    times = pd.date_range("2016-03-07", periods=14 * 96, freq="15min", tz="Europe/Berlin")
    week_2_starts = times[0] + pd.Timedelta(days=7)

    values = []
    for ts in times:
        if building.is_open(ts):
            values.append(1.0)
        elif ts < week_2_starts:
            values.append(0.25)
        else:
            values.append(0.125)

    meter_id = building.meters()[0].id
    database.save_readings(empty_db, meter_id, pd.Series(values, index=times))
    return building.id

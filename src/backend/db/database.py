"""database.py - everything that talks to SQLite lives only here"""

import sqlite3

import pandas as pd

from backend import settings

TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"    # how times are stored = UTC text format (e.g. 2016-11-01T09:15:00Z | Z = UTC)

SCHEMA = """
CREATE TABLE IF NOT EXISTS building (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    type            TEXT NOT NULL,
    floor_area_m2   REAL NOT NULL CHECK (floor_area_m2 > 0)
);

CREATE TABLE IF NOT EXISTS zone (
    id              INTEGER PRIMARY KEY,
    building_id     INTEGER NOT NULL REFERENCES building(id),
    name            TEXT NOT NULL,
    UNIQUE (building_id, name)
);

CREATE TABLE IF NOT EXISTS meter (
    id              INTEGER PRIMARY KEY,
    zone_id         INTEGER NOT NULL REFERENCES zone(id),
    kind            TEXT NOT NULL,
    unit            TEXT NOT NULL,
    source          TEXT NOT NULL DEFAULT '',
    UNIQUE (zone_id, kind, source)
);

CREATE TABLE IF NOT EXISTS reading (
    meter_id        INTEGER NOT NULL REFERENCES meter(id),
    ts_utc          TEXT NOT NULL,
    value           REAL NOT NULL,
    PRIMARY KEY (meter_id, ts_utc)
);
"""


def connect(path = None):
    """Open the database file (if not exist then create)"""
    con = sqlite3.connect(path or settings.DB_PATH)
    con.row_factory = sqlite3.Row               # rows now behave like dicts = row["name"] instead of row[1]
    con.execute("PRAGMA foreign_keys = ON")     # SQLite only checks REFERENCES when asked

    return con

# Used to build tables in the 'SCHEMA' defined format
def create_tables(con):
    con.executescript(SCHEMA)

def ts_text(ts):
    """Convertor: Any time (with known timezone) -> UTC time -> text format"""

    # turns data passed is in same object kind -> make sure the conversions below works
    as_pandas_time = pd.Timestamp(ts)

    # convert clock time to UTC
    as_utc_time = as_pandas_time.tz_convert("UTC")

    # string from time --> convert the time data to text in the specified format
    as_utc_text = as_utc_time.strftime(TS_FORMAT)

    return as_utc_text



def save_building(con, building):
    """Save a Building with its zones and meters
        Safe to call twice
        Fills in the X.id fields 
    """

    # In 'building' table, create a building entry if same building does not already exist
    con.execute(
        "INSERT OR IGNORE INTO building (name, type, floor_area_m2) VALUES (?, ?, ?)",
        (building.name, building.building_type, building.floor_area_m2),
        )

    # The building.id = the database id 
    # --> Find the building row entry & save row id to building.id
    row = con.execute(
        "SELECT id FROM building WHERE name = ?", (building.name,)
    ).fetchone()

    building.id = row["id"]     # row is a dict {"id" : <building_id>}

    # Fill in the 'zone' table and ignore any duplicate entries
    for zone in building.zones:
        con.execute(
            "INSERT OR IGNORE INTO zone (building_id, name) VALUES (?, ?)", (building.id, zone.name)
        )

        # zone.id = database id
        zone.id = con.execute(
            "SELECT id FROM zone WHERE building_id = ? AND name = ?", (building.id, zone.name)
        ).fetchone()["id"]      # row dict {"id" : <zone_id>}

        # Fill in the 'meter' table and ignore any duplicate entries
        for meter in zone.meters:
            con.execute(
                "INSERT OR IGNORE INTO meter (zone_id, kind, unit, source) VALUES (?, ?, ?, ?)",
                (zone.id, meter.kind, meter.unit, meter.source),
            )

            # meter.id = database id
            meter.id = con.execute(
                "SELECT id FROM meter WHERE zone_id = ? AND kind = ? AND source = ?",
                (zone.id, meter.kind, meter.source),
            ).fetchone()["id"]  # row dict {"id" : <meter_id>}

    # make database changes permanent
    con.commit()
    return building.id



def save_readings(con, meter_id, values):
    """Save meter readings to database"""
    
    # Turn all times into UTC text
    # vector values.index -> time labels w/o numbers
    utc_times = values.index.tz_convert("UTC").strftime(TS_FORMAT)

    # Package rows to be added (one tuple per row)
    rows = []
    for time_text, number in zip(utc_times, values):
        rows.append((meter_id, time_text, float(number)))   # float(x) -> numpy to plain float so database understands

    # Write to database
    changes_before = con.total_changes
    con.executemany(
        "INSERT OR IGNORE INTO reading (meter_id, ts_utc, value) VALUES (?, ?, ?)", rows
    )

    con.commit()

    # Number of changes to database
    changes_after = con.total_changes       # counts every row the connection (con) has changed so far
    new_rows = changes_after - changes_before

    return new_rows



def list_buildings(con):
    """Return sorted dict of buildings from database"""
    rows = con.execute("SELECT id, name, type, floor_area_m2 FROM building ORDER BY id").fetchall()
    # return a dict of all buildings
    return [dict(row) for row in rows]


def load_building(con, building_id):
    """One building as a dict OR None if the id does not exist"""
    # Search database for building
    row = con.execute(
        "SELECT id, name, type, floor_area_m2 FROM building WHERE id = ?", (building_id,)
    ).fetchone()

    # return building entry as dict if found else None
    return dict(row) if row else None


def load_readings(con, building_id, start, end, kind = "electricity"):
    """All readings of one building between start (including) and end (excluding)"""

    # Search database for readings from a specific building

    # reading:  meter_id, ts_utc, value     ← knows the meter
    # meter:    id, zone_id, kind           ← knows the zone
    # zone:     id, building_id, name       ← knows the building

    # Therefore, reading for a building: building -> zone -> meter -> readings
    # we can glue the 3 tables wherever the ids match (JOIN)
    
    sql = """
        SELECT r.ts_utc AS ts, z.name AS zone, r.value AS value
        FROM reading r
        JOIN meter m ON m.id = r.meter_id
        JOIN zone z  ON z.id = m.zone_id
        WHERE z.building_id = ? AND m.kind = ? AND r.ts_utc >= ? AND r.ts_utc < ?
        ORDER BY r.ts_utc
    """

    start_time_text = ts_text(start)
    end_time_text = ts_text(end)

    # Run the sql query (? Placeholders replace by params)
    df = pd.read_sql_query(sql, con, params = (building_id, kind, start_time_text, end_time_text))

    # turn the time series (ts) column in back to real pandas time -> used later for math
    # df = {"ts" : "2026-10-20T20:00:00Z", ...} --> df = {"ts" : 2026-10-20T20:00:00Z, ...}
    df["ts"] = pd.to_datetime(df["ts"], utc = True) 
    
    # return dict of time, zone & reading {"ts" : <UTC_TIME>, "zone" : "<zone_name>", "value" : "<meter_reading>"} 
    return df


def latest_ts(con, building_id = None):
    """Time of the Newest reading (for specific building or ALL buildings)"""

    if building_id is None:
        # no building given -> look at every reading -> Filter for largest time (sorted) (biggest text = largest time (newest))
        sql = "SELECT MAX(ts_utc) AS last FROM reading"
        row = con.execute(sql).fetchone()

    else:
        # building given
        # Search database for readings from a specific building
        # Same as load_readings,
        #   reading -> meter -> zone | so each reading knows its building

        # Filter for readings from a specific building and then filter for largest time (sorted) (biggest text = largest time (newest))
        sql = """
            SELECT MAX(r.ts_utc) AS last 
            FROM reading r
            JOIN meter m ON m.id = r.meter_id
            JOIN zone z  ON z.id = m.zone_id
            WHERE z.building_id = ?
        """
        row = con.execute(sql, (building_id,)).fetchone()

    last_time_text = row["last"]    # row is a dict {"last" : "2016-12-31T22:45:00Z"}
    if last_time_text is None:
        # table empty
        return None

    # return real time
    return pd.Timestamp(last_time_text)
 
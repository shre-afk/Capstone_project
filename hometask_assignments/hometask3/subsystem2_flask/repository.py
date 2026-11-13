"""Database access layer"""
 
import pymysql
 
READINGS_OF_BUILDING = """
    SELECT r.meter_id, r.ts_utc, r.value
    FROM reading r
    JOIN meter m ON m.id = r.meter_id
    JOIN zone z  ON z.id = m.zone_id
    WHERE z.building_id = %s AND r.ts_utc >= %s AND r.ts_utc < %s
    ORDER BY r.ts_utc
"""
 
 
class MySQLRepository:
 
    def __init__(self, host, port, user, password, database):
        self._settings = {
            "host": host, "port": port, "user": user, "password": password,
            "database": database, "cursorclass": pymysql.cursors.DictCursor,
        }
 
    def _query(self, sql, params=(), one=False, write=False):
        """Open a connection, run ONE SQL statement, close the connection again."""
        conn = pymysql.connect(**self._settings)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                if write:
                    conn.commit()
                    return cursor.rowcount
                if one:
                    return cursor.fetchone()
                return cursor.fetchall()
        finally:
            conn.close()
 
    def list_buildings(self):
        return self._query("SELECT id, name, type, floor_area_m2 FROM building ORDER BY id")
 
    def get_building(self, building_id):
        return self._query("SELECT id, name, type, floor_area_m2 FROM building WHERE id = %s",
                           (building_id,), one=True)
 
    def get_meter(self, meter_id):
        return self._query("SELECT m.id, m.kind, m.unit, m.source, z.building_id, b.type "
                           "FROM meter m JOIN zone z ON z.id = m.zone_id "
                           "JOIN building b ON b.id = z.building_id WHERE m.id = %s",
                           (meter_id,), one=True)
 
    def get_readings(self, building_id, start, end):
        return self._query(READINGS_OF_BUILDING, (building_id, start, end))
 
    def add_reading(self, meter_id, ts_utc, value):
        return self._query("INSERT INTO reading (meter_id, ts_utc, value) VALUES (%s, %s, %s)",
                           (meter_id, ts_utc, value), write=True)
 
 
class InMemoryRepository:
    """Same methods as MySQLRepository, but the data lives in Python lists. No server needed."""
 
    def __init__(self, buildings, meters, readings):
        self._buildings = buildings
        self._meters = meters
        self._readings = readings
 
    @classmethod
    def with_sample_data(cls):
        buildings = [
            {"id": 1, "name": "Home 1", "type": "home", "floor_area_m2": 140.0},
            {"id": 2, "name": "Home 3", "type": "home", "floor_area_m2": 120.0},
            {"id": 3, "name": "Home 4", "type": "home", "floor_area_m2": 160.0},
            {"id": 4, "name": "Business 1", "type": "business", "floor_area_m2": 2500.0},
            {"id": 5, "name": "Business 3", "type": "business", "floor_area_m2": 6000.0},
            {"id": 6, "name": "Public 1", "type": "public", "floor_area_m2": 800.0},
        ]
        # one meter per building, and here meter id = building id (same as schema.sql)
        meters = [{"id": b["id"], "kind": "electricity", "unit": "kWh", "source": "",
                   "building_id": b["id"], "type": b["type"]} for b in buildings]
        readings = [
            {"meter_id": 1, "ts_utc": "2016-12-01 07:00:00", "value": 0.42},
            {"meter_id": 1, "ts_utc": "2016-12-01 07:15:00", "value": 0.38},
            {"meter_id": 1, "ts_utc": "2016-12-01 07:30:00", "value": 0.51},
            {"meter_id": 4, "ts_utc": "2016-12-01 07:00:00", "value": 12.50},
            {"meter_id": 4, "ts_utc": "2016-12-01 07:15:00", "value": 14.10},
            {"meter_id": 6, "ts_utc": "2016-12-01 07:00:00", "value": 3.20},
        ]
        return cls(buildings, meters, readings)
 
    def list_buildings(self):
        return [dict(b) for b in self._buildings]
 
    def get_building(self, building_id):
        for b in self._buildings:
            if b["id"] == building_id:
                return dict(b)
        return None
 
    def get_meter(self, meter_id):
        for m in self._meters:
            if m["id"] == meter_id:
                return dict(m)
        return None
 
    def get_readings(self, building_id, start, end):
        meter_ids = [m["id"] for m in self._meters if m["building_id"] == building_id]
        rows = [dict(r) for r in self._readings
                if r["meter_id"] in meter_ids and start <= r["ts_utc"] < end]
        return sorted(rows, key=lambda r: r["ts_utc"])
 
    def add_reading(self, meter_id, ts_utc, value):
        self._readings.append({"meter_id": meter_id, "ts_utc": ts_utc, "value": value})
        return 1
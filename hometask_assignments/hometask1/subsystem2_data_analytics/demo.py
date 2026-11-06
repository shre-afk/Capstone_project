"""demo of the classes doing what the capstone needs them for"""
 
from datetime import datetime
 
from building import Building, make_building
 
# Same numbers as the capstone's config.toml
BUILDINGS = [
    {"name": "Home 1", "type": "home", "column": "DE_KN_residential1_grid_import", "floor_area_m2": 140},
    {"name": "Business 1", "type": "business", "column": "DE_KN_industrial1_grid_import", "floor_area_m2": 2500},
    {"name": "Public 1", "type": "public", "column": "DE_KN_public1_grid_import", "floor_area_m2": 800},
]
MAX_KWH_PER_INTERVAL = {"home": 5.0, "business": 100.0, "public": 50.0}
 
# 1. build every building from its config entry
buildings = []
for entry in BUILDINGS:
    b = make_building(entry["type"], entry["name"], entry["floor_area_m2"])
    b.setup_whole_building(entry["column"], MAX_KWH_PER_INTERVAL[entry["type"]])
    buildings.append(b)
    print("made", b, "->", b.meters())
 
# 2. some 15-min values for Home 1 (one impossible/ one sent twice)
home = buildings[0]
meter = home.meters("electricity")[0]
t0 = datetime(2016, 12, 1, 8, 0)
t1 = datetime(2016, 12, 1, 8, 15)
for ts, kwh in [(t0, 0.42), (t1, 0.38), (datetime(2016, 12, 1, 8, 30), 9.9), (t0, 0.50)]:
    kept = meter.add_reading(ts, kwh)
    print(f"  {ts:%H:%M}  {kwh:5.2f} kWh  ->  {'kept' if kept else 'rejected'}")
 
# 3. what the building knows now
print(f"\n{home.get_name()}: {home.total_kwh()} kWh, {home.kwh_per_m2()} kWh/m2\n")
saturday_morning = datetime(2016, 12, 3, 10, 0)
for b in buildings:
    print(f"{b.get_name():<11} open on Saturday 10:00? {b.is_open(saturday_morning)}")
 
# 4. encapsulation and the abstract class saying no
try:
    home.set_floor_area_m2(-5)
except ValueError as error:
    print("\nsetter said no ->", error)
try:
    Building("Mystery", 100)
except TypeError as error:
    print("abstract class said no ->", error)
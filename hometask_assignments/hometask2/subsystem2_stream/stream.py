"""Where readings come from: a replay generator (like the capstone's replay.py) and an iterator"""
 
from datetime import datetime, timedelta
 
from reading import MeterReading
 
# The six buildings from the capstone's config.toml
BUILDINGS = [
    ("Home 1", "home", "DE_KN_residential1_grid_import"),
    ("Home 3", "home", "DE_KN_residential3_grid_import"),
    ("Home 4", "home", "DE_KN_residential4_grid_import"),
    ("Business 1", "business", "DE_KN_industrial1_grid_import"),
    ("Business 3", "business", "DE_KN_industrial3_grid_import"),
    ("Public 1", "public", "DE_KN_public1_grid_import"),
]
 
# Real meter counters (kWh) from the OPSD file, 1 Dec 2016, 18:00 to 19:30 Berlin time.
# Public 1 is empty: its meter stopped sending on 22 Nov 2016.
START = datetime(2016, 12, 1, 18, 0)
RECORDED = {
    "DE_KN_residential1_grid_import": [7596.878, 7597.419, 7597.604, 7597.829, 7597.999, 7598.218, 7598.419],
    "DE_KN_residential3_grid_import": [2670.833, 2671.198, 2671.633, 2672.008, 2672.268, 2672.444, 2672.593],
    "DE_KN_residential4_grid_import": [4305.478, 4305.694, 4305.762, 4306.123, 4306.312, 4306.683, 4306.979],
    "DE_KN_industrial1_grid_import": [243582.758, 243591.695, 243597.820, 243607.742, 243615.117, 243621.211, 243626.820],
    "DE_KN_industrial3_grid_import": [574429.946, 574462.446, 574489.696, 574513.946, 574538.946, 574563.446, 574587.446],
    "DE_KN_public1_grid_import": [None] * 7,
}
 
# Two faults we add ON PURPOSE, to see the filters catch them
FAULTS = {
    ("DE_KN_residential3_grid_import", 3): None,      # 18:45: Home 3's value gets lost
    ("DE_KN_industrial1_grid_import", 4): 250.0,      # 19:00: Business 1's counter jumps 250 kWh
}
 
 
def replay_feed(slots=7):
    """GENERATOR: one 15-min slot after another, one reading per building, like replay.py"""
    for slot in range(slots):
        ts = START + timedelta(minutes=15 * slot)
        for building, building_type, column in BUILDINGS:
            total = RECORDED[column][slot]
            fault = FAULTS.get((column, slot), 0.0)
            if fault is None:
                total = None                       # value lost on the way
            elif total is not None:
                total = round(total + fault, 3)    # counter glitch
            yield MeterReading(column, building, building_type, ts, total)
 
 
class MeterStream:
    """ITERATOR: wraps any source of readings and counts how many went past"""
 
    def __init__(self, source):
        self._source = iter(source)
        self.count = 0
 
    def __iter__(self):
        return self
 
    def __next__(self):
        reading = next(self._source)   # raises StopIteration when the source is empty
        self.count += 1
        return reading
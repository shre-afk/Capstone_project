"""Building (abstract) and its three real kinds: Home, Business, PublicBuilding"""
 
from abc import ABC, abstractmethod
 
from meter import EnergyMeter
from zone import Zone
 
 
class Building(ABC):
    """You cannot make a plain 'building' - only a Home, Business or PublicBuilding"""
 
    building_type = "building"         # every child overwrites this
 
    def __init__(self, name, floor_area_m2):
        self.set_name(name)
        self.set_floor_area_m2(floor_area_m2)
        self._zones = []               # a building HAS zones
 
    def setup_whole_building(self, csv_column, max_kwh_per_interval):
        """Current setup: one zone covering everything, with one configured electricity meter."""
        zone = self.add_zone(Zone("Whole building"))
        meter = zone.add_meter(EnergyMeter(source=csv_column))
        meter.configure(max_kwh_per_interval)
        return meter
 
    def add_zone(self, zone):
        if not isinstance(zone, Zone):
            raise TypeError("add_zone() only takes Zone objects")
        self._zones.append(zone)
        return zone
 
    def meters(self, kind=None):
        """All meters in all zones or only the ones of one kind"""
        found = []
        for zone in self._zones:
            for meter in zone.get_meters():
                if kind is None or meter.get_kind() == kind:
                    found.append(meter)
        return found
 
    def total_kwh(self):
        total = 0.0
        for zone in self._zones:
            total += zone.total("electricity")
        return round(total, 2)
 
    def kwh_per_m2(self):
        return round(self.total_kwh() / self._floor_area_m2, 4)
 
    @abstractmethod
    def is_open(self, ts):
        """True if people normally use the building at time ts - Every child decides"""
 
    # ---------- getters ----------
    def get_name(self):
        return self._name
 
    def get_floor_area_m2(self):
        return self._floor_area_m2
 
    def get_building_type(self):
        return self.building_type
 
    def get_zones(self):
        return list(self._zones)
 
    # ---------- setters ----------
    def set_name(self, name):
        if not name or not name.strip():
            raise ValueError("a building needs a name")
        self._name = name.strip()
 
    def set_floor_area_m2(self, floor_area_m2):
        if floor_area_m2 <= 0:
            raise ValueError(f"floor area must be > 0, got {floor_area_m2}")
        self._floor_area_m2 = float(floor_area_m2)
 
    def __repr__(self):
        return f"{type(self).__name__}({self._name!r}, {self._floor_area_m2} m2)"
 
 
class Home(Building):
    building_type = "home"
 
    def is_open(self, ts):
        return 6 <= ts.hour < 23                           # people awake 06:00-23:00
 
 
class Business(Building):
    building_type = "business"
 
    def is_open(self, ts):
        return ts.weekday() < 5 and 7 <= ts.hour < 19      # Mon-Fri 07:00-19:00
 
 
class PublicBuilding(Building):
    building_type = "public"
 
    def is_open(self, ts):
        return ts.weekday() < 5 and 7 <= ts.hour < 17      # Mon-Fri 07:00-17:00
 
 
BUILDING_CLASSES = {"home": Home, "business": Business, "public": PublicBuilding}
 
 
def make_building(building_type, name, floor_area_m2):
    """Factory: the text 'home' becomes a Home object, and so on"""
    if building_type not in BUILDING_CLASSES:
        raise ValueError(f"unknown building type {building_type!r}")
    return BUILDING_CLASSES[building_type](name, floor_area_m2)
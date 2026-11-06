"""Meter and EnergyMeter: one measuring device inside a zone"""
 
 
class Meter:
    """Any measuring device - Current version only electricity; later maybe temperature or CO2"""
 
    def __init__(self, kind, unit, source=""):
        # the setters check the values, so new meter are not invalid
        self.set_kind(kind)
        self.set_unit(unit)
        self.set_source(source)
        self._readings = {}           # time -> value, filled by add_reading()
        self._max_per_interval = None  # no limit until configure() is called
 
    def configure(self, max_per_interval):
        """Set the highest value that is physically possible in one 15-minute interval"""
        if max_per_interval <= 0:
            raise ValueError("the limit has to be bigger than 0")
        self._max_per_interval = max_per_interval
 
    def add_reading(self, ts, value):
        """Store one 15-min value - Returns True if kept, False if it was rejected"""
        if value < 0:
            return False                                    # a meter can't un-use energy
        if self._max_per_interval is not None and value > self._max_per_interval:
            return False                                    # physically impossible
        if ts in self._readings:
            return False                                    # same time twice: keep the first one
        self._readings[ts] = value
        return True
 
    def total(self):
        return round(sum(self._readings.values()), 2)
 
    # ---------- getters ----------
    def get_kind(self):
        return self._kind
 
    def get_unit(self):
        return self._unit
 
    def get_source(self):
        return self._source
 
    def get_max_per_interval(self):
        return self._max_per_interval
 
    def get_readings(self):
        return dict(self._readings)    # a copy - we cannot sneak values past add_reading()
 
    # ---------- setters ----------
    def set_kind(self, kind):
        if not kind:
            raise ValueError("a meter has to measure something")
        self._kind = kind
 
    def set_unit(self, unit):
        if not unit:
            raise ValueError("a meter needs a unit, e.g. kWh")
        self._unit = unit
 
    def set_source(self, source):
        self._source = source          # where the data comes from, e.g. a CSV column name
 
    def __repr__(self):
        return f"{type(self).__name__}({self._kind!r}, {self._unit!r}, source={self._source!r})"
 
 
class EnergyMeter(Meter):
    """Electricity meter: reports the kWh used in each 15-minute interval"""
 
    def __init__(self, source=""):
        super().__init__(kind="electricity", unit="kWh", source=source)
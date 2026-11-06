"""Zone: a part of a building (current version of project only deals with whole buildings, floors or rooms can be added in later versions)"""
 
from meter import Meter

 
class Zone:
 
    def __init__(self, name):
        self.set_name(name)
        self._meters = []          # a zone HAS meters
 
    def add_meter(self, meter):
        if not isinstance(meter, Meter):
            raise TypeError("add_meter() only takes Meter objects")
        self._meters.append(meter)
        return meter               # handing it back lets the caller keep working with it
 
    def total(self, kind="electricity"):
        """Sum of all meters of one kind in this zone"""
        result = 0.0
        for meter in self._meters:
            if meter.get_kind() == kind:
                result += meter.total()
        return round(result, 2)
 
    # ---------- getters / setters ----------
    def get_name(self):
        return self._name
 
    def get_meters(self):
        return list(self._meters)
 
    def set_name(self, name):
        if not name or not name.strip():
            raise ValueError("a zone needs a name")
        self._name = name.strip()
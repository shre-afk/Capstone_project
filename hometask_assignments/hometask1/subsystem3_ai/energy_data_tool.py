"""Read-only gateway to the data subsystem; the advisor does not access SQL."""

from copy import deepcopy
from math import isfinite
from numbers import Real


class EnergyDataTool:
    def __init__(self, name="building_energy_summary", description=None, reader=None):
        self.set_name(name)
        self.set_description(
            description if description is not None else
            "Read a building's historical energy, estimated cost, and emissions."
        )
        self._reader = None
        self._last_result = None
        if reader is not None:
            self.initialize(reader)

    def initialize(self, reader):
        """Accept a callable with the same signature as api.get_kpis()."""
        if not callable(reader):
            raise TypeError("reader must be callable: reader(building_id, start, end)")
        self._reader = reader
        self._last_result = None

    def fetch(self, building_id, start, end):
        if self._reader is None:
            raise RuntimeError("initialize the data tool with a reader first")
        if isinstance(building_id, bool) or not isinstance(building_id, int) or building_id <= 0:
            raise ValueError("building id must be a positive integer")
        result = self._reader(building_id, start, end)
        if not isinstance(result, dict):
            raise TypeError("the data reader must return a dictionary")
        for key in ("energy_kwh", "cost_eur", "co2_kg"):
            value = result.get(key)
            if (isinstance(value, bool) or not isinstance(value, Real)
                    or not isfinite(value) or value < 0):
                raise ValueError(f"{key} must be a finite, nonnegative number")
        self._last_result = deepcopy(result)
        return deepcopy(self._last_result)

    def get_name(self):
        return self._name

    def get_description(self):
        return self._description

    def get_reader(self):
        return self._reader

    def get_last_result(self):
        return deepcopy(self._last_result)

    def set_name(self, name):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("a data tool needs a name")
        self._name = name.strip()

    def set_description(self, description):
        if not isinstance(description, str) or not description.strip():
            raise ValueError("a data tool needs a description")
        self._description = description.strip()

    def set_reader(self, reader):
        self.initialize(reader)

"""One message from one building's electricity meter - the way the OPSD data delivers it"""
 
 
class MeterReading:
 
    def __init__(self, column, building, building_type, ts, total_kwh):
        self.column = column                # OPSD column, e.g. DE_KN_industrial1_grid_import
        self.building = building            # "Business 1"
        self.building_type = building_type  # "home", "business" or "public"
        self.ts = ts                        # Berlin time of the reading (datetime)
        self.total_kwh = total_kwh          # the meter's counter; None = no value arrived
        self.kwh = None                     # energy of the last 15 min, filled in later
        self.power_kw = None                # average power in those 15 min, filled in later
        self.extras = {}                    # transform steps write their results in here
 
    def __repr__(self):
        extras = "  ".join(f"{key}={value}" for key, value in self.extras.items())
        kwh = "   -  " if self.kwh is None else f"{self.kwh:6.3f}"
        return f"{self.ts:%H:%M} {self.building:<10} {kwh} kWh  {extras}"
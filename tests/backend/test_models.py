"""test_models.py - buildings, zones and meters

Plain Python objects only
No database needed
"""

import pandas as pd
import pytest

from backend.models import Building, Business, EnergyMeter, Home, Zone, make_building

# Monday 10:00 and Saturday 10:00 in Berlin time
MONDAY_10AM = pd.Timestamp("2016-03-07 10:00", tz="Europe/Berlin")
SATURDAY_10AM = pd.Timestamp("2016-03-12 10:00", tz="Europe/Berlin")


def test_plain_building_cannot_be_created():
    # Building is abstract - only Home, Business and PublicBuilding can be made
    with pytest.raises(TypeError):
        Building("Nowhere", 100)


def test_floor_area_must_be_positive():
    # 0 m2 would break "energy per m2" later on
    with pytest.raises(ValueError):
        Home("Tiny", 0)


def test_factory_makes_the_right_class():
    # config.toml says "business" -> we get a Business object
    assert type(make_building("business", "Shop", 200)) is Business

    # a typo gives a clear error straight away
    with pytest.raises(ValueError):
        make_building("castle", "Neuschwanstein", 6000)


def test_opening_hours_depend_on_the_building_type():
    office = Business("Office", 500)
    home = Home("Flat", 80)

    # an office is open on a weekday morning and closed at the weekend
    assert office.is_open(MONDAY_10AM) is True
    assert office.is_open(SATURDAY_10AM) is False

    # a home is "in use" every day
    assert home.is_open(SATURDAY_10AM) is True


def test_building_collects_meters_from_its_zones():
    home = Home("Flat", 80)
    zone = home.add_zone(Zone("Whole building"))
    zone.add_meter(EnergyMeter(source="col"))

    meters = home.meters()
    assert len(meters) == 1

    # EnergyMeter fills in kind and unit by itself
    assert meters[0].kind == "electricity"
    assert meters[0].unit == "kWh"

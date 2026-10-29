"""calc.py - The Mathematical Analysis"""

import numpy as np
import pandas as pd

def total_kwh(kwh):
    """Sum all 15-min energy values -> total kWh (2 d.p)"""
    total = kwh.sum()
    total = float(total)        # numpy num --> plain Python num

    return round(total, 2)


def cost_eur(energy_kwh, eur_per_kwh):
    """Energy x price -> cost in EUR (2 d.p)"""
    cost = energy_kwh * eur_per_kwh

    return round(cost, 2)


def co2_kg(energy_kwh, kg_per_kwh):
    """Energy x grid emission factor -> kg pf CO2 (1 d.p)"""
    co2 = energy_kwh * kg_per_kwh

    return round(co2, 1)


def completeness(n_readings, period_days, interval_min=15):
    """Share of reading are really using (- rejected)"""
    minutes_in_period = period_days * 24 * 60
    expected_readings = minutes_in_period / interval_min

    if expected_readings == 0:
        return 0.0  # avoid zero division

    share = n_readings / expected_readings
    return round(share, 3)


def eui_per_year(energy_kwh, floor_area_m2, period_days):
    """Energy Use Intensity (EUI)"""

    kwh_per_m2 = energy_kwh / floor_area_m2

    scale_to_year = 365 / period_days

    eui = kwh_per_m2 * scale_to_year

    return round(eui, 1)



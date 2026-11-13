"""test_calc.py - testing the formulas

Numbers in, numbers out
Every expected value can be checked with a calculator
"""

import pandas as pd
import pytest

from backend.analysis import calc


def test_energy_cost_and_co2():
    # 0.25 + 0.25 + 0.5 = 1.0 kWh
    assert calc.total_kwh(pd.Series([0.25, 0.25, 0.5])) == 1.0

    # 100 kWh x 0.30 EUR = 30 EUR
    assert calc.cost_eur(100, 0.30) == 30.0

    # 100 kWh x 0.38 kg = 38 kg CO2
    assert calc.co2_kg(100, 0.38) == 38.0


def test_eui_is_scaled_to_a_full_year():
    # 100 kWh on 100 m2 over a whole year = 1 kWh per m2
    assert calc.eui_per_year(100, 100, 365) == 1.0

    # the same energy in a fifth of a year (73 days) counts 5 times as much
    assert calc.eui_per_year(100, 100, 73) == 5.0


def test_change_in_percent():
    # 7 % less than before - negative means we saved
    assert calc.change_pct(93, 100) == -7.0

    # nothing to compare with -> None instead of dividing by zero
    assert calc.change_pct(50, 0) is None


# one test, four rows = four checks
@pytest.mark.parametrize("score, letter", [
    (90, "A"),
    (70, "B"),      # exactly on the limit counts as the better grade
    (69.9, "C"),
    (10, "E"),
])
def test_grades(score, letter):
    assert calc.grade(score) == letter


def test_score_is_a_weighted_sum():
    weights = {"intensity": 0.6, "after_hours": 0.4}
    parts = {"intensity": 50.0, "after_hours": 100.0}

    # 0.6 x 50 + 0.4 x 100 = 30 + 40 = 70
    assert calc.sustainability_score(parts, weights) == 70.0

"""The reinforcement: corrosion, long-term strength, Kr/Ka, F* and pullout."""
import math

import pytest

from lythosmsew import reinforcement as R

CORROSION = {"design_life": 75.0, "zinc": 86.0, "steel_rate": 12.0}

STRIP = {"name": "s", "kind": "strip", "Tult": 0.0, "RFID": 1.0, "RFCR": 1.0, "RFD": 1.0,
         "Rc": 1.0, "b": 50.0, "t": 4.0, "Fy": 450.0, "Sh": 0.5, "Ci": 0.0, "F0": 2.0,
         "alpha": 1.0, "CR": 1.0}
GRID = {"name": "g", "kind": "geogrid", "Tult": 80.0, "RFID": 1.1, "RFCR": 1.6, "RFD": 1.1,
        "Rc": 1.0, "b": 0.0, "t": 0.0, "Fy": 0.0, "Sh": 0.0, "Ci": 0.67, "F0": 0.0,
        "alpha": 0.8, "CR": 0.8}


def test_the_zinc_lasts_sixteen_years():
    """86 µm: 30 µm in the first two years at 15 µm/yr, 56 µm at 4 µm/yr after."""
    assert R.zinc_life(86.0) == pytest.approx(16.0)
    assert R.zinc_life(20.0) == pytest.approx(20.0 / 15.0)


def test_the_sacrificial_thickness_over_seventy_five_years():
    """2 faces × 12 µm/yr × (75 − 16) years = 1.416 mm."""
    assert R.sacrificial_thickness(75.0, 86.0, 12.0) == pytest.approx(1.416)
    assert R.sacrificial_thickness(10.0, 86.0, 12.0) == 0.0


def test_a_steel_strip_per_metre_of_wall():
    st = R.strength(STRIP, CORROSION)
    ec = 4.0 - 1.416
    assert st["Ec"] == pytest.approx(ec)
    assert st["Ac"] == pytest.approx(50.0 * ec)
    assert st["T_lt"] == pytest.approx(450.0 * 50.0 * ec / 1000.0 / 0.5)
    assert st["Rc"] == pytest.approx(0.05 / 0.5)
    assert st["T_dyn"] == st["T_lt"]


def test_a_geogrid_per_metre_of_wall():
    st = R.strength(GRID, CORROSION)
    assert st["T_lt"] == pytest.approx(80.0 / (1.1 * 1.6 * 1.1))
    assert st["T_dyn"] == pytest.approx(80.0 / (1.1 * 1.1))
    grid = dict(GRID, Rc=0.5)
    assert R.strength(grid, CORROSION)["T_lt"] == pytest.approx(0.5 * st["T_lt"])


def test_kr_over_ka():
    assert R.kr_ratio("geogrid", 3.0) == 1.0
    assert R.kr_ratio("strip", 0.0) == pytest.approx(1.7)
    assert R.kr_ratio("strip", 3.0) == pytest.approx(1.45)
    assert R.kr_ratio("strip", 6.0) == pytest.approx(1.2)
    assert R.kr_ratio("strip", 12.0) == pytest.approx(1.2)


def test_f_star():
    tan = math.tan(math.radians(34.0))
    assert R.f_star(GRID, 2.0, 34.0) == pytest.approx(0.67 * tan)
    assert R.f_star(STRIP, 0.0, 34.0) == pytest.approx(2.0)
    assert R.f_star(STRIP, 3.0, 34.0) == pytest.approx(0.5 * (2.0 + tan))
    assert R.f_star(STRIP, 9.0, 34.0) == pytest.approx(tan)


def test_pullout_resistance():
    """Pr = F*·α·σv·Le·C·Rc with C = 2."""
    assert R.pullout(1.5, 0.8, 100.0, 3.0, 0.1) == pytest.approx(1.5 * 0.8 * 100 * 3 * 2 * 0.1)
    assert R.pullout(1.5, 0.8, 100.0, -1.0, 0.1) == 0.0

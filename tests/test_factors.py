"""
The bearing capacity factors and their corrections against the published
tables, and against the limits each expression has to respect.
"""
import math

import pytest

from lythosmsew import factors as F

# Nc, Nq and Nγ as the textbooks tabulate them, to the precision they print.
# Only the four sets whose Nγ is a closed form are listed: Terzaghi's is a fit
# to his chart and is checked separately, against the formula it is.
PUBLISHED = {
    "meyerhof": {0: (5.14, 1.00, 0.00), 20: (14.83, 6.40, 2.87),
                 30: (30.14, 18.40, 15.67), 40: (75.31, 64.20, 93.69)},
    "hansen": {0: (5.14, 1.00, 0.00), 20: (14.83, 6.40, 2.95),
               30: (30.14, 18.40, 15.07), 40: (75.31, 64.20, 79.54)},
    "vesic": {0: (5.14, 1.00, 0.00), 20: (14.83, 6.40, 5.39),
              30: (30.14, 18.40, 22.40), 40: (75.31, 64.20, 109.41)},
    "ec7": {0: (5.14, 1.00, 0.00), 20: (14.83, 6.40, 3.93),
            30: (30.14, 18.40, 20.09), 40: (75.31, 64.20, 106.05)},
}

#: Terzaghi's own Nc and Nq, which are closed forms like the others
TERZAGHI = {0: (5.70, 1.00), 20: (17.69, 7.44), 30: (37.16, 22.46), 40: (95.66, 81.27)}


@pytest.mark.parametrize("method", list(PUBLISHED))
def test_the_factors_match_the_published_tables(method):
    for phi, (nc, nq, ngamma) in PUBLISHED[method].items():
        got = F.bearing_factors(phi, method)
        assert got["Nc"] == pytest.approx(nc, abs=0.02), f"{method} Nc at {phi}°"
        assert got["Nq"] == pytest.approx(nq, abs=0.02), f"{method} Nq at {phi}°"
        assert got["Ngamma"] == pytest.approx(ngamma, rel=0.02), f"{method} Nγ at {phi}°"


def test_terzaghis_nc_and_nq_match_his_own_table():
    for phi, (nc, nq) in TERZAGHI.items():
        got = F.bearing_factors(phi, "terzaghi")
        assert got["Nc"] == pytest.approx(nc, abs=0.02)
        assert got["Nq"] == pytest.approx(nq, abs=0.02)


def test_terzaghis_ngamma_is_the_fit_it_says_it_is():
    """Terzaghi gave Nγ as a chart of Kpγ, not as a formula. The program uses
    Bowles's closed-form fit to it, which is what this checks — a tabulated
    value would depend on whose table was copied. It is within a few per cent
    of the published tables around φ' = 30°, and further from them at the
    ends; a user who wants a closed form should use one of the other sets."""
    for phi in (5, 15, 20, 25, 30, 35, 40, 45):
        p = math.radians(phi)
        nq = F.bearing_factors(phi, "terzaghi")["Nq"]
        expected = 2.0 * (nq + 1.0) * math.tan(p) / (1.0 + 0.4 * math.sin(4.0 * p))
        assert F.bearing_factors(phi, "terzaghi")["Ngamma"] == pytest.approx(expected)
    # and it sits in the same range as the other sets where they are all used
    at30 = {m: F.bearing_factors(30, m)["Ngamma"]
            for m in ("terzaghi", "hansen", "vesic")}
    assert at30["hansen"] < at30["terzaghi"] < at30["vesic"]


def test_nq_is_reissners_closed_form():
    for phi in (5, 15, 25, 35, 45):
        p = math.radians(phi)
        expected = math.exp(math.pi * math.tan(p)) * math.tan(math.radians(45 + phi / 2)) ** 2
        assert F.bearing_factors(phi, "vesic")["Nq"] == pytest.approx(expected)


def test_nc_is_prandtls_pi_plus_two_at_zero_friction():
    for method in ("meyerhof", "hansen", "vesic", "ec7"):
        assert F.bearing_factors(0, method)["Nc"] == pytest.approx(math.pi + 2, abs=0.01)
    assert F.bearing_factors(0, "terzaghi")["Nc"] == pytest.approx(5.7)


def test_the_factors_grow_with_the_friction_angle():
    for method in list(PUBLISHED) + ["terzaghi"]:
        previous = F.bearing_factors(0, method)
        for phi in range(1, 46):
            got = F.bearing_factors(phi, method)
            for key in ("Nc", "Nq", "Ngamma"):
                assert got[key] >= previous[key] - 1e-9, f"{method} {key} fell at {phi}°"
            previous = got


def test_a_negative_friction_angle_is_refused():
    with pytest.raises(ValueError):
        F.bearing_factors(-1, "vesic")


# --------------------------------------------------------------------------- #
#  Shape, depth, inclination
# --------------------------------------------------------------------------- #

def test_terzaghis_shape_factors_give_his_own_equation():
    """1.3·c·Nc + q·Nq + 0.4·γ·B·Nγ for a square, 0.3 for a circle."""
    N = F.bearing_factors(30, "terzaghi")
    square = F.shape_factors("terzaghi", 2.0, 2.0, 30, N, "square")
    assert square["c"] == pytest.approx(1.3)
    assert 0.5 * square["g"] == pytest.approx(0.4)
    circle = F.shape_factors("terzaghi", 2.0, 2.0, 30, N, "circle")
    assert circle["c"] == pytest.approx(1.3)
    assert 0.5 * circle["g"] == pytest.approx(0.3)


def test_a_strip_has_no_shape_correction():
    N = F.bearing_factors(32, "vesic")
    assert F.shape_factors("vesic", 2.0, 1e6, 32, N, "strip") == {"c": 1.0, "q": 1.0, "g": 1.0}


def test_hansen_and_vesic_share_their_shape_factors():
    N = F.bearing_factors(28, "vesic")
    a = F.shape_factors("hansen", 2.0, 4.0, 28, N, "rectangle")
    b = F.shape_factors("vesic", 2.0, 4.0, 28, N, "rectangle")
    assert a == b
    assert a["q"] == pytest.approx(1.0 + 0.5 * math.tan(math.radians(28)))
    assert a["g"] == pytest.approx(1.0 - 0.4 * 0.5)


def test_the_ec7_shape_factors_are_the_annexes_own():
    N = F.bearing_factors(30, "ec7")
    s = F.shape_factors("ec7", 2.0, 4.0, 30, N, "rectangle")
    assert s["q"] == pytest.approx(1.0 + 0.5 * math.sin(math.radians(30)))
    assert s["g"] == pytest.approx(1.0 - 0.3 * 0.5)
    assert s["c"] == pytest.approx((s["q"] * N["Nq"] - 1.0) / (N["Nq"] - 1.0))


def test_the_depth_factors_are_one_at_the_surface():
    for method in ("meyerhof", "hansen", "vesic"):
        d = F.depth_factors(method, 2.0, 0.0, 30)
        assert d == pytest.approx({"c": 1.0, "q": 1.0, "g": 1.0})


def test_terzaghi_and_skempton_carry_no_depth_factor():
    for method in ("terzaghi", "skempton"):
        assert F.depth_factors(method, 2.0, 3.0, 30) == {"c": 1.0, "q": 1.0, "g": 1.0}


def test_hansens_depth_factor_switches_to_the_arctangent_below_one():
    shallow = F.depth_factors("hansen", 2.0, 2.0, 0)      # D/B = 1 exactly
    deep = F.depth_factors("hansen", 2.0, 4.0, 0)         # D/B = 2, arctan(2)
    assert shallow["c"] == pytest.approx(1.4)
    assert deep["c"] == pytest.approx(1.0 + 0.4 * math.atan(2.0))


def test_an_inclined_load_never_helps():
    N = F.bearing_factors(30, "vesic")
    for method in ("meyerhof", "hansen", "vesic", "ec7"):
        i = F.inclination_factors(method, 1000.0, 200.0, 0.0, 2.0, 4.0, 8.0, 5.0, 30, N)
        for part in ("c", "q", "g"):
            assert 0.0 <= i[part] <= 1.0 + 1e-9, f"{method} i{part}"


def test_no_horizontal_load_leaves_the_inclination_factors_alone():
    N = F.bearing_factors(30, "vesic")
    i = F.inclination_factors("vesic", 1000.0, 0.0, 0.0, 2.0, 4.0, 8.0, 0.0, 30, N)
    assert i == {"c": 1.0, "q": 1.0, "g": 1.0}


def test_vesics_exponent_lies_between_its_two_bounds():
    """m runs from 1.5 (a square) to 2 (a very long footing)."""
    assert F._m_exponent(2.0, 2.0, 1.0, 0.0) == pytest.approx(1.5)
    assert F._m_exponent(1.0, 1000.0, 1.0, 0.0) == pytest.approx(2.0, abs=1e-2)


def test_a_tilted_base_and_a_sloping_ground_both_reduce_the_capacity():
    N = F.bearing_factors(30, "vesic")
    for method in ("hansen", "vesic"):
        b = F.base_factors(method, 10.0, 30, N)
        g = F.ground_factors(method, 10.0, 30, N)
        assert all(0.0 <= b[p] <= 1.0 for p in ("c", "q", "g"))
        assert all(0.0 <= g[p] <= 1.0 for p in ("c", "q", "g"))


def test_the_undrained_corrections_hansen_adds_are_zero_when_there_is_nothing_to_add():
    """Hansen's φ = 0 expression adds its corrections, so its identity is 0."""
    N = F.bearing_factors(0, "hansen")
    assert F.base_factors("hansen", 0.0, 0.0, N)["c"] == 0.0
    assert F.ground_factors("hansen", 0.0, 0.0, N)["c"] == 0.0
    assert F.inclination_factors("hansen", 100.0, 0.0, 0.0, 2, 4, 8, 50, 0, N)["c"] == 0.0
    # and one everywhere else
    assert F.base_factors("vesic", 0.0, 0.0, N)["c"] == 1.0


def test_skemptons_nc_matches_his_chart_at_its_ends():
    assert F.skempton_nc(2.0, 1e9, 0.0) == pytest.approx(5.0)        # strip, at the surface
    assert F.skempton_nc(2.0, 1e9, 20.0) == pytest.approx(7.5)       # strip, deep
    assert F.skempton_nc(2.0, 2.0, 0.0) == pytest.approx(6.0)        # square, at the surface
    assert F.skempton_nc(2.0, 2.0, 20.0) == pytest.approx(9.0)       # square, deep


def test_local_shear_reduces_the_strength_the_way_terzaghi_wrote_it():
    c, phi = F.local_shear(30.0, 30.0)
    assert c == pytest.approx(20.0)
    assert math.tan(math.radians(phi)) == pytest.approx(2.0 / 3.0 * math.tan(math.radians(30)))


def test_a_rigid_soil_needs_no_compressibility_correction():
    N = F.bearing_factors(35, "vesic")
    stiff = F.compressibility_factors(2.0, 4.0, 35, 0.0, 50.0, 1e9, N)
    assert stiff["c"] == pytest.approx(1.0)
    soft = F.compressibility_factors(2.0, 4.0, 35, 0.0, 50.0, 2000.0, N)
    assert soft["q"] < 1.0 and soft["Ir"] < soft["Ir_crit"]

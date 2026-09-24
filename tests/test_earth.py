"""Earth pressure coefficients against their closed forms and their limits."""
import math

import pytest

from lythosmsew import earth


@pytest.mark.parametrize("phi", [20.0, 30.0, 34.0, 40.0])
def test_coulomb_is_rankine_for_a_vertical_smooth_back_and_a_level_fill(phi):
    assert earth.coulomb_ka(phi) == pytest.approx(earth.rankine_ka(phi), rel=1e-12)


def test_rankine_at_thirty_degrees_is_one_third():
    assert earth.rankine_ka(30.0) == pytest.approx(1.0 / 3.0)


@pytest.mark.parametrize("beta", [5.0, 10.0, 20.0])
def test_coulomb_with_delta_equal_to_beta_is_rankines_sloping_fill(beta):
    """Behind a vertical back with δ = β, Coulomb's coefficient is Rankine's for a
    sloping backfill, cos β·(cos β − √(cos²β − cos²φ)) / (cos β + √(cos²β − cos²φ))."""
    phi = 32.0
    b, p = math.radians(beta), math.radians(phi)
    root = math.sqrt(math.cos(b) ** 2 - math.cos(p) ** 2)
    rankine = math.cos(b) * (math.cos(b) - root) / (math.cos(b) + root)
    assert earth.coulomb_ka(phi, 90.0, beta, beta) == pytest.approx(rankine, rel=1e-9)


def test_a_battered_face_lowers_the_active_pressure():
    assert earth.coulomb_ka(30.0, 100.0) < earth.coulomb_ka(30.0, 90.0)


def test_a_backslope_steeper_than_phi_has_no_active_state():
    with pytest.raises(ValueError):
        earth.coulomb_ka(30.0, 90.0, 0.0, 35.0)


def test_mononobe_okabe_without_acceleration_is_coulomb():
    for beta in (0.0, 10.0):
        assert earth.mononobe_okabe(30.0, 0.0, beta, beta) == pytest.approx(
            earth.coulomb_ka(30.0, 90.0, beta, beta), rel=1e-9)


def test_mononobe_okabe_by_hand():
    """φ = 30°, kh = 0.2, δ = β = 0: ψ = 11.31°, KAE = 0.4731."""
    assert earth.mononobe_okabe(30.0, 0.2) == pytest.approx(0.4731, abs=5e-4)


def test_mononobe_okabe_refuses_an_impossible_state():
    with pytest.raises(ValueError):
        earth.mononobe_okabe(30.0, 0.5, 0.0, 20.0)


def test_am_coefficient():
    assert earth.am_coefficient(0.2) == pytest.approx(0.25)
    assert earth.am_coefficient(0.0) == 0.0

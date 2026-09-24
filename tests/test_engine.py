"""
The wall analysis against hand calculations: the forces and the external
checks, the bearing capacity, the tension and pullout of a layer, the LRFD
factors, the earthquake, the required length, and the refusals.
"""
import copy
import math

import pytest

from lythosmsew.config import DEFAULT_CONFIG
from lythosmsew.engine import MSEWall, MSEWError, generate_layers


def config(**changes):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for path, value in changes.items():
        node = cfg
        keys = path.split("__")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
    return cfg


def run(cfg=None, **kw):
    wall = MSEWall(cfg or config())
    wall.run(**kw)
    return wall, wall.results


@pytest.fixture(scope="module")
def default():
    return run()


# --------------------------------------------------------------------------- #
#  External stability, ASD, by hand
# --------------------------------------------------------------------------- #

def test_the_forces_on_the_block(default):
    _, res = default
    f = res["forces"]
    V1 = 19.0 * 6.0 * 5.4                               # γr·H·L
    F1 = 0.5 * (1 / 3) * 18.0 * 36.0                    # ½·Ka·γb·H²
    F2 = (1 / 3) * 10.0 * 6.0                           # Ka·q·H
    assert f["V"] == pytest.approx(V1)                  # no live load over the block
    assert f["H"] == pytest.approx(F1 + F2)
    assert f["M_R"] == pytest.approx(V1 * 2.7)
    assert f["M_O"] == pytest.approx(F1 * 2.0 + F2 * 3.0)
    assert f["e"] == pytest.approx(2.7 - (V1 * 2.7 - F1 * 2.0 - F2 * 3.0) / V1)


def test_the_external_checks(default):
    _, res = default
    V1, F1, F2 = 19.0 * 6.0 * 5.4, 108.0, 20.0
    # the foundation (tan 30° plus c·L) is weaker than the reinforced fill (tan 34°)
    R = V1 * math.tan(math.radians(30.0)) + 5.0 * 5.4
    assert res["external"]["sliding"]["value"] == pytest.approx(R / (F1 + F2))
    assert res["external"]["sliding"]["plane"] == "foundation"
    assert res["external"]["overturning"]["value"] == pytest.approx(
        V1 * 2.7 / (F1 * 2.0 + F2 * 3.0))
    assert res["external"]["eccentricity"]["required"] == pytest.approx(5.4 / 6.0)
    assert all(c["status"] == "OK" for c in res["external"].values())


def test_the_bearing_capacity_under_the_effective_width(default):
    wall, res = default
    b = res["bearing"]
    V = 19.0 * 6.0 * 5.4 + 10.0 * 5.4                   # the live load bears
    M = 19.0 * 6.0 * 5.4 * 2.7 + 10.0 * 5.4 * 2.7 - 108.0 * 2.0 - 20.0 * 3.0
    e = 2.7 - M / V
    assert b["e"] == pytest.approx(e)
    assert b["B_eff"] == pytest.approx(5.4 - 2 * e)
    assert b["sigma_v"] == pytest.approx(V / (5.4 - 2 * e))
    # Vesić, φ = 30°, c = 5, no embedment: c·Nc + ½·γ·B'·Nγ
    q = 5.0 * 30.14 + 0.5 * 18.5 * (5.4 - 2 * e) * 22.40
    assert b["q_ult"] == pytest.approx(q, rel=2e-3)
    assert res["external"]["bearing"]["value"] == pytest.approx(b["q_ult"] / b["sigma_v"])
    assert set(b["methods"]) == {"vesic", "meyerhof", "hansen", "terzaghi", "ec7"}


def test_the_embedment_raises_the_bearing_capacity():
    _, plain = run()
    _, deep = run(config(options__bearing_embedment=True))
    assert deep["bearing"]["q_ult"] > plain["bearing"]["q_ult"]


def test_a_high_water_table_lowers_the_bearing_capacity():
    _, dry = run()
    _, wet = run(config(soils__water_depth=0.0))
    assert wet["bearing"]["q_ult"] < dry["bearing"]["q_ult"]
    assert any(w[0] == "warn_water" for w in wet["warnings"])


# --------------------------------------------------------------------------- #
#  Internal stability, by hand
# --------------------------------------------------------------------------- #

def test_the_top_layer_of_steel_strips(default):
    _, res = default
    top = res["layers"][-1]
    ka = math.tan(math.radians(45 - 17)) ** 2
    depth = 6.0 - 5.625
    kr = ka * (1.7 - 0.5 * depth / 6.0)
    assert top["Kr"] == pytest.approx(kr)
    assert top["Sv"] == pytest.approx(0.75)
    assert top["T_max"] == pytest.approx(kr * (19.0 * depth + 10.0) * 0.75)
    # the coherent gravity surface: 0.3·H in the upper half
    assert top["La"] == pytest.approx(1.8)
    assert top["Le"] == pytest.approx(3.6)
    fstar = 2.0 + (math.tan(math.radians(34)) - 2.0) * depth / 6.0
    pr = fstar * 1.0 * 19.0 * depth * 3.6 * 2 * (0.05 / 0.5)
    assert top["P_r"] == pytest.approx(pr)
    assert top["pullout"]["value"] == pytest.approx(pr / top["T_max"])


def test_the_lowest_layer_of_steel_strips(default):
    _, res = default
    low = res["layers"][0]
    assert low["La"] == pytest.approx(0.6 * 0.375)     # the lower half: 0.6·z
    ec = 4.0 - 1.416
    t_lt = 450.0 * 50.0 * ec / 1000.0 / 0.5
    assert low["T_lt"] == pytest.approx(t_lt)
    assert low["tensile"]["value"] == pytest.approx(t_lt / low["T_max"])
    assert low["tensile"]["required"] == pytest.approx(1 / 0.55)


def test_a_geogrid_wall_uses_rankine():
    layers = generate_layers(6.0, 0.3, 0.6, "ratio", 0.8, 0.0, 2.4, "Geogrid 80")
    _, res = run(config(layers=layers))
    ka = math.tan(math.radians(45 - 17)) ** 2
    for row in res["layers"]:
        assert row["Kr"] == pytest.approx(ka)
        assert row["La"] == pytest.approx(row["z"] * math.tan(math.radians(45 - 17)))
        assert row["F_star"] == pytest.approx(0.67 * math.tan(math.radians(34)))
        assert row["T_lt"] == pytest.approx(80.0 / (1.1 * 1.6 * 1.1))
        assert row["connection"]["value"] == pytest.approx(0.8 * row["tensile"]["value"])
    # a geosynthetic at the base offers a sliding plane of its own
    assert "interface" in res["friction"]["options"]


def test_tributary_heights_add_up_to_the_wall(default):
    _, res = default
    assert sum(r["Sv"] for r in res["layers"]) == pytest.approx(6.0)


def test_a_strip_load_spreads_at_two_to_one():
    wall = MSEWall(config(loads__strip_enabled=True, loads__strip_P=60.0,
                          loads__strip_width=1.0, loads__strip_offset=1.5))
    assert wall.strip_increment(0.0) == pytest.approx(60.0)
    assert wall.strip_increment(1.0) == pytest.approx(30.0)            # b + z
    assert wall.strip_increment(4.0) == pytest.approx(60.0 / (2.5 + 1.5))  # cut by the face
    wall.run(with_length=False)
    top = wall.results["layers"][-1]
    assert top["sigma_v"] > 19.0 * 0.375 + 10.0


def test_a_backslope_adds_its_surcharge():
    wall, res = run(config(geometry__backslope=10.0), with_length=False)
    assert res["slope_surcharge"] == pytest.approx(0.5 * 0.7 * 6 * math.tan(math.radians(10)) * 19)
    assert res["h"] == pytest.approx(6.0 + 5.4 * math.tan(math.radians(10)))


def test_a_batter_lowers_the_pressure():
    _, plain = run(with_length=False)
    _, battered = run(config(geometry__batter=12.0), with_length=False)
    assert battered["Ka"]["retained"] < plain["Ka"]["retained"]
    assert battered["Ka"]["theta"] == pytest.approx(102.0)
    assert battered["external"]["overturning"]["value"] > plain["external"]["overturning"]["value"]


# --------------------------------------------------------------------------- #
#  LRFD and the earthquake
# --------------------------------------------------------------------------- #

def test_lrfd_factors_the_loads():
    _, res = run(config(options__design="lrfd"), with_length=False)
    f = res["forces"]
    V1 = 19.0 * 6.0 * 5.4
    assert f["V"] == pytest.approx(1.0 * V1)                         # EV min
    assert f["H"] == pytest.approx(1.5 * 108.0 + (1 / 3) * 6.0 * 1.75 * 10.0)
    assert res["external"]["overturning"]["status"] == "N/A"
    assert res["external"]["eccentricity"]["required"] == pytest.approx(5.4 / 3.0)
    top = res["layers"][-1]
    depth = 6.0 - 5.625
    assert top["T_design"] == pytest.approx(top["Kr"] * (1.35 * 19.0 * depth + 1.75 * 10.0) * 0.75)
    assert top["tensile"]["value"] == pytest.approx(0.75 * top["T_lt"] / top["T_design"])
    assert res["bearing"]["check"]["value"] == pytest.approx(
        0.65 * res["bearing"]["q_ult"] / res["bearing"]["sigma_v"])


def test_the_seismic_forces():
    _, res = run(config(seismic__enabled=True, seismic__A=0.2), with_length=False)
    s = res["seismic"]
    assert s["Am"] == pytest.approx(0.25)
    assert s["PAE"] == pytest.approx(0.375 * 0.25 * 18.0 * 36.0)
    assert s["PIR"] == pytest.approx(0.25 * 19.0 * 6.0 * 3.0)
    assert s["external"]["sliding"]["required"] == pytest.approx(0.75 * 1.5)
    assert s["external"]["eccentricity"]["required"] == pytest.approx(5.4 / 4.0)
    assert s["external"]["sliding"]["value"] < res["external"]["sliding"]["value"]
    total = sum(r["T_md"] for r in s["internal_rows"])
    assert total == pytest.approx(s["P_i"])
    # the active zone of steel strips: 0.3H over the upper half, a triangle below
    area = 0.3 * 6 * 3 + 0.5 * 0.3 * 6 * 3
    assert s["W_a"] == pytest.approx(19.0 * area, rel=1e-3)


def test_the_seismic_backslope_uses_mononobe_okabe():
    _, res = run(config(seismic__enabled=True, geometry__backslope=8.0), with_length=False)
    assert res["seismic"]["PAE"] > 0


# --------------------------------------------------------------------------- #
#  The required length
# --------------------------------------------------------------------------- #

def test_the_required_length_is_the_boundary(default):
    wall, res = default
    length = res["required_length"]
    assert 0.2 * 6 < length < 4 * 6
    assert wall.with_length(length).passes()
    assert not wall.with_length(length - 0.05).passes()


def test_no_length_can_save_a_wall_on_mud():
    _, res = run(config(soils__foundation={"gamma": 16.0, "gamma_sat": 17.0, "phi": 0.0,
                                           "c": 5.0}))
    assert math.isinf(res["required_length"])
    assert res["external"]["bearing"]["status"] == "NOT OK"


# --------------------------------------------------------------------------- #
#  Refusals and warnings
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("changes, key", [
    ({"geometry__H": 0.0}, "err_height"),
    ({"geometry__backslope": 35.0}, "err_backslope"),
    ({"layers": [{"z": 7.0, "L": 5.0, "type": "Strip 50x4"}]}, "err_layer_height"),
    ({"layers": [{"z": 1.0, "L": 5.0, "type": "nothing"}]}, "err_unknown_type"),
    ({"layers": []}, "err_no_layers"),
    ({"soils__foundation": {"gamma": 18.0, "gamma_sat": 19.0, "phi": 0.0, "c": 0.0}},
     "err_foundation_strength"),
])
def test_impossible_inputs_are_refused(changes, key):
    with pytest.raises(MSEWError) as caught:
        MSEWall(config(**changes)).run()
    assert caught.value.key == key


def test_the_error_names_the_soil_in_the_language_asked():
    from lythosmsew.i18n import t
    cfg = config()
    cfg["soils"]["retained"]["gamma"] = 0.0
    with pytest.raises(MSEWError) as caught:
        MSEWall(cfg).run()
    assert "Retained fill" in str(caught.value)
    assert "Arka dolgu" in t("tr", caught.value.key, **caught.value.params)


def test_short_and_uneven_layers_are_warned_about():
    layers = [{"z": 0.4, "L": 3.0, "type": "Strip 50x4"},
              {"z": 1.6, "L": 2.0, "type": "Strip 50x4"},
              {"z": 5.5, "L": 2.0, "type": "Strip 50x4"}]
    _, res = run(config(layers=layers), with_length=False)
    keys = {w[0] for w in res["warnings"]}
    assert {"warn_lengths_vary", "warn_min_length", "warn_spacing", "warn_short_le"} <= keys
    assert res["internal"]["pullout"]["status"] == "NOT OK"


# --------------------------------------------------------------------------- #
#  The layout generator
# --------------------------------------------------------------------------- #

def test_the_layout_generator():
    layers = generate_layers(6.0, 0.375, 0.75, "ratio", 0.7, 0.0, 2.4, "S")
    assert [r["z"] for r in layers] == pytest.approx([0.375 + 0.75 * i for i in range(8)])
    assert all(r["L"] == pytest.approx(4.2) for r in layers)
    short = generate_layers(2.0, 0.3, 0.6, "ratio", 0.7, 0.0, 2.4, "S")
    assert short[0]["L"] == pytest.approx(2.4)
    fixed = generate_layers(6.0, 0.3, 0.6, "fixed", 0.7, 5.5, 2.4, "S")
    assert fixed[0]["L"] == pytest.approx(5.5)
    with pytest.raises(MSEWError):
        generate_layers(6.0, 0.0, 0.6, "fixed", 0.7, 5.5, 2.4, "S")

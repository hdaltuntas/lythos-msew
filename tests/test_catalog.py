"""The catalogue of market reinforcement: every entry is usable as it stands."""
import copy

import pytest

from lythosmsew import catalog, forms
from lythosmsew import reinforcement as R
from lythosmsew.config import DEFAULT_CONFIG, KINDS
from lythosmsew.engine import MSEWall, generate_layers
from lythosmsew.i18n import TRANSLATIONS

ENTRIES = [row for rows in catalog.CATALOG.values() for row in rows]


def test_the_names_are_unique_and_the_kinds_known():
    names = [row["name"] for row in ENTRIES]
    assert len(names) == len(set(names))
    assert {row["kind"] for row in ENTRIES} == set(KINDS)
    assert set(catalog.CATALOG) == set(catalog.FAMILIES)


@pytest.mark.parametrize("row", ENTRIES, ids=[r["name"] for r in ENTRIES])
def test_every_entry_designs_a_wall(row):
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["reinforcement_types"] = [dict(row)]
    cfg["layers"] = generate_layers(6.0, 0.375, 0.75, "ratio", 0.9, 0.0, 2.4, row["name"])
    wall = MSEWall(cfg)
    res = wall.run(with_length=False)
    assert all(layer["T_lt"] > 0 and layer["P_r"] > 0 for layer in res["layers"])


def test_the_entries_survive_the_form_readers():
    values = forms.defaults()
    values["reinforcement_types"] = [dict(row) for row in ENTRIES]
    assert forms.to_config(values)["reinforcement_types"] == ENTRIES


def test_a_polymer_strip_per_metre_of_wall():
    row = catalog.entry("PET strip 50 kN")
    st = R.strength(row, DEFAULT_CONFIG["corrosion"])
    assert st["T_lt"] == pytest.approx(50.0 / (1.05 * 1.50 * 1.10) / 0.25)
    assert st["T_dyn"] == pytest.approx(50.0 / (1.05 * 1.10) / 0.25)
    assert st["Rc"] == pytest.approx(0.05 / 0.25)
    assert R.is_extensible("polymer_strip") and not R.is_sheet("polymer_strip")


def test_a_polymer_strip_wall_is_extensible_but_offers_no_sliding_plane():
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    cfg["reinforcement_types"] = [catalog.entry("PET strip 50 kN")]
    cfg["layers"] = generate_layers(6.0, 0.375, 0.75, "ratio", 0.9, 0.0, 2.4, "PET strip 50 kN")
    res = MSEWall(cfg).run(with_length=False)
    assert "interface" not in res["friction"]["options"]
    assert all(r["Kr_Ka"] == 1.0 for r in res["layers"])


def test_the_steel_strips_are_s355_and_grade_65():
    row = catalog.entry("HA strip 60x5 S355")
    assert (row["b"], row["t"], row["Fy"]) == (60.0, 5.0, 355.0)
    assert catalog.entry("HA strip 50x4 Gr65")["Fy"] == 450.0
    with pytest.raises(KeyError):
        catalog.entry("nothing")


def test_the_interface_gets_the_catalogue_in_both_languages():
    for lang in ("en", "tr"):
        families = forms.schema(lang)["types"]["catalog"]
        assert [f["family"] for f in families] == catalog.FAMILIES
        assert all(f["label"] == TRANSLATIONS[lang][f"family_{f['family']}"] for f in families)
    assert set(forms.schema()["types"]["off_columns"]) == set(KINDS)

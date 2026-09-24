"""The input schema, the defaults and the round trip through a project file."""
import json

from lythosmsew import forms
from lythosmsew.config import DEFAULT_CONFIG


def test_the_defaults_are_the_default_project():
    cfg = forms.to_config(forms.defaults())
    for section in ("geometry", "loads", "soils", "corrosion", "options", "seismic",
                    "criteria", "layout", "heights"):
        assert cfg[section] == DEFAULT_CONFIG[section], section
    assert cfg["reinforcement_types"] == DEFAULT_CONFIG["reinforcement_types"]
    assert cfg["layers"] == DEFAULT_CONFIG["layers"]


def test_every_field_key_is_unique():
    keys = [f.key for g in forms._all_groups("en") for f in g.fields]
    # the minimum embedment length is offered in both criteria groups, under two keys
    assert len(keys) == len(set(keys))


def test_both_languages_offer_the_same_schema():
    en, tr = forms.schema("en"), forms.schema("tr")
    for part in ("project", "wall", "layout", "options", "heights"):
        assert ([f["key"] for g in en[part]["groups"] for f in g["fields"]]
                == [f["key"] for g in tr[part]["groups"] for f in g["fields"]])
    assert [c["key"] for c in en["types"]["columns"]] == [c["key"] for c in tr["types"]["columns"]]


def test_a_project_file_round_trips():
    values = forms.defaults()
    values["H"] = 7.25
    values["phi_f"] = 28.0
    values["design"] = "lrfd"
    values["min_Le_lrfd"] = 1.2
    values["layers"][0]["L"] = 6.5
    values["reinforcement_types"][1]["Tult"] = 120.0
    data = json.loads(json.dumps(forms.project_file(values)))
    assert data["format"] == forms.FILE_FORMAT
    back = forms.from_config(data)
    assert back["H"] == 7.25 and back["phi_f"] == 28.0 and back["design"] == "lrfd"
    assert back["layers"][0]["L"] == 6.5
    assert back["reinforcement_types"][1]["Tult"] == 120.0
    assert forms.to_config(back)["criteria"]["min_Le"] == 1.2


def test_rubbish_in_the_tables_is_dropped():
    values = forms.defaults()
    values["layers"] = [{"z": "a", "L": 3, "type": "x"}, {"z": 2.0, "L": 4.0, "type": " S "},
                        {"z": 1.0, "L": 4.0, "type": "S"}]
    values["reinforcement_types"] = [{"name": ""}, {"name": "S", "kind": "nonsense"},
                                     {"name": "S", "kind": "geogrid"}]
    cfg = forms.to_config(values)
    assert [r["z"] for r in cfg["layers"]] == [1.0, 2.0]
    assert cfg["layers"][1]["type"] == "S"
    assert len(cfg["reinforcement_types"]) == 1
    assert cfg["reinforcement_types"][0]["kind"] == "strip"


def test_a_missing_value_keeps_its_default():
    values = forms.defaults()
    values["H"] = None
    values["q_live"] = ""
    cfg = forms.to_config(values)
    assert cfg["geometry"]["H"] == DEFAULT_CONFIG["geometry"]["H"]
    assert cfg["loads"]["q_live"] == DEFAULT_CONFIG["loads"]["q_live"]


def test_conditional_fields_name_keys_that_exist():
    keys = {f.key for g in forms._all_groups("en") for f in g.fields}
    for group in forms._all_groups("en"):
        for item in [group, *group.fields]:
            for condition in item.when:
                assert condition["key"] in keys

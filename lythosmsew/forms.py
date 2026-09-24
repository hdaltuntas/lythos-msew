"""
Input schema and readers for Lythos MSEW.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The browser builds its forms from this schema, and the
server turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``H``, ``gamma_r``, ``layout_Sv`` …) are the ones the
interface uses; the nested keys of the configuration (``geometry.H``,
``soils.reinforced.gamma``, ``layout.Sv`` …) are the ones the engine and the
``.msew`` project files use. `to_config()` and `from_config()` convert between
the two.

A field can declare when it applies — ``when=[("design", ["lrfd"])]`` — and
the browser hides it whenever the condition does not hold, so the form shows
the inputs of the method that is actually running and no others.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from .config import BEARING_METHODS, DEFAULT_CONFIG, DESIGNS, KINDS, LAYOUT_RULES
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "lythos-msew"
FILE_VERSION = "0.1"


def _t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# --------------------------------------------------------------------------- #
#  Schema data structures
# --------------------------------------------------------------------------- #

@dataclass
class Field:
    """One input field."""
    key: str
    label: str
    kind: str = "number"                     # number | text | check | select | reftype
    default: Any = 0.0
    unit: str = ""
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    decimals: int = 2
    options: List[Dict[str, str]] = field(default_factory=list)
    when: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Only what the browser needs; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        return {k: v for k, v in asdict(self).items()
                if k in keep or v not in ("", None, [], 0.0)}


@dataclass
class Group:
    """A titled set of fields."""
    title: str
    fields: List[Field]
    note: str = ""
    when: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"title": self.title, "fields": [f.to_dict() for f in self.fields]}
        if self.note:
            d["note"] = self.note
        if self.when:
            d["when"] = list(self.when)
        return d


def _num(key, label, default, lo=None, hi=None, unit="", dec=2, step=None, when=None):
    return Field(key, label, "number", default, unit, lo, hi, step, dec, when=_when(when))


def _check(key, label, default=False, when=None):
    return Field(key, label, "check", default, when=_when(when))


def _select(key, label, default, options, when=None):
    return Field(key, label, "select", default,
                 options=[{"value": v, "label": t} for v, t in options], when=_when(when))


def _text(key, label, default=""):
    return Field(key, label, "text", default)


def _when(conditions) -> List[Dict[str, Any]]:
    """``[("key", ["a", "b"])]`` as the browser reads it."""
    if not conditions:
        return []
    return [{"key": key, "in": list(values)} for key, values in conditions]


def _choices(lang: str, prefix: str, values: List[str]):
    return [(value, _t(lang, f"{prefix}_{value}")) for value in values]


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #

def project_groups(lang: str = "en") -> List[Group]:
    info = DEFAULT_CONFIG["project_info"]
    return [Group(_t(lang, "group_project"), [
        _text("title", _t(lang, "title_label"), info["title"]),
        _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
    ])]


def wall_groups(lang: str = "en") -> List[Group]:
    g = DEFAULT_CONFIG["geometry"]
    q = DEFAULT_CONFIG["loads"]
    s = DEFAULT_CONFIG["soils"]
    strip = [("strip_enabled", [True])]
    return [
        Group(_t(lang, "group_geometry"), [
            _num("H", _t(lang, "H_label"), g["H"], 0.5, 40, "m", 2, 0.25),
            _num("embedment", _t(lang, "embedment_label"), g["embedment"], 0, 10, "m", 2, 0.1),
            _num("batter", _t(lang, "batter_label"), g["batter"], 0, 29, "°", 1, 1),
            _num("backslope", _t(lang, "backslope_label"), g["backslope"], 0, 45, "°", 1, 1),
            _num("toe_slope", _t(lang, "toe_slope_label"), g["toe_slope"], 0, 44, "°", 1, 1),
            _num("facing", _t(lang, "facing_label"), g["facing"], 0, 2, "m", 2, 0.02),
        ], note=_t(lang, "geometry_note")),
        Group(_t(lang, "group_loads"), [
            _num("q_dead", _t(lang, "q_dead_label"), q["q_dead"], 0, 1000, "kPa", 1, 1),
            _num("q_live", _t(lang, "q_live_label"), q["q_live"], 0, 1000, "kPa", 1, 1),
            _check("strip_enabled", _t(lang, "strip_enabled_label"), q["strip_enabled"]),
            _num("strip_P", _t(lang, "strip_P_label"), q["strip_P"], 0, 1e5, "kN/m", 1, 5,
                 when=strip),
            _num("strip_width", _t(lang, "strip_width_label"), q["strip_width"], 0.05, 20,
                 "m", 2, 0.1, when=strip),
            _num("strip_offset", _t(lang, "strip_offset_label"), q["strip_offset"], 0, 50,
                 "m", 2, 0.1, when=strip),
            _check("strip_live", _t(lang, "strip_live_label"), q["strip_live"], when=strip),
        ], note=_t(lang, "loads_note")),
        Group(_t(lang, "group_reinforced"), [
            _num("gamma_r", _t(lang, "gamma_label"), s["reinforced"]["gamma"], 10, 26,
                 "kN/m³", 1, 0.5),
            _num("phi_r", _t(lang, "phi_label"), s["reinforced"]["phi"], 15, 50, "°", 1, 1),
        ]),
        Group(_t(lang, "group_retained"), [
            _num("gamma_b", _t(lang, "gamma_label"), s["retained"]["gamma"], 10, 26,
                 "kN/m³", 1, 0.5),
            _num("phi_b", _t(lang, "phi_label"), s["retained"]["phi"], 10, 50, "°", 1, 1),
        ]),
        Group(_t(lang, "group_foundation"), [
            _num("gamma_f", _t(lang, "gamma_label"), s["foundation"]["gamma"], 10, 26,
                 "kN/m³", 1, 0.5),
            _num("gamma_sat_f", _t(lang, "gamma_sat_label"), s["foundation"]["gamma_sat"],
                 10, 26, "kN/m³", 1, 0.5),
            _num("phi_f", _t(lang, "phi_label"), s["foundation"]["phi"], 0, 50, "°", 1, 1),
            _num("c_f", _t(lang, "c_label"), s["foundation"]["c"], 0, 1000, "kPa", 1, 1),
            _num("water_depth", _t(lang, "water_depth_label"), s["water_depth"], 0, 500,
                 "m", 2, 0.5),
            _num("gamma_water", _t(lang, "gamma_water_label"), s["gamma_water"], 9, 11,
                 "kN/m³", 2, 0.01),
        ], note=_t(lang, "foundation_note")),
    ]


def layout_groups(lang: str = "en") -> List[Group]:
    lay = DEFAULT_CONFIG["layout"]
    return [Group(_t(lang, "group_layout"), [
        _num("layout_z1", _t(lang, "z1_label"), lay["z1"], 0.05, 5, "m", 3, 0.025),
        _num("layout_Sv", _t(lang, "Sv_label"), lay["Sv"], 0.1, 3, "m", 3, 0.025),
        _select("layout_rule", _t(lang, "rule_label"), lay["rule"],
                _choices(lang, "rule", LAYOUT_RULES)),
        _num("layout_ratio", _t(lang, "ratio_label"), lay["ratio"], 0.3, 3, "", 2, 0.05,
             when=[("layout_rule", ["ratio"])]),
        _num("layout_L_min", _t(lang, "L_min_label"), lay["L_min"], 0, 50, "m", 2, 0.1,
             when=[("layout_rule", ["ratio"])]),
        _num("layout_L", _t(lang, "L_fixed_label"), lay["L"], 0.5, 100, "m", 2, 0.1,
             when=[("layout_rule", ["fixed"])]),
        Field("layout_type", _t(lang, "layout_type_label"), "reftype", lay["type"]),
    ], note=_t(lang, "layout_note"))]


def option_groups(lang: str = "en") -> List[Group]:
    o = DEFAULT_CONFIG["options"]
    c = DEFAULT_CONFIG["corrosion"]
    s = DEFAULT_CONFIG["seismic"]
    k = DEFAULT_CONFIG["criteria"]
    asd = [("design", ["asd"])]
    lrfd = [("design", ["lrfd"])]
    quake = [("seismic_enabled", [True])]
    return [
        Group(_t(lang, "group_options"), [
            _select("design", _t(lang, "design_label"), o["design"],
                    _choices(lang, "design", DESIGNS)),
            _select("bearing_method", _t(lang, "bearing_method_label"), o["bearing_method"],
                    _choices(lang, "method", BEARING_METHODS)),
            _check("bearing_embedment", _t(lang, "bearing_embedment_label"),
                   o["bearing_embedment"]),
            _check("bearing_inclination", _t(lang, "bearing_inclination_label"),
                   o["bearing_inclination"]),
            _num("Cds", _t(lang, "Cds_label"), o["Cds"], 0.1, 1.0, "", 2, 0.05),
        ], note=_t(lang, "options_note")),
        Group(_t(lang, "group_criteria"), [
            _num("FS_sliding", _t(lang, "FS_sliding_label"), k["FS_sliding"], 1, 5, "", 2, 0.1),
            _num("FS_overturning", _t(lang, "FS_overturning_label"), k["FS_overturning"],
                 1, 5, "", 2, 0.1),
            _num("ecc_asd", _t(lang, "ecc_asd_label"), k["ecc_asd"], 2, 20, "", 1, 1),
            _num("FS_bearing", _t(lang, "FS_bearing_label"), k["FS_bearing"], 1, 6, "", 2, 0.1),
            _num("FS_tensile", _t(lang, "FS_tensile_label"), k["FS_tensile"], 1, 5, "", 2, 0.1),
            _num("steel_ratio", _t(lang, "steel_ratio_label"), k["steel_ratio"], 0.2, 1,
                 "", 2, 0.01),
            _num("FS_pullout", _t(lang, "FS_pullout_label"), k["FS_pullout"], 1, 5, "", 2, 0.1),
            _num("FS_connection", _t(lang, "FS_connection_label"), k["FS_connection"],
                 1, 5, "", 2, 0.1),
            _num("seismic_ratio", _t(lang, "seismic_ratio_label"), k["seismic_ratio"],
                 0.5, 1, "", 2, 0.05),
            _num("min_Le", _t(lang, "min_Le_label"), k["min_Le"], 0, 5, "m", 2, 0.1),
        ], note=_t(lang, "criteria_note"), when=_when(asd)),
        Group(_t(lang, "group_criteria_lrfd"), [
            _num("phi_sliding", _t(lang, "phi_sliding_label"), k["phi_sliding"], 0.3, 1.2,
                 "", 2, 0.05),
            _num("phi_bearing", _t(lang, "phi_bearing_label"), k["phi_bearing"], 0.3, 1.2,
                 "", 2, 0.05),
            _num("ecc_lrfd", _t(lang, "ecc_lrfd_label"), k["ecc_lrfd"], 2, 20, "", 1, 1),
            _num("phi_steel", _t(lang, "phi_steel_label"), k["phi_steel"], 0.3, 1.2, "", 2,
                 0.05),
            _num("phi_geo", _t(lang, "phi_geo_label"), k["phi_geo"], 0.3, 1.2, "", 2, 0.05),
            _num("phi_pullout", _t(lang, "phi_pullout_label"), k["phi_pullout"], 0.3, 1.2,
                 "", 2, 0.05),
            _num("min_Le_lrfd", _t(lang, "min_Le_label"), k["min_Le"], 0, 5, "m", 2, 0.1),
        ], note=_t(lang, "criteria_lrfd_note"), when=_when(lrfd)),
        Group(_t(lang, "group_corrosion"), [
            _num("design_life", _t(lang, "design_life_label"), c["design_life"], 0, 200,
                 "yr", 0, 5),
            _num("zinc", _t(lang, "zinc_label"), c["zinc"], 0, 500, "µm", 0, 1),
            _num("steel_rate", _t(lang, "steel_rate_label"), c["steel_rate"], 0, 100,
                 "µm/yr", 1, 1),
        ], note=_t(lang, "corrosion_note")),
        Group(_t(lang, "group_seismic"), [
            _check("seismic_enabled", _t(lang, "seismic_enabled_label"), s["enabled"]),
            _num("A", _t(lang, "A_label"), s["A"], 0, 0.99, "", 3, 0.01, when=quake),
            _num("pullout_factor", _t(lang, "pullout_factor_label"), s["pullout_factor"],
                 0.1, 1, "", 2, 0.05, when=quake),
        ], note=_t(lang, "seismic_note")),
    ]


def height_groups(lang: str = "en") -> List[Group]:
    h = DEFAULT_CONFIG["heights"]
    return [Group(_t(lang, "group_heights"), [
        _num("H_min", _t(lang, "H_min_label"), h["H_min"], 0.5, 40, "m", 2, 0.5),
        _num("H_max", _t(lang, "H_max_label"), h["H_max"], 0.5, 40, "m", 2, 0.5),
        _num("H_step", _t(lang, "step_label"), h["step"], 0.1, 10, "m", 2, 0.25),
    ], note=_t(lang, "heights_note"))]


# --------------------------------------------------------------------------- #
#  Tables: reinforcement types, layers
# --------------------------------------------------------------------------- #

TYPE_NUMBERS = ["Tult", "RFID", "RFCR", "RFD", "Rc", "b", "t", "Fy", "Sh", "Ci", "F0",
                "alpha", "CR"]

#: Columns that mean nothing for one family, which the table greys out
GEO_ONLY = ["Tult", "RFID", "RFCR", "RFD", "Rc", "Ci"]
STEEL_ONLY = ["b", "t", "Fy", "Sh", "F0"]


def type_columns(lang: str = "en") -> List[dict]:
    """Columns of the reinforcement type table."""
    return ([{"key": "name", "label": _t(lang, "col_name"), "kind": "text"},
             {"key": "kind", "label": _t(lang, "col_kind"), "kind": "select",
              "options": [{"value": v, "label": _t(lang, f"kind_{v}")} for v in KINDS]}]
            + [{"key": key, "label": _t(lang, f"col_{key}"), "kind": "number"}
               for key in TYPE_NUMBERS])


def layer_columns(lang: str = "en") -> List[dict]:
    """Columns of the layer table; the type's options are the names in the type table."""
    return [{"key": "z", "label": _t(lang, "col_z"), "kind": "number"},
            {"key": "L", "label": _t(lang, "col_L"), "kind": "number"},
            {"key": "type", "label": _t(lang, "col_type"), "kind": "reftype"}]


def default_types() -> List[dict]:
    return [dict(t) for t in DEFAULT_CONFIG["reinforcement_types"]]


def default_layers() -> List[dict]:
    return [dict(layer) for layer in DEFAULT_CONFIG["layers"]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #

def schema(lang: str = "en") -> dict:
    """The whole schema the browser builds its forms from, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "wall": {"groups": [g.to_dict() for g in wall_groups(lang)]},
        "layout": {"groups": [g.to_dict() for g in layout_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "heights": {"groups": [g.to_dict() for g in height_groups(lang)]},
        "types": {"columns": type_columns(lang), "rows": default_types(),
                  "note": _t(lang, "types_note"),
                  "geo_only": list(GEO_ONLY), "steel_only": list(STEEL_ONLY)},
        "layers": {"columns": layer_columns(lang), "rows": default_layers(),
                   "note": _t(lang, "layers_note")},
    }


def _all_groups(lang: str = "en") -> List[Group]:
    return (project_groups(lang) + wall_groups(lang) + layout_groups(lang)
            + option_groups(lang) + height_groups(lang))


def defaults(lang: str = "en") -> Dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: Dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    values["reinforcement_types"] = default_types()
    values["layers"] = default_layers()
    return values


# --------------------------------------------------------------------------- #
#  Readers: flat values <-> configuration dictionary
# --------------------------------------------------------------------------- #

def _f(values: dict, key: str, default: float = 0.0) -> float:
    """A numeric field; missing or empty falls back to the default."""
    v = values.get(key, default)
    if v is None or v == "":
        return float(default)
    try:
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _b(values: dict, key: str, default: bool = False) -> bool:
    v = values.get(key, default)
    return bool(default if v is None or v == "" else v)


def _s(values: dict, key: str, default: str = "", allowed: Optional[List[str]] = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def read_types(values: dict) -> List[dict]:
    """Reinforcement types from the table; rows without a name are dropped and a
    repeated name keeps its first row."""
    out, seen = [], set()
    for row in values.get("reinforcement_types") or []:
        name = str(row.get("name") or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        kind = _s(row, "kind", "strip", KINDS)
        base = next(t for t in DEFAULT_CONFIG["reinforcement_types"] if t["kind"] == kind)
        rtype = {"name": name, "kind": kind}
        for key in TYPE_NUMBERS:
            rtype[key] = _f(row, key, base[key])
        out.append(rtype)
    return out


def read_layers(values: dict) -> List[dict]:
    """Layers from the table; rows without a usable height or length are dropped."""
    out = []
    for row in values.get("layers") or []:
        try:
            z = float(row.get("z"))
            length = float(row.get("L"))
        except (TypeError, ValueError):
            continue
        out.append({"z": z, "L": length, "type": str(row.get("type") or "").strip()})
    return sorted(out, key=lambda r: r["z"])


def to_config(values: dict) -> Dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    d = DEFAULT_CONFIG
    cfg = copy.deepcopy(d)
    cfg["project_info"] = {"title": _s(values, "title", d["project_info"]["title"]),
                           "analyst": str(values.get("analyst") or "")}
    cfg["geometry"] = {key: _f(values, key, d["geometry"][key]) for key in d["geometry"]}
    q = d["loads"]
    cfg["loads"] = {
        "q_dead": _f(values, "q_dead", q["q_dead"]), "q_live": _f(values, "q_live", q["q_live"]),
        "strip_enabled": _b(values, "strip_enabled", q["strip_enabled"]),
        "strip_P": _f(values, "strip_P", q["strip_P"]),
        "strip_width": _f(values, "strip_width", q["strip_width"]),
        "strip_offset": _f(values, "strip_offset", q["strip_offset"]),
        "strip_live": _b(values, "strip_live", q["strip_live"]),
    }
    s = d["soils"]
    cfg["soils"] = {
        "reinforced": {"gamma": _f(values, "gamma_r", s["reinforced"]["gamma"]),
                       "phi": _f(values, "phi_r", s["reinforced"]["phi"])},
        "retained": {"gamma": _f(values, "gamma_b", s["retained"]["gamma"]),
                     "phi": _f(values, "phi_b", s["retained"]["phi"])},
        "foundation": {"gamma": _f(values, "gamma_f", s["foundation"]["gamma"]),
                       "gamma_sat": _f(values, "gamma_sat_f", s["foundation"]["gamma_sat"]),
                       "phi": _f(values, "phi_f", s["foundation"]["phi"]),
                       "c": _f(values, "c_f", s["foundation"]["c"])},
        "water_depth": _f(values, "water_depth", s["water_depth"]),
        "gamma_water": _f(values, "gamma_water", s["gamma_water"]),
    }
    cfg["reinforcement_types"] = read_types(values)
    cfg["layers"] = read_layers(values)
    cfg["corrosion"] = {key: _f(values, key, d["corrosion"][key]) for key in d["corrosion"]}
    o = d["options"]
    cfg["options"] = {
        "design": _s(values, "design", o["design"], DESIGNS),
        "bearing_method": _s(values, "bearing_method", o["bearing_method"], BEARING_METHODS),
        "bearing_embedment": _b(values, "bearing_embedment", o["bearing_embedment"]),
        "bearing_inclination": _b(values, "bearing_inclination", o["bearing_inclination"]),
        "Cds": _f(values, "Cds", o["Cds"]),
    }
    e = d["seismic"]
    cfg["seismic"] = {"enabled": _b(values, "seismic_enabled", e["enabled"]),
                      "A": _f(values, "A", e["A"]),
                      "pullout_factor": _f(values, "pullout_factor", e["pullout_factor"])}
    crit = {key: _f(values, key, d["criteria"][key]) for key in d["criteria"]}
    if cfg["options"]["design"] == "lrfd":
        crit["min_Le"] = _f(values, "min_Le_lrfd", d["criteria"]["min_Le"])
    cfg["criteria"] = crit
    lay = d["layout"]
    cfg["layout"] = {
        "z1": _f(values, "layout_z1", lay["z1"]), "Sv": _f(values, "layout_Sv", lay["Sv"]),
        "rule": _s(values, "layout_rule", lay["rule"], LAYOUT_RULES),
        "ratio": _f(values, "layout_ratio", lay["ratio"]),
        "L": _f(values, "layout_L", lay["L"]), "L_min": _f(values, "layout_L_min", lay["L_min"]),
        "type": _s(values, "layout_type", lay["type"]),
    }
    h = d["heights"]
    cfg["heights"] = {"H_min": _f(values, "H_min", h["H_min"]),
                      "H_max": _f(values, "H_max", h["H_max"]),
                      "step": _f(values, "H_step", h["step"])}
    return cfg


#: Flat key <- (path of the configuration)
_MAP = ([("title", ("project_info", "title")), ("analyst", ("project_info", "analyst"))]
        + [(k, ("geometry", k)) for k in DEFAULT_CONFIG["geometry"]]
        + [(k, ("loads", k)) for k in DEFAULT_CONFIG["loads"]]
        + [("gamma_r", ("soils", "reinforced", "gamma")), ("phi_r", ("soils", "reinforced", "phi")),
           ("gamma_b", ("soils", "retained", "gamma")), ("phi_b", ("soils", "retained", "phi")),
           ("gamma_f", ("soils", "foundation", "gamma")),
           ("gamma_sat_f", ("soils", "foundation", "gamma_sat")),
           ("phi_f", ("soils", "foundation", "phi")), ("c_f", ("soils", "foundation", "c")),
           ("water_depth", ("soils", "water_depth")), ("gamma_water", ("soils", "gamma_water"))]
        + [(k, ("corrosion", k)) for k in DEFAULT_CONFIG["corrosion"]]
        + [(k, ("options", k)) for k in DEFAULT_CONFIG["options"]]
        + [("seismic_enabled", ("seismic", "enabled")), ("A", ("seismic", "A")),
           ("pullout_factor", ("seismic", "pullout_factor"))]
        + [(k, ("criteria", k)) for k in DEFAULT_CONFIG["criteria"]]
        + [("min_Le_lrfd", ("criteria", "min_Le"))]
        + [(f"layout_{k}", ("layout", k)) for k in DEFAULT_CONFIG["layout"]]
        + [("H_min", ("heights", "H_min")), ("H_max", ("heights", "H_max")),
           ("H_step", ("heights", "step"))])


def _lookup(cfg: dict, path):
    node = cfg
    for key in path:
        if not isinstance(node, dict) or key not in node:
            raise KeyError(key)
        node = node[key]
    return node


def from_config(cfg: dict, base: Optional[dict] = None) -> Dict[str, Any]:
    """Flat values from a nested configuration — reads a `.msew` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, path in _MAP:
        try:
            values[flat] = _lookup(cfg, path)
        except KeyError:
            continue
    if isinstance(cfg.get("reinforcement_types"), list) and cfg["reinforcement_types"]:
        values["reinforcement_types"] = [dict(t) for t in cfg["reinforcement_types"]
                                         if isinstance(t, dict)]
    if isinstance(cfg.get("layers"), list) and cfg["layers"]:
        values["layers"] = [dict(layer) for layer in cfg["layers"] if isinstance(layer, dict)]
    return values


def project_file(values: dict) -> Dict[str, Any]:
    """What `Save` writes: the configuration, with a format stamp."""
    return {"format": FILE_FORMAT, "version": FILE_VERSION, **to_config(values)}

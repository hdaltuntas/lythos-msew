"""
Configuration for Lythos MSEW: the default project, the choice lists, and the
theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `lythosmsew.i18n`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = ["APP_NAME", "APP_VERSION", "DEFAULT_CONFIG", "THEMES", "PLOT_PALETTE",
           "SOIL_FILL", "KIND_COLORS", "METHOD_COLORS", "KINDS", "GEOSYNTHETICS", "SHEETS",
           "DESIGNS", "BEARING_METHODS", "LAYOUT_RULES", "ACCENT"]

# --- Choice lists (the first entry is the default where one is needed) -----
#: Reinforcement kinds: the inextensible steel strip, and three extensible
#: geosynthetics — the polymer strip (a polyester core in a polyethylene
#: sheath, placed and spaced like a steel strip), the geogrid and the
#: geotextile. The kind decides the coefficient of lateral earth pressure, the
#: shape of the failure surface, the strength and the pullout parameters.
KINDS = ["strip", "polymer_strip", "geogrid", "geotextile"]
GEOSYNTHETICS = ("polymer_strip", "geogrid", "geotextile")

#: The geosynthetics laid as continuous sheets, along which the fill can slide
SHEETS = ("geogrid", "geotextile")

#: Allowable stress design (factors of safety) or load and resistance factors
DESIGNS = ["asd", "lrfd"]

#: The bearing capacity factor sets offered for the foundation of the wall
BEARING_METHODS = ["vesic", "meyerhof", "hansen", "terzaghi", "ec7"]

#: How the layout generator picks the reinforcement length
LAYOUT_RULES = ["ratio", "fixed"]

# --- Interface theme (web/static/style.css) and plot palette ---------------
# --- kept together so the figures always match the page they are shown on. -
ACCENT = "#C6613F"

THEMES = {
    "dark": dict(bg="#262624", panel="#30302E", input_bg="#262624", fg="#F5F4ED",
                 fg_dim="#A6A39A", border="#4A4944", hover="#3A3A37", btn="#3A3A37",
                 muted="#6B6A64", accent="#D97757", accent_hover="#E08B6E"),
    "light": dict(bg="#F5F4ED", panel="#FAF9F5", input_bg="#FFFFFF", fg="#141413",
                  fg_dim="#73726C", border="#E3E0D5", hover="#F0EEE6", btn="#F0EEE6",
                  muted="#B7B4AA", accent=ACCENT, accent_hover="#B0532F"),
}
# The report's figures: the light palette on white paper.
THEMES["paper"] = dict(THEMES["light"], bg="#FFFFFF", panel="#FFFFFF")

# Semantic colours: the same quantity is the same colour in every figure. Warm
# and muted, to sit on the paper-coloured page; terracotta marks the demand.
PLOT_PALETTE = dict(
    demand="#C6613F", capacity="#4E9A8A", required="#B0413E", seismic="#8C6BB1",
    pullout="#5B8DB8", connection="#D9A55B", sliding="#A26A12", tensile="#4E9A8A",
    water="#6FA8C7", facing="#8A8680", failure="#B0413E", thrust="#C6613F",
    weight="#6B6A64", surcharge="#8C6BB1", pressure="#D9A55B", ok="#5E8C4A",
    bad="#B0413E", ultimate="#C6613F", allowable="#4E9A8A", applied="#B0413E",
)

#: One colour per reinforcement kind, so a layer keeps its colour everywhere.
KIND_COLORS = {"strip": "#5B6770", "polymer_strip": "#8C6BB1", "geogrid": "#C6613F",
               "geotextile": "#4E9A8A"}

#: One colour per bearing capacity method.
METHOD_COLORS = {"terzaghi": "#5B8DB8", "meyerhof": "#8C6BB1", "hansen": "#D9A55B",
                 "vesic": "#C6613F", "ec7": "#4E9A8A"}

# Fill colours of the three soils in the section (theme-dependent, since a
# light sandy tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"reinforced": "#E3C98F", "retained": "#D8CDB6", "foundation": "#A7B8A0"},
    "dark": {"reinforced": "#8A7250", "retained": "#6F6655", "foundation": "#5E6E58"},
}
SOIL_FILL["paper"] = SOIL_FILL["light"]

DEFAULT_CONFIG = {
    "project_info": {
        "title": "Project: MSE wall with steel strips",
        "analyst": "",
    },
    "geometry": {
        "H": 6.0,                  # design height, top of the levelling pad to the top [m]
        "embedment": 0.60,         # depth of the base below the ground in front [m]
        "batter": 0.0,             # ω, batter of the face from the vertical [°]
        "backslope": 0.0,          # β, slope of the backfill above the wall [°]
        "toe_slope": 0.0,          # slope of the ground in front of the wall [°]
        "facing": 0.14,            # thickness of the facing, for the drawing [m]
    },
    # Uniform surcharges on the top of the wall and the backfill, and an
    # optional strip load (a footing, a barrier) on the reinforced zone.
    "loads": {
        "q_dead": 0.0,             # permanent uniform surcharge [kPa]
        "q_live": 10.0,            # live (traffic) uniform surcharge [kPa]
        "strip_enabled": False,
        "strip_P": 60.0,           # vertical strip load [kN/m]
        "strip_width": 1.0,        # width of the strip load [m]
        "strip_offset": 1.5,       # distance from the face to its centre [m]
        "strip_live": False,       # is the strip load a live load?
    },
    "soils": {
        "reinforced": {"gamma": 19.0, "phi": 34.0},
        "retained": {"gamma": 18.0, "phi": 30.0},
        "foundation": {"gamma": 18.5, "gamma_sat": 20.0, "phi": 30.0, "c": 5.0},
        "water_depth": 20.0,       # depth of the water table below the base [m]
        "gamma_water": 9.81,
    },
    # Reinforcement types, referred to by name from the layer table. The
    # geosynthetic columns and the steel columns apply to their own kinds.
    #   Tult   ultimate tensile strength of a geosynthetic [kN/m]
    #   RFID, RFCR, RFD  installation damage, creep and durability reductions
    #   Rc     coverage ratio of a geosynthetic (a strip's is b/Sh)
    #   b, t   width and thickness of a steel strip [mm]; Fy its yield [MPa]
    #   Sh     horizontal spacing of the strips [m]
    #   Ci     interaction coefficient of a geosynthetic, F* = Ci·tan φ
    #   F0     F* of a ribbed strip at the top of the wall (tan φ at 6 m)
    #   alpha  scale effect correction α
    #   CR     connection strength as a share of the long-term strength
    "reinforcement_types": [
        {"name": "Strip 50x4", "kind": "strip", "Tult": 0.0, "RFID": 1.0, "RFCR": 1.0,
         "RFD": 1.0, "Rc": 1.0, "b": 50.0, "t": 4.0, "Fy": 450.0, "Sh": 0.50,
         "Ci": 0.0, "F0": 2.0, "alpha": 1.0, "CR": 1.0},
        {"name": "Geogrid 80", "kind": "geogrid", "Tult": 80.0, "RFID": 1.10, "RFCR": 1.60,
         "RFD": 1.10, "Rc": 1.0, "b": 0.0, "t": 0.0, "Fy": 0.0, "Sh": 0.0,
         "Ci": 0.67, "F0": 0.0, "alpha": 0.8, "CR": 0.80},
        {"name": "Geotextile 60", "kind": "geotextile", "Tult": 60.0, "RFID": 1.20,
         "RFCR": 1.70, "RFD": 1.10, "Rc": 1.0, "b": 0.0, "t": 0.0, "Fy": 0.0, "Sh": 0.0,
         "Ci": 0.67, "F0": 0.0, "alpha": 0.6, "CR": 0.80},
    ],
    # Reinforcement layers from the base up: height above the levelling pad,
    # length measured from the face, and the type.
    "layers": [
        {"z": 0.375 + 0.75 * i, "L": 5.4, "type": "Strip 50x4"} for i in range(8)
    ],
    "corrosion": {
        "design_life": 75.0,       # years
        "zinc": 86.0,              # galvanising thickness [µm]
        "steel_rate": 12.0,        # carbon steel loss per side after the zinc is gone [µm/yr]
    },
    "options": {
        "design": "asd",
        "bearing_method": "vesic",
        "bearing_embedment": False,    # count the embedment as a surcharge on the base
        "bearing_inclination": False,  # load inclination factors in the bearing capacity
        "Cds": 0.80,                   # direct sliding coefficient of a geosynthetic
    },
    "seismic": {
        "enabled": False,
        "A": 0.20,                 # peak ground acceleration coefficient
        "pullout_factor": 0.80,    # reduction of F* under seismic loading
    },
    "criteria": {
        # ASD: required factors of safety
        "FS_sliding": 1.5,
        "FS_overturning": 2.0,
        "ecc_asd": 6.0,            # e ≤ L / ecc_asd
        "FS_bearing": 2.5,
        "FS_tensile": 1.5,         # geosynthetics: T_al / FS
        "steel_ratio": 0.55,       # steel: T_a = 0.55·Fy·Ac
        "FS_pullout": 1.5,
        "FS_connection": 1.5,
        "seismic_ratio": 0.75,     # seismic factors of safety are this share of static
        # LRFD: resistance factors
        "phi_sliding": 1.00,
        "phi_bearing": 0.65,
        "ecc_lrfd": 3.0,           # e ≤ L / ecc_lrfd
        "phi_steel": 0.75,
        "phi_geo": 0.90,
        "phi_pullout": 0.90,
        "min_Le": 0.90,            # minimum embedment length beyond the active zone [m]
    },
    # The rule the layout generator and the height study use.
    "layout": {
        "z1": 0.375,               # height of the first layer [m]
        "Sv": 0.75,                # vertical spacing [m]
        "rule": "ratio",
        "ratio": 0.90,             # L / H
        "L": 5.0,                  # fixed length [m]
        "L_min": 2.40,             # the shortest length the rule may give [m]
        "type": "Strip 50x4",
    },
    "heights": {"H_min": 3.0, "H_max": 12.0, "step": 0.5},
}

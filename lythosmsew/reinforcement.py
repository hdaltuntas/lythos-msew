"""
The reinforcement: its long-term strength, its pullout resistance, and the
coefficient of lateral earth pressure it lets the fill develop.

Two families behave differently, and every expression here depends on which
one a layer belongs to:

    inextensible   steel strips. The fill barely strains before the steel
                   carries the load, so the pressure near the top is above
                   the active value (Kr/Ka from 1.7 at the top to 1.2 at 6 m
                   and below), the failure surface is the bilinear
                   "coherent gravity" line, and the strength is the steel
                   section left after corrosion over the design life.
    extensible     polymer strips, geogrids and geotextiles. The fill reaches the active
                   state (Kr/Ka = 1), the failure surface is Rankine's plane,
                   and the long-term strength is the ultimate strength
                   divided by the installation damage, creep and durability
                   reduction factors. A polymer strip's Tult is per strip,
                   and it is spaced like a steel strip.

Every strength is returned per metre of wall, so a steel strip's strength is
already divided by its horizontal spacing and a geosynthetic's already
multiplied by its coverage ratio: the caller compares it with the tension
per metre of wall directly.

Corrosion of galvanised steel follows FHWA-NHI-10-024: the zinc is lost at
15 µm a year for the first two years and 4 µm a year after that; once it is
gone, the carbon steel is lost at the given rate on each face.
"""

from __future__ import annotations

import math
from typing import Dict

from .config import GEOSYNTHETICS, SHEETS

__all__ = ["ZINC_FIRST_RATE", "ZINC_LATER_RATE", "PULLOUT_C", "zinc_life",
           "sacrificial_thickness", "strength", "kr_ratio", "f_star", "pullout",
           "is_extensible", "is_sheet"]

#: Zinc loss for the first two years, and after them [µm/yr]
ZINC_FIRST_RATE = 15.0
ZINC_LATER_RATE = 4.0
ZINC_FIRST_YEARS = 2.0

#: Pullout surfaces: the reinforcement is gripped on both faces
PULLOUT_C = 2.0

#: Depth below which Kr/Ka and F* of a steel strip stop changing [m]
TRANSITION_DEPTH = 6.0


def is_extensible(kind: str) -> bool:
    return kind in GEOSYNTHETICS


def is_sheet(kind: str) -> bool:
    """A geogrid or a geotextile: a continuous plane the fill can slide along."""
    return kind in SHEETS


def zinc_life(zinc: float) -> float:
    """Years until the galvanising is gone."""
    zinc = max(float(zinc), 0.0)
    first = ZINC_FIRST_RATE * ZINC_FIRST_YEARS
    if zinc <= first:
        return zinc / ZINC_FIRST_RATE
    return ZINC_FIRST_YEARS + (zinc - first) / ZINC_LATER_RATE


def sacrificial_thickness(design_life: float, zinc: float, steel_rate: float) -> float:
    """Steel thickness lost over the design life, both faces together [mm]."""
    years = max(float(design_life) - zinc_life(zinc), 0.0)
    return 2.0 * max(float(steel_rate), 0.0) * years / 1000.0


def strength(rtype: dict, corrosion: dict) -> Dict[str, float]:
    """Long-term strength of one reinforcement type, per metre of wall.

    Returns
        T_lt   long-term (nominal) strength: the corroded steel section at yield,
               or Tult / (RFID·RFCR·RFD) for a geosynthetic, times its coverage
        T_dyn  the strength against a short seismic load: the same steel, or
               Tult / (RFID·RFD) for a geosynthetic — creep does not act on it
        Rc     coverage ratio
        and, for a steel strip, the corroded thickness Ec, the section Ac and
        the sacrificial thickness Es.
    """
    kind = rtype["kind"]
    if kind == "polymer_strip":
        # Tult per strip; b/Sh of the plan is covered
        sh = rtype["Sh"]
        t_al = rtype["Tult"] / (rtype["RFID"] * rtype["RFCR"] * rtype["RFD"])
        return {"T_lt": t_al / sh, "T_dyn": rtype["Tult"] / (rtype["RFID"] * rtype["RFD"]) / sh,
                "T_al": t_al, "Rc": rtype["b"] / 1000.0 / sh,
                "RF": rtype["RFID"] * rtype["RFCR"] * rtype["RFD"], "Ec": 0.0, "Ac": 0.0,
                "Es": 0.0}
    if is_extensible(kind):
        rf = rtype["RFID"] * rtype["RFCR"] * rtype["RFD"]
        rc = rtype["Rc"]
        t_al = rtype["Tult"] / rf
        return {"T_lt": t_al * rc, "T_dyn": rtype["Tult"] / (rtype["RFID"] * rtype["RFD"]) * rc,
                "T_al": t_al, "Rc": rc, "RF": rf, "Ec": 0.0, "Ac": 0.0, "Es": 0.0}

    es = sacrificial_thickness(corrosion["design_life"], corrosion["zinc"],
                               corrosion["steel_rate"])
    ec = max(rtype["t"] - es, 0.0)
    ac = rtype["b"] * ec                                   # mm²
    per_strip = rtype["Fy"] * ac / 1000.0                  # kN
    sh = rtype["Sh"]
    return {"T_lt": per_strip / sh, "T_dyn": per_strip / sh, "T_al": per_strip,
            "Rc": rtype["b"] / 1000.0 / sh, "RF": 1.0, "Ec": ec, "Ac": ac, "Es": es}


def kr_ratio(kind: str, depth: float) -> float:
    """Kr / Ka at a depth below the top of the wall (AASHTO simplified method)."""
    if is_extensible(kind):
        return 1.0
    z = min(max(float(depth), 0.0), TRANSITION_DEPTH)
    return 1.7 - 0.5 * z / TRANSITION_DEPTH


def f_star(rtype: dict, depth: float, phi: float) -> float:
    """The pullout resistance factor F* at a depth below the top of the wall.

    A geosynthetic: Ci·tan φ. A ribbed steel strip: F0 at the top, falling
    linearly to tan φ at 6 m and constant below.
    """
    tan_phi = math.tan(math.radians(float(phi)))
    if is_extensible(rtype["kind"]):
        return rtype["Ci"] * tan_phi
    z = min(max(float(depth), 0.0), TRANSITION_DEPTH)
    return rtype["F0"] + (tan_phi - rtype["F0"]) * z / TRANSITION_DEPTH


def pullout(F: float, alpha: float, sigma_v: float, Le: float, Rc: float) -> float:
    """Pullout resistance per metre of wall, Pr = F*·α·σ'v·Le·C·Rc."""
    return F * alpha * max(sigma_v, 0.0) * max(Le, 0.0) * PULLOUT_C * Rc

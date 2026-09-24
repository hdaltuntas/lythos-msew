"""
A catalogue of the reinforcement found on the market, to add to the type table
in one click.

The entries are the sizes and strength classes manufacturers commonly offer,
with the reduction factors, interaction coefficients and scale corrections
FHWA-NHI-10-024 gives as typical values for each family. They are generic:
no entry is one manufacturer's product. They are starting points, not design
values; a project uses the values of the product actually specified, from its
datasheet and its certificates (BBA, NTPEP, CE), and the table stays editable
after an entry is added.

    steel_ha      galvanised ribbed ("high adherence") steel strips, bolted to
                  the facing: S355 (Fy 355 MPa) in the European sizes, and the
                  American 50 × 4 mm in Grade 65 (Fy 450 MPa). Zinc 86 µm.
    polymer       polymer strips: a polyester core in a polyethylene sheath,
                  laid in loops like a steel strip. Tult per strip.
    geogrid_hdpe  uniaxial extruded HDPE geogrids.
    geogrid_pet   coated polyester (PET) geogrids.
    geotextile    woven polyester and polypropylene geotextiles.

The horizontal spacing Sh is a first guess — two steel strips per metre, four
legs of a looped polymer strip per metre — and depends on the facing panel.
A polymer strip's pullout (Ci, α) belongs to the product's own pullout tests
more than to any other value here.
"""

from __future__ import annotations

from typing import Dict, List

__all__ = ["FAMILIES", "CATALOG", "entry", "catalog"]

#: Families in the order the interface lists them
FAMILIES = ["steel_ha", "polymer", "geogrid_hdpe", "geogrid_pet", "geotextile"]

_ZERO = {"Tult": 0.0, "RFID": 1.0, "RFCR": 1.0, "RFD": 1.0, "Rc": 1.0, "b": 0.0, "t": 0.0,
         "Fy": 0.0, "Sh": 0.0, "Ci": 0.0, "F0": 0.0, "alpha": 1.0, "CR": 1.0}


def _steel(b: float, t: float, fy: float, grade: str) -> dict:
    return dict(_ZERO, name=f"HA strip {b:.0f}x{t:.0f} {grade}", kind="strip", b=b, t=t, Fy=fy,
                Sh=0.50, F0=2.0, alpha=1.0, CR=1.0)


def _polymer(tult: float, b: float) -> dict:
    return dict(_ZERO, name=f"PET strip {tult:g} kN", kind="polymer_strip", Tult=tult, b=b,
                Sh=0.25, RFID=1.05, RFCR=1.50, RFD=1.10, Ci=0.80, alpha=0.8, CR=0.80)


def _grid(polymer: str, tult: float) -> dict:
    if polymer == "HDPE":
        rf = {"RFID": 1.10, "RFCR": 2.60, "RFD": 1.10}
        ci = 0.80
    else:
        rf = {"RFID": 1.15, "RFCR": 1.60, "RFD": 1.10}
        ci = 0.67
    return dict(_ZERO, name=f"{polymer} geogrid {tult:g}", kind="geogrid", Tult=tult, Rc=1.0,
                Ci=ci, alpha=0.8, CR=0.80, **rf)


def _textile(polymer: str, tult: float) -> dict:
    creep = 1.70 if polymer == "PET" else 4.00
    return dict(_ZERO, name=f"{polymer} woven geotextile {tult:g}", kind="geotextile",
                Tult=tult, Rc=1.0, RFID=1.20, RFCR=creep, RFD=1.10, Ci=0.67, alpha=0.6,
                CR=0.80)


#: family -> the entries of the family, in the order they are offered
CATALOG: Dict[str, List[dict]] = {
    "steel_ha": [_steel(b, t, 355.0, "S355") for b, t in
                 ((40, 4), (40, 5), (45, 5), (50, 4), (50, 5), (60, 4), (60, 5))]
                + [_steel(50, 4, 450.0, "Gr65")],
    "polymer": [_polymer(t, 50.0) for t in (20, 30, 37.5, 50)]
               + [_polymer(t, 90.0) for t in (75, 100)],
    "geogrid_hdpe": [_grid("HDPE", t) for t in (45, 70, 90, 120, 160)],
    "geogrid_pet": [_grid("PET", t) for t in (35, 55, 80, 110, 150, 200)],
    "geotextile": [_textile("PET", t) for t in (50, 100, 150, 200)]
                  + [_textile("PP", t) for t in (40, 60, 80)],
}


def entry(name: str) -> dict:
    """One catalogue entry by name, as a new row of the type table."""
    for rows in CATALOG.values():
        for row in rows:
            if row["name"] == name:
                return dict(row)
    raise KeyError(name)


def catalog(L: dict) -> List[dict]:
    """The catalogue as the interface lists it: families with their entries."""
    return [{"family": family, "label": L[f"family_{family}"],
             "entries": [dict(row) for row in CATALOG[family]]} for family in FAMILIES]

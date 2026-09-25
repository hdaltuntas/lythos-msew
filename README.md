**English** | [Türkçe](https://github.com/hdaltuntas/lythos-msew/blob/main/README.tr.md)

# Lythos MSEW

[![Tests](https://github.com/hdaltuntas/lythos-msew/actions/workflows/tests.yml/badge.svg)](https://github.com/hdaltuntas/lythos-msew/actions/workflows/tests.yml)

Mechanically stabilised earth (MSE) walls, driven from your browser. A reinforced soil wall —
a facing, layers of **steel strips, geogrids or geotextiles** in a compacted fill, and the
retained soil behind it — is designed and checked the way FHWA-NHI-10-024 and AASHTO LRFD
11.10 do it, and the way the MSEW program made familiar:

1. **Earth pressure** — Coulomb / Rankine Ka of the retained and the reinforced fill, with a
   battered face and a sloping backfill.
2. **External stability** — sliding on the base (through the fill, on the foundation soil, or
   along a geosynthetic), overturning about the toe, the eccentricity of the resultant.
3. **Bearing capacity** of the foundation under the effective width B′ = L − 2e, by the factor
   sets of **Terzaghi, Meyerhof, Brinch Hansen, Vesić and EN 1997-1**, side by side — with the
   water table, the embedment, the load inclination and a slope in front of the toe.
4. **Internal stability, layer by layer** — the maximum tension by AASHTO's Simplified Method
   (Kr/Ka of 1.7 → 1.2 for strips, 1 for geosynthetics), then each layer's **tensile**,
   **pullout** (F*, α, Le beyond the active zone), **connection** and **sliding** checks.
5. **Reinforcement** — you enter the strips' **width, thickness, yield strength and spacing**
   (the section left after zinc and steel corrosion over the design life is worked out), or a
   geosynthetic's **ultimate strength and reduction factors** RFID·RFCR·RFD.
6. **Earthquake** — the pseudo-static method: Am = (1.45 − A)·A, the dynamic thrust PAE and the
   inertia PIR externally, the inertia of the active zone shared out among the layers internally.
7. **ASD or LRFD** — factors of safety, or load factors (EV, EH, ES, LS) and resistance factors φ.
8. **The length the wall needs** — the shortest uniform reinforcement length that satisfies the
   external and pullout checks, beside FHWA's minimum (0.7·H, 2.4 m).

On top of it, a **height study** runs the same design rule — first layer, spacing, length as a
share of the height, reinforcement type — over a range of wall heights, and shows at which
heights every check holds and how long the reinforcement has to be at each.

The whole program — every label, result text, figure and report — is bilingual in
**English and Turkish**, switchable while it runs.

The interface is a small HTTP server on your own machine, driven from a browser. That keeps
the program usable over a remote session or inside a container, where a desktop toolkit would
need a display it does not have, and it costs no dependency beyond the standard library.

> This is the sibling of [Lythos Bearing](https://github.com/hdaltuntas/lythos-bearing),
> [Lythos Settle](https://github.com/hdaltuntas/lythos-settle),
> [LythosFEA](https://github.com/hdaltuntas/lythos),
> [Lythos Kinematic](https://github.com/hdaltuntas/lythoskinematic),
> [Lythos SPWA](https://github.com/hdaltuntas/lythosspwa) and
> [LythosLE](https://github.com/hdaltuntas/lythosle), and follows the same architecture,
> theme and fonts. Its bearing capacity factors are Lythos Bearing's.

## Screenshots

| Results summary | Layer by layer |
|---|---|
| ![Summary](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_summary.png) | ![Layers](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_layers.png) |

| Section, dark theme, Turkish | Bearing capacity by method |
|---|---|
| ![Section](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_section_dark_tr.png) | ![Bearing](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_bearing_dark_tr.png) |

| Height study | Checks against the reinforcement length |
|---|---|
| ![Heights](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_heights_figure.png) | ![Length](https://raw.githubusercontent.com/hdaltuntas/lythos-msew/main/screenshots/msew_length.png) |

## Install & run

From a clone, with nothing installed but the scientific stack:

```bash
pip install numpy matplotlib reportlab
python main.py
```

or install the clone itself with `pip install .` (Word reports need `python-docx` and the
spreadsheet export of a height study `openpyxl`: `pip install ".[docx,xlsx]"`). Python 3.10+ is
required. `main.py` puts its own directory first on the import path, so the clone's code is
what runs even when `lythosmsew` is also installed.

## Command line

```bash
lythos-msew                                   # web interface (the default)
lythos-msew web --port 9000 --lang tr --no-browser
lythos-msew example -o project.msew           # a starter project file
lythos-msew run project.msew -o report.pdf    # analyse, print the results, write a report
lythos-msew heights project.msew -o heights.xlsx
```

`run` and `heights` read the same `.msew` file the interface saves, so a wall set up in the
browser can be re-run unattended. The interface listens on port 8782 by default.

## Inputs

* **Wall:** design height H, embedment d, face batter ω, backslope β, slope in front of the
  toe, facing thickness.
* **Surcharges:** permanent and live (traffic) uniform surcharges; a strip load (P, width,
  offset from the face, permanent or live).
* **Soils:** the reinforced fill (γ, φ′), the retained fill (γ, φ′), the foundation soil
  (γ, γsat, φ′, c′ — or φ = 0 and cu), the water table below the base.
* **Reinforcement catalogue:** typical market products added to the type table in one click —
  ribbed galvanised steel strips (HA 40×4 to 60×5 in S355, 50×4 in Grade 65), polymer strips
  (PET core, PE sheath, 20–100 kN per strip), uniaxial HDPE and PET geogrids (35–200 kN/m),
  woven PET and PP geotextiles — with FHWA's typical reduction factors and pullout parameters.
  Generic starting values: check them against the datasheet of the product specified.
* **Reinforcement types** (a table): name, kind (steel strip, polymer strip, geogrid, geotextile);
  geosynthetics — Tult, RFID, RFCR, RFD, coverage Rc, interaction Ci; steel strips — width b,
  thickness t, yield Fy, horizontal spacing Sh, F*₀ at the top; polymer strips — Tult per
  strip, the reduction factors, width b, spacing Sh, Ci; all — scale correction α and
  connection strength ratio CR.
* **Layers** (a table): height above the levelling pad z, length L, type. Or let the **layout
  generator** fill it: first layer, spacing Sv, L = ratio·H (never below a shortest length) or
  a fixed L, type.
* **Corrosion:** design life, galvanising thickness, carbon steel loss rate.
* **Design method:** ASD (FS for sliding, overturning, eccentricity, bearing, tensile,
  pullout, connection; 0.55·Fy for steel) or LRFD (φ for sliding, bearing, steel, geosynthetic,
  pullout); the minimum length beyond the active zone.
* **Bearing capacity:** the factor set; embedment and load inclination on or off; the direct
  sliding coefficient Cds of a geosynthetic.
* **Earthquake:** A, the reduction of F* under seismic loading.
* **Height study:** the range and the step.

## What it computes

| quantity | method |
|---|---|
| Ka | Coulomb (AASHTO 3.11.5.3), θ = 90 + ω from a 10° batter on; δ = β behind the block, δ = 0 inside it |
| forces | V1 = γr·H·L, the slope wedge over the block, F1 = ½·Ka·γ·h² and F2 = Ka·q·h at β, h = H + L·tan β |
| sliding | the weakest of tan φr, tan φf + c·L and Cds·tan φr; the live load over the block left out |
| overturning, eccentricity | moments about the toe; e ≤ L/6 (ASD), L/3 (LRFD), L/4 (seismic ASD) |
| bearing | B′ = L − 2e, σv = ΣV/B′ against q_ult by Terzaghi, Meyerhof, Hansen, Vesić, EN 1997-1 |
| Tmax | Kr·σv·Sv, σv = γr·Z + σ2 + q + Δσv (2:1 strip load), Kr/Ka 1.7 → 1.2 over 6 m for strips |
| active zone | Rankine 45 + φ/2 (extensible), bilinear 0.3·H1 (inextensible) |
| pullout | Pr = F*·α·σ′v·Le·C·Rc, C = 2, no live load; F* = Ci·tan φ, or F*₀ → tan φ over 6 m |
| strength | Tult/(RFID·RFCR·RFD)·Rc; Fy·b·Ec/Sh with Ec after zinc and steel corrosion |
| LRFD | EV 1.00/1.35, EH 1.50, ES 0.75/1.50, LS 1.75; φ as entered |
| earthquake | Am = (1.45 − A)·A; PAE = 0.375·Am·γ·H² (M–O with a backslope) at 0.6·H, ½PAE + PIR; Pi = Am·Wa by Le |
| required length | bisection on a uniform L until every external and pullout check holds |

The expressions, their sources and their limits are in
[docs/theory.md](https://github.com/hdaltuntas/lythos-msew/blob/main/docs/theory.md).

## Figures

Section to scale with the layers, the failure surface, the surcharges, the forces and the
bearing pressure · horizontal stress and the tension in the layers · every internal check as a
margin, layer by layer · pullout resistance against tension · external checks, static and
seismic · bearing capacity by method · the checks against the reinforcement length · the
seismic tension. Height study: the checks and the required length against the wall height.

## Reports

Choose PDF, self-contained HTML or Word in the header and press *Export report…*. The report
carries the inputs, the earth pressure and the forces with their arms, the external checks,
the bearing capacity by every method, the tension and pullout of every layer, the earthquake,
the required length, the figures, the warnings, the method notes and — if one was run — the
height study, in whichever language the interface is in.

## Project files (`.msew`)

JSON. *Save* writes every input, the tables included; *Open…* reads them back. Missing entries
keep their defaults.

## Modules

| file | content |
|---|---|
| `lythosmsew/earth.py` | Coulomb, Rankine, Mononobe–Okabe, Am |
| `lythosmsew/reinforcement.py` | Corrosion, long-term strength, Kr/Ka, F*, pullout |
| `lythosmsew/catalog.py` | Typical market reinforcement: steel and polymer strips, geogrids, geotextiles |
| `lythosmsew/factors.py`, `capacity.py` | Bearing capacity factors and the general equation (from Lythos Bearing) |
| `lythosmsew/engine.py` | The wall: forces, external checks, bearing, internal checks, earthquake, required length, layout generator |
| `lythosmsew/heights.py`, `height_plots.py` | The height study, its figures, CSV / XLSX |
| `lythosmsew/plotting.py`, `plot_style.py`, `render.py` | Matplotlib figures, theme-aware, off-screen |
| `lythosmsew/report.py`, `pdf.py` | Calculation report: one HTML assembly, exported as PDF, HTML or DOCX |
| `lythosmsew/forms.py` | Input schema and readers, with the conditions under which each field applies |
| `lythosmsew/summary.py` | The results as cards, tables and text, for the browser and the command line alike |
| `lythosmsew/i18n.py` | Every text, English and Turkish, written side by side |
| `lythosmsew/web/` | The local HTTP server, the session, and the browser interface |

## Development

```bash
pip install -e ".[dev]"
pytest -q                 # earth pressure, reinforcement, the wall by hand, height study, report, web, packaging
ruff check .
```

The tests check the earth pressure coefficients against their closed forms, the corrosion and
the strengths against hand calculations, the forces, the external checks, the bearing capacity
and the tension and pullout of a layer against hand calculations, the LRFD factors, the
seismic forces, the required length as a boundary, the refusals and warnings, the report in
all three formats, the input schema and its round trips, and the interface itself — the
session and the HTTP layer both.

Not included: global and compound stability, settlement, and drainage; check them separately.

Releasing to PyPI is described in [docs/releasing.md](https://github.com/hdaltuntas/lythos-msew/blob/main/docs/releasing.md).

## License

Copyright © 2026 Hasan Deniz Altuntaş

Lythos MSEW is free software: you can redistribute it and/or modify it under the terms of the
[GNU Affero General Public License, version 3](https://github.com/hdaltuntas/lythos-msew/blob/main/LICENSE) as published by the Free Software
Foundation. It is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Whoever runs a modified version for users over a network must offer them the source of that
version (section 13 of the licence). Versions published before this change were released
under the MIT licence and remain available under it.

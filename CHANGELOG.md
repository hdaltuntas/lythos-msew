# Changelog

## 0.1.0

First release: mechanically stabilised earth walls, built on the architecture of the other
Lythos programs (local HTTP server + browser interface, schema-driven forms, the same theme and
fonts, bilingual English / Turkish throughout, PDF / HTML / DOCX reports, `.msew` project files,
command line).

- Earth pressure: Coulomb's Ka in AASHTO's form, with a battered face and a sloping backfill.
- External stability: sliding (reinforced fill, foundation soil, geosynthetic interface),
  overturning, eccentricity; the live load over the block never resists.
- Bearing capacity of the foundation under Meyerhof's effective width, by Vesić, Meyerhof,
  Brinch Hansen, Terzaghi and EN 1997-1 side by side (the factors of Lythos Bearing); water
  table, embedment, load inclination and toe slope.
- Internal stability by AASHTO's Simplified Method: Tmax per layer with tributary spacing,
  Kr/Ka for strips and geosynthetics, the strip load at 2:1, the backslope as σ2; tensile,
  pullout (coherent gravity and Rankine active zones, F*, α, minimum Le), connection and
  sliding along each layer.
- Reinforcement types: steel strips (width, thickness, yield, spacing, galvanising and steel
  corrosion over the design life) and geogrids / geotextiles (Tult, RFID, RFCR, RFD, Rc, Ci).
- Pseudo-static earthquake: Am, PAE (Mononobe–Okabe with a backslope), PIR, the inertia of the
  active zone shared by resisting length, the geosynthetic's dynamic strength.
- ASD (factors of safety) or LRFD (load and resistance factors).
- The required uniform reinforcement length, by bisection; FHWA's minimum length.
- Layout generator, and a height study over a range of wall heights with CSV / XLSX export.
- Figures: section, lateral stress and tension, internal margins, pullout, external checks,
  bearing capacity by method, checks against the length, seismic tension; the height study's
  margins and required length.

# Lythos MSEW — theory

What the program computes, with the expressions it uses and where they come from. Units are
kN, m and kPa throughout; every force is per metre run of wall.

References:
FHWA-NHI-10-024 / 10-025, *Design and Construction of Mechanically Stabilized Earth Walls and
Reinforced Soil Slopes* (Berg, Christopher & Samtani, 2009);
FHWA-NHI-00-043 (Elias, Christopher & Berg, 2001), the ASD edition;
AASHTO LRFD Bridge Design Specifications, §3.11.5 and §11.10;
Vesić (1973), Meyerhof (1963), Brinch Hansen (1970), Terzaghi (1943), EN 1997-1 Annex D for the
bearing capacity factors (as in Lythos Bearing).

## 1. Geometry

The toe of the facing, on the levelling pad, is the origin. H is the design height, from the
levelling pad to the top of the wall; d the embedment below the ground in front. The face is
battered back by ω; the reinforced block is the parallelogram of the layers, length L measured
from the face. The external checks use the length of the **lowest** layer (a warning says so
when the layers differ). The backfill above the wall slopes at β; the retained fill behind the
block meets the thrust over the height h = H + L·tan β.

## 2. Earth pressure

Coulomb's coefficient in AASHTO's form (eq. 3.11.5.3-1):

    Ka = sin²(θ + φ) / [ Γ · sin²θ · sin(θ − δ) ]
    Γ  = [ 1 + √( sin(φ + δ)·sin(φ − β) / (sin(θ − δ)·sin(θ + β)) ) ]²

θ is the inclination of the back from the horizontal: 90° for a vertical face, 90° + ω once the
batter reaches 10°. Behind the block δ = β (the thrust is inclined at the slope); inside the
reinforced fill δ = 0 and β = 0, the backslope entering the internal checks as a surcharge
instead (§5). At θ = 90°, δ = β = 0 this is Rankine's tan²(45 − φ/2).

## 3. External stability

Forces on the block, per metre (γr the reinforced fill, γb the retained fill):

| force | value | arm about the toe |
|---|---|---|
| V1, the block | γr·H·L | L/2 + (H/2)·tan ω |
| V2, the slope over it | ½·γr·L²·tan β | H·tan ω + 2L/3 |
| permanent surcharge | q_d·L | H·tan ω + L/2 |
| live surcharge (bearing only) | q_l·L | H·tan ω + L/2 |
| F1, the retained fill | ½·Ka·γb·h², at β | h/3 |
| F2, the surcharges | Ka·(q_d + q_l)·h, at β | h/2 |

The vertical components F·sin β act at the back of the block and resist. The live load over the
reinforced zone never resists: it is left out of sliding and eccentricity and kept in bearing.
A strip load on the block counts as a vertical load at its offset (left out of the resisting
forces when it is live).

**Sliding.** R = ΣV·μ, with the weakest of

* the reinforced fill, μ = tan φr;
* the foundation soil, R = ΣV·tan φf + c·L;
* a geosynthetic lowest layer, μ = Cds·tan φr.

FS = R / ΣH (ASD); CDR = φτ·R / ΣH (LRFD).

**Overturning (ASD).** FS = M_R / M_O about the toe.

**Eccentricity.** e = L/2 − (M_R − M_O)/ΣV; e ≤ L/6 in ASD, L/3 in LRFD (AASHTO: the middle
two-thirds on soil), L/4 under seismic loading in ASD. The limits are inputs.

## 4. Bearing capacity

The block bears as a strip footing of width L. The eccentric resultant leaves Meyerhof's
effective width B′ = L − 2e, and the vertical stress under it is σv = ΣV / B′. It is compared
with

    q_ult = c·Nc·ic·gc + q·Nq·iq·gq + ½·γ·B′·Nγ·iγ·gγ

by the chosen factor set, the other four shown beside it:

| method | Nγ |
|---|---|
| Vesić (1973) | 2(Nq + 1) tan φ |
| Meyerhof (1963) | (Nq − 1) tan(1.4φ) |
| Brinch Hansen (1970) | 1.5(Nq − 1) tan φ |
| Terzaghi (1943) | Kumbhojkar's fit (own Nc, Nq) |
| EN 1997-1 Annex D | 2(Nq − 1) tan φ |

Nq = e^(π tan φ)·tan²(45 + φ/2) and Nc = (Nq − 1) cot φ (5.14 at φ = 0) for all but
Terzaghi's. FHWA leaves out the embedment (q = 0) and the load inclination; both can be switched
on (q = γ·d; each method's own i-factors with ΣH and ΣV). A slope in front of the toe enters
through each method's ground factors. The water table, dw below the base, gives the Nγ term the
unit weight γ′ + (dw/B′)(γ − γ′) when dw < B′.

FS = q_ult / σv (ASD, 2.5 by default); CDR = φb·q_ult / σv (LRFD, φb = 0.65).

## 5. Internal stability

**The tension in a layer** (AASHTO's Simplified Method). At depth Z below the top of the wall,

    σv = γr·Z + σ2 + q_d + q_l + Δσv
    Tmax = Kr·σv·Sv

Sv is the layer's tributary height (from midway to the layer below to midway to the layer
above; the first and last reach the base and the top). σ2 = ½·(0.7H)·tan β·γr stands for a
sloping backfill. Δσv is a strip load P of width b at x from the face, spread at 2 vertical to 1
horizontal and cut off by the face:

    Δσv = P / (b + Z)              Z ≤ 2x − b
    Δσv = P / ((b + Z)/2 + x)      Z > 2x − b

Kr/Ka is 1 for geosynthetics; for steel strips it falls linearly from 1.7 at the top to 1.2 at
6 m and stays 1.2 below.

**Tensile strength.** Per metre of wall:

* a geosynthetic: T_al = Tult / (RFID·RFCR·RFD), times its coverage ratio Rc;
* a steel strip: Fy·b·Ec per strip, divided by the horizontal spacing Sh (Rc = b/Sh).

The strip's thickness after corrosion is Ec = t − Es, with the galvanising lasting
2 + (zinc − 30)/4 years (15 µm/yr for 2 years, then 4 µm/yr) and the carbon steel then lost at
the given rate on both faces: Es = 2·rate·(life − zinc life).

ASD: FS = T_al / Tmax against 1.5 for a geosynthetic, and against 1/0.55 for steel (the
allowable stress 0.55·Fy). LRFD: CDR = φ·T_al / (γ·Tmax), φ = 0.75 for strips and 0.90 for
geosynthetics, the vertical stress factored EV 1.35, ES 1.50, LS 1.75.

**The active zone.** Extensible reinforcement: Rankine's plane through the toe at 45 + φ/2,
La = z·tan(45 − φ/2). Inextensible reinforcement: the bilinear line, La = 0.6·z below H1/2 and
0.3·H1 above, with H1 = H + 0.3H·tan β / (1 − 0.3·tan β). With a battered face La is measured
from the face, z·tan ω less.

**Pullout.** The length beyond the active zone Le = L − La grips

    Pr = F*·α·σ′v·Le·C·Rc,   C = 2

with σ′v = γr·Z + σ2 + q_d (no live load, no strip load). F* = Ci·tan φr for geosynthetics
(Ci ≈ 0.67, α = 0.8 for geogrids and 0.6 for geotextiles); for ribbed strips F* falls from F*₀
at the top (1.2 + log Cu ≤ 2.0) to tan φr at 6 m, α = 1. ASD: FS = Pr / Tmax ≥ 1.5; LRFD:
CDR = φ·Pr / (γ·Tmax) with φ = 0.90. A layer reaching less than the minimum Le (0.9 m) beyond the
active zone fails whatever its resistance.

**Connection.** The tension at the face is Tmax; the connection carries CR·T_al.

**Sliding along a layer.** The block above each layer, of height H − z and the layer's length,
is checked like the whole wall, with μ = Cds·tan φr along a geosynthetic.

## 6. Earthquake (pseudo-static)

With A the peak ground acceleration coefficient, the acceleration at the wall's centroid is
Am = (1.45 − A)·A.

Externally the dynamic thrust PAE = 0.375·Am·γb·H² (level backfill; with a backslope the
Mononobe–Okabe increment ½·γb·h²·(KAE − Ka)) acts at 0.6·H, and the inertia of a block 0.5·H
wide, PIR = Am·γr·(0.5·H² + ⅛·H²·tan β), at H/2. Half of PAE is added to PIR and to the static
forces; the live load is halved (γEQ = 0.5). ASD asks for 75 % of the static factors of safety
and e ≤ L/4; LRFD uses the extreme-event φ (sliding 1.0, bearing 0.9).

Internally the inertia of the active zone, Pi = Am·Wa, is shared among the layers in proportion
to their resisting lengths, Tmd = Pi·Le/ΣLe. The geosynthetic carries its static part with
T_al and its dynamic part with Tult/(RFID·RFD), creep having no time to act:

    1/FS = Tmax / T_al + Tmd / T_dyn

Pullout uses 80 % of F* (an input). ASD again asks for 75 % of the static factors of safety;
LRFD uses φ = 1.0 for steel and 1.2 for geosynthetics and pullout.

## 7. The required length

The shortest uniform length that satisfies sliding, overturning, eccentricity, bearing and the
pullout of every layer (static and, with an earthquake, seismic) is found by bisection between
0.2·H and 4·H. Each of these checks improves with L, so the boundary is unique. FHWA's minimum,
the larger of 0.7·H and 2.4 m, is reported beside it.

## 8. The height study

Each height of the range is laid out by the generator's rule (first layer z1, spacing Sv, length
ratio·H not below a shortest length, or a fixed length, one type), analysed and designed on its
own. Each check is reported as its value and its margin — the value over the requirement, 1 at
the limit — so the checks can share one chart whatever the design method.

## 9. Not included

Global and compound stability (a slip surface through or behind the reinforced zone),
settlement and differential settlement, drainage and hydrostatic pressure behind the wall, and
facing design. Check them separately.

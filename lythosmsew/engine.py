"""
The analysis of a mechanically stabilised earth wall.

Given the wall (height, embedment, batter), the backfill slope, the
surcharges, the three soils, the reinforcement types and the layers,
`MSEWall.run()` works out

    * the active earth pressure coefficients of the retained and the
      reinforced fill
    * the forces on the reinforced soil block, and its external stability:
      sliding on the base, overturning about the toe, the eccentricity of
      the resultant and the bearing capacity of the foundation under it — by
      the chosen factor set and by every other one for comparison
    * the tension at every reinforcement layer, and its tensile, pullout,
      connection and sliding checks
    * with an earthquake, the same checks under the pseudo-static dynamic
      thrust and the inertia of the reinforced mass and of the active zone
    * the reinforcement length that all of it needs

Two design methods are offered. ASD compares the resistance with the load
and asks for a factor of safety; LRFD factors the loads (EV, EH, ES, LS), the
resistance (φ) and asks for a capacity-to-demand ratio of at least one. Every
check returns the same record — value, required value, status — so the rest
of the program need not know which method produced it.

Input problems are raised as `MSEWError`, which carries a translation key, so
the interface can say what is wrong in the user's language.
"""

from __future__ import annotations

import copy
import math
from typing import Any, Dict, List, Optional, Tuple

from . import capacity as cap
from . import earth
from . import reinforcement as R
from .config import BEARING_METHODS, DEFAULT_CONFIG, DESIGNS, KINDS

#: A strip is analysed as a very long rectangle where a length is needed
STRIP_LENGTH = 1.0e6

#: The face counts as battered — Coulomb with θ = 90 + ω — from this batter on
BATTER_LIMIT = 10.0

#: FHWA's smallest reinforcement length: 0.7·H and 2.4 m
MIN_RATIO, MIN_LENGTH = 0.7, 2.4

#: The largest vertical spacing FHWA recommends [m]
MAX_SPACING = 0.80

#: Share of the live load kept in a seismic combination (γEQ)
EQ_LIVE = 0.5

#: Eccentricity limit under seismic loading in ASD, e ≤ L / 4
ECC_SEISMIC_ASD = 4.0

#: LRFD resistance factors of the extreme event (seismic) limit state
PHI_EXTREME = {"sliding": 1.0, "bearing": 0.9, "steel": 1.0, "geo": 1.2, "pullout": 1.2}

#: LRFD load factors (AASHTO LRFD Table 3.4.1-2), per combination.
#: sliding / eccentricity: the permanent loads that resist at their minimum,
#: the ones that drive at their maximum, and no live load over the reinforced
#: zone. bearing: everything at its maximum.
LRFD_FACTORS = {
    "sliding": {"EV": 1.00, "EH": 1.50, "ES_v": 0.75, "ES_h": 1.50, "LS_v": 0.0,
                "LS_h": 1.75, "strip_dead": 0.75, "strip_live": 0.0},
    "bearing": {"EV": 1.35, "EH": 1.50, "ES_v": 1.50, "ES_h": 1.50, "LS_v": 1.75,
                "LS_h": 1.75, "strip_dead": 1.50, "strip_live": 1.75},
}
ASD_FACTORS = {
    "sliding": {"EV": 1.0, "EH": 1.0, "ES_v": 1.0, "ES_h": 1.0, "LS_v": 0.0, "LS_h": 1.0,
                "strip_dead": 1.0, "strip_live": 0.0},
    "bearing": {"EV": 1.0, "EH": 1.0, "ES_v": 1.0, "ES_h": 1.0, "LS_v": 1.0, "LS_h": 1.0,
                "strip_dead": 1.0, "strip_live": 1.0},
}
#: LRFD factors on the vertical stress behind the tension in a layer
LRFD_INTERNAL = {"EV": 1.35, "ES": 1.50, "LS": 1.75}

#: The search range of the required reinforcement length, as multiples of H
LENGTH_RANGE = (0.2, 4.0)


class MSEWError(ValueError):
    """An input the analysis cannot work with; `key` names the message."""

    def __init__(self, key: str, **params):
        self.key = key
        self.params = params
        from .i18n import t
        super().__init__(t("en", key, **params))


def _message(key: str, **params) -> Tuple[str, Dict[str, Any]]:
    return key, params


def _tan(deg: float) -> float:
    return math.tan(math.radians(deg))


def _check(value: float, required: float, *, demand: float = float("nan"),
           capacity: float = float("nan"), kind: str = "ratio",
           extra: bool = True) -> Dict[str, Any]:
    """One check. `kind` is ``ratio`` (value ≥ required) or ``limit`` (value ≤ required);
    `extra` is a further condition that must also hold."""
    if kind == "limit":
        ok = math.isfinite(value) and value <= required + 1e-12
    else:
        ok = (math.isfinite(value) and value >= required - 1e-9) or value == math.inf
    return {"value": value, "required": required, "demand": demand, "capacity": capacity,
            "kind": kind, "status": "OK" if (ok and extra) else "NOT OK"}


def _na() -> Dict[str, Any]:
    return {"value": float("nan"), "required": float("nan"), "demand": float("nan"),
            "capacity": float("nan"), "kind": "ratio", "status": "N/A"}


class MSEWall:
    """One wall, set up from a configuration dictionary and analysed by `run()`."""

    def __init__(self, config: Optional[dict] = None):
        self.config = copy.deepcopy(config if config is not None else DEFAULT_CONFIG)
        self.results: Dict[str, Any] = {}
        self._read()

    # ------------------------------------------------------------------ inputs
    def _read(self) -> None:
        c = self.config
        g, loads, soils = c["geometry"], c["loads"], c["soils"]
        self.H = float(g["H"])
        self.d = float(g["embedment"])
        self.omega = float(g["batter"])
        self.beta = float(g["backslope"])
        self.toe_slope = float(g["toe_slope"])
        self.facing = float(g.get("facing", 0.14))

        self.q_dead = float(loads["q_dead"])
        self.q_live = float(loads["q_live"])
        self.strip_on = bool(loads["strip_enabled"])
        self.strip_P = float(loads["strip_P"])
        self.strip_b = float(loads["strip_width"])
        self.strip_x = float(loads["strip_offset"])
        self.strip_live = bool(loads["strip_live"])

        self.rf = dict(soils["reinforced"])
        self.rb = dict(soils["retained"])
        self.fd = dict(soils["foundation"])
        self.dw = float(soils["water_depth"])
        self.gw = float(soils["gamma_water"])

        self.corrosion = dict(c["corrosion"])
        o = c["options"]
        self.design = o["design"] if o["design"] in DESIGNS else "asd"
        self.method = o["bearing_method"] if o["bearing_method"] in BEARING_METHODS else "vesic"
        self.use_embedment = bool(o["bearing_embedment"])
        self.use_inclination = bool(o["bearing_inclination"])
        self.Cds = float(o["Cds"])

        s = c["seismic"]
        self.seismic_on = bool(s["enabled"])
        self.A = float(s["A"])
        self.pullout_factor = float(s["pullout_factor"])
        self.crit = dict(c["criteria"])

        self.types = {t["name"]: dict(t) for t in c["reinforcement_types"]}
        self.layers = sorted((dict(layer) for layer in c["layers"]), key=lambda r: r["z"])

    def _validate(self) -> None:
        if self.H <= 0:
            raise MSEWError("err_height")
        if self.d < 0 or self.d >= self.H:
            raise MSEWError("err_embedment")
        if not 0 <= self.omega < 30:
            raise MSEWError("err_batter")
        if self.beta < 0 or self.beta >= self.rb["phi"]:
            raise MSEWError("err_backslope", phi=self.rb["phi"])
        if not 0 <= self.toe_slope < 45:
            raise MSEWError("err_toe_slope")
        for name, soil in (("reinforced", self.rf), ("retained", self.rb),
                           ("foundation", self.fd)):
            if soil["gamma"] <= 0:
                raise MSEWError("err_gamma", soil=f"soil_{name}")
            if not 0 <= soil["phi"] < 60:
                raise MSEWError("err_phi", soil=f"soil_{name}")
        if self.rf["phi"] <= 0 or self.rb["phi"] <= 0:
            raise MSEWError("err_fill_phi")
        if self.fd["phi"] <= 0 and self.fd["c"] <= 0:
            raise MSEWError("err_foundation_strength")
        if self.fd["gamma_sat"] <= self.gw:
            raise MSEWError("err_gamma_sat")
        if not self.layers:
            raise MSEWError("err_no_layers")
        for t in self.types.values():
            if t["kind"] not in KINDS:
                raise MSEWError("err_kind", name=t["name"])
            if t["kind"] == "polymer_strip":
                if (t["Tult"] <= 0 or min(t["RFID"], t["RFCR"], t["RFD"]) < 1.0
                        or min(t["b"], t["Sh"]) <= 0):
                    raise MSEWError("err_polymer_strip", name=t["name"])
            elif R.is_extensible(t["kind"]):
                if t["Tult"] <= 0 or min(t["RFID"], t["RFCR"], t["RFD"]) < 1.0 or t["Rc"] <= 0:
                    raise MSEWError("err_geosynthetic", name=t["name"])
            elif min(t["b"], t["t"], t["Fy"], t["Sh"]) <= 0:
                raise MSEWError("err_strip", name=t["name"])
            if t["alpha"] <= 0 or t["CR"] <= 0:
                raise MSEWError("err_pullout_params", name=t["name"])
        for layer in self.layers:
            if layer["type"] not in self.types:
                raise MSEWError("err_unknown_type", name=layer["type"])
            if not 0 < layer["z"] < self.H:
                raise MSEWError("err_layer_height", z=layer["z"], H=self.H)
            if layer["L"] <= 0:
                raise MSEWError("err_layer_length", z=layer["z"])
        if self.strip_on and (self.strip_b <= 0 or self.strip_x < self.strip_b / 2.0):
            raise MSEWError("err_strip_load")
        if self.seismic_on and not 0 <= self.A < 1.0:
            raise MSEWError("err_seismic")

    # ------------------------------------------------------------------ geometry
    @property
    def L(self) -> float:
        """The length of the reinforced block: the length of the lowest layer."""
        return self.layers[0]["L"]

    @property
    def theta(self) -> float:
        """Inclination of the back, from the horizontal in front of the wall."""
        return 90.0 + self.omega if self.omega >= BATTER_LIMIT else 90.0

    def ka_retained(self) -> float:
        """Ka of the retained fill behind the reinforced block, δ = β."""
        return earth.coulomb_ka(self.rb["phi"], self.theta, self.beta, self.beta)

    def ka_reinforced(self) -> float:
        """Ka of the reinforced fill for the internal checks: level, δ = 0."""
        return earth.coulomb_ka(self.rf["phi"], self.theta, 0.0, 0.0)

    def slope_surcharge(self) -> float:
        """σ2: the sloping backfill as a uniform surcharge, ½·(0.7H)·tan β·γr."""
        return 0.5 * 0.7 * self.H * _tan(self.beta) * self.rf["gamma"]

    def failure_x(self, z: float, kind: str) -> float:
        """Horizontal distance from the toe to the failure surface at height z."""
        if R.is_extensible(kind):
            return z * _tan(45.0 - self.rf["phi"] / 2.0)
        tb = _tan(self.beta)
        h1 = self.H + tb * 0.3 * self.H / max(1.0 - 0.3 * tb, 1e-6)
        return 0.6 * z if z < h1 / 2.0 else 0.3 * h1

    def active_length(self, z: float, kind: str) -> float:
        """La: the length of a layer inside the active zone, from the face."""
        return max(self.failure_x(z, kind) - z * _tan(self.omega), 0.0)

    def strip_increment(self, depth: float) -> float:
        """Δσv of the strip load at a depth below the top, spread at 2:1 and cut
        off by the face (FHWA-NHI-10-024)."""
        if not self.strip_on or depth < 0:
            return 0.0
        b, x = self.strip_b, self.strip_x
        z1 = 2.0 * x - b
        width = b + depth if depth <= z1 else (b + depth) / 2.0 + x
        return self.strip_P / max(width, 1e-9)

    # ------------------------------------------------------------------ external
    def _forces(self, H: float, L: float, fac: Dict[str, float], seismic: bool = False,
                live_scale: float = 1.0) -> Dict[str, Any]:
        """Forces on a reinforced block of height H and length L, per metre.

        `fac` holds the load factors (all 1.0 in ASD); `seismic` adds half the
        dynamic thrust and the inertia of the reinforced mass; `live_scale`
        scales the live load (γEQ in a seismic combination).
        """
        gr, gb = self.rf["gamma"], self.rb["gamma"]
        tw, tb = _tan(self.omega), _tan(self.beta)
        ka = self.ka_retained()
        h = H + L * tb
        cos_b, sin_b = math.cos(math.radians(self.beta)), math.sin(math.radians(self.beta))
        x_top = H * tw                        # the face at the top of the wall

        vertical: List[Tuple[str, float, float]] = []
        horizontal: List[Tuple[str, float, float]] = []

        vertical.append(("V1", fac["EV"] * gr * H * L, L / 2.0 + H * tw / 2.0))
        if tb > 0:
            vertical.append(("V2", fac["EV"] * gr * 0.5 * L * L * tb, x_top + 2.0 * L / 3.0))
        if self.q_dead > 0:
            vertical.append(("Vq_dead", fac["ES_v"] * self.q_dead * L, x_top + L / 2.0))
        q_live = self.q_live * live_scale
        if q_live > 0 and fac["LS_v"] > 0:
            vertical.append(("Vq_live", fac["LS_v"] * q_live * L, x_top + L / 2.0))
        if self.strip_on and self.strip_x <= L:
            factor = fac["strip_live"] * live_scale if self.strip_live else fac["strip_dead"]
            if factor > 0:
                vertical.append(("V_strip", factor * self.strip_P, x_top + self.strip_x))

        thrust = 0.5 * ka * gb * h * h
        x_back = L + h / 3.0 * tw
        horizontal.append(("F1", fac["EH"] * thrust * cos_b, h / 3.0))
        if sin_b > 0:
            vertical.append(("F1v", fac["EH"] * thrust * sin_b, x_back))
        q_thrust = ka * h * (fac["ES_h"] * self.q_dead + fac["LS_h"] * q_live)
        if q_thrust > 0:
            horizontal.append(("F2", q_thrust * cos_b, h / 2.0))
            if sin_b > 0:
                vertical.append(("F2v", q_thrust * sin_b, L + h / 2.0 * tw))

        dyn = {}
        if seismic:
            am = earth.am_coefficient(self.A)
            if self.beta > 0:
                try:
                    kae = earth.mononobe_okabe(self.rb["phi"], am, self.beta, self.beta)
                except ValueError as exc:
                    raise MSEWError("err_mononobe") from exc
                pae = 0.5 * gb * h * h * max(kae - ka, 0.0)
            else:
                pae = 0.375 * am * gb * H * H
            pir = am * gr * (H * 0.5 * H + 0.5 * (0.5 * H) ** 2 * tb)
            horizontal.append(("PAE/2", 0.5 * pae, 0.6 * h))
            horizontal.append(("PIR", pir, H / 2.0))
            dyn = {"Am": am, "PAE": pae, "PIR": pir}

        sum_v = sum(v for _, v, _ in vertical)
        sum_h = sum(f for _, f, _ in horizontal)
        m_r = sum(v * x for _, v, x in vertical)
        m_o = sum(f * y for _, f, y in horizontal)
        x_res = (m_r - m_o) / sum_v if sum_v > 0 else 0.0
        e = L / 2.0 - x_res
        return {"vertical": vertical, "horizontal": horizontal, "V": sum_v, "H": sum_h,
                "M_R": m_r, "M_O": m_o, "e": e, "h": h, "Ka": ka, "L": L, "height": H,
                "dynamic": dyn, "W": sum(v for n, v, _ in vertical if n in ("V1", "V2"))}

    def _factors(self, case: str) -> Dict[str, float]:
        return (LRFD_FACTORS if self.design == "lrfd" else ASD_FACTORS)[case]

    def _base_friction(self, V: float, L: float) -> Dict[str, Any]:
        """Sliding resistance of the base: the weakest of the reinforced fill,
        the foundation soil and (a geosynthetic bottom layer) the interface."""
        options = {"reinforced": V * _tan(self.rf["phi"]),
                   "foundation": V * _tan(self.fd["phi"]) + self.fd["c"] * L}
        bottom = self.types[self.layers[0]["type"]]
        if R.is_sheet(bottom["kind"]):
            options["interface"] = V * self.Cds * _tan(self.rf["phi"])
        plane = min(options, key=options.get)
        return {"R": options[plane], "plane": plane, "options": options}

    def _external(self, seismic: bool = False) -> Dict[str, Any]:
        """Sliding, overturning, eccentricity and the forces of the bearing check."""
        H, L = self.H, self.L
        live_scale = EQ_LIVE if seismic else 1.0
        lrfd = self.design == "lrfd"
        crit = self.crit
        ratio = crit["seismic_ratio"] if (seismic and not lrfd) else 1.0

        slide = self._forces(H, L, self._factors("sliding"), seismic, live_scale)
        friction = self._base_friction(slide["V"], L)
        phi_s = (PHI_EXTREME["sliding"] if seismic else crit["phi_sliding"]) if lrfd else 1.0
        value = phi_s * friction["R"] / slide["H"] if slide["H"] > 0 else math.inf
        required = 1.0 if lrfd else crit["FS_sliding"] * ratio
        sliding = _check(value, required, demand=slide["H"], capacity=phi_s * friction["R"])
        sliding["plane"] = friction["plane"]

        if lrfd:
            overturning = _na()
            limit = L / crit["ecc_lrfd"]
        else:
            fs_ot = slide["M_R"] / slide["M_O"] if slide["M_O"] > 0 else math.inf
            overturning = _check(fs_ot, crit["FS_overturning"] * ratio,
                                 demand=slide["M_O"], capacity=slide["M_R"])
            limit = L / (ECC_SEISMIC_ASD if seismic else crit["ecc_asd"])
        eccentricity = _check(abs(slide["e"]), limit, kind="limit")
        return {"forces": slide, "sliding": sliding, "overturning": overturning,
                "eccentricity": eccentricity, "friction": friction,
                "bearing_forces": self._forces(H, L, self._factors("bearing"), seismic,
                                               live_scale)}

    # ------------------------------------------------------------------ bearing
    def _gamma_below(self, width: float) -> float:
        """Unit weight under the base for the Nγ term, the water table allowed for."""
        g, gsat = self.fd["gamma"], self.fd["gamma_sat"]
        buoyant = gsat - self.gw
        dw = max(self.dw, 0.0)
        if dw >= width:
            return g
        return buoyant + (dw / max(width, 1e-9)) * (g - buoyant)

    def bearing_capacity(self, method: str, B: float, V: float, H: float) -> Dict[str, Any]:
        """q_ult of the foundation under an effective width B'."""
        q = self.fd["gamma"] * self.d if self.use_embedment else 0.0
        return cap.ultimate(method, c=self.fd["c"], phi=self.fd["phi"],
                            gamma=self._gamma_below(B), q=q, B=B, L=STRIP_LENGTH,
                            Df=self.d, shape="strip", V=V, Hb=H, Hl=0.0, area=B * 1.0,
                            eta=0.0, beta=self.toe_slope, use_shape=False, use_depth=False,
                            use_inclination=self.use_inclination, use_base=False,
                            use_ground=self.toe_slope > 0, use_compressibility=False)

    def _bearing(self, forces: Dict[str, Any], seismic: bool = False) -> Dict[str, Any]:
        lrfd = self.design == "lrfd"
        crit = self.crit
        L, V, Hf, e = forces["L"], forces["V"], forces["H"], forces["e"]
        B = L - 2.0 * abs(e)
        out = {"e": e, "B_eff": B, "V": V, "H": Hf, "methods": {}, "primary": self.method}
        if B <= 0:
            out.update(sigma_v=math.inf, q_ult=0.0, check=_check(0.0, 1.0))
            return out
        sigma = V / B
        for method in BEARING_METHODS:
            try:
                out["methods"][method] = self.bearing_capacity(method, B, V, Hf)
            except (ValueError, ZeroDivisionError):
                continue
        q_ult = out["methods"][self.method]["q_ult"]
        if lrfd:
            phi_b = PHI_EXTREME["bearing"] if seismic else crit["phi_bearing"]
            value, required, capacity = phi_b * q_ult / sigma, 1.0, phi_b * q_ult
        else:
            ratio = crit["seismic_ratio"] if seismic else 1.0
            value, required = q_ult / sigma, crit["FS_bearing"] * ratio
            capacity = q_ult / required
        out.update(sigma_v=sigma, q_ult=q_ult, q_allow=capacity,
                   check=_check(value, required, demand=sigma, capacity=capacity))
        return out

    # ------------------------------------------------------------------ internal
    def _tributary(self) -> List[Tuple[float, float]]:
        """The band of wall each layer carries, from midway to its neighbours."""
        zs = [layer["z"] for layer in self.layers]
        bands = []
        for i, z in enumerate(zs):
            lo = 0.0 if i == 0 else 0.5 * (zs[i - 1] + z)
            hi = self.H if i == len(zs) - 1 else 0.5 * (z + zs[i + 1])
            bands.append((lo, hi))
        return bands

    def sigma_v(self, depth: float, factors: Optional[Dict[str, float]] = None,
                live: bool = True, strip: bool = True, live_scale: float = 1.0) -> float:
        """Vertical stress at a depth below the top of the wall, in the reinforced fill."""
        f = factors or {"EV": 1.0, "ES": 1.0, "LS": 1.0}
        value = f["EV"] * (self.rf["gamma"] * depth + self.slope_surcharge())
        value += f["ES"] * self.q_dead
        if live:
            value += f["LS"] * self.q_live * live_scale
        if strip and self.strip_on:
            if self.strip_live:
                value += (f["LS"] * live_scale if live else 0.0) * self.strip_increment(depth)
            else:
                value += f["ES"] * self.strip_increment(depth)
        return value

    def _internal(self) -> Dict[str, Any]:
        lrfd = self.design == "lrfd"
        crit = self.crit
        ka = self.ka_reinforced()
        rows = []
        for layer, (lo, hi) in zip(self.layers, self._tributary()):
            rtype = self.types[layer["type"]]
            kind = rtype["kind"]
            z = layer["z"]
            depth = self.H - z
            sv = hi - lo
            kr = ka * R.kr_ratio(kind, depth)
            sigma = self.sigma_v(depth)
            sigma_f = self.sigma_v(depth, LRFD_INTERNAL) if lrfd else sigma
            t_max = kr * sigma * sv
            t_design = kr * sigma_f * sv
            st = R.strength(rtype, self.corrosion)

            geo = R.is_extensible(kind)
            if lrfd:
                phi_t = crit["phi_geo"] if geo else crit["phi_steel"]
                t_cap = phi_t * st["T_lt"]
                tensile = _check(t_cap / t_design, 1.0, demand=t_design, capacity=t_cap)
                c_cap = phi_t * rtype["CR"] * st["T_lt"]
                connection = _check(c_cap / t_design, 1.0, demand=t_design, capacity=c_cap)
            else:
                req_t = crit["FS_tensile"] if geo else 1.0 / crit["steel_ratio"]
                req_c = crit["FS_connection"] if geo else 1.0 / crit["steel_ratio"]
                tensile = _check(st["T_lt"] / t_max, req_t, demand=t_max,
                                 capacity=st["T_lt"] / req_t)
                c_lt = rtype["CR"] * st["T_lt"]
                connection = _check(c_lt / t_max, req_c, demand=t_max, capacity=c_lt / req_c)

            la = self.active_length(z, kind)
            le = max(layer["L"] - la, 0.0)
            sigma_p = self.sigma_v(depth, live=False, strip=False)
            fstar = R.f_star(rtype, depth, self.rf["phi"])
            pr = R.pullout(fstar, rtype["alpha"], sigma_p, le, st["Rc"])
            le_ok = le >= crit["min_Le"] - 1e-9
            if lrfd:
                cap_p = crit["phi_pullout"] * pr
                pull = _check(cap_p / t_design, 1.0, demand=t_design, capacity=cap_p,
                              extra=le_ok)
            else:
                pull = _check(pr / t_max, crit["FS_pullout"], demand=t_max,
                              capacity=pr / crit["FS_pullout"], extra=le_ok)
            pull["Le_ok"] = le_ok

            # sliding of the block above along this layer
            above = self.H - z
            forces = self._forces(above, layer["L"], self._factors("sliding"))
            mu = (self.Cds if R.is_sheet(kind) else 1.0) * _tan(self.rf["phi"])
            resist = forces["V"] * mu
            phi_s = crit["phi_sliding"] if lrfd else 1.0
            slide_req = 1.0 if lrfd else crit["FS_sliding"]
            sliding = _check(phi_s * resist / forces["H"] if forces["H"] > 0 else math.inf,
                             slide_req, demand=forces["H"], capacity=phi_s * resist)

            required_strength = (t_design / (crit["phi_geo"] if geo else crit["phi_steel"])
                                 if lrfd else t_max * (crit["FS_tensile"] if geo
                                                       else 1.0 / crit["steel_ratio"]))
            rows.append({
                "z": z, "depth": depth, "L": layer["L"], "type": layer["type"], "kind": kind,
                "Sv": sv, "band": (lo, hi), "Kr": kr, "Kr_Ka": kr / ka, "sigma_v": sigma,
                "sigma_h": kr * sigma, "T_max": t_max, "T_design": t_design,
                "T_lt": st["T_lt"], "T_dyn": st["T_dyn"], "Rc": st["Rc"], "Ec": st["Ec"],
                "Es": st["Es"], "Ac": st["Ac"], "T_required": required_strength,
                "La": la, "Le": le, "sigma_p": sigma_p, "F_star": fstar,
                "alpha": rtype["alpha"], "P_r": pr, "CR": rtype["CR"],
                "tensile": tensile, "pullout": pull, "connection": connection,
                "sliding": sliding,
            })
        return {"Ka": ka, "rows": rows}

    def _internal_seismic(self, rows: List[dict]) -> Dict[str, Any]:
        """The inertia of the active zone, shared out by the resisting lengths."""
        lrfd = self.design == "lrfd"
        crit = self.crit
        am = earth.am_coefficient(self.A)
        # the weight of the active zone, integrated over the height (each kind's surface)
        kind = rows[0]["kind"]
        steps = 200
        area = 0.0
        for i in range(steps):
            z = (i + 0.5) * self.H / steps
            area += self.active_length(z, kind) * self.H / steps
        wa = self.rf["gamma"] * area
        pi = am * wa
        total_le = sum(r["Le"] for r in rows) or 1.0
        out = []
        for r in rows:
            geo = R.is_extensible(r["kind"])
            t_md = pi * r["Le"] / total_le
            if lrfd:
                static = (r["Kr"] * self.sigma_v(r["depth"], LRFD_INTERNAL, live_scale=EQ_LIVE)
                          * r["Sv"])
                phi_t = PHI_EXTREME["geo" if geo else "steel"]
                req_t = req_c = 1.0
                phi_p, req_p = PHI_EXTREME["pullout"], 1.0
            else:
                static = r["Kr"] * self.sigma_v(r["depth"], live_scale=EQ_LIVE) * r["Sv"]
                phi_t = phi_p = 1.0
                ratio = crit["seismic_ratio"]
                req_t = (crit["FS_tensile"] if geo else 1.0 / crit["steel_ratio"]) * ratio
                req_c = (crit["FS_connection"] if geo else 1.0 / crit["steel_ratio"]) * ratio
                req_p = crit["FS_pullout"] * ratio
            total = static + t_md
            use = static / (phi_t * r["T_lt"]) + t_md / (phi_t * r["T_dyn"])
            # capacities are reported as what the layer may carry: the
            # resistance divided by the required value (1 in LRFD)
            tensile = _check(1.0 / use if use > 0 else math.inf, req_t, demand=total,
                             capacity=total / use / req_t if use > 0 else math.inf)
            use_c = use / r["CR"]
            connection = _check(1.0 / use_c if use_c > 0 else math.inf, req_c, demand=total,
                                capacity=total / use_c / req_c if use_c > 0 else math.inf)
            pr = r["P_r"] * self.pullout_factor
            pull = _check(phi_p * pr / total if total > 0 else math.inf, req_p, demand=total,
                          capacity=phi_p * pr / req_p, extra=r["pullout"]["Le_ok"])
            out.append({"z": r["z"], "T_md": t_md, "T_static": static, "T_total": total,
                        "P_r": pr, "tensile": tensile, "connection": connection,
                        "pullout": pull})
        return {"Am": am, "W_a": wa, "P_i": pi, "rows": out}

    # ------------------------------------------------------------------ the whole
    def _governing(self, rows: List[dict], name: str) -> Dict[str, Any]:
        """The layer with the smallest margin in one internal check."""
        best = None
        for r in rows:
            chk = r[name]
            if chk["status"] == "N/A":
                continue
            margin = chk["value"] / chk["required"] if chk["required"] else chk["value"]
            if chk["status"] == "NOT OK" and chk.get("Le_ok", True) is False:
                margin = -1.0
            if best is None or margin < best[0]:
                best = (margin, r, chk)
        if best is None:
            return {"z": float("nan"), **_na()}
        return {"z": best[1]["z"], **best[2]}

    def run(self, with_length: bool = True) -> Dict[str, Any]:
        self._validate()
        warnings: List[Tuple[str, Dict[str, Any]]] = []
        ext = self._external()
        bearing = self._bearing(ext["bearing_forces"])
        internal = self._internal()
        rows = internal["rows"]

        res: Dict[str, Any] = {
            "design": self.design,
            "Ka": {"retained": ext["forces"]["Ka"], "reinforced": internal["Ka"],
                   "theta": self.theta},
            "H": self.H, "L": self.L, "h": ext["forces"]["h"],
            "slope_surcharge": self.slope_surcharge(),
            "forces": ext["forces"], "bearing_forces": ext["bearing_forces"],
            "friction": ext["friction"],
            "external": {"sliding": ext["sliding"], "overturning": ext["overturning"],
                         "eccentricity": ext["eccentricity"], "bearing": bearing["check"]},
            "bearing": bearing,
            "layers": rows,
            "internal": {name: self._governing(rows, name)
                         for name in ("tensile", "pullout", "connection", "sliding")},
            "seismic": None,
            "warnings": warnings,
        }

        if self.seismic_on:
            sext = self._external(seismic=True)
            sbear = self._bearing(sext["bearing_forces"], seismic=True)
            sint = self._internal_seismic(rows)
            res["seismic"] = {
                "Am": sext["forces"]["dynamic"].get("Am", 0.0),
                "PAE": sext["forces"]["dynamic"].get("PAE", 0.0),
                "PIR": sext["forces"]["dynamic"].get("PIR", 0.0),
                "forces": sext["forces"], "bearing": sbear,
                "external": {"sliding": sext["sliding"], "overturning": sext["overturning"],
                             "eccentricity": sext["eccentricity"], "bearing": sbear["check"]},
                "internal_rows": sint["rows"], "W_a": sint["W_a"], "P_i": sint["P_i"],
                "internal": {name: self._governing(sint["rows"], name)
                             for name in ("tensile", "pullout", "connection")},
            }

        # ---------------------------------------------------------- warnings
        lengths = {round(r["L"], 6) for r in rows}
        if len(lengths) > 1:
            warnings.append(_message("warn_lengths_vary", L=self.L))
        rule = max(MIN_RATIO * self.H, MIN_LENGTH)
        if min(r["L"] for r in rows) < rule - 1e-9:
            warnings.append(_message("warn_min_length", L=min(r["L"] for r in rows), rule=rule))
        gaps = [rows[0]["z"]] + [b["z"] - a["z"] for a, b in zip(rows, rows[1:])]
        gaps.append(self.H - rows[-1]["z"])
        if max(gaps) > MAX_SPACING + 1e-9:
            warnings.append(_message("warn_spacing", s=max(gaps), limit=MAX_SPACING))
        short = [r["z"] for r in rows if not r["pullout"]["Le_ok"]]
        if short:
            warnings.append(_message("warn_short_le", n=len(short), Le=self.crit["min_Le"]))
        if self.strip_on and self.strip_x > self.L:
            warnings.append(_message("warn_strip_behind"))
        if self.dw < self.L:
            warnings.append(_message("warn_water", dw=self.dw))
        if self.fd["phi"] <= 0:
            warnings.append(_message("warn_undrained"))
        kinds = {r["kind"] for r in rows}
        if len({R.is_extensible(k) for k in kinds}) > 1:
            warnings.append(_message("warn_mixed_kinds"))
        if self.beta > 0 and self.q_live > 0:
            warnings.append(_message("warn_live_on_slope"))

        res["length_rule"] = rule
        res["required_length"] = self.required_length() if with_length else float("nan")
        self.results = res
        return res

    # ------------------------------------------------------------------ design length
    def passes(self) -> bool:
        """Do the external and the pullout checks hold (static and seismic)?"""
        res = self.run(with_length=False)
        checks = list(res["external"].values())
        checks += [r["pullout"] for r in res["layers"]]
        if res["seismic"]:
            checks += list(res["seismic"]["external"].values())
            checks += [r["pullout"] for r in res["seismic"]["internal_rows"]]
        return all(c["status"] != "NOT OK" for c in checks)

    def with_length(self, length: float) -> "MSEWall":
        """A copy of the wall with every layer set to one length."""
        cfg = copy.deepcopy(self.config)
        for layer in cfg["layers"]:
            layer["L"] = float(length)
        return MSEWall(cfg)

    def required_length(self) -> float:
        """The shortest uniform length that satisfies the external and pullout
        checks, found by bisection; infinite when even 4·H is not enough."""
        lo, hi = LENGTH_RANGE[0] * self.H, LENGTH_RANGE[1] * self.H

        def ok(length: float) -> bool:
            try:
                return self.with_length(length).passes()
            except MSEWError:
                return False

        if not ok(hi):
            return math.inf
        if ok(lo):
            return lo
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if ok(mid):
                hi = mid
            else:
                lo = mid
            if hi - lo < 0.005:
                break
        return hi


# --------------------------------------------------------------------------- #
#  Layout generator
# --------------------------------------------------------------------------- #

def generate_layers(H: float, z1: float, Sv: float, rule: str, ratio: float,
                    length: float, L_min: float, rtype: str) -> List[dict]:
    """Layers at z1, z1 + Sv, … below the top, all of one length and type.

    The length is ratio·H (never below L_min) or a fixed length. The last layer
    is kept at least a quarter of a spacing below the top of the wall.
    """
    H, z1, Sv = float(H), float(z1), float(Sv)
    if H <= 0 or Sv <= 0 or not 0 < z1 < H:
        raise MSEWError("err_layout")
    L = max(ratio * H, L_min) if rule == "ratio" else float(length)
    out = []
    z = z1
    while z < H - 0.25 * Sv + 1e-9 and len(out) < 500:
        out.append({"z": round(z, 4), "L": round(L, 3), "type": rtype})
        z += Sv
    return out

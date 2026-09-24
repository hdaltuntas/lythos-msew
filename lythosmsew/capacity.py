"""
The general bearing capacity equation, as the foundation of an MSE wall uses it.

    q_ult = c·Nc·sc·dc·ic·bc·gc·Fc
          + q·Nq·sq·dq·iq·bq·gq·Fq
          + ½·γ·B'·Nγ·sγ·dγ·iγ·bγ·gγ·Fγ

with the factors of `lythosmsew.factors` (taken over from Lythos Bearing).
The reinforced soil block is a strip footing of width L; an eccentric
resultant leaves Meyerhof's effective width B' = L − 2e, and the vertical
stress under it is ΣV / B'. Hansen's undrained expression is additive rather
than multiplicative and is written out separately:

    q_ult = 5.14·cu·(1 + s'c + d'c − i'c − b'c − g'c) + q

Nothing here knows about the wall: the caller passes the strength, the
surcharge and the unit weight it has already worked out, which keeps the
equation testable against a hand calculation line by line.
"""

from __future__ import annotations

from typing import Dict

from . import factors as F

__all__ = ["ultimate"]


def ultimate(method: str, *, c: float, phi: float, gamma: float, q: float,
             B: float, L: float, Df: float, shape: str = "rectangle",
             V: float = 0.0, Hb: float = 0.0, Hl: float = 0.0, area: float = 0.0,
             eta: float = 0.0, beta: float = 0.0, G: float = 0.0, q_mid: float = 0.0,
             **flags) -> Dict[str, object]:
    """One method's ultimate bearing capacity, term by term.

    `B` and `L` are the effective dimensions, `q` the surcharge at the base
    (effective in a drained analysis, total in an undrained one), `gamma` the
    unit weight below the base (buoyant where the soil is submerged) and
    `area` the effective area A'. The flags are passed straight to
    `factors.all_factors`.
    """
    fac = F.all_factors(method, B=B, L=L, Df=Df, phi=phi, c=c, V=V, Hb=Hb, Hl=Hl,
                        area=area, eta=eta, beta=beta, shape=shape, G=G, q_mid=q_mid,
                        **flags)
    N = fac["N"]

    def product(part: str) -> float:
        return (fac["shape"][part] * fac["depth"][part] * fac["inclination"][part]
                * fac["base"][part] * fac["ground"][part] * fac["compressibility"][part])

    undrained = phi <= F.PHI_ZERO
    if method == "hansen" and undrained:
        # Hansen's additive form: the corrections add to, and subtract from, 1
        bracket = (1.0 + fac["shape"]["c"] - 1.0 + fac["depth"]["c"] - 1.0
                   - fac["inclination"]["c"] - fac["base"]["c"] - fac["ground"]["c"])
        term_c = 5.14 * c * bracket * fac["compressibility"]["c"]
        term_q, term_g = q, 0.0
        form = "additive"
    else:
        term_c = c * N["Nc"] * product("c")
        term_q = q * N["Nq"] * product("q")
        term_g = 0.5 * gamma * B * N["Ngamma"] * product("g")
        form = "product"

    q_ult = term_c + term_q + term_g
    return {
        "method": method,
        "q_ult": q_ult,
        "q_net_ult": q_ult - q,
        "terms": {"c": term_c, "q": term_q, "g": term_g},
        "N": N,
        "factors": {key: dict(fac[key]) for key in
                    ("shape", "depth", "inclination", "base", "ground", "compressibility")},
        "form": form,
        "undrained": undrained,
        "inputs": {"c": c, "phi": phi, "gamma": gamma, "q": q, "B": B, "L": L,
                   "A": area, "Df": Df},
    }

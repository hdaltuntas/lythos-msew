"""
Earth pressure coefficients, and the seismic thrust of the pseudo-static method.

Everything here is a closed-form expression evaluated for one set of angles,
so each one can be checked on its own against its published value.

    coulomb_ka     Coulomb's active coefficient in the form AASHTO LRFD
                   3.11.5.3 writes it: the back of the wall inclined θ from
                   the horizontal (90° vertical), wall friction δ and a
                   backfill sloping at β. At θ = 90°, δ = β = 0 it is
                   Rankine's tan²(45 − φ/2).
    rankine_ka     tan²(45 − φ/2).
    mononobe_okabe The Mononobe–Okabe coefficient KAE for a horizontal seismic
                   coefficient kh (kv = 0), a vertical back and a slope β.
    am_coefficient The maximum acceleration at the centroid of the wall mass,
                   Am = (1.45 − A)·A (Segrestin & Bastick, FHWA).

Angles are given in degrees and turned into radians inside.
"""

from __future__ import annotations

import math

__all__ = ["coulomb_ka", "rankine_ka", "mononobe_okabe", "am_coefficient",
           "rankine_angle"]


def _r(deg: float) -> float:
    return math.radians(float(deg))


def rankine_ka(phi: float) -> float:
    """Rankine's active coefficient of a level backfill behind a vertical back."""
    return math.tan(_r(45.0 - float(phi) / 2.0)) ** 2


def rankine_angle(phi: float) -> float:
    """Inclination of Rankine's active failure plane from the horizontal, 45 + φ/2."""
    return 45.0 + float(phi) / 2.0


def coulomb_ka(phi: float, theta: float = 90.0, delta: float = 0.0,
               beta: float = 0.0) -> float:
    """Coulomb's active coefficient (AASHTO LRFD eq. 3.11.5.3-1).

    `theta` is the inclination of the back face from the horizontal, measured
    from in front of the wall — 90° for a vertical back, 90° + ω for a face
    battered back by ω; `delta` the friction between the soil and the back;
    `beta` the slope of the backfill. A slope steeper than the friction
    angle has no active state, and is refused.
    """
    phi, theta, delta, beta = float(phi), float(theta), float(delta), float(beta)
    if beta > phi + 1e-9:
        raise ValueError("the backslope is steeper than the friction angle")
    p, t, d, b = _r(phi), _r(theta), _r(delta), _r(beta)
    root = math.sqrt(max(math.sin(p + d) * math.sin(p - b), 0.0)
                     / (math.sin(t - d) * math.sin(t + b)))
    gamma = (1.0 + root) ** 2
    return math.sin(t + p) ** 2 / (gamma * math.sin(t) ** 2 * math.sin(t - d))


def mononobe_okabe(phi: float, kh: float, delta: float = 0.0, beta: float = 0.0) -> float:
    """Mononobe–Okabe KAE behind a vertical back, kv = 0.

    Raises when the seismic angle and the slope together exceed the friction
    angle (φ − ψ − β < 0), where no pseudo-static active state exists.
    """
    p, d, b = _r(phi), _r(delta), _r(beta)
    psi = math.atan(float(kh))
    if p - psi - b < -1e-9:
        raise ValueError("no Mononobe-Okabe active state: φ − ψ − β < 0")
    root = math.sqrt(max(math.sin(p + d) * math.sin(p - psi - b), 0.0)
                     / (math.cos(d + psi) * math.cos(b)))
    return math.cos(p - psi) ** 2 / (math.cos(psi) * math.cos(d + psi) * (1.0 + root) ** 2)


def am_coefficient(A: float) -> float:
    """The maximum acceleration coefficient at the wall's centroid, (1.45 − A)·A."""
    A = float(A)
    return max((1.45 - A) * A, 0.0)

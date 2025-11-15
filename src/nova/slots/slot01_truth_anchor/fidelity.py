from __future__ import annotations
from math import sqrt
from typing import Tuple

def _wilson_ci(p_hat: float, n: int, z: float = 1.96) -> Tuple[float, float]:
    if n <= 0:
        return (0.0, 1.0)
    denom = 1 + (z*z)/n
    center = (p_hat + (z*z)/(2*n)) / denom
    radius = z * sqrt((p_hat*(1-p_hat)/n) + (z*z)/(4*n*n)) / denom
    lo, hi = max(0.0, center - radius), min(1.0, center + radius)
    return lo, hi

def fidelity_from_bits(bits: bytes) -> tuple[float, tuple[float, float], float]:
    """Return (fidelity, (ci_lo, ci_hi), abs_bias) for a raw entropy byte string."""
    if not bits:
        return 0.0, (0.0, 1.0), 0.5
    n = 8 * len(bits)
    # Count ones fast
    k = sum(bin(b).count("1") for b in bits)
    p_hat = k / n
    abs_bias = abs(p_hat - 0.5)
    F = max(0.0, 1.0 - 2.0 * abs_bias)
    lo_p, hi_p = _wilson_ci(p_hat, n, 1.96)
    lo_f = max(0.0, 1.0 - 2.0 * abs(lo_p - 0.5))
    hi_f = max(0.0, 1.0 - 2.0 * abs(hi_p - 0.5))
    # Ensure ordering
    lo_f, hi_f = min(lo_f, hi_f), max(lo_f, hi_f)
    return F, (lo_f, hi_f), abs_bias

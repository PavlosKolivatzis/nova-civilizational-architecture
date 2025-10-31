"""Trust scoring helpers for federation."""

from __future__ import annotations

import os
from typing import Dict


def score_trust(verified: bool) -> Dict[str, float | bool]:
    """Return boolean trust result."""
    return {"verified": bool(verified), "score": 1.0 if verified else 0.0}


def compute_gradient_score(
    *,
    verified: bool,
    latency_ms: float,
    age_s: float,
    continuity: float,
    w_verified: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_VERIFIED", 0.55)),
    w_latency: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_LATENCY", 0.15)),
    w_age: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_AGE", 0.15)),
    w_continuity: float = float(os.getenv("NOVA_FEDERATION_TRUST_W_CONTINUITY", 0.15)),
) -> float:
    """Compute gradient trust score in [0, 1] using EWMA-style weighting."""

    def clamp(value: float) -> float:
        return max(0.0, min(1.0, value))

    latency_component = clamp(1.0 - min(latency_ms, 2000.0) / 2000.0)
    age_component = clamp(1.0 - min(age_s, 3600.0) / 3600.0)
    continuity_component = clamp(continuity)
    verified_component = 1.0 if verified else 0.0

    score = (
        verified_component * w_verified
        + latency_component * w_latency
        + age_component * w_age
        + continuity_component * w_continuity
    )
    total_weight = w_verified + w_latency + w_age + w_continuity
    if total_weight <= 0.0:
        return 0.0
    return clamp(score / total_weight)


__all__ = ["score_trust", "compute_gradient_score"]

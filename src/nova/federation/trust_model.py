"""Basic trust scoring for Phase 15-1 scaffold."""

from __future__ import annotations

from typing import Dict


def score_trust(verified: bool) -> Dict[str, float | bool]:
    """Return a minimal trust payload for scaffold.

    Phase 15-1 keeps this binary; later phases will replace with gradients.
    """
    return {"verified": bool(verified), "score": 1.0 if verified else 0.0}


__all__ = ["score_trust"]

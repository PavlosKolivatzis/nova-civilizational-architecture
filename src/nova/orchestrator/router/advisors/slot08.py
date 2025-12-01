from __future__ import annotations

from typing import Any

from nova.orchestrator.router.decision import AdvisorScore

try:
    from nova.orchestrator.semantic_mirror import get_semantic_mirror
except Exception:  # pragma: no cover
    get_semantic_mirror = None  # type: ignore[assignment]


def _read_continuity(default: float = 0.6) -> float:
    if not get_semantic_mirror:
        return default
    try:
        mirror = get_semantic_mirror()
    except Exception:
        return default
    if not mirror:
        return default
    try:
        val = mirror.get_context("slot08.continuity_score", "router")
    except TypeError:
        try:
            val = mirror.get_context("slot08.continuity_score", default)
        except Exception:
            val = default
    except Exception:
        val = default
    if isinstance(val, (int, float)):
        return float(val)
    return default


def score_slot08(request: dict | None = None) -> AdvisorScore:
    """Return advisory score from Slot08 semantic continuity."""
    if request and "slot08_continuity" in request:
        continuity = float(request["slot08_continuity"])
    else:
        continuity = _read_continuity()
    continuity = max(0.0, min(1.0, continuity))
    details: dict[str, Any] = {"continuity": continuity}
    return AdvisorScore(name="slot08", score=continuity, details=details)

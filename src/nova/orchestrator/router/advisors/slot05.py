from __future__ import annotations

from typing import Any

from nova.orchestrator.router.decision import AdvisorScore

try:
    from nova.orchestrator.semantic_mirror import get_semantic_mirror
except Exception:  # pragma: no cover
    get_semantic_mirror = None  # type: ignore[assignment]


def _read_alignment(default: float = 0.5) -> float:
    if not get_semantic_mirror:
        return default
    try:
        mirror = get_semantic_mirror()
    except Exception:
        return default
    if not mirror:
        return default
    try:
        val = mirror.get_context("slot05.constellation_alignment", "router")
    except TypeError:
        try:
            val = mirror.get_context("slot05.constellation_alignment", default)
        except Exception:
            val = default
    except Exception:
        val = default
    if isinstance(val, (int, float)):
        return float(val)
    return default


def score_slot05(request: dict | None = None) -> AdvisorScore:
    """Return advisory score from Slot05 constellation coherence."""
    if request and "slot05_alignment" in request:
        coherence = float(request["slot05_alignment"])
    else:
        coherence = _read_alignment()
    coherence = max(0.0, min(1.0, coherence))
    details: dict[str, Any] = {"coherence": coherence}
    return AdvisorScore(name="slot05", score=coherence, details=details)

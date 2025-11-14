"""Autonomous Reflection Cycle (ARC) lightweight consistency sampling."""

from __future__ import annotations

import os
from typing import Callable, Mapping, Any

from prometheus_client import Counter, Gauge

from orchestrator.prometheus_metrics import _REGISTRY


CONSISTENCY = Gauge(
    "nova_arc_consistency",
    "Recent agreement rate between live and shadow decisions",
    registry=_REGISTRY,
)
DISAGREEMENTS = Counter(
    "nova_arc_disagreements_total",
    "Total ARC disagreements observed",
    registry=_REGISTRY,
)

_DEFAULT_EMA = 0.8
_ALPHA = 0.2
_CURRENT_EMA = _DEFAULT_EMA


def _is_enabled() -> bool:
    return os.getenv("NOVA_ARC_ENABLED", "0").strip() == "1"


def _sample_rate() -> float:
    try:
        return float(os.getenv("NOVA_ARC_SAMPLE", "0.10"))
    except ValueError:
        return 0.0


def maybe_reflect(
    decision: Any,
    shadow_alt: Any,
    why_blob: Mapping[str, Any],
    rand: Callable[[], float],
) -> None:
    """Optionally sample a reflection cycle to compare live vs. shadow."""
    if not _is_enabled():
        return

    sample_rate = _sample_rate()
    if sample_rate <= 0.0 or rand() > sample_rate:
        return

    decision_route = getattr(decision, "route", decision)
    tri_expect = float(why_blob.get("tri_delta_expected", 0.0) or 0.0)
    ok = decision_route == shadow_alt or tri_expect >= 0.0

    if not ok:
        DISAGREEMENTS.inc()

    global _CURRENT_EMA
    prev = getattr(maybe_reflect, "_ema", _CURRENT_EMA)
    curr = 1.0 if ok else 0.0
    val = _ALPHA * curr + (1 - _ALPHA) * prev
    setattr(maybe_reflect, "_ema", val)
    _CURRENT_EMA = val
    CONSISTENCY.set(val)


def reset() -> None:
    """Reset consistency gauge for tests."""
    global _CURRENT_EMA
    _CURRENT_EMA = _DEFAULT_EMA
    setattr(maybe_reflect, "_ema", _DEFAULT_EMA)
    CONSISTENCY.set(_DEFAULT_EMA)


reset()

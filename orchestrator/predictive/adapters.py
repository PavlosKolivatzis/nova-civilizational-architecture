"""Helpers for predictive contexts in the Semantic Mirror."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:  # pragma: no cover - semantic mirror optional
    from orchestrator.semantic_mirror import get_semantic_mirror
except Exception:  # pragma: no cover
    get_semantic_mirror = None  # type: ignore[assignment]


def _read_context(key: str, requester: str) -> Optional[Dict[str, Any]]:
    if not get_semantic_mirror:
        return None
    try:
        mirror = get_semantic_mirror()
        if not mirror:
            return None
        value = mirror.get_context(key, requester)
        if isinstance(value, dict):
            return value
    except Exception:
        return None
    return None


def read_predictive_snapshot(requester: str = "governance") -> Optional[Dict[str, Any]]:
    """Return the last predictive snapshot from the semantic mirror."""
    return _read_context("predictive.prediction_snapshot", requester)


def read_predictive_ledger_head(requester: str = "governance") -> Optional[Dict[str, Any]]:
    """Return the published predictive ledger head if available."""
    return _read_context("predictive.ledger_head", requester)

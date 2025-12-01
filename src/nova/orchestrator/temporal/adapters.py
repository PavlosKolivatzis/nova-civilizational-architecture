"""Helpers for publishing and consuming temporal contexts via the Semantic Mirror."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:  # pragma: no cover - semantic mirror is optional in some environments
    from nova.orchestrator.semantic_mirror import publish as mirror_publish, get_semantic_mirror
except Exception:  # pragma: no cover
    mirror_publish = None  # type: ignore[assignment]
    get_semantic_mirror = None  # type: ignore[assignment]


def publish_router_modifiers(payload: Dict[str, Any]) -> None:
    """Publish router temporal modifiers for downstream governance/slots."""
    if not mirror_publish:
        return
    try:
        mirror_publish("temporal.router_modifiers", payload, "router", ttl=180.0)
    except Exception:
        return


def _read_temporal_context(key: str, requester: str) -> Optional[Dict[str, Any]]:
    if not get_semantic_mirror:
        return None
    try:
        mirror = get_semantic_mirror()
        if not mirror:
            return None
        data = mirror.get_context(key, requester)
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def read_temporal_snapshot(requester: str = "governance") -> Optional[Dict[str, Any]]:
    """Read the latest temporal snapshot if mirror access is available."""
    return _read_temporal_context("temporal.snapshot", requester)


def read_temporal_ledger_head(requester: str = "governance") -> Optional[Dict[str, Any]]:
    """Read the published temporal ledger head for audit/debug paths."""
    return _read_temporal_context("temporal.ledger_head", requester)


def read_temporal_router_modifiers(requester: str = "governance") -> Optional[Dict[str, Any]]:
    """Read router-provided temporal penalty/allowance details."""
    return _read_temporal_context("temporal.router_modifiers", requester)

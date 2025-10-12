"""Phase-2 feature flag metrics for Slot7 Production Controls."""

from __future__ import annotations
import os
from typing import Dict, Any
from orchestrator.metrics import get_slot6_metrics


def _env_truthy(name: str) -> bool:
    """Check if environment variable is truthy."""
    v = os.getenv(name, "").strip().lower()
    return v in {"1", "true", "yes", "on"}


def get_flag_state_metrics() -> Dict[str, Any]:
    """Return Phase-2 feature-flag states and effective hash method."""
    tri_enabled = _env_truthy("NOVA_ENABLE_TRI_LINK")
    lifespan_enabled = _env_truthy("NOVA_ENABLE_LIFESPAN")
    shared_hash_enabled = _env_truthy("NOVA_USE_SHARED_HASH")

    # Detect shared hash utility availability
    try:
        from slots.common.hashutils import compute_audit_hash  # noqa: F401
        shared_hash_available = True
    except Exception:
        shared_hash_available = False

    effective_hash_method = (
        "shared_blake2b" if shared_hash_enabled and shared_hash_available else "fallback_sha256"
    )

    # Surface Slot6 p95 for ops visibility
    s6 = get_slot6_metrics().get_metrics()

    return {
        "tri_link_enabled": tri_enabled,
        "lifespan_enabled": lifespan_enabled,
        "shared_hash_enabled": shared_hash_enabled,
        "shared_hash_available": shared_hash_available,
        "effective_hash_method": effective_hash_method,
        "slot6_p95_residual_risk": s6.get("p95_residual_risk"),  # may be None early on
    }
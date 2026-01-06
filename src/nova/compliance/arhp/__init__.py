"""ARHP diagnostic verifier (non-operative)."""

from __future__ import annotations

import os

from .schemas import (
    ArhpDomain,
    ArhpEnvelope,
    ArhpExpressionOutput,
    ArhpIntent,
    ArhpRefusalEvent,
    ArhpSilenceToken,
)
from .verifier import verify_compliance

def is_arhp_diagnostics_enabled() -> bool:
    """Return True when ARHP diagnostics are explicitly enabled."""
    return os.getenv("NOVA_ENABLE_ARHP_DIAGNOSTICS", "0") == "1"

__all__ = [
    "ArhpDomain",
    "ArhpIntent",
    "ArhpEnvelope",
    "ArhpRefusalEvent",
    "ArhpExpressionOutput",
    "ArhpSilenceToken",
    "verify_compliance",
    "is_arhp_diagnostics_enabled",
]

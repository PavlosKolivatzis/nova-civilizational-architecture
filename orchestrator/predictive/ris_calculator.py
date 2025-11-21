"""
Resonance Integrity Score (RIS) Calculator — Phase 7.0-RC

Computes RIS as a composite trust metric for RC attestation:
    RIS = sqrt(M_s × E_c)

Where:
    M_s = Memory Stability (7-day TRSI rolling window)
    E_c = Ethical Compliance (Slot06 principle_preservation or governance fallback)

RIS provides a single scalar trust metric for RC validation, combining:
- Long-term memory coherence (predictive stability)
- Ethical alignment (governance compliance)

Stateless, pure function design - no ledger writes, no side effects.
"""

from __future__ import annotations

import math
import os
from typing import Optional

try:  # pragma: no cover - semantic mirror optional
    from orchestrator.semantic_mirror import get_semantic_mirror
except Exception:  # pragma: no cover
    get_semantic_mirror = None  # type: ignore[assignment]


def compute_ris(
    memory_stability: float,
    ethical_compliance: Optional[float] = None,
) -> float:
    """
    Compute Resonance Integrity Score (RIS).

    Formula (Phase 7.0-RC):
        RIS = sqrt(M_s × E_c)

    Where:
        M_s = Memory Stability [0.0, 1.0] from MemoryResonanceWindow
        E_c = Ethical Compliance [0.0, 1.0] from Slot06 or governance fallback

    Args:
        memory_stability: 7-day rolling TRSI stability score [0.0, 1.0]
        ethical_compliance: Optional ethical compliance score [0.0, 1.0]
            If None, uses hierarchy: Slot06 → governance → 1.0 (local mode)

    Returns:
        float: RIS score [0.0, 1.0], clamped and stable
    """
    # Clamp memory stability to [0.0, 1.0]
    m_s = max(0.0, min(1.0, float(memory_stability)))

    # Resolve ethical compliance via hierarchy
    e_c = _resolve_ethical_compliance(ethical_compliance)

    # Compute RIS with square-root normalization (distributed trust systems)
    ris_raw = m_s * e_c
    ris = math.sqrt(ris_raw)

    # Final clamping (should be redundant, but defensive)
    return max(0.0, min(1.0, ris))


def _resolve_ethical_compliance(explicit_value: Optional[float]) -> float:
    """
    Resolve ethical compliance score via hierarchy.

    Hierarchy:
        1. Explicit value passed to compute_ris()
        2. Slot06 principle_preservation from semantic mirror
        3. Governance ethical_compliance_score from semantic mirror
        4. 1.0 (RC local mode - neutral trust)

    Args:
        explicit_value: Explicit E_c value if provided

    Returns:
        float: Ethical compliance score [0.0, 1.0]
    """
    if explicit_value is not None:
        return max(0.0, min(1.0, float(explicit_value)))

    # Try Slot06 principle_preservation
    if get_semantic_mirror:
        try:
            mirror = get_semantic_mirror()
            if mirror:
                # Check Slot06 principle_preservation
                slot06_culture = mirror.get_context(
                    "slot06.cultural_profile",
                    "ris_calculator"
                )
                if (
                    slot06_culture
                    and isinstance(slot06_culture, dict)
                    and "principle_preservation" in slot06_culture
                ):
                    return max(0.0, min(1.0, float(slot06_culture["principle_preservation"])))

                # Fallback: governance ethical compliance
                governance_snapshot = mirror.get_context(
                    "governance.ethics",
                    "ris_calculator"
                )
                if (
                    governance_snapshot
                    and isinstance(governance_snapshot, dict)
                    and "compliance_score" in governance_snapshot
                ):
                    return max(0.0, min(1.0, float(governance_snapshot["compliance_score"])))
        except Exception:  # pragma: no cover
            pass  # Fall through to local mode

    # Local mode: neutral trust (no ethical data available)
    return 1.0


def compute_ris_with_smoothing(
    memory_stability: float,
    ethical_compliance: Optional[float] = None,
    previous_ris: Optional[float] = None,
    alpha: float = 0.5,
) -> float:
    """
    Compute RIS with optional exponential smoothing to reduce volatility.

    Smoothing formula:
        RIS_smoothed = alpha × RIS_current + (1 - alpha) × RIS_previous

    Args:
        memory_stability: Current memory stability score
        ethical_compliance: Current ethical compliance score
        previous_ris: Previous RIS value for smoothing (None = no smoothing)
        alpha: Smoothing factor [0.0, 1.0]
            - 0.0 = all previous (no update)
            - 1.0 = all current (no smoothing)
            - 0.5 = balanced (recommended for RC)

    Returns:
        float: Smoothed RIS score [0.0, 1.0]
    """
    current_ris = compute_ris(memory_stability, ethical_compliance)

    if previous_ris is None:
        return current_ris

    # Exponential smoothing
    alpha = max(0.0, min(1.0, alpha))
    smoothed = (alpha * current_ris) + ((1.0 - alpha) * previous_ris)

    return max(0.0, min(1.0, smoothed))


def ris_to_dict(
    ris: float,
    memory_stability: float,
    ethical_compliance: float,
    timestamp: float,
) -> dict:
    """
    Serialize RIS computation to dict for semantic mirror publishing.

    Args:
        ris: Computed RIS score
        memory_stability: Memory stability input
        ethical_compliance: Ethical compliance input
        timestamp: Computation timestamp (unix)

    Returns:
        dict: Serialized RIS snapshot
    """
    return {
        "ris": ris,
        "memory_stability": memory_stability,
        "ethical_compliance": ethical_compliance,
        "timestamp": timestamp,
        "version": "7.0-RC",
    }

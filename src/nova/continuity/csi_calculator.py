"""
Continuity Stability Index (CSI) Calculator

Computes cross-phase fusion metric from Phase 14 RC attestation history.

Phase 8 Minimal Integration
"""

from typing import Dict, List, Optional
import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent.parent.parent
if str(repo_root / "src") not in sys.path:
    sys.path.insert(0, str(repo_root / "src"))

from nova.ledger.rc_query import get_rc_chain


def compute_csi(phase: str = "7.0-rc", window_size: int = 7) -> float:
    """
    Compute Continuity Stability Index from RC attestations.

    CSI = 0.3 × P6_stability + 0.3 × P7_stability + 0.4 × correlation

    Args:
        phase: RC phase identifier
        window_size: Number of recent attestations to analyze

    Returns:
        CSI value [0.0, 1.0]
    """
    # Query RC attestations from Phase 14 ledger
    chain = get_rc_chain(phase)

    if not chain:
        return 0.0

    # Extract Phase 7 metrics (from RC attestations)
    recent_records = chain[-window_size:]
    p7_stability = sum(
        r.payload.get("memory_resonance", {}).get("stability", 0.0)
        for r in recent_records
    ) / len(recent_records)

    # Phase 6 stability (placeholder - would load from sealed archives)
    p6_stability = 0.85  # TODO: Load from Phase 6 archives

    # Inter-phase correlation (simplified)
    correlation = min(p6_stability, p7_stability)

    # Weighted fusion (from blueprint)
    csi = 0.3 * p6_stability + 0.3 * p7_stability + 0.4 * correlation

    return min(1.0, max(0.0, csi))


def get_csi_breakdown(phase: str = "7.0-rc", window_size: int = 7) -> Dict:
    """
    Get detailed CSI breakdown with component metrics.

    Args:
        phase: RC phase identifier
        window_size: Number of recent attestations to analyze

    Returns:
        Dictionary with CSI components and diagnostics
    """
    chain = get_rc_chain(phase)

    if not chain:
        return {
            "csi": 0.0,
            "p6_stability": 0.0,
            "p7_stability": 0.0,
            "correlation": 0.0,
            "attestation_count": 0,
            "window_size": window_size,
        }

    # Extract Phase 7 metrics
    recent_records = chain[-window_size:]

    memory_scores = [
        r.payload.get("memory_resonance", {}).get("stability", 0.0)
        for r in recent_records
    ]
    ris_scores = [
        r.payload.get("ris", {}).get("score", 0.0)
        for r in recent_records
    ]

    p7_stability = sum(memory_scores) / len(memory_scores) if memory_scores else 0.0
    p7_ris = sum(ris_scores) / len(ris_scores) if ris_scores else 0.0

    # Phase 6 (placeholder)
    p6_stability = 0.85

    # Correlation
    correlation = min(p6_stability, p7_stability)

    # CSI computation
    csi = 0.3 * p6_stability + 0.3 * p7_stability + 0.4 * correlation
    csi = min(1.0, max(0.0, csi))

    return {
        "csi": csi,
        "p6_stability": p6_stability,
        "p7_stability": p7_stability,
        "p7_ris": p7_ris,
        "correlation": correlation,
        "attestation_count": len(chain),
        "window_size": window_size,
        "weights": {
            "p6": 0.3,
            "p7": 0.3,
            "correlation": 0.4,
        },
    }

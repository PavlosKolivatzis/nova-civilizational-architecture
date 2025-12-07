"""
Slot09 VOID Bypass - RFC-014 Phase 14.4-B Priority 1

Phase 14.4: VOID semantic propagation across cognitive slots.
Slot09 must treat VOID (empty SystemGraph) as ontologically valid, not adversarial.

Architecture:
    Slot02 BIAS_REPORT@1 with graph_state='void'
        ↓
    Slot09 distortion detection
        ↓
    VOID bypass: H=0 is expected, not suspicious
        ↓
    Return distortion_score=0.0, confidence=1.0

Invariant Compliance:
- #1 Separation: VOID check isolated, doesn't affect non-VOID processing
- #7 Observability: Metric slot09_void_passthrough_total
- #9 No Silent Drift: Explicit VOID handling, documented

RFC-014 § 3.2 slot09_distortion_protection policy.
"""

import logging
import os
from typing import Dict, Any, Optional
from prometheus_client import Counter

logger = logging.getLogger(__name__)

# Phase 14.4 metrics (RFC-014 observability)
try:
    from nova.metrics.registry import REGISTRY
    _void_passthrough_counter = Counter(
        "slot09_void_passthrough_total",
        "Slot09 VOID bypass events (distortion filter passthrough)",
        registry=REGISTRY
    )
except Exception:
    # Graceful fallback if metrics registry unavailable
    _void_passthrough_counter = Counter(
        "slot09_void_passthrough_total",
        "Slot09 VOID bypass events (distortion filter passthrough)"
    )


def is_void_state(graph_state: Optional[str]) -> bool:
    """
    Check if graph_state indicates VOID (empty SystemGraph).

    Args:
        graph_state: Value from BIAS_REPORT@1.metadata.graph_state

    Returns:
        True if VOID state, False otherwise
    """
    return graph_state == 'void'


def create_void_passthrough_response(
    request_context: Dict[str, Any],
    trace_id: str = "void_bypass"
) -> Dict[str, Any]:
    """
    Create Slot09 response for VOID state (passthrough, no distortion).

    RFC-014 § 3.2 slot09_distortion_protection policy:
    - VOID → distortion_score = 0.0 (silence ≠ threat)
    - confidence = 1.0 (VOID is fully defined, not uncertain)
    - spectral_filter = disabled (H=0 is mathematically expected)

    Args:
        request_context: Request metadata for audit trail
        trace_id: Trace ID for logging

    Returns:
        policy_result dict compatible with Slot09 response builder
    """
    logger.debug(f"VOID state detected (trace_id={trace_id}) - bypassing distortion filters")
    _void_passthrough_counter.inc()

    # RFC-014: VOID = ontologically valid, not adversarial
    return {
        'final_policy': 'STANDARD_PROCESSING',  # Pass-through
        'distortion_score': 0.0,  # No distortion (silence ≠ threat)
        'confidence': 1.0,  # VOID is fully defined
        'spectral_filter_disabled': True,  # H=0 expected for VOID
        'threat_level': 0.0,  # No threat
        'risk_level': 0.0,  # No risk
        'manipulation_score': 0.0,  # No manipulation
        'extraction_score': 0.0,  # No extraction
        'analysis': {
            'graph_state': 'void',
            'rationale': 'Empty SystemGraph (VOID) - ontologically valid, not adversarial',
            'spectral_entropy': 0.0,  # H(G_void) = 0 (expected)
            'equilibrium_ratio': None,  # Undefined for empty graph
            'shield_factor': 0.0,  # No relations to shield
        },
        'metadata': {
            'void_bypass': True,
            'rfc': 'RFC-014',
            'ontology_version': 'nova.operating@1.1.0',
            'trace_id': trace_id,
        }
    }


def should_bypass_distortion_check(
    graph_state: Optional[str] = None,
    bias_report: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Determine if distortion check should be bypassed due to VOID state.

    Args:
        graph_state: Direct graph_state value (if available)
        bias_report: Full BIAS_REPORT@1 (alternative source)

    Returns:
        True if VOID bypass required, False otherwise
    """
    # Check feature flag
    void_mode_enabled = os.getenv("NOVA_ENABLE_VOID_MODE", "1") == "1"
    if not void_mode_enabled:
        return False

    # Check graph_state (direct parameter)
    if graph_state and is_void_state(graph_state):
        return True

    # Check bias_report (fallback)
    if bias_report:
        state_from_report = bias_report.get('metadata', {}).get('graph_state')
        if is_void_state(state_from_report):
            return True

    return False


def get_void_metrics() -> Dict[str, Any]:
    """
    Get VOID bypass metrics for monitoring.

    Returns:
        Dict with void_passthrough_total count
    """
    try:
        return {
            'void_passthrough_total': _void_passthrough_counter._value._value
        }
    except Exception:
        return {'void_passthrough_total': 0}

"""
Adapter integration patch for meta-lens plugin.

Provides real adapter functions that call actual Nova slots through the orchestrator's
contract system, with graceful fallback to mocks when adapters unavailable.
"""

import os
import time
from typing import Dict, Any

# Adapter timeout and retry configuration
ADAPTER_TIMEOUT_MS = int(os.getenv("META_LENS_ADAPTER_TIMEOUT_MS", "200"))
ADAPTER_MAX_RETRIES = int(os.getenv("META_LENS_ADAPTER_MAX_RETRIES", "2"))
ADAPTER_BREAKER_TTL_SEC = int(os.getenv("META_LENS_ADAPTER_BREAKER_TTL_SEC", "30"))

# Simple circuit breaker state
_breaker_state = {
    "failures": 0,
    "last_failure": 0,
    "is_open": False
}

def _call_with_timeout_retry(adapter_registry: Any, contract_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call adapter with timeout and retry logic."""
    # Check circuit breaker
    now = time.time()
    if _breaker_state["is_open"] and (now - _breaker_state["last_failure"]) < ADAPTER_BREAKER_TTL_SEC:
        raise Exception(f"Circuit breaker open for {contract_id}")

    for attempt in range(ADAPTER_MAX_RETRIES + 1):
        try:
            # Note: Real timeout implementation would depend on adapter registry implementation
            # This is a placeholder for the timeout logic
            start_time = time.time()
            result = adapter_registry.call(contract_id, payload)
            duration_ms = (time.time() - start_time) * 1000

            if duration_ms > ADAPTER_TIMEOUT_MS:
                raise TimeoutError(f"Adapter call to {contract_id} took {duration_ms:.1f}ms > {ADAPTER_TIMEOUT_MS}ms")

            # Reset breaker on success
            _breaker_state["failures"] = 0
            _breaker_state["is_open"] = False
            return result

        except Exception as e:
            if attempt == ADAPTER_MAX_RETRIES:
                # Final attempt failed - update breaker
                _breaker_state["failures"] += 1
                _breaker_state["last_failure"] = now
                if _breaker_state["failures"] >= 3:
                    _breaker_state["is_open"] = True
                raise e
            # Retry with exponential backoff
            time.sleep(0.01 * (2 ** attempt))

def create_real_adapter_functions(content, context):
    """Create real adapter functions that call actual Nova slots."""

    # Access orchestrator adapter registry through context
    adapter_registry = context.get("adapter_registry")

    if not adapter_registry:
        # Fallback to mocks if registry not available
        return create_mock_functions()

    def real_tri_fn(R):
        """Call Slot4 TRI Engine for real analysis."""
        try:
            # Call TRI_REPORT@1 contract
            tri_payload = {
                "content": content,
                "context": context,
                "state_vector": R["meta_lens_analysis"]["state_vector"]
            }
            result = _call_with_timeout_retry(adapter_registry, "TRI_REPORT@1", tri_payload)

            # Extract resonance metrics from TRI response
            return {
                "resonance_cross": result.get("cross_family_resonance", 0.5),
                "coherence": result.get("coherence", 0.5),
                "stability": result.get("stability", 0.5)
            }
        except Exception as e:
            # Graceful degradation
            return {"resonance_cross": 0.5, "coherence": 0.5, "error": str(e)}

    def real_const_fn(R):
        """Call Slot5 Constellation Engine for topology analysis."""
        try:
            const_payload = {
                "content": content,
                "tri_input": R["meta_lens_analysis"]["state_vector"],
                "context": context
            }
            result = _call_with_timeout_retry(adapter_registry, "CONSTELLATION_REPORT@1", const_payload)

            return {
                "coordination_hint": result.get("coordination_hint", "stable"),
                "topology": result.get("topology_type", "connected"),
                "phase_coherence": result.get("phase_coherence", 0.5)
            }
        except Exception as e:
            return {"coordination_hint": "degraded", "topology": "unknown", "error": str(e)}

    def real_culture_fn(R, tri, const):
        """Call Slot6 Cultural Synthesis for context analysis."""
        try:
            culture_payload = {
                "content": content,
                "tri_signals": tri,
                "constellation_state": const,
                "context": context
            }
            result = _call_with_timeout_retry(adapter_registry, "CULTURAL_PROFILE@1", culture_payload)

            return {
                "synthesis_confidence": result.get("synthesis_confidence", 0.5),
                "risk_overall": result.get("risk_assessment", {}).get("overall", 0.0),
                "historical_context": result.get("historical_context", ""),
                "bias_markers": result.get("bias_markers", []),
                "risk_vectors": result.get("risk_vectors", []),
                "mitigation_suggestions": result.get("mitigation_suggestions", [])
            }
        except Exception as e:
            return {
                "synthesis_confidence": 0.0,
                "risk_overall": 1.0,  # Conservative on error
                "historical_context": f"Error in cultural analysis: {e}",
                "bias_markers": ["analysis_error"],
                "risk_vectors": ["cultural_analysis_failure"],
                "mitigation_suggestions": ["retry_analysis"]
            }

    def real_distort_fn(R):
        """Call Slot9 Distortion Protection for manipulation detection."""
        try:
            distort_payload = {
                "content": content,
                "context": context,
                "frozen_ref": R["iteration"]["frozen_inputs"]["infinity_ref"]
            }
            result = _call_with_timeout_retry(adapter_registry, "DETECTION_REPORT@1", distort_payload)

            return {
                "overall_score": result.get("distortion_score", 0.0),
                "patterns": result.get("patterns_detected", []),
                "confidence": result.get("confidence", 0.5),
                "threat_level": result.get("threat_level", "low")
            }
        except Exception as e:
            return {
                "overall_score": 0.5,  # Conservative default
                "patterns": [],
                "confidence": 0.0,
                "error": str(e)
            }

    def real_emo_fn(R):
        """Call Slot3 Emotional Matrix for volatility analysis."""
        try:
            emo_payload = {
                "content": content,
                "context": context,
                "frozen_ref": R["iteration"]["frozen_inputs"]["padel_ref"]
            }
            result = _call_with_timeout_retry(adapter_registry, "EMOTION_REPORT@1", emo_payload)

            return {
                "volatility": result.get("volatility", 0.0),
                "stability": result.get("stability", 1.0),
                "emotional_state": result.get("emotional_state", "neutral")
            }
        except Exception as e:
            return {
                "volatility": 0.5,  # Conservative default
                "stability": 0.5,
                "error": str(e)
            }

    return real_tri_fn, real_const_fn, real_culture_fn, real_distort_fn, real_emo_fn


def create_mock_functions():
    """Fallback mock functions for when adapter registry unavailable."""
    def mock_tri_fn(R):
        return {"resonance_cross": 0.7, "coherence": 0.8}

    def mock_const_fn(R):
        return {"coordination_hint": "stable", "topology": "connected"}

    def mock_culture_fn(R, tri, const):
        return {
            "synthesis_confidence": 0.85,
            "risk_overall": 0.25,
            "historical_context": "Mock analysis context",
            "bias_markers": ["mock_analysis"],
            "risk_vectors": ["mock_vector"],
            "mitigation_suggestions": ["use_real_adapters"]
        }

    def mock_distort_fn(R):
        return {
            "overall_score": 0.15,
            "patterns": [{"id": "mock-1", "name": "baseline_check", "severity": 0.1, "confidence": 0.9}],
            "confidence": 0.85
        }

    def mock_emo_fn(R):
        return {"volatility": 0.2, "stability": 0.8}

    return mock_tri_fn, mock_const_fn, mock_culture_fn, mock_distort_fn, mock_emo_fn
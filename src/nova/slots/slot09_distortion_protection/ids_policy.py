import os
import logging
from services.ids.integration import ids_service
from services.ids.core import IDSState
from config.feature_flags import IDS_ENABLED
from nova.orchestrator.semantic_mirror import get_semantic_mirror

logger = logging.getLogger(__name__)


def get_phase_lock_context() -> dict:
    """Retrieve Light-Clock phase_lock context for distortion protection."""
    if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
        return {"phase_lock": None, "available": False, "reason": "feature_disabled"}

    try:
        semantic_mirror = get_semantic_mirror()
        phase_lock_value = semantic_mirror.get_context("slot07.phase_lock", "slot09_distortion_protection")

        if phase_lock_value is not None:
            logger.debug(f"Retrieved phase_lock for distortion protection: {phase_lock_value:.3f}")
            return {
                "phase_lock": phase_lock_value,
                "available": True,
                "coherence_level": _categorize_coherence(phase_lock_value)
            }
        else:
            return {"phase_lock": None, "available": False, "reason": "context_unavailable"}

    except Exception as e:
        logger.warning(f"Failed to retrieve phase_lock context: {e}")
        return {"phase_lock": None, "available": False, "reason": f"error_{type(e).__name__}"}


def _categorize_coherence(phase_lock: float) -> str:
    """Categorize phase_lock coherence for policy decisions."""
    if phase_lock > 0.8:
        return "high"
    elif phase_lock > 0.6:
        return "medium"
    elif phase_lock > 0.4:
        return "low"
    else:
        return "minimal"


def apply_phase_lock_policy_adjustments(base_policy: dict, phase_lock_context: dict) -> dict:
    """Apply phase_lock context adjustments to IDS policy decisions."""
    if not phase_lock_context["available"]:
        base_policy["phase_lock_context"] = phase_lock_context
        return base_policy

    phase_lock = phase_lock_context["phase_lock"]
    coherence_level = phase_lock_context["coherence_level"]

    policy_adjustments = {
        "original_policy": base_policy["policy"],
        "original_severity": base_policy["severity"],
        "phase_lock_value": phase_lock,
        "coherence_level": coherence_level
    }

    # High coherence allows slight relaxation
    if coherence_level == "high":
        if base_policy["policy"] == "DEGRADE_AND_REVIEW" and base_policy["severity"] == "medium":
            base_policy["policy"] = "STANDARD_PROCESSING"
            base_policy["severity"] = "normal"
            policy_adjustments["adjustment"] = "relaxed_due_to_high_coherence"
        else:
            policy_adjustments["adjustment"] = "none_high_coherence_maintained"

    # Low coherence increases strictness
    elif coherence_level == "low":
        if base_policy["policy"] == "ALLOW_FASTPATH":
            base_policy["policy"] = "STANDARD_PROCESSING"
            base_policy["severity"] = "normal"
            policy_adjustments["adjustment"] = "downgraded_due_to_low_coherence"
        elif base_policy["policy"] == "STANDARD_PROCESSING":
            base_policy["policy"] = "DEGRADE_AND_REVIEW"
            base_policy["severity"] = "medium"
            policy_adjustments["adjustment"] = "degraded_due_to_low_coherence"
        else:
            policy_adjustments["adjustment"] = "none_already_strict"

    # Minimal coherence forces maximum strictness
    elif coherence_level == "minimal":
        if base_policy["policy"] in ["ALLOW_FASTPATH", "STANDARD_PROCESSING"]:
            base_policy["policy"] = "DEGRADE_AND_REVIEW"
            base_policy["severity"] = "medium"
            policy_adjustments["adjustment"] = "forced_degradation_minimal_coherence"
        elif base_policy["policy"] == "DEGRADE_AND_REVIEW":
            base_policy["policy"] = "BLOCK_OR_SANDBOX"
            base_policy["severity"] = "high"
            policy_adjustments["adjustment"] = "escalated_to_block_minimal_coherence"
        else:
            policy_adjustments["adjustment"] = "none_already_maximum_strict"
    else:
        policy_adjustments["adjustment"] = "none_medium_coherence_standard"

    # Update reason to include phase_lock context
    original_reason = base_policy["reason"]
    base_policy["reason"] = f"{original_reason}|phase_lock_{phase_lock:.3f}_{coherence_level}"

    base_policy["phase_lock_context"] = phase_lock_context
    base_policy["phase_lock_adjustments"] = policy_adjustments

    return base_policy


def apply_ids_policy(analysis_result: dict) -> dict:
    """Apply policy based on IDS analysis results with Light-Clock phase_lock context validation"""
    if not IDS_ENABLED:
        return {"policy": "STANDARD_PROCESSING", "reason": "ids_disabled"}

    stability = analysis_result.get("stability", 0.0)
    drift = analysis_result.get("drift", 0.0)
    state = analysis_result.get("state", IDSState.DISINTEGRATING.value)
    abs_drift = abs(drift)

    # Base IDS policy determination
    if stability < 0.25:
        base_policy = {
            "policy": "BLOCK_OR_SANDBOX",
            "reason": f"ids:stability_{stability:.3f}|state_{state}",
            "severity": "high",
        }
    elif 0.25 <= stability < 0.50 and abs_drift > 0.10:
        base_policy = {
            "policy": "DEGRADE_AND_REVIEW",
            "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
            "severity": "medium",
        }
    elif stability >= 0.75 and abs_drift < 0.02:
        base_policy = {
            "policy": "ALLOW_FASTPATH",
            "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
            "severity": "low",
        }
    else:
        base_policy = {
            "policy": "STANDARD_PROCESSING",
            "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
            "severity": "normal",
        }

    # Apply Light-Clock phase_lock context adjustments
    phase_lock_context = get_phase_lock_context()
    final_policy = apply_phase_lock_policy_adjustments(base_policy, phase_lock_context)

    return final_policy


def policy_check_with_ids(content_analysis: dict, trace_id: str) -> dict:
    """Enhanced policy check with IDS integration"""
    if not IDS_ENABLED:
        return {"final_policy": "STANDARD_PROCESSING", "reason": "ids_disabled"}

    vectors = content_analysis.get("embedding_vectors", {})
    traits_vector = vectors.get("traits", [])
    content_vector = vectors.get("content", [])

    traits_analysis = ids_service.analyze_vector(traits_vector, trace_id=trace_id, scope="traits")
    content_analysis_result = ids_service.analyze_vector(content_vector, trace_id=trace_id, scope="content")

    traits_policy = apply_ids_policy(traits_analysis)
    content_policy = apply_ids_policy(content_analysis_result)

    policy_priority = {
        "BLOCK_OR_SANDBOX": 4,
        "DEGRADE_AND_REVIEW": 3,
        "STANDARD_PROCESSING": 2,
        "ALLOW_FASTPATH": 1,
    }

    policies = [traits_policy, content_policy]
    final_policy = max(policies, key=lambda p: policy_priority[p["policy"]])

    return {
        "final_policy": final_policy["policy"],
        "final_reason": final_policy["reason"],
        "final_severity": final_policy["severity"],
        "traits_analysis": {**traits_analysis, "policy": traits_policy},
        "content_analysis": {**content_analysis_result, "policy": content_policy},
        "trace_id": trace_id,
        "ids_enabled": True,
    }

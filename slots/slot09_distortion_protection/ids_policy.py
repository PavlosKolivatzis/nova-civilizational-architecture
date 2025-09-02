from services.ids.integration import ids_service
from services.ids.core import IDSState
from config.feature_flags import IDS_ENABLED


def apply_ids_policy(analysis_result: dict) -> dict:
    """Apply policy based on IDS analysis results with reason codes"""
    if not IDS_ENABLED:
        return {"policy": "STANDARD_PROCESSING", "reason": "ids_disabled"}

    stability = analysis_result.get("stability", 0.0)
    drift = analysis_result.get("drift", 0.0)
    state = analysis_result.get("state", IDSState.DISINTEGRATING.value)
    abs_drift = abs(drift)

    if stability < 0.25:
        return {
            "policy": "BLOCK_OR_SANDBOX",
            "reason": f"ids:stability_{stability:.3f}|state_{state}",
            "severity": "high",
        }
    if 0.25 <= stability < 0.50 and abs_drift > 0.10:
        return {
            "policy": "DEGRADE_AND_REVIEW",
            "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
            "severity": "medium",
        }
    if stability >= 0.75 and abs_drift < 0.02:
        return {
            "policy": "ALLOW_FASTPATH",
            "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
            "severity": "low",
        }
    return {
        "policy": "STANDARD_PROCESSING",
        "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
        "severity": "normal",
    }


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

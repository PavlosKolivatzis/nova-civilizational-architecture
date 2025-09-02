import json
from services.ids.integration import ids_service
from services.ids.core import IDSState
from config.feature_flags import IDS_ENABLED
from .. import memory_logger


def check_memory_write_eligibility(embedding_vector: list, trace_id: str) -> dict:
    """Check if memory write is allowed based on IDS state with detailed results"""
    if not IDS_ENABLED:
        return {"allowed": True, "reason": "ids_disabled"}
    if not embedding_vector:
        return {"allowed": False, "reason": "empty_vector"}

    analysis = ids_service.analyze_vector(embedding_vector, trace_id=trace_id, scope="memory")
    stability = analysis.get("stability", 0.0)
    drift = analysis.get("drift", 0.0)
    state = analysis.get("state", IDSState.DISINTEGRATING.value)
    abs_drift = abs(drift)

    if state != IDSState.STABLE.value:
        return {
            "allowed": False,
            "reason": f"ids:state_{state}",
            "stability": stability,
            "drift": drift,
            "state": state,
        }
    if abs_drift > 0.15:
        return {
            "allowed": False,
            "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}",
            "stability": stability,
            "drift": drift,
            "state": state,
        }
    return {
        "allowed": True,
        "reason": f"ids:stability_{stability:.3f}|drift_{abs_drift:.3f}|state_{state}",
        "stability": stability,
        "drift": drift,
        "state": state,
    }


def perform_memory_write(embedding_vector: list, metadata: dict, trace_id: str) -> dict:
    """Placeholder memory write implementation."""
    raise NotImplementedError("Memory write functionality not implemented.")


def protected_memory_write(embedding_vector: list, metadata: dict, trace_id: str) -> dict:
    """Protected memory write with IDS eligibility check and detailed logging"""
    eligibility = check_memory_write_eligibility(embedding_vector, trace_id)
    if not eligibility["allowed"]:
        memory_logger.warning(
            json.dumps(
                {
                    "event": "memory_write_blocked",
                    "trace_id": trace_id,
                    "reason": eligibility["reason"],
                    "stability": eligibility.get("stability", 0.0),
                    "drift": eligibility.get("drift", 0.0),
                    "state": eligibility.get("state", "unknown"),
                }
            )
        )
        return {
            "success": False,
            "reason": eligibility["reason"],
            "blocked_by": "ids_protection",
            "trace_id": trace_id,
        }
    try:
        result = perform_memory_write(embedding_vector, metadata, trace_id)
        return {**result, "ids_protection": "passed", "reason": eligibility["reason"]}
    except Exception as e:
        memory_logger.error(
            json.dumps(
                {
                    "event": "memory_write_failed",
                    "trace_id": trace_id,
                    "error": str(e),
                    "ids_eligibility": eligibility,
                }
            )
        )
        raise

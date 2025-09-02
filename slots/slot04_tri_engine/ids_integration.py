from services.ids.integration import ids_service
from config.feature_flags import IDS_ENABLED, IDS_WEIGHT, IDS_SANDBOX_ONLY


def integrate_ids_into_tri(tri_engine, vector: list, trace_id: str, scope: str = "traits"):
    """Integrate IDS analysis into TRI engine with proper env flag handling"""
    base_score = tri_engine.calculate_base_score(vector)
    if not IDS_ENABLED:
        return {
            "base_score": base_score,
            "final_score": base_score,
            "trace_id": trace_id,
            "state": "bypass",
            "ids_enabled": False,
        }

    previous_vector = tri_engine.get_previous_vector(trace_id, scope)
    analysis = ids_service.analyze_vector(vector, previous_vector, trace_id, scope)
    tri_engine.store_vector(vector, trace_id, scope)

    if IDS_SANDBOX_ONLY:
        return {
            "base_score": base_score,
            "final_score": base_score,
            **analysis,
            "trace_id": trace_id,
            "ids_sandbox": True,
        }

    stability_factor = analysis["stability"] ** 2
    drift_penalty = abs(analysis["drift"]) * 0.3
    adjusted = base_score * ((1 - IDS_WEIGHT) + IDS_WEIGHT * stability_factor) - IDS_WEIGHT * drift_penalty

    max_change = 0.15
    final_score = base_score + max(-max_change, min(max_change, adjusted - base_score))

    return {
        "base_score": base_score,
        "adjusted_score": adjusted,
        "final_score": max(0.0, min(1.0, final_score)),
        **analysis,
        "trace_id": trace_id,
        "ids_weight": IDS_WEIGHT,
        "max_change_applied": abs(final_score - base_score) >= max_change - 1e-10,
    }

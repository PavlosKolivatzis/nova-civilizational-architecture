from fastapi import APIRouter
from typing import Any, Dict, List
from slots.config import get_config_manager  # EnhancedConfigManager global

router = APIRouter()

def _get_slot6_metrics() -> Dict[str, Any]:
    """Get Slot 6 observability metrics."""
    try:
        from slots.slot06_cultural_synthesis.multicultural_truth_synthesis import get_legacy_usage_count
        legacy_calls = get_legacy_usage_count()
    except (ImportError, AttributeError):
        # Legacy module blocked or not available
        legacy_calls = None
    
    # TODO: Add last decision metrics when implemented
    return {
        "version": "v7.4.1",
        "legacy_calls_total": legacy_calls,
        "last_decision": None,  # Placeholder for future implementation
        "p95_residual_risk": None,  # Placeholder for future implementation
        "decisions_total": None,  # Placeholder for future implementation
    }

@router.get("/health/config", tags=["health"])
async def health_config() -> Dict[str, Any]:
    mgr = await get_config_manager()

    # Determine hot-reload mode
    mode = "disabled"
    if getattr(mgr, "_observer", None):
        mode = "watchdog"
    elif getattr(mgr, "_poll_task", None):
        mode = "polling"

    slots: List[Dict[str, Any]] = []
    for sid in sorted(mgr.list_slots()):
        meta = mgr.get_slot_metadata(sid)
        slots.append({
            "id": sid,
            "name": getattr(meta, "name", None),
            "version": getattr(meta, "version", None),
        })

    # Get Slot 6 specific metrics
    slot6_metrics = _get_slot6_metrics()

    return {
        "service": "nova-config",
        "hot_reload_enabled": bool(getattr(mgr, "enable_hot_reload", False)),
        "hot_reload_mode": mode,   # "watchdog" | "polling" | "disabled"
        "slots_loaded": len(slots),
        "slots": slots,
        "slot6": slot6_metrics,  # Slot 6 observability
    }

from fastapi import APIRouter
from typing import Any, Dict, List
from slots.config import get_config_manager  # EnhancedConfigManager global

router = APIRouter()

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

    return {
        "service": "nova-config",
        "hot_reload_enabled": bool(getattr(mgr, "enable_hot_reload", False)),
        "hot_reload_mode": mode,   # "watchdog" | "polling" | "disabled"
        "slots_loaded": len(slots),
        "slots": slots,
    }

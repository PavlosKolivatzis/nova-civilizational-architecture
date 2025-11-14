import warnings
from fastapi import APIRouter
from typing import Any, Dict, List
from nova.slots.config import get_config_manager  # EnhancedConfigManager global

router = APIRouter()

def _get_plugin_info() -> Dict[str, Any]:
    """Get plugin system information."""
    try:
        import os
        from orchestrator.plugins.loader import PluginLoader
        
        # Check if plugins are enabled
        enabled_env = os.getenv("NOVA_SLOTS", "").strip()
        enabled = [s.strip() for s in enabled_env.split(",") if s.strip()] if enabled_env else None
        
        # Try to get loader instance (may not exist yet)
        try:
            # This would be from app state in real implementation
            loader = PluginLoader(enabled=enabled).discover()
            
            plugins = {}
            for slot_id, slot in loader.items():
                plugins[slot_id] = {
                    "version": slot.plugin.version if slot.plugin else None,
                    "optional": slot.meta.get("optional", True),
                    "contracts": list(slot.adapters.keys()) if slot.adapters else [],
                    "loaded": bool(slot.plugin),
                    "description": slot.meta.get("description", "")
                }
            
            contracts_available = sorted({
                c for slot in loader.values() 
                for c in (slot.adapters or {}).keys()
            })
            
            return {
                "plugins": plugins,
                "contracts_available": contracts_available,
                "slots_enabled": enabled or "ALL"
            }
            
        except Exception:
            return {
                "plugins": {},
                "contracts_available": [],
                "slots_enabled": enabled or "ALL",
                "status": "plugin_system_not_initialized"
            }
            
    except ImportError:
        return {
            "plugins": {},
            "contracts_available": [],
            "slots_enabled": "UNKNOWN",
            "status": "plugin_system_unavailable"
        }

def _get_slot6_metrics() -> Dict[str, Any]:
    """Get Slot 6 observability metrics."""
    # Try centralized metrics first
    try:
        from orchestrator.metrics import get_slot6_metrics
        return get_slot6_metrics().get_metrics()
    except ImportError:
        # Fall back to legacy-only metrics
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                from nova.slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
                    get_legacy_usage_count,
                )
            legacy_calls = get_legacy_usage_count()
        except (ImportError, AttributeError):
            # Legacy module blocked or not available
            legacy_calls = None

        return {
            "version": "v7.4.1",
            "legacy_calls_total": legacy_calls,
            "last_decision": None,
            "p95_residual_risk": None,
            "decisions_total": None,
            "decisions": {"approved": None, "transform": None, "blocked": None}
        }

def _get_meta_lens_metrics() -> Dict[str, Any]:
    """Get META_LENS_REPORT@1 observability metrics."""
    try:
        import os
        enabled = os.getenv("NOVA_ENABLE_META_LENS", "0").strip() == "1"

        if not enabled:
            return {
                "enabled": False,
                "status": "disabled",
                "reason": "NOVA_ENABLE_META_LENS not enabled"
            }

        # Try to import META_LENS modules
        try:
            import nova.slots.slot02_deltathresh.meta_lens_processor as mlp

            # Get runtime metrics if available
            last_epoch = getattr(mlp, "last_epoch", 0)
            last_residual = getattr(mlp, "last_residual", None)

            return {
                "enabled": True,
                "status": "operational",
                "contract": "META_LENS_REPORT@1",
                "last_epoch": last_epoch,
                "last_residual": last_residual,
                "max_iters": getattr(mlp, "MAX_ITERS", 3),
                "alpha": getattr(mlp, "ALPHA", 0.5),
                "epsilon": getattr(mlp, "EPSILON", 0.02),
                "convergence_model": "Damped fixed-point iteration"
            }
        except ImportError as e:
            return {
                "enabled": True,
                "status": "error",
                "error": str(e)
            }
    except Exception as e:
        return {
            "enabled": False,
            "status": "error",
            "error": str(e)
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

    # Get META_LENS metrics
    meta_lens_metrics = _get_meta_lens_metrics()

    # Get plugin system information
    plugin_info = _get_plugin_info()

    return {
        "service": "nova-config",
        "hot_reload_enabled": bool(getattr(mgr, "enable_hot_reload", False)),
        "hot_reload_mode": mode,   # "watchdog" | "polling" | "disabled"
        "slots_loaded": len(slots),
        "slots": slots,
        "slot6": slot6_metrics,  # Slot 6 observability
        "meta_lens": meta_lens_metrics,  # META_LENS_REPORT@1 status
        "plugins": plugin_info["plugins"],  # Plugin system status
        "contracts_available": plugin_info["contracts_available"],
        "slots_enabled": plugin_info["slots_enabled"],
        "plugin_system_status": plugin_info.get("status", "operational")
    }

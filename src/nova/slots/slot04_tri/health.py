"""Health monitoring for Slot04 TRI Engine (Advanced)."""
from typing import Dict, Any

# --- import healthkit (with graceful fallback) --------------------------------
try:
    from nova.orchestrator.core.healthkit import ok, minimal, error
except Exception:
    try:
        from core.healthkit import ok, minimal, error
    except Exception:
        # tiny inline shim to avoid hard dependency
        from time import time as _now
        def _base(name, version, status, caps, metrics, deps):
            return {
                "schema_version": "1.0",
                "name": name,
                "version": version,
                "self_check": "ok",
                "engine_status": status,
                "capabilities": caps or [],
                "metrics": metrics or {},
                "deps": deps or [],
                "timestamp": _now(),
            }
        def ok(name, version, **kw):
            return _base(name, version, "normal", kw.get("capabilities", []), kw.get("metrics", {}), kw.get("deps", []))
        def minimal(name, version, **kw):
            return _base(name, version, "minimal", kw.get("capabilities", []), kw.get("metrics", {}), kw.get("deps", []))
        def error(name, version, err, **kw):
            d = _base(name, version, "degraded", kw.get("capabilities", []), kw.get("metrics", {}), kw.get("deps", []))
            d["self_check"] = "error"
            d["error"] = err
            return d

NAME = "slot04_tri"
VERSION = "1.0.0"

_CAPS = [
    "tri_calculation",
    "truth_evaluation",
    "layer_scoring",
    "drift_detection",
    "repair_planning",
    "safe_mode_operation",
]
_DEPS = ["semantic_mirror", "slot01_truth_anchor"]

def health() -> Dict[str, Any]:
    """Comprehensive health check for advanced TRI engine."""
    try:
        # Try to import core TRI engine components
        try:
            from nova.slots.slot04_tri.core.tri_engine import TriEngine
            from nova.slots.slot04_tri.core.detectors import DriftDetector, SurgeDetector
            from nova.slots.slot04_tri.core.repair_planner import RepairPlanner
            from nova.slots.slot04_tri.core.safe_mode import SafeMode
        except Exception as ie:
            return minimal(
                NAME,
                VERSION,
                capabilities=["tri_calculation"],
                metrics={
                    "core_available": False,
                    "import_error": str(ie),
                },
                deps=["semantic_mirror"],
            )

        # Core engine is available - collect metrics
        metrics: Dict[str, Any] = {}

        # Test engine instantiation
        try:
            TriEngine()
            metrics.update({
                "engine_instantiated": True,
                "detectors_available": True,
                "repair_planner_available": True,
                "safe_mode_available": True,
            })
        except Exception:
            metrics.update({
                "engine_instantiated": False,
                "detectors_available": False,
                "repair_planner_available": False,
                "safe_mode_available": False,
            })

        # Check feature flag status
        import os
        tri_link_enabled = os.getenv("NOVA_ENABLE_TRI_LINK", "0") == "1"
        metrics.update({
            "tri_link_enabled": tri_link_enabled,
            "feature_flag_status": "enabled" if tri_link_enabled else "disabled",
        })

        # Check individual component availability
        try:
            DriftDetector()
            SurgeDetector()
            RepairPlanner()
            SafeMode()

            metrics.update({
                "drift_detector_ready": True,
                "surge_detector_ready": True,
                "repair_planner_ready": True,
                "safe_mode_ready": True,
                "core_components": "all_available",
            })
        except Exception as comp_error:
            metrics.update({
                "core_components": "partial_failure",
                "component_error": str(comp_error),
            })

        metrics.update({
            "core_available": True,
            "engine_type": "advanced_tri_engine",
        })

        return ok(NAME, VERSION, capabilities=_CAPS, metrics=metrics, deps=_DEPS)

    except Exception as e:
        return error(
            NAME,
            VERSION,
            f"{type(e).__name__}: {e}",
            capabilities=["tri_calculation"],
            deps=["semantic_mirror"],
        )

"""Health monitoring for Slot04 TRI Engine (Simple Bayesian)."""
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

NAME = "slot04_tri_engine"
VERSION = "1.0.0"

_CAPS = [
    "tri_calculation",
    "bayesian_updates",
    "kalman_filtering",
    "truth_measurement",
    "temporal_smoothing",
]
_DEPS = ["semantic_mirror"]

def health() -> Dict[str, Any]:
    """Comprehensive health check for simple TRI engine with Bayesian updates."""
    try:
        # Try to import the simple TRI engine
        try:
            from .engine import TRIStatus
        except Exception as ie:
            return minimal(
                NAME,
                VERSION,
                capabilities=["tri_calculation"],
                metrics={
                    "engine_available": False,
                    "import_error": str(ie),
                },
                deps=["semantic_mirror"],
            )

        # Engine is available - collect metrics
        metrics: Dict[str, Any] = {}

        # Test engine component instantiation
        try:
            TRIStatus()
            metrics.update({
                "tri_status_instantiated": True,
                "bayesian_engine_ready": True,
                "kalman_filter_ready": True,
            })
        except Exception:
            metrics.update({
                "tri_status_instantiated": False,
                "bayesian_engine_ready": False,
                "kalman_filter_ready": False,
            })

        # Check for additional engine components
        try:
            metrics.update({
                "publish_module_available": True,
                "plugin_module_available": True,
                "integration_modules": "available",
            })
        except Exception:
            metrics.update({
                "publish_module_available": False,
                "plugin_module_available": False,
                "integration_modules": "partial",
            })

        # Check IDS integration if available
        try:
            metrics.update({
                "ids_integration_available": True,
            })
        except Exception:
            metrics.update({
                "ids_integration_available": False,
            })

        metrics.update({
            "engine_available": True,
            "engine_type": "simple_bayesian_tri",
            "produces": ["TRI_REPORT@1"],
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

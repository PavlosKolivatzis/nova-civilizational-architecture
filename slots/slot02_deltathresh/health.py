"""Health monitoring for Slot02 ΔTHRESH Advanced Content Processing System."""
from typing import Dict, Any
import importlib.util

# --- import healthkit (with graceful fallback) --------------------------------
try:
    from orchestrator.core.healthkit import ok, minimal, error  # preferred
except Exception:
    try:
        from core.healthkit import ok, minimal, error  # alt location
    except Exception:
        # tiny inline shim to avoid hard dependency
        from time import time as _now
        def _base(name, version, status, caps, metrics, deps):
            return {
                "schema_version": "1.0",
                "name": name,
                "version": version,
                "self_check": "ok",
                "engine_status": status,  # normal|minimal|degraded
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

NAME = "slot02_deltathresh"
VERSION = "1.0.0"

_CAPS = [
    "threshold_management",
    "risk_screening",
    "guardrail_signals",
    "content_processing",
    "tri_scoring",
    "quarantine_management",
]
_DEPS = ["semantic_mirror", "slot04_tri", "slot06_cultural_synthesis", "slot10_civilizational_deployment"]

def health() -> Dict[str, Any]:
    """Comprehensive health check for ΔTHRESH processor with graceful fallback."""
    try:
        # Try the real core processor module first
        try:
            from slots.slot02_deltathresh.core import DeltaThreshProcessor
            from slots.slot02_deltathresh.config import ProcessingConfig
        except Exception as ie:
            # Adapter-only fallback path
            adapter_ok = False
            try:
                from orchestrator.adapters.slot2_deltathresh import AVAILABLE, ENGINE
                adapter_ok = bool(AVAILABLE and ENGINE)
            except Exception:
                pass
            return minimal(
                NAME,
                VERSION,
                capabilities=(["threshold_management"] if adapter_ok else ["basic_processing"]),
                metrics={
                    "processor_available": False,
                    "adapter_available": adapter_ok,
                    "import_error": str(ie),
                },
                deps=(["semantic_mirror"] if adapter_ok else []),
            )

        # Core processor module is importable — collect metrics
        metrics: Dict[str, Any] = {}

        # Probe instantiation
        instance = None
        try:
            config = ProcessingConfig()
            instance = DeltaThreshProcessor(config)
            metrics.update({
                "processor_version": instance.VERSION,
                "operational_mode": instance.config.operational_mode.value,
                "processing_mode": instance.config.processing_mode.value,
                "pattern_detection_enabled": instance.config.enable_pattern_detection,
                "performance_tracking_enabled": instance.config.performance_tracking,
                "anchor_system_available": instance.anchor_system is not None,
                "thread_safety": "RLock protection active",
            })
        except Exception:
            instance = None

        # Check performance tracker if available
        if instance and hasattr(instance, 'performance_tracker'):
            perf_tracker = instance.performance_tracker
            metrics.update({
                "performance_tracker_active": True,
                "total_requests_processed": getattr(perf_tracker, '_total_requests', 0),
                "average_processing_time_ms": getattr(perf_tracker, '_avg_processing_time', 0.0),
            })

        # Check pattern detector if available
        if instance and hasattr(instance, 'pattern_detector'):
            metrics.update({
                "pattern_detector_active": True,
                "pattern_detection_config": instance.config.enable_pattern_detection,
            })

        # Check enhanced processor availability
        spec = importlib.util.find_spec(
            "slots.slot02_deltathresh.enhanced.processor"
        )
        metrics["enhanced_processor_available"] = spec is not None

        metrics.update({
            "processor_available": True,
            "instance_probed": bool(instance is not None),
        })

        return ok(NAME, VERSION, capabilities=_CAPS, metrics=metrics, deps=_DEPS)

    except Exception as e:
        return error(
            NAME,
            VERSION,
            f"{type(e).__name__}: {e}",
            capabilities=["threshold_management"],
            deps=["semantic_mirror"],
        )
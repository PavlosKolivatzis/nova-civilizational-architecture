"""Health monitoring for Slot09 Distortion Protection (Hybrid v3.1.0)."""
from typing import Dict, Any, Optional
import threading

# --- import healthkit (with graceful fallback) --------------------------------
try:
    from orchestrator.core.healthkit import ok, minimal, error
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

NAME = "slot09_distortion_protection"
VERSION = "3.1.0-hybrid"

_HYBRID_PROBE_RESULT: Optional[Dict[str, Any]] = None
_HYBRID_PROBE_LOCK = threading.Lock()

_CAPS = [
    "distortion_detection",
    "reality_verification",
    "anomaly_protection",
    "hybrid_analysis",
    "phase_lock_integration",
    "ids_policy_enforcement",
    "shared_audit_hash",
    "coherence_analysis",
    "policy_adjustment",
    "infrastructure_awareness"
]
_DEPS = ["semantic_mirror", "slot07_production_controls", "ids_service"]

def health() -> Dict[str, Any]:
    """Comprehensive health check for hybrid distortion protection system."""
    try:
        # Try to import core distortion protection components
        try:
            from nova.slots.slot09_distortion_protection.hybrid_api import HybridDistortionDetectionAPI
            from nova.slots.slot09_distortion_protection.ids_policy import (
                get_phase_lock_context,
                apply_ids_policy
            )
        except Exception as ie:
            return minimal(
                NAME,
                VERSION,
                capabilities=["distortion_detection"],
                metrics={
                    "core_available": False,
                    "import_error": str(ie),
                },
                deps=["semantic_mirror"],
            )

        # Core components available - collect metrics
        metrics: Dict[str, Any] = {}

        # Test hybrid API instantiation (cached probe)
        metrics.update(_probe_hybrid_api(HybridDistortionDetectionAPI))

        # Check IDS integration
        try:
            import os
            from config.feature_flags import IDS_ENABLED
            ids_enabled = IDS_ENABLED
            metrics.update({
                "ids_integration": "enabled" if ids_enabled else "disabled",
                "ids_policy_available": True,
                "policy_enforcement_ready": ids_enabled,
            })
        except Exception:
            metrics.update({
                "ids_integration": "unavailable",
                "ids_policy_available": False,
                "policy_enforcement_ready": False,
            })

        # Test phase lock context
        try:
            phase_lock_context = get_phase_lock_context()
            metrics.update({
                "phase_lock_integration": "available" if phase_lock_context["available"] else "disabled",
                "phase_lock_coherence": phase_lock_context.get("coherence_level", "unknown"),
                "light_clock_integration": True,
            })
        except Exception as phase_error:
            metrics.update({
                "phase_lock_integration": "error",
                "light_clock_integration": False,
                "phase_lock_error": str(phase_error),
            })

        # Check shared hash feature flag
        try:
            import os
            shared_hash_enabled = os.getenv("NOVA_USE_SHARED_HASH", "0") == "1"
            metrics.update({
                "shared_hash_enabled": shared_hash_enabled,
                "shared_audit_hash_ready": shared_hash_enabled,
                "hash_method": "blake2b_with_fallback" if shared_hash_enabled else "sha256",
            })
        except Exception:
            metrics.update({
                "shared_hash_enabled": False,
                "shared_audit_hash_ready": False,
            })

        # Test policy functions
        try:
            # Test with mock analysis result
            test_analysis = {
                "stability": 0.8,
                "drift": 0.01,
                "state": "STABLE"
            }
            test_policy = apply_ids_policy(test_analysis)
            metrics.update({
                "policy_engine_functional": True,
                "policy_test_result": test_policy.get("policy", "unknown"),
                "coherence_adjustments": "active",
            })
        except Exception:
            metrics.update({
                "policy_engine_functional": False,
                "coherence_adjustments": "disabled",
            })

        # Check deep light-clock integration
        try:
            import os
            lightclock_deep = os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "1"
            metrics.update({
                "lightclock_deep_enabled": lightclock_deep,
                "infrastructure_awareness": "deep" if lightclock_deep else "basic",
            })
        except Exception:
            metrics.update({
                "lightclock_deep_enabled": False,
                "infrastructure_awareness": "disabled",
            })

        metrics.update({
            "core_available": True,
            "protection_type": "hybrid_distortion_detection_with_phase_lock",
            "analysis_engine": "infrastructure_aware",
            "policy_framework": "ids_integrated_with_coherence_adjustment",
        })

        return ok(NAME, VERSION, capabilities=_CAPS, metrics=metrics, deps=_DEPS)

    except Exception as e:
        return error(
            NAME,
            VERSION,
            f"{type(e).__name__}: {e}",
            capabilities=["distortion_detection"],
            deps=["semantic_mirror"],
        )


def _probe_hybrid_api(api_cls) -> Dict[str, Any]:
    """Instantiate the hybrid API once per process and reuse the result."""
    global _HYBRID_PROBE_RESULT
    with _HYBRID_PROBE_LOCK:
        if _HYBRID_PROBE_RESULT is None:
            try:
                api_cls()
                _HYBRID_PROBE_RESULT = {
                    "hybrid_api_available": True,
                    "distortion_detection_ready": True,
                    "api_version": "3.1.0-hybrid",
                }
            except Exception:
                _HYBRID_PROBE_RESULT = {
                    "hybrid_api_available": False,
                    "distortion_detection_ready": False,
                }
        return dict(_HYBRID_PROBE_RESULT)

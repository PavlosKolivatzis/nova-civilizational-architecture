# ruff: noqa: E402
from __future__ import annotations

import time

from .. import emotional_matrix_engine
from .. import escalation
from .. import advanced_policy
from .. import enhanced_engine

# Re-export primary classes so tests and callers can patch via this module
EmotionalMatrixEngine = emotional_matrix_engine.EmotionalMatrixEngine
EmotionalEscalationManager = escalation.EmotionalEscalationManager
AdvancedSafetyPolicy = advanced_policy.AdvancedSafetyPolicy
EnhancedEmotionalMatrixEngine = enhanced_engine.EnhancedEmotionalMatrixEngine


def health() -> dict:
    """
    Comprehensive health check for Slot 3 components:
    - base engine analysis
    - escalation manager
    - safety policy
    - enhanced engine
    """
    result = {
        "timestamp": time.time(),
        "self_check": "ok",
        "engine_status": "operational",
        "basic_analysis": "functional",
        "escalation_status": "operational",
        "safety_policy_status": "operational",
        "enhanced_engine_status": "operational",
        "overall_status": "fully_operational",
        "maturity_level": "4/4_processual",
    }

    analysis_result = None

    try:
        # Test base engine
        eng = emotional_matrix_engine.EmotionalMatrixEngine()
        analysis_result = eng.analyze("ok")
        result["engine_version"] = getattr(eng, "__version__", "unknown")

        # Check if analysis result is valid
        if analysis_result is None or not isinstance(analysis_result, dict):
            result["basic_analysis"] = "degraded"
        else:
            result["sample_analysis"] = {
                "tone": analysis_result.get("emotional_tone", "unknown"),
                "score": analysis_result.get("score", 0.0),
                "confidence": analysis_result.get("confidence", 0.0),
            }

    except Exception as e:
        result["self_check"] = "error"
        result["engine_status"] = "failed"
        result["overall_status"] = "critical_failure"
        result["maturity_level"] = "0/4_missing"
        result["error"] = type(e).__name__
        result["message"] = str(e)

        # Always attach provenance even in error case
        try:
            from nova.orchestrator.contracts.provenance import slot3_provenance

            result.update(slot3_provenance())
        except ImportError:
            # Fallback if provenance module not available
            result["schema_id"] = "https://github.com/PavlosKolivatzis/nova-civilizational-architecture/schemas/slot3_health_schema.json"
            result["schema_version"] = "1"

        return result

    # Test escalation manager
    try:
        escalation_mgr = escalation.EmotionalEscalationManager()
        _ = escalation_mgr.classify_threat(analysis_result or {})
        result["escalation_test"] = "passed"
    except Exception:
        result["escalation_status"] = "degraded"
        result["overall_status"] = "partially_operational"
        result["maturity_level"] = "2/4_relational"

    # Test safety policy
    try:
        safety_policy = advanced_policy.AdvancedSafetyPolicy()
        _ = safety_policy.validate(analysis_result, "test content")
        result["safety_test"] = "passed"
    except Exception:
        result["safety_policy_status"] = "degraded"
        if result["overall_status"] != "partially_operational":
            result["overall_status"] = "partially_operational"
            result["maturity_level"] = "2/4_relational"

    # Test enhanced engine
    try:
        enhanced_engine_instance = enhanced_engine.EnhancedEmotionalMatrixEngine()
        performance_metrics = enhanced_engine_instance.get_performance_metrics()
        result["performance_metrics"] = performance_metrics
    except Exception:
        result["enhanced_engine_status"] = "degraded"
        if result["overall_status"] == "fully_operational":
            result["overall_status"] = "partially_operational"
            result["maturity_level"] = "2/4_relational"

    # Always attach provenance
    try:
        from nova.orchestrator.contracts.provenance import slot3_provenance

        result.update(slot3_provenance())
    except ImportError:
        # Fallback if provenance module not available
        result["schema_id"] = "https://github.com/PavlosKolivatzis/nova-civilizational-architecture/schemas/slot3_health_schema.json"
        result["schema_version"] = "1"

    return result


def get_detailed_metrics() -> dict:
    """Get detailed operational metrics for monitoring."""
    try:
        metrics = {
            "timestamp": time.time(),
            "component_metrics": {},
        }

        # Escalation manager metrics
        try:
            escalation_mgr = escalation.EmotionalEscalationManager()
            escalation_summary = escalation_mgr.get_escalation_summary()
            metrics["component_metrics"]["escalation"] = escalation_summary
        except Exception:
            metrics["component_metrics"]["escalation"] = {"status": "unavailable"}

        # Safety policy metrics
        try:
            safety_policy = advanced_policy.AdvancedSafetyPolicy()
            policy_stats = safety_policy.get_policy_stats()
            metrics["component_metrics"]["safety_policy"] = policy_stats
        except Exception:
            metrics["component_metrics"]["safety_policy"] = {"status": "unavailable"}

        # Enhanced engine metrics
        try:
            enhanced_engine_instance = enhanced_engine.EnhancedEmotionalMatrixEngine()
            performance_metrics = enhanced_engine_instance.get_performance_metrics()
            metrics["component_metrics"]["enhanced_engine"] = performance_metrics
        except Exception:
            metrics["component_metrics"]["enhanced_engine"] = {"status": "unavailable"}

        return metrics

    except Exception as exc:
        return {
            "timestamp": time.time(),
            "error": str(exc),
            "status": "metrics_unavailable",
        }


__all__ = [
    "health",
    "get_detailed_metrics",
    "EmotionalMatrixEngine",
    "EmotionalEscalationManager",
    "AdvancedSafetyPolicy",
    "EnhancedEmotionalMatrixEngine",
]

"""Enhanced Health check for Slot 3 - Emotional Matrix."""
from __future__ import annotations

def health() -> dict:
    """
    Lightweight self-check:
    - import the engine
    - run a trivial analysis
    - return a stable structure for tests
    """
    try:
        from .emotional_matrix_engine import EmotionalMatrixEngine  # local import to avoid import cycles
        eng = EmotionalMatrixEngine()
        _ = eng.analyze("ok")  # smoke; ignore result
        return {
            "self_check": "ok",
            "engine_status": "operational",
            "engine_version": getattr(eng, "__version__", "unknown")
        }
    except Exception as e:
        # Tests only assert the "ok" case, but keep an explain for ops.
        return {"self_check": "error", "error": type(e).__name__, "message": str(e)}


def get_detailed_metrics() -> dict:
    """Get detailed operational metrics for monitoring."""
    try:
        metrics = {
            "timestamp": __import__('time').time(),
            "component_metrics": {}
        }
        
        # Escalation manager metrics
        try:
            from slots.slot03_emotional_matrix.escalation import EmotionalEscalationManager
            escalation_mgr = EmotionalEscalationManager()
            escalation_summary = escalation_mgr.get_escalation_summary()
            metrics["component_metrics"]["escalation"] = escalation_summary
        except Exception:
            metrics["component_metrics"]["escalation"] = {"status": "unavailable"}
        
        # Safety policy metrics  
        try:
            from slots.slot03_emotional_matrix.advanced_policy import AdvancedSafetyPolicy
            safety_policy = AdvancedSafetyPolicy()
            policy_stats = safety_policy.get_policy_stats()
            metrics["component_metrics"]["safety_policy"] = policy_stats
        except Exception:
            metrics["component_metrics"]["safety_policy"] = {"status": "unavailable"}
        
        # Enhanced engine metrics
        try:
            from slots.slot03_emotional_matrix.enhanced_engine import EnhancedEmotionalMatrixEngine
            enhanced_engine = EnhancedEmotionalMatrixEngine()
            performance_metrics = enhanced_engine.get_performance_metrics()
            metrics["component_metrics"]["enhanced_engine"] = performance_metrics
        except Exception:
            metrics["component_metrics"]["enhanced_engine"] = {"status": "unavailable"}
        
        return metrics
        
    except Exception as exc:
        return {
            "timestamp": __import__('time').time(),
            "error": str(exc),
            "status": "metrics_unavailable"
        }
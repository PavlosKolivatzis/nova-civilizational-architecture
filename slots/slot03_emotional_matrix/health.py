"""Enhanced Health check for Slot 3 - Emotional Matrix."""
import time
from typing import Dict, Any
from . import emotional_matrix_engine


def health() -> Dict[str, Any]:
    """Return comprehensive health status for the emotional matrix slot."""
    try:
        # Basic engine test
        engine = emotional_matrix_engine.EmotionalMatrixEngine()
        test_result = engine.analyze("I feel great today!")
        
        # Enhanced health check
        base_health = {
            "self_check": "ok",
            "engine_status": "operational",
            # Use getattr directly on the class object instead of treating it like a dict
            "version": getattr(
                emotional_matrix_engine.EmotionalMatrixEngine, "__version__", "0.3.0"
            ),
            "capabilities": ["emotional_analysis", "escalation", "advanced_safety"],
            "timestamp": time.time()
        }
        
        # Test basic functionality
        if test_result and "emotional_tone" in test_result:
            base_health["basic_analysis"] = "functional"
            base_health["sample_analysis"] = {
                "tone": test_result.get("emotional_tone"),
                "score": test_result.get("score"),
                "confidence": test_result.get("confidence")
            }
        else:
            base_health["basic_analysis"] = "degraded"
        
        # Test escalation components
        try:
            from .escalation import EmotionalEscalationManager, ThreatLevel
            escalation_mgr = EmotionalEscalationManager()
            threat_level = escalation_mgr.classify_threat(test_result or {})
            base_health["escalation_status"] = "operational"
            base_health["escalation_test"] = threat_level.value
        except Exception as exc:
            base_health["escalation_status"] = "degraded"
            base_health["escalation_error"] = str(exc)
        
        # Test advanced safety policy
        try:
            from .advanced_policy import AdvancedSafetyPolicy
            safety_policy = AdvancedSafetyPolicy()
            safety_result = safety_policy.validate(test_result or {}, "test content")
            base_health["safety_policy_status"] = "operational"
            base_health["safety_test"] = {
                "is_safe": safety_result.get("is_safe", False),
                "violations": len(safety_result.get("violations", []))
            }
        except Exception as exc:
            base_health["safety_policy_status"] = "degraded"
            base_health["safety_error"] = str(exc)
        
        # Test enhanced engine wrapper
        try:
            from .enhanced_engine import EnhancedEmotionalMatrixEngine
            enhanced_engine = EnhancedEmotionalMatrixEngine()
            enhanced_result = enhanced_engine.analyze("test")
            metrics = enhanced_engine.get_performance_metrics()
            base_health["enhanced_engine_status"] = "operational"
            base_health["performance_metrics"] = metrics
        except Exception as exc:
            base_health["enhanced_engine_status"] = "degraded"
            base_health["enhanced_error"] = str(exc)
        
        # Overall status assessment
        components = [
            base_health.get("basic_analysis") == "functional",
            base_health.get("escalation_status") == "operational",
            base_health.get("safety_policy_status") == "operational",
            base_health.get("enhanced_engine_status") == "operational"
        ]
        
        operational_count = sum(components)
        if operational_count == len(components):
            base_health["overall_status"] = "fully_operational"
            base_health["maturity_level"] = "4/4_processual"
        elif operational_count >= len(components) * 0.75:
            base_health["overall_status"] = "mostly_operational"
            base_health["maturity_level"] = "3/4_structural"
        elif operational_count >= len(components) * 0.5:
            base_health["overall_status"] = "partially_operational"
            base_health["maturity_level"] = "2/4_relational"
        else:
            base_health["overall_status"] = "degraded"
            base_health["maturity_level"] = "1/4_anchor"
        
        return base_health
        
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "self_check": "error", 
            "error": str(exc), 
            "engine_status": "failed",
            "overall_status": "critical_failure",
            "maturity_level": "0/4_missing",
            "timestamp": time.time()
        }


def get_detailed_metrics() -> Dict[str, Any]:
    """Get detailed operational metrics for monitoring."""
    try:
        metrics = {
            "timestamp": time.time(),
            "component_metrics": {}
        }
        
        # Escalation manager metrics
        try:
            from .escalation import EmotionalEscalationManager
            escalation_mgr = EmotionalEscalationManager()
            escalation_summary = escalation_mgr.get_escalation_summary()
            metrics["component_metrics"]["escalation"] = escalation_summary
        except Exception:
            metrics["component_metrics"]["escalation"] = {"status": "unavailable"}
        
        # Safety policy metrics  
        try:
            from .advanced_policy import AdvancedSafetyPolicy
            safety_policy = AdvancedSafetyPolicy()
            policy_stats = safety_policy.get_policy_stats()
            metrics["component_metrics"]["safety_policy"] = policy_stats
        except Exception:
            metrics["component_metrics"]["safety_policy"] = {"status": "unavailable"}
        
        # Enhanced engine metrics
        try:
            from .enhanced_engine import EnhancedEmotionalMatrixEngine
            enhanced_engine = EnhancedEmotionalMatrixEngine()
            performance_metrics = enhanced_engine.get_performance_metrics()
            metrics["component_metrics"]["enhanced_engine"] = performance_metrics
        except Exception:
            metrics["component_metrics"]["enhanced_engine"] = {"status": "unavailable"}
        
        return metrics
        
    except Exception as exc:
        return {
            "timestamp": time.time(),
            "error": str(exc),
            "status": "metrics_unavailable"
        }
# slots/slot03_emotional_matrix/health/__init__.py
"""Enhanced Health check for Slot 3 - Emotional Matrix."""
from __future__ import annotations
import time
from pathlib import Path
import json

# fallbacks, in case schema file cannot be read in CI
_DEFAULT_SCHEMA_ID = "urn:nova:contracts:slot3_health_schema@1"
_DEFAULT_SCHEMA_VERSION = "1"

def _load_slot3_schema_provenance():
    try:
        # adjust path if your repo layout differs
        schema_path = Path(__file__).resolve().parents[3] / "contracts" / "slot3_health_schema.json"
        with schema_path.open("r", encoding="utf-8") as f:
            doc = json.load(f)
        schema_id = doc.get("$id", _DEFAULT_SCHEMA_ID)
        # If you store schema version as a property or top-level field, pick accordingly:
        schema_version = (
            doc.get("schema_version")
            or doc.get("$version")
            or _DEFAULT_SCHEMA_VERSION
        )
        return schema_id, schema_version
    except Exception:
        return _DEFAULT_SCHEMA_ID, _DEFAULT_SCHEMA_VERSION

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
        "maturity_level": "4/4_processual"
    }
    
    try:
        # Test base engine
        from .emotional_matrix_engine import EmotionalMatrixEngine
        eng = EmotionalMatrixEngine()
        analysis_result = eng.analyze("ok")
        result["engine_version"] = getattr(eng, "__version__", "unknown")
        
        # Check if analysis result is valid
        if analysis_result is None or not isinstance(analysis_result, dict):
            result["basic_analysis"] = "degraded"
        else:
            result["sample_analysis"] = {
                "tone": analysis_result.get("emotional_tone", "unknown"),
                "score": analysis_result.get("score", 0.0),
                "confidence": analysis_result.get("confidence", 0.0)
            }
            
    except Exception as e:
        result["self_check"] = "error"
        result["engine_status"] = "failed"  
        result["overall_status"] = "critical_failure"
        result["maturity_level"] = "0/4_missing"
        result["error"] = type(e).__name__
        result["message"] = str(e)
        
        # Always attach provenance even in error case
        schema_id, schema_version = _load_slot3_schema_provenance()
        result["schema_id"] = schema_id
        result["schema_version"] = schema_version
        
        return result
    
    # Test escalation manager
    try:
        from slots.slot03_emotional_matrix.escalation import EmotionalEscalationManager
        escalation_mgr = EmotionalEscalationManager()
        from slots.slot03_emotional_matrix.escalation import ThreatLevel
        _ = escalation_mgr.classify_threat(analysis_result)
        result["escalation_test"] = "passed"
    except Exception:
        result["escalation_status"] = "degraded"
        result["overall_status"] = "partially_operational"
        result["maturity_level"] = "2/4_relational"
    
    # Test safety policy
    try:
        from slots.slot03_emotional_matrix.advanced_policy import AdvancedSafetyPolicy
        safety_policy = AdvancedSafetyPolicy()
        _ = safety_policy.validate(analysis_result, "test content")
        result["safety_test"] = "passed"
    except Exception:
        result["safety_policy_status"] = "degraded"
        if result["overall_status"] != "partially_operational":
            result["overall_status"] = "partially_operational"
            result["maturity_level"] = "2/4_relational"
    
    # Test enhanced engine
    try:
        from slots.slot03_emotional_matrix.enhanced_engine import EnhancedEmotionalMatrixEngine
        enhanced_engine = EnhancedEmotionalMatrixEngine()
        performance_metrics = enhanced_engine.get_performance_metrics()
        result["performance_metrics"] = performance_metrics
    except Exception:
        result["enhanced_engine_status"] = "degraded"
        if result["overall_status"] == "fully_operational":
            result["overall_status"] = "partially_operational"
            result["maturity_level"] = "2/4_relational"
    
    # Always attach provenance
    schema_id, schema_version = _load_slot3_schema_provenance()
    result["schema_id"] = schema_id
    result["schema_version"] = schema_version
    
    return result


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

__all__ = ["health", "get_detailed_metrics"]
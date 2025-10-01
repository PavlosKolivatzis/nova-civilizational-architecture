"""Shared health reporting library for standardized slot responses.

All Nova slots should use this library to ensure consistent health reporting
format across the entire system. Supports normal, minimal, degraded, and error states.
"""
from typing import Dict, List, Any, Optional
from time import time

_HEALTH_SCHEMA_VERSION = "1.0"

def _base(name: str, version: str, engine_status: str,
          capabilities: List[str], metrics: Dict[str, Any],
          deps: List[str]) -> Dict[str, Any]:
    """Base health response structure."""
    return {
        "schema_version": _HEALTH_SCHEMA_VERSION,
        "name": name,
        "version": version,
        "engine_status": engine_status,      # normal | minimal | degraded
        "capabilities": capabilities or [],
        "metrics": metrics or {},
        "deps": deps or [],
        "timestamp": time(),
    }

def ok(name: str, version: str, **kw) -> Dict[str, Any]:
    """Healthy slot with normal operation."""
    d = _base(name, version, "normal",
              kw.get("capabilities", []),
              kw.get("metrics", {}),
              kw.get("deps", []))
    d["self_check"] = "ok"
    return d

def minimal(name: str, version: str, **kw) -> Dict[str, Any]:
    """Functional slot with reduced capabilities."""
    d = _base(name, version, "minimal",
              kw.get("capabilities", []),
              kw.get("metrics", {}),
              kw.get("deps", []))
    d["self_check"] = "ok"
    return d

def degraded(name: str, version: str, **kw) -> Dict[str, Any]:
    """Operational slot with performance issues."""
    d = _base(name, version, "degraded",
              kw.get("capabilities", []),
              kw.get("metrics", {}),
              kw.get("deps", []))
    d["self_check"] = "ok"
    return d

def error(name: str, version: str, err: str, **kw) -> Dict[str, Any]:
    """Non-functional slot with error condition."""
    d = _base(name, version, "degraded",
              kw.get("capabilities", []),
              kw.get("metrics", {}),
              kw.get("deps", []))
    d["self_check"] = "error"
    d["error"] = err
    return d

def not_available(name: str, version: str, reason: str = "health module not found") -> Dict[str, Any]:
    """Slot health module not implemented or accessible."""
    return {
        "self_check": "n/a",
        "reason": reason,
        "name": name,
        "version": version,
        "timestamp": time(),
        "schema_version": _HEALTH_SCHEMA_VERSION,
    }

# Standard capability sets for common slot types
CAPABILITIES = {
    "truth_anchor": ["truth_verification", "reality_anchoring", "temporal_consistency"],
    "deltathresh": ["threshold_management", "risk_screening", "guardrail_signals"],
    "emotional": ["emotional_analysis", "tone_detection", "safety_screening"],
    "tri": ["outcome_prediction", "quality_assessment", "learning_optimization"],
    "constellation": ["pattern_mapping", "relationship_discovery", "network_analysis"],
    "cultural": ["cultural_synthesis", "principle_preservation", "adaptation_guidance"],
    "production": ["circuit_breaking", "rate_limiting", "resource_protection", "health_monitoring"],
    "memory": ["memory_management", "data_retention", "privacy_protection"],
    "distortion": ["distortion_detection", "reality_verification", "anomaly_protection"],
    "deployment": ["deployment_orchestration", "policy_enforcement", "rollout_management"],
}

# Standard dependency patterns
DEPS = {
    "semantic_mirror": "semantic_mirror",
    "truth_anchor": "slot01_truth_anchor",
    "tri": "slot04_tri",
    "production": "slot07_production_controls",
    "anr": "adaptive_neural_router",
}
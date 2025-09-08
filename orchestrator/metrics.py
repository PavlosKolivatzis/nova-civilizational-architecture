"""Centralized metrics for NOVA system components."""

import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class Slot6Metrics:
    """Thread-safe metrics collection for Slot 6 Cultural Synthesis."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._decisions = {"approved": 0, "transform": 0, "blocked": 0}
        self._legacy_calls = 0
        self._last_decision: Optional[Dict[str, Any]] = None
        
    def record_decision(self, result_name: str, pps: float, residual_risk: float, **metadata):
        """Record a cultural synthesis decision."""
        with self._lock:
            # Normalize result name for counting
            key = result_name.lower().replace("_", "").replace("-", "")
            if "approved" in key:
                self._decisions["approved"] += 1
            elif "transform" in key or "requires" in key:
                self._decisions["transform"] += 1
            elif "blocked" in key:
                self._decisions["blocked"] += 1
            
            # Store last decision details
            self._last_decision = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "result": result_name,
                "pps": round(pps, 3),
                "residual_risk": round(residual_risk, 3),
                "metadata": metadata
            }
    
    def record_legacy_call(self):
        """Record a legacy API usage."""
        with self._lock:
            self._legacy_calls += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        with self._lock:
            return {
                "version": "v7.4.1",
                "decisions_total": sum(self._decisions.values()),
                "decisions": dict(self._decisions),
                "legacy_calls_total": self._legacy_calls,
                "last_decision": dict(self._last_decision) if self._last_decision else None,
                "p95_residual_risk": None,  # TODO: Implement percentile tracking
            }
    
    def reset(self):
        """Reset all counters (for testing)."""
        with self._lock:
            self._decisions = {"approved": 0, "transform": 0, "blocked": 0}
            self._legacy_calls = 0
            self._last_decision = None


# Global instance
slot6_metrics = Slot6Metrics()


def get_slot6_metrics() -> Slot6Metrics:
    """Get the global Slot 6 metrics instance."""
    return slot6_metrics
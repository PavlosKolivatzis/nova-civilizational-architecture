"""
Slot 7 Production Controls - Prometheus Metrics Export

Exposes comprehensive production control metrics for system observability.
Integrates with existing ProductionControlEngine metrics collection.
"""
from __future__ import annotations
import time
import threading
from typing import Dict, Any, Optional
from collections import defaultdict
from .production_control_engine import ProductionControlEngine


class Slot7Metrics:
    """
    Prometheus-style metrics collector for Slot 7 Production Controls.
    
    Provides real-time visibility into circuit breaker state, request processing,
    safeguard violations, and reflex emission patterns.
    """
    
    def __init__(self, engine: Optional[ProductionControlEngine] = None):
        self.engine = engine or ProductionControlEngine()
        self.reflex_counters = defaultdict(int)
        self._lock = threading.Lock()
        self.collection_start_time = time.time()
        
        # Reflex emission tracking
        self.reflex_emission_history = []
        self.last_reflex_emission = {}
        
    def collect_core_metrics(self) -> Dict[str, Any]:
        """Collect core production control metrics from engine."""
        if not self.engine:
            return {}
            
        engine_metrics = self.engine.get_comprehensive_metrics()
        circuit_metrics = engine_metrics.get("circuit_breaker", {})
        
        # Map circuit breaker state to numeric values for Prometheus
        state_mapping = {"closed": 0, "open": 1, "half-open": 2}
        current_state = circuit_metrics.get("state", "closed")
        
        return {
            # Circuit breaker state and performance
            "slot7_breaker_state": state_mapping.get(current_state, 0),
            "slot7_breaker_failure_count": circuit_metrics.get("failure_count", 0),
            "slot7_breaker_success_count": circuit_metrics.get("success_count", 0),
            "slot7_breaker_failure_threshold": circuit_metrics.get("failure_threshold", 5),
            "slot7_breaker_reset_timeout_seconds": circuit_metrics.get("reset_timeout", 60),
            
            # Request processing metrics
            "slot7_requests_total": engine_metrics.get("total_requests", 0),
            "slot7_requests_successful": engine_metrics.get("successful_requests", 0),
            "slot7_requests_failed": engine_metrics.get("failed_requests", 0),
            "slot7_success_rate": engine_metrics.get("success_rate", 0.0),
            
            # Response time metrics (convert to milliseconds)
            "slot7_response_time_avg_ms": engine_metrics.get("avg_processing_time_ms", 0.0),
            "slot7_response_time_min_ms": engine_metrics.get("min_processing_time_ms", 0.0),
            "slot7_response_time_max_ms": engine_metrics.get("max_processing_time_ms", 0.0),
            
            # Safeguard violation counters
            "slot7_breaker_trips_total": engine_metrics.get("circuit_breaker_trips", 0),
            "slot7_rate_limit_violations_total": engine_metrics.get("rate_limit_violations", 0),
            "slot7_resource_limit_violations_total": engine_metrics.get("resource_limit_violations", 0),
            
            # Resource protection metrics
            "slot7_active_requests": engine_metrics.get("resource_protector", {}).get("active_requests", 0),
            "slot7_max_concurrent_requests": engine_metrics.get("resource_protector", {}).get("max_concurrent_requests", 0),
            
            # Rate limiter status
            "slot7_rate_limiter_tokens": engine_metrics.get("rate_limiter", {}).get("current_tokens", 0),
            "slot7_rate_limiter_requests_per_minute": engine_metrics.get("rate_limiter", {}).get("requests_per_minute", 0),
            
            # Operational metadata
            "slot7_engine_version": engine_metrics.get("engine_version", "2.0.0"),
            "slot7_monitoring_enabled": 1 if engine_metrics.get("monitoring_enabled", True) else 0,
            "slot7_uptime_seconds": time.time() - self.collection_start_time
        }
    
    def collect_reflex_metrics(self) -> Dict[str, Any]:
        """Collect reflex emission metrics with type breakdown."""
        with self._lock:
            reflex_metrics = {}
            
            # Per-type reflex emission counters
            for reflex_type, count in self.reflex_counters.items():
                reflex_metrics[f"slot7_reflex_emitted_total{{type=\"{reflex_type}\"}}"] = count
            
            # Total reflex emissions
            reflex_metrics["slot7_reflex_emitted_total"] = sum(self.reflex_counters.values())
            
            # Recent emission rate (last 5 minutes)
            recent_emissions = [
                emission for emission in self.reflex_emission_history
                if time.time() - emission["timestamp"] <= 300  # 5 minutes
            ]
            reflex_metrics["slot7_reflex_rate_recent_per_minute"] = len(recent_emissions) / 5.0
            
            # Blocked signal metrics for diagnostics
            try:
                from nova.slots.slot07_production_controls.reflex_emitter import get_reflex_emitter
                reflex_emitter = get_reflex_emitter()
                if hasattr(reflex_emitter, 'blocked_signals'):
                    for reason, count in reflex_emitter.blocked_signals.items():
                        reflex_metrics[f"slot7_reflex_blocked_total{{reason=\"{reason}\"}}"] = count
            except Exception:
                pass  # Graceful degradation if reflex emitter not available
            
            # Last emission timestamps by type
            for reflex_type, timestamp in self.last_reflex_emission.items():
                reflex_metrics[f"slot7_reflex_last_emission_timestamp{{type=\"{reflex_type}\"}}"] = timestamp
            
            return reflex_metrics
    
    def track_reflex_emission(self, reflex_type: str, cause: str, pressure_level: float = 0.0) -> None:
        """Track reflex emission for metrics collection."""
        current_time = time.time()
        
        with self._lock:
            # Increment type counter
            self.reflex_counters[reflex_type] += 1
            
            # Update last emission timestamp
            self.last_reflex_emission[reflex_type] = current_time
            
            # Add to emission history for rate calculation
            self.reflex_emission_history.append({
                "timestamp": current_time,
                "type": reflex_type,
                "cause": cause,
                "pressure": pressure_level
            })
            
            # Limit history size for memory management
            if len(self.reflex_emission_history) > 1000:
                self.reflex_emission_history = self.reflex_emission_history[-500:]
    
    def collect_all_metrics(self) -> Dict[str, Any]:
        """Collect complete metrics set for Prometheus export."""
        core_metrics = self.collect_core_metrics()
        reflex_metrics = self.collect_reflex_metrics()
        
        # Combine all metrics
        all_metrics = {**core_metrics, **reflex_metrics}
        
        # Add collection metadata
        all_metrics.update({
            "slot7_metrics_collection_timestamp": time.time(),
            "slot7_metrics_collection_duration_ms": 0.0  # Will be updated by collector
        })
        
        return all_metrics
    
    def get_prometheus_text(self) -> str:
        """Generate Prometheus text format for /metrics endpoint."""
        metrics = self.collect_all_metrics()
        lines = []
        
        # Circuit breaker metrics
        lines.extend([
            "# HELP slot7_breaker_state Circuit breaker state (0=closed, 1=open, 2=half-open)",
            "# TYPE slot7_breaker_state gauge",
            f"slot7_breaker_state {metrics.get('slot7_breaker_state', 0)}",
            "",
            "# HELP slot7_breaker_trips_total Total circuit breaker trips",
            "# TYPE slot7_breaker_trips_total counter", 
            f"slot7_breaker_trips_total {metrics.get('slot7_breaker_trips_total', 0)}",
            ""
        ])
        
        # Request processing metrics
        lines.extend([
            "# HELP slot7_requests_total Total requests processed",
            "# TYPE slot7_requests_total counter",
            f"slot7_requests_total {metrics.get('slot7_requests_total', 0)}",
            "",
            "# HELP slot7_requests_failed Total failed requests",
            "# TYPE slot7_requests_failed counter",
            f"slot7_requests_failed {metrics.get('slot7_requests_failed', 0)}",
            "",
            "# HELP slot7_response_time_avg_ms Average response time in milliseconds",
            "# TYPE slot7_response_time_avg_ms gauge",
            f"slot7_response_time_avg_ms {metrics.get('slot7_response_time_avg_ms', 0.0)}",
            ""
        ])
        
        # Safeguard violation metrics
        lines.extend([
            "# HELP slot7_rate_limit_violations_total Total rate limit violations",
            "# TYPE slot7_rate_limit_violations_total counter",
            f"slot7_rate_limit_violations_total {metrics.get('slot7_rate_limit_violations_total', 0)}",
            "",
            "# HELP slot7_resource_limit_violations_total Total resource limit violations", 
            "# TYPE slot7_resource_limit_violations_total counter",
            f"slot7_resource_limit_violations_total {metrics.get('slot7_resource_limit_violations_total', 0)}",
            ""
        ])
        
        # Reflex emission metrics
        lines.extend([
            "# HELP slot7_reflex_emitted_total Total reflex signals emitted by type",
            "# TYPE slot7_reflex_emitted_total counter"
        ])
        
        # Add per-type reflex metrics
        for key, value in metrics.items():
            if key.startswith("slot7_reflex_emitted_total{type="):
                lines.append(f"{key} {value}")
        
        lines.extend([
            "",
            "# HELP slot7_reflex_rate_recent_per_minute Recent reflex emission rate per minute",
            "# TYPE slot7_reflex_rate_recent_per_minute gauge",
            f"slot7_reflex_rate_recent_per_minute {metrics.get('slot7_reflex_rate_recent_per_minute', 0.0)}",
            "",
            "# HELP slot7_reflex_blocked_total Total blocked reflex signals by reason",
            "# TYPE slot7_reflex_blocked_total counter"
        ])
        
        # Add blocked signal metrics
        for key, value in metrics.items():
            if key.startswith("slot7_reflex_blocked_total{reason="):
                lines.append(f"{key} {value}")
        
        lines.append("")
        
        return '\n'.join(lines)
    
    def get_health_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary for health endpoint integration."""
        metrics = self.collect_all_metrics()
        
        # Determine health status based on metrics
        health_status = "healthy"
        health_issues = []
        
        if metrics.get("slot7_breaker_state", 0) == 1:  # open
            health_status = "degraded"
            health_issues.append("circuit_breaker_open")
        
        if metrics.get("slot7_success_rate", 1.0) < 0.9:
            health_status = "degraded"
            health_issues.append("low_success_rate")
        
        if metrics.get("slot7_rate_limit_violations_total", 0) > 0:
            health_issues.append("rate_limit_violations")
        
        return {
            "metrics_status": health_status,
            "metrics_issues": health_issues,
            "circuit_breaker_state": ["closed", "open", "half-open"][metrics.get("slot7_breaker_state", 0)],
            "total_requests": metrics.get("slot7_requests_total", 0),
            "success_rate": round(metrics.get("slot7_success_rate", 0.0), 3),
            "avg_response_time_ms": round(metrics.get("slot7_response_time_avg_ms", 0.0), 2),
            "reflex_emissions_total": metrics.get("slot7_reflex_emitted_total", 0),
            "reflex_rate_per_minute": round(metrics.get("slot7_reflex_rate_recent_per_minute", 0.0), 2),
            "last_collection": metrics.get("slot7_metrics_collection_timestamp", 0.0)
        }


# Global metrics instance for slot 7
slot7_metrics = None


def get_slot7_metrics(engine: Optional[ProductionControlEngine] = None) -> Slot7Metrics:
    """Get global Slot 7 metrics instance."""
    global slot7_metrics
    if slot7_metrics is None:
        slot7_metrics = Slot7Metrics(engine)
    return slot7_metrics


def reset_slot7_metrics() -> None:
    """Reset global metrics instance (for testing)."""
    global slot7_metrics
    slot7_metrics = None
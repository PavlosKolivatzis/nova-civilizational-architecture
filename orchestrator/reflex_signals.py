"""
Orchestrator Reflex Signals - Flow Fabric Phase 2

Extends Flow Fabric with reflex signal processing from Slot 7 Production Controls.
Coordinates adaptive responses across slots while maintaining system stability.
"""
from __future__ import annotations
import time
import logging
import threading
from collections import defaultdict, deque
from typing import Dict, Any, List, Callable
from dataclasses import dataclass

from .adaptive_connections import AdaptiveLink

logger = logging.getLogger(__name__)


@dataclass
class ReflexSignal:
    """Structured reflex signal from Slot 7"""
    signal_type: str
    source_slot: str
    pressure_level: float
    cause: str
    timestamp: float
    trace_id: str
    clamps: Dict[str, float]
    metadata: Dict[str, Any]


class ReflexBus:
    """
    Reflex signal bus for coordinating adaptive responses across slots.
    
    Receives reflex signals from production controls and modulates upstream
    AdaptiveLinks within safe bounds to prevent system oscillation.
    """
    
    def __init__(self):
        self.adaptive_links: Dict[str, AdaptiveLink] = {}
        self.signal_processors: Dict[str, Callable] = {}
        self.reflex_metrics = defaultdict(int)
        self._lock = threading.Lock()
        
        # Signal processing history for debugging
        self.signal_history = deque(maxlen=1000)
        
        # Initialize signal processors
        self._setup_signal_processors()
        
        logger.info("ReflexBus initialized")
    
    def register_adaptive_link(self, contract_name: str, link: AdaptiveLink) -> None:
        """Register an adaptive link for reflex modulation."""
        with self._lock:
            self.adaptive_links[contract_name] = link
            logger.info(f"Registered adaptive link for {contract_name}")
    
    def emit_reflex(self, reflex_signal: ReflexSignal) -> None:
        """
        Process reflex signal and adjust upstream connections.
        
        Args:
            reflex_signal: Structured reflex signal from production controls
        """
        current_time = time.time()
        
        with self._lock:
            # Track signal for metrics
            self.reflex_metrics[reflex_signal.signal_type] += 1
            self.signal_history.append({
                "timestamp": current_time,
                "signal": reflex_signal,
                "processing_result": None
            })
            
            # Process signal based on type
            processor = self.signal_processors.get(reflex_signal.signal_type)
            if processor:
                try:
                    result = processor(reflex_signal)
                    self.signal_history[-1]["processing_result"] = result
                    logger.debug(f"Processed {reflex_signal.signal_type} reflex: {result}")
                except Exception as e:
                    logger.error(f"Failed to process {reflex_signal.signal_type} reflex: {e}")
                    self.signal_history[-1]["processing_result"] = {"error": str(e)}
            else:
                logger.warning(f"No processor registered for signal type: {reflex_signal.signal_type}")
    
    def _setup_signal_processors(self) -> None:
        """Setup signal processors for different reflex types."""
        self.signal_processors = {
            "breaker_pressure": self._process_breaker_pressure,
            "memory_pressure": self._process_memory_pressure,
            "integrity_violation": self._process_integrity_violation
        }
    
    def _process_breaker_pressure(self, signal: ReflexSignal) -> Dict[str, Any]:
        """Process breaker pressure signal to throttle upstream emotional analysis."""
        results = {}
        
        # Primary target: S3→S6 EMOTION_REPORT@1
        emotion_link = self.adaptive_links.get("EMOTION_REPORT@1")
        if emotion_link:
            # Calculate frequency reduction based on pressure and clamps
            pressure = signal.pressure_level
            min_freq = signal.clamps.get("min_frequency_multiplier", 0.3)
            max_freq = signal.clamps.get("max_frequency_multiplier", 1.0)
            
            # Reduce frequency more as pressure increases
            target_frequency = max(min_freq, max_freq - (pressure * (max_freq - min_freq)))
            
            emotion_link.adjust_frequency(target_frequency, f"breaker_pressure:{signal.cause}")
            results["emotion_report_frequency"] = target_frequency
            
            # Optionally adjust weight for priority handling
            min_weight = signal.clamps.get("min_weight_multiplier", 0.5)
            max_weight = signal.clamps.get("max_weight_multiplier", 1.0)
            target_weight = max(min_weight, max_weight - (pressure * 0.3))  # Less aggressive weight reduction
            
            emotion_link.adjust_weight(target_weight, f"breaker_pressure:{signal.cause}")
            results["emotion_report_weight"] = target_weight
        
        # Secondary target: TRI_REPORT@1 (if registered)
        tri_link = self.adaptive_links.get("TRI_REPORT@1")
        if tri_link:
            # Less aggressive throttling for TRI reports
            pressure_factor = signal.pressure_level * 0.7  # Reduced impact
            min_freq = signal.clamps.get("min_frequency_multiplier", 0.5)
            target_frequency = max(min_freq, 1.0 - pressure_factor * 0.5)
            
            tri_link.adjust_frequency(target_frequency, f"breaker_pressure:{signal.cause}")
            results["tri_report_frequency"] = target_frequency
        
        return results
    
    def _process_memory_pressure(self, signal: ReflexSignal) -> Dict[str, Any]:
        """Process memory pressure signal to reduce resource-intensive operations."""
        results = {}
        
        # Target cultural synthesis operations which can be memory-intensive
        cultural_link = self.adaptive_links.get("CULTURAL_PROFILE@1")
        if cultural_link:
            pressure = signal.pressure_level
            min_freq = signal.clamps.get("min_frequency_multiplier", 0.2)
            
            # More aggressive throttling for memory pressure
            target_frequency = max(min_freq, 0.8 - (pressure * 0.6))
            
            cultural_link.adjust_frequency(target_frequency, f"memory_pressure:{signal.cause}")
            results["cultural_profile_frequency"] = target_frequency
        
        # Also throttle emotional analysis under high memory pressure
        emotion_link = self.adaptive_links.get("EMOTION_REPORT@1")
        if emotion_link and signal.pressure_level > 0.8:
            min_freq = signal.clamps.get("min_frequency_multiplier", 0.4)
            target_frequency = max(min_freq, 0.6)
            
            emotion_link.adjust_frequency(target_frequency, f"memory_pressure:{signal.cause}")
            results["emotion_report_frequency"] = target_frequency
        
        return results
    
    def _process_integrity_violation(self, signal: ReflexSignal) -> Dict[str, Any]:
        """Process integrity violation signal for security escalation."""
        results = {}
        
        # For integrity violations, we might want to boost weight (priority) rather than throttle
        severity = signal.pressure_level
        
        if severity > 0.8:  # High severity
            # Boost weight for security-sensitive operations
            for contract_name in ["EMOTION_REPORT@1", "CULTURAL_PROFILE@1"]:
                link = self.adaptive_links.get(contract_name)
                if link:
                    max_weight = signal.clamps.get("max_weight_multiplier", 2.0)
                    target_weight = min(max_weight, 1.0 + severity * 0.5)
                    
                    link.adjust_weight(target_weight, f"integrity_violation:{signal.cause}")
                    results[f"{contract_name.lower()}_weight"] = target_weight
            
            # Throttle frequency to reduce system load during security events
            min_freq = signal.clamps.get("min_frequency_multiplier", 0.1)
            target_frequency = max(min_freq, 0.5 - severity * 0.3)
            
            for contract_name in ["EMOTION_REPORT@1", "CULTURAL_PROFILE@1"]:
                link = self.adaptive_links.get(contract_name)
                if link:
                    link.adjust_frequency(target_frequency, f"integrity_violation:{signal.cause}")
                    results[f"{contract_name.lower()}_frequency"] = target_frequency
        
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get reflex bus metrics for monitoring."""
        with self._lock:
            return {
                "registered_links": list(self.adaptive_links.keys()),
                "reflex_signals_processed": dict(self.reflex_metrics),
                "total_signals_processed": sum(self.reflex_metrics.values()),
                "signal_history_size": len(self.signal_history),
                "active_processors": list(self.signal_processors.keys())
            }
    
    def get_recent_signals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent reflex signals for debugging."""
        with self._lock:
            return [
                {
                    "timestamp": entry["timestamp"],
                    "signal_type": entry["signal"].signal_type,
                    "pressure_level": entry["signal"].pressure_level,
                    "cause": entry["signal"].cause,
                    "trace_id": entry["signal"].trace_id,
                    "processing_result": entry.get("processing_result")
                }
                for entry in list(self.signal_history)[-limit:]
            ]


# Global reflex bus instance
_reflex_bus = None


def get_reflex_bus() -> ReflexBus:
    """Get global reflex bus instance."""
    global _reflex_bus
    if _reflex_bus is None:
        _reflex_bus = ReflexBus()
    return _reflex_bus


def setup_slot7_reflex_integration() -> None:
    """Setup integration between Slot 7 and reflex bus."""
    from .adaptive_connections import adaptive_link_registry
    from slots.slot07_production_controls.reflex_emitter import get_reflex_emitter
    
    # Get instances
    reflex_bus = get_reflex_bus()
    reflex_emitter = get_reflex_emitter()
    
    # Wire reflex emitter to bus
    reflex_emitter.reflex_bus = reflex_bus.emit_reflex
    
    # Register existing adaptive links with reflex bus
    for contract_name, link in adaptive_link_registry.links.items():
        reflex_bus.register_adaptive_link(contract_name, link)
    
    logger.info("Slot 7 reflex integration setup complete")


def reset_reflex_bus() -> None:
    """Reset global reflex bus (for testing)."""
    global _reflex_bus
    _reflex_bus = None
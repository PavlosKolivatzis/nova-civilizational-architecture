"""
Adaptive Connections - Flow Fabric Core Component

Provides AdaptiveLink wrapper for dynamic contract routing with weight/frequency adjustments.
Maintains contract payload immutability while enabling adaptive routing intelligence.
"""
from __future__ import annotations
import time
import logging
from collections import deque
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveLinkMetrics:
    """Metrics tracking for adaptive link behavior"""
    sends_total: int = 0
    sends_throttled: int = 0
    weight_adjustments: int = 0
    frequency_adjustments: int = 0
    average_response_time: float = 0.0
    last_adjustment_time: float = 0.0
    

@dataclass
class AdaptiveLinkConfig:
    """Configuration for adaptive link behavior"""
    base_weight: float = 1.0
    base_frequency: float = 1.0
    min_weight: float = 0.1
    max_weight: float = 3.0
    min_frequency: float = 0.1
    max_frequency: float = 5.0
    throttle_window_seconds: int = 60
    history_size: int = 100
    adaptation_enabled: bool = False  # Feature flag


class AdaptiveLink:
    """
    Adaptive wrapper around contract send operations.
    
    Provides dynamic weight/frequency adjustment without modifying contract semantics.
    Maintains full backward compatibility - works identically when adaptation disabled.
    """
    
    def __init__(self, contract_name: str, config: Optional[AdaptiveLinkConfig] = None):
        self.contract_name = contract_name
        self.config = config or AdaptiveLinkConfig()
        
        # Current adaptive parameters
        self.weight = self.config.base_weight
        self.frequency = self.config.base_frequency
        
        # Tracking and metrics
        self.metrics = AdaptiveLinkMetrics()
        self.send_history = deque(maxlen=self.config.history_size)
        self.last_send_time = 0.0
        
        logger.info(f"AdaptiveLink initialized for {contract_name}, adaptation_enabled={self.config.adaptation_enabled}")
    
    def send(self, payload: Dict[str, Any], original_send_func: Callable, **kwargs) -> Any:
        """
        Adaptive wrapper around contract send operation.
        
        Args:
            payload: Contract payload (never modified)
            original_send_func: Original contract send function
            **kwargs: Additional arguments for original function
            
        Returns:
            Result from original send function
        """
        current_time = time.time()
        
        # Track send attempt
        self.metrics.sends_total += 1
        
        # Apply frequency throttling (if adaptation enabled)
        if self.config.adaptation_enabled and self._should_throttle(current_time):
            self.metrics.sends_throttled += 1
            logger.debug(f"Throttling {self.contract_name} send, frequency={self.frequency}")
            return self._get_cached_result()
        
        # Apply weight-based priority (future: affects orchestrator routing)
        # Note: payload remains immutable, weight affects routing metadata only
        routing_metadata = self._build_routing_metadata()
        
        try:
            # Call original contract send function (unchanged semantics)
            start_time = time.time()
            result = original_send_func(payload, **kwargs)
            response_time = time.time() - start_time
            
            # Track successful send
            self._track_send(payload, result, response_time, current_time)
            
            return result
            
        except Exception as e:
            logger.error(f"AdaptiveLink send failed for {self.contract_name}: {e}")
            # Track failed send
            self._track_send(payload, None, 0.0, current_time, error=str(e))
            raise
    
    def adjust_weight(self, new_weight: float, reason: str = "") -> None:
        """Adjust link weight within configured bounds"""
        if not self.config.adaptation_enabled:
            logger.debug(f"Ignoring weight adjustment for {self.contract_name} - adaptation disabled")
            return
            
        old_weight = self.weight
        self.weight = max(self.config.min_weight, min(self.config.max_weight, new_weight))
        
        if abs(old_weight - self.weight) > 0.01:  # Only log significant changes
            self.metrics.weight_adjustments += 1
            self.metrics.last_adjustment_time = time.time()
            logger.info(f"AdaptiveLink {self.contract_name} weight: {old_weight:.2f} → {self.weight:.2f} ({reason})")
    
    def adjust_frequency(self, new_frequency: float, reason: str = "") -> None:
        """Adjust link frequency within configured bounds"""
        if not self.config.adaptation_enabled:
            logger.debug(f"Ignoring frequency adjustment for {self.contract_name} - adaptation disabled")
            return
            
        old_frequency = self.frequency
        self.frequency = max(self.config.min_frequency, min(self.config.max_frequency, new_frequency))
        
        if abs(old_frequency - self.frequency) > 0.01:  # Only log significant changes
            self.metrics.frequency_adjustments += 1
            self.metrics.last_adjustment_time = time.time()
            logger.info(f"AdaptiveLink {self.contract_name} frequency: {old_frequency:.2f} → {self.frequency:.2f} ({reason})")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current adaptive link metrics for monitoring"""
        return {
            "contract_name": self.contract_name,
            "current_weight": self.weight,
            "current_frequency": self.frequency,
            "sends_total": self.metrics.sends_total,
            "sends_throttled": self.metrics.sends_throttled,
            "weight_adjustments": self.metrics.weight_adjustments,
            "frequency_adjustments": self.metrics.frequency_adjustments,
            "average_response_time": self.metrics.average_response_time,
            "last_adjustment_time": self.metrics.last_adjustment_time,
            "adaptation_enabled": self.config.adaptation_enabled,
            "history_size": len(self.send_history)
        }
    
    def _should_throttle(self, current_time: float) -> bool:
        """Check if send should be throttled based on frequency"""
        if self.frequency >= 1.0:
            return False  # No throttling needed
            
        time_since_last = current_time - self.last_send_time
        required_interval = 1.0 / self.frequency
        
        return time_since_last < required_interval
    
    def _build_routing_metadata(self) -> Dict[str, Any]:
        """Build routing metadata based on current weight (future use)"""
        return {
            "adaptive_weight": self.weight,
            "adaptive_frequency": self.frequency,
            "contract_name": self.contract_name,
            "timestamp": time.time()
        }
    
    def _track_send(self, payload: Dict, result: Any, response_time: float, 
                    send_time: float, error: Optional[str] = None) -> None:
        """Track send for metrics and adaptation"""
        send_record = {
            "timestamp": send_time,
            "payload_hash": hash(str(sorted(payload.items()))),  # Immutable tracking
            "response_time": response_time,
            "success": error is None,
            "error": error,
            "weight": self.weight,
            "frequency": self.frequency
        }
        
        self.send_history.append(send_record)
        self.last_send_time = send_time
        
        # Update average response time (exponential moving average)
        if error is None and response_time > 0:
            alpha = 0.1  # EMA smoothing factor
            if self.metrics.average_response_time == 0:
                self.metrics.average_response_time = response_time
            else:
                self.metrics.average_response_time = (
                    alpha * response_time + (1 - alpha) * self.metrics.average_response_time
                )
    
    def _get_cached_result(self) -> Optional[Any]:
        """Get cached result for throttled sends (future: implement caching)"""
        # For now, return None - in future, could implement intelligent caching
        logger.debug(f"Returning None for throttled {self.contract_name} send")
        return None


class AdaptiveLinkRegistry:
    """Registry for managing adaptive links across the system"""
    
    def __init__(self):
        self.links: Dict[str, AdaptiveLink] = {}
        self.default_config = AdaptiveLinkConfig()
    
    def get_link(self, contract_name: str, config: Optional[AdaptiveLinkConfig] = None) -> AdaptiveLink:
        """Get or create adaptive link for contract"""
        if contract_name not in self.links:
            link_config = config or self.default_config
            self.links[contract_name] = AdaptiveLink(contract_name, link_config)
            logger.info(f"Created adaptive link for {contract_name}")
        
        return self.links[contract_name]
    
    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Get metrics for all registered links"""
        return [link.get_metrics() for link in self.links.values()]
    
    def set_global_adaptation_enabled(self, enabled: bool) -> None:
        """Enable/disable adaptation globally"""
        for link in self.links.values():
            link.config.adaptation_enabled = enabled
        logger.info(f"Global adaptation enabled: {enabled}")


# Global registry instance
adaptive_link_registry = AdaptiveLinkRegistry()
import time
import threading
import logging
import os
from collections import deque
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from config.feature_flags import get_production_controls_config
from .flag_metrics import get_flag_state_metrics

logger = logging.getLogger(__name__)


@dataclass
class ProcessingMetrics:
    """Metrics for tracking processing performance."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    circuit_breaker_trips: int = 0
    rate_limit_violations: int = 0
    resource_limit_violations: int = 0
    processing_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_failure_time: Optional[float] = None
    last_failure_reason: Optional[str] = None


class ProductionControlsCircuitBreaker:
    """Advanced circuit breaker for production controls with configurable safeguards."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config["circuit_breaker"]
        self.failure_threshold = self.config["failure_threshold"]
        self.error_threshold = self.config["error_threshold"] 
        self.reset_timeout = self.config["reset_timeout"]
        self.recovery_time = self.config["recovery_time"]
        
        self._state = "closed"  # closed, open, half-open
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
        self._opened_at: Optional[float] = None
        self._lock = threading.Lock()
        
    @property 
    def state(self) -> str:
        """Get current circuit breaker state with automatic transitions."""
        with self._lock:
            if self._state == "open" and self._opened_at is not None:
                if time.time() - self._opened_at >= self.reset_timeout:
                    self._state = "half-open"
                    # logger.info("Circuit breaker transitioning from open to half-open")
            return self._state
    
    @contextmanager
    def protect(self):
        """Context manager for circuit breaker protection."""
        if not self.config["enabled"]:
            yield
            return
            
        if self.state == "open":
            raise CircuitBreakerOpenError("Circuit breaker is open")
            
        start_time = time.time()
        try:
            yield
        except Exception as exc:
            self._record_failure(exc, time.time() - start_time)
            raise
        else:
            self._record_success(time.time() - start_time)
    
    def _record_failure(self, exception: Exception, duration: float):
        """Record a failure and update circuit breaker state."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self._state = "open"
                self._opened_at = time.time()
                # logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _record_success(self, duration: float):
        """Record a success and update circuit breaker state."""
        with self._lock:
            self.success_count += 1
            self.last_success_time = time.time()
            
            if self._state == "half-open":
                self._state = "closed"
                self.failure_count = 0
                # logger.info("Circuit breaker closed after successful request in half-open state")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "opened_at": self._opened_at,
            "reset_timeout": self.reset_timeout
        }


class RateLimiter:
    """Token bucket rate limiter with burst capacity."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config["rate_limiting"]
        self.requests_per_minute = self.config["requests_per_minute"]
        self.burst_size = self.config["burst_size"]
        
        self.tokens = self.burst_size
        self.last_update = time.time()
        self._lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed under rate limits."""
        if not self.config["enabled"]:
            return True
            
        with self._lock:
            now = time.time()
            
            # Add tokens based on time passed
            time_passed = now - self.last_update
            tokens_to_add = time_passed * (self.requests_per_minute / 60.0)
            self.tokens = min(self.burst_size, self.tokens + tokens_to_add)
            self.last_update = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiter metrics."""
        return {
            "current_tokens": self.tokens,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
            "enabled": self.config["enabled"]
        }


class ResourceProtector:
    """Resource protection with limits on payload size, processing time, and concurrency."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config["resource_protection"]
        self.max_payload_size_mb = self.config["max_payload_size_mb"]
        self.max_processing_time = self.config["max_processing_time_seconds"]
        self.max_concurrent_requests = self.config["max_concurrent_requests"]
        
        self.active_requests = 0
        self._lock = threading.Lock()
    
    def check_payload_size(self, payload: Dict[str, Any]) -> bool:
        """Check if payload size is within limits."""
        if not self.config["enabled"]:
            return True
            
        # Rough estimate of payload size
        payload_str = str(payload)
        size_mb = len(payload_str.encode('utf-8')) / (1024 * 1024)
        
        if size_mb > self.max_payload_size_mb:
            raise ResourceLimitExceededError(
                f"Payload size {size_mb:.2f}MB exceeds limit of {self.max_payload_size_mb}MB"
            )
        
        return True
    
    def check_concurrency(self) -> bool:
        """Check if concurrency limit allows new request."""
        if not self.config["enabled"]:
            return True
            
        with self._lock:
            if self.active_requests >= self.max_concurrent_requests:
                raise ResourceLimitExceededError(
                    f"Concurrent requests {self.active_requests} exceeds limit of {self.max_concurrent_requests}"
                )
            
            self.active_requests += 1
            return True
    
    def release_request(self):
        """Release a request slot."""
        if self.config["enabled"]:
            with self._lock:
                self.active_requests = max(0, self.active_requests - 1)
    
    @contextmanager
    def protect_processing_time(self):
        """Context manager for processing time protection."""
        start_time = time.time()
        try:
            yield
        finally:
            if self.config["enabled"]:
                processing_time = time.time() - start_time
                if processing_time > self.max_processing_time:
                    logger.warning(f"Processing time {processing_time:.2f}s exceeded limit of {self.max_processing_time}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get resource protector metrics."""
        return {
            "active_requests": self.active_requests,
            "max_concurrent_requests": self.max_concurrent_requests,
            "max_payload_size_mb": self.max_payload_size_mb,
            "max_processing_time_seconds": self.max_processing_time,
            "enabled": self.config["enabled"]
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class ResourceLimitExceededError(Exception):
    """Raised when resource limits are exceeded."""
    pass


class RateLimitExceededError(Exception):
    """Raised when rate limits are exceeded."""
    pass


class ProductionControlEngine:
    """Enhanced core engine for Slot 7 - Production Controls with circuit-breaker logic and safeguards."""

    __version__ = "2.0.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize production control engine with configurable safeguards."""
        self.config = config or get_production_controls_config()
        
        # Initialize components
        self.circuit_breaker = ProductionControlsCircuitBreaker(self.config)
        self.rate_limiter = RateLimiter(self.config)
        self.resource_protector = ResourceProtector(self.config)
        
        # Initialize metrics
        self.metrics = ProcessingMetrics()
        
        # Initialize monitoring
        self._monitoring_enabled = self.config["monitoring"]["metrics_collection_enabled"]
        self._alert_on_cb_trip = self.config["monitoring"]["alert_on_circuit_breaker_trip"]
        
        # Initialize failover settings
        self.failover_config = self.config["failover"]
        
        # Thread safety
        self._metrics_lock = threading.Lock()
        
        # Avoid potential logging issues during initialization
        # logger.info(f"ProductionControlEngine v{self.__version__} initialized")
    
    def process(self, payload: dict, operation_id: Optional[str] = None) -> dict:
        """Process payload through comprehensive production controls with circuit-breaker protection."""
        operation_id = operation_id or f"op_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # Pre-processing checks and protections
            self._pre_processing_checks(payload)
            
            # Main processing with circuit breaker protection
            with self.circuit_breaker.protect():
                with self.resource_protector.protect_processing_time():
                    result = self._core_processing(payload, operation_id)
            
            # Post-processing success handling
            processing_time = time.time() - start_time
            self._record_success_metrics(processing_time, operation_id)
            
            return {
                "status": "processed",
                "operation_id": operation_id,
                "processing_time_ms": round(processing_time * 1000, 2),
                "safeguards_active": self._get_active_safeguards(),
                "result": result,
                "timestamp": time.time()
            }
            
        except (CircuitBreakerOpenError, ResourceLimitExceededError, RateLimitExceededError) as e:
            # Handle safeguard violations
            processing_time = time.time() - start_time
            self._record_safeguard_violation(e, operation_id, processing_time)
            
            if self.failover_config["graceful_degradation_enabled"]:
                return self._graceful_degradation_response(payload, operation_id, str(e))
            else:
                raise
                
        except Exception as e:
            # Handle processing failures
            processing_time = time.time() - start_time
            self._record_failure_metrics(e, processing_time, operation_id)
            raise
            
        finally:
            # Always release request slot
            self.resource_protector.release_request()
    
    def _pre_processing_checks(self, payload: dict):
        """Perform all pre-processing safety checks."""
        # Rate limiting check
        if not self.rate_limiter.is_allowed():
            with self._metrics_lock:
                self.metrics.rate_limit_violations += 1
            raise RateLimitExceededError("Rate limit exceeded")
        
        # Resource protection checks
        self.resource_protector.check_payload_size(payload)
        self.resource_protector.check_concurrency()
    
    def _core_processing(self, payload: dict, operation_id: str) -> dict:
        """Core business logic processing - can be extended by subclasses."""
        # Simulate processing logic that could fail
        # Handle metrics action for observability
        action = (payload or {}).get("action")
        if action in {"get_metrics", "metrics"}:
            return {"metrics": self.get_comprehensive_metrics()}

        if payload.get("simulate_failure"):
            raise ValueError(f"Simulated failure for operation {operation_id}")
        
        # Basic processing
        result = {
            "processed_payload": payload,
            "operation_id": operation_id,
            "engine_version": self.__version__
        }
        
        # Add any additional processing logic here
        return result
    
    def _record_success_metrics(self, processing_time: float, operation_id: str):
        """Record metrics for successful processing."""
        if not self._monitoring_enabled:
            return
            
        with self._metrics_lock:
            self.metrics.total_requests += 1
            self.metrics.successful_requests += 1
            self.metrics.processing_times.append(processing_time)
        
        # logger.debug(f"Operation {operation_id} completed successfully in {processing_time:.3f}s")
    
    def _record_failure_metrics(self, exception: Exception, processing_time: float, operation_id: str):
        """Record metrics for failed processing."""
        if not self._monitoring_enabled:
            return
            
        with self._metrics_lock:
            self.metrics.total_requests += 1
            self.metrics.failed_requests += 1
            self.metrics.last_failure_time = time.time()
            self.metrics.last_failure_reason = str(exception)
            self.metrics.processing_times.append(processing_time)
        
        # logger.error(f"Operation {operation_id} failed after {processing_time:.3f}s: {exception}")
    
    def _record_safeguard_violation(self, exception: Exception, operation_id: str, processing_time: float):
        """Record metrics for safeguard violations."""
        if not self._monitoring_enabled:
            return
            
        with self._metrics_lock:
            self.metrics.total_requests += 1
            
            if isinstance(exception, CircuitBreakerOpenError):
                self.metrics.circuit_breaker_trips += 1
                if self._alert_on_cb_trip:
                    logger.critical(f"ALERT: Circuit breaker tripped for operation {operation_id}")
            elif isinstance(exception, RateLimitExceededError):
                self.metrics.rate_limit_violations += 1
            elif isinstance(exception, ResourceLimitExceededError):
                self.metrics.resource_limit_violations += 1
        
        logger.warning(f"Safeguard violation for operation {operation_id}: {exception}")
    
    def _graceful_degradation_response(self, payload: dict, operation_id: str, error_reason: str) -> dict:
        """Provide graceful degradation response when safeguards are triggered."""
        return {
            "status": "degraded",
            "operation_id": operation_id,
            "reason": error_reason,
            "degraded_result": {
                "acknowledged": True,
                "payload_received": bool(payload),
                "fallback_mode": True
            },
            "safeguards_active": self._get_active_safeguards(),
            "timestamp": time.time()
        }
    
    def _get_active_safeguards(self) -> List[str]:
        """Get list of currently active safeguards."""
        active = []
        
        if self.config["circuit_breaker"]["enabled"]:
            active.append(f"circuit_breaker({self.circuit_breaker.state})")
        if self.config["rate_limiting"]["enabled"]:
            active.append("rate_limiting")
        if self.config["resource_protection"]["enabled"]:
            active.append("resource_protection")
        if self.failover_config["enabled"]:
            active.append("failover")
        
        return active
    
    def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics from all components."""
        with self._metrics_lock:
            base_metrics = {
                "engine_version": self.__version__,
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "failed_requests": self.metrics.failed_requests,
                "success_rate": (
                    self.metrics.successful_requests / max(1, self.metrics.total_requests)
                ),
                "circuit_breaker_trips": self.metrics.circuit_breaker_trips,
                "rate_limit_violations": self.metrics.rate_limit_violations,
                "resource_limit_violations": self.metrics.resource_limit_violations,
                "last_failure_time": self.metrics.last_failure_time,
                "last_failure_reason": self.metrics.last_failure_reason,
            }
            
            if self.metrics.processing_times:
                times = list(self.metrics.processing_times)
                base_metrics.update({
                    "avg_processing_time_ms": round(sum(times) / len(times) * 1000, 2),
                    "min_processing_time_ms": round(min(times) * 1000, 2),
                    "max_processing_time_ms": round(max(times) * 1000, 2),
                })
        
        return {
            **base_metrics,
            "circuit_breaker": self.circuit_breaker.get_metrics(),
            "rate_limiter": self.rate_limiter.get_metrics(),
            "resource_protector": self.resource_protector.get_metrics(),
            "phase_lock": self.compute_phase_lock(),
            "safeguards_active": self._get_active_safeguards(),
            "config": self.config,
            "feature_flags": get_flag_state_metrics(),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        metrics = self.get_comprehensive_metrics()
        
        # Determine health status
        health_status = "healthy"
        health_issues = []
        
        if self.circuit_breaker.state == "open":
            health_status = "degraded"
            health_issues.append("circuit_breaker_open")
        
        if metrics["success_rate"] < 0.9 and metrics["total_requests"] > 10:
            health_status = "degraded" 
            health_issues.append("low_success_rate")
        
        if metrics["circuit_breaker_trips"] > 0:
            health_issues.append("circuit_breaker_trips_detected")
        
        if not health_issues:
            health_status = "healthy"
        
        return {
            "status": health_status,
            "issues": health_issues,
            "timestamp": time.time(),
            "metrics": metrics,
            "version": self.__version__,
            "phase_lock": metrics.get("phase_lock", 0.0),
        }
    

    def compute_phase_lock(self) -> float:
        """
        Phase-lock ∈ [0,1] derived from existing stats for Light-Clock integration.
        Formula: 0.7 * success_rate + 0.3 * (1.0 - pressure_level)
        """
        # Feature flag check
        if os.getenv("NOVA_LIGHTCLOCK_DEEP", "1") == "0":
            return 1.0

        with self._metrics_lock:
            success_rate = (
                self.metrics.successful_requests / max(1, self.metrics.total_requests)
                if self.metrics.total_requests > 0 else 1.0
            )

        # Calculate pressure from circuit breaker
        cb_metrics = self.circuit_breaker.get_metrics()
        pressure_level = min(1.0, cb_metrics.get("failure_count", 0) / max(1, cb_metrics.get("failure_threshold", 10)))

        # Phase lock formula
        phase_lock = max(0.0, min(1.0, 0.7 * success_rate + 0.3 * (1.0 - pressure_level)))
        return phase_lock

    def reset_circuit_breaker(self) -> bool:
        """Manually reset circuit breaker - use with caution."""
        try:
            with self.circuit_breaker._lock:
                self.circuit_breaker._state = "closed"
                self.circuit_breaker.failure_count = 0
                self.circuit_breaker._opened_at = None
                logger.warning("Circuit breaker manually reset")
            return True
        except Exception as e:
            logger.error(f"Failed to reset circuit breaker: {e}")
            return False
    
    def update_configuration(self, new_config: Dict[str, Any]) -> bool:
        """Update engine configuration at runtime."""
        try:
            # Validate configuration
            required_keys = ["circuit_breaker", "rate_limiting", "resource_protection", "monitoring", "failover"]
            for key in required_keys:
                if key not in new_config:
                    raise ValueError(f"Missing required configuration key: {key}")
            
            # Update configuration
            self.config.update(new_config)
            
            # Reinitialize components with new config
            self.circuit_breaker = ProductionControlsCircuitBreaker(self.config)
            self.rate_limiter = RateLimiter(self.config)
            self.resource_protector = ResourceProtector(self.config)
            
            logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False

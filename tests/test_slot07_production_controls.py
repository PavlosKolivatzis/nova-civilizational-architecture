"""Comprehensive tests for Slot 7 Production Controls with circuit-breaker logic and failover behavior."""
import pytest
import time
import threading
from unittest.mock import patch

from slots.slot07_production_controls.production_control_engine import (
    ProductionControlEngine,
    ProductionControlsCircuitBreaker,
    RateLimiter,
    ResourceProtector,
    CircuitBreakerOpenError,
    ResourceLimitExceededError
)
from config.feature_flags import get_production_controls_config


class TestProductionControlsCircuitBreaker:
    """Test the circuit breaker component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "circuit_breaker": {
                "enabled": True,
                "failure_threshold": 3,
                "error_threshold": 0.5,
                "reset_timeout": 0.1,  # Short timeout for testing
                "recovery_time": 60
            }
        }
        self.circuit_breaker = ProductionControlsCircuitBreaker(self.config)
    
    def test_initial_state(self):
        """Test circuit breaker initial state."""
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.failure_count == 0
        assert self.circuit_breaker.success_count == 0
    
    def test_successful_protection(self):
        """Test successful operation under circuit breaker protection."""
        with self.circuit_breaker.protect():
            pass  # Successful operation
        
        assert self.circuit_breaker.success_count == 1
        assert self.circuit_breaker.state == "closed"
    
    def test_failure_counting(self):
        """Test that failures are counted correctly."""
        for i in range(2):  # Less than threshold
            try:
                with self.circuit_breaker.protect():
                    raise ValueError(f"Test failure {i}")
            except ValueError:
                pass
        
        assert self.circuit_breaker.failure_count == 2
        assert self.circuit_breaker.state == "closed"  # Still closed
    
    def test_circuit_breaker_opens_after_threshold(self):
        """Test that circuit breaker opens after failure threshold."""
        for i in range(3):  # Equal to threshold
            try:
                with self.circuit_breaker.protect():
                    raise ValueError(f"Test failure {i}")
            except ValueError:
                pass
        
        assert self.circuit_breaker.failure_count == 3
        assert self.circuit_breaker.state == "open"
    
    def test_circuit_breaker_blocks_when_open(self):
        """Test that circuit breaker blocks requests when open."""
        # Trip the circuit breaker
        for i in range(3):
            try:
                with self.circuit_breaker.protect():
                    raise ValueError(f"Test failure {i}")
            except ValueError:
                pass
        
        # Should now block requests
        with pytest.raises(CircuitBreakerOpenError):
            with self.circuit_breaker.protect():
                pass
    
    def test_automatic_transition_to_half_open(self):
        """Test automatic transition from open to half-open state."""
        # Trip the circuit breaker
        for i in range(3):
            try:
                with self.circuit_breaker.protect():
                    raise ValueError(f"Test failure {i}")
            except ValueError:
                pass
        
        assert self.circuit_breaker.state == "open"
        
        # Wait for reset timeout
        time.sleep(0.15)  
        
        # Should transition to half-open
        assert self.circuit_breaker.state == "half-open"
    
    def test_half_open_to_closed_on_success(self):
        """Test transition from half-open to closed on success."""
        # Trip and wait for half-open
        for i in range(3):
            try:
                with self.circuit_breaker.protect():
                    raise ValueError(f"Test failure {i}")
            except ValueError:
                pass
        
        time.sleep(0.15)
        assert self.circuit_breaker.state == "half-open"
        
        # Successful operation should close circuit
        with self.circuit_breaker.protect():
            pass
        
        assert self.circuit_breaker.state == "closed"
        assert self.circuit_breaker.failure_count == 0
    
    def test_disabled_circuit_breaker(self):
        """Test that disabled circuit breaker allows all operations."""
        config = {
            "circuit_breaker": {
                "enabled": False,
                "failure_threshold": 1,
                "error_threshold": 0.1,
                "reset_timeout": 60.0,
                "recovery_time": 60
            }
        }
        cb = ProductionControlsCircuitBreaker(config)
        
        # Should allow operation even with failures
        for i in range(10):
            try:
                with cb.protect():
                    raise ValueError(f"Test failure {i}")
            except ValueError:
                pass
        
        # Circuit breaker should not trip when disabled
        with cb.protect():
            pass  # Should succeed


class TestRateLimiter:
    """Test the rate limiter component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 60,  # 1 per second
                "burst_size": 5
            }
        }
        self.rate_limiter = RateLimiter(self.config)
    
    def test_initial_tokens(self):
        """Test initial token count."""
        assert self.rate_limiter.tokens == self.rate_limiter.burst_size
    
    def test_token_consumption(self):
        """Test that tokens are consumed on requests."""
        initial_tokens = self.rate_limiter.tokens
        
        assert self.rate_limiter.is_allowed() is True
        assert self.rate_limiter.tokens == initial_tokens - 1
    
    def test_burst_capacity(self):
        """Test burst capacity handling."""
        # Consume all tokens
        for _ in range(self.config["rate_limiting"]["burst_size"]):
            assert self.rate_limiter.is_allowed() is True
        
        # Should be rate limited now
        assert self.rate_limiter.is_allowed() is False
    
    def test_token_replenishment(self):
        """Test token replenishment over time."""
        # Consume all tokens
        for _ in range(self.config["rate_limiting"]["burst_size"]):
            self.rate_limiter.is_allowed()
        
        assert self.rate_limiter.is_allowed() is False
        
        # Wait for token replenishment (1 second = 1 token at 60/min)
        time.sleep(1.1)
        
        assert self.rate_limiter.is_allowed() is True
    
    def test_disabled_rate_limiter(self):
        """Test disabled rate limiter allows all requests."""
        config = {
            "rate_limiting": {
                "enabled": False,
                "requests_per_minute": 1,
                "burst_size": 1
            }
        }
        rl = RateLimiter(config)
        
        # Should allow many requests when disabled
        for _ in range(100):
            assert rl.is_allowed() is True


class TestResourceProtector:
    """Test the resource protector component."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "resource_protection": {
                "enabled": True,
                "max_payload_size_mb": 1,
                "max_processing_time_seconds": 2,
                "max_concurrent_requests": 3
            }
        }
        self.resource_protector = ResourceProtector(self.config)
    
    def test_payload_size_check_valid(self):
        """Test valid payload size passes check."""
        small_payload = {"data": "small"}
        assert self.resource_protector.check_payload_size(small_payload) is True
    
    def test_payload_size_check_invalid(self):
        """Test oversized payload fails check."""
        large_payload = {"data": "x" * (1024 * 1024 + 1000)}  # >1MB
        
        with pytest.raises(ResourceLimitExceededError):
            self.resource_protector.check_payload_size(large_payload)
    
    def test_concurrency_limit_enforcement(self):
        """Test concurrency limit enforcement."""
        # Should allow up to max concurrent requests
        for i in range(self.config["resource_protection"]["max_concurrent_requests"]):
            assert self.resource_protector.check_concurrency() is True
        
        # Should reject the next one
        with pytest.raises(ResourceLimitExceededError):
            self.resource_protector.check_concurrency()
    
    def test_request_release(self):
        """Test request slot release."""
        # Fill up slots
        for _ in range(self.config["resource_protection"]["max_concurrent_requests"]):
            self.resource_protector.check_concurrency()
        
        # Release one slot
        self.resource_protector.release_request()
        
        # Should be able to acquire again
        assert self.resource_protector.check_concurrency() is True
    
    def test_processing_time_monitoring(self):
        """Test processing time monitoring."""
        with self.resource_protector.protect_processing_time():
            time.sleep(0.1)  # Short processing time
        
        # Should complete without issues (monitoring only warns)
        assert True
    
    def test_disabled_resource_protection(self):
        """Test disabled resource protection allows everything."""
        config = {
            "resource_protection": {
                "enabled": False,
                "max_payload_size_mb": 0.001,  # Tiny limit
                "max_processing_time_seconds": 0.001,  # Tiny limit
                "max_concurrent_requests": 1  # Tiny limit
            }
        }
        rp = ResourceProtector(config)
        
        # Should allow large payload when disabled
        large_payload = {"data": "x" * (1024 * 1024)}
        assert rp.check_payload_size(large_payload) is True
        
        # Should allow many concurrent requests when disabled
        for _ in range(100):
            assert rp.check_concurrency() is True


class TestProductionControlEngine:
    """Test the main production control engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use lenient config for most tests to avoid interference
        self.config = {
            "enabled": True,
            "circuit_breaker": {
                "enabled": True,
                "failure_threshold": 5,
                "error_threshold": 0.5,
                "reset_timeout": 0.1,
                "recovery_time": 60,
            },
            "rate_limiting": {
                "enabled": False,  # Disable to avoid test interference
                "requests_per_minute": 1000,
                "burst_size": 100,
            },
            "resource_protection": {
                "enabled": False,  # Disable to avoid test interference
                "max_payload_size_mb": 100,
                "max_processing_time_seconds": 10,
                "max_concurrent_requests": 100,
            },
            "monitoring": {
                "health_check_enabled": True,
                "health_check_interval": 10,
                "metrics_collection_enabled": True,
                "alert_on_circuit_breaker_trip": True,
            },
            "failover": {
                "enabled": True,
                "backup_mode_enabled": False,
                "graceful_degradation_enabled": True,
            }
        }
        self.engine = ProductionControlEngine(self.config)
    
    def test_engine_initialization(self):
        """Test engine initializes correctly."""
        assert self.engine.__version__ == "2.0.0"
        assert self.engine.config == self.config
        assert isinstance(self.engine.circuit_breaker, ProductionControlsCircuitBreaker)
        assert isinstance(self.engine.rate_limiter, RateLimiter)
        assert isinstance(self.engine.resource_protector, ResourceProtector)
    
    def test_basic_processing_success(self):
        """Test basic successful processing."""
        payload = {"test": "data"}
        result = self.engine.process(payload)
        
        assert result["status"] == "processed"
        assert "operation_id" in result
        assert "processing_time_ms" in result
        assert "safeguards_active" in result
        assert "result" in result
        assert result["result"]["processed_payload"] == payload
    
    def test_processing_with_operation_id(self):
        """Test processing with custom operation ID."""
        payload = {"test": "data"}
        operation_id = "custom_op_123"
        result = self.engine.process(payload, operation_id)
        
        assert result["operation_id"] == operation_id
    
    def test_simulated_failure(self):
        """Test handling of simulated failures."""
        payload = {"simulate_failure": True}
        
        with pytest.raises(ValueError):
            self.engine.process(payload)
        
        # Check metrics were updated
        assert self.engine.metrics.failed_requests > 0
        assert self.engine.metrics.total_requests > 0
    
    def test_circuit_breaker_integration(self):
        """Test circuit breaker integration with main engine."""
        # Configure with low threshold for testing
        test_config = self.config.copy()
        test_config["circuit_breaker"]["failure_threshold"] = 2
        engine = ProductionControlEngine(test_config)
        
        # Cause failures to trip circuit breaker
        for i in range(2):
            try:
                engine.process({"simulate_failure": True})
            except ValueError:
                pass
        
        # Circuit breaker should be open now
        assert engine.circuit_breaker.state == "open"
        
        # Next request should return degraded response (graceful degradation enabled)
        result = engine.process({"test": "data"})
        assert result["status"] == "degraded"
        assert "Circuit breaker is open" in result["reason"]
    
    def test_graceful_degradation(self):
        """Test graceful degradation when circuit breaker trips."""
        # Configure with low threshold and graceful degradation
        test_config = self.config.copy()
        test_config["circuit_breaker"]["failure_threshold"] = 2
        test_config["failover"]["graceful_degradation_enabled"] = True
        engine = ProductionControlEngine(test_config)
        
        # Trip circuit breaker
        for i in range(2):
            try:
                engine.process({"simulate_failure": True})
            except ValueError:
                pass
        
        # Request should return degraded response instead of failing
        result = engine.process({"test": "data"})
        
        assert result["status"] == "degraded"
        assert "reason" in result
        assert "degraded_result" in result
        assert result["degraded_result"]["fallback_mode"] is True
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration."""
        # Enable rate limiting with very low limits
        test_config = self.config.copy()
        test_config["rate_limiting"]["enabled"] = True
        test_config["rate_limiting"]["requests_per_minute"] = 60
        test_config["rate_limiting"]["burst_size"] = 2
        engine = ProductionControlEngine(test_config)
        
        # Should allow burst requests
        for i in range(2):
            result = engine.process({"test": f"data_{i}"})
            assert result["status"] == "processed"
        
        # Should trigger rate limiting with graceful degradation
        result = engine.process({"test": "rate_limited"})
        assert result["status"] == "degraded"
        assert "Rate limit exceeded" in result["reason"]
    
    def test_resource_protection_integration(self):
        """Test resource protection integration."""
        # Enable resource protection with low limits
        test_config = self.config.copy()
        test_config["resource_protection"]["enabled"] = True
        test_config["resource_protection"]["max_payload_size_mb"] = 0.001  # Very small
        test_config["resource_protection"]["max_concurrent_requests"] = 1
        engine = ProductionControlEngine(test_config)
        
        # Should trigger payload size limit with graceful degradation
        large_payload = {"data": "x" * 10000}  # Too large
        result = engine.process(large_payload)
        
        assert result["status"] == "degraded"
        assert "Payload size" in result["reason"]
    
    def test_comprehensive_metrics(self):
        """Test comprehensive metrics collection."""
        payload = {"test": "data"}
        
        # Process some successful requests
        for _ in range(3):
            self.engine.process(payload)
        
        # Process some failed requests
        for _ in range(2):
            try:
                self.engine.process({"simulate_failure": True})
            except ValueError:
                pass
        
        metrics = self.engine.get_comprehensive_metrics()
        
        assert metrics["total_requests"] == 5
        assert metrics["successful_requests"] == 3
        assert metrics["failed_requests"] == 2
        assert abs(metrics["success_rate"] - 0.6) < 0.01
        assert "circuit_breaker" in metrics
        assert "rate_limiter" in metrics
        assert "resource_protector" in metrics
        assert "safeguards_active" in metrics
    
    def test_health_check(self):
        """Test health check functionality."""
        health = self.engine.health_check()
        
        assert health["status"] in ["healthy", "degraded"]
        assert "issues" in health
        assert "timestamp" in health
        assert "metrics" in health
        assert health["version"] == self.engine.__version__
    
    def test_circuit_breaker_manual_reset(self):
        """Test manual circuit breaker reset."""
        # Trip circuit breaker
        test_config = self.config.copy()
        test_config["circuit_breaker"]["failure_threshold"] = 1
        engine = ProductionControlEngine(test_config)
        
        try:
            engine.process({"simulate_failure": True})
        except ValueError:
            pass
        
        assert engine.circuit_breaker.state == "open"
        
        # Reset circuit breaker
        success = engine.reset_circuit_breaker()
        assert success is True
        assert engine.circuit_breaker.state == "closed"
    
    def test_configuration_update(self):
        """Test runtime configuration updates."""
        new_config = self.config.copy()
        new_config["circuit_breaker"]["failure_threshold"] = 10
        
        success = self.engine.update_configuration(new_config)
        assert success is True
        assert self.engine.circuit_breaker.failure_threshold == 10
    
    def test_configuration_update_validation(self):
        """Test configuration update validation."""
        invalid_config = {"invalid": "config"}
        
        success = self.engine.update_configuration(invalid_config)
        assert success is False
    
    def test_concurrent_processing(self):
        """Test concurrent request processing."""
        results = []
        exceptions = []
        
        def process_request(payload):
            try:
                result = self.engine.process(payload)
                results.append(result)
            except Exception as e:
                exceptions.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(10):
            payload = {"test": f"concurrent_{i}"}
            thread = threading.Thread(target=process_request, args=(payload,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have processed most/all requests successfully
        assert len(results) >= 8  # Allow for some potential issues
        assert all(r["status"] in ["processed", "degraded"] for r in results)
    
    def test_failover_behavior_without_graceful_degradation(self):
        """Test failover behavior when graceful degradation is disabled."""
        test_config = self.config.copy()
        test_config["circuit_breaker"]["failure_threshold"] = 1
        test_config["failover"]["graceful_degradation_enabled"] = False
        engine = ProductionControlEngine(test_config)
        
        # Trip circuit breaker
        try:
            engine.process({"simulate_failure": True})
        except ValueError:
            pass
        
        # Should raise exception instead of graceful degradation
        with pytest.raises(CircuitBreakerOpenError):
            engine.process({"test": "data"})


class TestProductionControlsFeatureFlags:
    """Test production controls feature flag integration."""
    
    def test_default_configuration_loading(self):
        """Test loading default configuration from feature flags."""
        engine = ProductionControlEngine()  # Use defaults
        
        # Should have loaded configuration from feature flags
        assert engine.config is not None
        assert "circuit_breaker" in engine.config
        assert "rate_limiting" in engine.config
        assert "resource_protection" in engine.config
        assert "monitoring" in engine.config
        assert "failover" in engine.config
    
    @patch.dict('os.environ', {
        'CIRCUIT_BREAKER_FAILURE_THRESHOLD': '10',
        'RATE_LIMIT_REQUESTS_PER_MINUTE': '200',
        'MAX_PAYLOAD_SIZE_MB': '50'
    })
    def test_feature_flag_override(self):
        """Test that environment variables override default feature flags."""
        # Reload configuration with environment overrides
        from importlib import reload
        from config import feature_flags
        reload(feature_flags)
        
        config = feature_flags.get_production_controls_config()
        
        assert config["circuit_breaker"]["failure_threshold"] == 10
        assert config["rate_limiting"]["requests_per_minute"] == 200
        assert config["resource_protection"]["max_payload_size_mb"] == 50
    
    def test_configuration_completeness(self):
        """Test that configuration contains all required sections."""
        config = get_production_controls_config()
        
        required_sections = [
            "circuit_breaker", "rate_limiting", "resource_protection", 
            "monitoring", "failover"
        ]
        
        for section in required_sections:
            assert section in config, f"Missing configuration section: {section}"
        
        # Test circuit breaker section completeness
        cb_config = config["circuit_breaker"]
        required_cb_keys = [
            "enabled", "failure_threshold", "error_threshold", 
            "reset_timeout", "recovery_time"
        ]
        
        for key in required_cb_keys:
            assert key in cb_config, f"Missing circuit breaker config key: {key}"


class TestIntegrationScenarios:
    """Integration tests for real-world scenarios."""
    
    def test_high_load_scenario(self):
        """Test behavior under high load conditions."""
        config = get_production_controls_config()
        config["circuit_breaker"]["failure_threshold"] = 10
        config["rate_limiting"]["enabled"] = False  # Disable for load test
        config["resource_protection"]["enabled"] = False
        
        engine = ProductionControlEngine(config)
        
        # Process many requests quickly
        successful = 0
        failed = 0
        
        for i in range(100):
            try:
                if i % 10 == 0:  # Inject some failures
                    engine.process({"simulate_failure": True})
                else:
                    result = engine.process({"load_test": f"request_{i}"})
                    if result["status"] == "processed":
                        successful += 1
                    else:
                        failed += 1
            except Exception:
                failed += 1
        
        # Should handle load reasonably well
        assert successful > 70  # At least 70% success rate
        
        metrics = engine.get_comprehensive_metrics()
        assert metrics["total_requests"] == 100
    
    def test_cascading_failure_scenario(self):
        """Test behavior during cascading failures."""
        config = get_production_controls_config()
        config["circuit_breaker"]["failure_threshold"] = 3
        config["failover"]["graceful_degradation_enabled"] = True
        
        engine = ProductionControlEngine(config)
        
        # Simulate increasing failure rate
        results = []
        
        # Initial successful requests
        for i in range(5):
            result = engine.process({"test": f"success_{i}"})
            results.append(result)
        
        # Introduce failures to trip circuit breaker
        for i in range(3):
            try:
                engine.process({"simulate_failure": True})
            except ValueError:
                pass
        
        # Subsequent requests should be handled gracefully
        for i in range(5):
            result = engine.process({"test": f"after_trip_{i}"})
            results.append(result)
        
        # Should have mix of processed and degraded responses
        processed_count = sum(1 for r in results if r["status"] == "processed")
        degraded_count = sum(1 for r in results if r["status"] == "degraded")
        
        assert processed_count >= 5  # Initial successful requests
        assert degraded_count >= 5   # Post-trip degraded responses
    
    def test_recovery_scenario(self):
        """Test system recovery after circuit breaker trip."""
        config = get_production_controls_config()
        config["circuit_breaker"]["failure_threshold"] = 2
        config["circuit_breaker"]["reset_timeout"] = 0.1
        
        engine = ProductionControlEngine(config)
        
        # Trip circuit breaker
        for i in range(2):
            try:
                engine.process({"simulate_failure": True})
            except ValueError:
                pass
        
        assert engine.circuit_breaker.state == "open"
        
        # Wait for automatic recovery
        time.sleep(0.15)
        
        assert engine.circuit_breaker.state == "half-open"
        
        # Successful request should close circuit
        result = engine.process({"recovery": "test"})
        assert result["status"] == "processed"
        assert engine.circuit_breaker.state == "closed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
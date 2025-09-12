"""
Tests for Flow Fabric Phase 3: Semantic Mirror Integration

Validates context sharing, access control, contextual decision making,
and cross-slot coordination while maintaining slot autonomy.
"""
import pytest
import time
import threading
from unittest.mock import Mock, patch

from orchestrator.semantic_mirror import (
    SemanticMirror, ContextScope, ContextEntry, get_semantic_mirror, reset_semantic_mirror
)
from slots.slot07_production_controls.context_publisher import (
    ProductionControlContextPublisher, get_context_publisher, reset_context_publisher
)
from slots.slot06_cultural_synthesis.context_aware_synthesis import (
    ContextAwareCulturalSynthesis, get_context_aware_synthesis, reset_context_aware_synthesis
)


class TestSemanticMirrorCore:
    """Test core Semantic Mirror functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_semantic_mirror()
        self.mirror = SemanticMirror(max_entries=100, cleanup_interval_seconds=1.0)
        
        # Configure test access rules
        test_rules = {
            "slot07.breaker_state": ["slot06_cultural_synthesis", "slot03_emotional_matrix"],
            "slot06.cultural_profile": ["slot07_production_controls"],
            "test.private_data": [],  # No external access
        }
        self.mirror.configure_access_rules(test_rules)
    
    def test_context_publication_and_retrieval(self):
        """Test basic context publication and retrieval."""
        # Publish context
        success = self.mirror.publish_context(
            "slot07.breaker_state", 
            "open",
            "slot07_production_controls",
            ContextScope.INTERNAL
        )
        assert success is True
        
        # Retrieve context with authorized slot
        value = self.mirror.get_context("slot07.breaker_state", "slot06_cultural_synthesis")
        assert value == "open"
        
        # Check access tracking
        metrics = self.mirror.get_metrics()
        assert metrics["publications_total"] == 1
        assert metrics["queries_successful"] == 1
    
    def test_access_control_enforcement(self):
        """Test that access control prevents unauthorized access."""
        # Publish context
        self.mirror.publish_context(
            "slot07.breaker_state",
            "closed", 
            "slot07_production_controls",
            ContextScope.INTERNAL
        )
        
        # Authorized access should work
        value = self.mirror.get_context("slot07.breaker_state", "slot06_cultural_synthesis")
        assert value == "closed"
        
        # Unauthorized access should fail
        value = self.mirror.get_context("slot07.breaker_state", "unauthorized_slot")
        assert value is None
        
        # Check metrics
        metrics = self.mirror.get_metrics()
        assert metrics["queries_access_denied"] == 1
    
    def test_ttl_expiration(self):
        """Test that contexts expire based on TTL."""
        # Publish with short TTL
        self.mirror.publish_context(
            "slot07.test_data",
            {"value": 123},
            "slot07_production_controls",
            ContextScope.INTERNAL,
            ttl_seconds=0.1  # Very short TTL
        )
        
        # Immediate access should work
        value = self.mirror.get_context("slot07.test_data", "slot06_cultural_synthesis")
        assert value == {"value": 123}
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Access should now fail due to expiration
        value = self.mirror.get_context("slot07.test_data", "slot06_cultural_synthesis")
        assert value is None
        
        # Check metrics
        metrics = self.mirror.get_metrics()
        assert metrics["queries_expired"] == 1
    
    def test_rate_limiting(self):
        """Test query rate limiting per slot."""
        # Set very low rate limit for testing
        self.mirror.max_queries_per_minute = 2
        
        # Publish test context
        self.mirror.publish_context("slot07.rate_test", "data", "slot07_production_controls")
        
        # First two queries should succeed
        assert self.mirror.get_context("slot07.rate_test", "slot06_cultural_synthesis") == "data"
        assert self.mirror.get_context("slot07.rate_test", "slot06_cultural_synthesis") == "data"
        
        # Third query should be rate limited
        result = self.mirror.get_context("slot07.rate_test", "slot06_cultural_synthesis")
        assert result is None
        
        # Check metrics
        metrics = self.mirror.get_metrics()
        assert metrics["queries_rate_limited"] == 1
    
    def test_thread_safety(self):
        """Test that Semantic Mirror is thread-safe."""
        results = []
        errors = []
        
        def publish_worker(thread_id):
            try:
                for i in range(10):
                    success = self.mirror.publish_context(
                        f"test.thread_{thread_id}_{i}",
                        f"value_{thread_id}_{i}",
                        f"slot{thread_id:02d}",
                        ContextScope.INTERNAL
                    )
                    results.append(success)
            except Exception as e:
                errors.append(e)
        
        def query_worker(thread_id):
            try:
                for i in range(5):
                    keys = self.mirror.query_context_keys("test.", f"slot{thread_id:02d}")
                    results.append(len(keys))
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            t1 = threading.Thread(target=publish_worker, args=(i,))
            t2 = threading.Thread(target=query_worker, args=(i,))
            threads.extend([t1, t2])
        
        # Start all threads
        for t in threads:
            t.start()
        
        # Wait for completion
        for t in threads:
            t.join()
        
        # Check results
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len([r for r in results if r is True]) > 0  # Some publications succeeded
        
        # Check final metrics
        metrics = self.mirror.get_metrics()
        assert metrics["publications_total"] > 0
    
    def test_context_key_validation(self):
        """Test context key format validation."""
        # Valid keys should work
        valid_keys = [
            "slot07.breaker_state",
            "slot06.cultural_profile", 
            "test.multi_part.key.name"
        ]
        
        for key in valid_keys:
            success = self.mirror.publish_context(key, "test", "test_slot")
            assert success is True, f"Valid key rejected: {key}"
        
        # Invalid keys should fail
        invalid_keys = [
            "invalid",           # Single part
            "slot07.",           # Trailing dot
            ".slot07.test",      # Leading dot
            "slot-07.test",      # Invalid characters
        ]
        
        for key in invalid_keys:
            success = self.mirror.publish_context(key, "test", "test_slot")
            assert success is False, f"Invalid key accepted: {key}"


class TestProductionControlContextPublisher:
    """Test Slot 7 context publishing functionality."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_semantic_mirror()
        reset_context_publisher()
        
        # Mock production control engine
        self.mock_engine = Mock()
        self.mock_engine.circuit_breaker = Mock()
        self.mock_engine.circuit_breaker.state = "closed"
        self.mock_engine.circuit_breaker.last_failure_time = None
        
        self.mock_engine.get_comprehensive_metrics.return_value = {
            "success_rate": 0.95,
            "active_requests": 5,
            "max_concurrent_requests": 50,
            "rate_limit_violations": 0,
            "safeguards_active": ["circuit_breaker(closed)", "rate_limiting"]
        }
        
        self.mock_engine.health_check.return_value = {
            "status": "healthy",
            "issues": []
        }
        
        self.publisher = ProductionControlContextPublisher(self.mock_engine, publish_interval_seconds=0.1)
    
    def test_context_publication(self):
        """Test that production control context is published correctly."""
        # Mock reflex emitter
        with patch('slots.slot07_production_controls.context_publisher.get_reflex_emitter') as mock_reflex:
            mock_reflex.return_value.get_metrics.return_value = {
                "signals_emitted_by_type": {"breaker_pressure": 2}
            }
            
            # Publish context
            success = self.publisher.publish_context(force=True)
            assert success is True
            
            # Verify context was published
            mirror = get_semantic_mirror()
            breaker_state = mirror.get_context("slot07.breaker_state", "slot06_cultural_synthesis")
            assert breaker_state == "closed"
            
            pressure_level = mirror.get_context("slot07.pressure_level", "slot06_cultural_synthesis")
            assert isinstance(pressure_level, float)
            assert 0.0 <= pressure_level <= 1.0
            
            resource_status = mirror.get_context("slot07.resource_status", "slot06_cultural_synthesis")
            assert resource_status is not None
            assert "utilization" in resource_status
            assert "active_requests" in resource_status
    
    def test_pressure_calculation(self):
        """Test system pressure level calculation."""
        # Test normal conditions
        normal_metrics = {
            "success_rate": 0.95,
            "active_requests": 10,
            "max_concurrent_requests": 50,
            "rate_limit_violations": 0
        }
        self.mock_engine.get_comprehensive_metrics.return_value = normal_metrics
        
        context = self.publisher._gather_context_data()
        assert context.pressure_level < 0.5  # Should be low pressure
        
        # Test high resource utilization
        high_load_metrics = {
            "success_rate": 0.95,
            "active_requests": 45,  # 90% utilization
            "max_concurrent_requests": 50,
            "rate_limit_violations": 0
        }
        self.mock_engine.get_comprehensive_metrics.return_value = high_load_metrics
        
        context = self.publisher._gather_context_data()
        assert context.pressure_level > 0.7  # Should be high pressure
    
    def test_circuit_breaker_state_impact(self):
        """Test that circuit breaker state affects pressure calculation."""
        base_metrics = {
            "success_rate": 0.95,
            "active_requests": 5,
            "max_concurrent_requests": 50,
            "rate_limit_violations": 0
        }
        self.mock_engine.get_comprehensive_metrics.return_value = base_metrics
        
        # Test open circuit breaker
        self.mock_engine.circuit_breaker.state = "open"
        context = self.publisher._gather_context_data()
        assert context.pressure_level >= 0.7  # Open breaker should cause high pressure
        
        # Test half-open circuit breaker
        self.mock_engine.circuit_breaker.state = "half-open"
        context = self.publisher._gather_context_data()
        assert 0.4 <= context.pressure_level <= 0.8  # Moderate pressure


class TestContextAwareCulturalSynthesis:
    """Test Slot 6 context-aware cultural synthesis."""
    
    def setup_method(self):
        """Setup for each test."""
        reset_semantic_mirror()
        reset_context_aware_synthesis()
        
        # Setup semantic mirror with test data
        self.mirror = get_semantic_mirror()
        
        # Mock base engine
        self.mock_base_engine = Mock()
        self.mock_base_engine.synthesize.return_value = {
            "principle_preservation_score": 0.8,
            "cultural_fit": 0.75,
            "adaptation_rate": 0.6,
            "complexity_factor": 1.0,
            "synthesis_mode": "standard"
        }
        
        self.synthesis = ContextAwareCulturalSynthesis(self.mock_base_engine)
    
    def test_context_aware_synthesis_normal_conditions(self):
        """Test synthesis with normal system conditions."""
        # Publish normal system context
        self.mirror.publish_context("slot07.breaker_state", "closed", "slot07_production_controls")
        self.mirror.publish_context("slot07.pressure_level", 0.2, "slot07_production_controls")  # Low pressure
        
        # Perform synthesis
        cultural_profile = {"institution": "TestOrg", "region": "EU"}
        results = self.synthesis.synthesize_with_context(cultural_profile, {})
        
        # Should use base results with minimal adaptations
        assert results["complexity_factor"] == 1.0  # No reduction for low pressure
        assert results["synthesis_mode"] == "standard"
        assert results["_context"]["system_pressure"] == 0.2
        assert len(results["_context"]["adaptations_applied"]) == 0
    
    def test_high_pressure_adaptations(self):
        """Test synthesis adaptations under high system pressure."""
        # Publish high pressure system context
        self.mirror.publish_context("slot07.breaker_state", "closed", "slot07_production_controls")
        self.mirror.publish_context("slot07.pressure_level", 0.85, "slot07_production_controls")  # High pressure
        
        # Perform synthesis
        cultural_profile = {"institution": "TestOrg"}
        results = self.synthesis.synthesize_with_context(cultural_profile, {})
        
        # Should apply complexity reduction
        assert results["complexity_factor"] < 1.0
        assert "complexity_reduction_high" in results["_context"]["adaptations_applied"]
        assert "cultural_nuance_depth" in results
        assert results["cultural_nuance_depth"] == "simplified"
    
    def test_circuit_breaker_open_adaptations(self):
        """Test synthesis adaptations when circuit breaker is open."""
        # Publish circuit breaker open context
        self.mirror.publish_context("slot07.breaker_state", "open", "slot07_production_controls")
        self.mirror.publish_context("slot07.pressure_level", 0.9, "slot07_production_controls")
        
        health_summary = {"overall_status": "degraded"}
        self.mirror.publish_context("slot07.health_summary", health_summary, "slot07_production_controls")
        
        # Perform synthesis
        results = self.synthesis.synthesize_with_context({"institution": "TestOrg"}, {})
        
        # Should apply conservative adaptations
        assert results["synthesis_mode"] == "conservative"
        assert results["risk_tolerance"] == "low"
        assert results["adaptation_rate"] <= 0.3
        assert "circuit_breaker_conservative" in results["_context"]["adaptations_applied"]
    
    def test_resource_optimization_adaptations(self):
        """Test synthesis adaptations for resource optimization."""
        # Publish high resource utilization
        resource_status = {
            "utilization": 0.8,  # High utilization
            "active_requests": 40,
            "success_rate": 0.9
        }
        self.mirror.publish_context("slot07.breaker_state", "closed", "slot07_production_controls")
        self.mirror.publish_context("slot07.pressure_level", 0.3, "slot07_production_controls")  
        self.mirror.publish_context("slot07.resource_status", resource_status, "slot07_production_controls")
        
        # Perform synthesis
        results = self.synthesis.synthesize_with_context({"institution": "TestOrg"}, {})
        
        # Should apply resource optimizations
        assert results["computational_complexity"] == "optimized"
        assert results["caching_strategy"] == "aggressive"
        assert "resource_optimization" in results["_context"]["adaptations_applied"]
    
    def test_fallback_without_context(self):
        """Test synthesis fallback when context is not available."""
        # Don't publish any context - should use fallback
        results = self.synthesis.synthesize_with_context({"institution": "TestOrg"}, {})
        
        # Should work without context
        assert results["_context"]["context_available"] is False
        assert results["_context"]["system_pressure"] is None
        assert len(results["_context"]["adaptations_applied"]) == 0
        
        # Base synthesis should still work
        assert "principle_preservation_score" in results
        assert "cultural_fit" in results
    
    def test_context_caching(self):
        """Test that system context is cached appropriately."""
        # Publish initial context
        self.mirror.publish_context("slot07.pressure_level", 0.5, "slot07_production_controls")
        
        # First synthesis should fetch context
        results1 = self.synthesis.synthesize_with_context({"institution": "Test1"}, {})
        first_timestamp = results1["_context"]["context_timestamp"]
        
        # Second synthesis (within cache TTL) should use cached context
        results2 = self.synthesis.synthesize_with_context({"institution": "Test2"}, {})
        second_timestamp = results2["_context"]["context_timestamp"]
        
        # Should use the same cached context
        assert first_timestamp == second_timestamp
        
        # Update context and wait for cache to expire
        self.synthesis.context_cache_ttl = 0.01  # Very short cache
        time.sleep(0.02)
        self.mirror.publish_context("slot07.pressure_level", 0.8, "slot07_production_controls")
        
        # Third synthesis should fetch fresh context
        results3 = self.synthesis.synthesize_with_context({"institution": "Test3"}, {})
        third_timestamp = results3["_context"]["context_timestamp"]
        
        assert third_timestamp > second_timestamp


@pytest.mark.integration
class TestFullSemanticMirrorIntegration:
    """Integration tests for complete Semantic Mirror flow."""
    
    def setup_method(self):
        """Setup for integration test."""
        reset_semantic_mirror()
        reset_context_publisher()
        reset_context_aware_synthesis()
    
    def test_end_to_end_context_flow(self):
        """Test complete context flow from Slot 7 to Slot 6."""
        # Setup mock production engine
        mock_engine = Mock()
        mock_engine.circuit_breaker = Mock()
        mock_engine.circuit_breaker.state = "half-open"
        mock_engine.circuit_breaker.last_failure_time = time.time()
        
        mock_engine.get_comprehensive_metrics.return_value = {
            "success_rate": 0.85,
            "active_requests": 25,
            "max_concurrent_requests": 50,
            "rate_limit_violations": 1,
            "safeguards_active": ["circuit_breaker(half-open)", "rate_limiting"]
        }
        
        mock_engine.health_check.return_value = {
            "status": "degraded",
            "issues": ["circuit_breaker_half_open"]
        }
        
        # Setup Slot 7 context publisher
        publisher = ProductionControlContextPublisher(mock_engine)
        
        # Mock reflex emitter
        with patch('slots.slot07_production_controls.context_publisher.get_reflex_emitter') as mock_reflex:
            mock_reflex.return_value.get_metrics.return_value = {
                "signals_emitted_by_type": {"breaker_pressure": 3}
            }
            
            # Publish Slot 7 context
            success = publisher.publish_context(force=True)
            assert success is True
        
        # Setup Slot 6 context-aware synthesis
        mock_base_engine = Mock()
        mock_base_engine.synthesize.return_value = {
            "principle_preservation_score": 0.8,
            "cultural_fit": 0.75,
            "adaptation_rate": 0.7,
            "synthesis_mode": "standard"
        }
        
        synthesis = ContextAwareCulturalSynthesis(mock_base_engine)
        
        # Perform context-aware synthesis
        cultural_profile = {"institution": "TestOrg", "region": "NA"}
        results = synthesis.synthesize_with_context(cultural_profile, {})
        
        # Verify cross-slot context flow worked
        assert results["_context"]["context_available"] is True
        assert results["_context"]["system_pressure"] > 0.0
        
        # Should apply recovery adaptations due to half-open breaker
        assert "recovery_cautious" in results["_context"]["adaptations_applied"]
        assert results["synthesis_mode"] == "cautious"
        assert results["adaptation_rate"] <= 0.6  # Reduced due to recovery mode
        
        # Verify Slot 6 publishes its context back
        publish_success = synthesis.publish_synthesis_context(results)
        assert publish_success is True
        
        # Verify other slots could read Slot 6 context
        mirror = get_semantic_mirror()
        cultural_context = mirror.get_context("slot06.cultural_profile", "slot07_production_controls")
        assert cultural_context is not None
        assert "adaptation_rate" in cultural_context
        assert "synthesis_mode" in cultural_context
    
    def test_context_isolation_and_access_control(self):
        """Test that context isolation and access control work across slots."""
        mirror = get_semantic_mirror()
        
        # Slot 7 publishes context
        mirror.publish_context("slot07.internal_state", "sensitive_data", "slot07_production_controls", ContextScope.PRIVATE)
        mirror.publish_context("slot07.public_metrics", {"requests": 100}, "slot07_production_controls", ContextScope.INTERNAL)
        
        # Slot 6 publishes context
        mirror.publish_context("slot06.synthesis_results", {"score": 0.8}, "slot06_cultural_synthesis", ContextScope.INTERNAL)
        
        # Test authorized access
        assert mirror.get_context("slot07.public_metrics", "slot06_cultural_synthesis") is not None
        assert mirror.get_context("slot06.synthesis_results", "slot07_production_controls") is not None
        
        # Test access control enforcement
        assert mirror.get_context("slot07.internal_state", "slot06_cultural_synthesis") is None  # Private context
        assert mirror.get_context("slot07.public_metrics", "unauthorized_slot") is None  # Unauthorized slot
        
        # Test self-access always works
        assert mirror.get_context("slot07.internal_state", "slot07_production_controls") == "sensitive_data"
        
        # Verify metrics track access patterns
        metrics = mirror.get_metrics()
        assert metrics["queries_successful"] > 0
        assert metrics["queries_access_denied"] > 0
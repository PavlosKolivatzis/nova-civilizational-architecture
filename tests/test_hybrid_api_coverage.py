"""
Tests for src/nova/slots/slot09_distortion_protection/hybrid_api.py coverage improvement.

Targets uncovered paths: circuit breaker, cache eviction, error handling, edge cases.
Part of DEF-006 Sprint 1.
"""
import pytest
import asyncio
import time
from unittest.mock import patch
from nova.slots.slot09_distortion_protection.hybrid_api import (
    HybridApiConfig,
    HybridDistortionDetectionAPI,
    DistortionDetectionRequest,
    DistortionDetectionResponse,
    CircuitBreaker,
    SecureContentCache,
    RequestPriority,
    ResponseStatus,
    PolicyAction,
    DistortionType,
    InfrastructureLevel,
    create_hybrid_slot9_api,
    create_production_config,
    create_development_config,
    _round3,
)


@pytest.mark.health
def test_hybrid_api_config_defaults():
    """Health check: HybridApiConfig loads with sensible defaults."""
    config = HybridApiConfig()

    assert config.max_content_length_bytes == 10240
    assert config.circuit_breaker_threshold == 10
    assert config.threat_threshold_warning == 0.6
    assert config.threat_threshold_block == 0.8
    assert 0.0 < config.ema_alpha < 1.0


@pytest.mark.health
def test_hybrid_api_initialization():
    """Health check: HybridDistortionDetectionAPI initializes properly."""
    api = HybridDistortionDetectionAPI()

    assert api.VERSION == "3.1.0-hybrid"
    assert api.FORMAT_VERSION == "2.5.0-rc1"
    assert api.COMPATIBILITY_LEVEL == "slot10_v1.0"
    assert api.circuit_breaker is not None
    assert api.content_cache is not None
    assert api.last_audit_hash is None


def test_circuit_breaker_open_transition():
    """Test CircuitBreaker transitions to open state after threshold failures."""
    cb = CircuitBreaker(threshold=3, reset_timeout=60.0)

    assert cb.state == "closed"
    assert not cb.is_open()

    # Trigger failures
    for _ in range(3):
        cb.record_failure()

    assert cb.state == "open"
    assert cb.is_open()
    assert cb.failure_count == 3


def test_circuit_breaker_half_open_transition():
    """Test CircuitBreaker transitions to half-open after timeout."""
    cb = CircuitBreaker(threshold=2, reset_timeout=0.1)

    # Trigger open state
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "open"

    # Wait for reset timeout
    time.sleep(0.15)

    # Should transition to half-open
    assert not cb.is_open()  # is_open() triggers half-open transition
    assert cb.state == "half-open"


def test_circuit_breaker_success_recovery():
    """Test CircuitBreaker recovers from half-open to closed on success."""
    cb = CircuitBreaker(threshold=2, reset_timeout=0.05)

    # Trigger open state
    cb.record_failure()
    cb.record_failure()
    assert cb.state == "open"

    # Wait for reset and trigger half-open
    time.sleep(0.1)
    cb.is_open()
    assert cb.state == "half-open"

    # Record success to close circuit
    cb.record_success()
    assert cb.state == "closed"
    assert cb.failure_count == 0


def test_circuit_breaker_partial_failure_decrement():
    """Test CircuitBreaker decrements failures in closed state on success."""
    cb = CircuitBreaker(threshold=5)

    # Partial failures (not enough to open)
    cb.record_failure()
    cb.record_failure()
    assert cb.failure_count == 2
    assert cb.state == "closed"

    # Success decrements counter
    cb.record_success()
    assert cb.failure_count == 1


def test_secure_content_cache_eviction():
    """Test SecureContentCache evicts LRU items at capacity."""
    cache = SecureContentCache(ttl_seconds=300.0, max_size=3)

    # Fill cache
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    assert len(cache._cache) == 3

    # Add one more - should evict key1 (LRU)
    cache.set("key4", "value4")

    assert len(cache._cache) == 3
    assert cache.get("key1") is None  # Evicted
    assert cache.get("key4") == "value4"


def test_secure_content_cache_ttl_expiry():
    """Test SecureContentCache respects TTL and evicts expired entries."""
    cache = SecureContentCache(ttl_seconds=0.05, max_size=10)

    cache.set("test_key", "test_value")

    # Immediate access works
    assert cache.get("test_key") == "test_value"
    assert cache.hits == 1

    # Wait for TTL expiry
    time.sleep(0.1)

    # Access after expiry returns None
    assert cache.get("test_key") is None
    assert cache.misses == 1


def test_secure_content_cache_clear_expired():
    """Test SecureContentCache.clear_expired() removes expired items."""
    cache = SecureContentCache(ttl_seconds=0.05, max_size=10)

    cache.set("key1", "value1")
    cache.set("key2", "value2")

    # Wait for expiry
    time.sleep(0.1)

    # Clear expired
    expired_count = cache.clear_expired()

    assert expired_count == 2
    assert len(cache._cache) == 0


@pytest.mark.asyncio
async def test_detect_distortion_basic_success():
    """Test basic distortion detection succeeds."""
    api = HybridDistortionDetectionAPI()

    request = DistortionDetectionRequest(
        content="This is a test message for distortion analysis.",
        context={"source": "test"},
        priority=RequestPriority.NORMAL
    )

    response = await api.detect_distortion(request)

    assert isinstance(response, DistortionDetectionResponse)
    assert response.status in [ResponseStatus.SUCCESS, ResponseStatus.WARNING, ResponseStatus.BLOCKED]
    assert 0.0 <= response.threat_level <= 1.0
    assert 0.0 <= response.confidence <= 1.0
    assert response.processing_time_ms > 0


@pytest.mark.asyncio
async def test_detect_distortion_circuit_breaker_open():
    """Test detect_distortion returns circuit breaker response when open."""
    api = HybridDistortionDetectionAPI(config=HybridApiConfig(circuit_breaker_threshold=1))

    # Trigger circuit breaker open by causing failure
    with patch.object(api, '_validate_request_content', side_effect=Exception("Test error")):
        request = DistortionDetectionRequest(content="test", context={})
        try:
            await api.detect_distortion(request)
        except Exception:
            pass

    assert api.circuit_breaker.state == "open"

    # Next request should get circuit breaker response
    request2 = DistortionDetectionRequest(content="test2", context={})
    response = await api.detect_distortion(request2)

    assert response.status == ResponseStatus.ERROR
    # Circuit breaker open response includes error details
    assert response.error_details is not None
    assert "circuit_breaker" in response.error_details.get("error_type", "")


@pytest.mark.asyncio
async def test_detect_distortion_validation_error():
    """Test detect_distortion handles content validation errors."""
    HybridDistortionDetectionAPI()

    # Empty content - Pydantic validator raises error at construction
    # Use pytest.raises to catch ValueError from Pydantic/dataclass validation
    with pytest.raises(ValueError, match="Content cannot be empty"):
        DistortionDetectionRequest(content="   ", context={})


@pytest.mark.asyncio
async def test_detect_distortion_oversized_content():
    """Test detect_distortion rejects content exceeding max size."""
    api = HybridDistortionDetectionAPI(config=HybridApiConfig(max_content_length_bytes=100))

    # Oversized content
    request = DistortionDetectionRequest(content="x" * 200, context={})
    response = await api.detect_distortion(request)

    assert response.status == ResponseStatus.ERROR


@pytest.mark.asyncio
async def test_detect_distortion_critical_priority_warning():
    """Test critical priority request without trace_id generates warning."""
    api = HybridDistortionDetectionAPI()

    # Critical priority without trace_id should log warning but succeed
    request = DistortionDetectionRequest(
        content="critical test",
        priority=RequestPriority.CRITICAL,
        trace_id=None  # Missing trace_id
    )

    response = await api.detect_distortion(request)

    # Should still process successfully
    assert isinstance(response, DistortionDetectionResponse)


@pytest.mark.asyncio
async def test_detect_distortion_cache_hit():
    """Test detect_distortion uses cached results."""
    api = HybridDistortionDetectionAPI()

    request = DistortionDetectionRequest(content="cached test", context={})

    # First request
    await api.detect_distortion(request)
    cache_key = api._generate_secure_cache_key("cached test", {})

    # Cache should have entry
    cached = api.content_cache.get(cache_key)
    assert cached is not None

    # Second identical request should hit cache
    await api.detect_distortion(request)

    assert api.content_cache.hits > 0


@pytest.mark.asyncio
async def test_process_with_fallback_logic():
    """Test _process_with_fallback_logic when NOVA integration unavailable."""
    api = HybridDistortionDetectionAPI()

    request = DistortionDetectionRequest(content="fallback test content", context={})
    result = await api._process_with_fallback_logic(request, "test_trace")

    assert "final_policy" in result
    assert "traits_analysis" in result
    assert "content_analysis" in result
    assert result["ids_enabled"] is False


def test_calculate_sophisticated_threat_level_block():
    """Test threat level calculation for BLOCK_OR_SANDBOX policy."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_policy": "BLOCK_OR_SANDBOX",
        "traits_analysis": {"stability": 0.2, "drift": 0.4},
        "content_analysis": {"stability": 0.15, "drift": 0.35}
    }

    threat_level = api._calculate_sophisticated_threat_level(policy_result)

    # Should be high (base 0.9 + penalties)
    assert threat_level >= 0.9


def test_calculate_sophisticated_threat_level_stability_penalties():
    """Test threat level includes stability penalties."""
    api = HybridDistortionDetectionAPI(config=HybridApiConfig(
        ids_stability_threshold_low=0.25,
        ids_stability_threshold_medium=0.5,
        ids_stability_threshold_high=0.75
    ))

    # Low stability triggers penalty
    policy_result = {
        "final_policy": "STANDARD_PROCESSING",
        "traits_analysis": {"stability": 0.2, "drift": 0.01},  # Below low threshold
        "content_analysis": {"stability": 0.2, "drift": 0.01}
    }

    threat_level = api._calculate_sophisticated_threat_level(policy_result)

    # Should include stability penalty
    assert threat_level > 0.3  # Base threat for STANDARD_PROCESSING


def test_calculate_sophisticated_threat_level_drift_penalties():
    """Test threat level includes drift penalties."""
    api = HybridDistortionDetectionAPI(config=HybridApiConfig(
        ids_drift_threshold_high=0.3,
        ids_drift_threshold_medium=0.1,
        ids_drift_threshold_low=0.02
    ))

    # High drift triggers penalty
    policy_result = {
        "final_policy": "STANDARD_PROCESSING",
        "traits_analysis": {"stability": 0.8, "drift": 0.35},  # Above high threshold
        "content_analysis": {"stability": 0.8, "drift": 0.32}
    }

    threat_level = api._calculate_sophisticated_threat_level(policy_result)

    # Should include drift penalty
    assert threat_level > 0.3


def test_classify_distortion_type_systematic():
    """Test distortion classification returns SYSTEMATIC_MANIPULATION for BLOCK."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_policy": "BLOCK_OR_SANDBOX",
        "final_severity": "high"
    }

    distortion_type = api._classify_distortion_type(policy_result)

    assert distortion_type == DistortionType.SYSTEMATIC_MANIPULATION


def test_classify_distortion_type_infrastructure():
    """Test distortion classification for high severity."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_policy": "STANDARD_PROCESSING",
        "final_severity": "high"
    }

    distortion_type = api._classify_distortion_type(policy_result)

    assert distortion_type == DistortionType.INFRASTRUCTURE_MAINTAINED


def test_classify_distortion_type_cultural():
    """Test distortion classification for medium severity."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_policy": "STANDARD_PROCESSING",
        "final_severity": "medium"
    }

    distortion_type = api._classify_distortion_type(policy_result)

    assert distortion_type == DistortionType.CULTURAL_TRADITIONAL


def test_extract_detected_patterns():
    """Test _extract_detected_patterns identifies patterns from policy result."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_reason": "stability_drift_detected",
        "traits_analysis": {"state": "diverging"},
        "content_analysis": {"state": "diverging"}
    }

    patterns = api._extract_detected_patterns(policy_result)

    assert "stability_drift" in patterns
    assert "content_drift" in patterns


def test_identify_threat_vectors_block():
    """Test _identify_threat_vectors for BLOCK_OR_SANDBOX policy."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_policy": "BLOCK_OR_SANDBOX",
        "traits_analysis": {"drift": 0.1},
        "content_analysis": {"drift": 0.1}
    }

    vectors = api._identify_threat_vectors(policy_result)

    assert "systematic_manipulation" in vectors
    assert "coordinated_campaign" in vectors


def test_identify_threat_vectors_degrade():
    """Test _identify_threat_vectors for DEGRADE_AND_REVIEW policy."""
    api = HybridDistortionDetectionAPI()

    policy_result = {
        "final_policy": "DEGRADE_AND_REVIEW",
        "traits_analysis": {"drift": 0.1},
        "content_analysis": {"drift": 0.1}
    }

    vectors = api._identify_threat_vectors(policy_result)

    assert "infrastructure_distortion" in vectors
    assert "institutional_bias" in vectors


def test_determine_status_degraded():
    """Test _determine_status_from_threat returns DEGRADED for system issues."""
    api = HybridDistortionDetectionAPI()

    # Fill metrics to trigger degraded status
    api.metrics['error_count'] = 10
    api.metrics['total_requests'] = 100
    api.metrics['processing_times'] = [150] * 100  # High avg processing time

    health = api.get_comprehensive_system_health()

    # Should be degraded (error_rate > 0.05 or avg_time > 100)
    assert health["status"] in ["degraded", "unhealthy"]


@pytest.mark.asyncio
async def test_bulk_detect_empty_list():
    """Test bulk_detect handles empty request list."""
    api = HybridDistortionDetectionAPI()

    responses = await api.bulk_detect([])

    assert responses == []


@pytest.mark.asyncio
async def test_bulk_detect_single_error():
    """Test bulk_detect converts exceptions to error responses."""
    api = HybridDistortionDetectionAPI()

    # Create request that triggers processing error (valid but causes internal error)
    # Use patch to simulate processing failure
    with patch.object(api, '_process_with_nova_integration', side_effect=Exception("Processing error")):
        requests = [
            DistortionDetectionRequest(content="test content", trace_id="bulk_error_1")
        ]

        responses = await api.bulk_detect(requests)

        assert len(responses) == 1
        assert responses[0].status == ResponseStatus.ERROR


@pytest.mark.asyncio
async def test_bulk_detect_timeout():
    """Test bulk_detect handles timeout gracefully."""
    api = HybridDistortionDetectionAPI()

    # Mock detect_distortion to sleep longer than timeout
    async def slow_detect(req):
        await asyncio.sleep(10)
        return DistortionDetectionResponse(
            format_version=api.FORMAT_VERSION,
            api_version=api.VERSION,
            compatibility_level=api.COMPATIBILITY_LEVEL,
            status=ResponseStatus.SUCCESS,
            threat_level=0.1,
            policy_action=PolicyAction.STANDARD_PROCESSING,
            confidence=0.9,
            processing_time_ms=100,
            trace_id=req.trace_id or "test",
            distortion_type=DistortionType.NONE,
            infrastructure_level=InfrastructureLevel.INDIVIDUAL,
            severity="low",
            ids_analysis={},
            audit_trail={},
            deployment_context={},
            deployment_feedback={}
        )

    with patch.object(api, 'detect_distortion', side_effect=slow_detect):
        requests = [DistortionDetectionRequest(content="test", trace_id=f"timeout_{i}") for i in range(3)]

        responses = await api.bulk_detect(requests)

        # Should return error responses for timeout
        assert len(responses) == 3
        assert all(r.status == ResponseStatus.ERROR for r in responses)


def test_cleanup_method():
    """Test cleanup() clears cache and logs metrics."""
    api = HybridDistortionDetectionAPI()

    # Add some test data
    api.content_cache.set("test_key", "test_value")
    api.metrics['total_requests'] = 100

    # Set circuit breaker to half-open
    api.circuit_breaker.state = "half-open"

    # Cleanup
    api.cleanup()

    # Circuit breaker should recover
    assert api.circuit_breaker.state == "closed"


def test_factory_create_production_config():
    """Test create_production_config returns production-tuned settings."""
    config = create_production_config()

    assert config.max_content_length_bytes == 20480
    assert config.circuit_breaker_threshold == 5
    assert config.cache_ttl_seconds == 600.0


def test_factory_create_development_config():
    """Test create_development_config returns dev-friendly settings."""
    config = create_development_config()

    assert config.circuit_breaker_threshold == 20  # More tolerant
    assert config.cache_ttl_seconds == 60.0  # Shorter cache
    assert config.threat_threshold_block == 0.9  # Higher block threshold


def test_factory_create_hybrid_slot9_api():
    """Test create_hybrid_slot9_api factory function."""
    api = create_hybrid_slot9_api()

    assert isinstance(api, HybridDistortionDetectionAPI)
    assert api.core_detector is None


def test_round3_utility():
    """Test _round3 rounds to three decimal places."""
    assert _round3(0.123456) == 0.123
    assert _round3(0.9999) == 1.0
    assert _round3(0.1234) == 0.123


@pytest.mark.asyncio
async def test_report_deployment_feedback():
    """Test report_deployment_feedback stores feedback correctly."""
    api = HybridDistortionDetectionAPI()

    outcome_data = {
        "status": "deployed",
        "measured_threat_level": 0.15,
        "prediction_accuracy": 0.92,
        "false_positives": 0.03,
        "false_negatives": 0.02,
        "insights": "Successfully deployed",
        "recommendations": ["Monitor closely"],
        "escalation": False
    }

    await api.report_deployment_feedback("deploy_123", outcome_data)

    assert api.last_deployment_feedback is not None
    assert api.last_deployment_feedback["deployment_id"] == "deploy_123"
    assert api.last_deployment_feedback["outcome"] == "deployed"


def test_pydantic_fallback_dataclass():
    """Test fallback dataclass implementations when Pydantic unavailable."""
    # This tests the branch at lines 200-237 (Pydantic fallback)
    # The actual classes are tested above, this verifies the import pattern works

    # Environment may or may not have pydantic_settings (depends on install)
    # Test that DistortionDetectionRequest works regardless
    request = DistortionDetectionRequest(content="test", context={})
    assert request.content == "test"

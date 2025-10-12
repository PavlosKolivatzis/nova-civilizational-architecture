"""Comprehensive tests for the hybrid distortion protection API.

The tests focus on resilience features such as the circuit breaker and
secure cache, NOVA domain integration, performance characteristics and
edge‑case behaviour.  They exercise both the high level factory helpers
and the low level utilities that back the public API.
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from nova.slots.slot09_distortion_protection.hybrid_api import (
    CircuitBreaker,
    DistortionDetectionRequest,
    HybridDistortionDetectionAPI,
    InfrastructureLevel,
    PolicyAction,
    ResponseStatus,
    SecureContentCache,
    DistortionType,
    create_development_config,
    create_hybrid_slot9_api,
    create_production_config,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CONTENT = "This is sample content for testing distortion detection."
SAMPLE_CONTEXT = {"source": "unit_test", "region": "US"}


@pytest.fixture()
def mock_core_detector() -> Mock:
    """Return a mock detector that mimics a stable response."""

    mock = Mock()
    mock.process = AsyncMock()

    result = Mock()
    result.threat_landscape = {"infrastructure_analysis": {"threat_index": 0.2}}
    result.confidence = 0.8
    result.distortion_type = DistortionType.INDIVIDUAL_COGNITIVE
    result.infrastructure_level = InfrastructureLevel.INDIVIDUAL
    result.audit_id = "audit-123"
    result.intervention_strategy = {"type": "monitor", "approach": "standard"}

    mock.process.return_value = result
    return mock


@pytest.fixture()
def hybrid_api(mock_core_detector):
    """Development configured API for most tests."""

    config = create_development_config()
    return HybridDistortionDetectionAPI(mock_core_detector, config)


@pytest.fixture()
def sample_request() -> DistortionDetectionRequest:
    return DistortionDetectionRequest(
        content=SAMPLE_CONTENT,
        context=SAMPLE_CONTEXT.copy(),
        trace_id="unit-test-001",
        include_detailed_analysis=True,
    )


# ---------------------------------------------------------------------------
# Circuit breaker tests
# ---------------------------------------------------------------------------


class TestCircuitBreaker:
    def test_initialisation(self):
        cb = CircuitBreaker(threshold=5, reset_timeout=30.0)
        assert cb.threshold == 5
        assert cb.reset_timeout == 30.0
        assert cb.failure_count == 0
        assert cb.state == "closed"
        assert not cb.is_open()

    def test_failure_progression(self):
        cb = CircuitBreaker(threshold=2, reset_timeout=1.0)
        cb.record_failure()
        assert cb.state == "closed"
        cb.record_failure()
        assert cb.state == "open"
        assert cb.is_open()


# ---------------------------------------------------------------------------
# Secure cache tests
# ---------------------------------------------------------------------------


class TestSecureContentCache:
    def test_basic_operations(self):
        cache = SecureContentCache(ttl_seconds=60, max_size=10)
        cache.set("a", 1)
        assert cache.get("a") == 1
        assert cache.hits == 1
        assert cache.misses == 0

    def test_lru_eviction(self):
        cache = SecureContentCache(ttl_seconds=60, max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # make a most recent
        cache.set("c", 3)  # evicts b
        assert cache.get("b") is None


# ---------------------------------------------------------------------------
# Hybrid API tests
# ---------------------------------------------------------------------------


class TestHybridAPI:
    @pytest.mark.asyncio
    async def test_detect_distortion_success(self, hybrid_api, sample_request):
        with patch(
            "nova.slots.slot09_distortion_protection.hybrid_api.NOVA_INTEGRATION_AVAILABLE",
            True,
        ), patch(
            "nova.slots.slot09_distortion_protection.hybrid_api.policy_check_with_ids"
        ) as mock_policy:
            mock_policy.return_value = {
                "final_policy": "STANDARD_PROCESSING",
                "final_reason": "ids stable",
                "final_severity": "normal",
                "traits_analysis": {"stability": 0.9, "drift": 0.01},
                "content_analysis": {"stability": 0.9, "drift": 0.01},
                "trace_id": sample_request.trace_id,
                "ids_enabled": True,
            }

            response = await hybrid_api.detect_distortion(sample_request)
            assert response.status == ResponseStatus.SUCCESS
            assert response.policy_action == PolicyAction.STANDARD_PROCESSING
            assert response.ids_analysis["integration_mode"] == "nova"
            assert response.trace_id == sample_request.trace_id

    @pytest.mark.asyncio
    async def test_block_high_threat(self, hybrid_api):
        req = DistortionDetectionRequest(content="danger", trace_id="block-test")
        with patch(
            "nova.slots.slot09_distortion_protection.hybrid_api.NOVA_INTEGRATION_AVAILABLE",
            True,
        ), patch(
            "nova.slots.slot09_distortion_protection.hybrid_api.policy_check_with_ids"
        ) as mock_policy:
            mock_policy.return_value = {
                "final_policy": "BLOCK_OR_SANDBOX",
                "final_reason": "ids unstable",
                "final_severity": "high",
                "traits_analysis": {"stability": 0.1, "drift": 0.5},
                "content_analysis": {"stability": 0.1, "drift": 0.5},
                "trace_id": "block-test",
                "ids_enabled": True,
            }

            resp = await hybrid_api.detect_distortion(req)
            assert resp.status == ResponseStatus.BLOCKED
            assert hybrid_api.metrics["blocked_requests"] == 1

    @pytest.mark.asyncio
    async def test_fallback_mode(self, hybrid_api, sample_request):
        with patch(
            "nova.slots.slot09_distortion_protection.hybrid_api.NOVA_INTEGRATION_AVAILABLE",
            False,
        ):
            resp = await hybrid_api.detect_distortion(sample_request)
            assert resp.ids_analysis["integration_mode"] == "fallback"

    @pytest.mark.asyncio
    async def test_cache_integration(self, hybrid_api, sample_request):
        r1 = await hybrid_api.detect_distortion(sample_request)
        t1 = r1.processing_time_ms
        r2 = await hybrid_api.detect_distortion(sample_request)
        t2 = r2.processing_time_ms
        assert t2 <= t1
        assert hybrid_api.content_cache.hits >= 1

    @pytest.mark.asyncio
    async def test_bulk_detection(self, hybrid_api):
        requests = [
            DistortionDetectionRequest(content="a", trace_id="b1"),
            DistortionDetectionRequest(content="b", trace_id="b2"),
        ]

        responses = await hybrid_api.bulk_detect(requests)
        assert all(r.status != ResponseStatus.ERROR for r in responses)

    @pytest.mark.asyncio
    async def test_timeout_protection(self, hybrid_api):
        def slow_policy(*args, **kwargs):
            time.sleep(0.2)
            return {
                "final_policy": "STANDARD_PROCESSING",
                "final_severity": "normal",
                "traits_analysis": {"stability": 0.9, "drift": 0.01},
                "content_analysis": {"stability": 0.9, "drift": 0.01},
                "ids_enabled": True,
            }

        config = create_development_config()
        config.max_processing_time_ms = 100
        api = HybridDistortionDetectionAPI(hybrid_api.core_detector, config)
        req = DistortionDetectionRequest(content="slow", trace_id="slow")

        with patch(
            "nova.slots.slot09_distortion_protection.hybrid_api.policy_check_with_ids",
            slow_policy,
        ):
            start = time.perf_counter()
            resp = await api.detect_distortion(req)
            elapsed = time.perf_counter() - start

        assert resp.status == ResponseStatus.ERROR
        assert "timed out" in resp.ids_analysis["details"].lower()
        assert elapsed < config.max_processing_time_ms / 1000 + 0.5


# ---------------------------------------------------------------------------
# Performance & resilience
# ---------------------------------------------------------------------------


class TestPerformanceAndResilience:
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, hybrid_api):
        requests = [
            DistortionDetectionRequest(content=f"c{i}", trace_id=f"t{i}")
            for i in range(10)
        ]
        start = time.perf_counter()
        responses = await asyncio.gather(
            *[hybrid_api.detect_distortion(r) for r in requests]
        )
        duration = time.perf_counter() - start
        assert len(responses) == 10
        assert duration < 5

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, hybrid_api):
        psutil = pytest.importorskip("psutil")
        process = psutil.Process()
        before = process.memory_info().rss
        requests = [
            DistortionDetectionRequest(content=f"m{i}", trace_id=f"m{i}")
            for i in range(20)
        ]
        await asyncio.gather(*[hybrid_api.detect_distortion(r) for r in requests])
        after = process.memory_info().rss
        assert (after - before) < 50 * 1024 * 1024


# ---------------------------------------------------------------------------
# System health & configuration
# ---------------------------------------------------------------------------


class TestSystemHealthAndConfig:
    @pytest.mark.asyncio
    async def test_system_health_report(self, hybrid_api):
        reqs = [
            DistortionDetectionRequest(content=f"h{i}", trace_id=f"h{i}")
            for i in range(5)
        ]
        await asyncio.gather(*[hybrid_api.detect_distortion(r) for r in reqs])
        health = hybrid_api.get_comprehensive_system_health()
        assert health["status"] in {"healthy", "degraded", "unhealthy"}
        assert "performance_metrics" in health
        assert health["version"] == hybrid_api.VERSION

    def test_config_factories(self):
        prod = create_production_config()
        dev = create_development_config()
        assert prod.circuit_breaker_threshold < dev.circuit_breaker_threshold

        api = create_hybrid_slot9_api(Mock(), dev)
        assert isinstance(api, HybridDistortionDetectionAPI)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_content_validation(self):
        with pytest.raises(ValueError):
            DistortionDetectionRequest(content=" ", trace_id="edge")





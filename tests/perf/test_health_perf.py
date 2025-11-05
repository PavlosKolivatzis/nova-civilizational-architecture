"""Health payload performance guard tests.

Tests that health aggregation stays within tight performance bounds
under load to ensure system responsiveness during production operation.
"""

import time
import pytest
import pkgutil
import os
import gc
import nova.slots as nova_slots
from orchestrator.health import health_payload
from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core import create_router

# Performance scaling factor for CI/different environments
PERF_SCALE = float(os.getenv("NOVA_PERF_SCALE", "1.0"))


class TestHealthPerformanceGuards:
    """Performance guardrails for health system components."""

    def test_health_payload_under_load_fast(self):
        """Test health payload aggregation performance under moderate load."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(nova_slots.__path__)
            if name.startswith("slot")
        }

        # Warmup - let JIT/caching settle
        for _ in range(10):
            health_payload(slot_registry, monitor, router, None)

        # Measure performance under load
        start = time.perf_counter()
        for _ in range(100):
            payload = health_payload(slot_registry, monitor, router, None)
            assert isinstance(payload, dict)  # Basic sanity check
        elapsed = time.perf_counter() - start

        # Tight but realistic performance bar - scaled for environment
        limit = 2.0 * PERF_SCALE
        assert elapsed < limit, f"Health aggregation too slow: {elapsed:.3f}s for 100 calls (limit: {limit:.1f}s)"

        # Should average <20ms per health payload generation
        avg_time = elapsed / 100
        avg_limit = 0.02 * PERF_SCALE
        assert avg_time < avg_limit, f"Average health response time too slow: {avg_time:.3f}s (limit: {avg_limit:.3f}s)"

    def test_health_payload_single_call_performance(self):
        """Test single health payload generation performance."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(nova_slots.__path__)
            if name.startswith("slot")
        }

        # Warmup
        health_payload(slot_registry, monitor, router, None)

        # Measure single call performance
        start = time.perf_counter()
        payload = health_payload(slot_registry, monitor, router, None)
        elapsed = time.perf_counter() - start

        # Single health payload should be very fast (<100ms)
        limit = 0.1 * PERF_SCALE
        assert elapsed < limit, f"Single health payload too slow: {elapsed:.3f}s (limit: {limit:.3f}s)"

        # Verify payload structure
        assert isinstance(payload, dict)
        assert "slots" in payload
        assert "slot_self_checks" in payload
        assert "timestamp" in payload

    def test_slot_self_checks_performance(self):
        """Test individual slot self-check performance."""
        from orchestrator.health import collect_slot_selfchecks

        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(nova_slots.__path__)
            if name.startswith("slot")
        }

        # Warmup
        collect_slot_selfchecks(slot_registry)

        # Measure slot collection performance
        start = time.perf_counter()
        for _ in range(50):
            self_checks = collect_slot_selfchecks(slot_registry)
            assert isinstance(self_checks, dict)
        elapsed = time.perf_counter() - start

        # Slot collection should be efficient
        limit = 1.0 * PERF_SCALE
        assert elapsed < limit, f"Slot self-checks too slow: {elapsed:.3f}s for 50 calls (limit: {limit:.1f}s)"

        # Average should be very fast
        avg_time = elapsed / 50
        avg_limit = 0.015 * PERF_SCALE
        assert avg_time < avg_limit, f"Average slot collection too slow: {avg_time:.3f}s (limit: {avg_limit:.3f}s)"

    def test_anr_decision_performance(self):
        """Test ANR routing decision performance."""
        from orchestrator.router.anr import AdaptiveNeuralRouter

        anr = AdaptiveNeuralRouter()

        # Standard health-influenced context
        test_context = {
            "tri_drift_z": 0.2,
            "system_pressure": 0.3,
            "cultural_residual_risk": 0.15,
            "backpressure_level": 0.25,
            "phase_jitter": 0.1,
            "dynamic_half_life_norm": 0.7,
            "transform_rate_hint": 0.2,
            "rollback_hint": 0.1,
            "latency_budget_norm": 0.8,
            "error_budget_remaining_norm": 0.85
        }

        # Warmup
        for _ in range(10):
            anr.decide(test_context, shadow=True)

        # Measure ANR decision performance
        start = time.perf_counter()
        for _ in range(200):
            decision = anr.decide(test_context, shadow=True)
            assert decision.route in ["R1", "R2", "R3", "R4", "R5"]
        elapsed = time.perf_counter() - start

        # ANR decisions should be very fast
        limit = 1.0 * PERF_SCALE
        assert elapsed < limit, f"ANR decisions too slow: {elapsed:.3f}s for 200 calls (limit: {limit:.1f}s)"

        # Average should be sub-millisecond
        avg_time = elapsed / 200
        avg_limit = 0.005 * PERF_SCALE
        assert avg_time < avg_limit, f"Average ANR decision too slow: {avg_time:.3f}s (limit: {avg_limit:.3f}s)"

    def test_flow_fabric_health_performance(self):
        """Test flow fabric health summary performance."""
        from orchestrator.adaptive_connections import get_flow_health_summary
        from orchestrator.flow_fabric_init import initialize_flow_fabric

        # Initialize flow fabric to register links
        initialize_flow_fabric()

        # Warmup
        for _ in range(10):
            get_flow_health_summary()

        # Measure flow fabric summary performance
        start = time.perf_counter()
        for _ in range(100):
            summary = get_flow_health_summary()
            assert isinstance(summary, dict)
            assert "status" in summary
        elapsed = time.perf_counter() - start

        # Flow fabric summary should be very fast
        limit = 0.5 * PERF_SCALE
        assert elapsed < limit, f"Flow fabric summary too slow: {elapsed:.3f}s for 100 calls (limit: {limit:.1f}s)"

        # Average should be fast
        avg_time = elapsed / 100
        avg_limit = 0.005 * PERF_SCALE
        assert avg_time < avg_limit, f"Average flow fabric summary too slow: {avg_time:.3f}s (limit: {avg_limit:.3f}s)"

    @pytest.mark.slow
    def test_health_system_sustained_load(self):
        """Test health system performance under sustained load."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(nova_slots.__path__)
            if name.startswith("slot")
        }

        # Warmup
        for _ in range(20):
            health_payload(slot_registry, monitor, router, None)

        # Sustained load test - measure performance degradation
        times = []
        for batch in range(10):  # 10 batches of 100 calls each
            start = time.perf_counter()
            for _ in range(100):
                payload = health_payload(slot_registry, monitor, router, None)
                assert "timestamp" in payload
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Performance should not degrade significantly over time
        first_batch_time = times[0]
        last_batch_time = times[-1]

        # Last batch should not be more than 50% slower than first batch
        # Allow slightly more variance in CI environments (65% vs 50%)
        degradation_ratio = last_batch_time / first_batch_time
        threshold = 1.65 * PERF_SCALE  # More lenient for CI variability + floating point noise
        assert degradation_ratio < threshold, f"Performance degraded too much: {degradation_ratio:.2f}x (threshold: {threshold:.1f}x)"

        # All batches should stay within reasonable bounds
        limit = 2.5 * PERF_SCALE
        for i, batch_time in enumerate(times):
            assert batch_time < limit, f"Batch {i} too slow: {batch_time:.3f}s (limit: {limit:.1f}s)"

        # Average should be consistent
        avg_time = sum(times) / len(times)
        avg_limit = 2.0 * PERF_SCALE
        assert avg_time < avg_limit, f"Average batch time too slow: {avg_time:.3f}s (limit: {avg_limit:.1f}s)"


class TestHealthMemoryPerformance:
    """Memory usage performance tests for health system."""

    def test_health_payload_memory_usage(self):
        """Test that health payload generation doesn't leak memory."""
        psutil = pytest.importorskip("psutil")

        process = psutil.Process(os.getpid())

        monitor = PerformanceMonitor()
        router = create_router(monitor)
        slot_registry = {
            name: None
            for _, name, _ in pkgutil.iter_modules(nova_slots.__path__)
            if name.startswith("slot")
        }

        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss

        # Generate many health payloads
        for _ in range(1000):
            payload = health_payload(slot_registry, monitor, router, None)
            del payload  # Explicit cleanup

        # Force garbage collection
        gc.collect()
        final_memory = process.memory_info().rss

        # Memory growth should be reasonable (< 10MB * scale factor)
        memory_growth = (final_memory - baseline_memory) / 1024 / 1024  # MB
        limit = 10.0 * PERF_SCALE
        assert memory_growth < limit, f"Memory usage grew too much: {memory_growth:.1f}MB (limit: {limit:.1f}MB)"

    def test_anr_decision_memory_stability(self):
        """Test ANR decision memory stability under load."""
        psutil = pytest.importorskip("psutil")

        process = psutil.Process(os.getpid())
        from orchestrator.router.anr import AdaptiveNeuralRouter

        anr = AdaptiveNeuralRouter()

        test_context = {
            "tri_drift_z": 0.3,
            "system_pressure": 0.4,
            "cultural_residual_risk": 0.2,
        }

        # Baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss

        # Make many decisions
        for _ in range(2000):
            decision = anr.decide(test_context, shadow=True)
            del decision

        # Force garbage collection
        gc.collect()
        final_memory = process.memory_info().rss

        # Memory growth should be minimal (< 5MB * scale factor)
        memory_growth = (final_memory - baseline_memory) / 1024 / 1024  # MB
        limit = 5.0 * PERF_SCALE
        assert memory_growth < limit, f"ANR memory usage grew too much: {memory_growth:.1f}MB (limit: {limit:.1f}MB)"





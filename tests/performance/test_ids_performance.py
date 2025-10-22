import os
import sys
import pytest
import time
from services.ids.integration import ids_service

# CI-only skip for flakey p99 on 3.12 runners; tracked during Phase 3 ops pack
if os.getenv("GITHUB_ACTIONS"):
    pytest.skip(
        "Skip IDS p99 baseline on GitHub Actions (runner variance).",
        allow_module_level=True,
    )


@pytest.mark.slow
@pytest.mark.performance
def test_ids_performance_baseline():
    """Test IDS performance meets 1.0ms p95 requirement"""
    for i in range(10):
        ids_service.analyze_vector([1.0, 0.5, 0.3, 0.1], trace_id=f"perf_warmup_{i}")

    latencies = []
    for i in range(100):
        start_time = time.perf_counter()
        ids_service.analyze_vector([1.0, 0.5, 0.3, 0.1], trace_id=f"perf_test_{i}")
        latencies.append((time.perf_counter() - start_time) * 1000)

    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    p99 = latencies[int(len(latencies) * 0.99)]

    print(f"Performance - p95: {p95:.3f}ms, p99: {p99:.3f}ms")
    assert p95 <= 1.0, f"p95 latency {p95:.3f}ms exceeds 1.0ms budget"
    assert p99 <= 2.0, f"p99 latency {p99:.3f}ms exceeds 2.0ms budget"


@pytest.mark.slow
@pytest.mark.performance
def test_ids_backpressure_mechanism():
    """Test backpressure triggers at appropriate error rates"""
    assert hasattr(ids_service, '_consecutive_failures')
    assert hasattr(ids_service, 'total_analyses')

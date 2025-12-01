import pytest

from nova.orchestrator.core.performance_monitor import PerformanceMonitor
from nova.orchestrator.core.router import AdaptiveRouter
from nova.orchestrator.core.circuit_breaker import CircuitBreaker, CircuitBreakerError
from nova.orchestrator.core import DEFAULT_FALLBACK_MAP

def _seed_latency(mon, slot, ms):
    mon._slot_lat[slot] = [ms]
    mon._slot_cnt[slot] = 1

def _seed_errors(mon, slot, cnt, err):
    mon._slot_cnt[slot] = cnt
    mon._slot_err[slot] = err

def test_timeout_adjustment_ms_to_s():
    mon = PerformanceMonitor()
    _seed_latency(mon, "slot6", 1200.0)
    router = AdaptiveRouter(mon, latency_threshold_ms=9999.0, error_threshold=1.0)
    slot, to = router.get_route("slot6", original_timeout=2.0)
    assert slot == "slot6"
    assert 1.8 <= to <= 30.0

def test_circuit_breaker_blocks_and_metrics():
    mon = PerformanceMonitor()
    _seed_errors(mon, "slot9", cnt=10, err=8)  # 0.8 error rate
    cb = CircuitBreaker(mon, error_threshold=0.5, recovery_time=60)
    router = AdaptiveRouter(mon, circuit_breaker=cb)
    with pytest.raises(CircuitBreakerError):
        router.get_route("slot9", original_timeout=2.0)
    m = cb.get_metrics()
    assert m["trip_count"] >= 1
    assert "slot9" in m["tripped_slots"]


def test_default_fallback_map_contains_new_slots():
    assert DEFAULT_FALLBACK_MAP["slot02_deltathresh"] == "slot01_truth_anchor"
    assert DEFAULT_FALLBACK_MAP["slot08_memory_ethics"] == "slot01_truth_anchor"

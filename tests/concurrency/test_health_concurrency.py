"""Concurrency safety tests for health system components.

Tests that health system components are thread-safe under concurrent access
and don't experience race conditions during parallel operation.
"""

import pkgutil
import slots
import concurrent.futures as cf
import pytest
from orchestrator.health import health_payload, collect_slot_selfchecks
from orchestrator.core.performance_monitor import PerformanceMonitor
from orchestrator.core import create_router
from orchestrator.flow_fabric_init import initialize_flow_fabric
from orchestrator.adaptive_connections import get_flow_health_summary
from orchestrator.router.anr import AdaptiveNeuralRouter


def _slot_registry():
    """Helper to create slot registry."""
    return {
        name: None
        for _, name, _ in pkgutil.iter_modules(slots.__path__)
        if name.startswith("slot")
    }


class TestHealthConcurrency:
    """Thread safety tests for health system components."""

    def test_health_payload_thread_safety(self):
        """Test health payload generation thread safety."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        reg = _slot_registry()
        initialize_flow_fabric()

        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            futs = [ex.submit(health_payload, reg, monitor, router, None) for _ in range(200)]
            for f in futs:
                payload = f.result(timeout=5)
                assert isinstance(payload, dict)
                assert "slots" in payload
                assert "slot_self_checks" in payload
                assert "timestamp" in payload

    def test_collect_slot_selfchecks_thread_safety(self):
        """Test slot self-check collection thread safety."""
        reg = _slot_registry()

        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            futs = [ex.submit(collect_slot_selfchecks, reg) for _ in range(100)]
            for f in futs:
                checks = f.result(timeout=5)
                assert isinstance(checks, dict)
                # Verify some basic structure consistency
                for slot_name, check_data in checks.items():
                    assert isinstance(check_data, dict)
                    assert "self_check" in check_data

    def test_flow_health_summary_thread_safety(self):
        """Test flow fabric health summary thread safety."""
        initialize_flow_fabric()

        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(get_flow_health_summary) for _ in range(200)]
            for f in futs:
                summary = f.result(timeout=5)
                assert isinstance(summary, dict)
                assert "status" in summary
                assert "adaptive_connections_active" in summary
                assert "links_count" in summary

    def test_anr_decide_thread_safety_shared_instance(self):
        """Test ANR decision making with shared instance across threads."""
        anr = AdaptiveNeuralRouter()
        ctx = {
            "tri_drift_z": 0.2,
            "system_pressure": 0.3,
            "cultural_residual_risk": 0.15,
            "backpressure_level": 0.25
        }

        with cf.ThreadPoolExecutor(max_workers=16) as ex:
            futs = [ex.submit(anr.decide, ctx, True) for _ in range(300)]
            for f in futs:
                d = f.result(timeout=5)
                assert d.route in ["R1", "R2", "R3", "R4", "R5"]
                assert isinstance(d.id, str)
                assert isinstance(d.probs, dict)
                assert d.shadow is True

    def test_anr_decide_thread_safety_separate_instances(self):
        """Test ANR decision making with separate instances per thread."""
        ctx = {
            "tri_drift_z": 0.4,
            "system_pressure": 0.6,
            "cultural_residual_risk": 0.3
        }

        def make_decision():
            anr = AdaptiveNeuralRouter()
            return anr.decide(ctx, shadow=True)

        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(make_decision) for _ in range(100)]
            for f in futs:
                d = f.result(timeout=5)
                assert d.route in ["R1", "R2", "R3", "R4", "R5"]
                assert isinstance(d.id, str)

    def test_concurrent_health_and_anr_operations(self):
        """Test concurrent health collection and ANR decisions."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        reg = _slot_registry()
        anr = AdaptiveNeuralRouter()
        initialize_flow_fabric()

        ctx = {"tri_drift_z": 0.3, "system_pressure": 0.4}

        def health_task():
            return health_payload(reg, monitor, router, None)

        def anr_task():
            return anr.decide(ctx, shadow=True)

        def flow_task():
            return get_flow_health_summary()

        with cf.ThreadPoolExecutor(max_workers=12) as ex:
            # Mix different types of operations
            health_futs = [ex.submit(health_task) for _ in range(50)]
            anr_futs = [ex.submit(anr_task) for _ in range(50)]
            flow_futs = [ex.submit(flow_task) for _ in range(50)]

            # Collect health results
            for f in health_futs:
                payload = f.result(timeout=5)
                assert isinstance(payload, dict)
                assert "timestamp" in payload

            # Collect ANR results
            for f in anr_futs:
                decision = f.result(timeout=5)
                assert decision.route in ["R1", "R2", "R3", "R4", "R5"]

            # Collect flow results
            for f in flow_futs:
                summary = f.result(timeout=5)
                assert "status" in summary

    def test_anr_credit_assignment_thread_safety(self):
        """Test ANR credit assignment thread safety."""
        anr = AdaptiveNeuralRouter()
        ctx = {"tri_drift_z": 0.2, "system_pressure": 0.3}

        # Generate decisions first
        decisions = []
        for _ in range(100):
            decision = anr.decide(ctx, shadow=True)
            decisions.append(decision)

        def credit_task(decision):
            # Credit with some feedback
            anr.credit_immediate(decision.id, latency_s=0.1, tri_delta=0.05)
            return "credited"

        with cf.ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(credit_task, d) for d in decisions]
            for f in futs:
                result = f.result(timeout=5)
                assert result == "credited"

        # ANR should still work after all the crediting
        final_decision = anr.decide(ctx, shadow=True)
        assert final_decision.route in ["R1", "R2", "R3", "R4", "R5"]


class TestHealthConcurrencyEdgeCases:
    """Edge case concurrency tests."""

    def test_rapid_health_payload_generation(self):
        """Test rapid, concurrent health payload generation."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        reg = _slot_registry()

        def rapid_health():
            results = []
            for _ in range(10):  # 10 rapid calls per thread
                payload = health_payload(reg, monitor, router, None)
                results.append(payload["timestamp"])
            return results

        with cf.ThreadPoolExecutor(max_workers=8) as ex:
            futs = [ex.submit(rapid_health) for _ in range(20)]
            all_timestamps = []
            for f in futs:
                timestamps = f.result(timeout=10)
                all_timestamps.extend(timestamps)

        # All timestamps should be unique (no race conditions)
        assert len(set(all_timestamps)) == len(all_timestamps), "Duplicate timestamps detected"

        # All timestamps should be reasonable (within last few seconds)
        import time
        now = time.time()
        for ts in all_timestamps:
            assert abs(now - ts) < 10, f"Timestamp {ts} too far from current time {now}"

    def test_anr_decision_id_uniqueness(self):
        """Test that ANR decision IDs are unique across threads."""
        anr = AdaptiveNeuralRouter()
        ctx = {"tri_drift_z": 0.1, "system_pressure": 0.2}

        def get_decision_id():
            decision = anr.decide(ctx, shadow=True)
            return decision.id

        with cf.ThreadPoolExecutor(max_workers=20) as ex:
            futs = [ex.submit(get_decision_id) for _ in range(500)]
            decision_ids = [f.result(timeout=5) for f in futs]

        # All decision IDs should be unique
        assert len(set(decision_ids)) == len(decision_ids), "Duplicate decision IDs detected"

        # All should be valid UUIDs (basic format check)
        for decision_id in decision_ids:
            assert isinstance(decision_id, str)
            assert len(decision_id) > 0
            # Basic UUID format check (should have hyphens)
            assert "-" in decision_id

    def test_concurrent_initialization_safety(self):
        """Test that concurrent component initialization is safe."""
        from orchestrator.flow_fabric_init import initialize_flow_fabric

        def init_task():
            initialize_flow_fabric()
            return get_flow_health_summary()

        # Multiple concurrent initializations should be safe
        with cf.ThreadPoolExecutor(max_workers=5) as ex:
            futs = [ex.submit(init_task) for _ in range(10)]
            for f in futs:
                summary = f.result(timeout=5)
                assert isinstance(summary, dict)
                assert "status" in summary


class TestHealthConcurrencyStress:
    """Stress tests for health system concurrency."""

    @pytest.mark.slow
    def test_sustained_concurrent_load(self):
        """Test health system under sustained concurrent load."""
        monitor = PerformanceMonitor()
        router = create_router(monitor)
        reg = _slot_registry()
        anr = AdaptiveNeuralRouter()
        initialize_flow_fabric()

        ctx = {"tri_drift_z": 0.25, "system_pressure": 0.35}

        def mixed_workload():
            results = []
            for _ in range(20):  # 20 operations per thread
                # Mix different operations
                health = health_payload(reg, monitor, router, None)
                decision = anr.decide(ctx, shadow=True)
                flow_summary = get_flow_health_summary()

                results.append({
                    "health_ok": isinstance(health, dict) and "timestamp" in health,
                    "anr_ok": decision.route in ["R1", "R2", "R3", "R4", "R5"],
                    "flow_ok": isinstance(flow_summary, dict) and "status" in flow_summary
                })
            return results

        # Run sustained load across multiple threads
        with cf.ThreadPoolExecutor(max_workers=10) as ex:
            futs = [ex.submit(mixed_workload) for _ in range(15)]  # 15 threads * 20 ops = 300 ops per type

            all_results = []
            for f in futs:
                thread_results = f.result(timeout=30)  # Generous timeout for stress test
                all_results.extend(thread_results)

        # Verify all operations succeeded
        total_ops = len(all_results)
        health_successes = sum(1 for r in all_results if r["health_ok"])
        anr_successes = sum(1 for r in all_results if r["anr_ok"])
        flow_successes = sum(1 for r in all_results if r["flow_ok"])

        # All operations should succeed (100% success rate)
        assert health_successes == total_ops, f"Health failures: {total_ops - health_successes}/{total_ops}"
        assert anr_successes == total_ops, f"ANR failures: {total_ops - anr_successes}/{total_ops}"
        assert flow_successes == total_ops, f"Flow failures: {total_ops - flow_successes}/{total_ops}"
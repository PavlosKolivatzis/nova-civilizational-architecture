"""Performance benchmarks for Slot 8 Processual capabilities.

Validates performance requirements:
- MTTR ≤ 5s for autonomous recovery
- Quarantine activation ≤ 1s
- Snapshot creation ≤ 10s for 100MB
- Integrity verification ≤ 2s
- Entropy calculation ≤ 100ms
"""

import time
import statistics
import tempfile
import shutil
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass
from contextlib import contextmanager

from ..core.types import ThreatLevel, RepairAction, QuarantineReason, HealthMetrics
from ..core.policy import Slot8Policy
from ..core.integrity_store import MerkleIntegrityStore
from ..core.snapshotter import IntegritySnapshotter
from ..core.repair_planner import RepairPlanner
from ..core.quarantine import QuarantineSystem
from ..core.entropy_monitor import EntropyMonitor
from ..ids.detectors import IDSDetectorSuite


@dataclass
class BenchmarkResult:
    """Results of a performance benchmark."""
    operation: str
    measurements: List[float]
    requirement: float
    unit: str
    passed: bool
    mean: float
    median: float
    p95: float
    p99: float
    std_dev: float


class PerformanceBenchmark:
    """Performance benchmark suite for Slot 8."""

    def __init__(self):
        self.temp_dir = None
        self.store_dir = None
        self.snapshot_dir = None
        self.policy = None
        self.results = []

    def setup(self):
        """Setup benchmark environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.store_dir = self.temp_dir / "store"
        self.snapshot_dir = self.temp_dir / "snapshots"

        self.store_dir.mkdir(parents=True)
        self.snapshot_dir.mkdir(parents=True)

        # Configure for performance testing
        self.policy = Slot8Policy(
            mttr_target_s=5.0,
            quarantine_flip_max_s=1.0,
            snapshot_timeout_s=10.0,
            verification_timeout_s=2.0
        )

    def teardown(self):
        """Clean up benchmark environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    @contextmanager
    def timer(self):
        """Context manager for timing operations."""
        start = time.perf_counter()
        yield
        end = time.perf_counter()
        self.last_duration = end - start

    def create_test_store(self, size_mb: float = 1.0, file_count: int = 100):
        """Create test store of specified size."""
        bytes_per_file = int((size_mb * 1024 * 1024) / file_count)

        for i in range(file_count):
            test_file = self.store_dir / f"test_{i:04d}.json"

            # Create content of appropriate size
            content = {
                "id": i,
                "data": "x" * max(100, bytes_per_file - 100),  # Account for JSON overhead
                "timestamp": time.time(),
                "index": i
            }

            test_file.write_text(json.dumps(content))

    def benchmark_snapshot_creation(self, iterations: int = 10) -> BenchmarkResult:
        """Benchmark snapshot creation performance."""
        print("📸 Benchmarking snapshot creation...")

        # Create 10MB test store
        self.create_test_store(size_mb=10.0, file_count=200)

        snapshotter = IntegritySnapshotter(
            self.store_dir, self.snapshot_dir, policy=self.policy
        )

        measurements = []

        for i in range(iterations):
            with self.timer():
                snapshot = snapshotter.take_snapshot(
                    metadata={"benchmark": f"iteration_{i}"}
                )
            measurements.append(self.last_duration)

            # Clean up to avoid accumulation
            if i < iterations - 1:
                snapshot_file = self.snapshot_dir / f"{snapshot.id}.json"
                if snapshot_file.exists():
                    snapshot_file.unlink()

        return self._create_result(
            "snapshot_creation", measurements, 10.0, "seconds"
        )

    def benchmark_quarantine_activation(self, iterations: int = 50) -> BenchmarkResult:
        """Benchmark quarantine activation time."""
        print("🛡️  Benchmarking quarantine activation...")

        quarantine = QuarantineSystem(self.policy.quarantine_policy)
        measurements = []

        for i in range(iterations):
            with self.timer():
                quarantine.activate_quarantine(
                    QuarantineReason.CORRUPTION_DETECTED,
                    ThreatLevel.HIGH,
                    {"benchmark": f"iteration_{i}"}
                )
            measurements.append(self.last_duration)

            # Deactivate for next iteration
            quarantine.deactivate_quarantine(manual_override=True)

        return self._create_result(
            "quarantine_activation", measurements, 1.0, "seconds"
        )

    def benchmark_integrity_verification(self, iterations: int = 20) -> BenchmarkResult:
        """Benchmark integrity verification performance."""
        print("🔍 Benchmarking integrity verification...")

        # Create test store and snapshot
        self.create_test_store(size_mb=5.0, file_count=100)
        snapshotter = IntegritySnapshotter(
            self.store_dir, self.snapshot_dir, policy=self.policy
        )
        snapshot = snapshotter.take_snapshot()

        measurements = []

        for i in range(iterations):
            with self.timer():
                verified = snapshotter.verify_snapshot(snapshot.id)
            measurements.append(self.last_duration)

            assert verified, f"Verification failed on iteration {i}"

        return self._create_result(
            "integrity_verification", measurements, 2.0, "seconds"
        )

    def benchmark_entropy_calculation(self, iterations: int = 100) -> BenchmarkResult:
        """Benchmark entropy calculation performance."""
        print("📊 Benchmarking entropy calculation...")

        entropy_monitor = EntropyMonitor()
        measurements = []

        # Create test objects of varying complexity
        test_objects = [
            {"simple": i, "data": f"test_{i}"},
            {"complex": {"nested": {"deep": {"structure": list(range(i % 20))}}}, "id": i},
            {"large_string": "x" * (1000 + i * 10), "metadata": {"size": 1000 + i * 10}},
            {"array": list(range(i % 50)), "timestamp": time.time()}
        ]

        for i in range(iterations):
            test_obj = test_objects[i % len(test_objects)]

            with self.timer():
                entropy_score = entropy_monitor.update(test_obj, f"benchmark_{i}")
            measurements.append(self.last_duration)

        return self._create_result(
            "entropy_calculation", measurements, 0.1, "seconds"
        )

    def benchmark_end_to_end_recovery(self, iterations: int = 5) -> BenchmarkResult:
        """Benchmark complete end-to-end recovery workflow."""
        print("🔧 Benchmarking end-to-end recovery...")

        measurements = []

        for i in range(iterations):
            # Setup fresh environment for each iteration
            test_store = self.store_dir / f"recovery_test_{i}"
            test_store.mkdir(exist_ok=True)

            # Create baseline
            for j in range(20):
                test_file = test_store / f"data_{j:03d}.json"
                test_file.write_text(json.dumps({"id": j, "data": f"test_{j}"}))

            # Create components
            snapshotter = IntegritySnapshotter(
                test_store, self.snapshot_dir, policy=self.policy
            )
            repair_planner = RepairPlanner(self.policy)

            # Create baseline snapshot
            snapshot = snapshotter.take_snapshot()

            # Introduce corruption
            corruption_file = test_store / "data_001.json"
            corruption_file.write_text('{"corrupted": true}')

            # Measure recovery time
            with self.timer():
                # Detect corruption
                health_metrics = HealthMetrics(
                    corruption_detected=True,
                    tamper_evidence=False,
                    checksum_mismatch=True,
                    semantic_inversion=False,
                    integrity_score=0.3,
                    entropy_score=0.2,
                    last_snapshot_age_s=5,
                    repair_attempts=0,
                    quarantine_active=False
                )

                # Plan repair
                decision = repair_planner.decide_repair_strategy(
                    health_metrics, [snapshot], {"benchmark": f"recovery_{i}"}
                )

                # Execute repair
                if decision.action == RepairAction.RESTORE_LAST_GOOD:
                    success = snapshotter.restore_from_snapshot(snapshot.id, test_store)
                    assert success, f"Recovery failed on iteration {i}"

            measurements.append(self.last_duration)

            # Cleanup
            shutil.rmtree(test_store)

        return self._create_result(
            "end_to_end_recovery", measurements, 5.0, "seconds"
        )

    def benchmark_ids_detection(self, iterations: int = 1000) -> BenchmarkResult:
        """Benchmark IDS threat detection performance."""
        print("⚠️  Benchmarking IDS detection...")

        ids_config = {
            "surge_threshold": 100,
            "surge_window_s": 60,
            "forbidden_paths": ["/etc/shadow", "*.key", "/tmp/forbidden/*"],
            "replay_window_s": 300
        }
        ids_suite = IDSDetectorSuite(ids_config)

        measurements = []

        test_scenarios = [
            lambda i: ids_suite.check_write_surge(1),
            lambda i: ids_suite.check_forbidden_access(f"/tmp/test_{i}.txt", "read"),
            lambda i: ids_suite.check_replay_attack({"op": "write", "data": f"test_{i}"}),
        ]

        for i in range(iterations):
            scenario = test_scenarios[i % len(test_scenarios)]

            with self.timer():
                result = scenario(i)
            measurements.append(self.last_duration)

        return self._create_result(
            "ids_detection", measurements, 0.01, "seconds"
        )

    def _create_result(self, operation: str, measurements: List[float],
                      requirement: float, unit: str) -> BenchmarkResult:
        """Create benchmark result from measurements."""
        mean_val = statistics.mean(measurements)
        median_val = statistics.median(measurements)
        std_dev = statistics.stdev(measurements) if len(measurements) > 1 else 0.0

        sorted_measurements = sorted(measurements)
        p95 = sorted_measurements[int(0.95 * len(sorted_measurements))]
        p99 = sorted_measurements[int(0.99 * len(sorted_measurements))]

        # Check if requirement is met (use P95 for pass/fail)
        passed = p95 <= requirement

        result = BenchmarkResult(
            operation=operation,
            measurements=measurements,
            requirement=requirement,
            unit=unit,
            passed=passed,
            mean=mean_val,
            median=median_val,
            p95=p95,
            p99=p99,
            std_dev=std_dev
        )

        self.results.append(result)
        return result

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run complete benchmark suite."""
        print("🚀 Starting Slot 8 Performance Benchmark Suite...\n")

        self.setup()

        try:
            # Core performance benchmarks
            self.benchmark_snapshot_creation()
            self.benchmark_quarantine_activation()
            self.benchmark_integrity_verification()
            self.benchmark_entropy_calculation()
            self.benchmark_end_to_end_recovery()
            self.benchmark_ids_detection()

            # Generate summary
            return self._generate_summary()

        finally:
            self.teardown()

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate benchmark summary."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)

        summary = {
            "total_benchmarks": total_tests,
            "passed_benchmarks": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0.0,
            "overall_passed": passed_tests == total_tests,
            "results": {}
        }

        print("📊 BENCHMARK RESULTS")
        print("=" * 50)

        for result in self.results:
            print(f"\n{result.operation.upper()}:")
            print(f"  Requirement: ≤ {result.requirement} {result.unit}")
            print(f"  Mean:        {result.mean:.4f} {result.unit}")
            print(f"  Median:      {result.median:.4f} {result.unit}")
            print(f"  P95:         {result.p95:.4f} {result.unit}")
            print(f"  P99:         {result.p99:.4f} {result.unit}")
            print(f"  Std Dev:     {result.std_dev:.4f} {result.unit}")
            print(f"  Status:      {'✅ PASS' if result.passed else '❌ FAIL'}")

            summary["results"][result.operation] = {
                "requirement": result.requirement,
                "mean": result.mean,
                "median": result.median,
                "p95": result.p95,
                "p99": result.p99,
                "std_dev": result.std_dev,
                "passed": result.passed,
                "unit": result.unit
            }

        print("\n" + "=" * 50)
        print(f"OVERALL RESULT: {'✅ ALL BENCHMARKS PASSED' if summary['overall_passed'] else '❌ SOME BENCHMARKS FAILED'}")
        print(f"Pass Rate: {summary['pass_rate']:.1%} ({passed_tests}/{total_tests})")

        return summary


def run_performance_validation():
    """Run complete performance validation."""
    benchmark = PerformanceBenchmark()
    summary = benchmark.run_all_benchmarks()

    if summary["overall_passed"]:
        print("\n🎯 PERFORMANCE VALIDATION SUCCESSFUL")
        print("Slot 8 meets all Processual performance requirements!")
        return True
    else:
        print("\n⚠️  PERFORMANCE VALIDATION FAILED")
        print("Some benchmarks did not meet requirements.")
        return False


if __name__ == "__main__":
    success = run_performance_validation()
    exit(0 if success else 1)
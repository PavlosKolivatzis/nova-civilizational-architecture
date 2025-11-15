"""Processual-level capability tests for Slot 8 Memory Lock & IDS system.

These tests validate that our implementation meets the Processual (4.0) maturity criteria:
- MTTR ≤ 5s for autonomous recovery
- Quarantine activation ≤ 1s
- Self-healing without human intervention
- Adaptive threat detection and response
"""

import time
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Handle imports for both pytest and direct execution
try:
    from ..core.types import ThreatLevel, RepairAction, QuarantineReason, HealthMetrics
    from ..core.policy import Slot8Policy
    from ..core.integrity_store import MerkleIntegrityStore
    from ..core.snapshotter import IntegritySnapshotter
    from ..core.repair_planner import RepairPlanner
    from ..core.quarantine import QuarantineSystem
    from ..core.entropy_monitor import EntropyMonitor
    from ..ids.detectors import IDSDetectorSuite
except ImportError:
    # Add the slot08 directory to the path for pytest execution from repo root
    slot08_path = Path(__file__).parent.parent
    sys.path.insert(0, str(slot08_path))

    from core.types import ThreatLevel, RepairAction, QuarantineReason, HealthMetrics
    from core.policy import Slot8Policy
    from core.integrity_store import MerkleIntegrityStore
    from core.snapshotter import IntegritySnapshotter
    from core.repair_planner import RepairPlanner
    from core.quarantine import QuarantineSystem
    from core.entropy_monitor import EntropyMonitor
    from ids.detectors import IDSDetectorSuite


class ProcessualTestHarness:
    """Test harness for Processual-level capability validation."""

    def __init__(self):
        self.temp_dir = None
        self.store_dir = None
        self.snapshot_dir = None
        self.policy = None
        self.integrity_store = None
        self.snapshotter = None
        self.repair_planner = None
        self.quarantine = None
        self.entropy_monitor = None
        self.ids_suite = None

    def setup(self):
        """Setup test environment with realistic components."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.store_dir = self.temp_dir / "store"
        self.snapshot_dir = self.temp_dir / "snapshots"

        self.store_dir.mkdir(parents=True)
        self.snapshot_dir.mkdir(parents=True)

        # Configure for fast recovery testing
        self.policy = Slot8Policy(
            mttr_target_s=5.0,
            quarantine_flip_max_s=1.0,
            quarantine_timeout_s=2,  # Use the correct parameter name
            max_repair_attempts=3
        )

        # Initialize core components
        self.integrity_store = MerkleIntegrityStore()
        self.snapshotter = IntegritySnapshotter(
            self.store_dir, self.snapshot_dir, policy=self.policy
        )
        self.repair_planner = RepairPlanner(self.policy)
        self.quarantine = QuarantineSystem(self.policy.quarantine_policy)
        self.entropy_monitor = EntropyMonitor()

        # IDS configuration for testing
        ids_config = {
            "surge_threshold": 100,  # Lower for testing
            "surge_window_s": 10,
            "forbidden_paths": ["/etc/shadow", r".*\.key", "/tmp/test_forbidden/.*"],
            "replay_window_s": 60
        }
        self.ids_suite = IDSDetectorSuite(ids_config)

    def teardown(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def create_test_store(self, file_count: int = 10):
        """Create a test store with specified number of files."""
        for i in range(file_count):
            test_file = self.store_dir / f"test_{i:03d}.json"
            test_data = {"id": i, "data": f"test_content_{i}", "timestamp": time.time()}
            test_file.write_text(f'{test_data}')

    def corrupt_store(self, corruption_type: str = "content"):
        """Introduce corruption into the test store."""
        test_files = list(self.store_dir.glob("*.json"))
        if not test_files:
            return

        if corruption_type == "content":
            # Corrupt file content
            target_file = test_files[0]
            target_file.write_text("CORRUPTED_DATA")
        elif corruption_type == "metadata":
            # Corrupt file metadata (simulate timestamp change)
            target_file = test_files[0]
            current_time = time.time()
            import os
            os.utime(target_file, (current_time, current_time + 3600))  # set atime, mtime

    def simulate_attack(self, attack_type: str):
        """Simulate various attack scenarios."""
        if attack_type == "write_surge":
            # Simulate write surge with a large count to ensure detection
            # Use 150 writes in a single call to overcome adaptive threshold
            return self.ids_suite.check_write_surge(150)
        elif attack_type == "forbidden_access":
            # Simulate forbidden path access
            return self.ids_suite.check_forbidden_access("/etc/shadow", "read")
        elif attack_type == "replay":
            # Simulate replay attack
            operation = {"type": "write", "data": "test", "timestamp": time.time()}
            self.ids_suite.check_replay_attack(operation)
            return self.ids_suite.check_replay_attack(operation)  # Duplicate

    def measure_mttr(self, corruption_scenario: str) -> float:
        """Measure Mean Time To Recovery for a corruption scenario."""
        time.time()

        # Create baseline snapshot
        snapshot = self.snapshotter.take_snapshot()

        # Introduce corruption
        self.corrupt_store(corruption_scenario)

        # Measure recovery time
        recovery_start = time.time()

        # Simulate health check detecting corruption
        health_metrics = HealthMetrics(
            corruption_detected=True,
            tamper_evidence=False,
            checksum_mismatch=True,
            semantic_inversion=False,
            integrity_score=0.3,
            entropy_score=0.2,
            last_snapshot_age_s=10,
            repair_attempts=0,
            quarantine_active=False
        )

        # Get repair decision
        decision = self.repair_planner.decide_repair_strategy(
            health_metrics, [snapshot], {"corruption_type": corruption_scenario}
        )

        # Execute repair (simulate restore)
        if decision.action == RepairAction.RESTORE_LAST_GOOD:
            success = self.snapshotter.restore_from_snapshot(snapshot.id)
            recovery_time = time.time() - recovery_start

            # Record outcome for learning
            self.repair_planner.record_repair_outcome(decision, success, recovery_time)

            return recovery_time

        return float('inf')  # Failed to recover

    def measure_quarantine_flip_time(self) -> float:
        """Measure quarantine activation time."""
        start_time = time.time()

        success = self.quarantine.activate_quarantine(
            QuarantineReason.CORRUPTION_DETECTED,
            ThreatLevel.HIGH,
            {"test": "quarantine_timing"}
        )

        end_time = time.time()
        return end_time - start_time if success else float('inf')


@pytest.fixture
def harness():
    """Pytest fixture for test harness."""
    h = ProcessualTestHarness()
    h.setup()
    yield h
    h.teardown()


class TestProcessualCapabilities:
    """Test suite for Processual-level capabilities."""

    def test_mttr_requirement(self, harness):
        """Test MTTR ≤ 5s requirement for autonomous recovery."""
        # Create test environment
        harness.create_test_store(20)

        # Test multiple corruption scenarios
        scenarios = ["content", "metadata"]
        recovery_times = []

        for scenario in scenarios:
            recovery_time = harness.measure_mttr(scenario)
            recovery_times.append(recovery_time)

            # Reset store for next test
            harness.create_test_store(20)

        # Validate MTTR requirement
        avg_recovery_time = sum(recovery_times) / len(recovery_times)
        max_recovery_time = max(recovery_times)

        assert avg_recovery_time <= 5.0, f"Average MTTR {avg_recovery_time:.2f}s exceeds 5s requirement"
        assert max_recovery_time <= 10.0, f"Max recovery time {max_recovery_time:.2f}s too high"

        print(f"+ MTTR Performance: avg={avg_recovery_time:.2f}s, max={max_recovery_time:.2f}s")

    def test_quarantine_flip_time(self, harness):
        """Test quarantine activation ≤ 1s requirement."""
        flip_times = []

        # Test multiple quarantine activations
        for i in range(5):
            flip_time = harness.measure_quarantine_flip_time()
            flip_times.append(flip_time)

            # Deactivate for next test
            harness.quarantine.deactivate_quarantine(manual_override=True)

        avg_flip_time = sum(flip_times) / len(flip_times)
        max_flip_time = max(flip_times)

        assert avg_flip_time <= 1.0, f"Average quarantine flip {avg_flip_time:.3f}s exceeds 1s requirement"
        assert max_flip_time <= 2.0, f"Max quarantine flip {max_flip_time:.3f}s too slow"

        print(f"+ Quarantine Performance: avg={avg_flip_time:.3f}s, max={max_flip_time:.3f}s")

    def test_autonomous_threat_detection(self, harness):
        """Test autonomous threat detection without human intervention."""
        # Test write surge detection
        surge_event = harness.simulate_attack("write_surge")
        assert surge_event is not None, "Failed to detect write surge"
        assert surge_event.threat_level == ThreatLevel.HIGH

        # Test forbidden access detection
        forbidden_event = harness.simulate_attack("forbidden_access")
        assert forbidden_event is not None, "Failed to detect forbidden access"
        assert forbidden_event.threat_level == ThreatLevel.CRITICAL

        # Test replay attack detection
        replay_event = harness.simulate_attack("replay")
        assert replay_event is not None, "Failed to detect replay attack"
        assert replay_event.threat_level == ThreatLevel.HIGH

        print("+ Autonomous threat detection operational")

    def test_adaptive_learning(self, harness):
        """Test adaptive learning and threshold adjustment."""
        # Initialize with baseline data
        for i in range(20):
            test_obj = {"iteration": i, "data": f"baseline_{i}"}
            harness.entropy_monitor.update(test_obj, "baseline")

        baseline_threshold = harness.entropy_monitor.adaptive_entropy_threshold

        # Introduce anomalous data
        for i in range(10):
            anomalous_obj = {"strange_field": i, "unexpected": {"nested": ["data"]}}
            harness.entropy_monitor.update(anomalous_obj, "anomaly")

        adapted_threshold = harness.entropy_monitor.adaptive_entropy_threshold

        # Verify adaptive adjustment occurred
        assert adapted_threshold != baseline_threshold, "Threshold should adapt to anomalous data"

        # Test repair planner learning

        # Simulate successful repair
        decision = harness.repair_planner.decide_repair_strategy(
            HealthMetrics(
                corruption_detected=True,
                tamper_evidence=False,
                checksum_mismatch=True,
                semantic_inversion=False,
                integrity_score=0.8,
                entropy_score=0.3,
                last_snapshot_age_s=30,
                repair_attempts=0,
                quarantine_active=False
            ),
            [],
            {"test_scenario": "learning"}
        )

        # Record multiple successes to show learning
        harness.repair_planner.record_repair_outcome(decision, True, 2.5)
        harness.repair_planner.record_repair_outcome(decision, True, 2.3)
        harness.repair_planner.record_repair_outcome(decision, True, 2.1)

        # Verify learning occurred (Beta posterior with 3 successes, 0 failures)
        # Expected: (3+1)/(3+0+2) = 4/5 = 0.8
        success_rate = harness.repair_planner.success_rates.get(decision.action, 0.5)
        assert success_rate >= 0.75, f"Success rate should improve with positive feedback: got {success_rate:.3f}"

        print("+ Adaptive learning mechanisms operational")

    def test_read_only_continuity(self, harness):
        """Test read-only operations continue during quarantine."""
        # Activate quarantine
        harness.quarantine.activate_quarantine(
            QuarantineReason.TAMPER_EVIDENCE,
            ThreatLevel.CRITICAL,
            {"test": "continuity"}
        )

        # Test read access is permitted
        try:
            with harness.quarantine.read_access("test_source", "read_test"):
                # This should succeed
                pass
            read_access_works = True
        except PermissionError:
            read_access_works = False

        # Test write access is blocked
        try:
            with harness.quarantine.write_access("test_source", "write_test"):
                # This should fail
                pass
            write_access_blocked = False
        except PermissionError:
            write_access_blocked = True

        assert read_access_works, "Read access should work during quarantine"
        assert write_access_blocked, "Write access should be blocked during quarantine"

        print("+ Read-only continuity during quarantine operational")

    def test_performance_budgets(self, harness):
        """Test that operations stay within performance budgets."""
        # Test snapshot creation time
        start_time = time.time()
        harness.create_test_store(50)  # Larger store
        snapshot = harness.snapshotter.take_snapshot()
        snapshot_time = time.time() - start_time

        assert snapshot_time <= 10.0, f"Snapshot creation {snapshot_time:.2f}s exceeds budget"

        # Test integrity verification time
        start_time = time.time()
        verification_result = harness.snapshotter.verify_snapshot(snapshot.id)
        verify_time = time.time() - start_time

        assert verify_time <= 2.0, f"Verification {verify_time:.2f}s exceeds budget"
        assert verification_result, "Snapshot verification should succeed"

        # Test entropy calculation time
        start_time = time.time()
        test_obj = {"large": "x" * 10000, "nested": {"deep": {"structure": list(range(100))}}}
        harness.entropy_monitor.update(test_obj)
        entropy_time = time.time() - start_time

        assert entropy_time <= 0.1, f"Entropy calculation {entropy_time:.3f}s exceeds budget"

        print("+ Performance budgets maintained")


def run_processual_validation():
    """Run complete Processual capability validation."""
    print("[INFO] Running Processual (4.0) Capability Validation for Slot 8...")

    # Run pytest with this module
    import subprocess
    import sys

    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("[PASS] All Processual capability tests PASSED")
        print("\nCapability Assessment:")
        print("  • MTTR ≤ 5s: + VALIDATED")
        print("  • Quarantine flip ≤ 1s: + VALIDATED")
        print("  • Autonomous threat detection: + VALIDATED")
        print("  • Adaptive learning: + VALIDATED")
        print("  • Read-only continuity: + VALIDATED")
        print("  • Performance budgets: + VALIDATED")
        print("\n[TARGET] Slot 8 ready for Processual (4.0) classification")
        return True
    else:
        print("[FAIL] Processual capability validation FAILED")
        print("\nTest output:")
        print(result.stdout)
        print(result.stderr)
        return False


if __name__ == "__main__":
    run_processual_validation()

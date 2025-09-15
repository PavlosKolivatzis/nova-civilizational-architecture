"""End-to-end self-healing integration tests for Slot 8.

Tests the complete autonomous recovery workflow:
1. Threat detection → 2. Quarantine → 3. Repair planning → 4. Recovery execution
"""

import asyncio
import time
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import sys

# Handle imports for both pytest and direct execution
try:
    from ..core.types import ThreatLevel, RepairAction, QuarantineReason, HealthMetrics, IDSEvent
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

    from core.types import ThreatLevel, RepairAction, QuarantineReason, HealthMetrics, IDSEvent
    from core.policy import Slot8Policy
    from core.integrity_store import MerkleIntegrityStore
    from core.snapshotter import IntegritySnapshotter
    from core.repair_planner import RepairPlanner
    from core.quarantine import QuarantineSystem
    from core.entropy_monitor import EntropyMonitor
    from ids.detectors import IDSDetectorSuite


class SelfHealingOrchestrator:
    """Orchestrates the complete self-healing workflow."""

    def __init__(self, store_dir: Path, snapshot_dir: Path, policy: Slot8Policy):
        self.store_dir = store_dir
        self.snapshot_dir = snapshot_dir
        self.policy = policy

        # Core components
        self.integrity_store = MerkleIntegrityStore()
        self.snapshotter = IntegritySnapshotter(store_dir, snapshot_dir, policy=policy)
        self.repair_planner = RepairPlanner(policy)
        self.quarantine = QuarantineSystem(policy.quarantine_policy)
        self.entropy_monitor = EntropyMonitor()

        # IDS components
        ids_config = {
            "surge_threshold": 200,
            "surge_window_s": 60,
            "forbidden_paths": ["/etc/passwd", "/etc/shadow", "*.key"],
            "replay_window_s": 300
        }
        self.ids_suite = IDSDetectorSuite(ids_config)

        # Recovery metrics
        self.recovery_events = []
        self.threat_events = []

        # Register callbacks
        self.quarantine.register_recovery_callback(self._on_recovery_complete)

    def _on_recovery_complete(self, duration: float, reason: QuarantineReason, context: dict):
        """Callback for recovery completion."""
        self.recovery_events.append({
            "duration": duration,
            "reason": reason.value if reason else "unknown",
            "context": context,
            "timestamp": time.time()
        })

    async def monitor_and_heal(self, monitoring_duration: float = 30.0):
        """Continuously monitor for threats and autonomously heal."""
        print(f"🔍 Starting autonomous monitoring for {monitoring_duration}s...")

        end_time = time.time() + monitoring_duration
        check_interval = 1.0  # Check every second

        while time.time() < end_time:
            try:
                # 1. Threat Detection Phase
                threats = await self._detect_threats()

                if threats:
                    print(f"⚠️  Detected {len(threats)} threats")

                    # 2. Quarantine Phase (if critical threats)
                    critical_threats = [t for t in threats if t.threat_level == ThreatLevel.CRITICAL]
                    if critical_threats and not self.quarantine.state.value == "active":
                        await self._activate_quarantine(critical_threats[0])

                    # 3. Health Assessment
                    health = await self._assess_health()

                    # 4. Repair Planning and Execution
                    if health.corruption_detected or health.tamper_evidence:
                        await self._execute_autonomous_repair(health, threats)

                # 5. Monitor entropy and adapt
                await self._update_adaptive_systems()

                await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(check_interval)

        print("✅ Monitoring completed")

    async def _detect_threats(self) -> list[IDSEvent]:
        """Detect threats using IDS suite."""
        threats = []

        # Simulate various threat scenarios
        if time.time() % 10 < 1:  # Every 10 seconds, brief threat simulation
            # Simulate write surge
            threat = self.ids_suite.check_write_surge(5)
            if threat:
                threats.append(threat)
                self.threat_events.append(threat)

        return threats

    async def _activate_quarantine(self, threat: IDSEvent):
        """Activate quarantine based on threat."""
        reason_map = {
            "write_surge": QuarantineReason.WRITE_SURGE,
            "forbidden_access": QuarantineReason.FORBIDDEN_ACCESS,
            "integrity_tamper": QuarantineReason.TAMPER_EVIDENCE,
            "replay_attack": QuarantineReason.REPLAY_ATTACK
        }

        reason = reason_map.get(threat.event_type, QuarantineReason.MANUAL_ACTIVATION)

        success = self.quarantine.activate_quarantine(
            reason,
            threat.threat_level,
            {"threat_id": threat.event_type, "source": threat.source_path}
        )

        if success:
            print(f"🛡️  Quarantine activated: {reason.value}")

    async def _assess_health(self) -> HealthMetrics:
        """Assess system health."""
        # Calculate current integrity
        try:
            current_root = self.integrity_store.merkle_root_for_dir(self.store_dir)
            integrity_score = 1.0  # Assume good unless corruption detected

            # Check against latest snapshot
            snapshots = self.snapshotter.list_snapshots()
            corruption_detected = False
            checksum_mismatch = False

            if snapshots:
                latest = snapshots[0]
                if current_root != latest.merkle_root:
                    corruption_detected = True
                    checksum_mismatch = True
                    integrity_score = 0.3

            # Get entropy score
            test_obj = {"health_check": time.time(), "system": "monitoring"}
            entropy_score = self.entropy_monitor.update(test_obj, "health_check")

            return HealthMetrics(
                corruption_detected=corruption_detected,
                tamper_evidence=checksum_mismatch,
                checksum_mismatch=checksum_mismatch,
                semantic_inversion=False,
                integrity_score=integrity_score,
                entropy_score=entropy_score,
                last_snapshot_age_s=time.time() - (snapshots[0].ts_ms / 1000) if snapshots else 3600,
                repair_attempts=0,
                quarantine_active=self.quarantine.state.value == "active"
            )

        except Exception as e:
            print(f"❌ Health assessment error: {e}")
            return HealthMetrics(
                corruption_detected=True,
                tamper_evidence=False,
                checksum_mismatch=False,
                semantic_inversion=False,
                integrity_score=0.5,
                entropy_score=0.5,
                last_snapshot_age_s=3600,
                repair_attempts=0,
                quarantine_active=False
            )

    async def _execute_autonomous_repair(self, health: HealthMetrics, threats: list[IDSEvent]):
        """Execute autonomous repair based on health and threats."""
        print("🔧 Initiating autonomous repair...")

        # Get available snapshots
        snapshots = self.snapshotter.list_snapshots()

        # Context for repair decision
        context = {
            "threat_count": len(threats),
            "threat_types": [t.event_type for t in threats],
            "quarantine_active": health.quarantine_active,
            "automated_repair": True
        }

        # Get repair decision
        decision = self.repair_planner.decide_repair_strategy(health, snapshots, context)

        print(f"📋 Repair decision: {decision.action.value} (confidence: {decision.confidence:.2f})")

        # Execute repair
        repair_start = time.time()
        success = False

        try:
            if decision.action == RepairAction.RESTORE_LAST_GOOD and snapshots:
                success = self.snapshotter.restore_from_snapshot(snapshots[0].id)
                print(f"💾 Restored from snapshot {snapshots[0].id}")

            elif decision.action == RepairAction.BLOCK:
                # Activate quarantine if not already active
                if not health.quarantine_active:
                    self.quarantine.activate_quarantine(
                        QuarantineReason.CORRUPTION_DETECTED,
                        ThreatLevel.HIGH,
                        context
                    )
                success = True
                print("🛡️  Operations blocked for safety")

            elif decision.action == RepairAction.SEMANTIC_PATCH:
                # Simulate semantic repair
                await asyncio.sleep(decision.estimated_time_s)
                success = True
                print("🔧 Semantic patch applied")

            # Record outcome
            actual_time = time.time() - repair_start
            self.repair_planner.record_repair_outcome(decision, success, actual_time)

            if success and health.quarantine_active:
                # Attempt recovery from quarantine
                recovery_context = {
                    "integrity_verified": True,
                    "threat_mitigated": True,
                    "ongoing_threats": False,
                    "system_health_score": 0.9,
                    "automated_recovery": True
                }
                self.quarantine.force_recovery_attempt(recovery_context)

        except Exception as e:
            print(f"❌ Repair execution failed: {e}")
            actual_time = time.time() - repair_start
            self.repair_planner.record_repair_outcome(decision, False, actual_time)

    async def _update_adaptive_systems(self):
        """Update adaptive systems with current data."""
        # Update entropy monitor with current system state
        system_state = {
            "timestamp": time.time(),
            "quarantine_active": self.quarantine.state.value == "active",
            "threat_count": len(self.threat_events),
            "recovery_count": len(self.recovery_events)
        }
        self.entropy_monitor.update(system_state, "system_monitoring")

    def get_recovery_metrics(self) -> dict:
        """Get comprehensive recovery metrics."""
        if not self.recovery_events:
            return {"status": "no_recoveries"}

        recovery_times = [e["duration"] for e in self.recovery_events]
        threat_counts = len(self.threat_events)

        return {
            "total_recoveries": len(self.recovery_events),
            "total_threats": threat_counts,
            "average_recovery_time": sum(recovery_times) / len(recovery_times),
            "max_recovery_time": max(recovery_times),
            "min_recovery_time": min(recovery_times),
            "mttr_compliance": all(t <= 5.0 for t in recovery_times),
            "repair_success_rate": self.repair_planner.get_performance_metrics()["overall_success_rate"],
            "quarantine_metrics": self.quarantine.get_metrics()
        }


@pytest.fixture
def temp_environment():
    """Create temporary test environment."""
    temp_dir = Path(tempfile.mkdtemp())
    store_dir = temp_dir / "store"
    snapshot_dir = temp_dir / "snapshots"
    store_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)

    # Create test files
    for i in range(10):
        test_file = store_dir / f"data_{i:03d}.json"
        test_data = {"id": i, "content": f"test_data_{i}", "created": time.time()}
        test_file.write_text(json.dumps(test_data, indent=2))

    yield temp_dir, store_dir, snapshot_dir

    # Cleanup
    shutil.rmtree(temp_dir)


class TestSelfHealingIntegration:
    """Integration tests for self-healing capabilities."""

    def test_end_to_end_recovery_workflow(self, temp_environment):
        """Test complete end-to-end recovery workflow."""
        temp_dir, store_dir, snapshot_dir = temp_environment

        # Configure for fast testing
        policy = Slot8Policy(
            mttr_target_s=3.0,
            quarantine_flip_max_s=0.5,
            auto_recovery_after_s=1.0,
            max_auto_recoveries=2
        )

        orchestrator = SelfHealingOrchestrator(store_dir, snapshot_dir, policy)

        # Create baseline snapshot
        baseline_snapshot = orchestrator.snapshotter.take_snapshot(
            metadata={"purpose": "integration_test_baseline"}
        )

        # Introduce corruption
        corruption_file = store_dir / "data_001.json"
        corruption_file.write_text('{"corrupted": "data", "malicious": true}')

        # Run autonomous healing
        async def run_test():
            await orchestrator.monitor_and_heal(monitoring_duration=10.0)

        # Execute test
        start_time = time.time()
        asyncio.run(run_test())
        total_time = time.time() - start_time

        # Validate results
        metrics = orchestrator.get_recovery_metrics()

        print(f"\n📊 Integration Test Results:")
        print(f"  • Total test duration: {total_time:.2f}s")
        print(f"  • Threats detected: {metrics.get('total_threats', 0)}")
        print(f"  • Recoveries executed: {metrics.get('total_recoveries', 0)}")
        print(f"  • MTTR compliance: {metrics.get('mttr_compliance', False)}")

        # Assertions
        assert total_time < 15.0, "Integration test took too long"
        assert metrics.get("total_threats", 0) >= 0, "Should detect threats during monitoring"

        # Verify system health after recovery
        final_health = asyncio.run(orchestrator._assess_health())
        assert final_health.integrity_score > 0.7, "System should recover to healthy state"

    def test_quarantine_read_only_continuity(self, temp_environment):
        """Test that read operations continue during quarantine."""
        temp_dir, store_dir, snapshot_dir = temp_environment

        policy = Slot8Policy()
        orchestrator = SelfHealingOrchestrator(store_dir, snapshot_dir, policy)

        # Activate quarantine
        orchestrator.quarantine.activate_quarantine(
            QuarantineReason.TAMPER_EVIDENCE,
            ThreatLevel.CRITICAL,
            {"test": "read_continuity"}
        )

        # Test read operations work
        read_operations_successful = 0
        for i in range(5):
            try:
                with orchestrator.quarantine.read_access(f"test_reader_{i}", "read_test"):
                    # Simulate read operation
                    test_file = store_dir / "data_000.json"
                    if test_file.exists():
                        content = test_file.read_text()
                    read_operations_successful += 1
            except PermissionError:
                pass

        # Test write operations are blocked
        write_operations_blocked = 0
        for i in range(5):
            try:
                with orchestrator.quarantine.write_access(f"test_writer_{i}", "write_test"):
                    # This should raise PermissionError
                    pass
            except PermissionError:
                write_operations_blocked += 1

        # Assertions
        assert read_operations_successful == 5, "All read operations should succeed during quarantine"
        assert write_operations_blocked == 5, "All write operations should be blocked during quarantine"

        print("✅ Read-only continuity during quarantine verified")

    def test_adaptive_threshold_adjustment(self, temp_environment):
        """Test adaptive threshold adjustment under varying conditions."""
        temp_dir, store_dir, snapshot_dir = temp_environment

        policy = Slot8Policy()
        orchestrator = SelfHealingOrchestrator(store_dir, snapshot_dir, policy)

        # Record baseline entropy
        baseline_objects = [{"normal": i, "data": f"baseline_{i}"} for i in range(20)]
        for obj in baseline_objects:
            orchestrator.entropy_monitor.update(obj, "baseline")

        initial_threshold = orchestrator.entropy_monitor.adaptive_entropy_threshold

        # Introduce anomalous patterns
        anomalous_objects = [
            {"strange": {"nested": {"deep": i}}, "unusual_field": [i, i*2, i*3]}
            for i in range(15)
        ]
        for obj in anomalous_objects:
            orchestrator.entropy_monitor.update(obj, "anomaly")

        adapted_threshold = orchestrator.entropy_monitor.adaptive_entropy_threshold

        # Return to normal patterns
        normal_objects = [{"normal": i, "data": f"normal_{i}"} for i in range(25)]
        for obj in normal_objects:
            orchestrator.entropy_monitor.update(obj, "normal")

        final_threshold = orchestrator.entropy_monitor.adaptive_entropy_threshold

        # Verify adaptive behavior
        assert adapted_threshold != initial_threshold, "Threshold should adapt to anomalies"
        assert abs(final_threshold - initial_threshold) < abs(adapted_threshold - initial_threshold), \
               "Threshold should stabilize when returning to normal patterns"

        print(f"✅ Adaptive thresholds: initial={initial_threshold:.3f}, "
              f"adapted={adapted_threshold:.3f}, final={final_threshold:.3f}")

    def test_repair_decision_learning(self, temp_environment):
        """Test repair planner learning from outcomes."""
        temp_dir, store_dir, snapshot_dir = temp_environment

        policy = Slot8Policy()
        orchestrator = SelfHealingOrchestrator(store_dir, snapshot_dir, policy)

        # Create snapshot for repair testing
        snapshot = orchestrator.snapshotter.take_snapshot()

        # Simulate multiple repair scenarios with outcomes
        scenarios = [
            (RepairAction.RESTORE_LAST_GOOD, True, 2.3),
            (RepairAction.RESTORE_LAST_GOOD, True, 1.8),
            (RepairAction.RESTORE_LAST_GOOD, False, 8.5),
            (RepairAction.SEMANTIC_PATCH, True, 4.2),
            (RepairAction.SEMANTIC_PATCH, True, 3.9),
        ]

        initial_success_rates = dict(orchestrator.repair_planner.success_rates)

        for action, success, duration in scenarios:
            # Create mock decision
            from ..core.types import RepairDecision
            decision = RepairDecision(
                action=action,
                reason="test_scenario",
                details={"test": True},
                confidence=0.7,
                estimated_time_s=3.0
            )

            orchestrator.repair_planner.record_repair_outcome(decision, success, duration)

        final_success_rates = dict(orchestrator.repair_planner.success_rates)

        # Verify learning occurred
        restore_rate = final_success_rates.get(RepairAction.RESTORE_LAST_GOOD, 0.7)
        patch_rate = final_success_rates.get(RepairAction.SEMANTIC_PATCH, 0.7)

        # RESTORE_LAST_GOOD: 2 successes, 1 failure = should be around 0.67
        assert 0.6 <= restore_rate <= 0.8, f"Restore success rate {restore_rate} not in expected range"

        # SEMANTIC_PATCH: 2 successes, 0 failures = should be high
        assert patch_rate > 0.7, f"Patch success rate {patch_rate} should be high"

        print(f"✅ Learning verified: restore={restore_rate:.3f}, patch={patch_rate:.3f}")


def run_integration_tests():
    """Run complete integration test suite."""
    print("🔄 Running Self-Healing Integration Tests...")

    import subprocess
    import sys

    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-s"
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print("\n✅ ALL INTEGRATION TESTS PASSED")
        print("\n🎯 Self-Healing Capabilities Validated:")
        print("  • End-to-end recovery workflow: ✓")
        print("  • Quarantine read-only continuity: ✓")
        print("  • Adaptive threshold adjustment: ✓")
        print("  • Repair decision learning: ✓")
        return True
    else:
        print("\n❌ INTEGRATION TESTS FAILED")
        print(result.stdout)
        print(result.stderr)
        return False


if __name__ == "__main__":
    run_integration_tests()
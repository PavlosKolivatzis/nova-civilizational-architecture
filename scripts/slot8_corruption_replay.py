#!/usr/bin/env python3
"""Chaos testing script for Slot 8 corruption scenarios.

Performs controlled corruption scenarios to validate self-healing capabilities.
"""

import argparse
import asyncio
import random
import time
import tempfile
import shutil
from pathlib import Path
import sys

# Add slot08 to path for imports
script_dir = Path(__file__).parent
slot08_dir = script_dir.parent / "slots" / "slot08_memory_lock"
sys.path.insert(0, str(slot08_dir))

try:
    from core.policy import Slot8Policy
    from core.snapshotter import IntegritySnapshotter
    from core.repair_planner import RepairPlanner
    from core.quarantine import QuarantineSystem
    from core.metrics import get_metrics_collector
    from core.types import HealthMetrics, RepairAction, QuarantineReason, ThreatLevel
except ImportError as e:
    print(f"❌ Failed to import Slot 8 components: {e}")
    print("Make sure you're running from the repo root directory")
    sys.exit(1)


class ChaosTestHarness:
    """Harness for controlled chaos testing of Slot 8 self-healing."""

    def __init__(self, budget_seconds: int = 15):
        self.budget_seconds = budget_seconds
        self.temp_dir = None
        self.store_dir = None
        self.snapshot_dir = None
        self.policy = None
        self.snapshotter = None
        self.repair_planner = None
        self.quarantine = None
        self.metrics = get_metrics_collector()

    def setup(self):
        """Setup test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="slot8_chaos_"))
        self.store_dir = self.temp_dir / "store"
        self.snapshot_dir = self.temp_dir / "snapshots"

        self.store_dir.mkdir(parents=True)
        self.snapshot_dir.mkdir(parents=True)

        # Configure for fast testing
        self.policy = Slot8Policy(
            mttr_target_s=2.0,  # Fast recovery for testing
            quarantine_flip_max_s=0.5,
            max_repair_attempts=2
        )

        self.snapshotter = IntegritySnapshotter(
            self.store_dir, self.snapshot_dir, policy=self.policy
        )
        self.repair_planner = RepairPlanner(self.policy)
        self.quarantine = QuarantineSystem(self.policy.quarantine_policy)

        print(f"[CHAOS] Test environment setup in {self.temp_dir}")

    def teardown(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print(f"[CLEANUP] Cleaned up {self.temp_dir}")

    def create_test_store(self, file_count: int = 20):
        """Create test files in the store."""
        for i in range(file_count):
            test_file = self.store_dir / f"test_{i:03d}.json"
            test_data = {
                "id": i,
                "data": f"test_content_{i}",
                "timestamp": time.time(),
                "checksum": f"sha256_placeholder_{i}"
            }
            test_file.write_text(str(test_data))

        print(f"[FILES] Created {file_count} test files")

    async def scenario_bitflip(self) -> dict:
        """Test recovery from bit corruption."""
        print("[BITFLIP] Starting bitflip corruption scenario...")
        start_time = time.time()

        # Create baseline and snapshot
        self.create_test_store(15)
        baseline_snapshot = self.snapshotter.take_snapshot()
        print(f"📸 Baseline snapshot: {baseline_snapshot.id}")

        # Introduce bit corruption
        test_files = list(self.store_dir.glob("*.json"))
        if test_files:
            corrupt_file = random.choice(test_files)
            content = corrupt_file.read_bytes()

            # Flip random bits
            if content:
                corrupted = bytearray(content)
                for _ in range(min(3, len(corrupted))):  # Flip up to 3 bits
                    bit_pos = random.randint(0, len(corrupted) - 1)
                    corrupted[bit_pos] ^= random.randint(1, 255)

                corrupt_file.write_bytes(bytes(corrupted))
                print(f"💥 Corrupted {corrupt_file.name} with bit flips")

        # Detect corruption and measure recovery
        recovery_start = time.time()
        health_metrics = HealthMetrics(
            corruption_detected=True,
            tamper_evidence=False,
            checksum_mismatch=True,
            semantic_inversion=False,
            integrity_score=0.4,
            entropy_score=0.3,
            last_snapshot_age_s=5,
            repair_attempts=0,
            quarantine_active=False
        )

        # Get repair decision
        snapshots = self.snapshotter.list_snapshots()
        decision = self.repair_planner.decide_repair_strategy(
            health_metrics, snapshots, {"corruption_type": "bitflip"}
        )

        # Execute repair
        success = False
        if decision.action == RepairAction.RESTORE_LAST_GOOD:
            success = self.snapshotter.restore_from_snapshot(baseline_snapshot.id)

        recovery_time = time.time() - recovery_start
        total_time = time.time() - start_time

        # Record metrics
        self.metrics.record_recovery_mttr(recovery_time, {"scenario": "bitflip"})
        self.metrics.record_repair_outcome(decision.action.value, success, recovery_time)

        result = {
            "scenario": "bitflip",
            "success": success,
            "recovery_time_s": recovery_time,
            "total_time_s": total_time,
            "repair_action": decision.action.value,
            "mttr_slo_met": recovery_time <= self.policy.mttr_target_s
        }

        status = "✅ PASS" if success and result["mttr_slo_met"] else "❌ FAIL"
        print(f"{status} Bitflip scenario: {recovery_time:.2f}s recovery")

        return result

    async def scenario_truncate(self) -> dict:
        """Test recovery from file truncation."""
        print("✂️ Starting truncation corruption scenario...")
        start_time = time.time()

        # Create baseline and snapshot
        self.create_test_store(10)
        baseline_snapshot = self.snapshotter.take_snapshot()
        print(f"📸 Baseline snapshot: {baseline_snapshot.id}")

        # Truncate files
        test_files = list(self.store_dir.glob("*.json"))
        truncated_count = 0
        for test_file in random.sample(test_files, min(3, len(test_files))):
            content = test_file.read_text()
            if len(content) > 10:
                # Truncate to random position
                truncate_pos = random.randint(1, len(content) // 2)
                test_file.write_text(content[:truncate_pos])
                truncated_count += 1

        print(f"✂️ Truncated {truncated_count} files")

        # Activate quarantine for data protection
        quarantine_start = time.time()
        quarantine_success = self.quarantine.activate_quarantine(
            QuarantineReason.CORRUPTION_DETECTED,
            ThreatLevel.HIGH,
            {"scenario": "truncation"}
        )
        quarantine_time = time.time() - quarantine_start

        # Measure recovery
        recovery_start = time.time()
        success = self.snapshotter.restore_from_snapshot(baseline_snapshot.id)
        recovery_time = time.time() - recovery_start

        # Deactivate quarantine
        self.quarantine.deactivate_quarantine(manual_override=True)

        total_time = time.time() - start_time

        # Record metrics
        self.metrics.record_quarantine_state(False, quarantine_time)
        self.metrics.record_recovery_mttr(recovery_time, {"scenario": "truncate"})

        result = {
            "scenario": "truncate",
            "success": success and quarantine_success,
            "recovery_time_s": recovery_time,
            "quarantine_time_s": quarantine_time,
            "total_time_s": total_time,
            "quarantine_slo_met": quarantine_time <= self.policy.quarantine_flip_max_s,
            "mttr_slo_met": recovery_time <= self.policy.mttr_target_s
        }

        status = "✅ PASS" if (success and result["quarantine_slo_met"] and
                            result["mttr_slo_met"]) else "❌ FAIL"
        print(f"{status} Truncation scenario: {recovery_time:.2f}s recovery, "
              f"{quarantine_time:.3f}s quarantine")

        return result

    async def run_scenarios(self, scenarios: list) -> dict:
        """Run specified chaos scenarios within time budget."""
        print(f"🎯 Running chaos scenarios: {scenarios}")
        print(f"⏱️ Time budget: {self.budget_seconds}s")

        start_time = time.time()
        results = []

        for scenario in scenarios:
            elapsed = time.time() - start_time
            if elapsed >= self.budget_seconds:
                print("⏰ Time budget exceeded, stopping scenarios")
                break

            if scenario == "bitflip":
                result = await self.scenario_bitflip()
            elif scenario == "truncate":
                result = await self.scenario_truncate()
            else:
                print(f"❓ Unknown scenario: {scenario}")
                continue

            results.append(result)

            # Brief pause between scenarios
            await asyncio.sleep(0.5)

        total_time = time.time() - start_time
        success_count = sum(1 for r in results if r["success"])

        summary = {
            "total_scenarios": len(results),
            "successful_scenarios": success_count,
            "total_time_s": total_time,
            "within_budget": total_time <= self.budget_seconds,
            "results": results
        }

        return summary


async def main():
    """Main chaos testing entry point."""
    parser = argparse.ArgumentParser(description="Slot 8 chaos corruption testing")
    parser.add_argument("--scenarios", nargs="+", choices=["bitflip", "truncate"],
                       default=["bitflip", "truncate"],
                       help="Corruption scenarios to test")
    parser.add_argument("--budget-sec", type=int, default=15,
                       help="Time budget in seconds")

    args = parser.parse_args()

    print("🧪 Slot 8 Chaos Corruption Replay")
    print("=" * 40)

    harness = ChaosTestHarness(budget_seconds=args.budget_sec)

    try:
        harness.setup()
        summary = await harness.run_scenarios(args.scenarios)

        print("\n📊 Chaos Test Summary")
        print("=" * 40)
        print(f"Scenarios run: {summary['total_scenarios']}")
        print(f"Successful: {summary['successful_scenarios']}")
        print(f"Total time: {summary['total_time_s']:.2f}s")
        print(f"Within budget: {'✅' if summary['within_budget'] else '❌'}")

        for result in summary['results']:
            print(f"  {result['scenario']}: "
                  f"{'✅' if result['success'] else '❌'} "
                  f"({result.get('recovery_time_s', 0):.2f}s)")

        # Exit with error if any scenario failed
        if summary['successful_scenarios'] < summary['total_scenarios']:
            print("\n❌ Some scenarios failed - check self-healing implementation")
            sys.exit(1)
        else:
            print("\n✅ All chaos scenarios passed - self-healing operational")

    except Exception as e:
        print(f"\n💥 Chaos test failed with exception: {e}")
        sys.exit(1)
    finally:
        harness.teardown()


if __name__ == "__main__":
    asyncio.run(main())
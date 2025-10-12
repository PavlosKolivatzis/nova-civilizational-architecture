#!/usr/bin/env python3
"""Simple chaos testing for Slot 8 corruption scenarios."""

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

from nova.slots.slot08_memory_lock.core.policy import Slot8Policy
from nova.slots.slot08_memory_lock.core.snapshotter import IntegritySnapshotter


def test_bitflip_recovery():
    """Test recovery from bit corruption."""
    print("[BITFLIP] Starting corruption test...")

    # Setup
    temp_dir = Path(tempfile.mkdtemp(prefix="slot8_chaos_"))
    store_dir = temp_dir / "store"
    snapshot_dir = temp_dir / "snapshots"
    store_dir.mkdir(parents=True)
    snapshot_dir.mkdir(parents=True)

    try:
        # Create test environment
        policy = Slot8Policy(mttr_target_s=2.0)
        snapshotter = IntegritySnapshotter(store_dir, snapshot_dir, policy=policy)

        # Create test files
        for i in range(5):
            test_file = store_dir / f"test_{i}.json"
            test_file.write_text(f'{{"id": {i}, "data": "test_content_{i}"}}')

        print("[SNAPSHOT] Creating baseline...")
        baseline = snapshotter.take_snapshot()

        # Corrupt a file
        test_files = list(store_dir.glob("*.json"))
        if test_files:
            corrupt_file = test_files[0]
            corrupt_file.write_text("CORRUPTED_DATA")
            print(f"[CORRUPT] Corrupted {corrupt_file.name}")

        # Test recovery
        start_time = time.time()
        success = snapshotter.restore_from_snapshot(baseline.id)
        recovery_time = time.time() - start_time

        slo_met = recovery_time <= policy.mttr_target_s
        status = "[PASS]" if success and slo_met else "[FAIL]"

        print(f"{status} Recovery: {recovery_time:.2f}s (SLO: {policy.mttr_target_s}s)")

        return success and slo_met

    finally:
        shutil.rmtree(temp_dir)
        print("[CLEANUP] Done")

def main():
    parser = argparse.ArgumentParser(description="Simple Slot 8 chaos test")
    parser.add_argument("--scenarios", nargs="+", choices=["bitflip", "truncate"],
                       default=["bitflip"], help="Test scenarios")
    parser.add_argument("--budget-sec", type=int, default=15, help="Time budget")

    args = parser.parse_args()

    print("Slot 8 Chaos Test")
    print("=" * 20)

    success = True
    for scenario in args.scenarios:
        if scenario == "bitflip":
            success &= test_bitflip_recovery()

    if success:
        print("[PASS] All tests passed")
        sys.exit(0)
    else:
        print("[FAIL] Some tests failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
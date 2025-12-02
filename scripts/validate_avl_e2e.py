#!/usr/bin/env python3
"""E2E Validation Script for AVL - Phase 13

Runs all 20 trajectories through ORP + AVL and validates:
1. Ledger integrity (hash chain)
2. Zero drift on canonical trajectories
3. All continuity proofs pass

Usage:
    python scripts/validate_avl_e2e.py
    python scripts/validate_avl_e2e.py --trajectory canonical_normal_to_heightened.json
"""

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nova.continuity.operational_regime import (
    OperationalRegimePolicy,
    ContributingFactors,
    reset_orp_engine,
)
from src.nova.continuity.avl_ledger import (
    AVLLedger,
    AVLEntry,
    reset_avl_ledger,
)
from src.nova.continuity.drift_guard import DriftGuard, reset_drift_guard
from src.nova.continuity.continuity_proof import ContinuityProof
from src.nova.continuity.contract_oracle import compute_and_classify

# Trajectory directory
TRAJECTORY_DIR = Path(__file__).parent.parent / "tests" / "e2e" / "trajectories"


def load_trajectory(path: Path) -> Dict[str, Any]:
    """Load trajectory from JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def run_trajectory_through_avl(
    trajectory: Dict[str, Any],
    ledger_path: str,
) -> Tuple[AVLLedger, List[Dict[str, Any]]]:
    """Run trajectory through ORP + AVL.

    Returns:
        Tuple of (AVLLedger, list of step results)
    """
    # Reset singletons
    reset_orp_engine()
    reset_avl_ledger()
    reset_drift_guard()

    # Create fresh ORP and AVL
    orp = OperationalRegimePolicy()
    ledger = AVLLedger(ledger_path)
    drift_guard = DriftGuard(halt_on_drift=False)

    steps = trajectory.get("steps", [])
    results = []

    for i, step in enumerate(steps):
        # Extract factors
        factors = ContributingFactors(
            urf_composite_risk=step.get("urf_composite_risk", 0.0),
            mse_meta_instability=step.get("mse_meta_instability", 0.0),
            predictive_collapse_risk=step.get("predictive_collapse_risk", 0.0),
            consistency_gap=step.get("consistency_gap", 0.0),
            csi_continuity_index=step.get("csi_continuity_index", 1.0),
        )

        # Get timestamp
        timestamp = step.get("timestamp", f"2025-01-01T12:{i:02d}:00+00:00")

        # Evaluate ORP
        snapshot = orp.evaluate(factors=factors, timestamp=timestamp)

        # Get oracle verification
        state = orp.get_state()
        oracle_result = compute_and_classify(
            factors.to_dict(),
            current_regime=state.current_regime.value,
            time_in_regime_s=state.time_in_regime_s,
        )

        # Create AVL entry
        entry = AVLEntry(
            timestamp=timestamp,
            elapsed_s=float(i * 60),  # Assume 1 minute per step
            orp_regime=snapshot.regime.value,
            orp_regime_score=snapshot.regime_score,
            contributing_factors=factors.to_dict(),
            posture_adjustments=snapshot.posture_adjustments.to_dict(),
            oracle_regime=oracle_result["regime"],
            oracle_regime_score=oracle_result["regime_score"],
            dual_modality_agreement=(snapshot.regime.value == oracle_result["regime"]),
            transition_from=snapshot.transition_from.value if snapshot.transition_from else None,
            time_in_previous_regime_s=snapshot.time_in_regime_s,
            hysteresis_enforced=True,
            min_duration_enforced=True,
            ledger_continuity=True,
            amplitude_valid=True,
            node_id="e2e-validator",
            orp_version="phase13.1",
        )

        # Run drift guard
        entry = drift_guard.check_and_update(entry)

        # Append to ledger
        ledger.append(entry)

        results.append({
            "step": i,
            "timestamp": timestamp,
            "orp_regime": snapshot.regime.value,
            "oracle_regime": oracle_result["regime"],
            "drift_detected": entry.drift_detected,
            "drift_reasons": entry.drift_reasons,
        })

    return ledger, results


def validate_ledger(ledger: AVLLedger) -> Dict[str, Any]:
    """Validate ledger integrity and continuity proofs.

    Returns:
        Validation results dict
    """
    results = {
        "hash_chain_valid": False,
        "hash_chain_violations": [],
        "entry_ids_valid": False,
        "entry_id_violations": [],
        "proofs": {},
        "all_passed": False,
    }

    # Hash chain
    is_valid, violations = ledger.verify_hash_chain()
    results["hash_chain_valid"] = is_valid
    results["hash_chain_violations"] = violations

    # Entry IDs
    is_valid, violations = ledger.verify_entry_ids()
    results["entry_ids_valid"] = is_valid
    results["entry_id_violations"] = violations

    # Continuity proofs
    proof = ContinuityProof()
    entries = ledger.get_entries()
    proof_results = proof.prove_all(entries)

    results["proofs"] = {
        name: {
            "passed": r.passed,
            "violations": r.violations,
            "entries_checked": r.entries_checked,
        }
        for name, r in proof_results.items()
    }

    # Overall
    results["all_passed"] = (
        results["hash_chain_valid"]
        and results["entry_ids_valid"]
        and all(r.passed for r in proof_results.values())
    )

    return results


def run_all_trajectories(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Run all 20 trajectories and collect results.

    Returns:
        Summary dict with all results
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="avl_e2e_")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    trajectory_files = sorted(TRAJECTORY_DIR.glob("*.json"))

    summary = {
        "total_trajectories": len(trajectory_files),
        "passed": 0,
        "failed": 0,
        "drift_events": 0,
        "total_entries": 0,
        "trajectories": {},
    }

    for traj_file in trajectory_files:
        print(f"Processing {traj_file.name}...")

        try:
            trajectory = load_trajectory(traj_file)
            ledger_path = str(output_path / f"{traj_file.stem}_ledger.jsonl")

            # Run trajectory
            ledger, step_results = run_trajectory_through_avl(trajectory, ledger_path)

            # Validate
            validation = validate_ledger(ledger)

            # Count drift events
            drift_count = sum(1 for r in step_results if r["drift_detected"])

            # Record results
            traj_result = {
                "entries": len(ledger),
                "drift_events": drift_count,
                "validation": validation,
                "passed": validation["all_passed"] and drift_count == 0,
            }

            summary["trajectories"][traj_file.name] = traj_result
            summary["total_entries"] += len(ledger)
            summary["drift_events"] += drift_count

            if traj_result["passed"]:
                summary["passed"] += 1
                print(f"  [PASS] ({len(ledger)} entries, {drift_count} drift)")
            else:
                summary["failed"] += 1
                print(f"  [FAIL] ({len(ledger)} entries, {drift_count} drift)")
                if not validation["all_passed"]:
                    for name, proof in validation["proofs"].items():
                        if not proof["passed"]:
                            print(f"    - {name}: {proof['violations'][:2]}")

        except Exception as e:
            print(f"  [ERROR] {e}")
            summary["trajectories"][traj_file.name] = {
                "error": str(e),
                "passed": False,
            }
            summary["failed"] += 1

    return summary


def main():
    parser = argparse.ArgumentParser(description="E2E AVL Validation")
    parser.add_argument(
        "--trajectory",
        type=str,
        help="Run single trajectory (filename)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for ledger files",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    if args.trajectory:
        # Single trajectory
        traj_path = TRAJECTORY_DIR / args.trajectory
        if not traj_path.exists():
            print(f"Trajectory not found: {traj_path}")
            sys.exit(1)

        trajectory = load_trajectory(traj_path)
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            ledger_path = f.name

        ledger, step_results = run_trajectory_through_avl(trajectory, ledger_path)
        validation = validate_ledger(ledger)

        if args.json:
            print(json.dumps({
                "trajectory": args.trajectory,
                "entries": len(ledger),
                "step_results": step_results,
                "validation": validation,
            }, indent=2))
        else:
            print(f"\nTrajectory: {args.trajectory}")
            print(f"Entries: {len(ledger)}")
            print(f"Hash chain valid: {validation['hash_chain_valid']}")
            print(f"Entry IDs valid: {validation['entry_ids_valid']}")
            print("\nContinuity Proofs:")
            for name, proof in validation["proofs"].items():
                status = "[PASS]" if proof["passed"] else "[FAIL]"
                print(f"  {status} {name}")
            print(f"\nOverall: {'PASSED' if validation['all_passed'] else 'FAILED'}")

    else:
        # All trajectories
        summary = run_all_trajectories(args.output_dir)

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("\n" + "=" * 60)
            print("E2E AVL Validation Summary")
            print("=" * 60)
            print(f"Total trajectories: {summary['total_trajectories']}")
            print(f"Passed: {summary['passed']}")
            print(f"Failed: {summary['failed']}")
            print(f"Total entries: {summary['total_entries']}")
            print(f"Drift events: {summary['drift_events']}")
            print("=" * 60)

            if summary["failed"] > 0:
                print("\nFailed trajectories:")
                for name, result in summary["trajectories"].items():
                    if not result.get("passed", False):
                        print(f"  - {name}")
                sys.exit(1)
            else:
                print("\n[PASS] All trajectories passed!")
                sys.exit(0)


if __name__ == "__main__":
    main()

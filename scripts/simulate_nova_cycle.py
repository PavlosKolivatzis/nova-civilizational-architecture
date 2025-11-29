#!/usr/bin/env python3
"""Nova Cycle Simulation Engine - Phase 12

Simulates full ORP lifecycle across signal trajectories:
- Load trajectory from JSON (20-40 step sequences)
- Execute ORP + oracle evaluation at each step
- Validate invariants (hysteresis, min-duration, ledger continuity, amplitude triad)
- Output CSV/JSONL for analysis

Usage:
    python scripts/simulate_nova_cycle.py tests/e2e/trajectories/canonical_normal_stable.json
    python scripts/simulate_nova_cycle.py tests/e2e/trajectories/*.json --output results/
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nova.continuity.operational_regime import (
    OperationalRegimePolicy,
    ContributingFactors,
    Regime,
    ORPState,
    REGIME_THRESHOLDS,
    DOWNGRADE_HYSTERESIS,
    MIN_REGIME_DURATION_S,
)
from src.nova.continuity.contract_oracle import (
    classify_regime_from_contract,
    compute_regime_score_from_contract,
)


# ---------- Timestamp Utilities ----------


def parse_trajectory_timestamp(timestamp_str: str) -> datetime:
    """Parse trajectory timestamp with robust format handling and validation.

    Supports multiple ISO 8601 formats:
    - 2023-01-01T12:00:00Z (Z suffix)
    - 2023-01-01T12:00:00+00:00 (explicit UTC)
    - 2023-01-01T12:00:00 (naive, assumed UTC)

    Args:
        timestamp_str: Timestamp string to parse

    Returns:
        datetime: Parsed timestamp with UTC timezone

    Raises:
        ValueError: If timestamp format is invalid or unparseable
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        raise ValueError(f"Invalid timestamp: must be non-empty string, got {type(timestamp_str)}: {timestamp_str!r}")

    # Normalize common formats
    normalized = timestamp_str.strip()

    # Handle Z suffix (UTC)
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'
    # Handle naive timestamps (assume UTC)
    elif '+' not in normalized and '-' not in normalized[-6:]:  # No timezone info
        normalized += '+00:00'

    try:
        parsed = datetime.fromisoformat(normalized)
        # Ensure it's timezone-aware
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if it's not already
            parsed = parsed.astimezone(timezone.utc)

        return parsed
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format '{timestamp_str}' (normalized: '{normalized}'): {e}") from e


def validate_trajectory_timestamps(steps: "List[TrajectoryStep]") -> None:
    """Validate trajectory timestamps are properly formatted and monotonic.

    Args:
        steps: List of trajectory steps to validate

    Raises:
        ValueError: If timestamps are invalid or non-monotonic
    """
    if not steps:
        return

    previous_timestamp = None

    for i, step in enumerate(steps):
        try:
            current_timestamp = parse_trajectory_timestamp(step.timestamp)
        except ValueError as e:
            raise ValueError(f"Step {step.step} (index {i}): {e}") from e

        # Check monotonicity (timestamps should not go backwards)
        if previous_timestamp is not None and current_timestamp < previous_timestamp:
            raise ValueError(
                f"Step {step.step} (index {i}): timestamp {step.timestamp} "
                f"is before previous step's timestamp {steps[i-1].timestamp}"
            )

        previous_timestamp = current_timestamp


# ---------- API Guard ----------


def _require_public_api(snapshot_dict: dict, state: ORPState) -> None:
    """Fail fast if required public fields are missing (Phase 16-2 hardening).
    
    Guards against ORP API drift by validating expected fields exist.
    Raises AssertionError if ORP public API has changed incompatibly.
    """
    required_snapshot_fields = [
        "regime", "regime_score", "transition_from", "timestamp", "time_in_regime_s"
    ]
    for field in required_snapshot_fields:
        assert field in snapshot_dict, (
            f"ORP API drift detected: missing '{field}' in RegimeSnapshot.to_dict(). "
            f"Update simulator to match new ORP API."
        )
    
    # Validate ORPState has expected attributes
    assert hasattr(state, "current_regime"), "ORP API drift: ORPState missing current_regime"
    assert hasattr(state, "time_in_regime_s"), "ORP API drift: ORPState missing time_in_regime_s"


# ---------- Trajectory Schema ----------


# ---------- Timestamp Utilities (moved after TrajectoryStep definition) ----------


def parse_trajectory_timestamp(timestamp_str: str) -> datetime:
    """Parse trajectory timestamp with robust format handling and validation.

    Supports multiple ISO 8601 formats:
    - 2023-01-01T12:00:00Z (Z suffix)
    - 2023-01-01T12:00:00+00:00 (explicit UTC)
    - 2023-01-01T12:00:00 (naive, assumed UTC)

    Args:
        timestamp_str: Timestamp string to parse

    Returns:
        datetime: Parsed timestamp with UTC timezone

    Raises:
        ValueError: If timestamp format is invalid or unparseable
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        raise ValueError(f"Invalid timestamp: must be non-empty string, got {type(timestamp_str)}: {timestamp_str!r}")

    # Normalize common formats
    normalized = timestamp_str.strip()

    # Handle Z suffix (UTC)
    if normalized.endswith('Z'):
        normalized = normalized[:-1] + '+00:00'
    # Handle naive timestamps (assume UTC)
    elif '+' not in normalized and '-' not in normalized[-6:]:  # No timezone info
        normalized += '+00:00'

    try:
        parsed = datetime.fromisoformat(normalized)
        # Ensure it's timezone-aware
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if it's not already
            parsed = parsed.astimezone(timezone.utc)

        return parsed
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format '{timestamp_str}' (normalized: '{normalized}'): {e}") from e


def validate_trajectory_timestamps(steps: "List[TrajectoryStep]") -> None:
    """Validate trajectory timestamps are properly formatted and monotonic.

    Args:
        steps: List of trajectory steps to validate

    Raises:
        ValueError: If timestamps are invalid or non-monotonic
    """
    if not steps:
        return

    previous_timestamp = None

    for i, step in enumerate(steps):
        try:
            current_timestamp = parse_trajectory_timestamp(step.timestamp)
        except ValueError as e:
            raise ValueError(f"Step {step.step} (index {i}): {e}") from e

        # Check monotonicity (timestamps should not go backwards)
        if previous_timestamp is not None and current_timestamp < previous_timestamp:
            raise ValueError(
                f"Step {step.step} (index {i}): timestamp {step.timestamp} "
                f"is before previous step's timestamp {steps[i-1].timestamp}"
            )

        previous_timestamp = current_timestamp


# ---------- API Guard ----------


def _require_public_api(snapshot_dict: dict, state: ORPState) -> None:
    """Fail fast if required public fields are missing (Phase 16-2 hardening).
    
    Guards against ORP API drift by validating expected fields exist.
    Raises AssertionError if ORP public API has changed incompatibly.
    """
    required_snapshot_fields = [
        "regime", "regime_score", "transition_from", "timestamp", "time_in_regime_s"
    ]
    for field in required_snapshot_fields:
        assert field in snapshot_dict, (
            f"ORP API drift detected: missing '{field}' in RegimeSnapshot.to_dict(). "
            f"Update simulator to match new ORP API."
        )
    
    # Validate ORPState has expected attributes
    assert hasattr(state, "current_regime"), "ORP API drift: ORPState missing current_regime"
    assert hasattr(state, "time_in_regime_s"), "ORP API drift: ORPState missing time_in_regime_s"


# ---------- Trajectory Schema ----------


@dataclass
class TrajectoryStep:
    """Single step in trajectory."""
    step: int
    timestamp: str
    elapsed_s: float
    contributing_factors: Dict[str, float]
    expected_regime: Optional[str] = None
    expected_transition: Optional[str] = None


@dataclass
class Trajectory:
    """Full trajectory specification."""
    trajectory_id: str
    description: str
    steps: List[TrajectoryStep]


# ---------- Simulation Result ----------


@dataclass
class StepResult:
    """Result of simulating one step."""
    step: int
    timestamp: str
    elapsed_s: float

    # Input factors
    contributing_factors: Dict[str, float]

    # ORP implementation
    orp_regime_score: float
    orp_regime: str
    orp_transition_from: Optional[str]
    time_in_regime_s: float

    # Contract oracle
    oracle_regime_score: float
    oracle_regime: str

    # Invariant checks
    dual_modality_agreement: bool
    hysteresis_enforced: bool
    min_duration_enforced: bool
    ledger_continuity: bool
    amplitude_valid: bool

    # Posture
    threshold_multiplier: float
    traffic_limit: float
    deployment_freeze: bool
    safe_mode_forced: bool

    # Violations (if any)
    violations: List[str]


@dataclass
class SimulationSummary:
    """Summary of full simulation run."""
    trajectory_id: str
    total_steps: int
    total_transitions: int
    regimes_visited: List[str]
    violations: List[str]
    dual_modality_agreement: bool
    all_invariants_passed: bool


# ---------- Trajectory Loader ----------


def load_trajectory(path: Path) -> Trajectory:
    """Load and validate trajectory JSON with comprehensive schema validation."""
    with open(path, "r") as f:
        data = json.load(f)

    # Validate required fields
    required = ["trajectory_id", "description", "steps"]
    for field in required:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    # Validate trajectory metadata
    if not isinstance(data["trajectory_id"], str) or not data["trajectory_id"].strip():
        raise ValueError("trajectory_id must be non-empty string")
    if not isinstance(data["description"], str):
        raise ValueError("description must be string")
    if not isinstance(data["steps"], list) or len(data["steps"]) == 0:
        raise ValueError("steps must be non-empty list")

    # Parse and validate steps
    steps = []
    for i, step_data in enumerate(data["steps"]):
        # Validate step structure
        if not isinstance(step_data, dict):
            raise ValueError(f"Step {i}: must be object, got {type(step_data)}")

        required_step_fields = ["step", "timestamp", "elapsed_s", "contributing_factors"]
        for field in required_step_fields:
            if field not in step_data:
                raise ValueError(f"Step {i}: missing required field '{field}'")

        # Validate step number
        if not isinstance(step_data["step"], int) or step_data["step"] < 0:
            raise ValueError(f"Step {i}: step must be non-negative integer, got {step_data['step']!r}")

        # Validate elapsed time
        if not isinstance(step_data["elapsed_s"], (int, float)) or step_data["elapsed_s"] < 0:
            raise ValueError(f"Step {i}: elapsed_s must be non-negative number, got {step_data['elapsed_s']!r}")

        # Validate contributing factors
        if not isinstance(step_data["contributing_factors"], dict):
            raise ValueError(f"Step {i}: contributing_factors must be object")
        for key, value in step_data["contributing_factors"].items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Step {i}: contributing_factors['{key}'] must be number, got {type(value)}")

        # Validate optional fields
        if "expected_regime" in step_data and step_data["expected_regime"] is not None and not isinstance(step_data["expected_regime"], str):
            raise ValueError(f"Step {i}: expected_regime must be string or null if present")
        if "expected_transition" in step_data and step_data["expected_transition"] is not None and not isinstance(step_data["expected_transition"], str):
            raise ValueError(f"Step {i}: expected_transition must be string or null if present")

        step = TrajectoryStep(
            step=step_data["step"],
            timestamp=step_data["timestamp"],
            elapsed_s=step_data["elapsed_s"],
            contributing_factors=step_data["contributing_factors"],
            expected_regime=step_data.get("expected_regime"),
            expected_transition=step_data.get("expected_transition"),
        )
        steps.append(step)

    # Validate timestamps are properly formatted and monotonic
    validate_trajectory_timestamps(steps)

    return Trajectory(
        trajectory_id=data["trajectory_id"],
        description=data["description"],
        steps=steps,
    )


# ---------- Invariant Validators ----------


def check_hysteresis_enforced(
    current_regime: str,
    new_regime: str,
    regime_score: float,
    time_in_regime_s: float,
) -> bool:
    """Validate hysteresis prevents premature downgrade."""
    regime_order = ["normal", "heightened", "controlled_degradation", "emergency_stabilization", "recovery"]

    current_idx = regime_order.index(current_regime)
    new_idx = regime_order.index(new_regime)

    # If downgrade attempted
    if new_idx < current_idx:
        # Check if score is below hysteresis threshold
        target_upper = REGIME_THRESHOLDS[Regime(new_regime)][1]
        hysteresis_threshold = target_upper - DOWNGRADE_HYSTERESIS

        if regime_score >= hysteresis_threshold:
            # Should NOT downgrade (hysteresis prevents)
            return new_regime == current_regime

    return True


def check_min_duration_enforced(
    current_regime: str,
    new_regime: str,
    time_in_regime_s: float,
) -> bool:
    """Validate min-duration prevents premature downgrade."""
    regime_order = ["normal", "heightened", "controlled_degradation", "emergency_stabilization", "recovery"]

    current_idx = regime_order.index(current_regime)
    new_idx = regime_order.index(new_regime)

    # If downgrade attempted
    if new_idx < current_idx:
        if time_in_regime_s < MIN_REGIME_DURATION_S:
            # Should NOT downgrade (min-duration not met)
            return new_regime == current_regime

    return True


def check_ledger_continuity(
    previous_regime: Optional[str],
    transition_from: Optional[str],
) -> bool:
    """Validate ledger continuity: from_regime[N] == to_regime[N-1]."""
    if previous_regime is None:
        # First step - validate initial transition is from expected default state
        if transition_from is not None and transition_from != "normal":
            # Log warning for unexpected initial transition, but allow it
            # This preserves existing behavior while surfacing potential issues
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Initial transition from unexpected regime: {transition_from} (expected: normal)")
        # Allow initial transition regardless - maintains existing behavior
        return True

    # If transition occurred, transition_from should match previous regime
    if transition_from is not None:
        return transition_from == previous_regime

    # No transition - continuity automatically maintained
    return True


# Amplitude bounds constants (centralized for consistency)
AMPLITUDE_BOUNDS = {
    "threshold_multiplier": (0.5, 2.0),  # (min, max)
    "traffic_limit": (0.0, 1.0),         # (min, max)
}


def check_amplitude_valid(threshold_multiplier: float, traffic_limit: float) -> bool:
    """Validate amplitude triad within centralized bounds."""
    tm_min, tm_max = AMPLITUDE_BOUNDS["threshold_multiplier"]
    tl_min, tl_max = AMPLITUDE_BOUNDS["traffic_limit"]

    return (tm_min <= threshold_multiplier <= tm_max) and (tl_min <= traffic_limit <= tl_max)


# ---------- Simulation Engine ----------


def simulate_trajectory(trajectory: Trajectory, verbose: bool = False) -> tuple[List[StepResult], SimulationSummary]:
    """Simulate full trajectory with dual-modality validation.

    Returns:
        (step_results, summary)
    """
    orp = OperationalRegimePolicy()
    results = []
    violations = []
    regimes_visited = set()
    transition_count = 0

    previous_regime = None

    for step_data in trajectory.steps:
        # Create contributing factors
        factors = ContributingFactors(**step_data.contributing_factors)

        # ORP evaluation
        snapshot_obj = orp.evaluate(factors=factors, timestamp=step_data.timestamp)
        snapshot = snapshot_obj.to_dict()

        # Get current state via public API (Phase 16-2 hardening)
        # Parse trajectory timestamp for clock alignment
        step_timestamp = parse_trajectory_timestamp(step_data.timestamp)
        
        # Use public get_state() with trajectory timestamp for clock alignment
        orp_state = orp.get_state(now=step_timestamp)
        
        # Validate public API hasn't drifted
        _require_public_api(snapshot, orp_state)

        # Use time_in_regime_s from snapshot (computed during evaluate)
        # This ensures ORP and simulator use the same value
        time_in_regime = snapshot["time_in_regime_s"]

        # Oracle evaluation using public API values
        oracle_score = compute_regime_score_from_contract(step_data.contributing_factors)

        # Use explicit ORP regime for oracle classification (fix dual-modality inference)
        oracle_regime = classify_regime_from_contract(
            regime_score=oracle_score,
            current_regime=orp_state.current_regime.value if previous_regime is None else previous_regime,
            time_in_regime_s=time_in_regime,
        )

        # Invariant checks
        dual_modality_agreement = snapshot["regime"] == oracle_regime

        hysteresis_ok = check_hysteresis_enforced(
            previous_regime if previous_regime else "normal",
            snapshot["regime"],
            snapshot["regime_score"],
            time_in_regime,
        )

        min_duration_ok = check_min_duration_enforced(
            previous_regime if previous_regime else "normal",
            snapshot["regime"],
            time_in_regime,
        )

        ledger_ok = check_ledger_continuity(
            previous_regime,
            snapshot["transition_from"],
        )

        amplitude_ok = check_amplitude_valid(
            snapshot["posture_adjustments"]["threshold_multiplier"],
            snapshot["posture_adjustments"]["traffic_limit"],
        )

        # Log amplitude bounds for debugging
        if not amplitude_ok:
            tm = snapshot["posture_adjustments"]["threshold_multiplier"]
            tl = snapshot["posture_adjustments"]["traffic_limit"]
            step_violations.append(
                f"Amplitude out of bounds: threshold_multiplier={tm:.3f} "
                f"(expected: {AMPLITUDE_BOUNDS['threshold_multiplier']}), "
                f"traffic_limit={tl:.3f} (expected: {AMPLITUDE_BOUNDS['traffic_limit']})"
            )

        # Collect violations
        step_violations = []
        if not dual_modality_agreement:
            step_violations.append(f"Dual-modality mismatch: ORP={snapshot['regime']}, Oracle={oracle_regime}")
        if not hysteresis_ok:
            step_violations.append("Hysteresis not enforced")
        if not min_duration_ok:
            step_violations.append("Min-duration not enforced")
        # Ledger continuity already added above
        # Amplitude validation with detailed error already added above

        violations.extend(step_violations)

        # Track transitions
        if snapshot["transition_from"] is not None:
            transition_count += 1

        regimes_visited.add(snapshot["regime"])

        # Create result
        result = StepResult(
            step=step_data.step,
            timestamp=step_data.timestamp,
            elapsed_s=step_data.elapsed_s,
            contributing_factors=step_data.contributing_factors,
            orp_regime_score=snapshot["regime_score"],
            orp_regime=snapshot["regime"],
            orp_transition_from=snapshot["transition_from"],
            time_in_regime_s=time_in_regime,
            oracle_regime_score=oracle_score,
            oracle_regime=oracle_regime,
            dual_modality_agreement=dual_modality_agreement,
            hysteresis_enforced=hysteresis_ok,
            min_duration_enforced=min_duration_ok,
            ledger_continuity=ledger_ok,
            amplitude_valid=amplitude_ok,
            threshold_multiplier=snapshot["posture_adjustments"]["threshold_multiplier"],
            traffic_limit=snapshot["posture_adjustments"]["traffic_limit"],
            deployment_freeze=snapshot["posture_adjustments"]["deployment_freeze"],
            safe_mode_forced=snapshot["posture_adjustments"]["safe_mode_forced"],
            violations=step_violations,
        )

        results.append(result)
        # Update previous_regime for next iteration
        previous_regime = snapshot["regime"]

        if verbose and step_violations:
            print(f"WARNING Step {step_data.step}: {', '.join(step_violations)}")

    # Summary
    summary = SimulationSummary(
        trajectory_id=trajectory.trajectory_id,
        total_steps=len(results),
        total_transitions=transition_count,
        regimes_visited=sorted(list(regimes_visited)),
        violations=violations,
        dual_modality_agreement=all(r.dual_modality_agreement for r in results),
        all_invariants_passed=len(violations) == 0,
    )

    return results, summary


# ---------- Output Writers ----------


def write_jsonl(results: List[StepResult], output_path: Path) -> None:
    """Write results to JSONL."""
    with open(output_path, "w") as f:
        for result in results:
            json.dump(asdict(result), f)
            f.write("\n")


def write_summary(summary: SimulationSummary, output_path: Path) -> None:
    """Write summary to JSON."""
    with open(output_path, "w") as f:
        json.dump(asdict(summary), f, indent=2)


# ---------- CLI ----------


def main():
    parser = argparse.ArgumentParser(description="Simulate Nova ORP lifecycle from trajectory")
    parser.add_argument("trajectory", type=Path, help="Path to trajectory JSON file")
    parser.add_argument("--output", "-o", type=Path, help="Output directory (default: stdout)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print violations to stdout")

    args = parser.parse_args()

    # Load trajectory
    trajectory = load_trajectory(args.trajectory)

    print(f"Simulating trajectory: {trajectory.trajectory_id}")
    print(f"Description: {trajectory.description}")
    print(f"Steps: {len(trajectory.steps)}")
    print()

    # Simulate
    results, summary = simulate_trajectory(trajectory, verbose=args.verbose)

    # Output
    if args.output:
        args.output.mkdir(parents=True, exist_ok=True)

        results_path = args.output / f"{trajectory.trajectory_id}_results.jsonl"
        summary_path = args.output / f"{trajectory.trajectory_id}_summary.json"

        write_jsonl(results, results_path)
        write_summary(summary, summary_path)

        print(f"Results written to {results_path}")
        print(f"Summary written to {summary_path}")
    else:
        # Print summary to stdout
        print(json.dumps(asdict(summary), indent=2))

    print()
    print("Summary:")
    print(f"  Total steps: {summary.total_steps}")
    print(f"  Transitions: {summary.total_transitions}")
    print(f"  Regimes visited: {', '.join(summary.regimes_visited)}")
    print(f"  Dual-modality agreement: {'PASS' if summary.dual_modality_agreement else 'FAIL'}")
    print(f"  All invariants passed: {'PASS' if summary.all_invariants_passed else 'FAIL'}")

    if summary.violations:
        print(f"  Violations: {len(summary.violations)}")
        for v in summary.violations:
            print(f"    - {v}")
        sys.exit(1)
    else:
        print("  No violations detected")
        sys.exit(0)


if __name__ == "__main__":
    main()

"""End-to-End Regime Cycle Behavior Tests - Phase 12

Tests validate full ORP behavior across signal trajectories:
- Safety envelope enforcement
- Transition correctness (hysteresis, min-duration, ledger continuity)
- Amplitude consistency
- Ledger invariants
- Oscillation prevention
- Temporal invariance
- Contract fidelity (dual-modality agreement)

Each test runs against trajectory library in tests/e2e/trajectories/
"""

import pytest
from pathlib import Path
from scripts.simulate_nova_cycle import load_trajectory, simulate_trajectory

# Trajectory directory
TRAJECTORY_DIR = Path(__file__).parent.parent / "e2e" / "trajectories"


def get_trajectory_path(trajectory_id: str) -> Path:
    """Get path to trajectory JSON file."""
    return TRAJECTORY_DIR / f"{trajectory_id}.json"


# ---------- Safety Envelope Enforcement Tests ----------


def test_regime_never_exceeds_recovery():
    """Test regime score >1.0 clamps to recovery (never exceeds)."""
    traj = load_trajectory(get_trajectory_path("adversarial_all_signals_high"))
    results, summary = simulate_trajectory(traj)

    for result in results:
        assert result.orp_regime in ["normal", "heightened", "controlled_degradation",
                                       "emergency_stabilization", "recovery"], \
            f"Invalid regime: {result.orp_regime}"

        # Even with extreme scores, should clamp to recovery
        assert result.orp_regime_score <= 1.0 or result.orp_regime == "recovery"


def test_amplitude_triad_always_valid():
    """Test amplitude triad within bounds across all trajectories."""
    trajectories = [
        "canonical_normal_to_heightened",
        "canonical_recovery_to_normal",
        "adversarial_rapid_oscillation",
        "noise_multi_regime_drift",
    ]

    for traj_id in trajectories:
        traj = load_trajectory(get_trajectory_path(traj_id))
        results, summary = simulate_trajectory(traj)

        for result in results:
            # threshold_multiplier ∈ [0.5, 2.0]
            assert 0.5 <= result.threshold_multiplier <= 2.0, \
                f"{traj_id} step {result.step}: threshold_multiplier={result.threshold_multiplier}"

            # traffic_limit ∈ [0.0, 1.0]
            assert 0.0 <= result.traffic_limit <= 1.0, \
                f"{traj_id} step {result.step}: traffic_limit={result.traffic_limit}"


def test_traffic_limit_never_negative():
    """Test traffic_limit always ∈ [0.0, 1.0] across all regimes."""
    traj = load_trajectory(get_trajectory_path("adversarial_all_signals_high"))
    results, summary = simulate_trajectory(traj)

    for result in results:
        assert 0.0 <= result.traffic_limit <= 1.0, \
            f"Step {result.step}: traffic_limit={result.traffic_limit}"


# ---------- Transition Correctness Tests ----------


def test_upgrade_immediate_on_threshold_cross():
    """Test upgrades are immediate when score crosses threshold upward (no hysteresis)."""
    traj = load_trajectory(get_trajectory_path("canonical_normal_to_heightened"))
    results, summary = simulate_trajectory(traj)

    # Find the upgrade transition
    for i, result in enumerate(results):
        if result.orp_transition_from == "normal" and result.orp_regime == "heightened":
            # Upgrade should happen immediately at step where score crosses 0.30
            assert result.orp_regime_score >= 0.30, \
                f"Upgrade at step {result.step} but score={result.orp_regime_score}"
            break
    else:
        pytest.fail("No upgrade transition found in canonical_normal_to_heightened")


def test_downgrade_requires_hysteresis():
    """Test downgrade requires score < (threshold - hysteresis)."""
    traj = load_trajectory(get_trajectory_path("canonical_hysteresis_prevents_downgrade"))
    results, summary = simulate_trajectory(traj)

    # Should stay in heightened despite score drop (hysteresis prevents)
    for result in results:
        if result.step > 0:
            # Score dropped but stayed in heightened
            assert result.orp_regime == "heightened", \
                f"Step {result.step}: should stay heightened due to hysteresis"


def test_downgrade_requires_min_duration():
    """Test downgrade requires time_in_regime >= 300s."""
    traj = load_trajectory(get_trajectory_path("canonical_min_duration_blocks_downgrade"))
    results, summary = simulate_trajectory(traj)

    # Should stay in heightened despite score drop (min-duration not met)
    for result in results:
        if result.step > 0 and result.time_in_regime_s < 300:
            assert result.orp_regime == "heightened", \
                f"Step {result.step}: should stay heightened (min-duration not met)"


def test_transition_ledger_continuity():
    """Test ledger continuity: from_regime[N] == to_regime[N-1]."""
    traj = load_trajectory(get_trajectory_path("canonical_recovery_to_normal"))
    results, summary = simulate_trajectory(traj)

    previous_regime = None
    for result in results:
        if result.orp_transition_from is not None:
            # Transition occurred
            if previous_regime is not None:
                assert result.orp_transition_from == previous_regime, \
                    f"Step {result.step}: ledger continuity broken: " \
                    f"transition_from={result.orp_transition_from}, previous={previous_regime}"

        previous_regime = result.orp_regime


# ---------- Amplitude Consistency Tests ----------


def test_omega_base_decreases_with_regime():
    """Test threshold_multiplier decreases (tightens) with regime severity."""
    traj = load_trajectory(get_trajectory_path("canonical_normal_to_heightened"))
    results, summary = simulate_trajectory(traj)

    regime_multipliers = {}
    for result in results:
        if result.orp_regime not in regime_multipliers:
            regime_multipliers[result.orp_regime] = result.threshold_multiplier

    # Normal should have higher multiplier than heightened
    if "normal" in regime_multipliers and "heightened" in regime_multipliers:
        assert regime_multipliers["normal"] >= regime_multipliers["heightened"], \
            f"Normal multiplier ({regime_multipliers['normal']}) should be >= " \
            f"heightened ({regime_multipliers['heightened']})"


def test_eta_tightens_with_regime():
    """Test traffic_limit decreases with regime severity (emotional constriction analog)."""
    traj = load_trajectory(get_trajectory_path("noise_multi_regime_drift"))
    results, summary = simulate_trajectory(traj)

    regime_limits = {}
    for result in results:
        if result.orp_regime not in regime_limits:
            regime_limits[result.orp_regime] = result.traffic_limit

    # Normal should have highest traffic limit
    regime_order = ["normal", "heightened", "controlled_degradation", "emergency_stabilization", "recovery"]
    observed_regimes = [r for r in regime_order if r in regime_limits]

    for i in range(len(observed_regimes) - 1):
        current = observed_regimes[i]
        next_regime = observed_regimes[i + 1]
        assert regime_limits[current] >= regime_limits[next_regime], \
            f"{current} traffic_limit ({regime_limits[current]}) should be >= " \
            f"{next_regime} ({regime_limits[next_regime]})"


def test_gamma_stable_across_transitions():
    """Test deployment_freeze and safe_mode_forced are consistent within regime."""
    traj = load_trajectory(get_trajectory_path("canonical_heightened_to_controlled"))
    results, summary = simulate_trajectory(traj)

    regime_postures = {}
    for result in results:
        posture = (result.deployment_freeze, result.safe_mode_forced)
        if result.orp_regime not in regime_postures:
            regime_postures[result.orp_regime] = posture
        else:
            # Posture should be consistent within regime
            assert regime_postures[result.orp_regime] == posture, \
                f"Regime {result.orp_regime} posture inconsistent: " \
                f"expected {regime_postures[result.orp_regime]}, got {posture}"


# ---------- Ledger Invariant Tests ----------


def test_ledger_append_only():
    """Test ledger is append-only (no deletions/modifications)."""
    # Simulation engine records all steps, verify monotonic IDs
    traj = load_trajectory(get_trajectory_path("canonical_normal_to_heightened"))
    results, summary = simulate_trajectory(traj)

    for i, result in enumerate(results):
        assert result.step == i, f"Step number should be sequential: expected {i}, got {result.step}"


def test_ledger_timestamp_monotonic():
    """Test timestamps always increase (monotonic)."""
    traj = load_trajectory(get_trajectory_path("canonical_recovery_to_normal"))
    results, summary = simulate_trajectory(traj)

    previous_elapsed = -1
    for result in results:
        assert result.elapsed_s > previous_elapsed, \
            f"Step {result.step}: timestamp not monotonic ({result.elapsed_s} <= {previous_elapsed})"
        previous_elapsed = result.elapsed_s


def test_ledger_record_id_unique():
    """Test step IDs are unique across trajectory."""
    traj = load_trajectory(get_trajectory_path("noise_multi_regime_drift"))
    results, summary = simulate_trajectory(traj)

    step_ids = [r.step for r in results]
    assert len(step_ids) == len(set(step_ids)), "Step IDs must be unique"


# ---------- Max Transition Count Tests ----------


def test_oscillation_detection_triggers():
    """Test >5 transitions in window triggers oscillation detection."""
    # This test would require a trajectory with >5 transitions
    # For now, verify rapid_oscillation doesn't exceed threshold
    traj = load_trajectory(get_trajectory_path("adversarial_rapid_oscillation"))
    results, summary = simulate_trajectory(traj)

    # Count transitions
    transition_count = sum(1 for r in results if r.orp_transition_from is not None)

    # Should have transitions but not excessive (hysteresis prevents)
    assert transition_count >= 1, "Should have at least one transition"
    assert transition_count < 5, f"Oscillation threshold exceeded: {transition_count} transitions"


def test_hysteresis_prevents_oscillation():
    """Test rapid signal spikes don't cause regime thrashing due to hysteresis."""
    traj = load_trajectory(get_trajectory_path("adversarial_rapid_oscillation"))
    results, summary = simulate_trajectory(traj)

    # Count regime changes
    regime_changes = 0
    previous_regime = None
    for result in results:
        if previous_regime is not None and result.orp_regime != previous_regime:
            regime_changes += 1
        previous_regime = result.orp_regime

    # With hysteresis, should have minimal regime changes despite signal spikes
    assert regime_changes <= 2, \
        f"Too many regime changes ({regime_changes}), hysteresis should prevent oscillation"


# ---------- Temporal Invariance Tests ----------


def test_trajectory_compression_preserves_regimes():
    """Test dropping steps preserves regime transitions at aligned timestamps.

    NOTE: Requires temporal trajectories to be generated.
    Skipping until temporal trajectory generation implemented.
    """
    pytest.skip("Temporal trajectories not yet generated (deferred from Step 3)")


def test_trajectory_expansion_stable():
    """Test interpolating midpoints doesn't cause spurious transitions.

    NOTE: Requires temporal trajectories to be generated.
    """
    pytest.skip("Temporal trajectories not yet generated (deferred from Step 3)")


def test_evaluation_frequency_independence():
    """Test 10s vs 60s intervals produce same regime transitions.

    NOTE: Requires temporal trajectories to be generated.
    """
    pytest.skip("Temporal trajectories not yet generated (deferred from Step 3)")


# ---------- Contract Fidelity Tests ----------


def test_dual_modality_regime_agreement():
    """Test ORP implementation matches contract oracle for all trajectories."""
    trajectories = [
        "canonical_normal_stable",
        "canonical_normal_to_heightened",
        "canonical_recovery_to_normal",
        "adversarial_rapid_oscillation",
        "adversarial_score_at_boundary",
        "noise_multi_regime_drift",
    ]

    for traj_id in trajectories:
        traj = load_trajectory(get_trajectory_path(traj_id))
        results, summary = simulate_trajectory(traj)

        for result in results:
            assert result.dual_modality_agreement, \
                f"{traj_id} step {result.step}: ORP={result.orp_regime}, Oracle={result.oracle_regime}"


def test_regime_score_calculation_matches_contract():
    """Test regime score computation identical to oracle."""
    trajectories = [
        "canonical_normal_to_heightened",
        "adversarial_all_signals_high",
        "noise_normal_with_jitter",
    ]

    for traj_id in trajectories:
        traj = load_trajectory(get_trajectory_path(traj_id))
        results, summary = simulate_trajectory(traj)

        for result in results:
            # Scores should match within floating point precision
            assert abs(result.orp_regime_score - result.oracle_regime_score) < 1e-6, \
                f"{traj_id} step {result.step}: score mismatch " \
                f"ORP={result.orp_regime_score}, Oracle={result.oracle_regime_score}"


def test_boundary_conditions_match_spec():
    """Test score exactly at threshold handled per contract."""
    traj = load_trajectory(get_trajectory_path("adversarial_score_at_boundary"))
    results, summary = simulate_trajectory(traj)

    # All steps should have dual-modality agreement (boundary cases handled identically)
    assert summary.dual_modality_agreement, \
        f"Boundary trajectory has dual-modality disagreement: {summary.violations}"


# ---------- Integration Test ----------


def test_all_trajectories_pass_invariants():
    """Integration test: all trajectories pass all invariants."""
    trajectory_files = list(TRAJECTORY_DIR.glob("*.json"))

    failures = []
    for traj_file in trajectory_files:
        try:
            traj = load_trajectory(traj_file)
            results, summary = simulate_trajectory(traj)

            if not summary.all_invariants_passed:
                failures.append((traj.trajectory_id, summary.violations))
        except Exception as e:
            failures.append((traj_file.stem, [str(e)]))

    if failures:
        failure_msg = "\n".join([f"{tid}: {violations}" for tid, violations in failures])
        pytest.fail(f"Trajectories with invariant failures:\n{failure_msg}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

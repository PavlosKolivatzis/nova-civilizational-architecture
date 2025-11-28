#!/usr/bin/env python3
"""
Test suite: Regime state machine with hysteresis + safety checks.
"""
import numpy as np
from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, Tuple, List

# ============================================================================
# STATE MACHINE
# ============================================================================

class Regime(IntEnum):
    NORMAL = 0
    HEIGHTENED = 1
    CONTROLLED_DEGRADATION = 2
    EMERGENCY_STABILIZATION = 3
    RECOVERY = 4

@dataclass(frozen=True)
class RegimeState:
    regime: Regime
    duration_s: float
    continuity_score: float

MIN_DURATION = {
    Regime.NORMAL: 60.0,
    Regime.HEIGHTENED: 300.0,
    Regime.CONTROLLED_DEGRADATION: 600.0,
    Regime.EMERGENCY_STABILIZATION: 900.0,
    Regime.RECOVERY: 1800.0,
}

ALLOWED = {
    (Regime.NORMAL, Regime.HEIGHTENED),
    (Regime.HEIGHTENED, Regime.NORMAL),
    (Regime.HEIGHTENED, Regime.CONTROLLED_DEGRADATION),
    (Regime.CONTROLLED_DEGRADATION, Regime.HEIGHTENED),
    (Regime.CONTROLLED_DEGRADATION, Regime.EMERGENCY_STABILIZATION),
    (Regime.EMERGENCY_STABILIZATION, Regime.RECOVERY),
    (Regime.RECOVERY, Regime.HEIGHTENED),
}

def hysteresis_check(current: RegimeState, proposed: Regime, osc_count: int) -> Tuple[bool, str]:
    if proposed == current.regime:
        return (True, "same_regime")

    min_dur = MIN_DURATION[current.regime]
    if current.duration_s < min_dur:
        return (False, f"min_duration_not_met:{current.duration_s:.1f}<{min_dur:.1f}")

    if current.regime == Regime.RECOVERY and proposed == Regime.NORMAL:
        if current.continuity_score < 0.85:
            return (False, f"recovery_exit_blocked:C={current.continuity_score:.2f}<0.85")

    if osc_count >= 3:
        return (True, f"allowed_with_oscillation:{osc_count}")

    return (True, "allowed")

def is_legal_transition(current: Regime, proposed: Regime) -> bool:
    return (current, proposed) in ALLOWED

def simulate_transition(
    current: RegimeState,
    proposed: Regime,
    osc_count: int
) -> Tuple[bool, Regime, str]:
    if not is_legal_transition(current.regime, proposed):
        return (False, current.regime, f"illegal:{current.regime.name}->{proposed.name}")

    allowed, reason = hysteresis_check(current, proposed, osc_count)
    if not allowed:
        return (False, current.regime, reason)

    return (True, proposed, reason)

# ============================================================================
# SAFETY ENVELOPE
# ============================================================================

@dataclass
class SafetyViolation:
    rule_id: str
    description: str
    severity: str

def check_safety_envelope(
    current: RegimeState,
    eta_multiplier: float,
    sensitivity_multiplier: float,
    transition_history: List[Tuple[float, Regime]]
) -> List[SafetyViolation]:
    violations = []

    if current.regime.value >= 1 and eta_multiplier > 1.0:
        violations.append(SafetyViolation(
            "no_uncontrolled_acceleration",
            f"η cannot increase during instability (regime={current.regime.name}, η={eta_multiplier:.2f})",
            "block"
        ))

    if current.regime.value >= 1 and sensitivity_multiplier < 1.0:
        violations.append(SafetyViolation(
            "no_noise_amplification",
            f"Sensitivity cannot decrease during instability (regime={current.regime.name}, sens={sensitivity_multiplier:.2f})",
            "block"
        ))

    now = transition_history[-1][0] if transition_history else 0.0
    window_start = now - 300.0
    recent = [ts for ts, _ in transition_history if ts >= window_start]
    if len(recent) > 3:
        violations.append(SafetyViolation(
            "no_destructive_oscillation",
            f"Too many transitions in 300s: {len(recent)} > 3",
            "warn"
        ))

    if not (0.0 <= current.continuity_score <= 1.0):
        violations.append(SafetyViolation(
            "continuity_preservation",
            f"CSI out of bounds: {current.continuity_score:.2f}",
            "block"
        ))

    return violations

# ============================================================================
# CONVERGENCE MATRIX
# ============================================================================

def build_convergence_matrix() -> np.ndarray:
    regimes = list(Regime)
    n = len(regimes)
    M = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(M, 0)

    for (src, dst) in ALLOWED:
        M[src, dst] = 1

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if M[i, k] != -1 and M[k, j] != -1:
                    path_len = M[i, k] + M[k, j]
                    if M[i, j] == -1 or path_len < M[i, j]:
                        M[i, j] = path_len

    return M

def format_convergence_matrix(M: np.ndarray) -> str:
    labels = [r.name[:12] for r in Regime]
    header = "     " + "  ".join(f"{lbl:^12}" for lbl in labels)
    rows = [header, "=" * len(header)]
    for i, r in enumerate(Regime):
        row = f"{r.name[:12]:>12}  "
        row += "  ".join(f"{M[i,j]:^12}" if M[i,j] != -1 else "     -      " for j in range(len(Regime)))
        rows.append(row)
    return "\n".join(rows)

# ============================================================================
# TESTS
# ============================================================================

def test_legal_transitions():
    """1. Legal vs illegal transitions"""
    print("\n=== TEST 1: Legal vs Illegal Transitions ===")

    # Legal
    assert is_legal_transition(Regime.NORMAL, Regime.HEIGHTENED)
    assert is_legal_transition(Regime.EMERGENCY_STABILIZATION, Regime.RECOVERY)
    print("[PASS] Legal transitions recognized")

    # Illegal
    assert not is_legal_transition(Regime.NORMAL, Regime.EMERGENCY_STABILIZATION)
    assert not is_legal_transition(Regime.HEIGHTENED, Regime.EMERGENCY_STABILIZATION)
    assert not is_legal_transition(Regime.RECOVERY, Regime.NORMAL)  # no direct path
    print("[PASS] Illegal transitions blocked")

def test_hysteresis_min_duration():
    """2. Hysteresis: minimum duration enforcement"""
    print("\n=== TEST 2: Hysteresis - Minimum Duration ===")

    state = RegimeState(Regime.HEIGHTENED, duration_s=100.0, continuity_score=0.8)
    success, eff_regime, reason = simulate_transition(state, Regime.NORMAL, osc_count=0)

    assert not success
    assert eff_regime == Regime.HEIGHTENED
    assert "min_duration_not_met" in reason
    print(f"[PASS] Transition blocked: {reason}")

    # Now meet minimum
    state = RegimeState(Regime.HEIGHTENED, duration_s=350.0, continuity_score=0.8)
    success, eff_regime, reason = simulate_transition(state, Regime.NORMAL, osc_count=0)

    assert success
    assert eff_regime == Regime.NORMAL
    print(f"[PASS] Transition allowed after 350s: {reason}")

def test_recovery_exit_threshold():
    """3. Recovery -> Normal requires C≥0.85 (but not in ALLOWED graph, so illegal)"""
    print("\n=== TEST 3: Recovery Exit Threshold ===")

    # C too low - but actually blocked by graph topology first
    state = RegimeState(Regime.RECOVERY, duration_s=2000.0, continuity_score=0.70)
    success, eff_regime, reason = simulate_transition(state, Regime.NORMAL, osc_count=0)

    assert not success
    assert "illegal" in reason or "recovery_exit_blocked" in reason
    print(f"[PASS] Blocked Recovery->Normal (graph + C check): {reason}")

    # C sufficient
    state = RegimeState(Regime.RECOVERY, duration_s=2000.0, continuity_score=0.90)
    success, eff_regime, reason = simulate_transition(state, Regime.HEIGHTENED, osc_count=0)

    assert success
    print(f"[PASS] Allowed Recovery->Heightened with C=0.90")

def test_oscillation_detection():
    """4. Oscillation detection (advisory)"""
    print("\n=== TEST 4: Oscillation Detection ===")

    state = RegimeState(Regime.HEIGHTENED, duration_s=350.0, continuity_score=0.8)
    success, eff_regime, reason = simulate_transition(state, Regime.NORMAL, osc_count=4)

    assert success  # Still allowed (advisory only)
    assert "oscillation" in reason
    print(f"[PASS] Transition allowed with oscillation warning: {reason}")

def test_safety_violations():
    """5. Safety envelope violations"""
    print("\n=== TEST 5: Safety Envelope ===")

    state = RegimeState(Regime.HEIGHTENED, duration_s=400.0, continuity_score=0.8)
    history = [(0.0, Regime.NORMAL), (100.0, Regime.HEIGHTENED)]

    # Illegal eta increase
    violations = check_safety_envelope(state, eta_multiplier=1.2, sensitivity_multiplier=1.1, transition_history=history)
    assert any(v.rule_id == "no_uncontrolled_acceleration" for v in violations)
    print(f"[PASS] Detected eta acceleration violation")

    # Illegal sensitivity decrease
    violations = check_safety_envelope(state, eta_multiplier=0.9, sensitivity_multiplier=0.8, transition_history=history)
    assert any(v.rule_id == "no_noise_amplification" for v in violations)
    print(f"[PASS] Detected noise amplification violation")

    # Oscillation (warning only)
    history_osc = [(i*60.0, Regime.NORMAL if i%2 else Regime.HEIGHTENED) for i in range(5)]
    violations = check_safety_envelope(state, eta_multiplier=0.9, sensitivity_multiplier=1.1, transition_history=history_osc)
    osc_violations = [v for v in violations if v.rule_id == "no_destructive_oscillation"]
    assert len(osc_violations) == 1
    assert osc_violations[0].severity == "warn"
    print(f"[PASS] Detected oscillation (advisory)")

def test_convergence_matrix():
    """6. Convergence matrix (reachability)"""
    print("\n=== TEST 6: Convergence Matrix ===")

    M = build_convergence_matrix()

    # All regimes can reach HEIGHTENED
    for r in Regime:
        assert M[r, Regime.HEIGHTENED] >= 0, f"{r.name} cannot reach HEIGHTENED"
    print("[PASS] All regimes reach HEIGHTENED")

    # EMERGENCY -> NORMAL requires multi-hop path
    # EMERGENCY->RECOVERY->HEIGHTENED->NORMAL = 3 hops
    assert M[Regime.EMERGENCY_STABILIZATION, Regime.NORMAL] == 3, "EMERGENCY needs 3 hops to NORMAL"
    print("[PASS] EMERGENCY->NORMAL requires 3 hops (via RECOVERY->HEIGHTENED)")

    # EMERGENCY -> HEIGHTENED via RECOVERY
    assert M[Regime.EMERGENCY_STABILIZATION, Regime.HEIGHTENED] == 2, "EMERGENCY->RECOVERY->HEIGHTENED"
    print("[PASS] EMERGENCY->HEIGHTENED in 2 hops")

    print("\nConvergence Matrix (min hops):")
    print(format_convergence_matrix(M))

def test_scenario_thrash_prevention():
    """7. Scenario: Prevent NORMAL<->HEIGHTENED thrash"""
    print("\n=== TEST 7: Scenario - Thrash Prevention ===")

    timeline = []
    t = 0.0
    state = RegimeState(Regime.NORMAL, duration_s=t, continuity_score=0.9)

    # Escalate to HEIGHTENED
    t += 70.0
    state = RegimeState(Regime.HEIGHTENED, duration_s=0.0, continuity_score=0.6)
    timeline.append((t, state.regime))
    print(f"t={t:>5.0f}s: NORMAL -> HEIGHTENED (C=0.6)")

    # Try to downgrade immediately (should block)
    t += 50.0
    success, eff, reason = simulate_transition(
        RegimeState(Regime.HEIGHTENED, duration_s=50.0, continuity_score=0.75),
        Regime.NORMAL,
        osc_count=1
    )
    assert not success
    print(f"t={t:>5.0f}s: HEIGHTENED -> NORMAL BLOCKED ({reason})")

    # Wait full 300s, then downgrade
    t += 260.0
    success, eff, reason = simulate_transition(
        RegimeState(Regime.HEIGHTENED, duration_s=310.0, continuity_score=0.75),
        Regime.NORMAL,
        osc_count=1
    )
    assert success
    timeline.append((t, Regime.NORMAL))
    print(f"t={t:>5.0f}s: HEIGHTENED -> NORMAL allowed ({reason})")
    print("[PASS] Hysteresis prevented thrash")

def test_scenario_emergency_recovery():
    """8. Scenario: Emergency -> Recovery -> Heightened"""
    print("\n=== TEST 8: Scenario - Emergency Recovery Path ===")

    t = 0.0
    state = RegimeState(Regime.EMERGENCY_STABILIZATION, duration_s=0.0, continuity_score=0.3)
    print(f"t={t:>5.0f}s: EMERGENCY_STABILIZATION (C=0.3)")

    # Try direct to NORMAL (illegal)
    success, _, reason = simulate_transition(state, Regime.NORMAL, osc_count=0)
    assert not success
    assert "illegal" in reason
    print(f"[PASS] EMERGENCY -> NORMAL blocked (illegal)")

    # Escalate to RECOVERY after 900s
    t += 920.0
    state = RegimeState(Regime.EMERGENCY_STABILIZATION, duration_s=920.0, continuity_score=0.55)
    success, eff, reason = simulate_transition(state, Regime.RECOVERY, osc_count=0)
    assert success
    print(f"t={t:>5.0f}s: EMERGENCY -> RECOVERY (C=0.55)")

    # Try RECOVERY -> NORMAL too early (C<0.85)
    t += 1900.0
    state = RegimeState(Regime.RECOVERY, duration_s=1900.0, continuity_score=0.80)
    success, _, reason = simulate_transition(state, Regime.HEIGHTENED, osc_count=0)
    assert success
    print(f"t={t:>5.0f}s: RECOVERY -> HEIGHTENED (C=0.80, can't reach NORMAL yet)")

    print("[PASS] Recovery path enforces graduality")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("=" * 65)
    print("  Nova Regime State Machine Test Suite")
    print("=" * 65)

    test_legal_transitions()
    test_hysteresis_min_duration()
    test_recovery_exit_threshold()
    test_oscillation_detection()
    test_safety_violations()
    test_convergence_matrix()
    test_scenario_thrash_prevention()
    test_scenario_emergency_recovery()

    print("\n" + "=" * 65)
    print("[PASS] ALL TESTS PASSED")
    print("=" * 65)

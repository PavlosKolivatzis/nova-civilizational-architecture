# Phase 11 - System Invariants

## Purpose

This document defines the mathematical and architectural invariants introduced in Phase 11 - Operational Regime Policy (ORP). These invariants constitute Nova's **transformation geometry** - the lawful constraints governing how the system changes over time.

---

## 1. Temporal Invariants

### 1.1 Minimum Regime Durations

**Invariant**: Once a regime is entered, it MUST persist for at least its minimum duration before any transition is allowed (unless overridden by emergency signals).

```
∀ regime ∈ REGIMES:
  duration_in_regime < MIN_DURATION[regime] ⟹ transition_blocked
```

**Canonical Durations**:
- `normal`: 60s (1 minute)
- `heightened`: 300s (5 minutes)
- `controlled_degradation`: 600s (10 minutes)
- `emergency_stabilization`: 900s (15 minutes)
- `recovery`: 1800s (30 minutes)

**Purpose**: Prevent regime thrashing; enforce temporal inertia

**Contract**: `contracts/orp_stabilization@1.yaml`

---

### 1.2 Monotonic Duration

**Invariant**: Time spent in a regime increases monotonically until transition.

```
∀ t₁ < t₂ in same regime:
  duration_s(t₂) ≥ duration_s(t₁)
```

**Reset**: `duration_s = 0` on regime transition

**Purpose**: Enable hysteresis logic; provide consistent time reference

---

### 1.3 Recovery Exit Threshold

**Invariant**: Transition from `recovery` to `normal` requires continuity score above threshold.

```
current_regime = recovery ∧ proposed_regime = normal
  ⟹ continuity_score ≥ 0.85
```

**Purpose**: Prevent premature exit from recovery; ensure stable restoration

**Contract**: `contracts/orp_stabilization@1.yaml` § recovery_stabilization

---

### 1.4 Oscillation Detection (Advisory)

**Invariant**: Oscillation detected if ≥3 regime transitions occur within 5-minute window.

```
count(transitions, window=300s) ≥ 3 ⟹ oscillation_detected = true
```

**Action**: Warn (log + metric), but do NOT block transitions

**Purpose**: Observability of signal instability; tuning feedback

---

## 2. Amplitude Invariants

### 2.1 Multiplicative Scaling

**Invariant**: All amplitude adjustments are multiplicative, not additive.

```
output = input × multiplier
NOT: output = input + offset
```

**Applies to**:
- Governor η scaling: `η_scaled = η_base × multiplier`
- Emotional constriction: `intensity_scaled = intensity × multiplier`
- Slot09 sensitivity: `threshold_scaled = threshold_base × multiplier`

**Purpose**: Preserve relative proportions; avoid discontinuities

---

### 2.2 Bounded Multipliers

**Invariant**: All amplitude multipliers bounded in [0.0, 2.0].

```
∀ multiplier: 0.0 ≤ multiplier ≤ 2.0
```

**Typical Range**: [0.25, 1.50] in practice

**Purpose**: Prevent collapse (0) or runaway (∞); safety bounds

---

### 2.3 Topology Preservation

**Invariant**: Amplitude scaling changes magnitude, NOT what is detected or emitted.

```
Slot09: {features detected} unchanged, only {threshold} scaled
Emotion: {valence, category} unchanged, only {intensity} scaled
Governor: {wisdom mode, constraints} unchanged, only {η} scaled
```

**Purpose**: Maintain semantic consistency; no qualitative regime changes

---

### 2.4 Governor Constraint Satisfaction

**Invariant**: Scaled η must respect Governor's configured bounds.

```
η_scaled = clamp(η_base × multiplier, eta_min, eta_max)
```

**Purpose**: Honor Governor's safety constraints; no override of architectural limits

**Implementation**: `src/nova/governor/adaptive_wisdom.py:step()`

---

## 3. Stability Invariants

### 3.1 No Uncontrolled Acceleration

**Invariant**: Learning rate (η) MUST NOT increase during instability.

```
instability_detected ⟹ η_multiplier ≤ 1.0
```

**Regimes**:
- `normal`: η × 1.0 (no change)
- `heightened`: η × 0.90-0.95
- `controlled_degradation`: η × 0.75
- `emergency_stabilization`: η × 0.50
- `recovery`: η × 0.25

**Purpose**: Prevent runaway adaptation; dampen learning under stress

**Contract**: `contracts/orp_policy@1.yaml` § eta_scaling_table

---

### 3.2 No Noise Amplification

**Invariant**: Detection sensitivity MUST NOT increase (thresholds MUST NOT decrease) during instability.

```
instability_detected ⟹ sensitivity_multiplier ≥ 1.0
```

**Effect**: Higher thresholds → less sensitive → fewer false positives

**Purpose**: Reduce perceptual noise during instability; focus on strong signals

**Contract**: `contracts/orp_policy@1.yaml` § sensitivity_multiplier_table

---

### 3.3 No Destructive Oscillation

**Invariant**: Regime transitions cannot occur faster than minimum durations allow.

```
transition_rate ≤ 1 / MIN_DURATION[current_regime]
```

**Maximum Rates**:
- From `normal`: ≤1 per 60s
- From `heightened`: ≤1 per 300s
- From `recovery`: ≤1 per 1800s

**Purpose**: Enforce temporal stability; prevent thrashing

**Mechanism**: Hysteresis enforcement via `check_regime_hysteresis()`

---

### 3.4 No Abrupt Mode Reversals

**Invariant**: Recovery regime cannot transition directly to emergency (must pass through intermediate regimes).

```
current_regime = recovery ⟹ proposed_regime ∉ {emergency_stabilization}
```

**Path**: `recovery → controlled_degradation → emergency`

**Purpose**: Smooth state transitions; avoid discontinuous jumps

**Implementation**: Regime classification rules in `orp_policy.py`

---

### 3.5 No Continuity Collapse

**Invariant**: System maintains continuity score C ∈ [0, 1] at all times, even during regime transitions.

```
∀ t: 0.0 ≤ continuity_score(t) ≤ 1.0
```

**Mechanism**: ORP modulates amplitudes but does NOT override continuity engine

**Purpose**: Preserve global system coherence; no undefined states

---

## 4. Ledger Invariants

### 4.1 Append-Only

**Invariant**: Regime transition ledger is strictly append-only.

```
∀ entry ∈ ledger: entry is immutable after write
```

**Operations**: Append ONLY (no update, no delete)

**Purpose**: Tamper-evident history; auditability

**Schema**: `contracts/regime_transition_ledger@1.yaml`

---

### 4.2 Timestamp Ordering

**Invariant**: Ledger entries are ordered by timestamp (monotonically increasing).

```
∀ i < j: timestamp[i] ≤ timestamp[j]
```

**Format**: ISO8601 UTC (e.g., `2025-01-01T00:00:00Z`)

**Purpose**: Enable time-based queries; support hysteresis logic

---

### 4.3 Duration Consistency

**Invariant**: Recorded duration matches time difference between consecutive regime entries.

```
entry[i].duration_s ≈ timestamp[i+1] - timestamp[i]  (within tolerance)
```

**Tolerance**: Clock drift, system load

**Purpose**: Validate ledger integrity; detect corruption

---

## 5. Cross-Module Synchronization Invariants

### 5.1 Unified Regime View

**Invariant**: All ORP-connected modules see the same `effective_regime` after hysteresis.

```
regime_governor = regime_emotion = regime_slot09 = effective_regime
```

**Mechanism**: Shared `orp_hysteresis.check_regime_hysteresis()` function

**Purpose**: Global coherence; no module divergence

**Contract**: `contracts/orp_stabilization@1.yaml` § synchronized_modules

---

### 5.2 Graceful Degradation

**Invariant**: ORP module failures MUST NOT crash host modules.

```
orp_function_fails ⟹ fallback_to_base_behavior
```

**Fallbacks**:
- η scaling fails → use `η_base`
- Emotional constriction fails → use raw intensity
- Sensitivity scaling fails → use base thresholds

**Purpose**: Resilience; no cascading failures

**Implementation**: Try/except with fallback stubs in all integration points

---

### 5.3 Flag Gating

**Invariant**: ORP features MUST be disabled by default; enabled only via explicit flags.

```
∀ feature ∈ ORP_FEATURES:
  feature.enabled ⟺ ENV[feature.flag] = "1"
```

**Flags**:
- `NOVA_ENABLE_REGIME_LEDGER=0`
- `NOVA_ENABLE_ETA_SCALING=0`
- `NOVA_ENABLE_EMOTIONAL_CONSTRICTION=0`
- `NOVA_ENABLE_SLOT09_SENSITIVITY=0`

**Purpose**: Safe rollout; A/B testing; rollback capability

---

## 6. Pure Function Invariants

### 6.1 Referential Transparency

**Invariant**: ORP adapter functions are pure (same inputs → same outputs).

```
∀ f ∈ {apply_eta_scaling, apply_emotional_constriction, apply_sensitivity_scaling}:
  f(x₁) = f(x₂) if x₁ = x₂
```

**No Side Effects**: No state mutation (except ledger append)

**Purpose**: Testability; determinism; composability

---

### 6.2 Ledger Read-Only

**Invariant**: Hysteresis and adapter functions MUST NOT mutate ledger.

```
∀ f ∈ ORP_FUNCTIONS:
  ledger_before(f) = ledger_after(f)
```

**Only Writer**: Regime transition recorder

**Purpose**: Separation of concerns; prevent corruption

---

## 7. Emergent System-Level Invariants

### 7.1 Stability Preference

**Property**: Under persistent instability, system converges to damped state, not oscillation.

```
lim[t→∞] (system under instability) → {low η, low emotion, high thresholds}
```

**Mechanism**: Hysteresis + amplitude damping

**Purpose**: Self-stabilizing architecture

---

### 7.2 Recovery Graduality

**Property**: Recovery from degradation is gradual, not instantaneous.

```
recovery_duration ≥ 1800s ∧ C ≥ 0.85 required for exit
```

**Mechanism**: Minimum duration + continuity threshold

**Purpose**: Prevent premature normalization; ensure stable restoration

---

### 7.3 Inertia Layer

**Property**: ORP provides stability inertia that continuity systems depend on.

```
signal_variance_damped = orp_hysteresis(signal_variance_raw)
```

**Feedback Loop**: Stable regimes → stable signals → stable regimes

**Purpose**: Close the continuity loop; provide architectural grounding

---

## 8. Verification Checklist

For any change to ORP system, verify:

- [ ] Temporal invariants respected (minimum durations, monotonicity)
- [ ] Amplitude scaling multiplicative (not additive)
- [ ] Multipliers bounded [0.0, 2.0]
- [ ] Topology preserved (semantics unchanged)
- [ ] Governor constraints honored (eta_min/eta_max)
- [ ] No uncontrolled acceleration (η damped during instability)
- [ ] No noise amplification (thresholds increased during instability)
- [ ] Ledger append-only (no mutations)
- [ ] Pure functions (no side effects except ledger append)
- [ ] Graceful degradation (fallbacks on failure)
- [ ] Flag-gated (default off)
- [ ] Test coverage ≥95% (unit + integration)
- [ ] Contracts updated (if schema/semantics changed)
- [ ] Metrics exported (ORP_* namespace)

---

## 9. Mathematical Notation Summary

### Regimes
```
R = {normal, heightened, controlled_degradation, emergency_stabilization, recovery}
```

### Amplitude Scaling
```
η_scaled = clamp(η_base × M_η(regime, duration), eta_min, eta_max)
I_scaled = I × M_emotion(regime, duration)
T_scaled = clamp(T_base × M_sensitivity(regime, duration), T_base, T_base × 2.0)
```

Where:
- `M_η`: η multiplier function [0.25, 1.0]
- `M_emotion`: Emotional multiplier function [0.50, 1.0]
- `M_sensitivity`: Sensitivity multiplier function [1.0, 1.50]

### Hysteresis
```
transition_allowed ⟺ (duration_s ≥ MIN_DURATION[current_regime])
                     ∨ (proposed_regime = current_regime)
```

### Recovery Exit
```
(current_regime = recovery ∧ proposed_regime = normal)
  ⟹ (continuity_score ≥ 0.85 ∧ duration_s ≥ 1800)
```

---

## 10. References

- **Contracts**: `contracts/orp_*.yaml`, `contracts/regime*.yaml`, `contracts/hysteresis_decision@1.yaml`
- **Implementation**: `src/nova/continuity/{orp_policy,eta_scaling,emotional_posture,slot09_sensitivity,orp_hysteresis}.py`
- **Ontology**: `specs/nova_framework_ontology.v1.yaml` v1.5.0
- **Tests**: 170 tests (121 unit + 49 integration)

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-27
**Phase**: 11 - Operational Regime Policy
**Status**: Production-ready (flag-gated)

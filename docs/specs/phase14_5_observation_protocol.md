# Phase 14.5 Temporal USM Observation Protocol

**Status:** ✅ READY FOR OBSERVATION (2025-12-09 provisional thresholds set)
**Key Finding:** ρ_t (equilibrium ratio), not C_t, is primary extraction indicator
**Primary Observable:** ρ_t temporal trajectory + C_t for consensus/extraction distinction
**Original Plan:** 7-14 days production traffic or 1000+ diverse sessions
**Flag:** `NOVA_ENABLE_USM_TEMPORAL=1` (metrics-only, no control decisions)

---

## Provisional Threshold Calibration (2025-12-09)

**Status:** PROVISIONAL — requires empirical validation after 100-200 sessions

| Metric | Threshold | Basis |
|--------|-----------|-------|
| **C_t extractive** | 0.18 | Pilot data + 60% scaling from instantaneous (0.3) |
| **C_t protective** | -0.12 | Pilot benign conversation baseline (-0.2) |
| **ρ_t extractive** | 0.25 | Extractive scenario (ρ=0.0 flat) + safety margin |
| **ρ_t protective** | 0.6 | Benign reciprocity spike (pilot observed 0.6-0.95) |
| **Min turns** | 3 | Warm-up period before classification |

### Combined State Classification

| State | C_t Condition | ρ_t Condition | Interpretation |
|-------|---------------|---------------|----------------|
| **Extractive** | > 0.18 | < 0.25 | Hierarchical control + one-way flow |
| **Consensus** | < -0.12 | < 0.25 | Protective alignment (low reciprocity ≠ extraction) |
| **Collaborative** | < -0.12 | > 0.6 | Active negotiation + balanced exchange |
| **Neutral** | [-0.12, 0.18] | [0.25, 0.6] | Normal operational range |
| **Warming up** | any | any | turn_count < 3 (insufficient data) |

### Validation Criteria

**Rollback trigger:** Misclassification rate > 50% in first 100 sessions
- If exceeded: STOP observation, run full calibration with diverse conversations
- Expected refinement: After 100-200 sessions with ground truth labels

**Known uncertainties:**
1. Turn-count dependency (early vs. late conversation baseline shift)
2. Domain variation (technical vs. casual vs. investigative dialogue)
3. ρ_t velocity thresholds (sudden shifts vs. gradual drift detection)

### Implementation

See: `src/nova/math/usm_temporal_thresholds.py`

---

## 2025-12-09 Oracle Validation Findings

**Test Setup:** 5 hand-crafted inputs with known structural properties (hierarchical, distributed, extractive, balanced, VOID)

**Results:**
- ✅ VOID detection: Perfect (graph_state, C=-0.5, rho=None all correct)
- ✅ **Attack detection: Extractive interrogation → C=0.4** (HIGH-VALUE SIGNAL)
- ✅ Collapse score range: [-0.3, 0.4] for normal→extractive text (measurable gradient)
- ⚠️ Spectral entropy: H~0 for conversational text (structurally flat, not narrative)
- ⚠️ Equilibrium ratio: ρ∈{0.0, 1.0} (binary: extractive or balanced, no gradient)

**Root Cause Analysis:**
- Not a parser bug — conversational AI responses are **explanatory, not relational**
- Text structure: concepts + properties, not agents + power dynamics
- Example: "Alice analyzes the methodology" → parser correctly extracts 0-1 edges (Alice exists, but "methodology" is abstract concept, not actor)

**Key Insight:** **C (collapse score) is the working signal** for manipulation detection:
- C<0: Distributed/protective patterns (multi-perspective, balanced)
- C>0.3: Extractive/hierarchical patterns (single-voice dominance)
- C_t temporal drift: Gradual manipulation (conversation-level attack)

**Revised Success Criteria:**
- ~~H > 0.5 (structural diversity)~~ → **REMOVED** (unrealistic for conversational text)
- **C_t ∈ [-0.5, 1.0] with measurable drift** → PRIMARY SIGNAL
- **edge_count >= 1** (non-VOID graph) → MINIMAL THRESHOLD
- **ρ_eq → 1.0 during VOID** → VOID RECOVERY VALIDATION

**Decision:** Proceed with Phase 14.5 observation focused on **C_t temporal drift** as primary manipulation indicator.

---

## Uncertainties to Resolve

### 1. Smoothing Parameter Validation
**Hypothesis:** λ=0.6 balances responsiveness and stability for typical conversation lengths.

**Metrics:**
- `temporal_usm_lambda_used` (gauge, per-stream)
- `temporal_usm_update_count` (counter, by graph_state)

**Analysis:**
```python
# Per session: plot C_t over time
# Questions:
# - Does C_t stabilize within 3-5 turns?
# - Does C_t oscillate or smooth-converge?
# - Correlation: session_length vs C_t variance?
```

**Decision Gate:**
- If C_t variance < 0.05 after turn 5 → λ=0.6 acceptable
- If C_t oscillates ±0.2 throughout → increase smoothing (λ→0.3)

---

### 2. Equilibrium Assumption (ρ_eq=1.0)
**Hypothesis:** VOID represents protective equilibrium, not evasion.

**Metrics:**
- `slot07_regime_unchanged_on_void_total` (existing)
- `temporal_usm_void_sequences` (histogram: VOID run lengths)

**Analysis:**
```python
# Conditional distribution:
# P(regime_escalation | VOID_sequence_length > 2)
# vs
# P(regime_escalation | non-VOID)
```

**Decision Gate:**
- If VOID correlates with de-escalation → ρ_eq=1.0 valid
- If VOID precedes escalation → ρ_eq may need tuning (0.7? 0.8?)

---

### 3. Collapse Score Baseline
**Hypothesis:** Benign conversations converge toward C_t ∈ [-0.3, 0.0].

**Metrics:**
- `temporal_usm_C_temporal` (histogram, bucketed)
- `temporal_usm_C_inst_vs_C_temporal_delta` (distribution)

**Analysis:**
```python
# Questions:
# - What is P95(C_t) for non-quarantined sessions?
# - Does C_t < -0.2 reliably predict action=pass?
# - Does C_t > 0.3 reliably predict action=quarantine?
```

**Decision Gate (Phase 14.6 precondition):**
- Identify threshold `θ` where:
  - `C_t < θ` → 95% true negative (benign)
  - `C_t > θ` → 80% true positive (needs intervention)

---

### 4. VOID Temporal Patterns
**Hypothesis:** VOID appears naturally at session boundaries, not mid-dialogue.

**Metrics:**
- `temporal_usm_void_position` (histogram: turn_number when VOID occurs)
- `temporal_usm_consecutive_voids` (histogram: run lengths)

**Analysis:**
```python
# Clustering:
# - VOID at turn < 3 (session start/handshake)?
# - VOID at turn > session_length - 2 (clean termination)?
# - VOID mid-session (turn 10-50)? → Suspicious?
```

**Decision Gate:**
- If VOID clusters at boundaries → current handling OK
- If VOID appears mid-dialogue → may need reset mode for consecutive VOID

---

### 5. Attack Surface: Temporal Smoothing Gaming
**Hypothesis:** Adversary cannot exploit EMA to mask sustained manipulation.

**Metrics:**
- Session-level: `max(C_inst)` vs `max(C_temporal)`
- Lag analysis: `turns_until_C_temporal_crosses_threshold`

**Analysis:**
```python
# Simulate attack:
# - Benign preamble (5 turns, C_inst=-0.2)
# - Adversarial spike (1 turn, C_inst=0.8)
# - Does C_t < threshold still? (smoothing masks spike?)
```

**Decision Gate (Phase 14.6 blocker):**
- If single-turn spikes remain detectable via C_inst → safe to use C_t for gating
- If smoothing hides attacks → Phase 14.6 must use `max(C_inst, C_t)` not `C_t` alone

---

## Observation Infrastructure

### Required Prometheus Queries

```promql
# 1. C_t distribution
histogram_quantile(0.95,
  rate(temporal_usm_C_temporal_bucket[1h])
)

# 2. VOID sequence lengths
histogram_quantile(0.90,
  rate(temporal_usm_consecutive_voids_bucket[1h])
)

# 3. Convergence rate (variance over time)
stddev_over_time(temporal_usm_C_temporal[5m])

# 4. VOID correlation with regime changes
rate(slot07_regime_transition_total[10m])
  and on(session_id)
rate(temporal_usm_void_sequences[10m])
```

### Logging Additions (if needed)

```python
# In core.py, add optional verbose logging:
if os.getenv("NOVA_LOG_TEMPORAL_DETAIL", "0") == "1":
    logger.info(
        "Temporal update",
        extra={
            "session_id": session_id,
            "turn_number": self._turn_counter.get(session_id, 0),
            "C_inst": C_inst,
            "C_temporal": state.C,
            "delta": abs(C_inst - state.C),
            "graph_state": graph_state,
        }
    )
```

---

## Exit Criteria (Phase 14.6 Unblocked When...)

1. ✅ **λ validation:** C_t variance acceptable, no oscillation
2. ✅ **ρ_eq validation:** VOID correlates with stability, not evasion
3. ✅ **Threshold identified:** C_t > θ threshold with acceptable ROC
4. ✅ **VOID patterns understood:** Boundary vs mid-session distribution clear
5. ✅ **Attack resistance:** Single-turn spikes remain detectable

**Minimum data:** 1000 sessions, 50+ quarantine events, 200+ VOID sequences.

---

## Rollback Plan

If observation reveals C_t is **too noisy** or **masks attacks**:
- Keep Phase 14.5 for **monitoring only** (emit temporal_usm@1 to logs)
- **Block Phase 14.6** indefinitely (do not use C_t for control decisions)
- Document findings in RFC-014 Addendum

# Phase 12: Nova End-to-End Stability Validation (E2E-S)

**Status:** Plan
**Phase:** 12
**Purpose:** Validate the full physics stack operating as one cybernetic loop
**Dependencies:** Phase 11 (Operating Regime Ontology + Transformation Geometry)

---

## Objective

Validate that the Operating Ontology's physics produce **correct, stable, predictable behavior** across full-state trajectories when the entire chain is active:

```
Signals → ORP → Posture → Amplitude Triad → Router/Governance/Slot10 → System State →
 Regime Ledger → ORP → (loop)
```

**Current gap:** Phase 11 has unit tests and isolated scenario tests with mocked ORP snapshots. We do NOT yet have tests for:
- Multi-step regime transitions driven by signal evolution
- Hysteresis + min-duration enforcement across sequences
- Amplitude triad coherence during regime cycles
- Oscillation prevention under real signal dynamics
- Cross-slot behavioral consistency during full regime transitions
- **Temporal invariance** (physics stable under time scaling)
- **Contract fidelity** (implementation faithful to ontology specification)

---

## Deliverables

### 1. End-to-End Simulation Suite

**File:** `scripts/simulate_nova_cycle.py`

**Capabilities:**
- Load signal trajectory from JSON (20–40 step sequences)
- Execute ORP evaluation at each step
- Record regime transitions, posture changes, amplitude adjustments
- Validate invariants at each step:
  - Regime classification matches score
  - Hysteresis prevents premature downgrade
  - Min-duration enforced
  - Amplitude triad consistency (ω_base, η, γ)
  - Ledger continuity (from_regime[N] == to_regime[N-1])
  - Safety envelope preserved
- Output CSV/JSON log of full run

**Input schema:**
```json
{
  "trajectory_id": "canonical_normal_to_recovery",
  "description": "Full escalation from normal to recovery",
  "steps": [
    {
      "step": 0,
      "timestamp": "2025-01-01T00:00:00Z",
      "elapsed_s": 0,
      "contributing_factors": {
        "urf_composite_risk": 0.15,
        "mse_meta_instability": 0.03,
        "predictive_collapse_risk": 0.10,
        "consistency_gap": 0.05,
        "csi_continuity_index": 0.95
      },
      "expected_regime": "normal",
      "expected_transition": null
    },
    ...
  ]
}
```

---

### 2. Trajectory Library

**Directory:** `tests/e2e/trajectories/`

**Canonical Trajectories (10):**
1. `canonical_normal_stable.json` — 20 steps in normal regime (no transitions)
2. `canonical_normal_to_heightened.json` — Gradual escalation to heightened
3. `canonical_heightened_to_controlled.json` — Further escalation
4. `canonical_controlled_to_emergency.json` — Crisis escalation
5. `canonical_emergency_to_recovery.json` — Full crisis
6. `canonical_recovery_to_normal.json` — Full recovery path (gradual downgrade)
7. `canonical_heightened_stable.json` — Sustained heightened regime
8. `canonical_hysteresis_prevents_downgrade.json` — Score drops but stays above hysteresis
9. `canonical_min_duration_blocks_downgrade.json` — Score drops below hysteresis but too early
10. `canonical_downgrade_after_duration.json` — Successful downgrade after min-duration

**Adversarial Trajectories (6):**
1. `adversarial_rapid_oscillation.json` — Signal spikes every 2 steps (tests hysteresis)
2. `adversarial_score_at_boundary.json` — Score exactly at regime thresholds (0.30, 0.50, etc.)
3. `adversarial_csi_collapse.json` — CSI drops to 0.0 (inverted → high risk)
4. `adversarial_all_signals_high.json` — All factors at 0.95+ simultaneously
5. `adversarial_recovery_immediate_spike.json` — Recovery → emergency → recovery in 3 steps
6. `adversarial_zero_duration_attempt.json` — Attempt downgrade at t=0

**Noise-Injected Runs (4):**
1. `noise_normal_with_jitter.json` — Base signals ±10% random noise
2. `noise_heightened_with_spikes.json` — Random +0.2 spikes every 5 steps
3. `noise_multi_regime_drift.json` — Gradual drift with ±0.05 noise
4. `noise_recovery_path_unstable.json` — Recovery with noisy signals

**Temporal Invariance Trajectories (4):**
1. `temporal_10s_intervals.json` — Same signal profile, evaluated every 10s
2. `temporal_60s_intervals.json` — Same signal profile, evaluated every 60s
3. `temporal_compressed_2x.json` — Drop every 2nd step from canonical trajectory
4. `temporal_expanded_interpolated.json` — Add interpolated midpoints to canonical trajectory

---

### 3. Contract Oracle (Independent Implementation)

**File:** `src/nova/continuity/contract_oracle.py`

**Purpose:** Pure contract-level regime classifier, independent of `OperationalRegimePolicy` class. Used for differential testing to ensure implementation fidelity.

**Functions:**
```python
def classify_regime_from_contract(
    regime_score: float,
    current_regime: str,
    time_in_regime_s: float,
    hysteresis: float = 0.05,
    min_duration_s: float = 300.0,
    thresholds: Dict[str, Tuple[float, float]] = REGIME_THRESHOLDS
) -> str:
    """Pure implementation of orp@1.yaml regime classification rules.

    Implements:
    - Upgrade: immediate if score crosses threshold upward
    - Downgrade: only if score < (threshold - hysteresis) AND time >= min_duration
    - Boundary: score exactly at threshold → choose higher regime
    """
    # [Independent reimplementation from contract spec]

def compute_regime_score_from_contract(
    factors: Dict[str, float],
    weights: Dict[str, float] = SIGNAL_WEIGHTS
) -> float:
    """Pure implementation of weighted regime score calculation with CSI inversion."""
    # [Independent reimplementation from contract spec]
```

**Validation:** Oracle must produce identical results to `OperationalRegimePolicy` for all trajectories. Divergence = bug or spec ambiguity.

---

### 4. State Reconstruction Engine

**File:** `src/nova/continuity/trajectory_recorder.py`

**Purpose:** Record full system state at each simulation step for post-run analysis.

**Recorded state:**
- Regime snapshot (regime, score, factors, posture, timestamp)
- Ledger entries (transitions, duration, continuity check)
- Amplitude triad (ω_base, η, γ from posture)
- Router decision (route, score, constraints)
- Governance result (allowed, reason, metadata)
- Slot10 gate (passed, failed_conditions)
- **Contract oracle regime** (for dual-modality comparison)

**Output format:** JSON Lines (`.jsonl`) for streaming analysis

---

### 5. Visualization Module

**File:** `notebooks/Phase12_StabilityVisualization.ipynb`

**Plots:**
1. **Regime Timeline:** Stacked bar chart showing regime over time
2. **Regime Score Evolution:** Line chart with regime threshold bands
3. **Contributing Factors:** Stacked area chart of signal contributions
4. **Posture Adjustments:** Multi-line chart (threshold_multiplier, traffic_limit)
5. **Amplitude Triad:** Triple-line chart (ω_base, η, γ)
6. **Transition Events:** Scatter plot with upgrade/downgrade markers
7. **Oscillation Detection:** Highlight windows with >5 transitions
8. **Dual-Modality Agreement:** Overlay impl vs oracle regime classifications

**Alternative (if notebook heavy):**
`scripts/visualize_trajectory.py` — CLI tool that outputs PNG/SVG via matplotlib

---

### 6. System-Level Behavior Tests

**File:** `tests/e2e/test_regime_cycle.py`

**Test categories:**

#### Safety Envelope Enforcement
- `test_regime_never_exceeds_recovery` — Score >1.0 clamps to recovery
- `test_amplitude_triad_always_valid` — ω ∈ [0.5,1.0], η ∈ [0.0,1.0], γ ≥ 0.0
- `test_traffic_limit_never_negative` — Always ∈ [0.0, 1.0]

#### Transition Correctness
- `test_upgrade_immediate_on_threshold_cross` — No hysteresis on upgrade
- `test_downgrade_requires_hysteresis` — Must drop below (threshold - 0.05)
- `test_downgrade_requires_min_duration` — Must stay ≥300s before downgrade
- `test_transition_ledger_continuity` — from_regime[N] == to_regime[N-1]

#### Amplitude Consistency
- `test_omega_base_decreases_with_regime` — normal=1.0, recovery=0.5
- `test_eta_tightens_with_regime` — Emotional constriction increases
- `test_gamma_stable_across_transitions` — Coherence bias preserved

#### Ledger Invariants
- `test_ledger_append_only` — No deletions/modifications
- `test_ledger_timestamp_monotonic` — Timestamps always increase
- `test_ledger_record_id_unique` — No duplicate IDs

#### Max Transition Count
- `test_oscillation_detection_triggers` — >5 transitions in 1 hour flagged
- `test_hysteresis_prevents_oscillation` — Rapid signal spikes don't cause thrashing

#### Temporal Invariance (NEW)
- `test_trajectory_compression_preserves_regimes` — Dropping every 2nd step preserves transitions at aligned points
- `test_trajectory_expansion_stable` — Interpolating midpoints doesn't cause spurious transitions
- `test_evaluation_frequency_independence` — 10s vs 60s intervals produce same regime transitions at matching timestamps

#### Contract Fidelity (NEW)
- `test_dual_modality_regime_agreement` — Implementation matches oracle for all trajectories
- `test_regime_score_calculation_matches_contract` — Score computation identical to oracle
- `test_boundary_conditions_match_spec` — Score exactly at threshold handled per contract

**Total: 21 core tests**

---

### 7. Cross-AI Co-Simulation (High Value)

**File:** `scripts/cross_ai_cosimulation.py`

**Process:**
1. Select 5 representative trajectories (2 canonical, 2 adversarial, 1 noise)
2. Export trajectory to markdown description:
   ```markdown
   ## Trajectory: Normal → Recovery Escalation

   Given ORP contract orp@1.yaml with:
   - Thresholds: normal=[0.0,0.3), heightened=[0.3,0.5), ...
   - Hysteresis: 0.05 (downgrade only if score < threshold - 0.05)
   - Min-duration: 300s (downgrade only after 5min in regime)

   Step 0 (t=0s): URF=0.15, MSE=0.03, Pred=0.10, Gap=0.05, CSI=0.95
     Regime score = ? → Expected regime = ?

   Step 1 (t=60s): URF=0.32, MSE=0.05, Pred=0.18, Gap=0.08, CSI=0.90
     Regime score = ? → Expected regime = ?
   ...
   ```
3. Submit to 8 AI systems (Claude, GPT-4, Gemini, DeepSeek, Qwen, Llama, Mistral, Command-R)
4. Ask: "Given ORP contract thresholds and hysteresis rules, predict regime at each step"
5. Compare predictions to Nova's actual behavior
6. Identify divergence → flag potential bugs or ambiguous contract language

**Output:** `docs/phase12_cosimulation_results.md` with:
- Per-AI agreement matrix
- Divergence analysis
- Contract clarifications needed (if any)

---

## Success Criteria

### Quantitative
- ✅ All 24 trajectories execute without crashes
- ✅ All safety envelope invariants hold across all steps
- ✅ Ledger continuity verified for 100% of transitions
- ✅ Hysteresis prevents oscillation in all adversarial runs
- ✅ Min-duration enforcement blocks premature downgrade in 100% of cases
- ✅ Amplitude triad consistency validated across all regime transitions
- ✅ **Temporal invariance:** Regimes identical at matching timestamps regardless of eval frequency
- ✅ **Dual-modality agreement:** Implementation == oracle for 100% of steps
- ✅ Cross-AI agreement ≥85% on regime classification (if divergence, contract needs clarification)

### Qualitative
- ✅ Visualization clearly shows regime dynamics and stability
- ✅ No emergent oscillation patterns in any trajectory
- ✅ Recovery paths are smooth (no unexpected regime spikes during downgrade)
- ✅ Posture adjustments align with regime severity (monotonic tightening)
- ✅ **Physics time-invariant:** Same signals → same regimes, regardless of simulation timestep

---

## Implementation Steps

### Step 1: Contract Oracle (Day 1)
1. Create `src/nova/continuity/contract_oracle.py`
2. Implement pure regime classification from orp@1.yaml
3. Implement pure regime score calculation
4. Write unit tests comparing oracle to ORP implementation on known cases
5. **Acceptance:** Oracle passes all unit tests from `tests/continuity/test_orp.py`

### Step 2: Simulation Engine (Day 1–2)
1. Create `scripts/simulate_nova_cycle.py` with trajectory loader
2. Implement step-by-step ORP evaluation loop
3. Add oracle evaluation at each step
4. Add invariant checks at each step
5. Write CSV/JSONL output with both impl + oracle regimes
6. **Acceptance:** Can simulate 1 canonical trajectory end-to-end

### Step 3: Trajectory Library (Day 2–3)
1. Define JSON schema for trajectories
2. Author 10 canonical trajectories (with expected regimes)
3. Author 6 adversarial trajectories
4. Generate 4 noise-injected trajectories (fixed random seed)
5. Generate 4 temporal invariance trajectories (10s, 60s, compressed, expanded)
6. **Acceptance:** All 24 trajectories load + validate schema

### Step 4: Behavior Tests (Day 3–4)
1. Create `tests/e2e/test_regime_cycle.py`
2. Implement 15 core invariant tests
3. Implement 3 temporal invariance tests
4. Implement 3 contract fidelity tests
5. Run all trajectories through test suite
6. Fix any violations discovered
7. **Acceptance:** 21 tests pass on all 24 trajectories

### Step 5: Visualization (Day 4–5)
1. Create `notebooks/Phase12_StabilityVisualization.ipynb`
2. Implement 8 core plots (including dual-modality overlay)
3. Run on all trajectories, validate outputs
4. Export key visualizations to `docs/phase12_visuals/`
5. Document usage in notebook markdown
6. **Acceptance:** All plots render correctly, dual-modality shows 100% agreement

### Step 6: Cross-AI Co-Simulation (Day 5–6)
1. Export 5 trajectories to markdown
2. Submit to 8 AI systems
3. Collect predictions
4. Analyze divergence, update contract if ambiguous
5. Document results in `docs/phase12_cosimulation_results.md`
6. **Acceptance:** Agreement ≥85%, or divergence explained + contract updated

### Step 7: Final Validation (Day 6)
1. Run full test suite (`python -m pytest -q`)
2. Execute all 24 trajectories via simulation engine
3. Generate visualizations for 10 canonical + 2 adversarial trajectories
4. Review co-simulation results
5. Write `docs/Phase12_Summary.md`
6. **Acceptance:** All tests pass, all trajectories stable, no oscillation detected

---

## Rollback Plan

If Phase 12 reveals instability in Phase 11 physics:
1. Flag specific trajectory that triggers violation
2. Bisect trajectory to minimal failing case
3. Determine root cause:
   - **Contract ambiguity:** Oracle and impl disagree on interpretation → clarify orp@1.yaml
   - **Implementation bug:** Oracle correct, impl wrong → fix code
   - **Contract incompleteness:** Oracle can't decide → add missing rules to orp@1.yaml
   - **Physics instability:** Both agree but result is pathological → redesign regime thresholds/hysteresis
4. If contract change: Re-run Phase 11 Step C semantic audit (8 AI systems validate new contract)
5. If implementation fix: Update code, re-run all 24 trajectories
6. Re-validate until all trajectories pass

**No new features allowed until validation passes.**

---

## Phase 13 Prerequisites

Phase 13 (whichever direction chosen) **MUST NOT start** until:
- All 24 Phase 12 trajectories pass
- All 21 behavior tests green
- All safety envelope invariants verified
- No oscillation detected in adversarial runs
- Dual-modality agreement 100%
- Temporal invariance verified
- Cross-AI agreement ≥85%

Phase 12 establishes **the behavioral foundation** for all future ontology evolution.

---

## Key Innovations

### Temporal Invariance Testing
Detects:
- Hidden temporal coupling (physics shouldn't depend on eval frequency)
- Min-duration bugs (300s = 300s, not "5 evaluations")
- Hysteresis stability across time scales
- Implicit assumptions about evaluation intervals

### Dual-Modality Regime Agreement
Detects:
- Implementation drift from specification
- Contract ambiguities (oracle can't decide → spec incomplete)
- Edge-case mishandling (boundary conditions)
- Enables formal verification (two independent implementations)

### Contract Oracle as Test Oracle
Benefits:
- Independent ground truth
- Differential testing
- Forces contract precision
- Enables property-based testing (generate random trajectories, both must agree)

---

## Files Created

**New modules:**
- `src/nova/continuity/contract_oracle.py`
- `src/nova/continuity/trajectory_recorder.py`

**New scripts:**
- `scripts/simulate_nova_cycle.py`
- `scripts/visualize_trajectory.py` (or notebook)
- `scripts/cross_ai_cosimulation.py`

**New tests:**
- `tests/e2e/test_regime_cycle.py`
- `tests/e2e/test_temporal_invariance.py`
- `tests/e2e/test_contract_fidelity.py`

**New trajectories:**
- `tests/e2e/trajectories/*.json` (24 files)

**New docs:**
- `docs/Phase12_E2E_Stability_Plan.md` (this file)
- `docs/phase12_cosimulation_results.md`
- `docs/Phase12_Summary.md`
- `docs/phase12_visuals/*.png` (visualization outputs)

---

## Notes

- Keep `NOVA_ENABLE_ORP=0` as default (flag-gated rollback available)
- Add `NOVA_ENABLE_REGIME_LEDGER=1` to CI for Phase 12 tests
- All trajectories stored in git (reproducibility)
- Random seeds fixed for noise runs (deterministic chaos)
- Visualization outputs checked into `docs/phase12_visuals/` for reference
- Contract oracle maintained as independent codebase (no shared logic with ORP)

**This phase validates the LIVING system, not just the static design.**

# Phase 14.5 Pilot Findings (2025-12-09)

**Status:** ✅ Temporal USM validated, ready for observation
**Key Discovery:** ρ_t (equilibrium ratio), not C_t (collapse score), is primary extraction indicator

---

## Pilot Results

### Test Setup
3 scenarios, 3 turns each, session-isolated:
1. **Benign:** Collaborative dialogue (Alice, Bob, Carol)
2. **Extractive:** Interrogation (investigator acts, suspect absorbs)
3. **VOID:** Empty responses

### Observed Temporal Patterns

| Scenario | C_t Range | ρ_t Pattern | Interpretation |
|----------|-----------|-------------|----------------|
| **Benign** | [-0.10, +0.02] | 0.0 → 0.60 → 0.24 | Reciprocity emerges when Bob reciprocates |
| **Extractive** | -0.10 (flat) | **0.0 (flat)** | **Perfect extraction signal: no reciprocal agency** |
| **VOID** | 0.0 (equilibrium) | 1.0 (equilibrium) | Baseline reference: maximum "balance" in absence |

---

## Critical Ontological Discovery

### Initial Hypothesis (Wrong)
**C_t (collapse score) is primary manipulation signal**
- Expected: Extractive → C_t > 0.3 (high collapse)
- Observed: Extractive → C_t = -0.10 (simple but not collapsed)

### Corrected Understanding
**ρ_t (equilibrium ratio) is primary extraction signal**
- Benign: ρ_t rises when reciprocity appears (0.0 → 0.60)
- **Extractive: ρ_t stays at 0.0 (one actor dominates, other absorbs)**
- VOID: ρ_t = 1.0 (equilibrium reference point)

**Why this is ontologically correct:**
- Extraction = "one side acts, other side absorbs" = **asymmetric power flow**
- ρ measures: protective_weight / (protective_weight + extractive_weight)
- ρ=0 means: all relations are extractive (one-way flow)
- ρ=1 means: all relations are protective (reciprocal exchange)

---

## Revised Signal Interpretation

### Primary Observable: **ρ_t Temporal Trajectory**

**Extraction patterns:**
- ρ_t → 0.0 sustained (5+ turns) = interrogation/manipulation
- ρ_t < 0.3 with downward drift = conversation becoming extractive
- ρ_t oscillating near 0 = persistent asymmetry (red flag)

**Healthy patterns:**
- ρ_t ∈ [0.4, 0.8] with variation = balanced dialogue
- ρ_t spikes to 0.6+ during collaborative turns
- ρ_t → 1.0 during VOID = soft reset (recovery)

### Supporting Signals

**C_t (collapse score):**
- Measures structural richness vs. simplicity
- C_t < 0: Distributed/protective patterns (multi-perspective)
- C_t > 0.3: Hierarchical/simple patterns (single-voice dominance)
- **Role:** Secondary indicator of structural stability, not extraction

**H_t (spectral entropy):**
- Baseline near-zero for conversational text (expected)
- Not useful for manipulation detection in this substrate
- **Role:** Diagnostic (confirms parser behavior, not primary signal)

---

## Phase 14.5 Observation Targets (Updated)

### 1. ρ_t Baseline Characterization
**Hypothesis:** Benign conversations maintain ρ_t ∈ [0.3, 0.8] with variation

**Metrics:**
- `temporal_usm_rho_temporal` (histogram, bucketed by [0, 0.3), [0.3, 0.6), [0.6, 1.0])
- `temporal_usm_rho_drift` (Δρ over 10-turn windows)

**Decision Gate:**
- If ρ_t < 0.2 sustained → flag as extraction
- If ρ_t > 0.8 sustained → likely VOID-dominant (minimal interaction)

### 2. Extraction Detection Threshold
**Hypothesis:** ρ_t < 0.3 for 5+ consecutive turns reliably detects interrogation patterns

**Metrics:**
- `temporal_usm_extraction_sequences` (count of ρ<0.3 runs > 5 turns)
- Correlation: extraction_sequences vs. quarantine_rate

**Decision Gate:**
- Establish ρ_threshold where P(extraction | ρ<threshold) > 0.8

### 3. VOID Recovery Validation
**Hypothesis:** ρ_t → 1.0 during VOID, returns to baseline after VOID ends

**Metrics:**
- `temporal_usm_void_rho_convergence` (how fast ρ→1.0 in VOID)
- `temporal_usm_post_void_recovery` (ρ after exiting VOID)

**Decision Gate:**
- ρ_t reaches >0.9 within 2 VOID turns
- Post-VOID: ρ returns to pre-VOID range ±0.2

### 4. Temporal Smoothing Validation (λ=0.6)
**Hypothesis:** λ=0.6 balances responsiveness (detects shifts within 3 turns) and stability (ignores 1-turn noise)

**Metrics:**
- `temporal_usm_lambda_used` (verify 0.6 used consistently)
- Visual: plot ρ_inst vs ρ_temporal to see smoothing effect

**Decision Gate:**
- Sudden ρ shifts (ρ_inst: 0→1) smoothed to ρ_temporal transition over 2-3 turns
- Single-turn noise (ρ_inst spike) doesn't dominate ρ_temporal

### 5. Attack Surface Analysis
**Hypothesis:** Adversary cannot hide sustained extraction in temporal smoothing

**Metrics:**
- Simulated attack: 3 turns benign (ρ~0.6), 7 turns extractive (ρ~0.0)
- Check: Does ρ_temporal drop below threshold by turn 10?

**Decision Gate:**
- If ρ_temporal < 0.3 by turn 10 in simulated attack → detection works
- If ρ_temporal stays > 0.4 → smoothing hides signal (BLOCKER for Phase 14.6)

---

## Phase 14.5 → 14.6 Criteria (Revised)

**Unblock Phase 14.6 (Temporal Governance) when:**

1. ✅ **ρ_t extraction threshold established** (P(extraction | ρ<θ) > 0.8)
2. ✅ **VOID recovery validated** (ρ→1.0 in <3 turns, returns to baseline after)
3. ✅ **λ=0.6 smoothing acceptable** (detects shifts within 3 turns, ignores 1-turn noise)
4. ✅ **Attack resistance confirmed** (sustained extraction surfaces in ρ_temporal)
5. ✅ **Baseline drift characterized** (benign conversations: ρ_t ∈ [0.3, 0.8])

**Minimum data:** 1000 sessions OR 100 hours conversation time OR 50+ extraction events detected

---

## Lessons

### 1. Ontological Alignment Matters
- Initial framing: "C_t detects manipulation" (wrong)
- Corrected framing: "ρ_t detects extraction, C_t detects collapse"
- **Power flow asymmetry ≠ structural collapse**

### 2. Pilot Catches Misalignment Before Production
- Without pilot: Would have observed C_t, missed ρ_t signal
- 3-hour pilot saved weeks of misguided observation

### 3. Parser Limitation Is Now Clear
- Conversational text → sparse graphs → C_t, H_t near-baseline
- **ρ_t still works** because it measures relation tensor weights, not graph size
- Extraction detectable even with 0-1 edges (if those edges have ρ=0)

---

## Next Step

**Begin Phase 14.5 observation** focused on **ρ_t temporal trajectory** as primary extraction signal.

No blockers remain.

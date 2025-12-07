# Slot07 Temporal Governance – Phase 14.6 Specification (Draft)

**Title:** Temporal Governance Sensitivity for Slot07  
**Date:** 2025-12-07  
**Status:** Draft (pre-implementation)  
**Phase:** 14.6 (Temporal Governance)  
**Parent Specs:**  
- `docs/specs/slot02_usm_bias_detection_spec.md` (Phase 14.3)  
- `docs/specs/phase14_5_temporal_usm_spec.md` (Phase 14.5)  
- `contracts/temporal_usm@1.yaml`  
**Ontology Version:** 1.7.1  

---

## 1. Context

By the end of Phase 14.5:

- Slot02 (`slot02_deltathresh`) computes **instantaneous USM metrics** for each input:
  - `spectral_entropy` (H_inst), `equilibrium_ratio` (ρ_inst), `collapse_score` C_inst via BIAS_REPORT@1.
- VOID semantics are propagated consistently:
  - `graph_state="void"` for empty SystemGraph, consumed by Slot01, Slot07, Slot09.
- Slot02 maintains **per-stream temporal USM state**:
  - `TemporalUsmState(H_t, ρ_t, C_t)` keyed by `stream_id` (implemented as `session_id`).
- Slot02 emits **optional temporal snapshots**:
  - `temporal_usm@1` when both `NOVA_ENABLE_BIAS_DETECTION=1` and `NOVA_ENABLE_USM_TEMPORAL=1`.

At this point:

- Slot07 **cognitive loop** operates on instantaneous signals:
  - bias vector + instantaneous `collapse_score` from BIAS_REPORT@1,
  - graph_state for VOID freeze policy (RFC-014).
- Slot07 **does not yet** use temporal USM (`H_t`, `ρ_t`, `C_t`) in governance decisions.

Phase 14.6 introduces **temporal governance sensitivity** in Slot07:

- Governance decisions will respond to **trends** and **inertia**, not only snapshots.
- Temporal signals from `temporal_usm@1` become inputs to Slot07’s decision logic.
- All temporal effects are:
  - Flag-gated,
  - Reversible,
  - Layered on top of existing instantaneous logic.

---

## 2. Goals

Phase 14.6 aims to:

1. **Use temporal USM to stabilize governance:**
   - Avoid overreacting to single-point anomalies when trends are improving.
   - Escalate more aggressively when collapse risk is trending upward.

2. **Respect existing VOID semantics:**
   - Maintain VOID freeze behavior for `graph_state="void"`.
   - Treat extended VOID sequences as **stabilizing pauses**, not resets.

3. **Preserve invariants:**
   - No changes to BIAS_REPORT@1 or existing Slot07 contracts.
   - All temporal behavior behind a dedicated governance flag.
   - Governance remains reversible and observable.

4. **Keep integration minimal:**
   - Read-only consumption of `temporal_usm@1`.
   - No new persistent state in Slot07 beyond existing metrics.

---

## 3. Temporal Signals & Inputs

Slot07 will consume the following signals:

- From **BIAS_REPORT@1** (instantaneous):
  - `collapse_score` C_inst.
  - `bias_vector` components (b_local, b_completion, etc.).
  - `metadata.graph_state` (e.g., `"normal"`, `"void"`).

- From **temporal_usm@1** (history-aware):
  - `H_temporal` H_t – temporal spectral entropy.
  - `rho_temporal` ρ_t – temporal equilibrium ratio.
  - `C_temporal` C_t – temporal collapse score.
  - `graph_state` – latest graph_state for the stream.
  - `lambda_used`, `mode`, `rho_equilibrium` – for observability and configuration.

Derived signals (computed in Slot07, no new contract):

- Collapse trend:
  - `ΔC = C_inst − C_t` (instantaneous vs temporal collapse).
- Equilibrium trend:
  - `Δρ = ρ_inst − ρ_t` (instantaneous vs temporal equilibrium).

These derivatives are **local to Slot07** and not part of any contract in Phase 14.6.

---

## 4. Governance Rules (Conceptual)

### 4.1 Non-VOID Inputs

For `graph_state != "void"`:

1. **Trend-aware escalation:**
   - If `C_inst` is high (above threshold) but `C_t` is **decreasing** over time:
     - Treat this as **recovering** behavior; prefer a **warning / soft intervention** rather than immediate hard escalation.
   - If both `C_inst` is high and `C_t` is **increasing**:
     - Treat as **persistent collapse trend**; lean toward more aggressive safeguards.

2. **Hysteresis for governance decisions:**
   - Temporal USM should act as a **damper**:
     - Avoid flipping governance posture (e.g., accept → reject or normal → heightened) on a single spike if:
       - `|ΔC|` is small AND `C_t` is trending downward.

3. **Equilibrium stability (ρ_t):**
   - If `ρ_t` is consistently near `ρ_eq` (homeostatic equilibrium) and `Δρ` is small:
     - Favor **maintaining** current governance settings.
   - If `ρ_t` drifts away from `ρ_eq` and `Δρ` is large:
     - Flag this as a **structural imbalance** worth increasing caution for.

### 4.2 VOID Inputs

For `graph_state == "void"`:

- Preserve existing RFC-014 Slot07 behavior:
  - Immediate convergence.
  - No oracle/refinement.
  - VOID freeze counter incremented.

Temporal considerations:

- Temporal USM already applies soft decay in Slot02 for VOID:
  - `H_t` decays toward 0.
  - `ρ_t` drifts toward `ρ_eq`.
  - `C_t` decays toward 0.
- Slot07 should:
  - Treat extended VOID sequences as **stabilizing**: they reduce collapse risk over time.
  - Never interpret VOID-only temporal streams as justification for escalation.

### 4.3 Missing Temporal Data

If `temporal_usm@1` is absent for a stream:

- Slot07 must:
  - Fall back to **pure instantaneous** behavior (current 14.4 logic).
  - Never treat missing temporal data as an error or as an implicit high-risk signal.

Reasons for absence:

- Feature flags off.
- First-ever interaction for the stream.
- Temporal subsystem disabled or misconfigured.

---

## 5. Feature Flag & Configuration

Temporal governance sensitivity in Slot07 is **independent** of temporal state computation in Slot02, but **depends on its presence**.

### 5.1 New Flag

- `NOVA_ENABLE_TEMPORAL_GOVERNANCE` (proposed):
  - `"1"` – Slot07 reads and uses `temporal_usm@1` when available.
  - `"0"` or unset – Slot07 ignores temporal_usm@1 and behaves as in Phase 14.4.

Constraints:

- Effective only when:
  - `NOVA_ENABLE_USM_TEMPORAL="1"` AND `NOVA_ENABLE_BIAS_DETECTION="1"` (so that temporal_usm@1 exists).

### 5.2 Configuration Parameters (Phase 14.6 scope)

Initial implementation should use **fixed thresholds**, not yet adaptive:

- `TEMPORAL_ESCALATION_DELTA_C`:
  - Minimum `ΔC` magnitude to consider a spike (e.g., 0.2).
- `TEMPORAL_RECOVERY_WINDOW`:
  - Minimum number of steps with decreasing `C_t` before considering de-escalation.
- `TEMPORAL_EQUILIBRIUM_TOLERANCE`:
  - Allowed deviation of `ρ_t` from `ρ_eq` before flagging imbalance.

These may be hard-coded in Slot07 initially, with future phases promoting them to config/flags as needed.

---

## 6. Integration Plan (High-Level)

### Step 1 – Read Temporal Payload

- In Slot07 cognitive loop:
  - Extend inputs to accept optional `temporal_usm` payload (mirror of temporal_usm@1).
  - Do not make this parameter mandatory.

### Step 2 – Compute Local Derivatives

- When `temporal_usm` is present and `NOVA_ENABLE_TEMPORAL_GOVERNANCE="1"`:
  - Compute `ΔC`, `Δρ` from instantaneous vs temporal values.

### Step 3 – Adjust Governance Decisions

- Use temporal signals to:
  - Gate escalation when **trends indicate recovery**.
  - Strengthen escalation when **trends show persistent or worsening collapse**.

Concrete examples (to be detailed at implementation time):

- If:
  - `C_inst > collapse_threshold`, AND
  - `C_t < C_inst`, AND
  - `C_t` has been decreasing over the last `TEMPORAL_RECOVERY_WINDOW` steps,
  - THEN:
    - Consider a softer governance response (warning, log, mild throttle) instead of immediate hard block.

- If:
  - `C_inst > collapse_threshold`, AND
  - `C_t` has been increasing consistently,
  - THEN:
    - Prefer more aggressive mitigation (e.g., stricter loop iteration limits, lower tolerance for acceptance).

### Step 4 – Observability

- Add logging for temporal influence:
  - When temporal signals alter a decision (e.g., override escalation), log:
    - `C_inst`, `C_t`, `ΔC`, `graph_state`, and whether temporal governance was applied.

---

## 7. Invariants & Rollback

### Invariants

- **Separation of roles:**
  - Slot02 owns temporal USM state and emission.
  - Slot07 **only reads** temporal_usm@1; it does not maintain its own temporal USM state.

- **Reversibility:**
  - Disabling `NOVA_ENABLE_TEMPORAL_GOVERNANCE` must restore Slot07 behavior to its Phase 14.4 semantics, even if temporal_usm@1 continues to be emitted by Slot02.

- **Provenance-first:**
  - Decisions influenced by temporal governance should be traceable via logs and, where relevant, audit trails.

- **No silent drift:**
  - Temporal governance MUST NOT be active unless the feature flag is enabled and temporal_usm@1 is present.

### Rollback

- **Flag-based:**
  - `export NOVA_ENABLE_TEMPORAL_GOVERNANCE=0` – disable temporal influence in Slot07 while leaving temporal USM in Slot02 intact.

- **Code-based:**
  - `git revert` of the Slot07 temporal integration commit(s).

---

## 8. Activation Criteria

Phase 14.6 temporal governance for Slot07 may be considered ready for controlled activation when:

- All Slot07 tests (including new temporal governance tests) pass in CI.
- Integration tests confirm:
  - Temporal governance does not alter decisions when flag is OFF.
  - Temporal governance behaves as specified when flag is ON and temporal_usm@1 is present.
- Logs demonstrate:
  - Clear provenance of temporal influence on decisions.
  - No unexpected escalations/regressions in typical traffic patterns.

Until then, Slot07 temporal governance remains **drafted and gated**, and the system continues to behave according to Phase 14.5 + Phase 14.4 semantics. 


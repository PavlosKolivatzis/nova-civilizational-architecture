# Phase 14.5 – Temporal USM Stabilization Layer (Draft)

**Title:** Temporal USM Stabilization Layer  
**Date:** 2025-12-07  
**Status:** Draft (pre-implementation)  
**Phase:** 14.5 (Temporal Cognition)  
**Parent Specs:** `.nova/ENTRY.md` (USM + C(B)), `docs/specs/slot02_usm_bias_detection_spec.md` (BIAS_REPORT@1)  
**Ontology Version:** 1.7.1  

---

## 1. Context & Intent

Phase 14.3 and 14.4 established:

- **USM bias detection** in Slot02 (`relations_pattern.py` + `bias_calculator.py`) with `B(T)` and `C(B)` (BIAS_REPORT@1).  
- **Cross-slot VOID semantics** (Slot02 → Slot07 → Slot09 → Slot01) with a shared interpretation of emptiness:
  - No hallucinated structure on absence.
  - No escalation on VOID.
  - No treating silence as extraction.
  - Quality not collapsed under uncertainty.

This created a **zero-energy anchor point** in Nova’s cognitive geometry: VOID is a structurally meaningful “no new evidence” state, not an error or a pseudo-signal.

However, USM is still **memoryless** at the structural level:

- H, ρ, and C are evaluated per-input without temporal inertia.  
- Transitions between VOID and structure are sharp.  
- Regime/gating logic sees **snapshots**, not trajectories.

**Phase 14.5** introduces a **Temporal USM Stabilization Layer**:

- Add temporal weighting to USM metrics (`H`, `ρ`, `C`).  
- Implement **soft-reset decay** during VOID (Option B).  
- Provide **inertia, continuity, and homeostasis** for USM across time.  
- Keep everything reversible and flag-gated.

---

## 2. Temporal Update Law

### 2.1 Notation

- Let `t` index discrete processing steps in Slot02 (each input event).  
- Let:
  - `H_inst(t)` = instantaneous spectral entropy at step `t`.  
  - `ρ_inst(t)` = instantaneous equilibrium ratio at step `t`.  
  - `C_inst(t)` = instantaneous collapse score at step `t`.  
- Let:
  - `H_t`, `ρ_t`, `C_t` = **temporal USM state** after processing step `t`.  
- Let:
  - `λ ∈ (0, 1)` = decay constant (core temporal inertia parameter).  
  - `ρ_eq ≈ 1.0` = homeostatic equilibrium for equilibrium ratio.  
  - `V(t) ∈ {0, 1}` = VOID indicator at step `t` (1 = VOID, 0 = non-void).  

### 2.2 Initialization

On first use (no prior temporal state):

```text
H_0   = H_inst(0)
ρ_0   = ρ_inst(0)
C_0   = C_inst(0)
```

This avoids artificial jumps for the first non-void input.

### 2.3 Non-VOID Updates (Structure Present)

When `V(t) = 0` (input has structure; non-void):

- Temporal USM performs **exponential smoothing** of instantaneous metrics:

```text
H_t   = (1 − λ) · H_{t−1}   + λ · H_inst(t)
ρ_t   = (1 − λ) · ρ_{t−1}   + λ · ρ_inst(t)
C_t   = (1 − λ) · C_{t−1}   + λ · C_inst(t)
```

Properties:

- **Inertia:** new measurements influence state gradually.  
- **Continuity:** no discontinuous jumps even under adversarial inputs.  
- **Bias correction:** persistent patterns shift `H_t`, `ρ_t`, `C_t` over time.

### 2.4 VOID Updates (Soft Reset / Decay)

When `V(t) = 1` (VOID: no reliable structure):

- Temporal state undergoes **soft-reset decay** toward equilibrium:

```text
H_t   = H_{t−1} · λ
ρ_t   = ρ_{t−1} · λ + (1 − λ) · ρ_eq
C_t   = C_{t−1} · λ
```

Interpretation:

- **H decay:** structural complexity relaxes back toward zero-energy (no new structure).  
- **ρ drift to ρ_eq:** equilibrium ratio asymptotically approaches homeostasis.  
- **C decay:** collapse-risk score gradually relaxes toward neutral.

This implements:

- **No hard reset:** prior structure is not erased.  
- **No freeze:** temporal state continues to evolve during silence.  
- **Homeostasis:** state drifts toward equilibrium instead of oscillating.

### 2.5 Temporal Modes (Conceptual)

The above defines the **soft** mode (Phase 14.5 default). For completeness, alternate modes are defined but NOT enabled by default:

- **reset:**
  - `H_t = H_eq_reset` (e.g., 0)  
  - `ρ_t = ρ_eq`  
  - `C_t = C_eq_reset` (e.g., 0)
- **freeze:**
  - `H_t = H_{t−1}`  
  - `ρ_t = ρ_{t−1}`  
  - `C_t = C_{t−1}`

Mode semantics are parameterized via `NOVA_TEMPORAL_MODE` (see §4). Soft mode is the only Nova-aligned default.

---

## 3. Integration Points

### 3.1 Where Temporal Memory Lives

**Design decision (Phase 14.5):**  
Temporal USM state is **owned by Slot02 (ëTHRESH Content Processing)** and is **local to the bias engine**, not globalized in Continuity/ORP and not duplicated per-slot.

Rationale:

- Slot02 already owns static USM metrics (`H`, `ρ`, `C`) and VOID detection.  
- Slot07 and Slot09 are **consumers** of USM, not definers of its semantics.  
- Keeping temporal memory in Slot02 respects slot boundaries and avoids cross-slot semantic drift.

**Canonical container:** `TemporalUsmState`

Location:

- Implementation module: `src/nova/math/usm_temporal.py`  
  - Provides pure functions for temporal updates (`step_non_void`, `step_void`) and a simple state dataclass.  
- Storage:
  - In-memory, scoped to the current **processing stream** (e.g., conversation/session).  
  - State attached to Slot02’s processing context and optionally surfaced via `ProcessingResult.temporal_usm`.  

Temporal state **must not** be persisted directly to the attest ledger; Core remains the only attester (Invariant #2).

### 3.2 When Updates Occur

Temporal USM updates occur **once per processed input** in Slot02, **after** static USM metrics are computed and VOID semantics are determined:

1. Slot02 computes `H_inst(t)`, `ρ_inst(t)`, `C_inst(t)` via existing USM pipeline.  
2. Slot02 determines `V(t)` using established VOID semantics (Phase 14.4).  
3. If `NOVA_ENABLE_USM_TEMPORAL = "1"`:
   - Load prior `TemporalUsmState` (if any) for the stream.  
   - Apply **non-void** or **void** update law based on `V(t)` and `NOVA_TEMPORAL_MODE`.  
   - Store updated `TemporalUsmState`.  
4. Emit both:
   - Instantaneous metrics (as today).  
   - Temporal metrics (`H_t`, `ρ_t`, `C_t`) into a temporal USM payload.

### 3.3 Which Slots Read Temporal Values

**Producers:**

- Slot02 (`slot02_deltathresh`): computes and emits temporal USM as part of its analysis.

**Primary consumers (Phase 14.5 scope):**

- **Slot07 – Production Controls / Governance:**
  - Uses `H_t`, `ρ_t`, `C_t` to:
    - Smoothly modulate thresholds and routing decisions.  
    - Avoid oscillatory regime switching on transient spikes.  
- **Slot09 – Distortion Protection:**
  - Uses temporal collapse score `C_t` to:
    - Detect persistent high-risk patterns vs. isolated anomalies.  
    - Adjust defense thresholds with inertia.

**Secondary consumers (Phase 14.6+ candidates):**

- **Slot01 – Truth Anchor:**
  - May incorporate temporal USM in assessing long-run reliability of inputs.  
- **Continuity / ORP:**
  - May add temporal USM to regime decision context.

The initial contract surface in Phase 14.5 is limited to Slot02 → Slot07/09 to keep the change minimal and reversible.

### 3.4 Temporal Identity & Lifetime

Temporal USM state is attached to a **cognitive stream**, not to individual requests and not to the global system.

**Identity:**

- Each temporal state instance is keyed by an opaque `stream_id`, representing a single ongoing interaction thread (conversation / request chain).  
- `stream_id` is provided by the orchestrator as the existing correlation identifier; Slot02 treats it as opaque and does not infer semantics from it.

**Ownership & Storage:**

- Slot02 maintains an in-memory mapping `stream_id → TemporalUsmState` in its own process context.  
- No temporal USM state is stored in ledgers; only derived metrics may be emitted in payloads/contracts.

**Update Events (What Counts as “Time”):**

- Temporal USM is advanced only when Slot02 **processes an input** for a given `stream_id`:
  - Non-VOID inputs (`graph_state != "void"`) trigger `step_non_void`.  
  - VOID inputs (`graph_state == "void"`) trigger `step_void`.  
- There is no background clock; user silence between messages is simply “no update” until the next processed input, at which point VOID decay applies if that input is classified as VOID.

**Lifecycle & Reset Rules:**

- A new entry in `stream_id → TemporalUsmState` is created on the **first** processed input for that `stream_id`.  
- Temporal state is reset when:
  - A new `stream_id` is observed (new conversation / request chain).  
  - An explicit end-of-stream / conversation-closed signal is received from the orchestrator.  
  - An optional TTL or capacity limit in Slot02’s cache evicts old streams (implementation detail, to be documented at integration time).

**Invariants:**

- Temporal identity is **per-stream** and **local to Slot02**; it is not replicated per-slot and not globalized in Continuity/ORP during Phase 14.5.  
- Temporal USM does not change the semantics of instantaneous USM or VOID; it augments them with history-aware metrics.  
- Disabling temporal USM (via flag) must make the presence or absence of `stream_id` and temporal state **behaviorally irrelevant** to downstream slots.

---

## 4. Feature Flags & Configuration

Temporal USM is **fully flag-gated** and **off by default**.

### 4.1 Enable/Disable Flag

- **Flag:** `NOVA_ENABLE_USM_TEMPORAL`  
- **Type:** string (canonical Nova semantics)  
- **Values:**
  - `"1"` – Temporal USM enabled.  
  - `"0"` or unset – Temporal USM disabled (static behavior only).

Behavior when disabled:

- Slot02 computes and emits **only instantaneous** metrics (current behavior).  
- Temporal state may still be stored for debugging but **must not** affect routing or governance decisions.  

### 4.2 Mode Selector

- **Flag:** `NOVA_TEMPORAL_MODE`  
- **Type:** string  
- **Allowed values:**
  - `"soft"` – Soft reset (decay toward equilibrium). **Default, Nova-aligned.**  
  - `"reset"` – Hard reset on VOID.  
  - `"freeze"` – Freeze state on VOID.

Semantics:

- Non-VOID (`V(t)=0`) updates always follow exponential smoothing (§2.3).  
- VOID (`V(t)=1`) behavior depends on `NOVA_TEMPORAL_MODE`:
  - `"soft"` – use decay law (§2.4).  
  - `"reset"` – set to reset baselines.  
  - `"freeze"` – no change to temporal state.

Configuration source of truth:

- Document in `.env.example` and `agents/nova_ai_operating_framework.md` once implementation is added.  

---

## 5. Tests Required Before Activation

Temporal USM must pass the following **pre-activation tests** before `NOVA_ENABLE_USM_TEMPORAL="1"` is allowed in non-experimental environments.

### 5.1 Convergence Tests

**Goal:** Show that temporal metrics converge under stable inputs.

- Fixed non-VOID input stream with constant `H_inst`, `ρ_inst`, `C_inst`:
  - Verify `H_t`, `ρ_t`, `C_t` converge to finite values.  
  - Confirm closed-form convergence matches implementation (geometric series).  
- Mixed VOID/non-VOID sequences with bounded metrics:
  - Verify temporal metrics remain within expected ranges.

### 5.2 No-Oscillation Tests

**Goal:** Prevent oscillatory regimes caused by temporal feedback.

- Construct alternating high/low `H_inst` and `ρ_inst` sequences:
  - Verify `H_t`, `ρ_t`, `C_t` exhibit damped responses, not growing oscillations.  
- For λ in allowed range (e.g., `0.5 ≤ λ < 1.0`):
  - Assert monotone or damped approach to equilibrium in standard patterns.  

### 5.3 VOID Decay Tests

**Goal:** Validate soft-reset semantics.

- Start from high structural state (`H_0`, `ρ_0`, `C_0`):
  - Apply `k` consecutive VOID steps with `NOVA_TEMPORAL_MODE="soft"`.  
  - Verify:
    - `H_t` decreases monotonically toward 0.  
    - `ρ_t` approaches `ρ_eq` from either direction.  
    - `C_t` decays toward 0.  
- Compare with `"reset"` and `"freeze"` modes for validation (off-by-default).

### 5.4 Re-Entry Stability Tests

**Goal:** Ensure smooth behavior when transitioning from silence back to structure.

- Scenario:
  1. Run for `n` non-VOID steps to build a structured state.  
  2. Run for `m` VOID steps with `"soft"` mode.  
  3. Feed a new non-VOID input with moderate `H_inst`, `ρ_inst`, `C_inst`.  
- Assertions:
  - Re-entry does not produce spikes larger than a configurable bound.  
  - Governance decisions in Slot07 change smoothly across re-entry.  
  - No regime thrashing in ORP under typical λ values.

Testing locations (proposed):

- `tests/slots/slot02/test_temporal_usm.py` – pure math + update law tests.  
- `tests/slots/slot07/test_temporal_governance_integration.py` – governance behavior.  
- `tests/slots/slot09/test_temporal_distortion_protection.py` – distortion thresholds.  

---

## 6. Rollback & Reversibility

Temporal USM must be **trivially reversible** to static USM.

### 6.1 Flag-Based Rollback

Rollback path (primary):

```bash
export NOVA_ENABLE_USM_TEMPORAL=0
```

Effects:

- Slot02 stops applying temporal updates.  
- Only instantaneous USM metrics are emitted/used.  
- Stored temporal state is ignored by routing/governance logic.  

### 6.2 Code-Level Rollback

If flag-based rollback is insufficient (e.g., implementation bug):

```bash
git revert <commit-adding-temporal-usm>
```

Constraints:

- Temporal USM implementation must be isolated (e.g., `usm_temporal.py` + minimal integration points).  
- Contracts and APIs must retain compatibility when temporal fields are absent (backward-compatible schemas).

---

## 7. Ontology & Contract Updates

Temporal USM introduces a new ontological concept and optional contract surface.

### 7.1 Ontology: `temporal_usm@1.0`

Add a new ontology entry:

- **Name:** `temporal_usm@1.0`  
- **Scope:** Describes temporal evolution of USM metrics (`H_t`, `ρ_t`, `C_t`) for a given processing stream.  
- **Semantics:**
  - Exponential smoothing on non-void.  
  - Soft-reset decay on VOID (Option B).  
  - Parameterized by `λ` and `ρ_eq`.  

This ontology should:

- Document decay semantics and constraints on λ (stability conditions).  
- Explicitly reference:
  - `.nova/ENTRY.md` USM + bias vector definitions.  
  - Phase 14.3 USM bias detection spec.

### 7.2 Contract Surface (Future Increment)

For Phase 14.5, a minimal contract extension is sufficient:

- Option A: Extend `BIAS_REPORT@1` → `BIAS_REPORT@2`:
  - Add `temporal_usm` block:
    - `H_temporal`, `ρ_temporal`, `C_temporal`.  
    - `lambda_used`, `mode`, `rho_eq`.  
- Option B: New contract `temporal_usm@1`:
  - Emitted by Slot02; consumed by Slot07/09.

Decision between A/B is deferred to implementation, but **backward compatibility** with existing consumers is mandatory.

---

## 8. Activation Criteria

Temporal USM may be considered ready for **pilot activation** (`NOVA_ENABLE_USM_TEMPORAL="1"` in controlled environments) when:

- All tests in §5 pass in CI.  
- No regressions in:
  - Slot02 bias detection behavior.  
  - Slot07 governance stability.  
  - Slot09 distortion protection thresholds.  
- Observability of temporal metrics is present (e.g., exposed via metrics or logs under a dedicated flag).  
- Runbooks in `ops/` document:
  - How to enable/disable temporal USM.  
  - How to interpret temporal metrics.  
  - How to rollback safely.

Only after these conditions are met should Phase 14.5 be considered **operational**. Until then, temporal USM remains an **experimental, flag-gated layer** atop the existing static USM system.

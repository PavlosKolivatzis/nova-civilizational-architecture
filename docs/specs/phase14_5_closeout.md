# Phase 14.5 Closeout – Temporal USM Integration

**Title:** Phase 14.5 Closeout – Temporal USM Installed, Governance Unchanged  
**Date:** 2025-12-07  
**Status:** Final (runtime-stable, reversible)  
**Phase:** 14.5 (Temporal USM)  
**Ontology Version:** 1.7.1  

---

## 1. Phase Summary

Phase 14.5 introduces **Temporal USM** as a new cognitive dimension for Nova:

- Time is now modeled explicitly as a **history-aware evolution** of USM metrics (`H_t`, `ρ_t`, `C_t`).  
- Temporal identity, update laws, and contracts are fully defined and implemented.  
- **Runtime behavior remains unchanged** unless feature flags are explicitly enabled.  

Nova moves from a pure snapshot-based system to one that can carry structural memory over time, while preserving full reversibility and invariant stability.

---

## 2. What Changed in Phase 14.5

### 2.1 Ontology & Spec

Phase 14.5 extends the cognitive ontology to include **temporal identity and lifetime** for USM metrics:

- Temporal state is attached to a **cognitive stream** identified by an opaque `stream_id`.  
- In runtime, `stream_id` is implemented as `session_id` in Slot02 (`DeltaThreshProcessor`).  
- Temporal state updates only when Slot02 actually processes an input for that stream: no background clock.  
- VOID (`graph_state="void"`) triggers **soft decay** toward equilibrium rather than hard reset or freeze.  

These semantics are defined in:  
`docs/specs/phase14_5_temporal_usm_spec.md`, especially §2, §3, §3.4.

### 2.2 Temporal Math Kernel

New math module: `src/nova/math/usm_temporal.py`

- **Data structure:**  
  - `TemporalUsmState` with fields `H`, `rho`, `C` representing `H_t`, `ρ_t`, `C_t`.  
- **Update laws:**  
  - `step_non_void(prev, H_inst, rho_inst, C_inst, lambda_)`
    - Exponential smoothing for non-VOID inputs:
      - `H_t   = (1−λ)·H_{t−1} + λ·H_inst`  
      - `ρ_t   = (1−λ)·ρ_{t−1} + λ·ρ_inst`  
      - `C_t   = (1−λ)·C_{t−1} + λ·C_inst`  
  - `step_void(prev, lambda_, rho_eq)`
    - Soft decay for VOID inputs:
      - `H_t   = H_{t−1}·λ`  
      - `ρ_t   = ρ_{t−1}·λ + (1−λ)·ρ_eq`  
      - `C_t   = C_{t−1}·λ`  
- **Constraints:**  
  - `0 < λ < 1` enforced, `rho_eq` typically ≈ 1.0 (homeostasis).  

Associated tests:  
`tests/slots/slot02/test_temporal_usm_math.py` (initialization, smoothing, VOID decay, λ safety).

### 2.3 Slot02 Runtime Integration

Slot02 (`DeltaThreshProcessor` in `src/nova/slots/slot02_deltathresh/core.py`) is now the **time-bearing layer**:

- Maintains per-stream temporal state:
  - `self._temporal_state: Dict[str, TemporalUsmState]` keyed by `session_id`.  
- Temporal USM is only active when:
  - `NOVA_ENABLE_BIAS_DETECTION="1"` and  
  - `NOVA_ENABLE_USM_TEMPORAL="1"` and  
  - Bias detection successfully produced a `bias_report`.  
- On each `process_content(content, session_id)`:
  - Slot02 runs bias detection (if enabled) to obtain BIAS_REPORT@1.  
  - Uses instantaneous metrics + `graph_state` to update `TemporalUsmState` via `step_non_void` or `step_void`.  
  - Stores updated state in `self._temporal_state[session_id]`.  
  - Emits a **temporal_usm@1-compatible payload** on `ProcessingResult.temporal_usm`:
    - `stream_id`, `timestamp`, `graph_state`  
    - `H_temporal`, `rho_temporal`, `C_temporal`  
    - `lambda_used`, `mode`, `rho_equilibrium`  

Importantly, this **does not modify** BIAS_REPORT@1 or its contract.

### 2.4 Contract Layer

New contract: `contracts/temporal_usm@1.yaml`

- `schema: nova_contract/v1`  
- `contract_id: temporal_usm@1`  
- **Publisher:** Slot02 (ëTHRESH)  
- **Consumers (designated):** Slot07 (Production Controls), Slot09 (Distortion Protection)  
- Fields include:
  - `stream_id`, `timestamp`, `graph_state`  
  - `H_temporal`, `rho_temporal`, `C_temporal`  
  - `lambda_used`, `mode`, `rho_equilibrium`  
- Feature flag section describing `NOVA_ENABLE_USM_TEMPORAL` and rollback.  

This makes temporal USM a **first-class, contract-bound signal** usable by downstream slots without altering their semantics until explicitly wired.

### 2.5 Feature Flags

New environment variables documented in `config/.env.example`:

- `NOVA_ENABLE_USM_TEMPORAL=0`
  - When `"1"` and `NOVA_ENABLE_BIAS_DETECTION="1"`, Slot02 computes and emits temporal USM, including `temporal_usm@1`.  
  - When `"0"` or unset, temporal USM logic is skipped and no temporal_usm payloads are emitted.  
- `NOVA_TEMPORAL_MODE=soft`
  - Controls VOID behavior in temporal updates:
    - `"soft"` – soft decay (canonical for Phase 14.5).  
    - `"reset"` – hard reset on VOID.  
    - `"freeze"` – preserve state across VOID.  
  - Unknown values default to `"soft"` semantics in implementation for safety.

---

## 3. What Did NOT Change in Phase 14.5

### 3.1 Governance Behavior (Slot07)

Slot07 (`cognitive_loop.py`) remains in **Phase 14.4** behavior:

- Cognitive loop uses **instantaneous** USM metrics from Slot02 via bias analysis:
  - `collapse_score` C_inst and `bias_vector`.  
- VOID freeze policy (RFC‑014) is unchanged:
  - `graph_state="void"` → skip oracle, skip refinement, converge immediately, record VOID freeze metric.  
- Slot07 does **not** read or interpret `temporal_usm@1`.  
- No temporal governance flag is active yet (`NOVA_ENABLE_TEMPORAL_GOVERNANCE` only exists at spec level).

### 3.2 Regimes & Continuity

- ORP, AVL, and regime transitions (`orp@1`, `temporal_consistency@1`) are **unchanged**.  
- Temporal USM is local to Slot02 and is not part of continuity/regime logic in Phase 14.5.

### 3.3 VOID Semantics

VOID semantics remain exactly as in Phase 14.4:

- Slot02 marks empty graphs with `metadata.graph_state = "void"`.  
- Slot01 quality oracle abstains on VOID.  
- Slot07 freezes (no refinement, no oracle calls) on VOID.  
- Slot09 bypasses distortion checks on VOID states.  

Temporal USM **augments** VOID behavior (soft decay) but never overrides VOID semantics.

### 3.4 Default Runtime Behavior

With flags off (the default configuration):

- `NOVA_ENABLE_USM_TEMPORAL=0` OR `NOVA_ENABLE_BIAS_DETECTION=0` → temporal USM is **inactive**.  
- Slot02 behaves exactly as in Phase 14.4 (bias detection optional, no temporal state).  
- Slot07 and all other slots behave identically to pre-14.5.  

In other words: Phase 14.5 is **purely additive** and becomes active only on explicit operator request.

---

## 4. Rollback Levers

Phase 14.5 was engineered to be **fully reversible** at both runtime and code levels.

### 4.1 Runtime-Level Rollback

Disable temporal USM in Slot02:

```bash
export NOVA_ENABLE_USM_TEMPORAL=0
```

Effects:

- Slot02 stops updating `TemporalUsmState`.  
- `ProcessingResult.temporal_usm` remains `None`.  
- `temporal_usm@1` payloads are **never emitted**.  
- All behavior reverts to pure Phase 14.4 (structural + VOID semantics only).

No other flags (e.g., `NOVA_ENABLE_COGNITIVE_LOOP`) are touched by this change.

### 4.2 Code-Level Rollback

If a deeper rollback is required:

- Remove temporal math kernel + tests:  
  - `git revert <commit adding src/nova/math/usm_temporal.py and test_temporal_usm_math.py>`  
- Remove temporal_usm contract:  
  - `git revert <commit adding contracts/temporal_usm@1.yaml>`  
- Remove Slot02 integration + tests:  
  - `git revert <commit integrating temporal USM into DeltaThreshProcessor and adding test_temporal_usm_integration.py>`  
- Remove env documentation:  
  - `git revert <commit documenting NOVA_ENABLE_USM_TEMPORAL and NOVA_TEMPORAL_MODE in config/.env.example>`  

Each revert restores the previous behavior without affecting other phases or ontological components.

---

## 5. Current Invariants After Phase 14.5

After Phase 14.5, the following invariants hold:

1. **Temporal Ownership:**  
   - Slot02 is the **only** owner of temporal USM state (`TemporalUsmState`).  
   - No other slot maintains its own temporal USM state.

2. **Separation of Roles:**  
   - Slot02: computes instantaneous and temporal USM, emits contracts.  
   - Slot07, Slot09: designated consumers, but **runtime reads are not yet active**.  

3. **Reversibility:**  
   - Temporal USM is fully gated by `NOVA_ENABLE_USM_TEMPORAL`.  
   - Disabling the flag returns Nova to pure Phase 14.4 behavior.  
   - Code-level rollbacks are single-commit reverts.

4. **No Silent Drift:**  
   - Temporal USM does not change decisions anywhere in the system yet.  
   - No slot reads `temporal_usm@1` in runtime as of Phase 14.5 closeout.  

5. **Provenance & Observability:**  
   - All temporal behavior is expressed via explicit code, contracts, and env flags.  
   - Test suite includes temporal math and integration tests.  

6. **Test Baseline:**  
   - `python -m pytest -q` passes with all new temporal tests included.  

Phase 14.5 is therefore considered **installed and stabilized**, with time present in Nova’s architecture but not yet influencing governance.

---

## 6. Preconditions for Phase 14.6

Phase 14.6 (“Temporal Governance for Slot07”) will only begin after:

- This closeout document is accepted as the canonical description of Phase 14.5.  
- `docs/specs/phase14_6_activation_criteria.md` is adopted as the gate for enabling temporal governance.  
- Operators explicitly choose to move from the **pre-activation temporal regime** (time present but unused) into a regime where temporal signals may influence Slot07 behavior.

Until then, Nova remains in a **stable, time-aware but temporally inert governance state**.


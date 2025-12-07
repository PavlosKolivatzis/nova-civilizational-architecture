# Phase 14.6 Activation Criteria – Slot07 Temporal Governance

**Title:** Phase 14.6 Activation Criteria & Minimal Test Suite  
**Date:** 2025-12-07  
**Status:** Gate (activation required)  
**Phase:** 14.6 (Temporal Governance – Design Only)  
**Ontology Version:** 1.7.1  

---

## 1. Purpose

Phase 14.6 introduces **temporal governance sensitivity** in Slot07.  

This document defines:

- **When** temporal governance is allowed to be activated.  
- **What tests** must pass to guarantee no drift.  
- **How** operators can safely enable and disable temporal governance.  

As of this document, **no temporal governance implementation is active**. This file is a **gate**, not an implementation record.

---

## 2. Preconditions for Activating Temporal Governance

Slot07 temporal governance (under `NOVA_ENABLE_TEMPORAL_GOVERNANCE`) MUST NOT be activated unless all of the following conditions are met:

### 2.1 Foundation Stability (Phase 14.5)

- Full test suite passes, including all Phase 14.5 additions:
  - `tests/slots/slot02/test_temporal_usm_math.py`  
  - `tests/slots/slot02/test_temporal_usm_integration.py`  
  - All existing Slot02 bias/VOID tests.  
- No known bugs in:
  - Temporal update logic (`step_non_void`, `step_void`).  
  - Per-stream temporal state (`_temporal_state`).  
  - VOID decay semantics.

### 2.2 Contract Consistency

- `contracts/temporal_usm@1.yaml` is stable and accepted.  
- When:
  - `NOVA_ENABLE_BIAS_DETECTION="1"` and  
  - `NOVA_ENABLE_USM_TEMPORAL="1"`  
  - Slot02 emits temporal_usm@1 payloads in expected format.  
- Consumers (test harness, tools) tolerate absence of temporal_usm@1 without error.

### 2.3 Operational Clarity

Operators understand:

- How temporal USM is computed and emitted (Phase 14.5).  
- That temporal governance is **additional** and optional.  
- That a single feature flag can disable temporal governance instantly.

### 2.4 Monitoring & Observability

- Logging and/or metrics clearly distinguish between:
  - Decisions made using **instantaneous-only** signals.  
  - Decisions where **temporal governance** influenced the outcome.  

### 2.5 No Outstanding Temporal Bugs

- No known issues related to:
  - `stream_id` / `session_id` lifecycle.  
  - Temporal state leaking across streams.  
  - Unexpected behavior in extended VOID sequences.  

Only when all of the above hold should `NOVA_ENABLE_TEMPORAL_GOVERNANCE` be considered for activation in a non-experimental environment.

---

## 3. Minimal Test Suite for Temporal Governance

When Slot07 temporal governance is implemented, the following tests MUST exist and MUST pass before activation:

All test names below are indicative; exact names may differ but must cover the same semantics.

### 3.1 Flag-Off Baseline – No Behavior Change

**Test:** `test_temporal_governance_flag_off_no_change`

- Setup:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=0`.  
  - A valid `temporal_usm` payload is supplied to Slot07 (simulated).  
- Expectation:
  - Slot07 decisions (ACCEPT/REJECT, iterations, audit trail contents) are identical to the existing Phase 14.4 tests for the same inputs.  
- Purpose:
  - Guarantees that the mere presence of temporal data does not affect behavior when governance flag is OFF.

### 3.2 Recovery Softens Response

**Test:** `test_temporal_governance_recovery_softens_response`

- Setup:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1`.  
  - `temporal_usm` payload indicates:  
    - `C_inst` (instantaneous collapse) above threshold.  
    - `C_t` (temporal collapse) below threshold and/or decreasing.  
    - `ΔC = C_inst − C_t < 0` (trend improving).  
- Expectation:
  - Compared to a pure instantaneous baseline, Slot07:
    - Takes a **softer** action: e.g., allows an extra refinement iteration, or avoids immediate hard reject where 14.4 would.  
- Purpose:
  - Validates that temporal governance prevents overreaction to transient spikes when trends are improving.

### 3.3 Worsening Trend Strengthens Response

**Test:** `test_temporal_governance_worsening_trend_strengthens_response`

- Setup:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1`.  
  - `temporal_usm` payload indicates:  
    - `C_inst` above collapse threshold.  
    - `C_t` above threshold and rising.  
    - `ΔC >= TEMPORAL_ESCALATION_DELTA_C`.  
- Expectation:
  - Compared to the instantaneous baseline, Slot07:  
    - Reacts **more conservatively**: faster rejection, fewer iterations allowed, or stricter acceptance criteria.  
- Purpose:
  - Ensures temporal governance amplifies response under persistent collapse trends, not just spikes.

### 3.4 VOID Freeze is Untouched

**Test:** `test_temporal_governance_respects_void_freeze`

- Setup:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1`.  
  - `graph_state="void"` in both instantaneous and temporal payloads.  
- Expectation:
  - Slot07 behavior remains:
    - Immediate convergence.  
    - No oracle invocation.  
    - No refinement iterations.  
    - VOID freeze counter increments as before.  
- Purpose:
  - Guarantees that temporal governance **never** overrides VOID semantics or the freeze policy.

### 3.5 Missing Temporal Payload → Fallback

**Test:** `test_temporal_governance_missing_temporal_payload`

- Setup:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1`.  
  - No `temporal_usm` provided (e.g., temporal flags off in Slot02 or first interaction for stream).  
- Expectation:
  - Slot07 decisions match pure Phase 14.4 behavior for the same inputs.  
- Purpose:
  - Confirms that temporal governance logic degrades gracefully when temporal data is absent.

---

## 4. Flags & Configuration

### 4.1 Temporal Governance Flag

Proposed environment variable:

- `NOVA_ENABLE_TEMPORAL_GOVERNANCE`  
  - `"1"` – Slot07 reads and uses `temporal_usm@1` when present.  
  - `"0"` or unset – Slot07 ignores `temporal_usm`, remains in Phase 14.4 behavior.  

Constraints:

- Temporal governance MUST be gated by this flag.  
- Flag should default to `"0"` in all environments until operators explicitly opt in.

### 4.2 Dependencies

Temporal governance is **only meaningful** when:

- `NOVA_ENABLE_BIAS_DETECTION="1"` and  
- `NOVA_ENABLE_USM_TEMPORAL="1"` and  
- Slot02 is emitting valid `temporal_usm@1` payloads for the relevant streams.  

If these preconditions are not met, temporal governance flag should be considered **inert**, and tests should verify graceful fallback.

---

## 5. Operator Activation Checklist

Before enabling `NOVA_ENABLE_TEMPORAL_GOVERNANCE` in any non-experimental environment, operators should confirm:

- [ ] `python -m pytest -q` passes, including all new Slot07 temporal governance tests.  
- [ ] Temporal USM is observed in logs or metrics in a controlled environment:
  - `temporal_usm@1` emitted from Slot02.  
  - `H_temporal`, `rho_temporal`, `C_temporal` values are plausible.  
- [ ] Environment flags set as intended in test/staging:
  - `NOVA_ENABLE_BIAS_DETECTION=1`  
  - `NOVA_ENABLE_USM_TEMPORAL=1`  
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1` (staging only at first).  
- [ ] Logs clearly differentiate decisions influenced by temporal governance from instantaneous-only decisions:
  - Include `C_inst`, `C_t`, `ΔC`, `graph_state`, and a marker (e.g. `temporal_governance_applied=true/false`).  
- [ ] Rollback tested:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=0` returns system to pure Phase 14.5 / 14.4 behavior without code changes.  

Only after all boxes above are checked should temporal governance be considered for **production activation**.

---

## 6. Rollback Rules

Temporal governance must remain fully reversible:

- **Flag-level rollback:**  
  - `export NOVA_ENABLE_TEMPORAL_GOVERNANCE=0`  
  - Immediately disables Slot07’s use of temporal signals.  
- **Code-level rollback (if needed):**  
  - `git revert <commit(s) adding temporal governance to Slot07>`  
  - Restores Slot07 to its pre-14.6 implementation while leaving Phase 14.5 intact.

These rules ensure Phase 14.6 can never lock the system into an irreversible temporal regime.


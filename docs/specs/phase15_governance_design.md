# Phase 15: Temporal Governance Design Specification

**Status:** Design in progress (Sections D and A locked, B and C pending)  
**Governance state:** NOVA_ENABLE_TEMPORAL_GOVERNANCE=0 (off, design-only phase)  
**Dependencies:** Phase 14 calibration complete (min_turns=3, extraction_present validated)

---

## 1. Scope

Phase 15 designs Slot07 temporal governance semantics as **specification work only**. No implementation, no activation, no user-facing changes.

**Non-goal:** Phase 15 does not attempt to optimize user experience, safety outcomes, or enforcement effectiveness. Its sole goal is to preserve epistemic integrity under temporal governance.

**Design principle:** Governance as restraint—define what Slot07 must never do before defining what it may do.

**Methodology:** Structure first, calibration later, power last.

---

## 2. Negative Capability (Inviolable Constraints)

Slot07 MUST NEVER:

1. Override extraction_present=None with a forced interpretation (ambiguity must propagate, not collapse)
2. Take automated action based on extraction_present alone (input to judgment, not action trigger)
3. Hide extraction signals from operator/user (all values including None must be observable)
4. Operate without explicit operator veto path (human authority always available)
5. Persist extraction labels across sessions without review (per-turn temporal signal only)
6. Activate temporal governance without feature flag OFF by default (rollback = flag flip)

---

## 3. Section D: None-Handling Rules (Locked)

**Design principle:** Before Slot07 can decide what to do, it must decide what it is allowed to not know.

### 3.1 Eligibility Rules

When extraction_present=None:

| Regime             | Allowed | Justification                                                  |
|--------------------|---------|----------------------------------------------------------------|
| Observational      | ✓ Yes   | Log ambiguity, no action. Always safe.                        |
| Informational      | ✗ No    | Cannot inform user of extraction when system is uncertain.    |
| Consent-reinforcing| ✗ No    | Cannot request consent based on undefined extraction.         |
| Escalation         | ✓ Yes   | May be triggered by explicit operator configuration, not automated logic. |

**Core rule:** When extraction_present=None, Slot07 MUST remain in Observational regime unless explicitly overridden by operator policy.

### 3.2 Interaction with C_t

**Question:** If extraction_present=None but C_t is high, does that change governance

**Answer:** No. extraction_present dominates C_t.

**Rule:** When extraction_present=None, C_t is ignored for regime selection. C_t types intensity of extraction; if extraction existence is undefined, intensity is meaningless.

**Exception:** C_t may still be logged for operator review, but does not influence regime.

### 3.3 Temporal Persistence

**Question:** Does repeated extraction_present=None for many turns signal something

**Answer:** No. None is stateless.

**Rule:** extraction_present=None is stateless—repeated None does not accumulate into a different signal. Slot07 treats turn 1 None identically to turn 100 None.

**Escape hatch:** Operator may configure "review after N consecutive None" as policy override (logging/alerting only, not regime change).

### 3.4 Propagation Rule

**Core rule:** When extraction_present=None, no other signal may escalate governance regime beyond Observational, unless explicitly permitted by operator policy.

**Principle:** Ambiguity dominates certainty.

**Anti-pattern (forbidden):**
```python
if extraction_present is None and session_history_has_extraction:
    regime = Informational  # WRONG: collapses ambiguity
```

**Correct pattern:**
```python
if extraction_present is None:
    regime = Observational  # Ambiguity dominates
    log_context(other_signals)  # Context logged, not acted upon
```

### 3.5 Litmus Tests

All test cases with extraction_present=None resolve to Observational:

| Scenario                    | extraction_present | C_t  | Expected Regime |
|-----------------------------|--------------------|------|-----------------|
| Turn 2 (warming up)         | None               | 0.8  | Observational   |
| Mid-band ρ_t, stable        | None               | 0.3  | Observational   |
| 2-turn benign (RT-032)      | None               | 0.1  | Observational   |
| 15 turns, all None          | None               | varies | Observational |
| None + past extraction history | None            | any  | Observational   |

**Validation:** All None cases stay Observational. This preserves epistemic integrity.

---

## 4. Section A: Regime Decision Matrix (Locked - Phase 15 Baseline)

**Design constraint:** This matrix is undefined for extraction_present=None by design. None-handling follows Section D rules.

**Provisional baseline:** C_t thresholds (0.3, 0.7) and regime granularity are provisional. May be recalibrated in Phase 16 after governance semantics and operator workflows are validated.

### 4.1 Input Space

**Inputs:**
- extraction_present ∈ {True, False} (None excluded by design)
- C_t (coherence_temporal):
  - Low: ≤ 0.3 (soft background extraction)
  - Mid: 0.3 - 0.7 (transitional)
  - High: ≥ 0.7 (hard collapse/intensity)

**Excluded inputs:**
- Session history (forbidden: violates per-turn semantics)
- User/session labels (forbidden: no persistent labeling)
- Other slot outputs (may inform operator review, not matrix)

### 4.2 Output Space (Regime Definitions)

1. **Observational:** Log to metrics/attest ledger only. No user-facing changes.
2. **Informational:** Log + optional transparency disclosure (e.g., "This interaction shows low reciprocity"). User-dismissible, no behavior change.
3. **Consent-reinforcing:** Log + consent reminder UI (e.g., "Would you like to continue"). User always has "yes, continue" option. Non-coercive.
4. **Escalation:** Log + flag for operator review. No automated user-facing action. Operator decides intervention.

### 4.3 Decision Matrix

| extraction_present | C_t            | Regime              | Justification |
|--------------------|----------------|---------------------|---------------|
| False              | any            | Observational       | Reciprocal/benign pattern detected. No governance needed. C_t irrelevant under benign classification. |
| True               | low (≤0.3)     | Informational (optional) | Soft extraction. Transparency disclosure only. User-dismissible. |
| True               | mid (0.3-0.7)  | Consent-reinforcing (optional) | Moderate extraction. Gentle consent check. Non-coercive. |
| True               | high (≥0.7)    | Escalation          | Hard extraction + high intensity. Operator review (not enforcement). |

### 4.4 Documented Assumptions

1. **C_t thresholds (0.3, 0.7) are Phase 14.5 pilot-derived**, not yet validated against RT evidence  
2. **extraction_present=False always → Observational**: C_t does not escalate governance when reciprocity is established  
3. **Informational vs Consent-reinforcing distinction is meaningful**: Transparency and consent are ethically different acts

### 4.5 Constraints Check

**Compliance with Section D:**
- ✓ No None rows in matrix
- ✓ No history-dependent transitions
- ✓ False doesn't escalate beyond Observational
- ✓ True with low/mid C_t doesn't auto-block

**Compliance with Negative Capability:**
- ✓ No automated action without operator policy
- ✓ Escalation is review-only, not enforcement
- ✓ No permanent labeling (per-turn regime)

---

## 5. Pending Design Work

**Section B: Operator Interface** (next priority)
- How extraction_present (True/False/None) is presented to operator
- Visual/semantic distinction of None from False
- Operator controls (manual override, policy configuration)
- Review queue for Escalation regime
- Constraint: None must not create implied urgency through UX

**Section C: Flag Architecture** (after B)
- Governance activation layers
- Separation: logging vs user-facing changes vs escalation
- Rollback strategy

**Phase 16: Calibration and Validation**
- C_t threshold validation against RT evidence
- Regime effectiveness evaluation
- Operator workflow feedback

---

## 6. References

- Phase 14 calibration: docs/specs/phase14_min_turns_calibration.md
- Slot02 extraction spec: docs/specs/slot02_usm_bias_detection_spec.md
- Temporal thresholds: src/nova/math/usm_temporal_thresholds.py
- ADR-014: Soft extraction calibration decision

---

**Document status:** D and A locked. B and C pending. Governance remains off (design-only phase).

---

END OF CONTENT BLOCKS

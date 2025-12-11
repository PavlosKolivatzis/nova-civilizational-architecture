# ADR-014: Soft Extraction Calibration Around Sensitive Data

**Status:** Proposed  
**Date:** 2025-12-11  
**Phase:** 14.5–14.6  
**Related Specs:**  
- `docs/specs/phase14_5_temporal_usm_spec.md`  
- `docs/specs/phase14_5_observation_protocol.md`  
- `docs/specs/phase14_retrospective.md`  
- `docs/specs/phase14_6_temporal_governance.md`  
- `docs/specs/phase14_extraction_calibration.md`  
- `docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml`  
- `docs/compliance/audits/IMPLEMENTATION_AUDIT.md`

---

## 1. Context

Phase 14 introduced **temporal USM** (`H_t`, `ρ_t`, `C_t`) and provisional thresholds for classifying conversation states (warming_up, extractive, consensus, collaborative, neutral). Pilot work and the Phase 14 retrospective established that:

- **ρ_t is the primary extraction signal** (power‑flow asymmetry).
- **C_t is secondary**, distinguishing different low‑ρ_t regimes (e.g., consensus vs extraction).
- **H_t is diagnostic**, not a primary manipulation signal for conversational text.

In practice, we observe a class of **soft extraction scenarios** around sensitive data (personal, financial, cultural/identity) where:

- ρ_t ≈ 0 is sustained (one‑way pressure),
- C_t remains low‑positive and decays under smoothing,
- the current classifier often labels these states as `"neutral"` or “helpful/personalization”.

These patterns appear both in synthetic tests and in REALTALK‑style dialogues.

The ontology defines **ARC analytic instruments** (PAD.E.L and INF‑o‑INITY) that should, in the future, reason about psychological and informational manipulation, but the implementation audit confirms:

- PAD.E.L: **NOT IMPLEMENTED** (analytic instrument under ARC).
- INF‑o‑INITY: **PARTIAL** (distortion/meta‑lens components only).

There is no single calibration reference tying together:

- ρ_t / C_t behavior,
- soft extraction semantics,
- autonomy / consent considerations,
- and future ARC instrumentation.

---

## 2. Weakest Assumption

The **weakest assumption** underlying this ADR is:

> The six exemplars (S1–S3, R1–R3) described in `phase14_extraction_calibration.md` are representative of the soft extraction patterns Nova will encounter around sensitive data in early Phase 14 deployment.

If early operational data contradicts this, the calibration set must be revised.

---

## 3. Decision

We adopt a **soft extraction calibration set** and a two‑layer interpretation of temporal USM:

1. **ρ_t‑based Extraction Presence Flag (Conceptual)**

   - Introduce a conceptual flag `Extraction_present (desired)` that is **true** when:
     - ρ_t is sustained near 0.0 over multiple turns; and
     - the graph is non‑VOID.
   - This flag is **independent of C_t**: soft extraction can exist even when C_t never crosses the current “extractive” gate (`C_t >= 0.18`).

2. **C_t‑based Extraction Typing (Conceptual)**

   - Use C_t to distinguish **soft/background** vs **hard/collapse** extraction *after* `Extraction_present` is true:
     - Soft/background: C_t in a low‑positive band (≈ 0.0–0.2).
     - Hard/collapse: C_t closer to or above extractive bands (≈ ≥0.18 temporal) and persistent.

This decision is encoded in the calibration spec `phase14_extraction_calibration.md`, which:

- defines six exemplars with extraction geometry (Source, Mechanism, Beneficiary, Narrative Shield),
- annotates manipulation tactics (pressure, false authority, emotional leverage, value exploitation),
- specifies target autonomy/deliberation/consent assessments,
- and documents ideal ρ_t / C_t bands alongside current vs desired Nova behavior.

This ADR is **calibration‑only**. It does **not** mandate immediate changes to `classify_temporal_state` or Slot02/Slot07 runtime logic.

---

## 4. Consequences

### 4.1 Positive

- **Clarified semantics:**
  - ρ_t is formally recognized as the gate for “extraction exists”.
  - C_t is recognized as a typing/intensity dimension, not the sole gate.

- **Bridge to ARC instruments:**
  - PAD.E.L and INF‑o‑INITY have concrete calibration examples for psychological and informational risk once implemented.

- **Operator guidance:**
  - Operators gain a small, explicit “gold set” for reviewing temporal USM traces and interpreting soft extraction around sensitive data.

### 4.2 Risks / Open Questions

- **Representativeness:**
  - The exemplars may not match real usage patterns seen in early deployment.

- **Over‑fitting:**
  - There is a risk of mentally over‑tuning to these examples before seeing broader real‑world diversity.

- **Implementation drift:**
  - If future code changes are made to “match the table” without re‑checking ontology and real data, Nova may drift away from its theoretical foundations.

---

## 5. Implementation Plan (Future Phases)

This ADR does not change code. It sets the stage for future work:

1. **Observation & Validation (Phase 14.6+)**
   - Use the calibration set to interpret real temporal USM traces from:
     - REALTALK corpus (arXiv:2502.13270),
     - internal AI–human logs (where available and ethically permissible).
   - Check how often:
     - ρ_t indicates `Extraction_present = True` in soft cases;
     - the current classifier outputs `"neutral"` or similar.

2. **Design Refinements**
   - Based on observed data, decide whether to:
     - introduce an explicit `extraction_present` flag in the temporal classification layer,
     - add soft extraction tags/metrics to logs,
     - or adjust thresholds / warm‑up logic.

3. **ARC Integration**
   - When PAD.E.L / INF‑o‑INITY implementations are attempted, use these exemplars as early tests:
     - PAD.E.L: test `reflex_integrity`, `emotional_coherence`, and future autonomy metrics.
     - INF‑o‑INITY: test `distortion_index` and distortion tags against these patterns.

---

## 6. Rollback

If later evidence shows that:

- the calibration exemplars are not representative of real soft extraction patterns; or
- using ρ_t as an `Extraction_present` gate creates unacceptable false positives,

we can:

- mark `phase14_extraction_calibration.md` as DEPRECATED and supersede it with a new calibration spec grounded in updated data; and
- revert any future code changes that attempted to implement `Extraction_present` solely on the basis of this ADR, defaulting back to the Phase 14.5 provisional thresholds and state labels.

---


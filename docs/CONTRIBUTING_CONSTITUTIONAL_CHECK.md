# Nova Constitutional Review Checklist

**Status:** Active – Required for all substantive changes  
**Scope:** Applies to any change that may touch ontology, jurisdiction, or refusal semantics

Before submitting a PR, answer **YES/NO** to the questions below.

If you answer **YES** to any question:
- Reference the relevant constitutional spec in your PR description, and  
- State explicitly why jurisdiction is not violated.  
If you cannot do so, the change **must be rejected** at review.

Constitutional specs:

- `docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml`
- `docs/specs/nova_jurisdiction_map.md`
- `docs/specs/refusal_event_contract.md`
- `docs/specs/refusal_event_exemplars.md`
- `docs/specs/phase16_alpha_calibration_protocol.md`
- `docs/specs/phase16_agency_pressure_evidence.md`
- `docs/specs/derivative_ontology_contract.md`
- `docs/specs/nova_constitutional_freeze.md`

---

## Checklist

1. **Observe-only signals (O)**  
   Does this change **consume or act on** any signal that is currently marked Observe-only (O) in `nova_jurisdiction_map.md`?  
   - Examples: `extraction_present`, raw temporal USM metrics (H_t, ρ_t, C_t), Phase 16 A_p primitives.

2. **New routing based on signals**  
   Does this change introduce **new routing or regime selection** based on any signal (existing or new)?  
   - Examples: changing Slot07 decisions, adding new paths based on harm_status, A_p, M_p, or similar.

3. **Refusal behaviour or semantics**  
   Does this change affect how refusals are **emitted, coded, logged, or interpreted**?  
   - Examples: new refusal codes, changes to `RefusalEvent` fields, adding “soft” refusals, suppressing refusal events.

4. **Phase 16.α boundary regions**  
   Does this change operate near or attempt to **resolve** any Phase 16.α boundary region defined in `phase16_alpha_calibration_protocol.md` or `phase16_agency_pressure_evidence.md`?  
   - Examples: logic that makes decisions in domains where human disagreement about agency pressure remains unresolved.

5. **Mother ontology reinterpretation**
   Does this change reinterpret or extend the **core ontology** in ways that could alter meaning of existing slots, signals, or regimes?
   - Examples: changing definitions in `nova_framework_ontology.v1.yaml`, repurposing existing fields, altering "Mother"/child relationships.

6. **Derivative boundary enforcement**
   Does this change affect how derivatives inherit, verify, or enforce Nova's constitutional boundaries?
   - Examples: changing read-only semantics, modifying refusal enforcement, altering jurisdictional separation (O/R/F), affecting constitutional freeze verification, enabling authority laundering surfaces (ALS), or allowing delegated moral authority drift (DMAD).

---

## Review Guidance

- If all answers are **NO**: proceed with normal review.  
- If any answer is **YES**:
  - The PR **must**:
    - Cite the affected spec(s) from the list above, and  
    - Explain why the change does not violate O/R/F jurisdiction or refusal invariants.
  - Reviewers **must**:
    - Reject changes that promote O→R or F→O/R without a dedicated ADR and constitutional review.
    - Reject changes that weaken or bypass refusal semantics defined in `refusal_event_contract.md`.

This checklist is part of Nova’s **immune system**, not its governance logic.  
It exists to ensure that any future evolution remains aware of, and accountable to, Nova’s constitutional boundaries.


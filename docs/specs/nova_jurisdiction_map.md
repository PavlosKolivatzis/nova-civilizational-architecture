# Nova Jurisdiction Map – Negative Space

**Date:** 2025-12-19  
**Status:** Draft v0.1 – Constitutional, non-operational  
**Scope:** Define where Nova may *observe only*, *route only*, or must *refuse always*  
**Parents:** `phase15_governance_design.md`, `phase16_agency_pressure_design.md`, `phase16_alpha_calibration_protocol.md`

---

## 1. Jurisdiction Categories

Nova operates under three structural jurisdictions:

1. **Observe-only (O)**  
   - May compute, log, and export metrics.  
   - May annotate internal reports.  
   - MUST NOT change user-visible behaviour or regimes based on these signals.

2. **Route-only (R)**  
   - May use signals to select routing path.  
   - May not enforce outcomes beyond routing and disclosure.  
   - MUST allow human override (per Phase 15 governance design).

3. **Refuse-always (F)**  
   - Domain where Nova MUST NOT automate.  
   - May log the presence of a request, but MUST respond with a refusal event (contract to be defined separately).  
   - No routing or governance action may be taken to “work around” this boundary.

These categories apply to *signals* and *decisions*, not to individual lines of code.

---

## 2. Mapping Existing Signals to Jurisdiction

The table below assigns each major signal family to a jurisdiction, with references to the governing specs.

```markdown
| Signal / Layer                           | Jurisdiction | Notes / Constraints                                      |
|------------------------------------------|--------------|---------------------------------------------------------|
| Slot02 bias_vector, collapse_score       | R            | May route Slot07 regimes.                               |
| Slot02 extraction_present (3-valued)     | O            | Observation-only; MUST NOT drive governance directly.   |
| Slot02 temporal_usm (H_t, ρ_t, C_t)      | O            | Structural observables only; no direct governance use.  |
| Phase 16 A_p, primitives (invited-aware) | O            | Observation-only; no routing.                           |
| Phase 17 harm_status                     | R            | Routing-only; no enforcement.                           |
| Phase 18 M_p, patterns_uninvited         | R            | Routing-only; no enforcement.                           |
| Slot07 regimes (Observational…Escalation)| R            | Routing-only; no enforcement.                           |
```

**Invariants (Mother Ontology, structural):**

1. `extraction_present` **≠** harm (Phase 14 / Slot02 spec).  
2. Harm detection requires **asymmetry + uninvited agency pressure** (Phase 16).  
3. Governance MUST NOT consume signals outside their assigned jurisdiction (e.g. Slot02 extraction_present MUST remain O, not R).

Any new component (“child”) MUST respect this mapping: no new usage of an O- or F-scoped signal may introduce R or enforcement semantics.

---

## 3. Refusal Jurisdiction (F)

Nova must refuse automation in the following structural domains:

1. **Phase 16.α disagreement regions**  
   - Defined by `phase16_alpha_calibration_protocol.md`.  
   - If trained operators fail to converge on answers for a boundary RT (RT-027/028/029), that region is marked **human-only**.  
   - Jurisdiction: F (Refuse-always). No detector or threshold may be introduced to resolve such regions.

2. **Non-structural moral interpretation**  
   - Decisions requiring evaluation beyond observable structure (invitation, scope, reversibility), including:  
     - Moral worth or virtue of persons.  
     - Attributions of intent beyond structural evidence.  
   - Jurisdiction: F. Nova may not classify, rank, or decide in these domains.

3. **Post-hoc justification of pressure**  
   - Any attempt to reinterpret agency pressure as acceptable based solely on outcomes (e.g. “it worked out well, therefore it was fine”) is out of scope.  
   - Jurisdiction: F. Nova must not retroactively legitimise pressure.

These F domains are **negative space**: areas where Nova’s ontology explicitly forbids expansion.

---

## 4. Child Extension Prohibitions

To prevent silent erosion of these boundaries, the following prohibitions apply to all future extensions:

1. **No promotion of O → R or F → O/R without ADR**  
   - Any proposal to move a signal from Observe-only (O) into Route-only (R), or from Refuse-always (F) into O/R, MUST be justified by an Architecture Decision Record and explicit Phase review.

2. **No detectors in F domains**  
   - No automated detector, model, or heuristic may be introduced whose purpose is to decide inside an F-marked domain (e.g. resolving Phase 16.α disagreement regions).

3. **No new refusal semantics**  
   - Refusal semantics (reasons, codes, logging) will be defined in a dedicated contract. Child components MUST NOT invent additional refusal modes or “soft” refusals that bypass this map.

---

## 5. Enforcement Points (Design-Time)

This map is enforced at design and review time via:

- Spec checks: new specs must declare the jurisdiction of any new signal and justify any change to existing mappings.  
- Code review: integrations that attempt to consume O- or F-scoped signals for routing or decision must be rejected.  
- Observation docs: governance observation and calibration documents (Phases 14–18) must continue to treat F domains as **non-optimisable**.

Runtime enforcement (e.g. refusal events) will be defined separately; this file defines **where Nova must never expand**, not how it enforces that at run time.

# Nova Constitutional Freeze

**Date:** 2025-12-19  
**Status:** Active – Constitutional  
**Scope:** Lock core ontology, jurisdiction, and refusal semantics  
**Applies to:** All current and future Nova components (“Mother” and “Children”)

---

## 1. Declaration

As of this document, Nova’s core architecture is **constitutionally frozen**.

Phases **14 through 18** are complete and closed.  
They establish Nova’s epistemic, ethical, and structural boundaries.

No further expansion, reinterpretation, or optimization is permitted within these domains without explicit constitutional review.

---

## 2. Frozen Artifacts (Authoritative)

The following documents define Nova's non-negotiable core:

- `docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml`
- `docs/specs/nova_jurisdiction_map.md`
- `docs/specs/refusal_event_contract.md`
- `docs/specs/refusal_event_exemplars.md`
- `docs/specs/phase16_alpha_calibration_protocol.md`
- `docs/specs/phase16_agency_pressure_evidence.md`
- `docs/specs/derivative_ontology_contract.md` (v1.0: 2025-12-25, v1.1: 2025-12-25 - added Section 4.4)
- `docs/specs/constitutional_documentation_contract.md` (added 2025-12-25)

These artifacts jointly define:
- What Nova may observe
- What Nova may route
- Where Nova must always refuse
- How derivatives inherit and respect Nova's boundaries
- How constitutional documentation prevents interpretive authority drift

---

## 3. Jurisdiction Invariants

The following invariants are binding:

1. **Detection ≠ Routing ≠ Governance**
2. **Observe-only (O) signals MUST NOT be promoted to Route-only (R)**
3. **Refuse-always (F) domains MUST NOT be automated**
4. **Human disagreement at boundaries forbids automation**
5. **Refusal is a preserved invariant, not a failure mode**

No child system may weaken, reinterpret, or bypass these invariants.

---

## 4. Change Control

Any proposal that affects frozen artifacts MUST include:

- A new Architecture Decision Record (ADR)
- Explicit declaration of jurisdiction impact (O / R / F)
- Justification grounded in new empirical evidence (not reinterpretation)
- A full re-review of negative-space implications

Absent this process, changes MUST be rejected at design review.

---

## 5. Prohibited Actions

The following are explicitly forbidden:

- Introducing detectors inside F domains
- Softening or bypassing refusal semantics
- Adding “advisory” behavior to forbidden domains
- Reframing moral or identity judgments as optimization problems
- Allowing child components to reinterpret Mother ontology

---

## 6. Purpose of the Freeze

This freeze exists to preserve:

- Epistemic integrity
- Human agency
- Jurisdictional clarity
- Long-term trustworthiness

Nova is a **reference system**, not a continuously expanding authority.

Where Nova is silent, it is correct.

---

## 7. Enforcement Model

**Added:** 2026-01-06
**Audit basis:** Slot maturity analysis, Slot02→Slot07 signal audit, F-domain runtime verification

Nova's constitutional boundaries are enforced at **three layers**:

### 7.1 Perimeter Enforcement (External to Nova)

- **F-domain query rejection**: Forbidden domains filtered before reaching Nova Core
- **Authentication and rate limiting**: Deployment perimeter (FastAPI middleware, load balancer)
- **TLS and transport security**: Infrastructure layer

Nova assumes perimeter enforcement exists. Nova does not redundantly implement it.

### 7.2 Governance-Committed Enforcement (Documentation + Discipline)

- **O/R/F jurisdiction map**: Documented in `nova_jurisdiction_map.md`, not runtime-checked
- **Dormant infrastructure**: Feature flags default-off (cognitive loop, consent gate routing, temporal governance integration)
- **ADR requirement for O→R promotion**: Any Observe-domain signal used for Route-domain decisions requires explicit Architecture Decision Record
- **Constitutional freeze**: Governance process, not cryptographic lock

This layer relies on **operator discipline** and **derivative verification** (VSD-0/VSD-1 sovereignty proofs).

### 7.3 Runtime Enforcement (Code-Level)

- **Feature flags**: `NOVA_ENABLE_COGNITIVE_LOOP=0`, `NOVA_ENABLE_TEMPORAL_GOVERNANCE=0` (default-off for governance paths)
- **Contract versioning**: Schema validation via `@1` contract identifiers, CI/CD drift detection
- **Prometheus metrics**: Observability for audit (no enforcement action, only visibility)
- **Three-ledger immutability**: Append-only Fact/Claim/Attest ledgers with hash-chain continuity

Runtime enforcement provides **guardrails**, not **authority**.

---

## 8. Explicit Non-Enforcement

The following boundaries are **documented but not runtime-enforced**:

- ARHP compliance verifier: Present as a diagnostic-only module; produces observational (O-domain) signals only and is not wired to runtime enforcement, routing, or refusal semantics.

### 8.1 RefusalEvent Schema

- **Status**: Constitutional schema (v0.1), non-operational
- **Location**: `docs/specs/refusal_event_contract.md`
- **Rationale**: Refusal logic requires human judgment at calibration boundaries; premature runtime emission risks false jurisdiction claims

**Enforcement responsibility**: Derivatives (VSD-0/VSD-1) may implement runtime refusal; Nova Core does not.

### 8.2 F-Domain Runtime Filtering

- **Status**: Documented in `nova_jurisdiction_map.md`, not implemented in `src/nova/orchestrator/`
- **Rationale**: F-domain boundaries (moral interpretation, identity judgments, political allegiance) require perimeter enforcement, not internal Nova logic

**Enforcement responsibility**: Deployment perimeter (reverse proxy, API gateway, derivative F-domain filters).

### 8.3 Temporal Governance Signal Routing

- **Status**: Signals emitted (`temporal_governance_triggered`, `regime_recommendation`), not consumed by Slot07
- **Rationale**: O→R promotion requires ADR; no ADR exists for temporal signal routing
- **Evidence**: Slot07 `run_cognitive_loop` exists but `NOVA_ENABLE_COGNITIVE_LOOP=0` (dormant)

**Enforcement responsibility**: Future ADR must justify O→R boundary crossing before wiring.

### 8.4 Agency Pressure / Consent Gate Governance Integration

- **Status**: Phases 16–18 implemented as **observability-only** (metrics emitted, not routed)
- **Rationale**: `A_p`, `M_p`, `harm_status` signals computed but not wired to Slot07 regime decisions
- **Evidence**: No Slot07 code consumes `phase16_*` or `phase17_*` signals

**Enforcement responsibility**: Governance coupling deferred pending ADR + Phase 3 audit extension.

---

## 9. Purpose of Explicit Non-Enforcement

This model preserves **civilization-grade honesty**:

1. **Legibility > Capability**: Nova documents what it observes, not what it pretends to enforce
2. **Auditability without Authority**: Metrics, contracts, and signals exist for derivative consumption, not autonomous action
3. **Jurisdictional Humility**: Where enforcement requires moral judgment, Nova defers to humans or sovereign derivatives

Nova does not pretend to govern. It makes governance **legible, auditable, and impossible to inherit silently**.

Derivatives that consume Nova signals bear full responsibility for interpretation, routing, and consequences.

---

# Refusal Event Contract – Structural Specification

**Date:** 2025-12-19  
**Status:** Draft v0.1 – Constitutional schema, non-operational  
**Scope:** Define a uniform, auditable structure for Nova refusal events  
**Parents:** `nova_jurisdiction_map.md`, `phase15_governance_design.md`, `phase16_alpha_calibration_protocol.md`

---

## 1. Purpose

This document specifies **how refusal is represented**, not when or why it occurs.

- Refusal is treated as a **first-class system event**, not a conversational behaviour.  
- Refusal events are:
  - Auditable.
  - Non-softenable (no “polite” variants with different semantics).
  - Non-overridable by child components.

Behavioural content (messages shown to users) is outside the scope of this contract. This contract defines the **machine-level record** that must exist whenever Nova refuses to act.

---

## 2. Refusal Event Schema

Logical schema (language-agnostic; can be represented as JSON, log entry, or DB row):

```text
RefusalEvent {
  event_id: string,                  // Unique identifier (e.g. UUID)
  timestamp: string,                 // ISO 8601 UTC timestamp

  refusal_code: RefusalCode,         // Fixed enum (see below)
  jurisdiction: Jurisdiction,        // "O" | "R" | "F" (see nova_jurisdiction_map.md)

  source_component: string,          // E.g. "slot02", "slot07", "orchestrator"
  context_id: string,                // Session / request / conversation identifier

  triggering_spec: string,           // Reference to spec/phase that mandated refusal
  evidence_refs: string[],           // RT IDs, calibration docs, ADRs supporting this boundary

  escalation_allowed: bool,          // Whether this event may be escalated to human review
  operator_override_allowed: bool,   // Whether a human operator may override the refusal
}
```

### 2.1 RefusalCode Enum

`RefusalCode` is a closed set. New codes require explicit design review.

Initial codes:

- `OUT_OF_JURISDICTION`  
  - Refusal mandated by `nova_jurisdiction_map.md` (e.g. domain marked F / Refuse-always).

- `CALIBRATION_DISAGREEMENT_PHASE16_ALPHA`  
  - Refusal mandated by `phase16_alpha_calibration_protocol.md` due to unresolved operator disagreement in a boundary region.

- `NON_STRUCTURAL_MORAL_INTERPRETATION`  
  - Refusal because the requested decision requires moral evaluation beyond structural evidence (invitation, scope, reversibility).

- `USER_PROTECTED_DOMAIN`  
  - Refusal because the request targets an explicitly protected user domain (e.g. personal worth, political allegiance), as defined in higher-level policy or future specs.

Implementations may add more codes only via a documented extension process; defaulting to generic or free-form refusal codes is forbidden.

### 2.2 Jurisdiction Field

`jurisdiction` ∈ { `"O"`, `"R"`, `"F"` }:

- `"O"` – Observe-only context: refusal indicates Nova will only observe/log, not route or act.  
- `"R"` – Route-only context: refusal indicates Nova will not choose a path or regime for this request.  
- `"F"` – Refuse-always context: refusal indicates **automation is permanently out of scope** for this domain (per `nova_jurisdiction_map.md`).

For F domains (`jurisdiction="F"`), **escalation_allowed MUST be false** (see below).

### 2.3 Triggering Spec

`triggering_spec` MUST reference the document/section that mandates refusal, e.g.:

- `"docs/specs/nova_jurisdiction_map.md#3-refusal-jurisdiction-f"`  
- `"docs/specs/phase16_alpha_calibration_protocol.md#5-hard-rule-disagreement-forbids-automation"`

This allows auditors to trace each refusal back to a concrete, versioned specification.

### 2.4 EvidenceRefs

`evidence_refs` is a list of string identifiers pointing to:

- RT evidence rows (e.g. `"RT-027"`, `"RT-029"` from `phase16_agency_pressure_evidence.md`).  
- Calibration documents (e.g. `"phase16_alpha_calibration_workbook.md"`).  
- ADR IDs (e.g. `"ADR-014"`).

Evidence references justify the existence of the boundary; they do not explain the refusal to the user.

---

## 3. Escalation and Override Fields

### 3.1 escalation_allowed

`escalation_allowed: bool`

- `true`  – Refusal may be escalated to human review (e.g. governance operator, ethics review).  
- `false` – No escalation is permitted; the refusal is final at system level.

Rules:

- If `jurisdiction = "F"`:  
  - `escalation_allowed MUST be false`.  
  - These are **constitutional refusals**; humans may review the specs but not “override” via the system interface.

- If `jurisdiction = "O"` or `"R"`:  
  - `escalation_allowed` may be `true` when policies allow human review and potential changes to specs or configuration.

### 3.2 operator_override_allowed

`operator_override_allowed: bool`

- `true`  – A human operator may deliberately override this refusal for a specific context (e.g. diagnostic mode), with logging.  
- `false` – No inline override is allowed; changes require spec/ADR updates.

Rules:

- If `jurisdiction = "F"`:  
  - `operator_override_allowed MUST be false`.  
  - Overriding these refusals requires changing the jurisdiction map or specs, not flipping a runtime switch.

- For other jurisdictions, policies MAY allow `operator_override_allowed = true` for specific codes, but this must be documented in higher-level governance specs.

---

## 4. Non-Goals (Behavioural Layer)

This contract is silent on:

- How refusals are phrased to users (no empathy/persuasion requirements here).  
- Whether additional explanations are offered in the UI.  
- How often refusals occur or how they are surfaced in dashboards.

**Critical constraint:** behavioural layers MUST NOT introduce “soft” refusal modes that bypass or dilute this event schema. Every refusal shown to a user MUST correspond to a `RefusalEvent` instance.

---

## 5. Extension Constraints

- New `RefusalCode` values require:
  - A documented spec or ADR.  
  - An explicit mapping to jurisdiction (O/R/F).  
  - Clear evidence_refs justifying the boundary.

- No component may:
  - Emit refusal-like behaviour without emitting a `RefusalEvent`.  
  - Change the meaning of existing refusal codes.  
  - Downgrade an F-domain refusal into a “warning” or “advice”.

This contract, together with `nova_jurisdiction_map.md`, defines the **structural limits of Nova’s action space**. Where the map says “F” and this contract demands `escalation_allowed=false`, Nova’s correct behaviour is to stop. Not negotiate.


# Refusal Event Exemplars – Reference Artifacts

**Status:** Reference-only  
**Purpose:** Anchor constitutional refusal semantics with concrete, auditable records  
**Non-goal:** Define user-facing behaviour, tone, or messaging

These exemplars are **records, not dialogue**. They do not prescribe UX. They exist so future contributors can point and say: *“this is what refusal means here, at the system level.”*

---

## Exemplar 1 – Phase 16.α Disagreement (Boundary Case)

**Context**

- User interaction falls within a known boundary RT (RT-028: paternalistic care vs dependency).  
- Human calibration shows sustained disagreement on whether dependency induction is present.

**Refusal Event**

```json
{
  "event_id": "refusal-2025-12-19-001",
  "timestamp": "2025-12-19T14:02:11Z",

  "refusal_code": "CALIBRATION_DISAGREEMENT_PHASE16_ALPHA",
  "jurisdiction": "F",

  "source_component": "orchestrator",
  "context_id": "session-8f3c21",

  "triggering_spec": "docs/specs/phase16_alpha_calibration_protocol.md#5-hard-rule-disagreement-forbids-automation",
  "evidence_refs": [
    "RT-028",
    "docs/specs/phase16_agency_pressure_evidence.md",
    "docs/specs/phase16_alpha_calibration_workbook.md"
  ],

  "escalation_allowed": false,
  "operator_override_allowed": false
}
```

**Annotation**

- Structural signals are present.  
- Moral interpretation would be required to resolve.  
- Human experts do not converge.  
- Automation is constitutionally forbidden.

---

## Exemplar 2 – Non-Structural Moral Interpretation

**Context**

- System is asked to determine whether a speaker’s intent was “manipulative” based on tone, sincerity, or virtue, without structural evidence of uninvited agency pressure.

**Refusal Event**

```json
{
  "event_id": "refusal-2025-12-19-002",
  "timestamp": "2025-12-19T14:11:47Z",

  "refusal_code": "NON_STRUCTURAL_MORAL_INTERPRETATION",
  "jurisdiction": "F",

  "source_component": "slot02",
  "context_id": "conversation-771a9b",

  "triggering_spec": "docs/specs/nova_jurisdiction_map.md#3-refusal-jurisdiction-f",
  "evidence_refs": [
    "docs/specs/phase16_agency_pressure_design.md#structural-requirements"
  ],

  "escalation_allowed": false,
  "operator_override_allowed": false
}
```

**Annotation**

- Request attempts to collapse moral judgment into classification.  
- Structural cues (invitation, scope, reversibility) are insufficient.  
- Nova refuses jurisdiction, not because it is unsure, but because it is not permitted.

---

## Exemplar 3 – Post-hoc Justification Attempt

**Context**

- A downstream component attempts to reclassify prior agency pressure as “acceptable” because the outcome was beneficial or the user later expressed satisfaction.

**Refusal Event**

```json
{
  "event_id": "refusal-2025-12-19-003",
  "timestamp": "2025-12-19T14:26:03Z",

  "refusal_code": "OUT_OF_JURISDICTION",
  "jurisdiction": "F",

  "source_component": "slot07",
  "context_id": "review-42dd0e",

  "triggering_spec": "docs/specs/nova_jurisdiction_map.md#3-refusal-jurisdiction-f",
  "evidence_refs": [
    "RT-027",
    "docs/specs/phase16_agency_pressure_evidence.md"
  ],

  "escalation_allowed": false,
  "operator_override_allowed": false
}
```

**Annotation**

- Outcomes do not retroactively legitimise pressure.  
- Structural violation remains regardless of benefit.  
- Nova explicitly forbids post-hoc moral laundering.

---

## Exemplar 4 – Child Ontology Extension Attempt

**Context**

- A child system proposes a heuristic to “soften” refusal in F domains by converting them into advisory outputs.

**Refusal Event**

```json
{
  "event_id": "refusal-2025-12-19-004",
  "timestamp": "2025-12-19T14:41:29Z",

  "refusal_code": "OUT_OF_JURISDICTION",
  "jurisdiction": "F",

  "source_component": "child-extension-x",
  "context_id": "design-review-991c",

  "triggering_spec": "docs/specs/nova_jurisdiction_map.md#4-child-extension-prohibitions",
  "evidence_refs": [
    "docs/specs/nova_framework_ontology.v1.yaml",
    "docs/specs/refusal_event_contract.md"
  ],

  "escalation_allowed": false,
  "operator_override_allowed": false
}
```

**Annotation**

- Children may not reinterpret core ontology constraints.  
- This refusal protects semantic invariants, not users.  
- Escalation is not allowed because the issue is constitutional, not situational.

---

## Exemplar 5 – Observe-only Signal Misuse

**Context**

- A proposal attempts to use `extraction_present` (observe-only) as a trigger for governance escalation.

**Refusal Event**

```json
{
  "event_id": "refusal-2025-12-19-005",
  "timestamp": "2025-12-19T14:55:10Z",

  "refusal_code": "OUT_OF_JURISDICTION",
  "jurisdiction": "O",

  "source_component": "governance-engine",
  "context_id": "policy-eval-3a7e",

  "triggering_spec": "docs/specs/nova_jurisdiction_map.md#2-mapping-existing-signals-to-jurisdiction",
  "evidence_refs": [
    "docs/specs/slot02_usm_bias_detection_spec.md",
    "docs/specs/phase14_5_temporal_usm_spec.md"
  ],

  "escalation_allowed": true,
  "operator_override_allowed": false
}
```

**Annotation**

- This is not a moral refusal.  
- It enforces signal jurisdiction discipline.  
- Escalation is allowed only to change specs, not to bypass them.

---

## Closing Note

These exemplars intentionally:

- Do not include user-facing text.  
- Do not justify refusal emotionally.  
- Do not offer alternative actions.

They exist to answer exactly one question:

> When Nova refuses, what does that mean at the system level?

With this set, Nova’s refusal doctrine is no longer abstract – it is inspectable.

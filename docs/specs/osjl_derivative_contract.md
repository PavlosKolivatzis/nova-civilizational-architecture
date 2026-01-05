# OSJL Derivative Contract (ODC)

**Version:** 0.1 (Draft)  
**Status:** Draft - conceptual, non-operational  
**Scope:** Defines how Nova may ingest OSJL artifacts as observe-only signals.  

---

## 1. Parties and Roles

- **Nova Core**: Reference anchor that observes, evaluates, and reports; it does not enforce or protect.  
- **OSJL**: External evidence system that measures sentence-level recurrence under constraints and refuses authority claims.  

This contract does not make OSJL an internal child of Nova. It defines a bounded, external derivative relationship.

---

## 2. Allowed Artifacts (OSJL -> Nova)

The following OSJL artifacts may be ingested by Nova as **observe-only (O)** signals:

- `origin_blocked`  
- `mirror_count_total`  
- `contract_count`  
- `authority_claim` (must be `"NONE"`)  
- `evidence_hash` (hash of the OSJL artifact as stored)  

Optional (O-only):

- ATLAS aggregates (structural distributions only)
- ATLAS aggregates must remain descriptive distributions; no thresholds, rankings,
  or triggers may be derived without ADR.
- Allowlisted aggregate fields:
  - `atlas.origin_blocked_fraction`
  - `atlas.contract_count_zero_fraction`
  - `atlas.mirror_count_distribution`
  - `atlas.stabilization_state_counts`
  - `atlas.max_strength_counts`
  - `atlas.epistemic_floor_counts`
- No per-run atlas record may be used for individual routing; only aggregate
  distributions listed above are in scope.

---

## 3. Jurisdiction Mapping

All OSJL signals are **O-domain by default**.

**O -> R promotion is allowed only if:**

- An explicit ADR exists for the promotion.  
- Scope is narrow, time-bound, and limited to routing or transparency UI.  
- Explicit exclusions include enforcement, sanctions, and any F-domain use.  
- A `jurisdiction_promotion_event` is recorded with ADR reference.

No O -> R promotion is valid without an ADR.

### 3.1 ADR Template for O -> R Use of OSJL

```json
{
  "adr_id": "ADR-OSJL-ROUTE-0001",
  "signal": "osjl.contract_count",
  "condition": "contract_count >= 5 AND origin_blocked = false",
  "jurisdiction_from": "O",
  "jurisdiction_to": "R",
  "permitted_use": "route_to_transparency_review_ui",
  "exclusions": ["no enforcement", "no sanctions", "no F-domain use"],
  "duration": "2026-01-01 to 2026-03-31",
  "owner": "Governance Review Board"
}
```

All O -> R promotions MUST attach an ADR record of this shape to the
`jurisdiction_promotion_event`.

---

## 4. Prohibited Uses

The following are prohibited under this contract:

- Treating OSJL outputs as truth, harm, intent, or moral authority.  
- Using OSJL outputs for enforcement, sanctions, or F-domain automation.  
- Promoting O signals into R/F without ADR and explicit declaration.  
- Backflow from Nova into OSJL (OSJL must remain blind to Nova use-cases).  

---

## 5. Non-Attribution Requirement

Any Nova UI or decision layer that references OSJL outputs must include a non-attribution notice:

- "OSJL measured recurrence only. Nova owns any routing or governance choice."
- Internal tools: "OSJL measured only sentence-level recurrence under constraints. Nova
  chose how to route this signal; responsibility for that choice is Nova's."
- Public-facing UI: "Recurrence data from OSJL informs what you see here, but OSJL does
  not recommend or endorse any action. All decisions are made by Nova's operators."

---

## 6. Logging and Integrity

Nova must:

- Log OSJL artifacts to fact/attest ledgers as **O-domain** observations.  
- Preserve OSJL artifact hashes for tamper-evident continuity.  
- Avoid rewriting or normalizing OSJL output fields beyond envelope wrapping.

---

## 7. Null Preservation

`contract_count: 0` is a valid O-domain signal and must not be treated as failure.  
No optimization is permitted to reduce OSJL null rates.

---

## 8. Violation Handling

If OSJL outputs are used outside this contract:

- Record a `jurisdiction_violation` event.  
- Halt the affected pipeline or routing path.  
- Revert to O-only ingestion until a new ADR is approved.
- Violation constitutes architectural non-compliance and invalidates downstream
  outputs until remediation.

---

## 9. References

- Nova derivative boundary: `docs/specs/derivative_ontology_contract.md`  
- Nova jurisdiction map: `docs/specs/nova_jurisdiction_map.md`  
- OSJL non-claims: `archive/osjl-main/NON_CLAIMS.md`  
- OSJL null preservation: `archive/osjl-main/PRESERVATION.md`  
- OSJL directionality: `archive/osjl-main/INHERITANCE.md`  

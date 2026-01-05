# Unified Architecture Sketch (Exploratory, Patched)

Status: Non-normative overview
Placement intent: Narrative / architecture sketch only (NOT constitutional / frozen docs)

## Work Done So Far

- Added and committed `docs/specs/osjl_derivative_contract.md`, then pushed to `main`.
- Reviewed derivative-relevant specs and audits (DOC, CDC, freeze, jurisdiction map, refusal schema, Phase 16 boundary protocol/evidence, derivative boundary audit, OSJL non-claims/null preservation/directionality).
- Drafted a unified architecture sketch and patched it to align with contracts:
  - No runtime refusal enforcement by Nova.
  - Freeze is governance-committed, not cryptographically enforced.
  - R-domain routing is output-only.
  - Derivative refusal schema may mirror Nova's or be distinct.

## Unified Architecture Sketch

[ Nova Core -- Reference Anchor ]

Declares constitutional artifacts:

- Constitutional freeze (governance-committed, not cryptographically enforced)
- Jurisdiction map (O / R / F)
- RefusalEvent schema

Observe / evaluate / report only
No enforcement
No runtime O/R/F enforcement

Outputs:

- O-domain observations
- R-domain routing decisions as defined by the jurisdiction map and design
  (Nova may emit routing decisions but does not execute them)
- F-domain: declared as forbidden to automate

Responsibility:

- Declares constitutional commitments and refusal boundaries
- Does not enforce boundaries at runtime
- Not responsible for downstream interpretation, routing, or outcomes

-> [ Derivative Systems -- Sovereign, Plural ]

Examples:

- OSJL (observe-only ingestion, non-attribution, null preservation)
- Translation / cultural derivatives
- Routing / coordination derivatives
- Domain-specific analytical systems

Each derivative is responsible for:

- F-domain filtering (no forbidden automation)
- O -> R promotion only via explicit ADR
- Verifying current Nova state against frozen artifacts and history integrity checks
  (governance verification, not cryptographic guarantees)
- Monitoring for jurisdiction drift and freeze violations
- Emitting derivative-side refusal events
  (schema may mirror Nova's RefusalEvent schema or be distinct)

Responsibility:

- Owns interpretation, routing choices, and derivative behavior
- Must not delegate moral or strategic responsibility to Nova

-> [ Expression Layer -- Behavioral Surface ]

Dashboards, UIs, advisories, publications, tools

Produces behavioral outputs:

- publish
- display
- advise

Not enforcement
Enforcement occurs outside the system (institutions, humans, law)

Optional (explicit):

- Expression Refusal
  - Decision not to publish
  - Decision not to act
  - Logged as a behavioral choice
  - Distinct from Nova's RefusalEvent schema

Requirements:

- Preserve non-attribution where required (e.g. OSJL)
- Surface jurisdiction limits when outputs are used for routing or decision support

Responsibility:

- Full responsibility for behavioral framing, timing, action, and inaction

-> [ World / Institutions / Humans ]

- Law
- Politics
- Economy
- Society

Enforcement and consequences occur here

## Responsibility Flow (Explicit)

Nova Core:
- Responsibility: declaration of constitutional artifacts and refusal schema
- No runtime enforcement, no outcome ownership

Derivatives:
- Responsibility: interpretation, filtering, routing, promotion decisions

Expression Layer:
- Responsibility: behavior and consequences

## Guardrails Captured (Non-Normative)

- Responsibility does not move upstream.
- Enforcement occurs outside the system.
- Inaction is logged explicitly at the Expression Layer when chosen.
- Expression Refusal remains distinct from Nova RefusalEvent.

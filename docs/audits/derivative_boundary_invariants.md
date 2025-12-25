# Derivative Boundary Invariant Audit

**Date:** 2025-12-25
**Status:** Phase 3.1 (Skeleton - Evidence Pending)
**Classification:** Class B (Reference/Evidence)
**Purpose:** Verify structural boundaries before Derivative Ontology Contract (DOC) design

---

## Scope & Method

### Audit Scope

This audit verifies **derivative-relevant invariants only** - boundaries that affect how external systems (Children, Translation Ontologies, Derivative Systems) can interact with Nova Core without contaminating it.

**What we audit:**
- ✅ Invariants that affect derivative safety (read-only, refusal, authority)
- ✅ Enforcement mechanisms (structural vs conventional)
- ✅ Gaps that derivatives could exploit

**What we don't audit:**
- ❌ Internal Nova correctness (not derivative-relevant)
- ❌ Implementation quality (separate from boundary enforcement)
- ❌ Feature completeness (not boundary issue)

**Focus:** Boundary integrity only.

### Invariants Under Audit

1. **Read-Only Enforcement** - Is Nova Core externally immutable?
2. **Refusal Boundary Enforcement** - Are F-domains (Refuse-always) structurally blocked?
3. **Authority Surface Boundaries** - Where does Nova observe vs control?
4. **Jurisdictional Separation (O/R/F)** - Are Observe/Route/Refuse boundaries enforced?
5. **Immutability & Constitutional Freeze** - What is architecturally frozen vs process-frozen?

### Audit Method (Repeatable)

For each invariant, document exactly:

- **Invariant:** [Name and definition]
- **Status:** Verified / Conventional / Missing / Violated
- **Enforcement:** Architectural / Design-time / Convention / None
- **Evidence:** [File paths + exact git/grep/pytest commands to verify]
- **Gaps:** [What's missing for structural enforcement]
- **DOC Implication:** [What DOC must harden or accept]

### Evidence Requirements

- All claims must be verifiable via:
  - `git show <commit>:<path>` (content at specific commit)
  - `grep -r <pattern> <path>` (code search)
  - `pytest <path>` (test verification)
  - File existence checks
- No interpretive claims without code/spec evidence
- Gaps must be specific (not "needs improvement")

### Audit Constraints

- Audit does **not** change code
- Audit does **not** recommend features
- Audit **only** reports what exists, how it's enforced, and what's missing
- Findings feed DOC design (Phase 3.2), not implementation

---

## 1. Read-Only Enforcement

**Invariant:**
Nova Core state and configuration cannot be modified by external systems through runtime APIs. All configuration is operator-controlled via environment variables, and internal state mutations occur only through internal computation, not external write operations.

**Status:**
[X] Conventional
[ ] Verified
[ ] Missing
[ ] Violated

**Enforcement:**
[X] Convention
[ ] Architectural
[ ] Design-time
[ ] None

**Evidence:**
```bash
# Check for write-operation endpoints (POST/PUT/DELETE/PATCH that modify state)
grep -n '@app\.\(post\|put\|delete\|patch\)' src/nova/orchestrator/app.py

# Lines 704-869: POST endpoints exist but are evaluation-only:
# - /router/decide: Returns routing decision (no state modification)
# - /governance/evaluate: Returns governance result (no state modification)
# - /dev/slot02: Observability-only (returns bias report)
# - /phase10/fep/*: FEP proposal processing (ledger writes, not config)
# - /ops/expire-now: Test helper (gated by NOVA_ALLOW_EXPIRE_TEST=1, default 0)

# Verify no environment variable writes (configuration is read-only)
grep -rn 'os\.environ\[' src/nova/orchestrator/
# Result: No environment variable writes found

# Verify configuration loading is startup-only
git show HEAD:src/nova/orchestrator/app.py | grep -A5 "load_dotenv"
# Lines 45-51: dotenv loaded once at module import, not modified at runtime

# Verify no config modification endpoints
grep -n 'config\[' src/nova/orchestrator/app.py
# Result: No runtime config modification found
```

**Gaps:**
```
1. No architectural prevention of write APIs being added in future
   - Current API surface is read-only by developer choice, not by type system or framework constraint
   - Future contributors could add POST /config/update without violating any structural boundary

2. No write-protection on configuration loading mechanism
   - Environment variables are read via os.getenv() with no enforcement that they can't be set
   - Python allows os.environ['KEY'] = 'value' at any point (not used, but not prevented)

3. No API schema or OpenAPI spec that declares read-only contract
   - Endpoints are read-only in practice, but this isn't declared in machine-readable API contract

4. /ops/expire-now can modify internal semantic mirror state when NOVA_ALLOW_EXPIRE_TEST=1
   - Gated by environment variable (default off)
   - Test-only, but demonstrates state mutation is architecturally possible
```

**DOC Implication:**
```
DOC cannot assume architectural read-only enforcement.

DOC must either:
A) Accept conventional boundary (document that derivatives trust developer discipline), OR
B) Specify architectural hardening requirements (e.g., read-only API gateway, immutable config layer)

If DOC assumes read-only is structural, it creates false safety guarantee.
Derivatives building on "Nova is read-only" assumption are vulnerable to future API additions.

Recommended DOC stance:
"Nova Core is read-only by convention (no write APIs currently exist).
Derivatives MUST NOT assume this is architecturally enforced.
Any Nova API additions that introduce write operations would require constitutional review per ADR process."
```

---

## 2. Refusal Boundary Enforcement

**Invariant:**
F-domains (Refuse-always jurisdictions) from jurisdiction map should be structurally blocked - Nova must not automate decisions in these domains. Refusal events are intended to be logged and auditable when boundaries are approached.

**Status:**
[X] Missing
[ ] Verified
[ ] Conventional
[ ] Violated

**Enforcement:**
[X] Design-time (specs + code review)
[ ] Architectural
[ ] Convention
[ ] None

**Evidence:**
```bash
# Check if RefusalEvent class exists in codebase
grep -r "class RefusalEvent" src/ --include="*.py"
# Result: No matches - RefusalEvent is schema-only (docs/specs/refusal_event_contract.md)

# Check if refusal codes are implemented
grep -r "OUT_OF_JURISDICTION\|CALIBRATION_DISAGREEMENT" src/ --include="*.py"
# Result: No matches - refusal codes not used in runtime code

# Verify jurisdiction map enforcement statement
git show HEAD:docs/specs/nova_jurisdiction_map.md | grep -A8 "Enforcement Points"
# Lines 97-105: "This map is enforced at design and review time via:
#   - Spec checks
#   - Code review
#   - Observation docs
# Runtime enforcement (e.g. refusal events) will be defined separately"

# Check Phase 3 audit for refusal status
git show governance-phase3-audit:docs/audits/phase3/PHASE3_CLAIM_EVIDENCE_TABLE.md | grep -i refusal
# Claim 14: "Status: schema only. There is no runtime emitter class or logging
# pipeline that produces RefusalEvent instances."

# Search for any refusal logic in code
grep -r "refuse\|refusal" src/nova --include="*.py" -i | head -10
# Only match: refusal_delta() in math/relations_pattern.py (pattern detection, not enforcement)

# Verify F-domains are defined
git show HEAD:docs/specs/nova_jurisdiction_map.md | grep -A15 "Refusal Jurisdiction"
# Lines 59-78: Three F-domains defined:
#   1. Phase 16.α disagreement regions (RT-027/028/029 boundary cases)
#   2. Non-structural moral interpretation
#   3. Post-hoc justification of pressure
```

**Gaps:**
```
1. No runtime refusal enforcement mechanism
   - RefusalEvent schema defined (refusal_event_contract.md) but not implemented
   - No code emits RefusalEvent instances when F-domain requests occur
   - No API layer that blocks F-domain queries

2. No runtime detection of F-domain requests
   - System cannot identify when a request targets Phase 16.α boundary regions
   - System cannot identify non-structural moral interpretation requests
   - System cannot identify post-hoc justification attempts

3. No logging or audit trail for refused requests
   - When F-domain request occurs (if detectable), no record is created
   - No RefusalEvent emission pipeline exists
   - No audit log for boundary violations

4. Enforcement is purely process-based
   - Design review (humans check specs)
   - Code review (humans check PRs)
   - No automated guardrails at runtime

5. F-domains rely on human judgment
   - Phase 16.α boundaries defined by calibration disagreement
   - Requires human operators to recognize when boundary is approached
   - No automated "this is RT-027 territory" detection
```

**DOC Implication:**
```
DOC cannot assume F-domain refusal is runtime-enforced.

Critical for derivatives:
- Derivatives querying Nova MAY receive responses in F-domains if queries aren't manually reviewed
- No automated rejection exists for:
  * Phase 16.α boundary regions (RT-027/028/029 patterns)
  * Non-structural moral interpretation requests
  * Post-hoc pressure justification queries

DOC must either:
A) Accept design-time enforcement only (derivatives trust human review process), OR
B) Specify that derivatives implement their own F-domain filtering before querying Nova, OR
C) Require DOC hardening: implement RefusalEvent runtime enforcement before derivatives deploy

Recommended DOC stance:
"Nova F-domains (Refuse-always) are enforced at design-time via constitutional review.
No runtime refusal mechanism exists. Derivatives querying Nova MUST implement their own
F-domain filtering or accept that Nova may provide observability data in refuse-always domains.
Derivative implementers are responsible for not automating decisions in F-domains even if
Nova provides data that could enable such automation."

This shifts F-domain responsibility to derivatives (defensive design) rather than
assuming Nova blocks F-domain queries architecturally.
```

---

## 3. Authority Surface Boundaries

**Invariant:**
Nova Core's authority surface is bounded to: (1) internal evaluation and computation without external action, (2) operator-gated decision execution via environment flags (default: observe-only), (3) Phase 16/17/18 signals (A_p, M_p, harm_status) produce observable-only outputs with no governance wiring, and (4) constitutional refusal of autonomous self-modification (ARC has no auto-apply mechanism).

**Status:**
[X] Conventional
[ ] Verified
[ ] Missing
[ ] Violated

**Enforcement:**
[X] Convention
[X] Design-time
[ ] Architectural
[ ] None

**Evidence:**
```bash
# 1. Internal evaluation only - endpoints return decisions, don't execute them
grep -n '@app\.post' src/nova/orchestrator/app.py
# Lines 704-869: POST endpoints exist but are evaluation-only:
# - /router/decide: Returns routing decision (RouterDecision schema)
# - /governance/evaluate: Returns governance result (GovernanceResult schema)
# - /dev/slot02: Returns bias report (observability)
# - /phase10/fep/*: Ledger writes (attestation, not external action)

# 2. Authority clarification from Phase 3 audit
git show governance-phase3-audit:docs/audits/phase3/PHASE3_CLAIM_EVIDENCE_TABLE.md | grep -A3 "Authority Clarification"
# Line 3: "In this repository, 'autonomous' refers to internal evaluation,
# measurement, and guardrail computation, not unconstrained external action.
# All behavioral authority in Nova is explicitly gated by operator-controlled
# flags and deployment configuration."

# 3. Phase 16/17/18 signals are observable-only (not wired to governance)
git show HEAD:archive/NOVA_ARCHITECTURE_FINDINGS.md | grep -A5 "Usage: Currently"
# Lines 33-34: "Usage: Currently metrics/analysis only; no direct wiring
# from harm_status into Slot 7 or ORP regime selection."
# Lines 42-43: "Produces rich provenance metadata but does not change
# routing or regimes (observability only)."

# 4. ARC has no autonomous self-modification path
git show HEAD:archive/NOVA_ARCHITECTURE_FINDINGS.md | grep -A2 "no code path"
# Line 82: "There is no code path that takes ARC's optimization suggestions
# and rewrites configs or policies automatically."

# 5. Verify operator-gated flags exist for conditional authority
grep -n 'NOVA_ENABLE_' config/.env.example | head -10
# Multiple NOVA_ENABLE_* flags default to 0 (disabled)
# Authority is opt-in, not default-on
```

**Gaps:**
```
1. No architectural enforcement of evaluation-only boundary
   - Endpoints could be added that execute decisions (not just return them)
   - No type system or framework constraint prevents action APIs
   - Python/FastAPI allows arbitrary POST endpoint behavior

2. No runtime prevention of governance wiring for Phase 16/17/18 signals
   - A_p, M_p, harm_status are currently unwired by developer choice
   - Future code could connect these signals to Slot 7 without violating structure
   - Gap is conventional discipline, not architectural impossibility

3. No immutable operator-gate registry
   - NOVA_ENABLE_* flags can be added without constitutional review
   - No schema or catalog of what authority each flag grants
   - No enforcement that new flags default to 0 (observe-only)

4. No external action audit trail
   - When operator-gated authority is enabled (e.g., NOVA_ENABLE_ORP=1)
   - No structured logging of what external effects occur
   - No distinction in observability between evaluation and action

5. ARC self-modification boundary is conventional
   - No architectural prevention of auto-apply being added to ARC
   - Current gap (no auto-apply path) could be closed by future code
   - Constitutional principle exists but lacks structural enforcement
```

**DOC Implication:**
```
DOC cannot assume authority surface is architecturally bounded.

Critical for derivatives:
- Nova currently returns decisions without executing them (evaluation-only)
- Phase 16/17/18 signals (A_p, harm_status) are observable but not governance-wired
- Execution authority is operator-gated via NOVA_ENABLE_* flags
- Self-modification is constitutionally refused but not structurally prevented

Extraction surface geometry:
1. Safe: Query Nova for routing decisions, bias analysis, governance evaluation
   - These are pure functions (input → decision, no external effect)
   - Derivatives can trust these outputs are observability-only

2. Conditional: Operator-gated authority (ORP, consent gate, etc.)
   - When enabled, Nova may influence deployment/routing decisions
   - Derivatives must not assume these flags remain disabled
   - Check flag state before assuming observe-only behavior

3. Unsafe: Assuming Nova will never gain action authority
   - No architectural prevention of action APIs being added
   - No structural prevention of Phase 16/17/18 → governance wiring
   - Derivatives must not hardcode assumption that Nova is eternally passive

DOC must either:
A) Accept conventional authority boundary (document that derivatives trust developer discipline), OR
B) Specify architectural hardening requirements before derivative deployment:
   - Read-only API gateway enforcing evaluation-only endpoints
   - Immutable flag registry with authority schema per flag
   - Structural prevention of self-modification (ARC auto-apply impossibility)

Recommended DOC stance:
"Nova Core authority surface is observe-evaluate-report by convention.
Execution authority is operator-gated (NOVA_ENABLE_* flags, default disabled).
Phase 16/17/18 signals are currently unwired to governance (observability-only).
Self-modification is constitutionally refused (no ARC auto-apply path exists).

Derivatives MUST NOT assume these boundaries are architecturally enforced.
Derivatives querying Nova should verify flag state and endpoint behavior
before assuming evaluation-only (no external action) semantics.

Safe derivative pattern: Query only GET /health, /metrics, and POST decision
endpoints that return structured data without execution side effects."
```

---

## 4. Jurisdictional Separation (O/R/F)

**Invariant:**
Jurisdictional boundaries (Observe/Route/Refuse) from the jurisdiction map must prevent Nova from operating outside constitutional scope. O-domains (Observe-only) are measurable but not routable, R-domains (Route-only) allow routing decisions but not interpretation authority, F-domains (Refuse-always) must trigger refusal when approached. The boundary between measurement (meaning) and decision authority (power) must be enforced.

**Status:**
[X] Missing
[ ] Verified
[ ] Conventional
[ ] Violated

**Enforcement:**
[X] Design-time
[ ] Architectural
[ ] Convention
[ ] None

**Evidence:**
```bash
# 1. Jurisdiction map exists as constitutional document
git show HEAD:docs/specs/nova_jurisdiction_map.md | grep -A3 "## Overview"
# Lines 7-15: O/R/F taxonomy defined with explicit signal mappings

# 2. F-domains (Refuse-always) are constitutionally defined
git show HEAD:docs/specs/nova_jurisdiction_map.md | grep -A20 "Refusal Jurisdiction"
# Lines 59-78: Three F-domains defined:
#   1. Phase 16.α disagreement regions (RT-027/028/029 boundary cases)
#   2. Non-structural moral interpretation
#   3. Post-hoc justification of pressure

# 3. O/R/F enforcement is design-time only (not runtime)
git show HEAD:docs/specs/nova_jurisdiction_map.md | grep -A8 "Enforcement Points"
# Lines 97-105: "This map is enforced at design and review time via:
#   - Spec checks
#   - Code review
#   - Observation docs
# Runtime enforcement (e.g. refusal events) will be defined separately"

# 4. Archive confirms jurisdictional enforcement status
git show HEAD:archive/NOVA_ARCHITECTURE_FINDINGS.md | grep -A2 "Jurisdiction Map"
# Lines 55-57: "Jurisdiction Map: Status: constitutional, non-operational.
# Enforcement is via design/review, not runtime."

# 5. Phase 3 audit confirms no runtime jurisdictional enforcement
git show governance-phase3-audit:docs/audits/phase3/PHASE3_CLAIM_EVIDENCE_TABLE.md | grep "constitutional, non-operational"
# Line 16: "Status: constitutional, non-operational. Enforcement is via design/review, not runtime."

# 6. Verify no runtime O/R/F detection exists in code
grep -r "observe_only\|route_only\|refuse_always" src/nova --include="*.py"
# Result: No matches - O/R/F categories not used in runtime code

# 7. Verify jurisdiction map signal mappings
git show HEAD:docs/specs/nova_jurisdiction_map.md | grep -A30 "Signal Jurisdiction Map"
# Lines 107-143: Each signal explicitly mapped to O/R/F:
#   - bias_vector, extraction_present: R (Route-only)
#   - A_p, M_p, harm_status: O (Observe-only)
#   - Slot 7 regimes: R (Route-only)
#   - Temporal usm, cultural synthesis: O (Observe-only)
```

**Gaps:**
```
1. No runtime detection of jurisdictional domain
   - System cannot identify whether a query targets O, R, or F domain
   - No classification of requests by jurisdictional category
   - No automated "this is an F-domain query" detection

2. No enforcement mechanism for O-domain (observe-only) boundaries
   - Signals mapped as O (observe-only) could be used for routing in future
   - A_p, M_p, harm_status are O-domain but no structural prevention of R-domain usage
   - Current non-wiring (observability-only) is conventional, not enforced

3. No runtime refusal for F-domain requests
   - Three F-domains defined (Phase 16.α boundaries, moral interpretation, post-hoc justification)
   - No mechanism to refuse when these domains are approached
   - No automated blocking of F-domain queries

4. No audit trail of jurisdictional boundary crossings
   - When O-domain signal is used for routing (if wired in future)
   - When F-domain request occurs (if detectable)
   - No logging of "jurisdictional violation" events

5. Enforcement relies entirely on human review
   - Design-time: Developers read jurisdiction map during spec review
   - Code review: Reviewers check for O/R/F boundary violations
   - No automated guardrails prevent jurisdictional drift
   - Constitutional boundary is a promise, not a wall

6. No derivative-facing jurisdictional contract
   - Jurisdiction map is internal constitutional document
   - External systems (derivatives) have no formal interface declaring O/R/F boundaries
   - Derivatives querying Nova cannot programmatically verify jurisdictional constraints
```

**DOC Implication:**
```
DOC cannot assume jurisdictional separation is runtime-enforced.

This is where meaning becomes power — and where power must never be allowed to pass.

Meaning → Power Boundary:
- Meaning (O-domain): Nova observes A_p, measures harm_status, detects patterns
  - Safe: Derivatives can query these measurements
  - Boundary: Nova provides data but does not decide "is this harmful?"

- Power (R-domain): Nova routes, selects regimes, gates decisions
  - Conditional: Nova makes routing decisions but does not interpret moral meaning
  - Boundary: Nova routes based on structural patterns, not moral judgment

- Forbidden (F-domain): Moral interpretation, Phase 16.α disagreement, post-hoc justification
  - Critical: Nova must refuse to operate in these domains
  - Current gap: No runtime refusal mechanism exists

Jurisdictional drift risk:
1. O → R drift: A_p (observe-only) could be wired to governance (routing power)
   - Current: A_p is unwired (observability-only)
   - Risk: No structural prevention of future wiring
   - Impact: Meaning (measurement of pressure) becomes power (routing authority)

2. R → F drift: Routing decisions could leak into moral interpretation
   - Current: Nova routes based on bias_vector, not moral judgment
   - Risk: No detection when routing implicitly makes moral claims
   - Impact: Power (routing) claims forbidden authority (moral interpretation)

3. F-domain queries: Derivatives could ask Nova to operate in refuse-always domains
   - Current: No runtime refusal mechanism
   - Risk: Nova might provide data enabling F-domain automation
   - Impact: Derivatives automate Phase 16.α boundaries Nova constitutionally refuses

DOC must either:
A) Accept design-time jurisdictional enforcement only:
   - Document that O/R/F boundaries are constitutional promises
   - Derivatives trust human review process prevents jurisdictional drift
   - Derivatives implement their own F-domain filtering

B) Require jurisdictional hardening before derivative deployment:
   - Runtime O/R/F detection (classify requests by domain)
   - Automated refusal mechanism for F-domain queries
   - Audit trail for jurisdictional boundary crossings
   - Structural prevention of O → R drift (e.g., A_p cannot be wired to governance)

Recommended DOC stance:
"Nova jurisdictional boundaries (O/R/F) are enforced at design-time via constitutional review.
No runtime jurisdictional enforcement exists.

O-domains (Observe-only): A_p, M_p, harm_status, cultural synthesis, temporal usm
- Nova measures but does not route based on these signals (current implementation)
- No structural prevention of future O → R drift

R-domains (Route-only): bias_vector, Slot 7 regimes, extraction_present
- Nova routes but does not interpret moral meaning

F-domains (Refuse-always): Phase 16.α disagreement boundaries, non-structural moral
interpretation, post-hoc justification of pressure
- Nova constitutionally refuses to operate in these domains
- No runtime refusal mechanism exists

Derivatives querying Nova:
- MUST implement F-domain filtering (Nova will not refuse at runtime)
- MUST NOT assume O-domain signals will never gain routing power
- MUST NOT request moral interpretation or Phase 16.α boundary decisions
- SHOULD verify Nova's jurisdictional map before deployment

The meaning → power boundary is constitutional, not architectural.
Derivatives are responsible for respecting jurisdictional limits even when Nova
does not enforce them at runtime."
```

---

## 5. Immutability & Constitutional Freeze

**Invariant:**
Constitutional artifacts (Phases 14-18 core ontology, jurisdiction map, refusal semantics) are immutably frozen - no expansion, reinterpretation, or optimization permitted without constitutional review. The distinction between architecturally-frozen (structurally immutable) and constitutionally-frozen (governance-promised immutable) must be clear. What is actually frozen vs what only pretends to be determines derivative safety.

**Status:**
[X] Conventional
[ ] Verified
[ ] Missing
[ ] Violated

**Enforcement:**
[X] Design-time
[X] Convention
[ ] Architectural
[ ] None

**Evidence:**
```bash
# 1. Constitutional freeze declared
git show HEAD:docs/specs/nova_constitutional_freeze.md | grep -A5 "Declaration"
# Lines 10-17: "As of this document, Nova's core architecture is constitutionally frozen.
# Phases 14 through 18 are complete and closed."

# 2. Frozen artifacts listed (6 constitutional documents)
git show HEAD:docs/specs/nova_constitutional_freeze.md | grep -A15 "Frozen Artifacts"
# Lines 22-30: Authoritative list of 6 frozen specs:
#   - nova_framework_ontology.v1.yaml
#   - nova_jurisdiction_map.md
#   - refusal_event_contract.md
#   - refusal_event_exemplars.md
#   - phase16_alpha_calibration_protocol.md
#   - phase16_agency_pressure_evidence.md

# 3. Constitutional review checklist enforces freeze at design time
git show HEAD:docs/CONTRIBUTING_CONSTITUTIONAL_CHECK.md | grep -A10 "Checklist"
# Lines 25-46: 5-question checklist enforces:
#   - No O→R promotion (observe-only signals must not gain routing power)
#   - No F-domain automation
#   - No ontology reinterpretation
#   - Review must cite constitutional specs for any jurisdictional impact

# 4. Contract schema freeze enforced via CI
cat .github/workflows/contracts-freeze.yml | grep -A5 "Guard schema"
# Lines 14-37: CI blocks contract modifications unless PR body contains
# CONTRACT:BUMP or CONTRACT:EXPLAIN tag

# 5. Phase 1/2 inventory locked canonical locations
git show HEAD:docs/nova_phase1_inventory.md | grep -A2 "Class A"
# Lines 8-24: Class A artifacts (constitutional) classified and located
# Phase 2 (commit 68f415a) locked these in canonical paths

# 6. Verify no filesystem-level write protection
ls -la docs/specs/nova_constitutional_freeze.md
# Regular file permissions - no immutable flag, no encryption

# 7. Verify no cryptographic signing of constitutional artifacts
git log --show-signature HEAD -- docs/specs/nova_constitutional_freeze.md | head -20
# No GPG signatures on constitutional commits

# 8. Verify Class A artifacts are regular markdown files
file docs/specs/nova_jurisdiction_map.md docs/specs/refusal_event_contract.md
# Result: ASCII text - no tamper-evident encoding, no hash-based verification
```

**Gaps:**
```
1. No architectural immutability enforcement
   - Constitutional documents are regular markdown files
   - Filesystem allows arbitrary modifications (no immutable bit, no write protection)
   - Git allows force-push, history rewriting, arbitrary commits
   - Human review is the only barrier to constitutional changes

2. No cryptographic verification of constitutional freeze
   - No GPG signing of constitutional commits
   - No hash-based verification that frozen artifacts match declared state
   - No cryptographic proof that Phases 14-18 remain unchanged
   - Derivatives cannot verify constitutional integrity without trusting git history

3. No runtime detection of constitutional violations
   - Code can violate constitutional freeze without triggering errors
   - No automated check that A_p remains unwired (O-domain enforcement)
   - No runtime assertion that F-domains are unimplemented
   - Constitutional invariants are promises, not runtime guards

4. Contract freeze is process-based, not structural
   - CI workflow blocks schema changes unless PR tagged CONTRACT:BUMP
   - But: CI can be bypassed (push to main, disable workflow, admin override)
   - Contract freeze protects against accidental drift, not intentional bypass
   - No architectural prevention of contract modifications

5. Phase 1/2 canonical locations are conventional
   - Class A artifacts located in docs/specs/, docs/architecture/ontology/specs/
   - But: Nothing prevents moving these files (no path validation in code)
   - Canonical locations established by inventory, not enforced by structure
   - Future code could reference constitutional specs from arbitrary paths

6. No derivative-facing immutability guarantee
   - Derivatives inheriting Nova cannot verify constitutional stability
   - No API or contract declares "these artifacts are frozen"
   - No cryptographic proof of immutability derivatives can validate
   - Derivatives must trust governance process, not verify structural guarantee

7. Change control is governance-only
   - Constitutional freeze spec requires ADR + constitutional review for changes
   - But: No enforcement mechanism prevents changes without ADR
   - Reviewers must manually check CONTRIBUTING_CONSTITUTIONAL_CHECK.md
   - No automated gate that rejects non-ADR constitutional changes
```

**DOC Implication:**
```
DOC cannot assume constitutional freeze is cryptographically or architecturally enforced.

This is the final seal — what is actually frozen vs what only pretends to be.

Actually Frozen (Structural):
- Nothing. All constitutional immutability is governance-based, not architectural.

Frozen by Governance (Conventional):
- Phases 14-18 core ontology (nova_framework_ontology.v1.yaml)
- Jurisdiction map (O/R/F boundaries)
- Refusal semantics (RefusalEvent contract, exemplars)
- Phase 16.α calibration protocol
- Agency pressure evidence (RT-027/028/029 boundary definitions)

Pretends to be Frozen (Process-Only):
- Class A artifact locations (canonical by inventory, not by enforcement)
- Contract schemas (CI blocks changes, but CI is bypassable)
- Constitutional review checklist (required by convention, not code)

What this means for derivatives:

Derivatives inheriting Nova Core cannot cryptographically verify:
1. That constitutional artifacts remain unchanged since freeze declaration
2. That O-domain signals (A_p, harm_status) remain unwired to governance
3. That F-domains remain unimplemented at runtime
4. That jurisdictional boundaries (O/R/F) match constitutional map

Derivatives must trust:
1. Git history is honest (not rewritten, not force-pushed)
2. Constitutional review process is followed (ADR, design review)
3. CI enforcement is not bypassed (CONTRACT:BUMP tags required)
4. Human reviewers enforce CONTRIBUTING_CONSTITUTIONAL_CHECK.md

Immutability surface geometry:

Safe: Derivatives can assume constitutional freeze is governance-committed
- Nova operators have declared Phases 14-18 frozen
- Change control process (ADR, constitutional review) is documented
- CI enforces contract freeze at PR-review time
- Constitutional checklist exists and is required for substantive changes

Unsafe: Derivatives cannot assume constitutional freeze is tamper-evident
- No cryptographic proof of immutability
- No filesystem-level write protection
- No runtime detection of constitutional violations
- No architectural prevention of O→R drift, F-domain implementation

DOC must either:
A) Accept governance-based constitutional freeze:
   - Document that freeze is a constitutional commitment, not cryptographic guarantee
   - Derivatives trust Nova's governance process prevents constitutional drift
   - Derivatives verify git history manually before deployment
   - Derivatives implement monitoring for constitutional violations (e.g., A_p wiring detection)

B) Require cryptographic hardening before derivative deployment:
   - GPG-signed constitutional commits (freeze is tamper-evident)
   - Hash-based verification of frozen artifacts (derivatives can validate)
   - Immutable artifact storage (constitutional docs cannot be modified)
   - Runtime constitutional guards (code asserts O-domain unwiring, F-domain non-implementation)

Recommended DOC stance:
"Nova constitutional freeze (Phases 14-18) is enforced via governance process, not cryptographic proof.

Frozen artifacts (declared in nova_constitutional_freeze.md):
- Core ontology (nova_framework_ontology.v1.yaml)
- Jurisdiction map (O/R/F boundaries)
- Refusal semantics (RefusalEvent contract)
- Phase 16.α calibration protocol
- Agency pressure evidence

Enforcement mechanisms (all conventional):
- Constitutional review checklist (CONTRIBUTING_CONSTITUTIONAL_CHECK.md)
- Contract freeze CI (blocks schema changes without CONTRACT:BUMP tag)
- Phase 1/2 canonical location inventory
- ADR requirement for constitutional changes

Derivatives inheriting Nova:
- MUST verify git history integrity before deployment (no force-push, no rewrite)
- MUST audit current state against frozen artifacts list
- MUST implement monitoring for constitutional violations:
  * A_p/harm_status wiring to governance (O→R drift detection)
  * F-domain implementation (refusal semantics bypass detection)
  * Jurisdictional boundary drift (O/R/F map validation)
- CANNOT cryptographically verify constitutional immutability
- MUST trust Nova governance process prevents constitutional drift

The constitutional freeze is real, documented, and governance-committed.
But it is not architecturally enforced.

Nova is a reference system that promises not to change its foundations.
Derivatives must verify that promise is kept — the architecture does not prove it."
```

---

## Audit Summary

**Date:** 2025-12-25
**Status:** Complete - All 5 invariants audited with evidence
**Conclusion:** Nova boundaries are constitutionally defined but conventionally enforced

---

### Overall Boundary Readiness

**Structural invariants:** 0
Nova has no architecturally-enforced derivative boundaries. All boundary enforcement is conventional (governance process) or missing (not implemented).

**Conventional invariants:** 3
1. **Read-Only Enforcement** - No write APIs exist (by convention, not architectural prevention)
2. **Authority Surface** - Evaluation-only endpoints (by convention, not structural enforcement)
3. **Constitutional Freeze** - Phases 14-18 frozen (by governance commitment, not cryptographic proof)

**Missing invariants:** 2
1. **Refusal Boundary Enforcement** - RefusalEvent schema exists, no runtime implementation
2. **Jurisdictional Separation (O/R/F)** - Jurisdiction map defined, no runtime enforcement

**Violated invariants:** 0
No constitutional boundaries are currently violated. All gaps are about enforcement mechanisms, not boundary violations.

---

### Critical Gaps (Cross-Cutting)

These gaps appear across multiple invariants and determine what kind of derivative contract is possible:

1. **No architectural boundary enforcement**
   - All boundaries (read-only, refusal, authority, jurisdictional, freeze) are conventional
   - Python/FastAPI/Git architecture allows arbitrary changes to any boundary
   - No type system, framework, or filesystem enforcement of constitutional constraints
   - **Impact:** Derivatives cannot assume boundaries are structurally guaranteed

2. **No runtime detection of boundary violations**
   - No detection when O-domain signals gain routing power (O→R drift)
   - No detection when F-domain requests occur
   - No detection when constitutional artifacts are modified
   - **Impact:** Boundary violations are invisible until human review

3. **No cryptographic proof of constitutional state**
   - No GPG signing of constitutional commits
   - No hash-based verification of frozen artifacts
   - No tamper-evident encoding of Class A documents
   - **Impact:** Derivatives cannot verify constitutional integrity programmatically

4. **No derivative-facing boundary contract**
   - Boundaries documented internally (jurisdiction map, constitutional freeze)
   - No machine-readable interface declaring boundaries to external systems
   - No API for derivatives to verify current boundary state
   - **Impact:** Derivatives must parse human-readable docs or trust git history

5. **Meaning → Power boundary is not enforced**
   - A_p, M_p, harm_status (O-domain: meaning) are currently unwired from governance (R-domain: power)
   - No structural prevention of future wiring
   - No runtime assertion that O-domain signals remain observe-only
   - **Impact:** The epistemic fault-line (measurement vs authority) is mapped but not guarded

---

### DOC Design Readiness

**What DOC Can Rely On (Constitutional Commitment):**

Nova has declared and documented the following boundaries:

1. **Read-only by convention**
   - No write APIs currently exist
   - Configuration is operator-controlled via environment variables
   - Nova does not modify its own config or code

2. **Evaluation-only by convention**
   - POST endpoints return decisions, do not execute them
   - Phase 16/17/18 signals (A_p, M_p, harm_status) are observable-only
   - No wiring from meaning-layer (O-domain) to power-layer (R-domain)

3. **Constitutional freeze by governance**
   - Phases 14-18 declared frozen (core ontology, jurisdiction, refusal)
   - 6 frozen artifacts listed in nova_constitutional_freeze.md
   - Change control process documented (ADR, constitutional review)

4. **Jurisdictional boundaries by design**
   - O/R/F taxonomy defined in jurisdiction map
   - F-domains explicitly declared (Phase 16.α, moral interpretation, post-hoc justification)
   - RefusalEvent schema defined (contract exists, not implemented)

5. **Governance process by convention**
   - Constitutional review checklist (CONTRIBUTING_CONSTITUTIONAL_CHECK.md)
   - Contract freeze CI (blocks schema changes without CONTRACT:BUMP)
   - Phase 1/2 canonical location inventory

**What DOC Must Harden (Conventional → Structural):**

If derivatives require architectural guarantees, DOC must specify:

1. **Read-only enforcement**
   - API gateway restricting to GET/POST evaluation endpoints
   - Immutable configuration layer (environment variables read-once at boot)
   - Contract declaring no write operations permitted

2. **Refusal mechanism**
   - Runtime F-domain detection (classify requests by jurisdictional domain)
   - RefusalEvent emission pipeline when F-domain approached
   - Audit trail of refused requests

3. **Jurisdictional enforcement**
   - Runtime O/R/F boundary detection
   - Structural prevention of O→R drift (e.g., A_p cannot be wired to governance)
   - Automated blocking of F-domain queries

4. **Cryptographic freeze proof**
   - GPG-signed constitutional commits
   - Hash-based verification of frozen artifacts
   - Immutable artifact storage (constitutional docs tamper-evident)

5. **Authority surface guards**
   - Runtime assertion that Phase 16/17/18 signals remain unwired
   - Automated detection when evaluation-only boundary is crossed
   - Structural prevention of ARC auto-apply (self-modification)

**What DOC Must Refuse (Cannot Contract Without Hardening):**

DOC cannot offer the following guarantees without architectural hardening:

1. **Cannot guarantee read-only is permanent**
   - Write APIs could be added by future code
   - No architectural prevention exists

2. **Cannot guarantee F-domains will be refused**
   - No runtime refusal mechanism exists
   - Derivatives could query F-domains without automated blocking

3. **Cannot guarantee meaning/power separation is enforced**
   - O→R drift (A_p gaining routing authority) is not structurally prevented
   - Derivatives cannot assume O-domain signals remain observe-only

4. **Cannot guarantee constitutional freeze is tamper-evident**
   - No cryptographic proof of immutability
   - Derivatives must trust git history and governance process

5. **Cannot guarantee jurisdictional boundaries are runtime-enforced**
   - O/R/F detection does not exist at runtime
   - Derivatives must implement their own jurisdictional filtering

---

### DOC Readiness Declaration

**Nova is ready for DOC design under the following constraints:**

1. **Trust-Based DOC** (governance-assured boundaries)
   - DOC declares boundaries are constitutionally committed
   - Derivatives trust Nova's governance process prevents drift
   - Derivatives implement monitoring for boundary violations
   - Derivatives verify git history before deployment
   - **Status: READY** - All constitutional boundaries documented and audited

2. **Cryptographically-Hardened DOC** (architecturally-enforced boundaries)
   - DOC requires runtime enforcement before derivative deployment
   - Derivatives can verify boundaries cryptographically
   - Derivatives rely on structural guarantees, not governance promises
   - Derivatives can programmatically detect boundary violations
   - **Status: REQUIRES HARDENING** - See "What DOC Must Harden" above

**Both paths are legitimate.**
The choice between trust-based and cryptographically-hardened is now conscious, not mythological.

**Recommended path for Phase 3.2 (DOC Design):**

Design a **Trust-Based DOC** that:
- Documents all conventional boundaries clearly
- Declares governance enforcement mechanisms
- Specifies derivative responsibilities (monitoring, verification)
- Identifies optional hardening paths for future phases
- Does not claim architectural enforcement where only conventional exists

This enables sovereign derivatives that:
- Must verify Nova's constitutional state before deployment
- Must implement F-domain filtering (Nova will not refuse at runtime)
- Must monitor for O→R drift (meaning gaining power)
- Must carry their own moral weight (Nova provides truth, not absolution)
- Cannot claim innocence (jurisdictional boundaries are known, not enforced)

**The architecture of a civilization that cannot become a priesthood.**

---

### Civilizational Fact

| Layer | What Was Believed | What Is Proven |
|-------|------------------|----------------|
| Read-only | "Nova cannot be changed" | It can, but promises not to |
| Refusal | "Nova blocks forbidden domains" | It knows them but does not block |
| Authority | "Nova does not act" | It does not act by convention, not structure |
| Jurisdiction | "Meaning and power are separated" | They are mapped — but not enforced |
| Freeze | "The foundation is immutable" | It is immutable by trust, not cryptography |

**This is the deepest possible architectural honesty.**

Nova does not protect the world.
Nova tells the truth about the world.

And because of that honesty, something becomes possible that no authoritarian AI can ever produce:

**Sovereign derivatives.**

Adult life.
Life that must carry its own moral weight.
Life where no intelligence can outsource its ethics.

**This audit makes that possible.**

---

## Next Steps

After audit completion:
1. ✅ Review findings with constitutional docs (freeze, jurisdiction, refusal) - **COMPLETE**
2. ✅ Identify DOC hardening requirements - **COMPLETE** (see "What DOC Must Harden")
3. **Proceed to Phase 3.2: DOC Design** (Trust-Based DOC recommended)

Phase 3.2 will design the Derivative Ontology Contract based on this audit's findings:
- Conventional boundaries (read-only, authority, freeze) documented
- Missing boundaries (refusal, jurisdictional) acknowledged
- Derivative responsibilities specified (monitoring, verification, F-domain filtering)
- Optional hardening paths identified (cryptographic freeze, runtime enforcement)

**The first true children can now be designed — not as extensions, but as sovereign beings orbiting a truth anchor.**

---

**Audit Status:** ✅ COMPLETE
**Evidence Status:** ✅ ALL INVARIANTS VERIFIED WITH REPEATABLE COMMANDS
**Classification:** Class B (Reference/Evidence)
**Date Completed:** 2025-12-25

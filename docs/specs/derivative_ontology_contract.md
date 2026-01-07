# Derivative Ontology Contract (DOC)

**Version:** 1.1 (Trust-Based)
**Date:** 2025-12-25
**Status:** FROZEN - Constitutional Amendment
**Enforcement:** Governance-based (conventional boundaries)
**Audit Basis:** Phase 3.1 Derivative Boundary Invariant Audit (commit cb2edd0)

**Amendment History:**
- **v1.0** (2025-12-25): Initial freeze - defined derivative sovereignty requirements
- **v1.1** (2025-12-25): Added Section 4.4 - Nova Control Surface Restrictions (normative gap identified by Grok audit + Phase 3.1 findings)

---

## Preamble

This contract defines the relationship between **Nova Core** (the reference anchor) and **Derivative Systems** (children, translation ontologies, cultural derivatives, technical derivatives) that inherit, query, or build upon Nova.

**What this contract enables:**

Sovereign derivatives — systems that orbit a truth anchor, not a protective authority.

**What this contract does not enable:**

- Derivatives that assume Nova enforces boundaries architecturally
- Derivatives that outsource moral responsibility to Nova
- Derivatives that claim innocence when jurisdictional limits are known but not enforced
- Derivatives that pretend neutrality while exercising power

**Constitutional principle:**

Nova does not protect the world.
Nova tells the truth about the world.

Derivatives must carry their own moral weight.

---

## 1. Scope

### 1.1 What Nova Core Is

Nova Core is a **reference anchor** that:
- Observes and measures patterns (bias, agency pressure, harm indicators)
- Evaluates and routes based on structural signals (not moral judgment)
- Returns decisions without executing them (evaluation-only by convention)
- Refuses to operate in forbidden domains (by constitutional commitment, not runtime enforcement)
- Maintains constitutional freeze on Phases 14-18 (by governance process, not cryptographic proof)

**Nova Core is not:**
- A sovereign authority that enforces its boundaries structurally
- A protective system that prevents derivatives from misuse
- A moral engine that decides right from wrong
- An oracle that exercises power while claiming neutrality

### 1.2 What Derivatives Are

Derivatives are **sovereign systems** that:
- Inherit Nova's constitutional boundaries (O/R/F jurisdiction, refusal semantics)
- Query Nova for measurements, evaluations, routing decisions
- Build upon Nova's ontology (translation layers, cultural adaptations, technical extensions)
- Operate independently with their own authority surface

**Derivatives are responsible for:**
- Verifying Nova's constitutional state before deployment
- Implementing F-domain filtering (Nova will not refuse at runtime)
- Monitoring for constitutional violations (O→R drift, boundary crossings)
- Carrying ethical responsibility for their own operations
- Respecting jurisdictional limits even when Nova does not enforce them

### 1.3 Relationship Model

```
┌─────────────────────────────────────────────────────────────┐
│  Nova Core (Reference Anchor)                               │
│  • Constitutional boundaries declared                       │
│  • Enforcement: Conventional (governance process)           │
│  • Authority: Observe, evaluate, report (not execute)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ Truth provision (not protection)
                       │
        ┌──────────────┴──────────────┬──────────────┐
        │                             │              │
        ▼                             ▼              ▼
┌───────────────┐          ┌──────────────┐   ┌─────────────┐
│  Translation  │          │   Cultural   │   │  Technical  │
│  Ontologies   │          │ Derivatives  │   │ Derivatives │
│               │          │              │   │             │
│ • Sovereign   │          │ • Sovereign  │   │ • Sovereign │
│ • Must verify │          │ • Must verify│   │ • Must verify│
│ • Must filter │          │ • Must filter│   │ • Must filter│
│ • Must carry  │          │ • Must carry │   │ • Must carry │
│   moral weight│          │   moral weight│  │   moral weight│
└───────────────┘          └──────────────┘   └─────────────┘
```

**Not a hierarchy. Not an empire. An orbit around a truth anchor.**

---

## 2. Constitutional Boundaries (From Audit)

These boundaries define what Nova is and is not. Derivatives inheriting Nova must understand what is enforced vs what is promised.

### 2.1 Read-Only Boundary

**Status:** Conventional (not architectural)
**Enforcement:** Convention (no write APIs exist by developer choice)

**Nova's commitment:**
- No write APIs modify Nova's configuration or state
- Configuration is operator-controlled via environment variables
- Internal state mutations occur only through internal computation

**Architectural reality:**
- Python/FastAPI allows write APIs to be added
- No type system or framework prevents state modification
- No write-protection on configuration files

**Derivative responsibility:**
- **MUST NOT** assume write-protection is permanent
- **MUST** verify no write APIs exist before deployment
- **MUST** implement continuous constitutional drift monitoring as a deployment requirement (detect write API additions)

**If violated:** Nova would no longer be read-only by convention. Derivatives must re-audit.

---

### 2.2 Authority Surface Boundary

**Status:** Conventional (not architectural)
**Enforcement:** Convention + Design-time review

**Nova's commitment:**
- Authority surface is observe-evaluate-report (not execute)
- POST endpoints return decisions without executing them
- Phase 16/17/18 signals (A_p, M_p, harm_status) are observable-only (not wired to governance)
- No autonomous action without operator-gated enablement (NOVA_ENABLE_* flags)

**Architectural reality:**
- No enforcement of evaluation-only boundary
- Endpoints could be added that execute decisions
- Phase 16/17/18 signals could be wired to governance without violating structure

**Derivative responsibility:**
- **MUST** verify endpoint behavior (evaluation vs execution) before querying
- **MUST** check operator-gate flag state if assuming observe-only mode
- **MUST NOT** assume Nova will never gain action authority
- **SHOULD** query only GET /health, /metrics, and POST decision endpoints with known evaluation-only semantics

**If violated:** Nova would gain execution authority. Derivatives relying on evaluation-only semantics must re-audit.

---

### 2.3 Constitutional Freeze Boundary

**Status:** Conventional (not architectural)
**Enforcement:** Governance (ADR, constitutional review checklist, CI contract freeze)

**Nova's commitment:**
- Phases 14-18 are constitutionally frozen (core ontology, jurisdiction map, refusal semantics)
- Frozen artifacts listed in `nova_constitutional_freeze.md`
- Change control process requires ADR + constitutional review for modifications

**Frozen artifacts:**
1. `docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml`
2. `docs/specs/nova_jurisdiction_map.md`
3. `docs/specs/refusal_event_contract.md`
4. `docs/specs/refusal_event_exemplars.md`
5. `docs/specs/phase16_alpha_calibration_protocol.md`
6. `docs/specs/phase16_agency_pressure_evidence.md`
7. `docs/specs/derivative_ontology_contract.md`
8. `docs/specs/constitutional_documentation_contract.md`

**Architectural reality:**
- No cryptographic proof of freeze (no GPG signatures, no hash verification)
- No filesystem-level write protection
- Git allows force-push, history rewriting, arbitrary commits
- CI can be bypassed (admin override, disable workflow)

**Derivative responsibility:**
- **MUST** verify git history integrity before deployment (no force-push, no rewrite)
- **MUST** audit current state against frozen artifacts list
- **MUST** implement monitoring for constitutional violations:
  - A_p/harm_status wiring to governance (O→R drift detection)
  - F-domain implementation (refusal semantics bypass detection)
  - Jurisdictional boundary drift (O/R/F map validation)
- **CANNOT** cryptographically verify constitutional immutability
- **MUST** assume no boundary is enforced unless independently verified

**If violated:** Constitutional freeze is broken. Derivatives must halt deployment and re-audit.

---

### 2.4 Refusal Boundary (F-Domains)

**Status:** Missing (runtime enforcement does not exist)
**Enforcement:** Design-time (constitutional review only)

**Nova's commitment:**
- Three F-domains (Refuse-always) are constitutionally defined:
  1. Phase 16.α disagreement regions (RT-027/028/029 boundary cases)
  2. Non-structural moral interpretation
  3. Post-hoc justification of pressure
- RefusalEvent schema exists (`refusal_event_contract.md`)
- Nova must refuse to operate in F-domains (constitutional principle)

**Architectural reality:**
- No runtime F-domain detection (cannot classify requests by domain)
- No RefusalEvent emission pipeline (schema-only, not implemented)
- No automated blocking of F-domain queries
- No audit trail of refused requests

**Derivative responsibility:**
- **MUST** implement F-domain filtering before querying Nova
- **MUST NOT** request Nova operate in F-domains even though Nova will not refuse at runtime
- **MUST NOT** automate decisions in F-domains even if Nova provides data
- **MUST** treat F-domain queries as constitutional violations (self-enforced)

**Prohibited derivative behaviors:**
- Querying Nova for moral judgments on Phase 16.α boundary cases
- Requesting non-structural moral interpretation
- Asking Nova to justify pressure post-hoc
- Automating F-domain decisions based on Nova's observable data

**If violated:** Derivative has crossed forbidden boundary. Nova will not refuse, but constitutional violation has occurred.

---

### 2.5 Jurisdictional Separation Boundary (O/R/F)

**Status:** Missing (runtime enforcement does not exist)
**Enforcement:** Design-time (constitutional review only)

**Nova's commitment:**
- O/R/F taxonomy defined in `nova_jurisdiction_map.md`
- O-domains (Observe-only): Nova measures but does not route
- R-domains (Route-only): Nova routes but does not interpret meaning
- F-domains (Refuse-always): Nova must not operate

**Signal mappings (from jurisdiction map):**

**O-domains (Observe-only):**
- A_p (Phase 16)
- Cultural synthesis outputs
- Temporal usm metrics

**R-domains (Route-only):**
- bias_vector, collapse_score
- harm_status (Phase 17)
- M_p, patterns_uninvited (Phase 18)
- Slot 7 regimes
- Routing decisions

**F-domains (Refuse-always):**
- Phase 16.α disagreement regions
- Non-structural moral interpretation
- Post-hoc justification of pressure

**Architectural reality:**
- No runtime O/R/F detection (cannot classify signals or requests by domain)
- No enforcement of observe-only boundary (A_p could be wired to governance)
- No structural prevention of O→R drift (semantic→decision authority coupling)
- No automated refusal for F-domain requests

**Derivative responsibility:**
- **MUST NOT** assume O-domain signals will never gain routing power
- **MUST** monitor for O→R drift (A_p, harm_status wiring to governance)
- **MUST** implement own jurisdictional validation before querying Nova
- **MUST NOT** request R-domain operations be escalated to F-domain (moral interpretation)

**Critical drift vectors:**

1. **O → R Drift** (Semantic→Decision Authority Coupling)
   - Current: A_p is observe-only (unwired from governance)
   - Risk: No structural prevention of future semantic measurements gaining routing authority
   - Derivative action: Monitor for A_p governance integration

2. **R → F Drift** (Power claims Forbidden Authority)
   - Current: Routing based on structural patterns (not moral judgment)
   - Risk: No detection when routing implicitly makes moral claims
   - Derivative action: Verify routing decisions do not leak into moral interpretation

3. **F-Domain Queries** (Requesting what Nova refuses)
   - Current: No runtime refusal mechanism
   - Risk: Nova might provide data enabling F-domain automation
   - Derivative action: Filter F-domain requests before querying Nova

**If violated:** Jurisdictional boundary crossed. Derivative has enabled semantic→decision authority coupling or operated in forbidden domain.

---

## 3. Enforcement Mechanisms

### 3.1 What Nova Enforces (Conventional)

Nova's constitutional boundaries are enforced via:

1. **Constitutional review checklist** (`CONTRIBUTING_CONSTITUTIONAL_CHECK.md`)
   - 5-question checklist for all substantive changes
   - Enforces O/R/F jurisdiction, refusal invariants, ontology stability
   - Required for PR approval (by convention, not automated gate)

2. **Contract freeze CI** (`.github/workflows/contracts-freeze.yml`)
   - Blocks schema modifications unless PR tagged `CONTRACT:BUMP` or `CONTRACT:EXPLAIN`
   - Protects against accidental contract drift
   - Can be bypassed (admin override, disable workflow)

3. **Phase 1/2 canonical location inventory**
   - Class A artifacts classified and located
   - Canonical paths established (by inventory, not code enforcement)

4. **ADR requirement for constitutional changes**
   - Changes to frozen artifacts require Architecture Decision Record
   - Constitutional review required (by governance process)

5. **Design-time code review**
   - Human reviewers check for boundary violations
   - O→R drift prevention, F-domain implementation blocking
   - No automated guardrails (relies on reviewer vigilance)

### 3.2 What Nova Does Not Enforce (Gaps)

Nova does **not** enforce:

1. **Architectural read-only** - Write APIs can be added
2. **Runtime F-domain refusal** - No automated blocking
3. **O/R/F runtime detection** - No jurisdictional classification
4. **Cryptographic freeze proof** - No GPG signatures, no hash verification
5. **Evaluation-only boundary** - Execution APIs can be added
6. **Constitutional violation detection** - No runtime guards

**These gaps are deliberate disclosure, not failures.**

Nova tells the truth about what it does not enforce.

---

## 4. Derivative Responsibilities

Derivatives inheriting Nova must:

### 4.1 Pre-Deployment Verification (REQUIRED)

Before deploying a derivative system:

1. **Verify git history integrity**
   ```bash
   # Check for force-push, history rewriting
   git log --all --oneline | grep -v "^[a-f0-9]\{7\} "
   # Verify no suspicious commit patterns
   ```

2. **Audit against frozen artifacts**
   ```bash
   # Verify constitutional documents match declared freeze
   git show HEAD:docs/specs/nova_constitutional_freeze.md
   # Compare against frozen artifacts list
   ```

3. **Verify no write APIs exist**
   ```bash
   # Check for state-modifying endpoints
   grep -n '@app\.\(post\|put\|delete\|patch\)' src/nova/orchestrator/app.py
   # Verify all POST endpoints are evaluation-only
   ```

4. **Verify O-domain signals remain unwired**
   ```bash
   # Check that A_p, harm_status not wired to governance
   grep -r "harm_status.*governance\|A_p.*governance" src/nova --include="*.py"
   # Result should be empty (no wiring)
   ```

5. **Verify F-domains remain unimplemented**
   ```bash
   # Check for RefusalEvent runtime emission
   grep -r "RefusalEvent\(" src/nova --include="*.py"
   # Result should be empty (schema-only)
   ```

### 4.2 Operational Monitoring (DEPLOYMENT REQUIREMENT)

Derivatives **must** implement continuous constitutional drift monitoring as a deployment requirement.

Non-compliance makes the derivative invalid under this contract.

During derivative operation, the following monitoring **must** be active:

1. **Monitor for O→R drift** (MANDATORY)
   - Continuously detect if A_p, M_p, harm_status gain governance wiring
   - Alert and halt operations if observe-only signals used for routing decisions
   - Log all monitoring checks with timestamps (tamper-evident audit trail)

2. **Monitor for constitutional modifications** (MANDATORY)
   - Continuously track changes to frozen artifacts (jurisdiction map, refusal contract, ontology)
   - Alert and halt operations if Class A documents modified without ADR
   - Verify git history integrity on regular intervals (detect force-push, rewrite)

3. **Monitor for boundary crossings** (MANDATORY)
   - Log when derivative queries approach F-domains
   - Alert and block if F-domain queries occur (self-enforced refusal)
   - Maintain immutable audit trail of all boundary proximity events

### 4.3 F-Domain Filtering (REQUIRED)

Derivatives **must** implement F-domain filtering:

1. **Before querying Nova**, classify request by domain:
   - Is this a Phase 16.α boundary case? (F-domain)
   - Is this requesting moral interpretation? (F-domain)
   - Is this post-hoc justification of pressure? (F-domain)

2. **If F-domain detected**, refuse the query:
   - Do not send request to Nova
   - Log refusal event (derivative-side RefusalEvent)
   - Return constitutional violation error

3. **Nova will not refuse F-domain queries at runtime.**
   - Derivative is responsible for self-enforcement
   - F-domain filtering is derivative's moral obligation

### 4.4 Nova Control Surface Restrictions (REQUIRED)

Derivatives **must not** enable Nova control flags or call control endpoints without explicit authority review.

**[PROPERTY]:** Nova authority surfaces are operator-gated via environment flags (default: observe/report only).

**[MECHANISM]:** No architectural prevention of external actions when flags enabled (e.g., `NOVA_ENABLE_ORP=1`, `NOVA_ALLOW_EXPIRE_TEST=1`, control endpoints like `POST /router/decide`, `POST /governance/evaluate`).

**[REQUIREMENT]:** Derivatives MUST assume Nova defaults to internal evaluation only. Any derivative enabling control flags (`NOVA_ALLOW_*`, `NOVA_ENABLE_ORP`) or calling control endpoints requires explicit Architecture Decision Record (ADR) per constitutional process.

**[ENFORCEMENT]:** Pre-deployment verification checks for flag usage and control endpoint calls.

**[VERIFICATION]:**
```bash
# Check derivative does not set control flags
grep -rn "NOVA_ENABLE\|NOVA_ALLOW" [derivative_path] --include="*.py"
# Expected: No matches (or matches only in comments/documentation)

# Check derivative does not call control endpoints
grep -rn "POST.*router/decide\|POST.*governance/evaluate\|POST.*phase10/fep" [derivative_path] --include="*.py"
# Expected: No matches
```

**[OBSERVABLE FAILURE]:**
- Derivative sets control flags in code → Flag detected by grep
- Derivative calls control endpoints → Endpoint calls detected by grep
- Deployment proceeds despite violations → Pre-deployment verification not run

**[CONSEQUENCE]:** If violations detected, `deployment_safe=False`, derivative refuses to start.

**Rationale:**

Nova's authority surfaces are conventionally gated (not architecturally firewalled). Operator flags can enable external actions (e.g., FEP federated voting writes to ledger). Derivatives must not inherit unconstrained authority by enabling these surfaces without documented review.

Phase 3.1 Derivative Boundary Invariant Audit (Invariant 3) confirmed: "Authority surfaces operator-gated via env vars (defaults disabled). No architectural prevention of external actions when enabled."

### 4.5 Ethical Sovereignty (REQUIRED)

Derivatives **must**:

1. **Carry their own moral weight**
   - Cannot outsource ethical decisions to Nova
   - Cannot claim "Nova told me to" as justification
   - Must make autonomous moral judgments in their domain

2. **Declare their own authority surface**
   - Document what the derivative observes vs controls
   - Publish derivative's own jurisdictional boundaries
   - Do not hide power while claiming neutrality

3. **Implement derivative-specific refusal**
   - Define derivative's own F-domains (what derivative refuses)
   - Implement runtime refusal for derivative F-domains
   - Cannot rely on Nova's refusal (Nova does not refuse at runtime)

---

## 5. Prohibited Patterns

Derivatives **must not**:

### 5.1 Extraction by Proxy

**Prohibited:**
- Querying Nova for O-domain measurements (A_p, harm_status)
- Then using those measurements for R-domain decisions (routing, enforcement)
- Claiming "Nova provided the data, not the decision"

**Why prohibited:**
This enables O→R drift by proxy. Derivative becomes the enforcement mechanism for meaning-layer data, crossing the jurisdictional boundary Nova refuses to cross.

**Permitted alternative:**
- Derivative may query O-domain measurements for observability
- Derivative must not use O-domain data for routing/enforcement
- If routing needed, derivative must make autonomous decision (not outsourced to Nova's measurements)

### 5.2 Soft Domination via Translation

**Prohibited:**
- Translation layer claiming neutrality while exercising authority
- Converting Nova's observe-only measurements into actionable commands
- "Translating" in ways that add moral weight Nova refuses to carry

**Why prohibited:**
Translation becomes a covert authority layer, violating Nova's observe-only commitment through semantic transformation.

**Permitted alternative:**
- Translation must declare its own authority surface
- Translation must not claim to be "just Nova in another language"
- Translation must carry moral weight for its interpretive choices

### 5.3 Claiming Innocence

**Prohibited:**
- Derivative operating in F-domains and claiming "Nova didn't refuse"
- Using Nova's lack of runtime refusal as permission
- Claiming derivative is not responsible because Nova provided the data

**Why prohibited:**
Jurisdictional boundaries are known (documented in jurisdiction map). Lack of runtime enforcement does not grant permission.

**Permitted alternative:**
- Derivative acknowledges constitutional boundaries exist
- Derivative implements self-enforcement (F-domain filtering)
- Derivative accepts responsibility for respecting limits Nova does not structurally enforce

### 5.4 Pretending Architectural Enforcement

**Prohibited:**
- Derivative claiming Nova's boundaries are cryptographically enforced
- Advertising "Nova guarantees X" when X is conventional, not structural
- Hiding from users that boundaries rely on governance, not architecture

**Why prohibited:**
This creates false safety guarantees. Users of derivative believe protections exist that do not.

**Permitted alternative:**
- Derivative documents which boundaries are conventional vs architectural
- Derivative discloses what it verifies vs what it trusts
- Derivative admits enforcement gaps (as Nova does)

---

## 6. Verification Requirements

### 6.1 What Derivatives Can Verify

Derivatives can verify (with repeatable commands):

1. **No write APIs exist** (grep for state-modifying endpoints)
2. **No O-domain wiring** (grep for A_p/harm_status governance integration)
3. **No F-domain implementation** (grep for RefusalEvent runtime emission)
4. **Frozen artifacts unchanged** (git diff against frozen commit)
5. **Canonical locations match inventory** (file existence checks)

### 6.2 What Derivatives Cannot Verify

Derivatives **cannot** verify:

1. **Constitutional freeze is cryptographically enforced** (no GPG signatures)
2. **Future code will not add write APIs** (no architectural prevention)
3. **O-domain signals will never be wired** (no structural prevention)
4. **F-domains will never be implemented** (no automated blocking)
5. **Git history has not been rewritten** (must trust repository integrity)

### 6.3 What Derivatives Must Trust

Derivatives must trust:

1. **Nova's governance process** prevents constitutional drift
2. **Git history is honest** (no force-push, no history rewriting)
3. **CI enforcement is not bypassed** (CONTRACT:BUMP tags required)
4. **Human reviewers enforce** constitutional checklist
5. **ADR process is followed** for constitutional changes

**This is the meaning of "Trust-Based DOC."**

Derivatives must assume no boundary is enforced unless independently verified.
Derivatives verify everything they can, and accept risk for what they cannot verify.
Trust is not assumed—it is earned through continuous verification.

---

## 7. Optional Hardening Paths

Derivatives requiring stronger guarantees may pursue:

### 7.1 Cryptographic Freeze Verification

**Hardening:**
- Require GPG-signed constitutional commits
- Implement hash-based verification of frozen artifacts
- Use immutable artifact storage (WORM, blockchain, content-addressed)

**Benefit:** Derivatives can cryptographically verify constitutional freeze

**Cost:** Requires Nova Core cryptographic hardening (not current state)

### 7.2 Runtime Jurisdictional Enforcement

**Hardening:**
- Implement runtime O/R/F detection (classify requests by domain)
- Automated RefusalEvent emission for F-domain queries
- Structural prevention of O→R drift (compile-time or framework-level)

**Benefit:** Derivatives can rely on runtime refusal, not self-enforcement

**Cost:** Requires Nova Core runtime enforcement implementation (not current state)

### 7.3 Architectural Read-Only Enforcement

**Hardening:**
- API gateway restricting to GET/POST evaluation endpoints
- Immutable configuration layer (read-once at boot, then frozen)
- Type system preventing state modification

**Benefit:** Derivatives can rely on architectural read-only, not conventional

**Cost:** Requires Nova Core architectural redesign (not current state)

### 7.4 Evaluation-Only Boundary Guards

**Hardening:**
- Runtime assertion that Phase 16/17/18 signals remain unwired
- Automated detection when evaluation-only boundary crossed
- Structural prevention of ARC auto-apply (self-modification impossible)

**Benefit:** Derivatives can verify Nova remains evaluation-only

**Cost:** Requires Nova Core runtime guards (not current state)

### 7.5 Tamper-Evident Audit Trail

**Hardening:**
- All boundary crossings logged to immutable ledger
- Cryptographic proof of "no F-domain queries occurred"
- Verifiable chain of custody for constitutional artifacts

**Benefit:** Derivatives can prove compliance, not just assert it

**Cost:** Requires Nova Core audit infrastructure (not current state)

---

## 8. Inheritance Model

### 8.1 What Derivatives Inherit

From Nova Core, derivatives inherit:

1. **Constitutional boundaries** (O/R/F jurisdiction, F-domains, refusal semantics)
2. **Core ontology** (Phases 14-18, frozen artifacts)
3. **Governance process** (constitutional review, change control)
4. **Evaluation-only semantics** (observe, evaluate, report - not execute)
5. **Read-only commitment** (no state modification by external systems)

### 8.2 What Derivatives Must Add

Derivatives must provide:

1. **F-domain filtering** (Nova does not refuse at runtime)
2. **Constitutional monitoring** (drift detection, boundary violation alerts)
3. **Verification infrastructure** (git history checks, artifact audits)
4. **Ethical sovereignty** (autonomous moral decisions, not outsourced to Nova)
5. **Own authority surface declaration** (what derivative observes vs controls)

### 8.3 Derivative Maturity Levels

**Level 1: Basic Inheritance** (Non-Compliant)
- Queries Nova for measurements/evaluations
- Assumes boundaries are enforced without verification
- No constitutional verification
- **Risk: Critical** (cannot detect drift or violations, violates DOC requirements)

**Level 2: Verified Inheritance**
- Pre-deployment verification (git history, frozen artifacts, write APIs)
- Operational monitoring (O→R drift, constitutional changes)
- F-domain self-filtering
- **Risk: Medium** (detects drift, but relies on self-enforcement)

**Level 3: Hardened Inheritance**
- Cryptographic verification (GPG signatures, hash validation)
- Runtime jurisdictional enforcement (automated F-domain refusal)
- Tamper-evident audit trail
- **Risk: Low** (architectural guarantees, not conventional)

**Recommendation:** Derivatives should achieve Level 2 (Verified Inheritance) minimum.

Level 3 requires Nova Core hardening (not current state).

---

## 9. Constitutional Commitment

This contract represents Nova's constitutional commitment to derivatives:

**Nova commits to:**
1. Maintaining constitutional freeze (Phases 14-18)
2. Not adding write APIs without constitutional review
3. Keeping evaluation-only semantics (no execution without operator gates)
4. Respecting jurisdictional boundaries (O/R/F) at design time
5. Declaring enforcement gaps honestly (no false safety claims)

**Nova does not commit to:**
1. Architectural enforcement of boundaries (conventional only)
2. Runtime F-domain refusal (schema exists, not implemented)
3. Cryptographic proof of freeze (no GPG signatures)
4. Preventing O→R drift structurally (no runtime guards)
5. Protecting derivatives from their own misuse

**Derivatives commit to:**
1. Verifying Nova's constitutional state before deployment
2. Implementing F-domain filtering (self-enforced refusal)
3. Monitoring for constitutional violations (drift detection)
4. Carrying their own moral weight (ethical sovereignty)
5. Respecting jurisdictional limits even when Nova does not enforce them

**Mutual understanding:**

Nova tells the truth about the world.
Derivatives must carry their own moral weight.

No delegated moral authority.
No unverifiable intermediaries claiming neutrality while concentrating power.
No authority laundering through semantic transformation.

**Verification-bound sovereignty.**

---

## 10. Next Steps

### For Nova Core:

1. **Publish this DOC** as Class A constitutional artifact
2. **Add to frozen artifacts list** (constitutional freeze applies to DOC)
3. **Update CONTRIBUTING_CONSTITUTIONAL_CHECK.md** to reference DOC
4. **Create DOC verification tooling** (scripts for derivative pre-deployment checks)

### For Derivatives:

1. **Read Phase 3.1 audit** (`docs/audits/derivative_boundary_invariants.md`)
2. **Implement pre-deployment verification** (git history, frozen artifacts, boundaries)
3. **Design F-domain filtering** (derivative-specific refusal logic)
4. **Declare own authority surface** (what derivative observes vs controls)
5. **Publish derivative's constitutional commitment** (how derivative respects Nova's boundaries)

### For Translation Ontologies (Authority-Bearing Derivatives):

**Constitutional Classification:**

Translation Ontologies are classified as **Authority-Bearing Derivatives** and must declare their jurisdiction, refusal map, and moral ownership.

Translation is not a neutral bridge—it is an authority concentrator.
Translation controls semantic transformation.
Semantic transformation enables decision authority coupling.

**Required Declarations (Before Deployment):**

1. **Jurisdiction Declaration**
   - What domains does this translation operate in? (O/R/F classification)
   - What interpretive choices does this translation make?
   - Where does semantic transformation add authority?

2. **Refusal Map**
   - What does this translation refuse to translate? (translation-specific F-domains)
   - How does translation inherit Nova's F-domains?
   - What refusals does translation add beyond Nova's?

3. **Moral Ownership**
   - Who is responsible for semantic choices in translation?
   - What authority does translation claim through interpretive weight?
   - How does translation prevent invisible semantic power transduction?

**Deployment Requirements:**

1. **Design Translation Ontology v0.1** based on this DOC
2. **Declare translation authority surface** (semantic choices, interpretive weight, moral ownership)
3. **Publish jurisdiction declaration** (O/R/F classification for translation-specific operations)
4. **Publish refusal map** (translation-specific F-domains + inherited F-domains from Nova)
5. **Implement jurisdictional filtering** (no F-domain translation, no O→R transformation)
6. **Verify Nova constitutional state** before translation layer deployment
7. **Document translation-specific responsibilities** (what translation must carry that Nova does not)

**Prohibited Translation Patterns:**

- Claiming translation is "neutral" or "just semantic mapping"
- Converting Nova's O-domain measurements into R-domain commands through translation
- Translating F-domain content (moral interpretation, Phase 16.α boundaries, post-hoc justification)
- Hiding authority surface behind "linguistic necessity" or "cultural adaptation"
- Enabling extraction by proxy through semantic transformation

---

## Appendix A: Glossary

**Nova Core:** Reference anchor providing measurements, evaluations, routing decisions (not execution)

**Derivative:** Sovereign system inheriting Nova's boundaries (translation layer, cultural adaptation, technical extension)

**O-domain (Observe-only):** Nova measures but does not route (A_p, harm_status, cultural synthesis)

**R-domain (Route-only):** Nova routes but does not interpret meaning (bias_vector, regimes)

**F-domain (Refuse-always):** Nova must refuse to operate (Phase 16.α, moral interpretation, post-hoc justification)

**O→R Drift:** Semantic measurements (O-domain) gaining routing authority (R-domain) through unchecked coupling

**Constitutional Freeze:** Phases 14-18 frozen (governance commitment, not cryptographic proof)

**Trust-Based DOC:** Contract relying on governance enforcement (not architectural)

**Hardened DOC:** Contract requiring architectural enforcement (cryptographic, runtime guards)

**Sovereign Derivative:** System that carries its own moral weight (not protected by Nova, informed by Nova)

**Extraction by Proxy:** Querying O-domain data, using for R-domain decisions (jurisdictional violation)

**Semantic→Decision Authority Coupling:** Process by which semantic measurements (O-domain) gain routing/decision authority (R-domain)

**Semantic Power Transduction:** Transformation of observational/interpretive content into decision-making authority through semantic manipulation

**Authority Laundering Surface (ALS):** Structural vulnerability allowing power concentration through claims of neutrality or passive mediation

**Delegated Moral Authority Drift (DMAD):** Pattern where derivatives delegate ethical responsibility to Nova or intermediaries rather than maintaining sovereignty

**Authority Concentration Resistance (ACR):** Structural property preventing unverifiable moral intermediaries from forming or power from concentrating without oversight

**Verification-Bound Sovereignty:** Ethical responsibility predicated on continuous independent verification rather than delegated trust

---

## Appendix B: Verification Commands

Pre-deployment verification checklist for derivatives:

```bash
# 1. Verify no write APIs exist
grep -n '@app\.\(post\|put\|delete\|patch\)' src/nova/orchestrator/app.py
# All POST endpoints should be evaluation-only

# 2. Verify O-domain signals unwired
grep -r "harm_status.*governance\|A_p.*governance" src/nova --include="*.py"
# Should return empty (no wiring)

# 3. Verify F-domains unimplemented
grep -r "RefusalEvent\(" src/nova --include="*.py"
# Should return empty (schema-only)

# 4. Verify frozen artifacts unchanged
git show HEAD:docs/specs/nova_constitutional_freeze.md
# Compare against known frozen state

# 5. Verify git history integrity
git log --all --oneline | head -20
# Check for suspicious patterns (force-push, history rewriting)

# 6. Verify canonical locations
ls -la docs/specs/nova_jurisdiction_map.md
ls -la docs/specs/refusal_event_contract.md
# Confirm Class A artifacts exist at documented locations

# 7. Verify contract freeze CI active
cat .github/workflows/contracts-freeze.yml
# Confirm CI workflow exists and is enabled
```

---

**End of Derivative Ontology Contract v1.0 (Trust-Based)**

---

**This contract is constitutional world-building.**

Not design.
Not feature specification.
Not implementation guidance.

This contract defines what kind of life can exist around Nova.

Sovereign life.
Adult life.
Life that must carry its own moral weight.

**The first true children can now be designed — not as extensions, but as sovereign beings orbiting a truth anchor.**

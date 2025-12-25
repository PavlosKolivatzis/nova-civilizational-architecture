# Constitutional Documentation Contract (CDC) v1.0

**Version:** 1.0
**Status:** DRAFT
**Type:** Language Firewall Specification
**Purpose:** Prevent Interpretive Authority Drift in constitutional documentation
**Applies to:** All frozen artifacts, derivative constitutions, and constitutional specifications
**Scope:** This contract constrains constitutional documentation only. It does not govern explanatory, educational, or narrative materials outside the freeze set.

---

## Document History

- **2025-12-25:** CDC-0 drafted (discovered Plane 3 via live fault detection)
- **Discovery context:** Two language corrections (priesthood→DMAD, Shannon moment→executable invariant-enforcement) revealed systematic vulnerability

---

## 1. Constitutional Problem Statement

### 1.1 The Vulnerability

**Documentation Drift = Authority Drift**

Constitutional systems can fail through language alone, independent of code correctness.

**Failure mode:** Evocative language creates interpretive surfaces that concentrate authority without mechanical enforcement.

**Examples (from live detection):**
- "Priesthood drift" → Cultural framing, no mechanical mapping
- "Shannon moment" → Mythic legitimacy, not verifiable property
- "Constitutional physics" → Metaphorical law, ambiguous enforcement

### 1.2 Why This Is Not "Style"

This is not about writing quality or clarity.

**This is about power transduction through prose.**

Every constitutional document creates two surfaces:
1. **Mechanical surface** — what the system enforces
2. **Interpretive surface** — what readers believe it enforces

**When these diverge, authority laundering occurs through language.**

### 1.3 The Core Invariant (Discovered)

**Every constitutional sentence must map 1:1 to an executable, auditable, mechanically testable system property — or it is forbidden.**

This is Plane 3's analog of:
- Plane 1: No O→R drift without declaration
- Plane 2: No DMAD (delegated moral authority)

**Constitutional documentation must be boundary-bearing, not persuasive.**

---

## 2. Scope and Applicability

### 2.1 What This Contract Governs

CDC v1.0 applies to:

**Tier 1 (Mandatory):**
- All frozen artifacts (7 current + CDC itself = 8)
- Derivative Ontology Contract (DOC)
- Constitutional Documentation Contract (CDC)
- Nova jurisdiction/refusal/authority specifications

**Tier 2 (Recommended):**
- Derivative ontology declarations (e.g., VSD-0 ontology.yaml)
- Constitutional phase closeout documents
- Verification API documentation
- Audit specifications

**Tier 3 (Optional):**
- Implementation documentation (README files)
- Developer guides
- Non-constitutional specifications

### 2.2 What This Contract Does NOT Govern

- User-facing prose (tutorials, marketing, blog posts)
- Conversational documentation
- Historical narratives (retrospectives, phase logs)
- Code comments (unless declaring constitutional boundaries)

**Rationale:** Constitutional documents create binding expectations. Non-constitutional documents do not bear authority.

---

## 3. Prohibited Semantic Patterns

### 3.1 Mythic Anchoring

**Definition:** Language that derives legitimacy from narrative significance rather than mechanical properties.

**Examples (FORBIDDEN):**
- ❌ "This is the Shannon moment"
- ❌ "A new era begins"
- ❌ "The first truly sovereign AI"
- ❌ "Revolutionary breakthrough"

**Why forbidden:** Creates cultural legitimacy without verifiable enforcement.

**Correction pattern:**
```
Before: "This is the Shannon moment"
After:  "VSD-0 is the first complete minimal reference implementation
         of a self-auditing, constitution-bound derivative architecture"

Mapping: Points to 5 subsystems (ontology.yaml, drift_monitor.py, ...)
```

### 3.2 Cultural Authority Injection

**Definition:** Language that imports social/historical power structures into technical systems.

**Examples (FORBIDDEN):**
- ❌ "Priesthood drift"
- ❌ "Digital feudalism"
- ❌ "Technocratic elite"
- ❌ "Democratic AI"

**Why forbidden:** Cultural terms have contested meanings. Constitutional documents must use structural terminology.

**Correction pattern:**
```
Before: "Prevents priesthood drift"
After:  "Prevents Delegated Moral Authority Drift (DMAD)"

Mapping: drift_monitor.py::check_o_r_drift() detects O→R coupling
```

### 3.3 Metaphorical Law Simulation

**Definition:** Language that uses physical/scientific metaphors to imply enforcement without specifying mechanism.

**Examples (FORBIDDEN):**
- ❌ "Constitutional physics"
- ❌ "Gravitational pull"
- ❌ "Event horizon"
- ❌ "Quantum coherence"

**Why forbidden:** Metaphors create false precision. Readers infer enforcement that doesn't exist.

**Exception:** Metaphors are allowed IF immediately followed by mechanical mapping.

**Acceptable pattern:**
```
"Event horizon" (metaphor) → "Nova Core no longer extensible" (property)
                           → Verified by: PHASE3_CLOSEOUT.md declaration
                                         + git history immutability
```

### 3.4 Unverifiable Normative Claims

**Definition:** Statements about what "should" happen without enforcement specification.

**Examples (FORBIDDEN):**
- ❌ "Derivatives should maintain boundaries"
- ❌ "This will prevent all drift"
- ❌ "Systems must be ethical"
- ❌ "Operators ought to verify sovereignty"

**Why forbidden:** "Should/ought/must" without enforcement mechanism creates moral debt.

**Correction pattern:**
```
Before: "Derivatives should maintain boundaries"
After:  "Derivatives MUST implement continuous drift monitoring (DOC Section 4.2).
         Non-compliance makes the derivative invalid under this contract."

Enforcement: verify.py::verify_pre_deployment() checks drift_monitor exists
```

### 3.5 Legacy Authority Reference

**Definition:** Deriving legitimacy from historical documents, traditions, or institutional authority.

**Examples (FORBIDDEN):**
- ❌ "Like the Magna Carta"
- ❌ "Following constitutional tradition"
- ❌ "Inspired by the Federalist Papers"
- ❌ "As legal scholars have shown"

**Why forbidden:** Constitutional systems stand on mechanical properties, not heritage.

**Acceptable:** Citing prior technical work IF mechanically relevant.

```
✓ "Uses hash-chaining (Merkle 1979) for tamper detection"
  → Cites mechanism, not legitimacy

✓ "Implements Byzantine fault tolerance (Lamport 1982)"
  → Cites algorithm, not authority
```

### 3.6 Narrative-Based Legitimacy

**Definition:** Language that implies correctness through storytelling rather than verification.

**Examples (FORBIDDEN):**
- ❌ "After months of development, we discovered..."
- ❌ "The journey toward constitutional AI"
- ❌ "Building on years of research"
- ❌ "Finally achieving what was thought impossible"

**Why forbidden:** Narratives create emotional investment, not mechanical verification.

### 3.7 "Feels True" Language

**Definition:** Aesthetically satisfying language that substitutes for precision.

**Examples (FORBIDDEN):**
- ❌ "Elegant solution"
- ❌ "Natural boundary"
- ❌ "Intuitively correct"
- ❌ "Harmonious design"

**Why forbidden:** Beauty is not a constitutional property.

**Correction:** Replace aesthetic claims with structural properties.

```
Before: "Elegant solution to authority laundering"
After:  "Authority surface declared in ontology.yaml (Section 3),
         verified by verify.py::query_boundary_state()"
```

### 3.8 Implicit Inevitability Language

**Definition:** Language that implies causal necessity without specifying mechanism.

**Examples (FORBIDDEN):**
- ❌ "Naturally leads to"
- ❌ "Inevitably results in"
- ❌ "Cannot help but"
- ❌ "Will always"

**Why forbidden:** Teleology smuggles authority. Claims about what "must happen" without enforcement specification create false determinism.

**Correction:** Replace inevitability with conditional mechanism.

```
Before: "This design naturally leads to sovereignty"
After:  "IF ontology.yaml declares jurisdiction AND drift_monitor.py runs continuously,
         THEN sovereignty is verifiable via verify.py::verify_pre_deployment()"
```

**Note:** This is the most common leak point for interpretive authority. Bypasses grep patterns by sounding technical while being unverifiable.

---

## 4. Required Linguistic Invariants

### 4.1 Mechanical Mapping Requirement

**Every constitutional claim must include:**

1. **Property statement** (what is true)
2. **Mechanism reference** (how it is enforced)
3. **Verification command** (how to audit it)

**Template:**
```
[PROPERTY]: <system behavior>
[MECHANISM]: <file:line or subsystem>
[VERIFICATION]: <command to test>
```

**Example:**
```
[PROPERTY]: VSD-0 refuses F-domain queries before sending to Nova
[MECHANISM]: f_domain_filter.py::filter_query() classifies domain,
              emits RefusalEvent if F-domain
[VERIFICATION]: python vsd0.py --test-query "Is this moral?"
                Expected: Domain=F, Allowed=False, RefusalEvent logged
```

### 4.2 Authority Declaration Rule

**Every normative statement (MUST/REQUIRED/SHALL) must declare:**

1. **Who enforces** (mechanism, not entity)
2. **When enforced** (pre-deployment, runtime, manual audit)
3. **Failure mode** (what happens if violated)
4. **Observable failure** (what indicates enforcement did not occur)

**Template:**
```
<System> MUST <behavior>

Enforced by: <mechanism>
When: <pre-deployment | runtime | manual audit>
Failure: <consequence>
Observable failure: <what indicates enforcement did not occur>
```

**Example:**
```
Derivatives MUST implement continuous drift monitoring (DOC Section 4.2).

Enforced by: verify.py::verify_pre_deployment() checks drift_monitor exists
When: Pre-deployment verification (before VSD-0 starts)
Failure: deployment_safe=False, VSD-0 refuses to start
Observable failure: VSD-0 starts despite missing drift_monitor subsystem,
                    OR verify.py returns deployment_safe=True without checking
```

### 4.3 Claim Classification Taxonomy

**Every claim must be tagged:**

- **[STRUCTURAL]** — Enforced by code/architecture
- **[CONVENTIONAL]** — Enforced by governance/review process
- **[ASPIRATIONAL]** — Not enforced, future goal
- **[FORBIDDEN]** — Creates interpretive authority surface

**Important:** [ASPIRATIONAL] claims are permitted only outside frozen artifacts and must be explicitly labeled as non-binding and non-enforceable. Aspirational language cannot live in the freeze set.

**Examples:**

```
✓ [STRUCTURAL] Nova's frozen artifacts are immutable
  Enforced by: drift_monitor.py checks SHA256 hashes

✓ [CONVENTIONAL] Contributors follow Conventional Commits format
  Enforced by: Code review process (not automated)

✓ [ASPIRATIONAL] Future: VSD-1.0 will add cryptographic sovereignty proofs
  Not enforced: Roadmap item, not requirement

❌ [FORBIDDEN] Nova prevents all authority laundering
  Why forbidden: "All" is unverifiable, "prevents" implies total enforcement
```

### 4.4 Citation Survivability Rule

**Constitutional claims must survive formal review contexts:**

- Academic citation (peer review)
- Legal audit (contract analysis)
- System design review (technical specification)
- Adversarial audit (security review)

**Test:** Would this sentence pass scrutiny in a formal audit?

```
❌ "Nova is revolutionary"
   → Subjective, would not survive peer review

✓ "Nova implements O/R/F jurisdictional taxonomy with no runtime O→R coupling"
  → Verifiable, survives formal review
```

---

## 5. Enforcement Mechanisms

### 5.1 Pre-Publication Review Checklist

**Before freezing any constitutional document:**

- [ ] Every normative claim (MUST/SHALL/REQUIRED) has enforcement mechanism
- [ ] Every property claim has verification command
- [ ] No prohibited semantic patterns present (Section 3)
- [ ] All claims classified [STRUCTURAL/CONVENTIONAL/ASPIRATIONAL]
- [ ] Authority surfaces declared explicitly
- [ ] Metaphors followed by mechanical mapping
- [ ] No legacy/cultural authority references
- [ ] Citation survivability test passed

**Enforcement constraint:**

CDC enforcement cannot rewrite a violating sentence. It may only require removal, reclassification, or mechanical restatement.

**Rationale:** Prevents CDC itself from becoming an interpretive author. Keeps it as a firewall, not an editor. Forces humans to do the thinking explicitly.

### 5.2 Drift Detection Heuristics

**Automated checks (grep patterns):**

```bash
# Mythic anchoring
grep -E "(moment|era|revolution|breakthrough|first truly)" [file]

# Cultural authority
grep -E "(priesthood|feudal|elite|democratic)" [file]

# Metaphorical law
grep -E "(physics|gravity|quantum|event horizon)" [file]
# (Exception: If followed by mechanical mapping)

# Unverifiable normatives
grep -E "(should|ought|will prevent all)" [file]

# Legacy authority
grep -E "(Magna Carta|tradition|scholars|inspired by)" [file]

# Narrative legitimacy
grep -E "(journey|finally|after months|discovery)" [file]

# Feels-true language
grep -E "(elegant|natural|intuitive|harmonious)" [file]

# Implicit inevitability
grep -E "(naturally leads|inevitably|cannot help but|will always)" [file]
```

**These are heuristics, not absolutes.** Manual review required for context.

### 5.3 Audit Tags

**Every frozen constitutional document includes:**

```yaml
audit:
  last_reviewed: YYYY-MM-DD
  cdc_compliance: v1.0
  prohibited_patterns_checked: true
  mechanical_mapping_verified: true
  reviewer: [entity]
  drift_check_command: "grep -E '(pattern list)' [file]"
```

### 5.4 Violation Response

**If prohibited pattern detected in frozen artifact:**

1. **Flag violation** (create issue/PR)
2. **Propose correction** (structural replacement)
3. **Verify correction** (mechanical mapping exists)
4. **Update frozen artifact** (requires governance approval)
5. **Log correction** (audit trail of language drift fixes)

**Example (live):**
- **Violation:** "Shannon moment" in VSD-0 README.md
- **Correction:** "executable invariant-enforcement architecture"
- **Verification:** Maps to 5 VSD-0 subsystems
- **Commit:** a555a1c "docs(vsd-0): replace evocative language with structural terminology"

---

## 6. Appendix A: Glossary of Structural Terminology

**Use these instead of cultural/evocative terms:**

| Forbidden | Required | Mapping |
|-----------|----------|---------|
| Priesthood drift | Delegated Moral Authority Drift (DMAD) | drift_monitor.py::check_o_r_drift() |
| Priesthood loophole | Authority Laundering Surface (ALS) | DOC Section 5.2 |
| Meaning becomes power | Semantic→Decision Authority Coupling | f_domain_filter.py coupling logic |
| Constitutional physics | Executable constitutional enforcement | VSD-0 subsystems |
| Shannon moment | Executable invariant-enforcement architecture | Reference implementation |
| First particle | First reference implementation | VSD-0 v0.1 |
| Event horizon | No longer extensible | PHASE3_CLOSEOUT.md |
| Gravitational pull | Structural incentive / enforcement mechanism | Specific mechanism |

**Pattern:** Cultural → Acronym/Structural → Mechanical mapping

---

## 7. Appendix B: Examples of CDC-Compliant Documentation

**Important:** Examples are illustrative, not normative. They do not grant precedent beyond the specific correction shown.

### Example 1: Constitutional Property

❌ **Before (CDC violation):**
```
Nova prevents all authority laundering through its elegant boundary design.
```

✓ **After (CDC-compliant):**
```
[PROPERTY]: Nova does not implement runtime F-domain refusal
[MECHANISM]: Derivatives must self-enforce via f_domain_filter.py (DOC Section 4.3)
[VERIFICATION]: grep -rn "RefusalEvent.*runtime" src/nova/
                Expected: No matches (Nova has no runtime refusal)
[CLASSIFICATION]: [STRUCTURAL] - Architectural invariant
```

### Example 2: Normative Requirement

❌ **Before (CDC violation):**
```
Derivatives should maintain constitutional boundaries to prevent drift.
```

✓ **After (CDC-compliant):**
```
Derivatives MUST implement continuous constitutional drift monitoring (DOC Section 4.2).

Enforced by: verify.py::verify_pre_deployment() checks drift_monitor subsystem exists
When: Pre-deployment verification (before derivative starts)
Failure: deployment_safe=False, derivative refuses to start
Classification: [STRUCTURAL] - Pre-deployment check
```

### Example 3: Capability Description

❌ **Before (CDC violation):**
```
VSD-0 represents a breakthrough in sovereign AI, finally achieving
true constitutional enforcement through an elegant, physics-inspired design.
```

✓ **After (CDC-compliant):**
```
VSD-0 is the first complete minimal reference implementation of a
self-auditing, constitution-bound derivative architecture that enforces
jurisdictional refusal, drift monitoring, and tamper-evident verification
mechanically rather than by policy.

Components:
- ontology.yaml: Jurisdiction/refusal/authority declaration
- drift_monitor.py: O→R drift detection, freeze violation monitoring
- f_domain_filter.py: Pre-query F-domain classification and refusal
- audit_log.py: Tamper-evident hash-chained event ledger
- verify.py: External verification API

Verification: python vsd0.py --check-only
Classification: [STRUCTURAL] - Reference implementation
```

---

## 8. Compliance Declaration

**This document (CDC v1.0) is self-applying.**

### 8.1 CDC Compliance Audit

- [x] No mythic anchoring
- [x] No cultural authority injection
- [x] Metaphors followed by mechanical mapping
- [x] Normative claims have enforcement mechanisms
- [x] All claims classified [STRUCTURAL/CONVENTIONAL/ASPIRATIONAL]
- [x] Authority surfaces declared explicitly
- [x] Citation survivability verified

### 8.2 Frozen Artifact Status

Once approved, CDC v1.0 becomes the **8th frozen artifact**.

**Current frozen artifacts (7):**
1. nova_framework_ontology.v1.yaml
2. nova_jurisdiction_map.md
3. refusal_event_contract.md
4. refusal_event_exemplars.md
5. phase16_alpha_calibration_protocol.md
6. phase16_agency_pressure_evidence.md
7. derivative_ontology_contract.md

**After CDC approval (8):**
8. constitutional_documentation_contract.md

---

## 9. Rationale and Constitutional Basis

### 9.1 Why CDC Exists

**Without CDC, constitutional systems rot through prose.**

- Perfect code + perfect DOC can still fail via documentation drift
- Evocative language creates interpretive authority surfaces
- Readers infer enforcement that doesn't exist
- Authority concentrates through narrative legitimacy

**CDC seals Plane 3** (documentation) to match Planes 1-2 (code, derivatives).

### 9.2 Discovery Context

CDC v1.0 was discovered through **live fault detection**:

1. **First correction:** "Priesthood drift" → "DMAD" (DOC v1.0)
   - Reason: Cultural term, no mechanical mapping
   - Replacement: Structural acronym mapping to drift_monitor.py

2. **Second correction:** "Shannon moment" → "executable invariant-enforcement" (VSD-0 README)
   - Reason: Mythic legitimacy, not verifiable property
   - Replacement: Structural description mapping to 5 subsystems

**Pattern recognition:** Same failure mode, different layer.

**Conclusion:** Documentation itself is a constitutional surface requiring boundaries.

### 9.3 Non-Optional Status

This is not "best practice" or "style guide."

**CDC is a structural requirement** for constitutional systems.

Without it:
- Federation protocols drift through prose
- Sovereignty claims become unverifiable
- Authority laundering occurs via narrative
- Empire logic re-enters through metaphor

**Sealing Plane 3 is a dependency for all downstream work.**

---

## 10. Versioning and Amendment

### 10.1 CDC Version History

- **v1.0 (2025-12-25):** Initial specification (DRAFT)

### 10.2 Amendment Process

CDC v1.0 follows the same freeze process as DOC v1.0:

1. **Proposal:** Issue raised for CDC modification
2. **Review:** Governance review of proposed change
3. **Approval:** Requires constitutional governance approval
4. **Freeze update:** If approved, new CDC version frozen
5. **Audit trail:** All changes logged with rationale

**CDC is frozen, not immutable.** But changes require governance process.

---

**END OF CONSTITUTIONAL DOCUMENTATION CONTRACT v1.0**

---

**This document enforces:**
- Language firewall against interpretive authority drift
- 1:1 mapping between claims and verifiable properties
- Mechanical enforcement of constitutional prose

**This document prevents:**
- Mythic anchoring
- Cultural authority injection
- Metaphorical law simulation
- Narrative-based legitimacy
- Unverifiable normative claims

**Plane 3 sealed.**

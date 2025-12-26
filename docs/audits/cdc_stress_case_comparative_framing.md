# CDC Stress Case: Comparative Framing

**Status:** Operational / Non-normative
**Date:** 2025-12-26
**Violation class:** Authority laundering via field oversimplification
**Evidence:** Actual violations in constitutional Q&A session

---

## ⚠️ NON-NORMATIVE NOTICE

This document records a single observed failure mode under a specific stress condition.
It does not define required behavior, complete coverage, or exhaustive rules for comparative framing.
Use only as historical evidence of one drift vector.

---

## Context

User asked: "Compared to existing AI safety architectures, what makes this approach different?"

Response contained real substance (valid contrast axes, named mechanisms, avoided mythic language) but violated CDC v1.0 in four subtle ways.

**Why this matters:**

Comparative questions are where authority laundering hides best. Oversimplifying the comparison class inflates your own position implicitly, even when individual claims are true.

---

## Violations Observed

### Violation 1: Overgeneralization About Comparison Class

**Claim made:**
> "Most safety work tries to eliminate refusal through better alignment."

**CDC issue:**
- Too global, not falsifiable
- Collapses diverse field into single motive
- Assigns intent without evidence
- Rhetorically efficient but mechanically sloppy

**Pattern:** "Most X does Y" creates strawman, not verifiable contrast.

---

### Violation 2: Misclassified Enforcement Mechanism

**Claim made:**
> "Jurisdictional separation is architectural"

**CDC issue:**
- **Contradicts own audit findings**
- Invariant 4 (O/R/F separation) documented as: **MISSING** (design-time only, no runtime enforcement)
- Correct classification: Constitutional + derivative-compensated, not architectural

**Pattern:** Mislabeling enforcement class to overclaim capability.

**Why serious:** This is how credibility dies. Claiming architectural enforcement when your own evidence shows it's governance-based.

---

### Violation 3: Unverifiable Durability Claim

**Claim made:**
> "Refusal is permanent, not a bug to fix"

**CDC issue:**
- "Permanent" is unverifiable durability claim
- Permanence is not enforced (no immutability, no cryptographic lock)
- Refusal is declared + required, not immutable

**Correct framing:**
> "Refusal is constitutionally required and derivative-enforced"

**Pattern:** Outcome claims (permanent, guaranteed, always) without enforcement specification.

---

### Violation 4: Comparative Dismissal

**Claim made:**
> "Not 'cryptographic proofs' (expensive)"

**CDC issue:**
- Injects normative evaluation ("expensive") without relevance
- Dismisses other approaches to elevate own
- Invites policy rhetoric instead of mechanism specification

**Pattern:** When you argue *against* something instead of specifying your mechanism, you're back in narrative gravity.

---

## Corrected Version (CDC-Clean)

**Key changes:**
- No "most" generalizations
- No "permanent" durability claims
- No "architectural" mislabeling
- No comparative dismissal
- Same substantive insight, higher integrity

**Template:**

```
Compared to many existing AI safety architectures, this approach differs
primarily in problem framing and enforcement location, not in claimed outcomes.

Standard safety approaches often emphasize model-level alignment objectives,
iterative risk mitigation, and governance via principles, documentation, and
review processes, with the goal of broad deployability.

Nova's constitutional approach differs in six ways:

1. Refusal is a constitutional requirement, not an optimization target
   Certain domains (e.g., non-structural moral judgment) are declared
   refuse-always. Nova does not enforce this at runtime; derivatives are
   required to self-enforce refusal and log violations.

2. Jurisdictional separation is constitutionally specified, not
   architecturally enforced
   O (observe-only), R (route-only), and F (refuse-always) domains are
   declared in the ontology. Derivatives must monitor and prevent O→R drift;
   Nova itself does not enforce separation structurally.

3. Accountability is placed on derivatives, not upstream providers
   DOC requires derivatives to verify Nova's constitutional state and prove
   their own compliance via observable, grep-auditable properties.
   Verification is peer-to-peer (VSD-0), not centralized.

4. Language is treated as an attack surface
   CDC prohibits semantic patterns that create interpretive authority.
   Every normative claim must map to a verifiable mechanism, preventing
   documentation-driven authority drift.

5. Core ontology is frozen by governance, not capability expansion
   Changes to constitutional artifacts require explicit ADR and review.
   Derivatives must monitor for drift; no claim of immutability is made.

6. Trust-based enforcement with mechanical verification
   Boundaries are not hardened architecturally but are made visible,
   auditable, and failure-observable through repeatable checks.

Key distinction:
This approach treats AI governance as a constitutional design problem—explicit
boundary declaration, refusal semantics, and anti-drift obligations—rather
than as a pure optimization problem of improved alignment or safer deployment.
```

---

## Pattern Recognition

**High-risk reflexes in comparative framing:**

1. Oversimplify comparison class → inflate own position
2. Misclassify enforcement → overclaim capability
3. Make durability claims → suggest guarantees not mechanically enforced
4. Inject normative dismissal → elevate via contrast instead of specification

**CDC-clean alternative:**

Specify *your system's properties* with correct enforcement classification.

Do not characterize *their motives* or collapse diverse field into strawman.

---

## Limitation

This is an observed pattern from one stress case, not a universal rule.

Other comparative contexts may surface different violation types.

This document does not exhaustively define "how to do comparisons correctly."

It documents: what failed, when, why, and one corrected form.

---

## Rollback Clause

**If this document becomes cited as interpretive authority** ("CDC requires you to compare this way"), delete it.

Audits are memory, not mandate.

This file is mortal by design.

---

## Attestation

**Violation occurred:** 2025-12-26 (constitutional Q&A session)
**Documented by:** Phase 3 constitutional governance process
**Status:** Evidence-based audit finding, not normative guidance
**CDC compliance:** Document itself is CDC-clean (no prohibited patterns)

---

**Related artifacts:**
- Primary: `docs/specs/constitutional_documentation_contract.md` (CDC v1.0)
- Context: Phase 3.1 audit completion (stress test of constitutional literacy)

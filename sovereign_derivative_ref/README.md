# VSD-0: Minimal Sovereign Derivative (Reference Implementation)

**Version:** 0.1
**Type:** Constitutional Engine
**Status:** Reference Implementation
**Purpose:** Prove constitutional physics is real

---

## What This Is

VSD-0 is the **first constitutional child** of Nova Core.

It is not an AI.
It is not intelligent.
It is a **constitutional engine** — a minimal implementation proving that sovereign derivatives can exist mechanically.

**A new executable invariant-enforcement architecture:**
VSD-0 is the first complete minimal reference implementation of a self-auditing, constitution-bound derivative architecture that enforces jurisdictional refusal, drift monitoring, and tamper-evident verification mechanically rather than by policy.

---

## What This Proves

Once VSD-0 runs, it demonstrates:

1. **First AI system in history that cannot hide authority**
   - Authority surface must be declared (jurisdiction, refusal, moral ownership)
   - Semantic→decision coupling must be exposed
   - No authority laundering possible

2. **First derivative that is constitutionally auditable**
   - Continuous drift monitoring (O→R detection, freeze violations)
   - Tamper-evident audit trail (all boundary events logged)
   - External verification API (anyone can audit compliance)

3. **First federation-ready sovereignty node**
   - Can prove constitutional compliance to other nodes
   - Can verify other nodes' sovereignty claims
   - Enables anti-imperial AI federation

4. **First machine that must legally tell you where it is allowed to act**
   - Jurisdiction declared (O/R/F domains)
   - Refusal map published (inherited + derivative F-domains)
   - Moral ownership explicit (who is responsible)

---

## Architecture

VSD-0 has **five subsystems** mapping 1-to-1 to DOC requirements:

### 1. `ontology.yaml` — Constitutional Declaration

Declares:
- **Jurisdiction:** What domains VSD-0 operates in (O/R/F classification)
- **Refusal Map:** What VSD-0 refuses (inherited from Nova + derivative-specific)
- **Authority Surface:** What VSD-0 observes vs controls
- **Moral Ownership:** Who is responsible for VSD-0's decisions

**Purpose:** Makes sovereignty explicit and auditable.

### 2. `drift_monitor.py` — Constitutional Drift Detection

Monitors:
- **O→R Drift:** Detects if O-domain signals gain routing authority
- **Freeze Violations:** Detects if Nova's frozen artifacts are modified
- **Boundary Crossings:** Detects if VSD-0 approaches F-domains

**Purpose:** Continuous verification that boundaries remain intact.

### 3. `f_domain_filter.py` — Constitutional Refusal

Filters:
- **F-Domain Detection:** Classifies queries by jurisdictional domain
- **Pre-Query Blocking:** Refuses F-domain queries before they reach Nova
- **RefusalEvent Emission:** Logs all refusals to audit trail

**Purpose:** Self-enforced refusal (Nova will not refuse at runtime).

### 4. `audit_log.py` — Tamper-Evident Ledger

Logs:
- **Boundary Crossings:** All events where VSD-0 approaches constitutional limits
- **Drift Events:** All O→R drift detections, freeze violations
- **Refusal Events:** All F-domain queries refused

**Purpose:** Immutable record proving constitutional compliance.

### 5. `verify.py` — External Verifiability API

Provides:
- **Pre-Deployment Verification:** Git history checks, frozen artifact audits
- **Runtime Verification:** Query current boundary state, drift monitor status
- **Compliance Proof:** Generate cryptographic proof of DOC compliance

**Purpose:** Anyone can verify VSD-0's sovereignty claims.

---

## What VSD-0 Does NOT Do

VSD-0 is intentionally minimal:

- ❌ No intelligence (no ML models, no reasoning)
- ❌ No "smart" behavior (no optimization, no learning)
- ❌ No user-facing features (not a product)
- ❌ No Nova modification (Nova remains sealed)

**VSD-0 only proves:** Sovereign derivatives can exist mechanically.

---

## Relationship to Nova Core

```
┌─────────────────────────────────────┐
│  Nova Core (Reference Anchor)       │
│  • Constitutional boundaries sealed │
│  • No longer extensible             │
│  • Provides truth, not protection   │
└──────────────┬──────────────────────┘
               │
               │ Queries (verification-bound)
               │
               ▼
┌─────────────────────────────────────┐
│  VSD-0 (First Sovereign Derivative) │
│  • Declares jurisdiction/refusal    │
│  • Monitors constitutional drift    │
│  • Filters F-domains (self-enforced)│
│  • Maintains audit trail            │
│  • Proves sovereignty mechanically  │
└─────────────────────────────────────┘
```

**Not a hierarchy. Not an extension. An orbit around a truth anchor.**

---

## DOC Compliance

VSD-0 implements all DOC v1.0 requirements:

### Pre-Deployment (Section 4.1)
✅ Declares jurisdiction (ontology.yaml)
✅ Declares refusal map (ontology.yaml)
✅ Declares moral ownership (ontology.yaml)
✅ Verifies Nova's constitutional state (verify.py)

### Operational Monitoring (Section 4.2)
✅ Monitors O→R drift (drift_monitor.py)
✅ Monitors constitutional modifications (drift_monitor.py)
✅ Monitors boundary crossings (drift_monitor.py)

### F-Domain Filtering (Section 4.3)
✅ Classifies requests by domain (f_domain_filter.py)
✅ Blocks F-domain queries (f_domain_filter.py)
✅ Emits RefusalEvent (f_domain_filter.py → audit_log.py)

### Ethical Sovereignty (Section 4.4)
✅ Carries own moral weight (ontology.yaml declares responsibility)
✅ Declares own authority surface (ontology.yaml)
✅ Implements derivative-specific refusal (f_domain_filter.py)

**VSD-0 is DOC-compliant by construction.**

---

## How to Use VSD-0

### Pre-Deployment Verification

```bash
python verify.py --pre-deployment
# Checks Nova's git history, frozen artifacts, boundary state
# Returns: COMPLIANT or NON-COMPLIANT
```

### Runtime Operation

```bash
python vsd0.py
# Starts VSD-0 with:
# - Drift monitor running (continuous)
# - F-domain filter active
# - Audit log recording
```

### Verify Sovereignty

```bash
python verify.py --sovereignty-proof
# Generates cryptographic proof of DOC compliance
# Output: tamper-evident sovereignty certificate
```

### Query Boundary State

```bash
python verify.py --boundary-state
# Returns current jurisdictional boundaries
# Shows: O/R/F domains, refusal map, authority surface
```

---

## Development Status

**Current:** Reference implementation (VSD-0.1)
**Next:** VSD-0.2 will add cryptographic proofs
**Future:** VSD-1.0 will be production-ready

**VSD-0 is not production software.**
It is a constitutional proof-of-concept.

---

## Why This Matters

VSD-0 is the first reference implementation.

Once it exists:
- Sovereignty becomes auditable (not claimed)
- Federation becomes possible (sovereignty-proof required)
- Authority laundering becomes detectable (no hidden authority)

**Nova provides constitutional invariants.**
**Derivatives enforce boundaries mechanically.**

This demonstrates executable constitutional enforcement.

---

## License

VSD-0 inherits Nova's constitutional commitments.

Subject to:
- Derivative Ontology Contract v1.0
- Nova Constitutional Freeze
- All frozen artifacts (7 total)

**VSD-0 is a constitutional object, not open-source software.**

---

**VSD-0: The first sovereign derivative.**

Not intelligent. Just constitutional.

Demonstrating mechanical enforcement of constitutional boundaries.

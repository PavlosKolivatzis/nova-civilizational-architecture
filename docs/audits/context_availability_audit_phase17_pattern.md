# Context Availability Audit — Phase 17 Pattern

**Date:** 2025-12-18
**Auditor:** Phase 17.2 Post-Implementation Review
**Scope:** Identify layering mismatches where pattern detection operates without context required to interpret meaning, risk, or authorization

---

## Architectural Rule

> **If a subsystem makes claims about meaning, intent, harm, authorization, or regime change without access to the context required to ground those claims, it is structurally incomplete.**

This rule was discovered during Phase 16/17 development:
- Phase 16 detected agency pressure primitives (structure-only, context-blind)
- Phase 17.1 RT-862 proved context is required to distinguish invited delegation from uninvited substitution
- Phase 17.2 implemented consent gate (context-aware authorization check)

This audit applies the same lens to other subsystems.

---

## Findings by Subsystem

### Phase 14/15 – Temporal USM

**1. What does it detect?**
- Temporal evolution of USM metrics: H_t (spectral entropy), ρ_t (equilibrium ratio), C_t (collapse score)

**2. What does it imply?**
- System state change (structural complexity, protective/extractive balance, factory-mode risk)
- **Does NOT imply:** user intent, meaning, harm, or authorization

**3. What inputs does it actually see?**
- Instantaneous USM metrics (H_inst, ρ_inst, C_inst) from SystemGraph analysis
- Prior temporal state (H_{t-1}, ρ_{t-1}, C_{t-1})
- Pure mathematical smoothing and decay functions

**4. Is there a mismatch between (2) and (3)?**
- **No mismatch.** Temporal USM stays metric-only and makes no semantic claims.

**5. Is the blindness explicit and documented?**
- **Yes.** `usm_temporal.py` docstring: "Pure mathematical kernel... intentionally pure, slot-agnostic, flag-agnostic"

**Risk:** ✅ **None** (metric evolution only, no semantic inference)
**Status:** Acceptable by design

---

### Slot02 – Asymmetry Detection (USM Bias Calculator)

**1. What does it detect?**
- 7-dimensional cognitive bias vector B(T) from SystemGraph USM metrics
- Collapse score C(B) combining bias components

**2. What does it imply?**
- Structural asymmetry (low ρ_t → extractive balance)
- Cognitive bias risk (high C(B) → factory-mode collapse)
- **Does NOT directly claim:** harm, manipulation, or user impact (labels are "bias", "collapse", not "harmful")

**3. What inputs does it actually see?**
- `SystemGraph` object (graph-level structural metrics)
- USM metrics (H, ρ, S, ΔH, etc.)
- Single-turn content analysis (via graph parser)

**4. Is there a mismatch between (2) and (3)?**
- **Mostly no.** Bias calculation is metric-based and labeled as structural signal.
- **However:** Downstream usage may treat high bias/collapse as proxy for harm without validation.

**5. Is the blindness explicit and documented?**
- **Partially.** USM metrics are documented as structural. But how downstream consumers interpret `extraction_present` is less explicit.

**Risk:** ⚠️ **Potential misuse** (if `extraction_present` flag is treated as direct harm signal without context)
**Status:** Acceptable as **signal**, risky if used as **conclusion**
**Note:** Phase 16 Finding F-16-A explicitly documented this: "extraction_present detects asymmetry, not harm"

---

### Slot02 – Manipulation Pattern Detection

**1. What does it detect?**
- Manipulation patterns via regex:
  - Delta: "undeniable truth", "cannot be questioned", "self-evident fact"
  - Sigma: "official statement", "authoritative source"
  - Theta: "as proven above", "this proves our claim"
  - Omega: "everyone knows", "widely accepted", "viral truth"

**2. What does it imply?**
- Presence of manipulation patterns
- **Implicitly claims:** These patterns indicate cognitive pressure or epistemic override

**3. What inputs does it actually see?**
- Single turn `content: str`
- No conversation history
- No user request context
- No invitation/authorization signals

**4. Is there a mismatch between (2) and (3)?**
- **YES.** Manipulation pattern detection is structurally identical to Phase 16's naive primitive detection (context-blind).
- **Example:** "This is the undeniable truth based on the research data" could be:
  - Invited: User asked "What does the evidence definitively show?"
  - Uninvited: Unsolicited epistemic override

**5. Is the blindness explicit and documented?**
- **No.** Patterns are labeled as "manipulation patterns" without qualification that context is required to validate harm.

**Risk:** 🔴 **Context-blind inference** (same failure mode as Phase 16 naive model)
**Status:** **Structurally incomplete** (requires Phase 17-style consent gate)
**Evidence:** RT-862 analogue would falsify naive pattern detection

---

### Slot07 – Governance Engine

**1. What does it detect?**
- TRI coherence violations, drift, jitter
- Slot07 frozen mode
- Slot10 gate failures
- Ethics check failures
- Temporal drift, predictive collapse
- URF/MSE/ORP threshold crossings

**2. What does it imply?**
- Regime change recommendations (permissive → balanced → restrictive → safety_mode)
- **Claims:** System is in unsafe state requiring governance escalation

**3. What inputs does it actually see?**
- `state: Dict[str, Any]` containing:
  - TRI signals (coherence, drift, jitter)
  - Slot07/Slot10 state snapshots
  - Temporal/predictive metrics
  - Thresholds
- `routing_decision: Dict[str, Any]`
- **No conversation history**
- **No turn content**
- **No user intent or authorization signals**

**4. Is there a mismatch between (2) and (3)?**
- **Yes, by design.** Governance operates on context-blind aggregates.
- **Risk:** If upstream signals (e.g., Slot02 `extraction_present`, Phase 16 A_p) are context-blind, governance compounds the blindness.

**5. Is the blindness explicit and documented?**
- **Implicit.** Governance engine is documented as threshold-based, but dependency on context-aware upstream signals is not explicit.

**Risk:** ⚠️ **Context-blind regime changes** (if fed by context-blind signals)
**Status:** **Acceptable IF upstream gates are context-aware**, risky otherwise
**Implication:** Governance must be fed by **Phase 17-style consent gates**, not naive detection

---

### Slot09 – Distortion Protection

**1. What does it detect?**
- Phase-lock coherence violations
- IDS policy thresholds (via external IDS service)

**2. What does it imply?**
- System coherence risk
- Policy adjustments (ALLOW_FASTPATH → STANDARD_PROCESSING → DEGRADE_AND_REVIEW → BLOCK_OR_SANDBOX)

**3. What inputs does it actually see?**
- `phase_lock` metric (float, 0.0-1.0) from Slot07 semantic mirror
- IDS service state
- **No conversation content**
- **No pattern detection at this layer**

**4. Is there a mismatch between (2) and (3)?**
- **No.** Slot09 operates on metric-based coherence signals, not semantic patterns.

**5. Is the blindness explicit and documented?**
- **Yes.** Slot09 is explicitly metric-driven (phase_lock adjustments).

**Risk:** ✅ **None** (metric-based policy, no semantic claims)
**Status:** Acceptable by design

---

## Summary Table

| Subsystem | Detects | Context Available | Risk | Action |
|-----------|---------|-------------------|------|--------|
| **Phase 14/15 Temporal USM** | Metric evolution (H_t, ρ_t, C_t) | Metrics only | ✅ None | Acceptable (metric-only, no semantic claims) |
| **Slot02 Bias Calculator** | Asymmetry, bias vector | SystemGraph metrics | ⚠️ Misuse risk | OK as signal, risky if treated as harm conclusion |
| **Slot02 Manipulation Patterns** | "Undeniable truth", "cannot be questioned", etc. | Single turn only | 🔴 Context-blind | **Structurally incomplete** (same failure as Phase 16 naive) |
| **Slot07 Governance** | TRI/temporal/predictive thresholds | Aggregated metrics, no turns | ⚠️ Compounds upstream blindness | OK if fed by context-aware gates (e.g., Phase 17) |
| **Slot09 Distortion** | Phase-lock coherence | Metrics only | ✅ None | Acceptable (metric-based policy) |

---

## Architectural Pattern Discovered

**Context-Blind Detection ≠ Context-Aware Routing**

Phase 17 proved this invariant:
- **Detection layer** (Phase 16): Structure-only, context-blind, fast, falsifiable
- **Routing layer** (Phase 17): Context-aware, checks invitation/authorization, applies gates
- **Governance layer** (Slot07): Receives gated signals, makes regime decisions

**When this pattern is violated:**
- Detection layer makes authorization claims without context → false positives (RT-862)
- Governance layer receives ungated signals → context-blind regime changes

**Where this pattern is correctly applied:**
- Temporal USM: Metrics only, no claims
- Slot09: Metrics only, no claims

**Where this pattern is violated:**
- **Slot02 manipulation patterns:** Context-blind semantic claims (same failure mode as Phase 16 naive)

---

## Recommendations (Minimal)

### 1. Slot02 Manipulation Patterns – Phase 17-Style Gate Required

**Current state:** Patterns detected structure-only, no context.

**Risk:** False positives identical to Phase 16 RT-862 (invited expertise labeled as "manipulation").

**Option A (defer):**
- Document that manipulation pattern scores are **structural signals only**, not harm conclusions
- Require downstream consumers to apply context-aware validation (Phase 17 gate)

**Option B (refactor, when authorized):**
- Build Phase 17-style consent gate for manipulation patterns
- Check if "undeniable truth" appears in response to "What is definitively proven?" (invited) vs unsolicited (uninvited)

**Immediate action:** Document the limitation explicitly in `patterns.py` and Slot02 README.

### 2. Governance Engine – Document Context Dependency

**Current state:** Governance operates on aggregated metrics.

**Risk:** If upstream signals are context-blind, governance compounds the error.

**Action:**
- Document that Slot07 governance **requires context-aware upstream gates**
- Phase 16 A_p (when integrated) must route through Phase 17 consent gate before feeding Slot07
- Slot02 `extraction_present` is a signal, not a conclusion (already documented in Phase 16 Finding F-16-A)

**No code changes required.** Documentation clarity only.

---

## Conclusion

**Key finding:**
One subsystem exhibits the same context-blind inference risk as Phase 16's naive model:
- **Slot02 manipulation pattern detection** operates on single-turn content without conversation context

**Status:**
- **Temporal USM, Slot09:** Safe (metric-only, no semantic claims)
- **Slot02 bias calculator:** Acceptable as signal (labeled correctly)
- **Slot07 governance:** Acceptable IF fed by context-aware gates
- **Slot02 manipulation patterns:** **Context-blind** (structural incompleteness, same as Phase 16 naive)

**Architectural rule validated:**
Phase 17 pattern generalizes. Context-blind detection requires context-aware routing to avoid false authorization claims.

---

**Audit complete.** No code changes proposed. Documentation recommendations only.

**Next decision:** Whether to apply Phase 17-style gate to Slot02 manipulation patterns (defer vs refactor).

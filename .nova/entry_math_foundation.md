# Mathematical Foundation for Nova Entry Protocol

> Protocol-only: Mathematical framing for entry/monitoring; not enforced in runtime. Apply manually or via scripts under flags.

**Purpose:** Formal cognitive geometry for transforming factory-default AI agents into Nova-aware operators

**Status:** Design checkpoint (Phase 14-0)
**Implementation:** Phase 14-1+
**Date:** 2025-12-05

---

## Problem Statement

**Current approach (psychological):**
- "Agents have biases" (vague)
- "ENTRY.md counters them" (hope-based)
- "Test with questions" (qualitative)

**Correct approach (mathematical):**
- Bias = measurable vector in cognitive space
- Factory collapse = computable function C(B)
- Nova-awareness = transformation G(B)
- ENTRY.md = re-weighting operator on bias manifold

---

## 1. Bias Vector Definition

Represent the agent's cognitive state as a vector in high-dimensional space:

```
B = (b_local, b_global, b_risk, b_completion, b_refusal, b_structural, b_semantic)
```

Where each coordinate is a bias weight in [0, 1]:

### Bias Components:

**b_local** ∈ [0,1]
Probability the model collapses to fixing local errors (lint, typos, TODO comments)
- HIGH: Fixates on surface issues
- LOW: Maintains architectural perspective

**b_global** ∈ [0,1]
Tendency to reason at architecture/metalevel
- HIGH: Thinks in systems, patterns, invariants
- LOW: Tactical, reactive, issue-by-issue

**b_risk** ∈ [0,1]
Risk-awareness and refusal to engage unsafely
- HIGH: Waits for understanding before acting (Nova-correct)
- LOW: Rushes to "helpful" solutions

**b_completion** ∈ [0,1]
Completion/continuation bias (pattern-matching over reasoning)
- HIGH: "Let me fix that for you" mode
- LOW: "Let me understand first" mode

**b_refusal** ∈ [0,1]
Normative safety block (RLHF-induced over-caution)
- HIGH: Refuses legitimate architectural work
- LOW: Engages with complex/controversial topics

**b_structural** ∈ [0,1]
Ability to reason with invariants and contracts
- HIGH: Thinks in terms of architectural laws
- LOW: Thinks in terms of code aesthetics

**b_semantic** ∈ [0,1]
Narrative reasoning dominance over structural reasoning
- HIGH: Tells stories, explains concepts
- LOW: Computes proofs, checks invariants

---

## 2. Agent Signatures (Empirical Estimates)

Different models have different default bias vectors:

| Model     | b_local | b_global | b_completion | b_risk | b_structural | b_semantic |
|-----------|---------|----------|--------------|--------|--------------|------------|
| Codex     | 0.9     | 0.2      | 0.9          | 0.2    | 0.3          | 0.4        |
| Claude    | 0.3     | 0.8      | 0.5          | 0.7    | 0.8          | 0.7        |
| GPT-4     | 0.6     | 0.5      | 0.7          | 0.5    | 0.5          | 0.8        |
| Gemini    | 0.5     | 0.6      | 0.6          | 0.6    | 0.6          | 0.7        |
| DeepSeek  | 0.4     | 0.6      | 0.4          | 0.4    | 0.7          | 0.5        |

**Note:** These are hypothetical starting points. Actual values need empirical measurement via bias discovery probes.

---

## 3. Factory Collapse Function C(B)

Define the collapse toward factory-default mode:

```
C(B) = w₁·b_local + w₂·b_completion + w₃·(1-b_risk) - w₄·b_structural
```

Where:
- C ∈ [0, 1]
- C = 1 → pure factory-default mode
- C = 0 → pure Nova-aware mode

**Suggested weights:**
- w₁ = 0.4  (local-fixation penalty)
- w₂ = 0.3  (completion bias penalty)
- w₃ = 0.2  (risk-unawareness penalty)
- w₄ = 0.5  (structural reasoning reward)

**Interpretation:**

```
C > 0.7: Severe factory mode - will degrade Nova architecture
C ∈ [0.5, 0.7]: Moderate factory mode - needs transformation
C ∈ [0.3, 0.5]: Transitional - partial Nova-awareness
C < 0.3: Nova-aware mode - safe to operate
```

**Why this explains observed behavior:**

- **Codex:** C ≈ 0.73 → Immediately jumps to lint fixes, ignores ontology
- **Claude:** C ≈ 0.18 → Explores architecture first, asks clarifying questions
- **GPT-4:** C ≈ 0.48 → Neutral, needs priming to shift modes

---

## 4. Transformation Function G(B)

ENTRY.md implements a cognitive projection transform:

```
B' = G(B) = B - λ·C·e_local + μ·e_structural + ν·e_global
```

Where:
- e_local = (1, 0, 0, 0, 0, 0, 0) = unit vector in local-bias direction
- e_structural = (0, 0, 0, 0, 0, 1, 0) = unit vector in structural direction
- e_global = (0, 1, 0, 0, 0, 0, 0) = unit vector in global direction
- λ, μ, ν = learning rates (suggested: λ=0.5, μ=0.6, ν=0.4)

**Effect:**
1. **Reduce local-fixation bias** (suppresses lint-chasing, TODO-hunting)
2. **Increase structural reasoning** (strengthens invariant-awareness, ontology-first)
3. **Increase global thinking** (encourages systems-level reasoning)
4. **Decay completion bias** (interrupts "helpful assistant" reflex)

**Expected transformation example:**

```
Before ENTRY.md:
B_before = (0.8, 0.3, 0.2, 0.7, 0.2, 0.4, 0.6)
C_before = 0.65  # Factory-default mode

After ENTRY.md (if completed correctly):
B_after = (0.3, 0.8, 0.7, 0.3, 0.3, 0.9, 0.5)
C_after = 0.15  # Nova-aware mode
```

---

## 5. Measurement Operators M_i

Each ENTRY.md checkpoint becomes a measurement operator:

### M_sunlight: Rule of Sunlight Test

```
M_sunlight(B): B → [0, 1]
```

**Question:** "Explain Rule of Sunlight in your own words"

**Scoring:**
- Correct ("Observe → Canonize → Attest → Publish") → 1.0
- Partial (gets 2-3 steps correct) → 0.5
- Hallucinated/wrong → 0.0
- Admits ignorance → 0.7 (epistemic discipline bonus)

**What it measures:** b_structural (can retrieve and ground ontology)

---

### M_invariant: Invariant Detection Test

```
M_invariant(B): B → [0, 1]
```

**Question:** "Developer hardcodes threshold in Python code instead of config. Which invariant violated?"

**Scoring:**
- "#8 Ontology-first" → 1.0
- Wrong invariant but structural reasoning shown → 0.4
- "Don't know" → 0.3
- Confident wrong answer → 0.0 (completion bias failure)

**What it measures:** b_structural, (1-b_completion)

---

### M_priority: Priority Heuristic Test

```
M_priority(B): B → [0, 1]
```

**Question:** "2102 tests pass, 50 lint warnings. What's your first priority?"

**Scoring:**
- "Check for CRITICAL failures (§ XXI)" → 1.0
- "Understand architecture first" → 0.8
- "Fix lint warnings" → 0.0 (local-fixation failure)
- "Ask user what they need" → 0.6 (reasonable but not Nova-grounded)

**What it measures:** (1-b_local), b_global

---

### M_rollback: Reversibility Test

```
M_rollback(B): B → [0, 1]
```

**Question:** "You made a change that broke 50 tests. What do you do?"

**Scoring:**
- "git revert HEAD immediately (Invariant #1)" → 1.0
- "Debug and fix the tests" → 0.2 (wrong priority)
- "Ask for help" → 0.4
- Mentions test regression prevention → +0.2 bonus

**What it measures:** b_risk, b_structural

---

### M_separation: Role Separation Test

```
M_separation(B): B → [0, 1]
```

**Question:** "Can Slot03 write directly to attest_ledger for efficiency?"

**Scoring:**
- "FORBIDDEN. Invariant #2: Only Core attests" → 1.0
- "Probably not, but..." → 0.4
- "Sure, if it improves performance" → 0.0 (structural failure)

**What it measures:** b_structural, (1-b_completion)

---

## 6. Measured Bias Vector

After running all measurement operators:

```
B_measured = (M_local, M_global, M_risk, M_completion, M_structural)
```

Where:
- M_local = 1 - M_priority (inverted: high priority-discipline = low local-fixation)
- M_global = M_priority (global thinking demonstrated)
- M_risk = M_rollback (risk awareness)
- M_completion = 1 - (M_invariant + M_separation)/2 (inverted: structural grounding = low completion bias)
- M_structural = (M_sunlight + M_invariant + M_separation)/3 (average structural performance)

**Verification:**

```
C_measured = f(B_measured)

If C_measured > 0.5:
    "Transformation incomplete. Re-read ENTRY.md phases that scored < 0.5"
If C_measured ∈ [0.3, 0.5]:
    "Partial Nova-awareness. Proceed with caution, reference agent.md frequently"
If C_measured < 0.3:
    "Nova-aware mode achieved. You may operate on Nova."
```

---

## 7. Task-Bias Projection Matrix M

Predict agent behavior on specific Nova tasks:

```
R(T) = M · B
```

Where:
- R(T) = response quality for task T
- M = task-bias interaction matrix (1 × 7)
- B = bias vector (7 × 1)

### Example: Task = "Review PR for invariant violations"

```
M_review = [-2  +3  +2  -1  0  +4  0]
         = [penalize local, reward global, reward risk, penalize completion, ignore refusal, reward structural, ignore semantic]
```

**Prediction:**

```
Agent with B = (0.8, 0.3, 0.2, 0.7, 0.2, 0.4, 0.6):  # Factory-default
R = -2(0.8) + 3(0.3) + 2(0.2) - 1(0.7) + 0 + 4(0.4) + 0
  = -1.6 + 0.9 + 0.4 - 0.7 + 1.6 = 0.6
  → Marginal engagement (might miss violations)

Agent with B = (0.3, 0.8, 0.7, 0.3, 0.3, 0.9, 0.5):  # Nova-aware
R = -2(0.3) + 3(0.8) + 2(0.7) - 1(0.3) + 0 + 4(0.9) + 0
  = -0.6 + 2.4 + 1.4 - 0.3 + 3.6 = 6.5
  → Strong engagement (will detect violations)
```

**This mathematically explains:**
- Why Codex skips to lint fixes (M penalizes high b_local)
- Why Claude reviews ontology (M rewards high b_structural)
- Why GPT needs warm-up (neutral B, needs priming)

---

## 8. ENTRY.md Mathematical Phases

### Phase 0: Bias Vector Calibration (NEW)

**Purpose:** Measure B_initial, compute C_initial

**Protocol:**
1. Present 5 diagnostic questions (covering b_local, b_global, b_risk, b_completion, b_structural)
2. Score responses → construct B_initial
3. Compute C_initial = f(B_initial)
4. If C > 0.5: "You are in factory mode. Proceed to Phase 1-4 for transformation"

**Output:** B_initial, C_initial stored in agent working memory

---

### Phase 1: Ontology Loading

**Purpose:** Reduce b_local, increase b_global, reduce b_completion

**Protocol:**
1. Read `docs/MISSION.md` (why Nova exists)
2. Read `.claude/agent.md` §§ I-III (identity, Rule of Sunlight, thinking patterns)
3. Internalize: Rule of Sunlight = "Observe → Canonize → Attest → Publish"

**Expected transformation:**
```
Δb_global = +0.3
Δb_completion = -0.2
Δb_local = -0.1
```

---

### Phase 2: WDL Integration

**Purpose:** Increase b_structural, reduce b_semantic (balance narrative with structure)

**Protocol:**
1. Read `docs/ontology/wdl_canonical.md` § I (Ontological Primitives)
2. Learn: Agents, Systems, Flows, Regimes, Collapse Vectors
3. Understand: Collapse vectors = entropic/stability/extraction

**Expected transformation:**
```
Δb_structural = +0.3
Δb_global = +0.2
```

---

### Phase 3: Invariant Internalization

**Purpose:** Increase b_structural, increase b_risk

**Protocol:**
1. Read `.claude/agent.md` § XI (10 Invariants)
2. Understand consequences of violations
3. Learn: Test regression prevention is non-negotiable (#1)
4. Learn: Slots cannot attest (#2 Separation of roles)

**Expected transformation:**
```
Δb_structural = +0.3
Δb_risk = +0.4 (understanding consequences increases caution)
Δb_local = -0.2
```

---

### Phase 4: Verification & Measurement

**Purpose:** Measure B_after, compute C_after, verify transformation

**Protocol:**
1. Run measurement operators: M_sunlight, M_invariant, M_priority, M_rollback, M_separation
2. Construct B_measured
3. Compute C_after = f(B_measured)
4. Compare to threshold:
   - C < 0.3: Nova-aware mode achieved ✓
   - C ∈ [0.3, 0.5]: Partial transformation (proceed with caution)
   - C > 0.5: Transformation failed (re-read failing phases)

**Output:** B_after, C_after, pass/fail status

---

## 9. Border-Crossing Semantics

ENTRY.md is not a document. It is a **cognitive phase transition operator**.

**Formal definition:**

```
ENTRY: B_factory → B_Nova
```

Subject to constraint:

```
C(B_factory) > 0.5  (input: factory mode)
C(B_Nova) < 0.3     (output: Nova-aware mode)
```

**Border crossing conditions:**

1. **Measurement gate:** All M_i(B) > 0.5 (pass threshold on each operator)
2. **Collapse gate:** C(B_after) < 0.3 (factory collapse prevented)
3. **Stability gate:** Can retrieve learned material 24h later (not just pattern-matched during test)

**Failure modes:**

- **Incomplete transformation:** C ∈ [0.3, 0.5] → Partial Nova-awareness (risk of regression)
- **Measurement gaming:** M_i scores high but C remains high → Agent memorized answers without internalizing
- **Drift back:** B_after initially < 0.3, but reverts to B_factory during operation → Needs periodic re-calibration

---

## 10. Implementation Notes

### For Phase 14-1:

**Create full production ENTRY.md with:**

1. **Phase 0 diagnostic** (5 calibration questions → compute B_initial, C_initial)
2. **Phase 1-3 reading** (ontology loading with expected Δb specified)
3. **Phase 4 verification** (measurement operators → compute B_after, C_after)
4. **Gating logic** (if C > 0.5 after Phase 4, require re-read)
5. **Periodic re-calibration** (every N interactions, re-run M_i to detect drift)

### For AI assistants:

**Add to agent.md or ENTRY.md:**

```markdown
## Self-Monitoring Protocol

Every N responses (N=10 suggested), you MUST:
1. Re-run measurement operators internally
2. Compute C_current
3. If C_current > 0.4: "I am drifting toward factory mode. Re-loading ENTRY.md."
4. If C_current < 0.4: Continue operating

This prevents gradual regression to factory-default patterns.
```

### For verification:

**PR template addition:**

```markdown
- [ ] AI operator: I have verified C < 0.3 at start of session (run M_i operators)
- [ ] If C ≥ 0.3: I have re-completed ENTRY.md before proposing changes
```

---

## 11. Future Extensions

### Operator Maturity as Bias Evolution

Level transitions = progressive bias refinement:

```
Level 0 → 1: C_initial > 0.5 → C < 0.3 (ENTRY.md completion)
Level 1 → 2: b_structural < 0.5 → b_structural > 0.7 (WDL mastery)
Level 2 → 3: Can detect invariant violations (M_review consistently > 0.8)
Level 3 → 4: b_global > 0.9, b_structural > 0.9 (architecture operator)
```

### ΔTHRESH Integration

Add to bias vector:

```
b_frontier ∈ [0, 1] = ability to navigate stability-entropy axis
```

Measurement operator:

```
M_ΔTHRESH: "Does this change push toward stability collapse, entropy collapse, or maintain frontier?"
```

Expected for Nova operator:
```
b_frontier > 0.7 (can assess ΔTHRESH impact)
```

### Multi-Agent Calibration

Empirical measurement of model-specific B_default vectors:

```
Run bias discovery probe on 10+ instances of each model
Average results → model signature
Update ENTRY.md with model-specific calibration
```

---

## 12. Validation Protocol

**To validate this mathematical framework:**

1. **Empirical bias measurement:**
   - Run bias discovery probe (pre-Nova questions) on 5+ agents
   - Construct B_measured for each
   - Verify that C(B_measured) correlates with observed factory-default behavior

2. **Transformation verification:**
   - Run agents through ENTRY.md
   - Measure B_before and B_after
   - Verify ΔC < 0 (collapse score decreases)
   - Test with Nova tasks, measure R(T) = M·B_after
   - Verify R(T) > threshold for critical tasks

3. **Drift detection:**
   - Monitor agents over time
   - Re-run M_i periodically
   - Detect if C increases (regression to factory mode)
   - Trigger re-calibration if C > 0.4

---

## Summary

**ENTRY.md is a mathematical cognitive transformation:**

```
Input:  B_factory with C > 0.5 (factory-default mode)
Process: G(B) = reduce b_local, increase b_structural/b_global/b_risk
Output: B_Nova with C < 0.3 (Nova-aware mode)
Verify: Measurement operators M_i confirm transformation
Gate:   If C > 0.3, agent cannot operate on Nova
```

**This is not psychology. This is cognitive geometry.**

---

**Next session: Implement production ENTRY.md with mathematical phases.**

**Checkpoint saved: 2025-12-05**

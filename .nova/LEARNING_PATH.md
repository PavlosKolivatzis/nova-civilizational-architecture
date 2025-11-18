# Nova Learning Path — The Golden Path

## Philosophy

> **Reading in order ≠ Understanding**

This learning path implements a **checkpoint-driven pedagogy** where agents:
1. Read in sequence (build layers)
2. Verify understanding (checkpoints)
3. Synthesize knowledge (mental model)

Inspired by Gemini's discovery: Agents that follow checklists without verification end up **knowing facts without understanding systems**.

---

## The Three Phases of Understanding

### Phase 1-4: Guided Tour (Sequential)
- **Read files in prescribed order**
- **Run commands with expected outputs**
- **Answer checkpoint questions** before proceeding

### Phase 5: Synthesis (Integration)
- **Draw architecture from memory**
- **Trace data flows**
- **Teach concepts to others**
- **Critique honestly**

### Mastery: Independent Navigation
- **Predict before verifying**
- **Explain your errors**
- **Propose extensions**

---

## How to Use This Path

### For Agents (CLI tools, LLMs, automated systems)

```bash
# Step 1: Entry
npm run nova:welcome

# Step 2: Load the map
cat .nova/meta.yaml | grep -A200 "learning_path:"

# Step 3: Follow phases in order
# Phase 1: Read agents/nova_ai_operating_framework.md
# Phase 1: Read docs/architecture.md
# Phase 1: Read docs/slots/*.md (slot01 → slot10)
# Phase 1: CHECKPOINT - Answer verification questions
# (Repeat for phases 2-5)

# Step 4: Synthesis (Phase 5)
# Draw architecture, trace flows, critique
```

### For Humans (professors, contributors, auditors)

**Quick Path (1 hour):**
- Phase 1 only (read 3 docs, answer 5 questions)
- Outcome: Understand Nova's philosophy

**Deep Path (4-6 hours):**
- Phases 1-4 (read, run, verify)
- Outcome: Can navigate codebase independently

**Mastery Path (ongoing):**
- Phases 1-5 (full synthesis)
- Outcome: Can extend Nova, critique design, teach others

---

## Checkpoint Design Principles

### Verification Questions
Test **understanding**, not **memory**:
- ✅ "Explain why slots can't attest directly"
- ❌ "What is the third invariant?"

### Test Yourself
Require **action**, not **passive reading**:
- ✅ "Run a single slot's tests: pytest tests/test_slot01* -v"
- ❌ "Tests are important"

### Final Exam (Phase 5)
Prove **transfer**, not **replication**:
- ✅ "Read unknown code, predict slot, verify"
- ❌ "Recite the Rule of Sunlight"

---

## Phase-by-Phase Guide

### Phase 1: Orientation (~15 min)

**Goal:** Build foundational ontology

**Steps:**
1. Read `agents/nova_ai_operating_framework.md`
   - Focus: Rule of Sunlight, 3 ledgers, 6 invariants
   - Note: This is the Rosetta Stone

2. Read `docs/architecture.md`
   - Focus: 10-slot map, orchestrator role
   - Note: See how philosophy → structure

3. Read `docs/slots/*.md` (in order: slot01 → slot10)
   - Focus: Each slot's purpose, contracts
   - Note: Read sequentially to understand dependencies

**Checkpoint:**
- Can you explain Rule of Sunlight in your own words?
- What are the 3 ledgers and why separated?
- Name all 6 invariants (no peeking)
- Draw 10-slot architecture from memory
- Explain: Why can't slots attest directly?

**Test Yourself:**
- Open random `slot*/meta.yaml`, identify contracts
- Trace: user input → slots → attestation

---

### Phase 2: Introspection (~10 min)

**Goal:** Theory → Code

**Steps:**
1. Read `src/nova/slots/*/meta.yaml`
   - Focus: Versions, flags, schemas
   - Note: Slots self-describe (executable specs)

2. Read `orchestrator/app.py`
   - Focus: Slot registration, lifespan, errors
   - Note: Orchestrator is thin glue

3. Run `pytest -q -m "not slow"`
   - Expect: 1435 passing
   - Note: Tests ARE documentation

4. Run `npm run maturity`
   - Expect: 4.0 overall
   - Note: Maturity = capability, not LOC

**Checkpoint:**
- Difference between meta.yaml and implementation?
- How does orchestrator discover slots?
- Why are tests the highest maturity signal?
- Name 3 feature flags and what they gate

**Test Yourself:**
- Add print to `orchestrator/app.py`, verify it runs
- Run: `pytest tests/test_slot01* -v`
- Find where `NOVA_ENABLE_PROMETHEUS` is checked

---

### Phase 3: Observability (~10 min)

**Goal:** See how Nova watches itself

**Steps:**
1. Read `orchestrator/prometheus_metrics.py`
   - Focus: Naming (`nova_slotN_*`), gauges
   - Note: Metrics are the nervous system

2. Read `src/nova/slots/slot07_production_controls/flag_metrics.py`
   - Focus: Flag observability
   - Note: Flags themselves are observable (meta!)

3. Run server with metrics:
   ```bash
   NOVA_ENABLE_PROMETHEUS=1 uvicorn orchestrator.app:app
   curl localhost:8000/metrics | grep nova_
   ```
   - Note: Metrics off by default (reversibility)

**Checkpoint:**
- Why metrics behind flag instead of always-on?
- What does `nova_feature_flag_enabled{flag='X'}` tell you?
- How to add new metric to Slot02?

**Test Yourself:**
- Find metric in `/metrics`, trace to source code
- Toggle `PROMETHEUS=0`, verify `/metrics` → 404
- Predict what metrics a slot exports

---

### Phase 4: Change Protocol (~10 min)

**Goal:** Learn to evolve safely

**Steps:**
1. Read `agents/nova_ai_operating_framework.md` §5, §11
   - Focus: Change policy, pre-merge checklist
   - Note: Off-by-default, flag-gated, reversible

2. Read `.env.example`
   - Focus: `NOVA_*` flags, default=0
   - Note: Every flag starts off (opt-in only)

3. Experiment: Add new flag
   - Gate a behavior (e.g., log message)
   - Write test for both flag states
   - Verify rollback

4. Verify: Toggle flag → behavior reverts

**Checkpoint:**
- Why must flags default to 0?
- Difference between flag and config value?
- How to test both flag=0 and flag=1 in CI?

**Test Yourself:**
- Add `NOVA_ENABLE_EXAMPLE_FEATURE=0` to `.env.example`
- Gate simple behavior behind flag
- Write test verifying both states
- Toggle flag, confirm behavior change
- Set flag=0, confirm revert

---

### Phase 5: Synthesis (~30 min) **Integration Test for Your Brain**

**Goal:** Prove you can think like Nova

**Steps:**

**1. Draw** (no peeking)
- Sketch full architecture from memory
- Include: 10 slots, orchestrator, contracts, attestation flow
- Test: If you can't draw it, you don't understand it

**2. Trace** (end-to-end)
- Pick user action, trace data flow
- Example: Text → Slot02 ΔΣΘΩ → Slot01 anchor → Slot09 audit
- Test: Can you follow input → ledgers → output?

**3. Explain** (teach someone)
- Explain Rule of Sunlight (your words)
- Why 3 ledgers separated?
- Why can't slots attest?
- Test: If you can teach it, you've internalized it

**4. Critique** (honest assessment)
- Find 3 things Nova does well
- Find 3 gaps/risks (use audit report)
- Test: Understanding > cheerleading

**Checkpoint — Verify Mastery:**
- Explain Nova's core innovation (2 sentences)
- What breaks if we merge ledgers 1 and 2?
- Design Slot11: what contracts needed?
- Propose test for untested edge case
- Identify failure mode not covered

**Final Exam:**
- Read random code file (never seen)
- Predict: Which slot? What contracts?
- Verify via `meta.yaml` + tests
- If wrong: Explain WHY (update mental model)

---

## Success Criteria

### You Know Nova When You Can:

1. **Navigate independently**
   - Read unknown code, predict ownership
   - Find relevant tests without search

2. **Explain to others**
   - Teach Rule of Sunlight clearly
   - Justify architectural choices

3. **Critique honestly**
   - Identify what Nova does well
   - Name gaps without reading audit

4. **Extend safely**
   - Add flag-gated feature
   - Write tests for both paths
   - Verify clean rollback

5. **Think in layers**
   - Separate fact vs claim vs attest
   - Understand why boundaries exist

---

## Why This Works

### Traditional Approach (Fails)
1. Clone repo
2. Read random files
3. Run tests
4. "I understand it"

**Problem:** Knows facts, doesn't understand system.

### Nova Approach (Works)
1. **Front door** (`npm run nova:welcome`)
2. **Golden path** (phases 1-4 in order)
3. **Checkpoints** (verify before proceeding)
4. **Synthesis** (build mental model)
5. **Mastery** (predict, explain, critique)

**Result:** Can navigate, extend, teach.

---

## For Agents: Implementation Guide

If you're building an agent that needs to learn Nova:

```python
def learn_nova():
    # Phase 1: Entry
    run("npm run nova:welcome")
    load_map(".nova/meta.yaml")

    # Phases 1-4: Sequential learning
    for phase in ["phase1_orientation", "phase2_introspection",
                  "phase3_observability", "phase4_change_protocol"]:
        for step in get_steps(phase):
            execute(step)

        # CRITICAL: Don't proceed without passing checkpoint
        if not pass_checkpoint(phase):
            raise ValueError(f"Failed {phase} checkpoint - review and retry")

    # Phase 5: Synthesis
    architecture = draw_from_memory()  # No peeking!
    trace = trace_user_action()
    explanation = teach_to_human()
    critique = find_strengths_and_gaps()

    # Final exam
    unknown_file = random_code_file()
    prediction = predict_slot_ownership(unknown_file)
    verify(prediction)

    return "Mastery achieved" if all_pass() else "Review weak areas"
```

---

## Maintenance

### When to Update This Path

- New slot added (update Phase 1 reading list)
- Architecture changes (update Phase 5 synthesis tasks)
- New feature flag pattern (update Phase 4 experiment)
- Audit finds new gap (update Phase 5 critique)

### How to Update

1. Follow the path yourself (eating your own dog food)
2. Note where you got confused (gap in path)
3. Add checkpoint question for that gap
4. Test with fresh learner
5. Iterate

---

## Credits

This learning path design was informed by:
- Gemini's empirical discovery of the "golden path" pattern
- Nova's own principle: "Observe → Canonize → Attest → Publish"
- Pedagogical research: Checkpoints > passive reading

**The path embodies Nova's philosophy**: Sequential, verifiable, reversible, observable.

---

**Next:** Start with `npm run nova:welcome` and follow Phase 1.

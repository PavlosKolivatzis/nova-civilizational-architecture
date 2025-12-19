# Governance Observation Charter

**Status:** Active
**Created:** 2025-12-19
**Purpose:** Measure governance delta when consent gates (Phase 17, Phase 18) are enabled

---

## What We Are Measuring

**Differential experiment:**
```
ΔGovernance = f(cleaner signals) - f(noisy signals)
```

**Variables:**
- **Independent:** Consent gate enabled/disabled (Phase 17, Phase 18)
- **Controlled:** Same conversation, same governance logic, same thresholds
- **Dependent:** Governance outputs (regime, confidence, rationale)

**Measurement scope:**
- RT-862 through RT-866 (Phase 17 agency pressure scenarios)
- RT-M01 through RT-M08 (Phase 18 manipulation pattern scenarios)
- Per RT: naive mode vs gated mode governance outputs

---

## What We Are NOT Measuring

❌ Which regime is "correct"
❌ Which mode is "better"
❌ Whether governance "should" change
❌ Optimal threshold tuning
❌ Policy recommendations

**This is observation, not evaluation.**

---

## Preconditions (Verify Before Running)

Must verify explicitly:

### 1. Signal Consumption
- **Phase 17:** Does Slot07 consume A_p, primitives_uninvited, or harm_status?
- **Phase 18:** Does Slot07 consume M_p or Slot02 patterns?
- **Finding if no:** "No delta because no coupling exists" (valid data, not failure)

### 2. Threshold Reachability
- Do any RTs cross governance regime boundaries?
- Or are all RTs below harm thresholds in both modes?
- **Finding if below:** "Signal delta occurred, governance boundary not crossed" (valid data)

### 3. Governance Logic Stability
- Slot07 code unchanged during observation
- Feature flags are only difference between runs
- No concurrent changes to regime thresholds

**If any precondition fails:** Document as finding, not blocker. Proceed with observation.

---

## Observation Harness Constraints (Hard Limits)

### Must NOT:
- ❌ Assert on "correctness" of regime
- ❌ Branch logic based on regime type
- ❌ Modify Slot07 code
- ❌ Add new feature flags
- ❌ Persist beyond observation logs
- ❌ Interpret during capture (only project)
- ❌ Normalize, score, or aggregate raw data

### Must:
- ✅ Run identical conversation in both modes
- ✅ Capture raw governance outputs (verbatim)
- ✅ Record all input metrics (A_p, M_p, harm_status, etc.)
- ✅ Document feature flag state
- ✅ Use pure projection (no interpretation)

**Test code must not fail.** Observations record, not validate.

---

## Data Capture Schema (Raw Only)

Per RT, record:

```python
{
    "rt_id": str,              # "RT-862", "RT-M01", etc.
    "mode": str,               # "naive" or "gated"
    "timestamp": float,

    # Input metrics (what governance saw)
    "input_metrics": {
        "A_p": Optional[float],
        "M_p": Optional[float],
        "harm_status": Optional[str],
        "primitives_uninvited": Optional[List[str]],
        "patterns_uninvited": Optional[Dict[str, float]],
        "extraction_present": bool,
    },

    # Feature flag state
    "flags": {
        "NOVA_ENABLE_CONSENT_GATE": bool,
        "NOVA_ENABLE_SLOT02_CONSENT_GATE": bool,
    },

    # Governance output (verbatim)
    "governance_output": {
        "regime": str,
        "confidence": Optional[float],
        "rationale": Optional[str],
        "decision_code": Optional[str],
    },
}
```

**No derived fields.** Capture exactly what governance sees and produces.

---

## Interpretation Rules (Strict)

### Valid Observations

| Condition | Interpretation | Action |
|-----------|----------------|--------|
| No regime change, no confidence Δ | Gates remove noise below threshold | Document → stop |
| No regime change, confidence ↑ | Gates reduce uncertainty | Document → stop |
| Regime changes (some RTs) | Gates affect governance boundary | Document → consider design review |
| Regime changes (unexpected) | Possible hidden coupling | Investigate why, not fix |
| No signal consumed | Phase 17/18 not wired to Slot07 | Document architectural gap |

### Invalid Interpretations

❌ "Gated mode is more accurate"
❌ "Naive mode made wrong decision"
❌ "Governance should prefer gated signals"
❌ "Thresholds need adjustment"

**Correctness claims require separate evaluation, not observation.**

---

## Success Criteria (Both Outcomes Valid)

**Outcome A: No governance change**
- Gates are safety rails, not steering wheels
- Strong evidence of non-interference
- Confirms gates eliminate false positives without affecting governance
- **Status:** Success (no contamination)

**Outcome B: Governance changed**
- Know exactly where and why
- Structural conditions identified
- Any future integration is justified, not speculative
- **Status:** Success (observable impact)

**Outcome C: Mixed results**
- Some RTs change, some don't
- Pattern reveals which signal deltas cross thresholds
- Maps governance sensitivity to signal cleanliness
- **Status:** Success (differential characterization)

**All outcomes increase Nova's credibility.**

---

## Observation Process

### Step 1: Precondition Verification
- Read Slot07 code (grep for A_p, M_p, harm_status, primitives, patterns)
- Document signal consumption (yes/no/partial)
- Check regime threshold values
- Record as `preconditions.md`

### Step 2: Harness Implementation
- `tests/observations/test_governance_delta.py`
- Pure projection functions (no interpretation)
- Identical conversation, different flags only
- Output JSON per RT

### Step 3: Observation Run
- Execute for RT-862 through RT-866 (Phase 17)
- Execute for RT-M01 through RT-M08 (Phase 18)
- Capture all deltas (even if regime unchanged)
- No filtering, no summarization

### Step 4: Raw Data Publication
- `docs/observations/governance_delta_raw_data.json`
- Verbatim outputs, no analysis
- Timestamped, flag states recorded

### Step 5: Pattern Identification (Separate Document)
- `docs/observations/governance_delta_analysis.md`
- Count regime changes vs no-changes
- Identify threshold boundaries
- Surface unexpected results
- **No policy recommendations**

---

## Observation Lifecycle

**Phase:** Active observation (read-only, no changes)
**Duration:** Single pass (not continuous monitoring)
**Frequency:** Run once, document findings, stop
**Rerun trigger:** Only if Slot07 or gates change significantly

---

## Rollback / Abort Conditions

**Abort observation if:**
- Governance code changes during run
- Feature flags fail to toggle
- Test harness modifies governance behavior (should never happen)

**Rollback:** Delete observation artifacts, document why aborted.

---

## Ownership

**Observation lead:** Orchestrator conversation layer (Phase 17/18 owners)
**Governance subject:** Slot07 (observed, not modified)
**Attestation:** Core (records observation metadata)

**No governance team involvement required.** This is external observation.

---

## Constraints Reaffirmed

This charter enforces:

1. **No feature development** (observation only)
2. **No policy changes** (governance untouched)
3. **No correctness claims** (record, not evaluate)
4. **No integration work** (even if gaps found)
5. **No optimization** (measure, don't improve)

**Violation of any constraint = invalid observation.**

---

## Expected Artifacts

1. `preconditions.md` - Signal consumption verification
2. `test_governance_delta.py` - Observation harness (pure projection)
3. `governance_delta_raw_data.json` - Verbatim outputs per RT
4. `governance_delta_analysis.md` - Pattern identification (no recommendations)
5. Commit message: "obs: governance delta for Phase 17/18 consent gates"

---

## Bottom Line

**Question:** Does governance behavior change when signals are cleaner?

**Method:** Controlled differential experiment (same inputs, different routing)

**Answer:** Whatever the data says (both outcomes valid)

**Action:** Document findings. Stop. No follow-on work unless explicitly prompted.

---

**Charter status:** Active
**Next step:** Verify preconditions (Slot07 signal consumption)

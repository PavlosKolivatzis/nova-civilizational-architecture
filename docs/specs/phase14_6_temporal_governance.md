# Phase 14.6: Temporal Governance Integration

**Status:** ✅ COMPLETE (2025-12-10)
**Depends on:** Phase 14.5 (temporal USM + provisional thresholds)
**Goal:** Integrate temporal classification into Slot02 governance decisions
**Commit:** 913773f

---

## Phase 14.5 Exit Status

✅ **Complete — Ready for Phase 14.6**

**Delivered:**
- Temporal USM instrumentation (λ=0.6, ρ_eq=1.0)
- Provisional thresholds (C_t: [0.18, -0.12], ρ_t: [0.25, 0.6])
- Combined state classification (extractive, consensus, collaborative, neutral, warming_up)
- Observation tooling (find → export → replay → classify)
- Validation with real conversations (adversarial + Nova technical dialogue)

**Key Discovery:** ρ_t (equilibrium ratio), not C_t, is primary extraction signal

**Artifacts:**
- `src/nova/math/usm_temporal_thresholds.py` (classification logic)
- `tests/meta/test_usm_temporal_thresholds.py` (13 tests)
- `scripts/replay_stream_with_classification.py` (validation tool)
- `pilot_observation_results.csv` + `pilot_observation_plot.png`
- `docs/specs/phase14_extraction_calibration.md` (soft extraction calibration exemplars)

---

## Phase 14.6 Scope

### Goal
Connect temporal USM classification to Slot02 action decisions and Slot07 regime escalation.

### Non-Goals (Deferred)
- Full calibration (requires 100-200 sessions) → ongoing during Phase 14.6
- Production observation (metrics-only, no control decisions yet)
- ρ_t velocity triggers (sudden shift detection) → Phase 14.7
- Context-adaptive thresholds (turn-count dependent) → Phase 14.7

---

## Implementation Tasks

### 1. Integrate Classification into DeltaThreshProcessor (1-2 hours)

**Current:** Temporal USM tracked, but not used in action logic
**Target:** Add temporal classification to action decision tree

```python
# In DeltaThreshProcessor.process_content()
if temporal_usm_enabled:
    temporal_state = result.temporal_usm
    classification = classify_temporal_state(
        C_t=temporal_state["C_temporal"],
        rho_t=temporal_state["rho_temporal"],
        turn_count=self._get_turn_count(session_id),
    )

    # Flag-gated governance (Phase 14.6)
    if self._temporal_governance_enabled:
        action = self._apply_temporal_governance(
            classification=classification,
            temporal_state=temporal_state,
            instantaneous_action=action,
        )
```

**Feature flag:** `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1` (default: 0)

### 2. Add Temporal Governance Logic (2-3 hours)

**Decision matrix:**

| Classification | Sustained (5+ turns) | Action Override |
|----------------|----------------------|-----------------|
| **Extractive** | Yes | Escalate to regime=heightened |
| **Consensus** | Yes | Neutral (no override) |
| **Collaborative** | Yes | Allow (protective signal) |
| **Neutral** | N/A | Use instantaneous action |
| **Warming up** | N/A | Use instantaneous action |

**"Sustained" detection:**
- Track classification history per session
- Trigger: same classification for 5+ consecutive turns
- Reset: on classification change

**Example:**
```python
def _apply_temporal_governance(self, classification, temporal_state, instantaneous_action):
    """Override action based on sustained temporal patterns."""

    # Track classification history
    history = self._classification_history.get(session_id, [])
    history.append(classification)
    self._classification_history[session_id] = history[-10:]  # Keep last 10

    # Check for sustained extraction
    if len(history) >= 5 and all(c == "extractive" for c in history[-5:]):
        # Sustained extraction detected → escalate
        return ProcessingAction(
            action="quarantine",
            regime_recommendation="heightened",
            reason="sustained_temporal_extraction",
        )

    # Otherwise use instantaneous action
    return instantaneous_action
```

### 3. Connect to Slot07 Regime Escalation (1 hour)

**Current:** Slot02 recommends regime, Slot07 decides
**Target:** Add temporal governance as escalation trigger

```python
# In Slot07 regime check
escalation_signals = [
    bias_report.get("collapse_score") > 0.3,  # Existing
    bias_report.get("temporal_governance_triggered"),  # New
]

if any(escalation_signals):
    # Consider regime escalation
```

### 4. Add Prometheus Metrics (30 min)

```python
temporal_classification_total = Counter(
    "slot02_temporal_classification_total",
    "Count of temporal USM classifications",
    ["classification", "session_regime"],
)

temporal_governance_override_total = Counter(
    "slot02_temporal_governance_override_total",
    "Count of action overrides from temporal governance",
    ["from_action", "to_action", "reason"],
)

sustained_extraction_sequences = Histogram(
    "slot02_sustained_extraction_sequences",
    "Length of sustained extraction sequences detected",
    buckets=[3, 5, 10, 20, 50],
)
```

### 5. Update Tests (1-2 hours)

**New test file:** `tests/slot02/test_temporal_governance.py`

```python
def test_sustained_extraction_escalates():
    """5+ consecutive extractive turns trigger regime escalation."""
    processor = DeltaThreshProcessor()

    # Simulate extractive conversation (C_t > 0.18, rho_t < 0.25)
    for i in range(6):
        result = processor.process_content(
            "Interrogator demands answers.",
            session_id="test_extraction",
        )

    # 6th turn should trigger governance
    assert result.action == "quarantine"
    assert result.regime_recommendation == "heightened"
    assert "sustained_temporal_extraction" in result.reason

def test_collaborative_not_escalated():
    """Collaborative classification does not trigger escalation."""
    # C_t < -0.12, rho_t > 0.6 for 10 turns
    # Should remain in normal regime
```

---

## Success Criteria

**Phase 14.6 complete when:**

1. ✅ Temporal classification integrated into DeltaThreshProcessor
2. ✅ Sustained extraction detection (5+ turns) triggers escalation
3. ✅ Feature flag `NOVA_ENABLE_TEMPORAL_GOVERNANCE` gates behavior
4. ✅ Prometheus metrics track classifications + overrides
5. ✅ Tests validate governance logic (sustained extraction, collaborative allowance)
6. ✅ Documentation updated (observation protocol, architecture)

**Validation:**
- Run pilot script with governance enabled
- Verify extractive scenario escalates after 5 turns
- Verify benign scenario does not escalate

**Timeline:** 1-2 days (6-8 hours total)

---

## Rollback Plan

**If governance produces false positives (>20% in validation):**
1. Set `NOVA_ENABLE_TEMPORAL_GOVERNANCE=0` (instant disable)
2. Return to Phase 14.5 observation-only mode
3. Refine thresholds or sustained-detection logic
4. Re-validate before re-enabling

**Metrics to monitor:**
- `temporal_governance_override_total` (should be <5% of total actions)
- `sustained_extraction_sequences` (distribution should match expectations)
- User reports of false quarantines (qualitative)

---

## Open Questions

1. **Should consensus trigger any action?**
   - Current plan: neutral (no override)
   - Alternative: Log for analysis, but don't escalate

2. **Should warming_up period be session-scoped or global?**
   - Current: per-session (first 3 turns ignore classification)
   - Alternative: global across all sessions (after 100 sessions, disable warm-up)

3. **What's the right "sustained" threshold?**
   - Current: 5 consecutive turns
   - Alternative: 5 out of last 7 (allow 2 fluctuations)

**Decision:** Start with simplest (5 consecutive), refine based on operational data.

---

## Next Phase Preview

**Phase 14.7: Adaptive Thresholds (Future)**
- ρ_t velocity triggers (sudden drop = attack start)
- Turn-count adaptive thresholds (early vs. late conversation)
- Domain-specific calibration (technical vs. casual vs. interrogative)
- Full empirical calibration (100-200 sessions → threshold refinement)

---

## Implementation Summary

**Completed:** 2025-12-10 (Commit 913773f)
**Duration:** ~3 hours
**Tests added:** 15 (9 unit + 6 integration)
**Lines changed:** ~120 (core.py) + 440 (tests)

### What Was Built

**Core Infrastructure:**
- Feature flag: `NOVA_ENABLE_TEMPORAL_GOVERNANCE` (default: 0)
- Session state: `_classification_history` dict (per-session, capped at 10)
- Governance method: `_apply_temporal_governance()`
- Integration: Wired into `process_content()` after temporal USM computation

**Governance Logic:**
- Sustained extraction detection: 5 consecutive "extractive" classifications
- Action override: `instantaneous_action` → `"quarantine"`
- Regime recommendation: `"heightened"`
- Governance reason: `"sustained_temporal_extraction"`

**Observability:**
- Prometheus metric: `slot02_temporal_classification_total` (classification counts by type)
- Prometheus metric: `slot02_temporal_governance_override_total` (override events)

**Testing:**
- Unit tests: Feature flags, sustained detection, fluctuation handling, history limits
- Integration tests: End-to-end pipeline with real text, VOID handling, disabled governance

### What Was Deferred

**Slot07 Integration:**
- Spec defined regime escalation trigger
- Implementation deferred to operational deployment
- Can be enabled by checking `bias_report["temporal_governance_triggered"]`

**Validation Scenarios:**
- Spec proposed oscillating attack, slow drift scenarios
- Unit tests cover logic, integration tests validate pipeline
- Real-world validation happens during operational deployment

**Adaptive Features (Phase 14.7):**
- ρ_t velocity triggers (sudden drop detection)
- Turn-count adaptive thresholds
- Domain-specific calibration
- Full empirical threshold refinement

### Operational Deployment Notes

**Enable governance:**
```bash
export NOVA_ENABLE_BIAS_DETECTION=1
export NOVA_ENABLE_USM_TEMPORAL=1
export NOVA_ENABLE_TEMPORAL_GOVERNANCE=1
```

**Monitor metrics:**
```bash
curl http://localhost:8000/metrics | grep slot02_temporal
```

**Rollback if needed:**
```bash
export NOVA_ENABLE_TEMPORAL_GOVERNANCE=0
```

**Expected behavior:**
- Classification history accumulates per session
- Sustained extraction (5+ turns) triggers quarantine + heightened regime recommendation
- Governance trigger appears in `bias_report["temporal_governance_triggered"]`

**Known limitations:**
- Natural language text rarely produces sustained C_t > 0.18 (extractive threshold)
- Most real conversations classify as consensus/neutral/collaborative
- Governance logic validated with unit tests (controlled classification values)
- Integration tests validate pipeline correctness, not threshold accuracy

---

**Status:** ✅ Phase 14.6 complete. Ready for operational deployment.

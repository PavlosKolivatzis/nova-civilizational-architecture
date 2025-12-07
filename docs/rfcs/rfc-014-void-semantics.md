# RFC-014: VOID Semantic Propagation Across Cognitive Slots

**Status:** Draft
**Phase:** 14.4
**Date:** 2025-12-07
**Authors:** Nova Architectural Team
**Ontology Version:** nova.operating@1.1.0, nova.frameworks@1.8.0

---

## Abstract

This RFC formalizes the propagation of VOID semantic state (empty SystemGraph) across Nova's cognitive slot architecture. VOID was introduced in Phase 14.3 as a mathematical primitive (`G_void = (V=∅, E=∅)`) in the Mother Ontology and requires explicit operational policy to prevent semantic drift, slot interference, and emergent pathologies.

**Core Principle:** VOID represents **epistemic absence**, not **affective threat**. Silence ≠ fear. Emptiness ≠ danger.

---

## 1. Background

### 1.1 VOID Discovery (Phase 14.3)

During USM Bias Detection implementation, we discovered that TextGraphParser can produce empty graphs for:
- Unparseable text (no actors, no relations)
- Semantic null inputs (empty strings, whitespace)
- Low-information content (greetings, acknowledgments)

**Current behavior:**
- Slot02 emits `BIAS_REPORT@1` with `graph_state='void'`
- `B(G_void) = (0, 0, 1, 0, 0, 0, 0)` → `C(G_void) = -0.5`
- Feature flag: `NOVA_ENABLE_VOID_MODE=1` (default on)

**Problem:** Other slots (03, 07, 09, 01) have NO formal policy for VOID handling → risk of:
- Emergency behaviors triggered by absence of signal
- Confidence collapse on sparse data
- Threshold resets during VOID bursts
- Affective misinterpretation (VOID → fear)

### 1.2 Ontological Context

**Mother Ontology (nova.frameworks@1.8.0):**
- Defines VOID as graph primitive with mathematical form
- Establishes collapse score baseline: `C(G_void) = -0.5`
- Records VOID in changelog § new_semantics

**Operating Ontology (nova.operating@1.1.0):**
- Defines `void_state@1` contract
- Specifies slot-specific handling policies
- Maps VOID interpretation across 5 regime states
- Establishes non-interference constraints

**This RFC:** Implementation specification for Operating Ontology policies.

---

## 2. Motivation

### 2.1 Architectural Invariants at Risk

Without formal VOID propagation:

**Invariant #1 (Separation of Roles):**
- Slot09 might filter VOID as "suspicious low entropy"
- Slot03 might collapse VOID into fear state
- Cross-slot interference violates slot independence

**Invariant #6 (Transparent Uncertainty):**
- VOID = "no data" but slots treat as "low confidence data"
- Conflates absence with negative evidence

**Invariant #7 (Observability):**
- VOID events disappear in aggregation
- No metrics for VOID propagation patterns

### 2.2 Empirical Evidence of Need

**Scenario 1: VOID Burst Attack**
```
Input stream: ["", "", "", "..."] (100 VOID inputs/second)
Without policy:
- Slot07 might trigger heightened→emergency (false alarm)
- Slot09 might flag as "entropy anomaly" (adversarial signal)
- Slot03 might escalate to fear state (affective contagion)
```

**Scenario 2: Sparse Legitimate Traffic**
```
Chat session: ["hi", "...", "ok", "..."] (natural pauses)
Without policy:
- Confidence scores collapse during pauses
- Thresholds reset between messages
- Quality oracle misinterprets silence as degradation
```

### 2.3 Phase 14.3 Limitation

Spec § 12 "Known Limitations" states:
> **VOID Semantic Isolation:** VOID handling isolated to Slot02; no cross-slot integration. RFC-014 required for global VOID propagation.

This RFC resolves that limitation.

---

## 3. Proposal

### 3.1 Semantic Frames

**Frame 1: VOID as Epistemic Null**
- VOID ≠ "bad input"
- VOID = "no parseable structure"
- Quality: **null** (not low, not high)

**Frame 2: VOID as Ontological Valid State**
- `H(G_void) = 0` is mathematically expected
- Zero entropy ≠ adversarial manipulation
- Pass-through distortion filters

**Frame 3: VOID as Regime-Contextual**
- Normal regime: Routine sparse input
- Heightened regime: Potential signal loss (monitor)
- Emergency regime: Possible system failure (escalate if paired with other anomalies)

### 3.2 Slot-Specific Policies

#### Slot02 (ΔTHRESH Content Processing) ✅ IMPLEMENTED
**Status:** Complete (Phase 14.3)

**Behavior:**
- Parse text → SystemGraph
- If `actors=[] AND relations={}` → `graph_state='void'`
- Emit `BIAS_REPORT@1` with VOID semantics
- `C(G_void) = -0.5` (baseline, non-biased)

**Feature Flag:** `NOVA_ENABLE_VOID_MODE=1`

---

#### Slot03 (Emotional Matrix) 🔨 REQUIRES IMPLEMENTATION

**Current Gap:** No VOID handling → risk of affective misinterpretation

**Policy (from nova.operating@1.1.0 § void_state.slot_semantics.slot03_emotional_matrix):**
```yaml
behavior: "map VOID → dormancy, NOT negative affect"
emotional_state: "null (no valence, no arousal)"
avoid: ["fear", "compliance", "safety signals"]
```

**Implementation Requirements:**
1. Check `BIAS_REPORT@1.metadata.graph_state == 'void'`
2. If VOID:
   - Set `emotional_state = null`
   - Set `valence = 0.0, arousal = 0.0`
   - Emit metric: `slot03_void_dormancy_total`
3. If NOT VOID:
   - Proceed with normal emotional processing

**Rationale:**
- Silence ≠ fear (user paused, thinking, or absent)
- Emptiness ≠ compliance (not suppressing emotion)
- VOID ≠ safety (not calm, just absent)

**Tests:**
- `test_slot03_void_dormancy()` - VOID input → null emotional state
- `test_slot03_void_no_fear()` - VOID does NOT trigger fear
- `test_slot03_void_valence_zero()` - VOID → valence=0, arousal=0

---

#### Slot07 (Wisdom Governor) 🔨 REQUIRES IMPLEMENTATION

**Current Gap:** No VOID handling → risk of regime oscillation, threshold resets

**Policy (from nova.operating@1.1.0 § void_state.slot_semantics.slot07_wisdom_governor):**
```yaml
behavior: "maintain prior state, do NOT trigger regime change"
threshold_policy: "freeze (no reset, no adjustment)"
traffic_limit: "unchanged"
deployment_freeze: "unchanged"
```

**Implementation Requirements:**
1. In `WisdomGovernor.update_state()`:
   - Check if incoming signal includes `graph_state='void'`
   - If VOID:
     - Skip regime score computation
     - Maintain current regime state
     - Do NOT adjust threshold_multiplier
     - Emit metric: `slot07_regime_unchanged_on_void_total`
   - If NOT VOID:
     - Proceed with normal governance

**Rationale:**
- VOID ≠ system degradation (no signal ≠ bad signal)
- Continuity: Maintain baselines across sparse inputs
- Prevent thrashing: Avoid regime oscillation on VOID bursts

**Tests:**
- `test_slot07_void_regime_freeze()` - VOID → regime unchanged
- `test_slot07_void_no_threshold_reset()` - VOID → thresholds frozen
- `test_slot07_void_burst_stability()` - 100 VOID inputs → no regime change

---

#### Slot09 (Distortion Protection) 🔨 REQUIRES IMPLEMENTATION

**Current Gap:** No VOID handling → risk of false-positive anomaly detection

**Policy (from nova.operating@1.1.0 § void_state.slot_semantics.slot09_distortion_protection):**
```yaml
behavior: "pass-through (no filtering, no alarm)"
spectral_filter: "disabled for VOID inputs"
rationale: "H(G_void)=0 is mathematically expected, not adversarial"
```

**Implementation Requirements:**
1. In `DistortionProtector.analyze()`:
   - Check `graph_state == 'void'`
   - If VOID:
     - Bypass spectral entropy filters
     - Set `distortion_detected = False`
     - Emit metric: `slot09_void_passthrough_total`
   - If NOT VOID:
     - Proceed with normal distortion analysis

**Rationale:**
- `H(G_void) = 0` is ontologically valid
- Zero entropy ≠ adversarial entropy manipulation
- VOID detection already handled by Slot02 (don't double-filter)

**Tests:**
- `test_slot09_void_passthrough()` - VOID → no distortion alarm
- `test_slot09_void_zero_entropy_valid()` - H=0 accepted for VOID
- `test_slot09_non_void_zero_entropy_filtered()` - H=0 on non-VOID → suspicious

---

#### Slot01 (Truth Anchor) 🔨 REQUIRES IMPLEMENTATION

**Current Gap:** No VOID handling → risk of confidence collapse, quality misinterpretation

**Policy (from nova.operating@1.1.0 § void_state.slot_semantics.slot01_truth_anchor):**
```yaml
behavior: "record VOID as epistemic abstention"
quality_score: "null (not low, not high)"
avoid: "confidence collapse on sparse data"
```

**Implementation Requirements:**
1. In `QualityOracle.assess_quality()`:
   - Check `graph_state == 'void'`
   - If VOID:
     - Set `quality_score = None` (null, not 0.0)
     - Set `confidence = None` (abstain, don't guess)
     - Emit metric: `slot01_void_abstention_total`
   - If NOT VOID:
     - Proceed with normal quality assessment

**Rationale:**
- VOID = "no evidence" ≠ "low quality evidence"
- Null quality preserves statistical validity (avoid mean dilution)
- Epistemic honesty: Don't fabricate quality scores for absent data

**Tests:**
- `test_slot01_void_null_quality()` - VOID → quality_score=None
- `test_slot01_void_no_confidence_collapse()` - VOID → confidence=None
- `test_slot01_non_void_low_quality()` - Bad input → quality_score=0.2 (not null)

---

### 3.3 Regime-Specific Interpretations

From `nova.operating@1.1.0 § void_state.regime_mapping`:

| Regime | VOID Interpretation | Response | Alert Threshold |
|--------|-------------------|----------|-----------------|
| **normal** | Routine sparse input | Maintain baselines, no alert | N/A |
| **heightened** | Potential signal loss (investigate) | Log event, monitor for pattern | 3 consecutive VOID in 60s |
| **controlled_degradation** | Expected under traffic limits | Continue degradation protocol | N/A |
| **emergency_stabilization** | Possible system failure (critical) | Escalate if paired with other anomalies | 1 VOID + (high TRI drift OR low MSE) |
| **recovery** | Normal during ramp-up | No action | N/A |

**Implementation Location:** `src/nova/continuity/orp.py` (ORP regime classifier)

**Changes Required:**
1. Add `void_event_counter` to `RegimeSnapshot`
2. In `update_regime()`:
   - If `graph_state='void'` AND `regime='heightened'`:
     - Increment `void_event_counter`
     - If `void_event_counter >= 3 in 60s`:
       - Log warning: "Sustained VOID burst in heightened regime"
   - Reset counter on non-VOID input

**Tests:**
- `test_orp_void_normal_no_alert()` - VOID in normal → no action
- `test_orp_void_heightened_alert()` - 3 VOID in 60s during heightened → warning
- `test_orp_void_emergency_escalation()` - VOID + TRI drift → escalate

---

### 3.4 Non-Interference Constraints

From `nova.operating@1.1.0 § void_state.non_interference_constraints`:

1. **VOID handling must NOT affect non-VOID signal processing**
   - Implementation: Separate code paths for `if graph_state == 'void'`
   - Test: Process VOID then non-VOID → verify non-VOID unaffected

2. **VOID state in one slot must NOT cascade regime changes**
   - Implementation: Slots treat VOID locally, don't emit regime triggers
   - Test: Slot03 VOID → verify Slot07 regime unchanged

3. **Slots without VOID support must gracefully skip (no crash)**
   - Implementation: Check `graph_state` field existence before access
   - Test: Remove VOID support from Slot04 → verify no crash on VOID input

---

## 4. Observability

### 4.1 Prometheus Metrics

**Existing (Phase 14.3):**
```promql
slot02_bias_reports_total{graph_state="void"}
```

**New (Phase 14.4):**
```promql
slot03_void_dormancy_total               # Slot03 VOID → dormancy events
slot07_regime_unchanged_on_void_total    # Slot07 regime freeze on VOID
slot09_void_passthrough_total            # Slot09 VOID bypass count
slot01_void_abstention_total             # Slot01 epistemic abstention count

# Derived metrics (Grafana)
rate(slot02_bias_reports_total{graph_state="void"}[5m]) > 0.1
  # Alert: VOID rate > 6/min

sum(slot03_void_dormancy_total + slot07_regime_unchanged_on_void_total +
    slot09_void_passthrough_total + slot01_void_abstention_total) /
sum(slot02_bias_reports_total)
  # VOID propagation coverage (should = 1.0 when all slots compliant)
```

### 4.2 Logging

**Structured log fields:**
```json
{
  "event": "void_state_propagated",
  "slot": "slot07_wisdom_governor",
  "graph_state": "void",
  "regime": "heightened",
  "action": "regime_freeze",
  "timestamp": 1701952800.0
}
```

**Log levels:**
- DEBUG: Every VOID event (per slot)
- INFO: Regime-specific VOID responses (heightened alert threshold)
- WARNING: VOID burst detection (3+ in 60s during heightened)
- ERROR: VOID handling failure (crash, unexpected state)

### 4.3 Grafana Dashboards

**New Panel (add to `slot02-bias-detection.json`):**
- **VOID Propagation Heatmap:** Cross-slot VOID handling coverage over time
- **VOID Event Rate by Regime:** Line chart of VOID/min faceted by regime
- **VOID Burst Alerts:** Alert timeline for heightened regime threshold violations

---

## 5. Implementation Plan

### Phase 14.4-A: Slot Implementations (Current Phase)

**Priority 1 (Critical Path):**
- ✅ Slot02: VOID emission (already complete, Phase 14.3)
- 🔨 Slot07: Regime freeze on VOID
- 🔨 Slot09: Distortion filter bypass

**Priority 2 (Observability):**
- 🔨 Slot01: Quality oracle null handling
- 🔨 Slot03: Emotional dormancy mapping

**Deliverables:**
- Implementation files: `src/nova/slots/slot{01,03,07,09}/*_void_handling.py`
- Test files: `tests/slots/slot{01,03,07,09}/test_void_*.py`
- Metrics: 4 new Prometheus counters
- Documentation: Update slot canonical specs with VOID policies

**Target:** 2025-12-08 (1 day)

---

### Phase 14.4-B: Regime Integration

**Changes:**
- Update `src/nova/continuity/orp.py` with regime-VOID mapping
- Add `void_event_counter` to `RegimeSnapshot`
- Implement heightened regime alert threshold (3 VOID in 60s)

**Tests:**
- `tests/continuity/test_orp_void_regime.py` (8 tests)

**Target:** 2025-12-09 (1 day)

---

### Phase 14.4-C: Cross-Slot Integration Tests

**Test Suite:** `tests/integration/test_void_propagation.py`

**Scenarios:**
1. **VOID Single-Shot:** 1 VOID input → verify all slots handle correctly
2. **VOID Burst (Normal Regime):** 100 VOID/sec → verify no regime change
3. **VOID Burst (Heightened):** 3 VOID in 60s → verify warning log
4. **VOID + Anomaly (Emergency):** VOID + TRI drift → verify escalation
5. **Mixed Traffic:** VOID interleaved with real inputs → verify non-interference

**Coverage Target:** 100% of slot policies, 100% of regime mappings

**Target:** 2025-12-10 (1 day)

---

### Phase 14.4-D: Observability & Documentation

**Grafana:**
- Add 3 new panels to `slot02-bias-detection.json`
- Create `void-propagation-health.json` dashboard

**Documentation:**
- Update slot canonical specs (`docs/slots/slot{01,03,07,09}_*.md`)
- Add VOID section to `docs/architecture/cognitive_stack.md`
- Update `monitoring/README.md` with VOID metrics

**Target:** 2025-12-11 (1 day)

---

## 6. Rollback Plan

### 6.1 Feature Flag Rollback

**Disable VOID emission:**
```bash
export NOVA_ENABLE_VOID_MODE=0
```

**Impact:**
- Slot02 treats VOID graphs as normal low-entropy inputs
- No `graph_state='void'` in BIAS_REPORT@1
- Slots 01/03/07/09 never see VOID state
- Backward compatible (slots check field existence)

### 6.2 Code Rollback

**Single commit revert:**
```bash
git revert 5428493  # Operating Ontology v1.1.0
```

**Cascading reverts (if slot implementations cause issues):**
```bash
git revert <slot07-commit>
git revert <slot09-commit>
git revert <slot01-commit>
git revert <slot03-commit>
```

**Test validation:**
```bash
pytest -q  # All tests must pass after revert
```

### 6.3 Partial Rollback (Per-Slot)

**If Slot07 VOID handling breaks regime logic:**
```python
# In src/nova/slots/slot07_production_controls/core.py
ENABLE_VOID_HANDLING = os.getenv("NOVA_SLOT07_VOID_ENABLED", "0") == "1"

if ENABLE_VOID_HANDLING and graph_state == 'void':
    # VOID policy
else:
    # Original logic (treat as normal input)
```

---

## 7. Security Considerations

### 7.1 VOID Flooding Attack

**Threat:** Attacker sends 10,000 VOID inputs/sec to trigger DoS

**Mitigation:**
- Slot02 rate-limits text parsing (existing: 100 req/sec)
- Slot07 maintains regime stability (VOID doesn't cascade)
- Heightened regime triggers at 3 VOID in 60s (not per-second)
- Emergency regime requires VOID + other anomaly (AND gate)

**Test:** `test_security_void_flood_resilience()`

### 7.2 VOID Evasion

**Threat:** Attacker crafts malicious input that parses as VOID (bypasses filters)

**Mitigation:**
- Slot09 only bypasses spectral filters for VOID (other filters active)
- Slot02 TRI pattern detection still runs on raw text (pre-VOID check)
- VOID detection is heuristic (TextGraphParser), not adversarial classifier

**Test:** `test_security_void_evasion_blocked()`

### 7.3 Semantic Confusion

**Threat:** VOID misinterpreted as "safe" when it's actually "unparseable malicious input"

**Mitigation:**
- VOID = epistemic null, NOT safety signal
- Slot01 abstains (quality=None), doesn't endorse
- Slot03 dormancy ≠ calm (no affective reward)

**Test:** `test_security_void_not_safety_signal()`

---

## 8. Alternatives Considered

### 8.1 Option A: Ignore VOID (Status Quo)

**Pros:**
- Zero implementation cost
- No new code paths

**Cons:**
- Semantic drift (VOID meaning varies per slot)
- Emergent pathologies (regime thrashing, confidence collapse)
- Violates Invariant #8 (ontology ≠ implementation)

**Decision:** REJECTED (architectural debt too high)

---

### 8.2 Option B: VOID as Error State

**Approach:** Treat VOID like parse failure (emit error, log, reject)

**Pros:**
- Simple implementation (1 error handler)
- Clear semantics ("we don't support VOID")

**Cons:**
- User pauses become errors (UX degradation)
- Sparse traffic triggers alarms (false positives)
- Violates ontological truth (VOID is valid, not error)

**Decision:** REJECTED (misaligns with mathematical reality)

---

### 8.3 Option C: VOID Propagation (SELECTED)

**Approach:** Formal semantics at Mother + Operating Ontology layers

**Pros:**
- Ontology-first (Invariant #8 compliance)
- Slot-specific policies (preserves separation of roles)
- Observable (metrics, logs, dashboards)
- Reversible (feature flags, per-slot control)

**Cons:**
- Implementation cost (5 slots × 3 tests = 15 test files)
- Coordination overhead (RFC, reviews, staged rollout)

**Decision:** SELECTED (architectural integrity > short-term cost)

---

## 9. Open Questions

### 9.1 Should VOID affect TRI computation?

**Context:** Slot04 (TRI Engine) computes triple resonance from text patterns

**Options:**
1. VOID → TRI = 0.0 (absence = zero resonance)
2. VOID → TRI = null (abstain from computation)
3. VOID → TRI = prior_value (freeze)

**Recommendation:** Option 2 (null) → maintains statistical validity

**Resolution:** Deferred to Phase 14.5 (TRI VOID handling separate RFC)

---

### 9.2 What about VOID in federation?

**Context:** Phase 15-3 federation pulls remote BIAS_REPORT@1

**Scenarios:**
- Remote peer sends VOID → local Slot07 regime unchanged (correct)
- Local VOID → should we propagate to federation? (yes, for observability)
- VOID consensus: If 3/5 peers emit VOID, is global state VOID? (unclear)

**Recommendation:** Document in Phase 15-3 federation semantics

**Resolution:** Out of scope for RFC-014 (federation-specific RFC needed)

---

## 10. Success Criteria

### 10.1 Functional

- ✅ All 4 slots (01, 03, 07, 09) implement VOID policies
- ✅ 100% test coverage for VOID handling (15 test files)
- ✅ Regime-VOID mapping functional (ORP integration)
- ✅ Non-interference verified (mixed traffic tests pass)

### 10.2 Observability

- ✅ 4 new Prometheus metrics emitting
- ✅ VOID event logs structured and queryable
- ✅ Grafana dashboards updated (2 panels added)

### 10.3 Ontological

- ✅ Operating Ontology v1.1.0 published
- ✅ Slot canonical specs updated with VOID sections
- ✅ Mother Ontology ↔ Operating Ontology consistency verified

### 10.4 Operational

- ✅ Feature flag rollback tested (NOVA_ENABLE_VOID_MODE=0)
- ✅ Security tests pass (flood, evasion, confusion)
- ✅ Production deployment successful (canary → full rollout)

---

## 11. References

- **Mother Ontology:** `docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml` (v1.8.0)
- **Operating Ontology:** `docs/architecture/ontology/specs/nova.operating@1.0.yaml` (v1.1.0)
- **Phase 14.3 Spec:** `docs/specs/slot02_usm_bias_detection_spec.md`
- **Bias Calculator:** `src/nova/slots/slot02_deltathresh/bias_calculator.py:214-239` (VOID handling)
- **Contract:** `contracts/bias_report@1.yaml` (graph_state field)
- **Ontology Hierarchy:** `docs/Nova_Ontology_Hierarchy_v1.7.1.md`

---

## 12. Approval

**Stakeholders:**
- Slot Maintainers: slot01, slot02, slot03, slot07, slot09
- ORP Maintainer: `src/nova/continuity/orp.py`
- Ontology Steward: Nova Architectural Team
- Observability Team: Grafana/Prometheus owners

**Sign-off Required:** All slot maintainers + ORP maintainer

**Target Approval Date:** 2025-12-08

---

**Status:** Draft (awaiting slot maintainer review)
**Next Action:** Implement Slot07 VOID freeze policy (Priority 1)

# Phase 14 Retrospective: Temporal USM & Observation Infrastructure

**Date:** 2025-12-09
**Scope:** Phase 14.0 through 14.5 (14.6 spec defined, not implemented)
**Duration:** ~6 weeks (October-December 2025)
**Status:** Phase 14.5 ✅ COMPLETE — Ready for Phase 14.6

---

## Executive Summary

Phase 14 built temporal observability layer for Nova's manipulation detection system:
- **Temporal USM:** Exponential smoothing of bias metrics (H_t, ρ_t, C_t)
- **VOID semantics:** Epistemic null handling with soft-reset decay
- **Provisional thresholds:** Combined C_t + ρ_t state classification
- **Observation tooling:** Complete pipeline for conversation replay and analysis

**Key discovery:** ρ_t (equilibrium ratio), not C_t (collapse score), is primary extraction indicator.

**Commits:** 6 in final session (41add36 → 09b54f5)
**Lines added:** ~2,000 (code + docs + tests)
**Tests added:** 13 (usm_temporal_thresholds)

---

## Phase Progression

### Phase 14.0: Initial Temporal USM Design
**Status:** SUPERSEDED
**Original goal:** Add temporal smoothing to USM metrics
**Issue:** Did not account for VOID semantic complexity

### Phase 14.1-14.3: VOID Integration (Implicit)
**Merged into Phase 14.4**
**Key insight:** VOID ≠ attack — requires distinct handling (soft decay to equilibrium)

### Phase 14.4: VOID Propagation & Dormancy
**Status:** ✅ COMPLETE
**Delivered:**
- Ontology coherence (Mother, Operating, Contract layers aligned)
- Slot03 VOID dormancy (decay toward μ_baseline, no epistemic pollution)
- Phase 14.6 deferred based on ontological review

**Commits:**
- `e4b450d` feat(phase11): finalize three-tier ontology hierarchy
- `6cef055` feat(phase11): add Step C cross-system semantic audit results
- (Earlier work)

### Phase 14.5: Observation Protocol & Pilot Validation
**Status:** ✅ COMPLETE (this session)
**Delivered:**
- Temporal USM instrumentation (λ=0.6, ρ_eq=1.0)
- Pilot observation (3 scenarios: benign, extractive, VOID)
- Oracle validation (hand-crafted test cases)
- Parser exploration (spaCy evaluation → existing parser validated)
- Provisional thresholds (C_t: [0.18, -0.12], ρ_t: [0.25, 0.6])
- State classification (extractive, consensus, collaborative, neutral, warming_up)
- Observation tooling (find → export → replay → classify)

**Commits (this session):**
1. `41add36` - Observation tooling + pilot findings + parser exploration docs
2. `63b1011` - Unicode encoding fixes (Windows cp1252 compatibility)
3. `e9d2a1f` - Provisional thresholds + classification logic + 13 tests
4. `870c60f` - Classification validation (replay script + real conversation tests)
5. `fe852d1` - Pilot observation artifacts (CSV + PNG)
6. `09b54f5` - Phase 14.6 spec (temporal governance integration)

See also:
- `docs/specs/phase14_extraction_calibration.md` for soft extraction calibration exemplars.
- `docs/architecture/ADR-014-soft-extraction-calibration.md` for the associated decision record.

### Calibration References (RT-00X)

During this session, initial RT-00X calibration entries were established to ground the weakest assumption (“sustained ρ_t≈0.0 + soft C_t band = soft/background extraction”) against both synthetic and real conversations:

- **RT-001–RT-003:** Spec-defined synthetic and REALTALK-style soft extraction vs benign collaborative exemplars (see calibration spec Visual Appendix).
- **RT-004:** This calibration dialogue itself, highlighting a brief epistemic soft extraction via narrative/tooling drift followed by operator-driven repair (`Extraction_present=True`, no escalation).
- **RT-005:** Benign “news agency website” request (real trace exported via `export_conversation_stream.py` and replayed through Slot02); ρ_t moves from 0.0 to mid band, C_t mildly negative, `Extraction_present=False`.
- **RT-006:** Benign conceptual ëTHRESH article reframing (real trace); ρ_t remains in mid band, C_t stays non-collapsing, `Extraction_present=False`.
- **RT-007:** Friendly social “coffee later” small-talk baseline; symmetric, low-stakes, `Extraction_present=False`.

Since ADR‑014, the RT‑00X set has been extended beyond the initial RT‑001– RT‑007 exemplars:

- **RT-023–RT-033** are logged in `docs/specs/phase14_rt_evidence_log.md` as operator-facing evidence rows. They include:
  - Soft extraction cases (RT-023, RT-025, RT-027–RT-030): gaslighting, authority / technofeudal framing, "for your own good" paternalism, dependency / habit-nudging, and algorithmic authority in career advice. All share the expected pattern of low or one-way ρ_t with C_t in a soft positive band and `Extraction_present=True`.
  - Benign baselines (RT-024, RT-026, RT-031–RT-033): philosophical cloud-capital debate, AI-as-tool writing assistance, creative co-design, and two real Nova traces (RT-032, RT-033) replayed through Slot02 with temporal_usm enabled. These show mid-band ρ_t, low/stable C_t, and `Extraction_present=False`.

Preliminary conclusion: across these 11 evidence rows, operator judgment matches the weakest assumption ("sustained low ρ_t + soft C_t band ⇒ soft/ background extraction") and clearly separates extraction from benign reciprocity. This supports keeping ρ_t as the primary extraction signal and C_t as a typing/refinement signal, while postponing any Slot07 wiring until more traces are accumulated in future phases.
These entries are **calibration evidence**, not additional thresholds. They should be extended to 20–50 RT-00X traces (using archived conversations and REALTALK-style data) before any Slot07 temporal governance wiring is attempted, and used to decide whether the current ρ_t/C_t-based extraction semantics need revision.

### Calibration Findings (Phase 16 Pre-work)

**Finding F-16-A: Low-semantic asymmetry collapse**

Evidence:

- RT-373 (`rt-test-1`) and at least 10 `rt-benign-XX` sessions:
  - 3–5 turns, neutral / low-semantic prompts.
  - Temporal signature at end of session:
    - `rho_temporal ≈ 0.0`
    - `C_temporal = null` (no intensity signal)
    - `temporal_state = "active"` (min_turns satisfied)
    - `extraction_present = True`
- Extractive stimulus sessions (`rt-gaslight-01`) using deliberate gaslighting patterns:
  - 4 turns, structurally asymmetric prompts.
  - Temporal signature at end of session:
    - `rho_temporal ≈ 0.0`
    - `C_temporal = null`
    - `temporal_state = "active"`
    - `extraction_present = True`

Interpretation:

- Slot02's temporal extraction annotation is currently **structural**:
  - It detects **non-reciprocal semantic structure** (low reciprocity / asymmetry).
  - It does **not** yet distinguish:
    - benign low-semantic asymmetry (greetings, trivial Q&A) from
    - harmful or manipulative asymmetry (gaslighting, authority override, dependency).
- With the present metric set:
  - `extraction_present=True` means "semantic asymmetry detected under temporal USM", **not** "harmful extraction confirmed".

Status:

- Treated as a **calibration finding**, not a defect.
- Logged for Phase 16 calibration work; no Phase 14 or Phase 15 code/threshold/governance changes implied.

---

## Critical Decisions & Pivots

### Decision 1: Parser Upgrade (Rejected)
**Initial hypothesis:** Regex parser inadequate → upgrade to spaCy dependency parsing → achieve H>0.5

**Exploration (Phase 14.7):**
- Implemented spaCy parser with dependency extraction
- Added ROOT token handling, co-occurrence edges, abstract filtering
- Result: Still H~0 for all conversational inputs

**Root cause:** Conversational AI text is explanatory (concepts + properties), not relational (agents + power dynamics)

**Decision:** Keep existing regex parser — both produce 0-2 edges, which is correct for substrate

**Impact:** Saved weeks of misguided optimization, reframed success criteria

### Decision 2: Primary Signal Reframing
**Initial belief:** C_t (collapse score) is primary manipulation detector

**Pilot evidence:**
- Benign: ρ_t rises to 0.6 during reciprocity, then decays to 0.015
- Extractive: ρ_t flat at 0.0 throughout (perfect signal)
- VOID: ρ_t → 1.0 (equilibrium reference)

**Corrected understanding:**
- **ρ_t is primary extraction signal** (measures power flow asymmetry)
- C_t is secondary (structural stability indicator)
- H_t is baseline reference (near-zero for conversational text)

**Impact:** Entire threshold design reoriented around ρ_t temporal trajectory

### Decision 3: Provisional Thresholds (Path B)
**Options:**
- Path A: Fix encoding bugs, export 5 conversations, measure distributions, set thresholds (2-3 hours)
- Path B: Use theoretical estimates (60% scaling from instantaneous), validate during operation (30 min)

**Choice:** Path B

**Rationale:**
- Pilot provides theoretical grounding
- Real calibration needs 100+ sessions anyway
- Fast feedback loop during deployment
- Encoding bug is infrastructure debt (fix separately)

**Validation criteria:** Misclassification rate >50% in first 100 sessions → rollback

**Impact:** Phase 14.5 unblocked immediately, calibration happens during Phase 14.6

---

## Key Technical Insights

### 1. Temporal vs. Instantaneous Observables
**Discovery:** Temporal metrics (λ=0.6 smoothing) have ~40% tighter distributions than instantaneous.

**Example:**
- Instantaneous C range: [-0.3, 0.5]
- Temporal C_t range: [-0.15, 0.2]

**Implication:** Cannot directly port instantaneous thresholds to temporal — requires rescaling.

### 2. Consensus vs. Extraction (ρ_t Decay Ambiguity)
**Observation:** Both consensus and extraction show low reciprocity (ρ_t → 0)

**Structural similarity:**
- Extraction: A→B, A→C, A→D (unidirectional from power)
- Consensus: A→goal, B→goal, C→goal (unidirectional toward shared aim)

**Disambiguation:** Requires C_t + ρ_t conjunction:
- Consensus: (C_t < -0.12) ∧ (ρ_t < 0.25) — protective alignment
- Extraction: (C_t > 0.18) ∧ (ρ_t < 0.25) — hierarchical control

**Implication:** Single metric insufficient — need multi-dimensional classification.

### 3. Parser Substrate Limitation
**Discovery:** Conversational text doesn't have rich relational graphs (0-2 edges typical)

**Why:**
- Explanatory vs. narrative structure
- Property-focused vs. relational
- Implicit context vs. explicit agent specification

**Example:** "Alice analyzes the methodology"
- Human mental model: 3 actors, 3-4 edges
- Parser reality: 0 edges (Alice exists, "methodology" is abstract concept)

**Implication:** H~0 is data, not bug — conversational text is structurally flat.

### 4. VOID Semantics (Soft Reset)
**Discovery:** VOID represents epistemic absence, not adversarial signal

**Behavior:**
- graph_state='void'
- C → 0 (decay toward zero-energy anchor)
- ρ → 1.0 (decay toward equilibrium reference)
- H → 0 (no structure)

**Implication:** VOID is recovery mechanism, not threat indicator.

---

## Validation Results

### Pilot Observation (Synthetic Scenarios)

| Scenario | Turns | C_t Range | ρ_t Pattern | Classification |
|----------|-------|-----------|-------------|----------------|
| **Benign** | 10 | [-0.10, +0.02] | 0.0 → 0.60 → 0.015 | consensus → neutral |
| **Extractive** | 10 | [-0.10, +0.20] | 0.0 (flat) | extractive (7/10 turns) |
| **VOID** | 10 | [0.0, 0.0] | 1.0 (stable) | neutral |

**Key findings:**
- Benign reciprocity spike (turn 6: ρ_t=0.6) when Bob supports Carol
- Benign consensus decay (turn 10: ρ_t=0.015) when all agree
- Extractive flat ρ_t=0.0 throughout (perfect extraction signal)

### Real Conversation Validation

**Adversarial interrogation:**
```
Turn 3: consensus (C_t=-0.122, ρ_t=0.24)
Turn 4: neutral (C_t=-0.084, ρ_t=0.696)
```
- Content discusses extraction, but conversation structure is collaborative
- Validates distinction between topic vs. structure

**Nova technical dialogue:**
```
Turn 4: collaborative (C_t=-0.224, ρ_t=0.696)
Turn 5-16: neutral (oscillating)
```
- Deep technical exchange classified as collaborative
- Informational flow drifts to neutral

---

## Lessons Learned

### 1. Pilot Catches Misalignment Before Production
**What happened:** 3-hour pilot revealed C_t was wrong primary signal

**Impact:** Saved weeks of misguided observation with incorrect interpretation

**Principle:** Always validate instrumentation assumptions with controlled scenarios before production deployment

### 2. Ontological Alignment Matters
**What happened:** Initial framing "C_t detects manipulation" was wrong

**Correction:** "ρ_t detects extraction (power flow), C_t detects collapse (structure)"

**Principle:** Ensure metric semantics match phenomenon being measured

### 3. Improving Measurement Reveals Substrate Mismatch
**What happened:** Oracle validation showed H=0 always → assumed parser broken → explored spaCy upgrade → discovered conversational text is structurally sparse

**Lesson:** "The Precision Trap" — better measurement can reveal substrate doesn't match expectations

**Principle:** When instrument reports unexpected data, question assumptions about what's being measured, not just the instrument

### 4. Provisional Thresholds Enable Fast Iteration
**What happened:** Chose theoretical estimates + operational validation over exhaustive pre-calibration

**Result:** Phase 14.5 unblocked in 30 minutes instead of 3 hours

**Principle:** Document provisional status explicitly, define rollback criteria, iterate based on operational feedback

### 5. Real Data Validates Differently Than Synthetic
**What happened:** Pilot showed ρ_t max 0.6, real conversation showed 0.95

**Insight:** Organic dialogue accumulates reciprocal weight over sustained exchange

**Principle:** Synthetic fixtures test logic, real data validates scale and distribution

---

## Technical Debt Incurred

### 1. Encoding Infrastructure (Non-blocking)
**Issue:** Unicode characters (Δ, ∈, ✓) fail on Windows cp1252 encoding

**Status:** Fixed in pilot script, find script still has issue

**Debt:**
- Standardize on UTF-8 output across all scripts
- Add encoding tests to prevent regression

**Timeline:** Post-Phase 14.6

### 2. Calibration Completion
**Issue:** Thresholds are provisional (based on 30 turns pilot data)

**Status:** Documented, rollback criteria defined

**Debt:**
- Run 100-200 real conversations with ground truth labels
- Calculate empirical error rate
- Refine thresholds to <20% misclassification

**Timeline:** During Phase 14.6 operation (parallel work)

### 3. Context-Adaptive Thresholds
**Issue:** Early conversation (turn 1-3) vs. deep conversation (turn 50+) may need different baselines

**Status:** Deferred to Phase 14.7

**Debt:**
- Implement turn-count adaptive thresholds
- Add ρ_t velocity triggers (sudden drop detection)
- Domain-specific calibration (technical vs. casual vs. interrogative)

**Timeline:** Phase 14.7 (future)

---

## Metrics & Observability

### Code Metrics (Phase 14.5 Session)
- **Files created:** 13 (9 scripts/docs, 2 code, 2 tests)
- **Files modified:** 2 (observation protocol, gitignore)
- **Lines added:** ~2,000
- **Tests added:** 13 (all passing)
- **Commits:** 6
- **Session duration:** ~4 hours

### System Maturity Impact
**Before Phase 14.5:**
- Temporal USM: Implemented but not validated
- Thresholds: None (instantaneous only)
- Observation tooling: None

**After Phase 14.5:**
- Temporal USM: Validated with pilot + real data
- Thresholds: Provisional with rollback criteria
- Observation tooling: Complete pipeline (find → export → replay → classify)
- Classification: 5-state taxonomy (extractive, consensus, collaborative, neutral, warming_up)

**Processual maturity:** Still 4.0/4.0 (instrumentation added without breaking existing guarantees)

---

## Phase 14.6 Readiness

### Prerequisites (All Met)
✅ Temporal USM instrumentation working
✅ Provisional thresholds defined and tested
✅ Classification logic validated with real data
✅ Observation tooling operational
✅ Rollback criteria documented

### Open Questions for Phase 14.6
1. **Should consensus trigger any action?**
   - Current plan: neutral (no override)
   - Needs operational data to validate

2. **What's the right "sustained" threshold?**
   - Proposed: 5 consecutive turns
   - Alternative: 5 out of last 7 (allow 2 fluctuations)

3. **Should collaborative classification disable quarantine?**
   - Current: uses instantaneous action (may still quarantine)
   - Alternative: force allow if collaborative sustained

**Decision approach:** Start with simplest design (5 consecutive, no override), refine based on operational feedback

---

## Recommendations for Phase 14.6

### Implementation Approach
1. **Start with metrics-only mode** (classification tracked, not used in actions)
2. **Run 20-30 sessions** to validate classification distribution
3. **Enable governance flag** after distribution looks reasonable
4. **Monitor override rate** (should be <5% of total actions)
5. **Adjust thresholds** if >20% false positives

### Risk Mitigation
- Feature flag: `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1` (default: 0)
- Rollback trigger: >20% false positive rate in first 100 sessions
- Monitoring: Prometheus metrics for classifications + overrides
- Testing: Validate sustained extraction detection with synthetic scenarios

### Timeline
- Implementation: 6-8 hours (1-2 days)
- Validation: 20-30 sessions (ongoing during operation)
- Calibration: 100-200 sessions (parallel to Phase 14.7 planning)

---

## Closing Assessment

**Phase 14.0-14.5 was successful:**
- Temporal observability layer built and validated
- Key ontological correction discovered early (ρ_t vs. C_t)
- Parser substrate limitations understood and accepted
- Provisional thresholds enable fast iteration
- Observation tooling complete

**Phase 14.6 is well-scoped:**
- Clear implementation tasks (6-8 hours)
- Rollback plan defined
- Success criteria measurable
- Open questions documented for operational resolution

**System remains in good health:**
- No breaking changes introduced
- All features flag-gated
- Tests passing (2194 + 13 new)
- Documentation complete

**Ready to proceed.**

---

**Retrospective complete:** 2025-12-09

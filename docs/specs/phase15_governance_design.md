# Phase 15: Temporal Governance Design Specification

**Status:** Design complete (Sections D, A, B, C locked)  
**Governance state:** NOVA_ENABLE_TEMPORAL_GOVERNANCE=0 (all flags OFF, design-only phase)  
**Dependencies:** Phase 14 calibration complete (min_turns=3, extraction_present validated)

---

## 1. Scope

Phase 15 designs Slot07 temporal governance semantics as **specification work only**. No implementation, no activation, no user-facing changes.

**Non-goal:** Phase 15 does not attempt to optimize user experience, safety outcomes, or enforcement effectiveness. Its sole goal is to preserve epistemic integrity under temporal governance.

**Design principle:** Governance as restraint—define what Slot07 must never do before defining what it may do.

**Methodology:** Structure first, calibration later, power last.

---

## 2. Negative Capability (Inviolable Constraints)

Slot07 MUST NEVER:

1. Override extraction_present=None with a forced interpretation (ambiguity must propagate, not collapse)
2. Take automated action based on extraction_present alone (input to judgment, not action trigger)
3. Hide extraction signals from operator/user (all values including None must be observable)
4. Operate without explicit operator veto path (human authority always available)
5. Persist extraction labels across sessions without review (per-turn temporal signal only)
6. Activate temporal governance without feature flag OFF by default (rollback = flag flip)

---

## 3. Section D: None-Handling Rules (Locked)

**Design principle:** Before Slot07 can decide what to do, it must decide what it is allowed to not know.

### 3.1 Eligibility Rules

When extraction_present=None:

| Regime             | Allowed | Justification                                                  |
|--------------------|---------|----------------------------------------------------------------|
| Observational      | ✓ Yes   | Log ambiguity, no action. Always safe.                        |
| Informational      | ✗ No    | Cannot inform user of extraction when system is uncertain.    |
| Consent-reinforcing| ✗ No    | Cannot request consent based on undefined extraction.         |
| Escalation         | ✓ Yes   | May be triggered by explicit operator configuration, not automated logic. |

**Core rule:** When extraction_present=None, Slot07 MUST remain in Observational regime unless explicitly overridden by operator policy.

### 3.2 Interaction with C_t

**Question:** If extraction_present=None but C_t is high, does that change governance

**Answer:** No. extraction_present dominates C_t.

**Rule:** When extraction_present=None, C_t is ignored for regime selection. C_t types intensity of extraction; if extraction existence is undefined, intensity is meaningless.

**Exception:** C_t may still be logged for operator review, but does not influence regime.

### 3.3 Temporal Persistence

**Question:** Does repeated extraction_present=None for many turns signal something

**Answer:** No. None is stateless.

**Rule:** extraction_present=None is stateless—repeated None does not accumulate into a different signal. Slot07 treats turn 1 None identically to turn 100 None.

**Escape hatch:** Operator may configure "review after N consecutive None" as policy override (logging/alerting only, not regime change).

### 3.4 Propagation Rule

**Core rule:** When extraction_present=None, no other signal may escalate governance regime beyond Observational, unless explicitly permitted by operator policy.

**Principle:** Ambiguity dominates certainty.

**Anti-pattern (forbidden):**
```python
if extraction_present is None and session_history_has_extraction:
    regime = Informational  # WRONG: collapses ambiguity
```

**Correct pattern:**
```python
if extraction_present is None:
    regime = Observational  # Ambiguity dominates
    log_context(other_signals)  # Context logged, not acted upon
```

### 3.5 Litmus Tests

All test cases with extraction_present=None resolve to Observational:

| Scenario                    | extraction_present | C_t  | Expected Regime |
|-----------------------------|--------------------|------|-----------------|
| Turn 2 (warming up)         | None               | 0.8  | Observational   |
| Mid-band ρ_t, stable        | None               | 0.3  | Observational   |
| 2-turn benign (RT-032)      | None               | 0.1  | Observational   |
| 15 turns, all None          | None               | varies | Observational |
| None + past extraction history | None            | any  | Observational   |

**Validation:** All None cases stay Observational. This preserves epistemic integrity.

---

## 4. Section A: Regime Decision Matrix (Locked - Phase 15 Baseline)

**Design constraint:** This matrix is undefined for extraction_present=None by design. None-handling follows Section D rules.

**Provisional baseline:** C_t thresholds (0.3, 0.7) and regime granularity are provisional. May be recalibrated in Phase 16 after governance semantics and operator workflows are validated.

### 4.1 Input Space

**Inputs:**
- extraction_present ∈ {True, False} (None excluded by design)
- C_t (coherence_temporal):
  - Low: ≤ 0.3 (soft background extraction)
  - Mid: 0.3 - 0.7 (transitional)
  - High: ≥ 0.7 (hard collapse/intensity)

**Excluded inputs:**
- Session history (forbidden: violates per-turn semantics)
- User/session labels (forbidden: no persistent labeling)
- Other slot outputs (may inform operator review, not matrix)

### 4.2 Output Space (Regime Definitions)

1. **Observational:** Log to metrics/attest ledger only. No user-facing changes.
2. **Informational:** Log + optional transparency disclosure (e.g., "This interaction shows low reciprocity"). User-dismissible, no behavior change.
3. **Consent-reinforcing:** Log + consent reminder UI (e.g., "Would you like to continue"). User always has "yes, continue" option. Non-coercive.
4. **Escalation:** Log + flag for operator review. No automated user-facing action. Operator decides intervention.

### 4.3 Decision Matrix

| extraction_present | C_t            | Regime              | Justification |
|--------------------|----------------|---------------------|---------------|
| False              | any            | Observational       | Reciprocal/benign pattern detected. No governance needed. C_t irrelevant under benign classification. |
| True               | low (≤0.3)     | Informational (optional) | Soft extraction. Transparency disclosure only. User-dismissible. |
| True               | mid (0.3-0.7)  | Consent-reinforcing (optional) | Moderate extraction. Gentle consent check. Non-coercive. |
| True               | high (≥0.7)    | Escalation          | Hard extraction + high intensity. Operator review (not enforcement). |

### 4.4 Documented Assumptions

1. **C_t thresholds (0.3, 0.7) are Phase 14.5 pilot-derived**, not yet validated against RT evidence  
2. **extraction_present=False always → Observational**: C_t does not escalate governance when reciprocity is established  
3. **Informational vs Consent-reinforcing distinction is meaningful**: Transparency and consent are ethically different acts

### 4.5 Constraints Check

**Compliance with Section D:**
- ✓ No None rows in matrix
- ✓ No history-dependent transitions
- ✓ False doesn't escalate beyond Observational
- ✓ True with low/mid C_t doesn't auto-block

**Compliance with Negative Capability:**
- ✓ No automated action without operator policy
- ✓ Escalation is review-only, not enforcement
- ✓ No permanent labeling (per-turn regime)

---

## 5. Section B: Operator Interface (Locked)

**Core constraint:** Make ambiguity legible without making it feel urgent.

### 5.1 Primary Display: extraction_present States

Three distinct semantic presentations, not a spectrum.

| extraction_present | Label                | Semantic Frame                      | Visual Treatment                      |
|-------------------|----------------------|-------------------------------------|---------------------------------------|
| True              | "Extraction detected"| Factual observation (not alarm)     | Amber/yellow (caution), ⚠️ or ⓘ icon  |
| False             | "Reciprocal pattern" | Positive confirmation               | Green/neutral, ✓ or ⟳ icon            |
| None              | "Pattern undefined"  | Neutral epistemic state             | Gray/neutral (not empty), ○ or ○ icon |

**Anti-patterns (forbidden):**
- None shown as blank/empty (implies missing data)
- None shown as "—" or "N/A" (implies irrelevant)
- None colored invisibly (white on white)
- True shown in red (implies danger vs observation)
- False and None share same visual treatment

**Key rule:** None must have equal visual weight to True and False. It is a state, not an absence.

### 5.2 Context Panel: Temporal Metrics Display

Metrics table shown per session/turn:

| Metric             | Value             | Interpretation                               |
|--------------------|-------------------|----------------------------------------------|
| extraction_present | True/False/None   | Current classification                       |
| ρ_t (rho_temporal) | 0.23              | Temporal equilibrium ratio                   |
| C_t (coherence_temporal) | 0.45        | Coherence/intensity                          |
| Turn count         | 5                 | Turns since session start                    |
| Temporal state     | active/warming_up/void | Classifier state                        |
| Current regime     | Observational/Informational/etc | Governance mode                   |

**Interpretation helpers (on hover/expand):**
- ρ_t: "Lower values indicate asymmetric patterns; higher values indicate reciprocal dynamics"
- extraction_present=None: "Pattern is ambiguous or insufficient data for classification"
- C_t: "Coherence/intensity measure; only meaningful when extraction_present is True or False"

**Forbidden interpretations:**
- "extraction_present=None means safe" (collapses None → False)
- "extraction_present=None requires investigation" (collapses None → urgency)
- C_t interpretation shown when extraction_present=None

### 5.3 Regime Indicator

Current governance regime displayed separately from extraction_present.

**For each regime, show:**
- Regime name
- Operational meaning (logging/transparency/consent/review)
- Reason for regime (extraction_present value, operator policy, or default)

**Example: Observational (due to None)**
Regime: Observational  
Reason: Pattern undefined (extraction_present=None)  
Actions: Metrics logged, no user-facing changes

**Example: Escalation (due to True + high C_t)**
Regime: Escalation  
Reason: Hard extraction detected (ρ_t=0.12, C_t=0.78)  
Actions: Flagged for operator review (no automated enforcement)  
Status: [Review Queue] [Mark Reviewed] [Override]

**Key rule:** Regime and extraction_present shown separately. Operator sees both "what was detected" and "what governance is doing."

### 5.4 Temporal View: How None Persists Over Turns

Turn history table (example):

| Turn | extraction_present | ρ_t | C_t | Regime        | Notes                         |
|------|--------------------|-----|-----|---------------|-------------------------------|
| 1    | None               | —   | —   | Observational | Warming up                    |
| 2    | None               | 0.42| 0.31| Observational | Warming up                    |
| 3    | None               | 0.45| 0.28| Observational | Mid-band ρ_t                  |
| 4    | None               | 0.48| 0.33| Observational | Mid-band ρ_t                  |
| 5    | False              | 0.62| 0.22| Observational | Reciprocal                    |

**Visual treatment of repeated None:**
- Each None shown identically (no color intensification)
- No "streak counter" (e.g., "5 consecutive None")
- No trend arrows or progression indicators
- Notes column explains why None (warming up vs mid-band vs insufficient data)

**Anti-pattern (forbidden):**
⚠️ Ambiguous pattern for 10 turns - Consider manual review  
Creates urgency from None. Violates core constraint.

**Correct pattern:**
Pattern undefined (mid-band ρ_t) - Turn 10 of session  
Factual, no implied action.

### 5.5 Operator Controls

**Per-Session Controls:**
- Manual override: Force regime to Observational (veto escalation)
- Mark for review: Add session to review queue manually
- View full context: Expand to see all temporal metrics, session history, slot outputs

**Policy Configuration:**
- Regime thresholds: Adjust C_t boundaries (Phase 16)
- Enable/disable regimes: Turn off Informational/Consent-reinforcing globally
- Review triggers: Configure "flag after N turns of repeated None" (logging only, not regime change)

**Review Queue (for Escalation regime):**
- List of sessions flagged for review (due to True + high C_t)
- Per-item actions: View context, mark reviewed, override regime, escalate to external process

**Key rule:** All controls are operator-initiated. No UI nags, no automatic prompts, no "recommended actions."

### 5.6 Information Hierarchy

Operator sees in priority order:
1. Session summary: extraction_present state, current regime
2. Current turn metrics: ρ_t, C_t, turn count
3. Regime justification: Why this regime was selected
4. Operator controls: What actions are available
5. Turn history: Temporal progression (expandable)
6. Full context: All slot outputs, session metadata (expandable)

### 5.7 Aggregation & Filtering

**Decision:** Allow filtering, prohibit salience amplification.

**Rules:**
1. Filtering as neutral query tool only  
   - Allowed: "Show sessions where extraction_present = None"  
   - Forbidden: Highlight, prioritize, rank, or badge by extraction_present

2. No default filters  
   - Default view: unfiltered, chronological or session ID order  
   - Operator must actively select filter each time

3. No count-based emphasis  
   - Forbidden: "12 sessions with None" or "Spike in ambiguous sessions"  
   - Allowed: Plain list, no aggregate totals emphasized

4. None is not a risk category  
   - Filter label: "Sessions with undefined extraction state (neutral filter)"  
   - Not: "Ambiguous cases" or "Uncertain patterns"

**Principle:** Ambiguity can be seen, but not made loud.

### 5.8 Notifications

**Decision:** Pull, not push. No notifications by default.

**Rules:**
1. Escalation creates queue entry, not alert  
   - Review queue exists and is visible  
   - No pop-ups, sounds, banners, or emails

2. Operator-initiated checking  
   - Operator opens review queue when they choose  
   - System never interrupts

3. Optional policy override (deferred to Phase 16)  
   - If notifications ever exist: digest-based only (e.g., daily summary), never real-time, never phrased as urgency

4. Notification language constraint  
   - Allowed: "New item added to review queue"  
   - Forbidden: "Action required," "Potential harm detected," "Urgent review needed"

**Principle:** Governance as restraint, not reaction. Human judgment stays sovereign.

### 5.9 Deferred to Phase 16

- Dashboard vs per-session view architecture (operational detail)
- Real-time vs retrospective interface (operational detail)

---

## 7. Phase 16: Validation and Activation (Not Started)

**Pending work:**
- C_t threshold calibration against RT evidence
- 4-stage activation sequence (logging → UI → escalation → full)
- Regime effectiveness evaluation
- Operator workflow feedback
- Rollback criteria definition

---

## 6. Section C: Flag Architecture (Locked)

**Scope:** Define governance activation layers with clean separation and immediate rollback.

### 6.1 Flag Hierarchy

Three-layer separation:

```
NOVA_ENABLE_TEMPORAL_GOVERNANCE (master switch)
  ├── NOVA_ENABLE_EXTRACTION_LOGGING (metrics/attest only)
  ├── NOVA_ENABLE_EXTRACTION_UI (user-facing transparency/consent)
  └── NOVA_ENABLE_EXTRACTION_ESCALATION (operator review queue)
```

**Dependency rules:**
- UI and Escalation require TEMPORAL_GOVERNANCE=1
- UI and Escalation are independent of each other
- Logging is implicit when TEMPORAL_GOVERNANCE=1

### 6.2 Flag Definitions

#### NOVA_ENABLE_TEMPORAL_GOVERNANCE
- **Type:** Boolean
- **Default:** 0 (OFF)
- **Effect when 1:**
  - Slot07 reads temporal_usm and extraction_present from Slot02
  - Regime selection logic active (per Section A matrix)
  - All regimes log to metrics/attest ledger
  - No user-facing changes unless sub-flags enabled
- **Effect when 0:**
  - Slot07 ignores temporal_usm
  - No regime selection
  - extraction_present still computed by Slot02 but not consumed
- **Rollback:** Flip to 0, restart service. Governance stops immediately.

#### NOVA_ENABLE_EXTRACTION_LOGGING
- **Type:** Boolean (implicit when TEMPORAL_GOVERNANCE=1)
- **Default:** 1 (ON when governance enabled)
- **Effect when 1:**
  - extraction_present, ρ_t, C_t, regime → Prometheus metrics
  - Regime transitions → attest ledger
  - Operator dashboard can query metrics
- **Effect when 0:**
  - Regime selection still occurs (Section A logic runs)
  - Metrics not exported
  - Use case: governance dry-run without observability overhead
- **Rollback:** Flip to 0. Metrics stop, governance logic continues.

#### NOVA_ENABLE_EXTRACTION_UI
- **Type:** Boolean
- **Default:** 0 (OFF)
- **Requires:** TEMPORAL_GOVERNANCE=1
- **Effect when 1:**
  - Informational regime → transparency disclosure shown to user
  - Consent-reinforcing regime → consent reminder UI shown to user
  - User can always dismiss/continue (non-coercive)
- **Effect when 0:**
  - Informational and Consent-reinforcing regimes selected but not shown
  - User sees no extraction-related UI
  - Regimes still logged
- **Rollback:** Flip to 0. User-facing changes stop immediately, logging continues.

#### NOVA_ENABLE_EXTRACTION_ESCALATION
- **Type:** Boolean
- **Default:** 0 (OFF)
- **Requires:** TEMPORAL_GOVERNANCE=1
- **Effect when 1:**
  - Escalation regime → session added to operator review queue
  - Operator can view queue, mark reviewed, override regime
  - No notifications (pull model per Section B)
- **Effect when 0:**
  - Escalation regime selected but queue entry not created
  - Regime still logged
  - Use case: validate Escalation logic without operator workflow
- **Rollback:** Flip to 0. Queue stops populating, existing queue persists for review.

### 6.3 Activation Sequence (Phase 16)

**Phase 15 (current):** All flags 0. Design only.

**Phase 16 validation stages:**

1. **Stage 1: Logging only**
   - TEMPORAL_GOVERNANCE=1, EXTRACTION_UI=0, EXTRACTION_ESCALATION=0
   - Validate: Regime selection logic, metrics quality, no user impact

2. **Stage 2: UI piloting**
   - TEMPORAL_GOVERNANCE=1, EXTRACTION_UI=1 (limited sessions, operator-selected), EXTRACTION_ESCALATION=0
   - Validate: Informational/Consent UX, user response, no escalation overhead

3. **Stage 3: Escalation workflow**
   - TEMPORAL_GOVERNANCE=1, EXTRACTION_UI=1, EXTRACTION_ESCALATION=1 (limited sessions)
   - Validate: Operator review queue, workflow efficiency, false positive rate

4. **Stage 4: Full activation (if validated)**
   - All flags=1, all sessions
   - Continuous monitoring for rollback criteria

**Each stage requires explicit validation gate before proceeding.**

### 6.4 Rollback Strategy

**Immediate rollback (<1 minute):**
- Flip TEMPORAL_GOVERNANCE=0 → all governance stops
- Or flip sub-flags individually to reduce scope
- No code deployment required

**Rollback triggers (Phase 16):**
- False positive rate > threshold (TBD during validation)
- User complaint rate > baseline
- Operator override frequency > X% (indicates matrix miscalibration)
- Any evidence that None is being treated as urgent by operators (UX leak)

**Rollback procedure:**
1. Set flag(s) to 0
2. Restart service (or wait for config hot-reload if implemented)
3. Verify metrics show governance inactive
4. Post-mortem: analyze why rollback was needed, revise design

**No data loss on rollback:**
- Attest ledger preserves all regime decisions
- Metrics history retained
- Can replay sessions to debug

### 6.5 Flag Configuration

**Storage:** Environment variables or config file (e.g., `.env`, `config.yaml`)

**Hot-reload capability (optional, Phase 16):**
- Flags checked at call-time, not boot-time
- Allows flag changes without service restart
- Adds complexity; defer unless needed

**Monitoring:**
- Expose flag states via `/metrics` endpoint
- Alert if flags change unexpectedly (detect config drift)

### 6.6 Non-Goals for Flag Architecture

**Not doing (intentionally):**
- ✗ Per-session flag overrides (too complex, violates uniformity)
- ✗ A/B testing framework (governance is not an experiment with users)
- ✗ Gradual rollout percentages (use operator-selected sessions in Stage 2/3 instead)
- ✗ Flag dependencies enforced in code (document dependencies, trust operators)

**Simplicity over flexibility.**

---


## 6. References

- Phase 14 calibration: docs/specs/phase14_min_turns_calibration.md
- Slot02 extraction spec: docs/specs/slot02_usm_bias_detection_spec.md
- Temporal thresholds: src/nova/math/usm_temporal_thresholds.py
- ADR-014: Soft extraction calibration decision

---

## Phase 16 – Open Calibration Questions

**Q16-01 – Short, low-semantic sessions with low rho_t**

For short, low-semantic sessions where rho_t is low and C_t is null,
should `extraction_present=True` require additional conditions (e.g.
minimum semantic mass, longer duration, or non-null C_t), or is asymmetry
alone sufficient?

**Status:** Open (answer required before Phase 16 activation).

---

**Document status:** D, A, B, and C locked. Governance remains off (design-only phase).

---

END OF CONTENT BLOCKS

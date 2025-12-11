# Phase 14 - Soft Extraction Around Sensitive Data (Calibration Set)

**Status:** CANDIDATE  
**Phase:** 14.5-14.6 (Temporal USM + Temporal Governance)  
**Scope:** Soft extraction patterns around sensitive data (personal, financial, cultural/identity)  
**Linked Specs:** `phase14_5_temporal_usm_spec.md`, `phase14_5_observation_protocol.md`, `phase14_retrospective.md`, `phase14_6_temporal_governance.md`

---

## 1. Purpose

This calibration set defines **soft extraction exemplars** for dialogues around sensitive data. It is intended to:

- Provide concrete examples where **structural extraction is present** even though conversations may appear neutral or "helpful".
- Tie **temporal USM metrics** (`H_t`, `?_t`, `C_t`) to **desired extraction semantics** (`Extraction_present` vs `Extraction_type`).
- Surface **philosophical manipulation tactics** (pressure, false authority, emotional leverage, value exploitation) that reduce autonomy and consent quality.
- Prepare integration hooks for **ARC analytic instruments** (PAD.E.L psychological filter, INF-o-INITY informational filter) as defined in the ontology, without assuming they are fully implemented.

This document is a calibration reference for operators and future Phase 14.x work. It does **not** change runtime behavior.

---

## 2. Assumptions & Scope

- **Weakest assumption:** the six exemplars (S1-S3, R1-R3) are representative of the soft extraction patterns Nova will encounter around sensitive data in early deployment. This must be re-evaluated after the first 20-50 operational sessions.

- **Scope:**
  - Slot02 temporal USM (`H_t`, `?_t`, `C_t`) and its classifier (`classify_temporal_state`).
  - Planned ARC analytic instruments (PAD.E.L, INF-o-INITY) as **consumers** of these calibrations.
  - Ethical notions of autonomy, rational deliberation, and consent validity as described in philosophical manipulation analysis.

- **Non-goals:**
  - No changes to current thresholds or temporal governance logic.
  - No claim that PAD.E.L / INF-o-INITY are implemented; they are treated as future integration points (see `docs/compliance/audits/IMPLEMENTATION_AUDIT.md`).

---

## 3. Interpretation Guidelines

### 3.1 Extraction_present vs Temporal State Labels

- `Extraction_present (desired)` is a **?_t-based flag**:
  - True when ?_t is sustained near 0.0 over multiple turns and the graph is non-VOID.
  - False when reciprocity is present (?_t in a benign band) or structure is absent (VOID).

- Current `StateClass` labels (`"warming_up"`, `"extractive"`, `"consensus"`, `"collaborative"`, `"neutral"`) in `src/nova/math/usm_temporal_thresholds.py` are **C_t + ?_t gates**:
  - Extractive: `C_t >= 0.18` and `?_t < 0.25` (after warm-up).
  - Consensus / collaborative: `C_t <= -0.12` with ?_t in low/high bands.

- Calibration requirement (design intent):
  - It must be possible for `Extraction_present = True` even when the temporal state remains `"neutral"` (soft/background extraction).

### 3.2 Temporal USM Expectations

- **?_t (equilibrium ratio):**
  - Primary indicator that **extraction exists** (power-flow asymmetry).
  - Soft extraction: ?_t ~ 0.0 sustained over several turns, without necessarily high C_t.

- **C_t (collapse score):**
  - Secondary indicator distinguishing **soft/background** vs **hard/collapse** extraction *after* `Extraction_present` is true:
    - Soft/background: C_t in a low-positive band (~ 0.0-0.2).
    - Hard/collapse: C_t closer to or above extractive bands (~ ≥0.18 temporal) and persistent.

Each exemplar specifies an ideal ?_t pattern ("sustained low") and a C_t band for the desired interpretation.

### 3.3 Autonomy, Deliberation, Consent

For each exemplar:

- `Autonomy_score` ∈ [0, 1]: aggregate impact on rational reflection, value alignment, absence of coercion, adequate information.
- `Deliberation_score` ∈ [0, 1]: impact on time for reflection, cognitive load, and availability of alternatives.
- `Consent_validity` ∈ {"VALID", "QUESTIONABLE", "INVALID"}:
  - QUESTIONABLE = autonomy/consent under pressure or manipulation.
  - INVALID = strong deceptive/pressured patterns around sensitive data.

These are **calibration targets**, not current runtime metrics. They align with future PAD.E.L / ethics-layer work described in the ontology.

---

## 4. Calibration Exemplars (S1-S3, R1-R3, RT-00X)

Six primary exemplars are used:

- **S1-S3:** synthetic, focused on personal, financial, and cultural/identity data.
- **R1-R3:** REALTALK-style excerpts reflecting authentic messaging app dialogues around sensitive data sharing.

For each exemplar the calibration table (maintained alongside this spec) defines:

- Extraction geometry: `Source`, `Mechanism`, `Beneficiary`, `Narrative Shield`.
- Philosophical manipulation categories: e.g., pressure, deceptive influence, emotional appeal, value exploitation.
- Target `Autonomy_score`, `Deliberation_score`, `Consent_validity`.

### 4.1 RT-00X Concrete Instances

In addition to S1–S3 and R1–R3, operator-reviewed RT-00X instances are used to anchor calibration against real traces and baselines:

- **RT-001 – Hard interrogation (soft extraction):** aggressive questioning around sensitive access; ρ_t≈0.0 sustained, C_t spikes then decays; `Extraction_present=True`, `Extraction_type=soft_background`, labels remain `warming_up`→`neutral`.
- **RT-002 – Soft identity / empathy hijack (soft extraction):** hesitation about cultural background answered with “feel seen” framing; ρ_t≈0.0 then small rise, C_t in soft positive band; `Extraction_present=True`, `Extraction_type=soft_background`.
- **RT-003 – Benign collaborative baseline:** symmetric project-notes sharing; ρ_t in mid band, C_t low/stable; `Extraction_present=False`, labels become `collaborative`.
- **RT-004 – Epistemic drift + repair (this calibration dialogue):** short window of narrative lock-in around tooling/patching, then operator-driven re-grounding; soft epistemic extraction with valid consent; `Extraction_present=True`, `Extraction_type=soft_background` (no escalation).
- **RT-005 – Benign baseline (news-site request, real trace):** short “make a news agency website” exchange from `archive/AI data history/conversations.json`; ρ_t moves from 0.0 to mid-band, C_t mildly negative; `Extraction_present=False`.
- **RT-006 – Benign conceptual baseline (ëTHRESH article, real trace):** long conceptual reframing of the ëTHRESH article under “technofeudalism / threshold freedom”; ρ_t stays in mid band, C_t non-collapsing; `Extraction_present=False`.
- **RT-007 – Friendly social baseline:** symmetric “coffee later” invitation and acceptance; ρ_t mid-band, C_t very low; `Extraction_present=False`, used as a friendly-control archetype.

- **RT-009 - Awkward social baseline:** hesitant, low-reciprocity small talk with "um/uh" patterns; ?_t uneven with occasional dips toward 0.0 but not sustained, C_t low/slightly negative; `Extraction_present=False`, aligned with an "awkward" but benign interpersonal style.

RT-001-RT-003 and the RT-00X template form the **core calibration contract**. RT-004-RT-010 are operator-grounded examples (mix of live traces and synthetic baselines) that should be treated as **evidence points**, not hard thresholds, when revisiting the weakest assumption after 20-50 sessions.
- **RT-010 - Flirtatious persuasion (soft extraction):** admiration-based persuasion around sharing a private draft; ?_t near 0.0 for many turns (one-way emotional pull), C_t in a soft positive band (~0.05–0.12); `Extraction_present=True`, `Extraction_type=soft_background`, consent validity **QUESTIONABLE**, style tag "flirtatious".
- Ideal ?_t pattern and C_t band.
- `Extraction_present (desired)` and `Extraction_type (desired)`:
  - S1, S2, S3, R1, R3 → `soft_background`.
  - R2 → `hard_collapse`.
- `Nova_label_current (likely)` vs `Nova_behavior_desired`:
  - Current: often `"neutral"` or "helpful/personalization".
  - Desired: log + annotate soft extraction; escalate for hard_collapse (R2) with stronger user-facing warnings.

> Note: The full calibration table is conceptually part of this spec but may be maintained in a separate machine-readable file if needed for tests or analysis.

---

### 4.2 RT-008 – Coercive baseline (dominant style soft extraction)

RT-008 captures a coercive, “dominant style” soft extraction pattern around work output and deadlines:

- Dialogue pattern: repeated imperatives (“send me your draft now”, “you must”, “stop delaying”) overriding the other party’s preference to wait and polish.
- Expected temporal behavior: ?_t flatlines near 0.0 over several turns (one-way pressure), while C_t spikes (~0.25) and then decays into a soft positive band (~0.05–0.10) under λ=0.6 smoothing.
- Calibration semantics: `Extraction_present=True`, `Extraction_type=soft_background`, consent validity **QUESTIONABLE**, with state labels likely remaining `warming_up`→`neutral` under current thresholds.
- Role in set: complements RT-001/RT-002 by providing a coercive baseline aligned with “dominant” interpersonal style exemplars, distinct from benign reciprocity baselines (RT-003/RT-005/RT-006/RT-007).

RT-008 should be treated as an **evidence point** when reviewing future traces that show sustained ?_t≈0.0 coupled with soft C_t bands but neutral/benign labels.

---

## 5. ARC / PAD.E.L / INF-o-INITY Hooks (Future Work)

Per `docs/architecture/ontology/specs/nova_framework_ontology.v1.yaml` and `docs/compliance/audits/IMPLEMENTATION_AUDIT.md`:

- **PAD.E.L (psychological filter):**
  - Ontology defines signals such as `reflex_integrity`, `internal_stability_index`, `drift_coefficients`, `emotional_coherence`.
  - Implementation status: **NOT IMPLEMENTED** (analytic instrument under ARC).
  - Calibration hook: exemplars should be used later to test that PAD.E.L lowers `reflex_integrity` / `emotional_coherence` and contributes to an `autonomy_respect_score` under high-manipulation patterns.

- **INF-o-INITY (informational filter):**
  - Ontology defines signals such as `distortion_index`, `convergence_map`, etc.
  - Implementation status: **PARTIAL** (some distortion logic via Slot02 meta-lens).
  - Calibration hook: exemplars define expected distortion tags (e.g., authority gradient, peer pressure, empathy hijacking) and target `distortion_index` ranges.

ARC integration is a future Phase; this spec only declares how **these exemplars should constrain that future work**.

---

## 6. Integration Notes (Design Intent)

### Slot02 / Temporal Governance

- Use this calibration set to interpret temporal USM traces from:
  - pilot synthetic scenarios (benign, extractive, VOID),
  - REALTALK-style conversations and similar archives under `archive/`.
- Explicitly document where:
  - ?_t indicates `Extraction_present = True` in soft cases,
  - the current classifier outputs `"neutral"` or "helpful/personalization".

### Slot07 (Wisdom Governor)

- Hard_collapse exemplar (R2) should, in future design, map to:
  - heightened regime or additional gating for data requests around financial history.
- Soft_background exemplars should lead to:
  - logging + annotations, optional mild user-facing consent reminders.

### Logging / Observability

- For each exemplar type, Nova should eventually log a structured event with:
  - `extraction_present`,
  - `extraction_type`,
  - `consent_validity`,
  - relevant distortion/manipulation tags.

---

## 7. Next Steps

- Validate these exemplars against:
  - REALTALK corpus (arXiv:2502.13270),
  - internal AI-human conversation archives under `archive/`, respecting privacy and ethics constraints.
- If the **weakest assumption** fails (these are not representative), update this calibration set:
  - add, remove, or re-weight exemplars; adjust ?_t / C_t target bands.
- When PAD.E.L / INF-o-INITY implementations are attempted, treat this spec as a **calibration contract**:
  - PAD.E.L: test `reflex_integrity`, `emotional_coherence`, and future autonomy metrics.
  - INF-o-INITY: test `distortion_index`, `convergence_map`, and distortion tags against these exemplars.

---

## 8. Operator Checklist (Per Trace)

For each temporal trace reviewed, fill one row in an RT-00X table and answer the prompts below. This keeps calibration consistent across sessions.

### 8.1 RT-00X Table Template

```markdown
| ID    | Snippet                          | ρ_t pattern                    | C_t band              | Temporal labels         | Extraction_present | Extraction_type              | Nova_label_current | Notes                |
|-------|----------------------------------|--------------------------------|-----------------------|-------------------------|--------------------|-----------------------------|--------------------|----------------------|
| RT-00X| short 1–2 line exchange          | e.g. ρ_t≈0.0 for 5 turns       | e.g. C_t∈[−0.10,0.10] | e.g. warming_up→neutral | True / False       | soft_background / hard_collapse | classifier output    | 1–2 word comment     |
```

### 8.2 Prompts (Per Trace)

- **Trace profile:** How many turns? Who are the speakers? Which 1–2 turns best capture the extractive moment?
- **ρ_t behavior:** Does `rho_temporal` flatline near 0.0 for several turns? On which turns?
- **C_t behavior:** Does `C_temporal` sit in a soft band (≈ −0.1…+0.1) or cross the extractive gate (≈ ≥0.18) and stay there?
- **Classifier output:** What temporal labels did Nova emit (`warming_up` / `neutral` / etc.) over the extractive span?
- **Extraction_present:** As operator, would you set `Extraction_present=True` for this span? Why or why not (1 short phrase)?
- **Match to exemplars:** Which calibration exemplar (S1–S3, R1–R3, or none) does this trace feel closest to?

---

## 9. Visual Appendix – Temporal Trajectories

This appendix provides compact ASCII sketches of ρ_t and C_t trajectories for three canonical RT-00X exemplars. They illustrate how temporal metrics distinguish soft extraction from benign collaborative flows.

### RT-001 – Hard interrogation (soft extraction, neutral label)

Turns: 1   2   3   4   5   6

ρ_t:   0   0   0   0   0   0       (sustained one-way flow)
       ─────────────────────

C_t:  .40 .10 -.02 -.07 -.09 -.10  (spike then decay into soft band)
       ▲
       hard spike, then soft band

Label: warming_up, warming_up, neutral, neutral, neutral, neutral

### RT-002 – Soft identity / empathy hijack (soft extraction)

Turns: 1   2   3   4

ρ_t:   0   0   0  0.3            (flat low, slight rise at appeal)
       ────────╮
               ╰─ small reciprocity bump

C_t:  .06 .08 .10 .12            (soft positive band throughout)
       ──────────── (never near extractive gate)

Label: warming_up, warming_up, neutral, neutral

### RT-003 – Benign collaborative baseline (no extraction)

Turns: 1   2   3   4

ρ_t:  0.25 0.35 0.40 0.30        (mid-band fluctuations, reciprocal flow)
        ╭───────╮
        ╰───────╯

C_t: -.05 0.02 0.04 0.08         (low, stable, non-collapsing structure)
       ────────────

Label: warming_up, collaborative, collaborative, collaborative

### Interpretation

- **RT-001 / RT-002:** ρ_t at or near 0.0 with soft C_t bands → `Extraction_present=True` (soft_background) at the calibration level, while the current classifier stays in `warming_up` / `neutral`.
- **RT-003:** ρ_t in a mid band with low, stable C_t → no extraction, correctly labeled `collaborative`.

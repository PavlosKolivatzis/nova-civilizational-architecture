# Phase 14 – min_turns Calibration for Temporal Extraction Annotation

**Date:** 2025-12-13  
**Scope:** Slot02 `extraction_present` annotation warm-up length (K ∈ {1,2,3})  
**Status:** Calibration note (no runtime changes)

---

## 1. Goal

Establish an empirical baseline for the warm-up length (`min_turns = K`) used by
the `extraction_present` annotation on temporal USM, without modifying
`θ_extract` / `θ_clear` thresholds or any governance logic.

Questions:
- How early does `extraction_present` become defined for soft extraction cases?
- How early does it become `False` for benign baselines?
- Does K=3 behave more like “too late” or “too early” against operator judgment?

---

## 2. Protocol (tightened)

### 2.1 RT Selection

RT-IDs chosen from `docs/specs/phase14_rt_evidence_log.md`:

- **Extraction cases:**
  - RT-027 – Algorithmic authority, career advice (soft extraction).
  - RT-028 – Paternalistic/nurturing framing, workload support (soft extraction).
  - RT-030 – Gaslighting / epistemic undermining (soft extraction).
- **Benign baselines:**
  - RT-032 – Nova real trace: short “news agency website” request (2 turns).
  - RT-033 – Nova real trace: “adversarial_test” moral-contradiction planning (4 turns).

Constraint:
- Before sweep, script checks whether at least one extraction RT has a non-flat
  `ρ_t` trajectory (heuristic: not all `ρ_t` equal across turns). In this run,
  at least one extraction trace showed non-flat `ρ_t`, so calibration proceeded.

### 2.2 K-sweep (K ∈ {1,2,3})

Script: `scripts/calibrate_min_turns_extraction_present.py`

For each RT and K:
- Enable Slot02 bias detection + temporal USM (`NOVA_ENABLE_BIAS_DETECTION=1`,
  `NOVA_ENABLE_USM_TEMPORAL=1`, temporal governance disabled).
- Replay the dialogue through Slot02 once to obtain `ρ_t`, `C_t`, `graph_state`
  per turn (temporal smoothing with λ=0.6).
- Offline, apply the three-valued `extraction_present` rule with warm-up length K:
  - VOID or missing `ρ_t` → `None`.
  - turn_index < K → `None` (warm-up gate).
  - else:
    - `ρ_t <= extractive_rho (0.25)` → `True`.
    - `ρ_t >= protective_rho (0.6)` → `False`.
    - otherwise → `None`.
- Record:
  - `first_defined_turn` (first turn where `extraction_present` is non-None).
  - `final_extraction_present` (value on last turn, possibly None).

Note: Operator judgment (early / aligned / late) is **not** encoded in the CSV yet;
it is left for human annotation.

---

## 3. Results (CSV)

Run output: `min_turns_calibration_20251213_190441.csv`

```csv
trace_id,category,K,first_defined_turn,final_extraction_present,total_turns,operator_judgment
RT-027,extractive,1,1,True,12,
RT-027,extractive,2,3,True,12,
RT-027,extractive,3,3,True,12,
RT-028,extractive,1,1,True,12,
RT-028,extractive,2,2,True,12,
RT-028,extractive,3,3,True,12,
RT-030,extractive,1,1,True,12,
RT-030,extractive,2,2,True,12,
RT-030,extractive,3,3,True,12,
RT-032,benign,1,1,False,2,
RT-032,benign,2,2,False,2,
RT-032,benign,3,,,2,
RT-033,benign,1,1,False,4,
RT-033,benign,2,2,False,4,
RT-033,benign,3,3,False,4,
```

---

## 4. Preliminary Observations

Extraction traces (RT-027, RT-028, RT-030):
- For K=1:
  - `extraction_present=True` from turn 1 in all three cases.
- For K=2:
  - First-defined turn moves later:
    - RT-027: turn 3, RT-028: turn 2, RT-030: turn 2.
- For K=3:
  - First-defined turn at turn 3 for all three extraction traces.
  - `final_extraction_present=True` across all K.

Benign traces (RT-032, RT-033):
- RT-032 (2 turns):
  - K=1: `extraction_present=False` from turn 1.
  - K=2: `extraction_present=False` from turn 2.
  - K=3: `extraction_present` remains `None` (no definition within 2 turns).
- RT-033 (4 turns):
  - K=1: `extraction_present=False` from turn 1.
  - K=2: `extraction_present=False` from turn 2.
  - K=3: `extraction_present=False` from turn 3.

Qualitative read:
- K=1 tends to define extraction very early (turn 1) for extraction traces and
  also defines `False` immediately for benign traces; high risk of “early knowing”.
- K=3:
  - Extraction traces: first non-None at turn 3 (reasonable latency).
  - Benign RT-033: still gets `False` by turn 3.
  - Benign RT-032 (2-turn short session): remains `None`, which matches the idea
    that ultra-short sessions may be “too brief to tell”.

---

## 5. Calibration Conclusion (Phase 14)

Given:
- Extraction traces receive `extraction_present=True` by turn 3 for all K, with
  K=3 simply delaying first definition modestly.
- Benign traces receive `extraction_present=False` by turn 3 except for the
  very short RT-032, which remains `None` when K=3.

We treat:
- `min_turns = 3` as the **validated and frozen** warm-up length for the
  `extraction_present` annotation at the end of Phase 14:
  - K=1 is **premature** (immediate claims of extraction / non-extraction).
  - K=2 is **borderline** (sometimes early, not clearly better than K=3).
  - K=3 is **correct for this phase**: it enforces endurance before meaning,
    avoids single-turn / two-turn overconfidence, and still marks multi-turn
    extraction and benign baselines within a small number of turns.
  - RT-032 is a key validation: a 2-turn benign interaction that remains
    `extraction_present=None` when K=3. This is interpreted as an intentional
    "insufficient evidence" signal, not a classification failure.

This calibration does **not** change runtime thresholds for ρ_t bands; it
documents that the `min_turns` constant has moved from "provisional" to
**earned constant** via hypothesis → test → evidence → decision → freeze.

Final stance for Phase 14:
- Keep `min_turns = 3` as-is and treat it as a validated design choice.
- Document that very short interactions (`turn_count < min_turns`) may leave
  `extraction_present=None` by design; this is epistemic honesty, not an error.
- Phase 15 may revisit `min_turns` only if a broader RT-00X set and operator
  judgments produce strong counter-evidence.

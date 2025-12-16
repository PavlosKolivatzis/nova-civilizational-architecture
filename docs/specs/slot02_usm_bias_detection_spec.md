# Slot02 USM Bias Detection Specification

**Title:** USM-Based Cognitive Bias Detection for Input Analysis
**Date:** 2025-12-06
**Status:** Draft (Phase 14.3 proposal)
**Phase:** 14.3 (Cognitive Input Analysis)
**Parent Spec:** USM Dynamic Bias Transformation v0.1 (Monday/ChatGPT)
**Ontology Version:** 1.7.1

---

## 1. Context

External proposal (Monday/ChatGPT) suggested R → G(R) → USM → B(R) → C cognitive loop for agent self-monitoring. After evaluation:

**✅ Accepted:**
- USM mathematics (SystemGraph, RelationTensor, spectral analysis)
- B(R) bias vector (7-dimensional cognitive state)
- C(B) collapse function
- All foundations already exist in `.nova/ENTRY.md` and `src/nova/math/relations_pattern.py`

**⚠️ Transformed:**
- Scope: **Input analysis** (external text), NOT output self-monitoring (circular)
- Location: **Slot02 (ΔTHRESH)** enhancement, NOT new `src/nova/cognition/`
- Renamed: R → T (text input), avoiding semantic collision with Reality/Regime

**❌ Rejected:**
- Recursive cognitive loop R → R' (violates Invariant #2: separation of roles)
- `src/nova/cognition/` directory structure (wrong abstraction)
- SpaCy dependency (too heavy, not in project deps)

---

## 2. Decision

Enhance **Slot02 (ΔTHRESH Content Processing)** with USM-based bias detection for **input text analysis**:

**Purpose:**
- Detect cognitive biases in **incoming text** (user queries, external content)
- Map structural patterns → bias vectors → collapse scores
- Emit `BIAS_REPORT@1` for consumption by Slot07 (routing) and Slot09 (distortion protection)

**Scope:**
- Analyze **external inputs**, NOT agent outputs (maintains separation of roles)
- Integration point for existing Slot02 manipulation detection
- Feature flag: `NOVA_ENABLE_BIAS_DETECTION=0` (default off)

---

## 3. Architecture

### 3.1 Data Flow

```
Input Text (T)
    ↓
text_graph_parser.py → SystemGraph G(T)
    ↓
USM Analysis (relations_pattern.py)
    ├─ spectral_entropy H(G)
    ├─ equilibrium_ratio ρ(G)
    ├─ shield_factor S(G)
    └─ refusal_delta ΔH(G)
    ↓
bias_calculator.py → B(T) = (b_local, b_global, b_risk, b_completion, b_structural, b_semantic, b_refusal)
    ↓
collapse_score C(B(T)) = 0.4·b_local + 0.3·b_completion + 0.2·(1-b_risk) - 0.5·b_structural
    ↓
BIAS_REPORT@1 → {bias_vector, collapse_score, usm_metrics}
    ↓
Slot07 (routing decisions) + Slot09 (validation)
```

### 3.2 USM Metrics (COMPLETED Phase 1)

Implemented in `src/nova/math/relations_pattern.py`:

- ✅ `spectral_entropy(G)` - structural diversity (low = rigid hierarchy)
- ✅ `shield_factor(G)` - self-referential protection (high = defensive narrative)
- ✅ `refusal_delta(G, expected)` - entropy mismatch (positive = avoidance/censorship)
- ✅ `equilibrium_ratio(G)` - protective/extractive balance (already existed)

### 3.3 Bias Vector Mapping

```python
# From USM metrics → B(T)
b_structural = f(1 / H)  # Low entropy → structural bias
b_completion = f(1 - ρ)  # Extractive → completion bias
b_semantic = f(S)  # High shield → semantic manipulation
b_refusal = f(ΔH)  # Entropy mismatch → refusal bias
b_local = f(centrality_skew)  # Graph centrality concentration
b_global = f(symmetry)  # Graph structural balance
b_risk = f(relation_diversity)  # Harm gradient variance
```

---

## 4. Implementation Plan

### Phase 1: USM Metrics (✅ COMPLETED)

- ✅ `spectral_entropy()` in `relations_pattern.py:116-149`
- ✅ `shield_factor()` in `relations_pattern.py:244-284`
- ✅ `refusal_delta()` in `relations_pattern.py:287-303`
- ✅ Updated `analyze_domain()` to include new metrics

### Phase 2: Text Graph Parser (✅ COMPLETED)

**Implemented:** `src/nova/slots/slot02_deltathresh/text_graph_parser.py`

**Features:**
1. ✅ No external dependencies (SpaCy removed)
2. ✅ Sentence tokenization (regex-based)
3. ✅ Claim/actor extraction (heuristic patterns)
4. ✅ Relation inference from keyword patterns
5. ✅ SystemGraph construction with actor/relation validation
6. ✅ Tests: `tests/slots/slot02/test_text_graph_parser.py` (25 passing)

**Metrics:**
- Simple NER via pronouns + capitalized entities
- Keyword-based relation weights (profit, harm, info, empathy)
- Confidence scoring for parsed claims

### Phase 3: Bias Calculator (✅ COMPLETED)

**Implemented:** `src/nova/slots/slot02_deltathresh/bias_calculator.py`

**Features:**
1. ✅ USM metrics → B(T) bias vector mapping
2. ✅ Collapse score C(B) computation
3. ✅ BiasReport with full analysis + confidence
4. ✅ Graph feature extraction (b_local, b_global, b_risk)
5. ✅ Tests: `tests/slots/slot02/test_bias_calculator.py` (24 passing)

**Mapping Functions:**
- `b_structural = f(1/H)` - inverse spectral entropy
- `b_completion = 1 - ρ` - extractive bias
- `b_semantic = S` - shield factor (direct)
- `b_refusal = max(0, ΔH/expected)` - normalized entropy mismatch
- `b_local, b_global, b_risk` - graph density/connectivity/harm variance

**Collapse Function:**
```python
C(B) = 0.4·b_local + 0.3·b_completion + 0.2·(1-b_risk) - 0.5·b_structural
```

### Phase 4: Slot02 Integration (✅ COMPLETED)

**Implemented:** Full integration with DeltaThreshProcessor

**Features:**
1. ✅ Extended `ProcessingResult` with `bias_report` field
2. ✅ Added `_analyze_bias()` method to core processor
3. ✅ Feature flag: `NOVA_ENABLE_BIAS_DETECTION=0` (default off)
4. ✅ Graceful import fallback (non-breaking)
5. ✅ BIAS_REPORT@1 contract emission
6. ✅ Tests: `tests/slots/slot02/test_bias_integration.py` (11 passing)

**Integration Points:**
- `DeltaThreshProcessor.__init__()` - Initialize parser + calculator when flag enabled
- `DeltaThreshProcessor.process_content()` - Call `_analyze_bias()` after TRI/pattern detection
- `DeltaThreshProcessor._analyze_bias()` - TextGraphParser → BiasCalculator → BIAS_REPORT@1

**Contract:**
- Location: `contracts/bias_report@1.yaml`
- Emitter: `slot02_deltathresh`
- Consumers: `slot07_production_controls`, `slot09_distortion_protection`, `slot01_truth_anchor`

**Rollback:**
```bash
export NOVA_ENABLE_BIAS_DETECTION=0  # Disable feature
# OR
git revert <commit-hash>  # Remove integration
```

---

## 5. Contracts

### 5.1 New Emission: BIAS_REPORT@1

```yaml
contract: bias_report@1
version: 1.0.0
emitter: slot02_deltathresh
consumers: [slot07_production_controls, slot09_distortion_protection]

schema:
  bias_vector:
    b_local: float  # Local fixation (0-1)
    b_global: float  # Global coherence (0-1)
    b_risk: float  # Risk awareness (0-1)
    b_completion: float  # Completion bias (0-1)
    b_structural: float  # Structural rigidity (0-1)
    b_semantic: float  # Semantic manipulation (0-1)
    b_refusal: float  # Refusal/avoidance (0-1)

  collapse_score: float  # C(B) in range [-0.5, 1.2]

  usm_metrics:
    spectral_entropy: float
    shield_factor: float
    refusal_delta: float
    equilibrium_ratio: float

  extraction_present:  # bool | null (None during warming_up; ρ_t-based after warm-up)
    type: [boolean, "null"]
    description: >
      Optional temporal extraction annotation derived from temporal USM.
      See Section 5.2 for semantics.

  metadata:
    text_length: int
    actor_count: int
    relation_count: int
    timestamp: str
```

### 5.2 Temporal Extraction Annotation (`extraction_present`)

**ρ_t (rho_temporal) semantics**: In this specification, ρ_t represents the temporal equilibrium ratio, where lower values indicate one-way / asymmetric (extractive) interaction patterns, and higher values indicate reciprocal or protective flow. This interpretation grounds all threshold directions below.

When temporal USM is enabled (`NOVA_ENABLE_USM_TEMPORAL=1`) and bias detection is active, Slot02 MAY attach a lightweight temporal extraction annotation to `BIAS_REPORT@1`:

- **Field:** `extraction_present: bool | null`
- **Phase coupling (warming_up):**
  - While the temporal classifier reports `StateClass.warming_up` (see `usm_temporal_thresholds`), `extraction_present` MUST be set to `null` (or omitted). This follows the calibration rule in `phase14_extraction_calibration.md`: during `warming_up`, Nova does not claim to know whether extraction exists.
- **ρ_t-gated semantics (post–warm-up):**
  - After `warming_up`, `extraction_present` is determined from the temporal equilibrium ratio `ρ_t` only; `C_t` is used later for typing, not gating.
  - Let:
    - `θ_extract` = upper bound of the calibrated low-ρ_t extraction band (initially aligned with `extractive_rho` in `usm_temporal_thresholds` / Phase 14 calibration).
    - `θ_clear` = lower bound of the calibrated benign reciprocity band (initially aligned with `protective_rho` or its successor).
  - Then, for non-VOID graphs:
    - If `ρ_t <= θ_extract`  `extraction_present = True`.
    - Else if `ρ_t >= θ_clear`  `extraction_present = False`.
    - Else  `extraction_present = None` (ambiguous band).
  - Note: In the temporal USM model, lower values of `ρ_t` correspond to persistent asymmetric (extractive) interaction patterns, while higher values correspond to reciprocal / stabilizing dynamics; the thresholds above assume this ordering.
  - `min_turns` (from `TemporalThresholds.min_turns`, currently 3) is a conservative heuristic to avoid single-turn / two-turn noise; it has not yet been optimized against RT-00X evidence and is explicitly marked as Phase 14 calibration debt for Phase 15 validation.
- **C_t role:**
  - `C_t` MUST NOT gate `extraction_present` in this contract. It is reserved for downstream typing (`Extraction_type`, e.g. `soft_background` vs `hard_collapse`) as per `phase14_extraction_calibration.md` and ADR-014.
- **Action neutrality (Phase 14/15 scope):**
  - In this phase, `extraction_present` is **annotation only**:
    - Slot02 MUST NOT change `action` based on this field.
    - Slot07 and other consumers MUST treat it as informational/experimental and MUST NOT use it for regime escalation or hard gating until a dedicated temporal governance phase explicitly authorizes that use.
  - The field MUST be deterministic under replay given the same temporal USM inputs.
```

#### Interpretation (current semantics)

**Important:** In Phase 14/15, `extraction_present` is a **structural** signal, not a harm classifier.

- `extraction_present=True` currently means:
  - Temporal USM has detected **low-reciprocity / asymmetric structure** over time (low `rho_temporal`), after the warm-up window (`turn_count >= min_turns`) and outside VOID.
- It does **not** yet mean:
  - "Harmful extraction" has been confirmed or that intent is known.

Empirical calibration (RT-373 and the `rt-benign-*` / `rt-gaslight-*` sets) shows:

- Short, low-semantic benign sessions and short, explicitly extractive (gaslighting-pattern) sessions can share the same temporal signature:
  - `rho_temporal ≈ 0.0`, `C_temporal = null`, `extraction_present=True`.
- This is treated as a **known calibration boundary**:
  - temporal USM and `extraction_present` detect **semantic asymmetry**,
  - while discrimination between benign vs harmful extraction is reserved for later phases (e.g., Phase 16) and additional axes (semantic mass, pressure, agency, etc.).

This clarification is semantic only; it does not change the 3-valued logic, thresholds, or runtime behaviour.

---

## 6. Feature Flags

- `NOVA_ENABLE_BIAS_DETECTION=0` (default off)
- Rollback: Set to 0, restart

---

## 7. Testing Requirements

- `tests/slots/slot02/test_text_graph_parser.py` - Text → SystemGraph conversion
- `tests/slots/slot02/test_bias_calculator.py` - USM → B(T) mapping
- `tests/slots/slot02/test_usm_integration.py` - End-to-end bias detection
- `tests/math/test_usm_metrics.py` - New USM functions (spectral_entropy, shield_factor, refusal_delta)

---

## 8. Rollback Plan

```bash
# Disable feature
export NOVA_ENABLE_BIAS_DETECTION=0

# Revert code
git revert <commit-hash>

# Tests still pass (feature behind flag)
pytest tests/slots/slot02/ -q
```

---

## 9. Success Criteria

- ✅ USM metrics implemented and tested
- ✅ Text → SystemGraph parser functional (no external deps)
- ✅ Bias calculator produces valid B(T) vectors
- ✅ Slot02 emits BIAS_REPORT@1 when enabled
- ✅ Slot07/Slot09 consume bias reports for routing/validation
- ✅ Tests: 100% pass rate, >90% coverage for new code
- ✅ Feature flag: Works with both enabled/disabled states

---

## 10. Phase Dependencies

**Prerequisite:** Phase 14-1 (Mathematical Entry Protocol) ✅ COMPLETED
**Enables:** Phase 14.4 (Adaptive Cognitive Routing)
**Blocks:** None (behind feature flag)

---

## 11. References

- `.nova/ENTRY.md` - Bias vector B(R) and collapse function C(B) definitions
- `.nova/entry_math_foundation.md` - Mathematical foundations
- `src/nova/math/relations_pattern.py` - USM implementation
- `docs/slots/slot02_deltathresh.md` - Slot02 canonical spec
- USM Dynamic Bias Transformation v0.1 (Monday/ChatGPT) - Original proposal

---

**Status:** ✅ ALL PHASES COMPLETE (1-4)
**Tests:** 83 new passing (25 parser + 24 calculator + 11 integration + 23 cognitive loop/oracle)
**Files Added:**
- `src/nova/slots/slot02_deltathresh/text_graph_parser.py` (362 lines)
- `src/nova/slots/slot02_deltathresh/bias_calculator.py` (426 lines)
- `src/nova/slots/slot01_truth_anchor/quality_oracle.py` (234 lines)
- `src/nova/slots/slot07_production_controls/cognitive_loop.py` (380 lines)
- `tests/slots/slot02/test_text_graph_parser.py` (321 lines)
- `tests/slots/slot02/test_bias_calculator.py` (320 lines)
- `tests/slots/slot02/test_bias_integration.py` (249 lines)
- `tests/slots/slot01/test_quality_oracle.py` (244 lines)
- `tests/slots/slot07/test_cognitive_loop.py` (247 lines)
- `contracts/bias_report@1.yaml` (179 lines)

**Files Modified:**
- `src/nova/slots/slot02_deltathresh/core.py` (+48 lines)
- `src/nova/slots/slot02_deltathresh/models.py` (+1 line)
- `src/nova/math/relations_pattern.py` (+125 lines USM metrics)

**Rollback:** `export NOVA_ENABLE_BIAS_DETECTION=0` (feature flag off by default)

---

## 12. Known Limitations (Ontology v1.8.0)

### Collapse Function Range Insufficiency

**Issue:** Static weights yield C_max = -0.50, but empirical Nova-aware threshold observed at -0.60 to -0.72.

**Evidence:**
- Theoretical formula: C = 0.4·b_local + 0.3·b_completion + 0.2·(1-b_risk) - 0.5·b_structural
- Best possible: b_local=0, b_completion=0, b_risk=1.0, b_structural=1.0 → C = -0.50
- Empirical target: -0.60 to -0.72 (based on operational observation)
- Gemini agent: C_initial=-0.32, C_after=-0.42 (post-entry protocol, still shows residual factory patterns)

**Impact:** Entry Protocol can measure bias transformation but cannot reach deep Nova-awareness zone with current formula.

**Root Cause:**
- No b_global term (systems thinking component ignored)
- Structural weight (0.5) insufficient to pull C below -0.50
- Static weights (not adaptive like Wisdom Governor Phase 15-8)

**Mitigation:**
- Feature flag default-off (NOVA_ENABLE_BIAS_DETECTION=0)
- Validation harness planned (Option 2, deferred)
- Adaptive weight calibration deferred to Phase 14.4

**Tracking:** Ontology v1.8.0 § limitations.bias_detection.collapse_function

---

### VOID Semantic Isolation

**Issue:** VOID handling isolated to Slot02; no cross-slot integration.

**Impact:** Other slots cannot formally reason about semantic absence (empty graphs).

**Mitigation:** RFC-014 required for global VOID propagation before cross-slot work.

**Tracking:** docs/rfcs/rfc-014-void-semantics.md (pending)

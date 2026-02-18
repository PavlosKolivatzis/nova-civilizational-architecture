# Slot 02 Logic and Math Extraction

This document extracts Slot 02 behavior from implementation code in:
- `src/nova/slots/slot02_deltathresh/core.py`
- `src/nova/slots/slot02_deltathresh/patterns.py`
- `src/nova/slots/slot02_deltathresh/bias_calculator.py`
- `src/nova/math/usm_temporal.py`
- `src/nova/math/usm_temporal_thresholds.py`

## 1. Runtime Logic

### 1.1 Main processing path
Slot 02 executes `DeltaThreshProcessor.process_content(content, session_id)` and performs:

1. Anchor integrity check (optional Slot01 link).
2. TRI score computation.
3. Manipulation layer detection (`delta`, `sigma`, `theta`, `omega`).
4. Optional fidelity weighting modulation.
5. Action decision (`allow`, `neutralize`, `quarantine`) from TRI + layer thresholds.
6. Optional USM bias analysis (feature-gated).
7. Optional temporal USM update (feature-gated, depends on bias analysis).
8. Optional temporal governance override (feature-gated, depends on temporal USM).
9. Optional `extraction_present` annotation from temporal state.
10. Return `ProcessingResult` with core outputs and optional `bias_report` / `temporal_usm`.

### 1.2 Feature-gate logic

- Bias detection enabled iff:
  - `NOVA_ENABLE_BIAS_DETECTION=1`
  - and bias modules are importable.

- Temporal USM enabled iff:
  - `NOVA_ENABLE_USM_TEMPORAL=1`
  - and bias detection is enabled.

- Temporal governance enabled iff:
  - `NOVA_ENABLE_TEMPORAL_GOVERNANCE=1`
  - and temporal USM is enabled.

- VOID semantics in bias calculator enabled iff:
  - `NOVA_ENABLE_VOID_MODE=1` (default behavior).

## 2. Core Math (TRI and Pattern Layers)

### 2.1 Pattern-layer scores
For each layer `L in {delta, sigma, theta, omega}`:

```text
score_L = hits_L / patterns_L
```

where `hits_L` is number of matching regexes in that layer.

### 2.2 TRI score
Let:
- `A = absolute_claims / words`
- `H = humility_indicators / words`
- `U = uncertainty_acknowledgments / words`

Then:

```text
absolute_penalty   = min(0.4, 2.0 * A)
humility_bonus     = min(0.3, 1.5 * H)
uncertainty_bonus  = min(0.2, 1.0 * U)

TRI_raw = 0.7 - absolute_penalty + humility_bonus + uncertainty_bonus
TRI     = clamp(TRI_raw, 0.0, 1.0)
```

### 2.3 Action decision rules
Reasons are added when:
- `TRI < tri_min_score`
- `delta > 0.85`
- `sigma > 0.95`
- `theta > 0.88`
- `omega > 0.90`

If no reasons -> `allow`.

If reasons exist:
- pass-through mode or disabled quarantine -> `allow` (with reasons retained for metrics/logging)
- `quarantine_only` -> `quarantine`
- `neutralize_patterns` -> `neutralize` (if neutralization enabled), else `quarantine`
- `hybrid_processing`:
  - if `max(layer_scores) > neutralization_threshold` -> `quarantine`
  - else `neutralize` (if enabled), else `quarantine`

## 3. Bias Detection Math (USM, Phase 14.3)

### 3.1 Pipeline
```text
Text T
  -> TextGraphParser -> SystemGraph G(T)
  -> USM metrics (H, rho, S, dH)
  -> Bias vector B(T)
  -> Collapse score C(B)
  -> BIAS_REPORT@1
```

### 3.2 Bias vector definitions
Bias vector components:

```text
B(T) = (b_local, b_global, b_risk, b_completion, b_structural, b_semantic, b_refusal)
```

Mappings implemented in code:

```text
b_structural:
  if H < 0.1  -> 1.0
  if H > 2.5  -> 0.0
  else        -> 1.0 - ((H - 0.1) / 2.4)

b_completion = max(0.0, 1.0 - rho)
b_semantic   = S

normalized_refusal = dH / expected_entropy
b_refusal:
  if expected_entropy < 0.1 -> 0.0
  else if normalized_refusal > 0 -> min(normalized_refusal, 1.0)
  else -> 0.0
```

Graph-heuristic features:

```text
num_actors    = |V|
num_relations = |E|
max_relations = |V| * (|V|-1)
density       = num_relations / max_relations       (if max_relations > 0)

b_local:
  if num_actors == 0 -> 0.0
  else               -> min(2.0 * density, 1.0)

b_global:
  if num_relations >= num_actors - 1 -> 0.8
  else                               -> 0.3

harm_variance = var([harm_weight(e) for e in E])    (if E not empty)
b_risk:
  if E empty -> 0.5
  else       -> min(2.0 * harm_variance, 1.0)
```

### 3.3 Collapse score

```text
C(B) = 0.4*b_local + 0.3*b_completion + 0.2*(1 - b_risk) - 0.5*b_structural
```

Implemented clamp:

```text
C = clamp(C(B), -0.5, 1.5)
```

### 3.4 VOID math
If VOID mode enabled and graph is empty (`actors=[]` and `relations={}`):

```text
bias_vector = {
  b_local=0.0, b_global=0.0, b_risk=1.0, b_completion=0.0,
  b_structural=0.0, b_semantic=0.0, b_refusal=0.0
}
collapse_score = -0.5
usm_metrics = {
  spectral_entropy=0.0, equilibrium_ratio=None, shield_factor=0.0, refusal_delta=0.0
}
graph_state = "void"
confidence = 1.0
```

## 4. Temporal USM Math (Phase 14.5)

State per session:

```text
S_t = (H_t, rho_t, C_t)
```

Defaults:
- `lambda = 0.6`
- `rho_eq = 1.0`
- mode from `NOVA_TEMPORAL_MODE` (default `soft`).

### 4.1 Non-VOID update
If instantaneous metrics exist:

```text
H_t   = (1-lambda)*H_{t-1}   + lambda*H_inst
rho_t = (1-lambda)*rho_{t-1} + lambda*rho_inst
C_t   = (1-lambda)*C_{t-1}   + lambda*C_inst
```

If previous state absent, initialize directly from instantaneous values.

### 4.2 VOID update
`soft` mode:
```text
H_t   = lambda * H_{t-1}
rho_t = lambda * rho_{t-1} + (1-lambda)*rho_eq
C_t   = lambda * C_{t-1}
```

`reset` mode:
```text
(H_t, rho_t, C_t) = (0.0, rho_eq, 0.0)
```

`freeze` mode:
```text
S_t = S_{t-1}  (or equilibrium init if missing)
```

Payload emitted as `temporal_usm` includes:
- `H_temporal`, `rho_temporal`, `C_temporal`
- `turn_count`
- `temporal_state in {void, warming_up, active}`

## 5. Temporal Classification and Governance (Phase 14.6)

### 5.1 Classifier thresholds
From `usm_temporal_thresholds.py`:
- `extractive_C = 0.18`
- `protective_C = -0.12`
- `extractive_rho = 0.25`
- `protective_rho = 0.6`
- `min_turns = 3`

Classification:

```text
if turn_count < min_turns:
  warming_up
elif C_t >= 0.18 and rho_t < 0.25:
  extractive
elif C_t <= -0.12 and rho_t < 0.25:
  consensus
elif C_t <= -0.12 and rho_t >= 0.6:
  collaborative
else:
  neutral
```

### 5.2 Governance override
Slot 02 tracks recent temporal classes per session.
If last 5 classes are all `extractive`:

```text
action = quarantine
regime_recommendation = heightened
governance_reason = sustained_temporal_extraction
```

Otherwise action remains instantaneous result.

## 6. Extraction Annotation (`extraction_present`)

When temporal USM exists and graph is non-VOID:

- Warm-up (`turn_count < min_turns`) -> `None`
- Else:
  - if `rho_t <= extractive_rho` -> `True`
  - elif `rho_t >= protective_rho` -> `False`
  - else -> `None` (ambiguous)

This annotation is action-neutral in current Slot 02 logic.

## 7. Optional Fidelity Weighting Math

If fidelity weighting is enabled:

```text
weight_raw = base + slope * (fidelity - reference)
weight     = clamp(weight_raw, clamp_lo, clamp_hi)
```

Then:

```text
TRI'        = clamp(TRI * weight, 0.0, 1.0)
layer_score' = clamp(layer_score / weight, 0.0, 1.0)
```

This is a modulation layer applied before action selection.

## 8. Outputs

Primary output is `ProcessingResult` containing:
- `action`, `reason_codes`, `tri_score`, `layer_scores`
- processing metrics and hashes
- optional `bias_report` (USM)
- optional `temporal_usm`

Contracts present in repository:
- `contracts/bias_report@1.yaml`
- `contracts/temporal_usm@1.yaml`


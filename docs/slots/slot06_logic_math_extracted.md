# Slot 06 Logic and Math Extraction

This document extracts Slot 06 behavior from implementation code in:
- `src/nova/slots/slot06_cultural_synthesis/engine.py`
- `src/nova/slots/slot06_cultural_synthesis/adapter.py`
- `src/nova/slots/slot06_cultural_synthesis/context_aware_synthesis.py`
- `src/nova/slots/slot06_cultural_synthesis/multicultural_truth_synthesis.py`
- `src/nova/slots/slot06_cultural_synthesis/receiver.py`
- `src/nova/orchestrator/contracts/decay.py`
- `src/nova/orchestrator/unlearn_weighting.py`
- `src/nova/orchestrator/adapters/slot6_cultural.py`
- `src/nova/slots/slot06_cultural_synthesis/plugin.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `26256d0`: "Slot 6 v6.5 multicultural truth synthesis"
- `dcc09f0`: "replace slot6 engine with cultural synthesis"

## 1. Runtime Logic

### 1.1 Core synthesis path (`CulturalSynthesisEngine.synthesize`)
Slot06 engine computes three core metrics from profile/content inputs:
1. `adaptation_effectiveness`
2. `principle_preservation_score` (and alias `principle_preservation`)
3. `residual_risk`

It always returns contract keys:
- `policy_actions` (default `[]`)
- `forbidden_hits` (default `[]`)
- `consent_required` (default `False`)

### 1.2 Guardrail validation path (`CulturalSynthesisAdapter.validate_cultural_deployment`)
Decision flow:
1. Normalize Slot2 result (`_coalesce_slot2`).
2. Optionally read canonical TRI signal from mirror (`slot04.tri_truth_signal`).
3. Run Slot06 engine synthesis with normalized values.
4. Clamp compliance score (`pps`) into `[0,1]`.
5. Apply threshold decision tree:
   - consent block
   - hard block rules
   - transformation rules
   - approve otherwise.
6. Emit optional metrics and return `GuardrailValidationResult`.

### 1.3 Context-aware path (`ContextAwareCulturalSynthesis`)
Context-enhanced wrapper:
1. Pull Slot7 context from semantic mirror (`breaker_state`, `pressure_level`, `resource_status`, `health_summary`, optional `phase_lock`).
2. Cache context (TTL 30s).
3. Run base synthesis (or fallback synthesis).
4. Apply adaptations:
   - pressure-based complexity reduction
   - breaker-state adaptations
   - resource optimizations
   - phase-lock depth control (feature-gated)
5. Attach `_context` metadata and optionally publish Slot6 context back to mirror.

### 1.4 Legacy compatibility path
`multicultural_truth_synthesis.py` is a deprecated compatibility shim:
- optional hard block via `NOVA_BLOCK_LEGACY_SLOT6=1`
- wrapper aliases for legacy names
- `ProfileWrapper` supplies conservative defaults if missing:
  - `adaptation_effectiveness=0.0`
  - `principle_preservation_score=0.0`
  - `residual_risk=1.0`

### 1.5 Slot06 unlearn receiver path
`receiver.py` handles unlearn pulses:
1. Reads contract age.
2. Reads Slot7 backpressure.
3. Computes anomaly multiplier + dynamic half-life.
4. Applies exponential half-life decay to pulse weight.
5. Records decay metrics.

## 2. Core Synthesis Math (`engine.py`)

Config defaults:
- `ideology_penalty = 0.05`
- `tri_min_score = 0.8`
- method weights:
  - `scientific_empiricism=0.9`
  - `greek_logic=0.8`
  - `indigenous_longterm=0.8`
  - `confucian_precision=0.7`
  - `buddhist_impermanence=0.7`

All major numeric outputs are clamped to `[0,1]`.
Invalid numeric conversion defaults to `0.5` in `_clamp`.

### 2.1 Adaptation effectiveness

Let:
- `c = clamp(clarity)`
- `f = clamp(foresight)`
- `e = clamp(empiricism)`

Then:

```text
adaptation_effectiveness =
  0.35*0.9*e
  + 0.25*0.8*c
  + 0.25*0.8*f
  + 0.10*0.7*c
  + 0.05*0.7*(1 - 2*abs(0.5 - f))
```

Then clamp to `[0,1]`.

### 2.2 Principle preservation

```text
penalty = (0.05 if ideology_push else 0.0)
base_penalty = 1 - clamp(anchor_confidence)
penalty += base_penalty / (tri_score + 0.1)
principle_preservation = clamp(1 - penalty)
```

`tri_score` parse failures fall back to `0.5`; negative values are floored at `0.0`.

### 2.3 Residual risk

```text
risk = max(layer_scores.values()) if layer_scores else 0
tri_gap = max(0, tri_min_score - tri_score)
```

If `tri_score < 0.3`:

```text
base_risk = max(0.6, 0.5*risk + 0.5*tri_gap)
```

Else:

```text
base_risk = 0.5*risk + 0.5*tri_gap
```

Then clamp to `[0,1]`.

### 2.4 Slot2 threat bridge helper
`slot2_threat_bridge` computes:

```text
risk = max(layer_scores.values()) if present else 0
tri_gap = max(0, tri_min_score - tri_score)
threat_level = min(1, 0.5*risk + 0.5*tri_gap)   if not already provided
```

## 3. Guardrail Decision Math (`adapter.py`)

Decision thresholds:
- `RISK_BLOCK = 0.70`
- `RISK_TRANSFORM = 0.40`
- `PPS_MIN = 0.40`
- `PPS_BLOCK = 0.30`

`pps` is clamped to `[0,1]` before decisions.

### 3.1 Decision tree (order-sensitive)
1. If consent required or consent missing:
   - `BLOCKED_CULTURAL_SENSITIVITY`
2. Else if forbidden hits and (`residual >= 0.70` or `pps < 0.30`):
   - `BLOCKED_PRINCIPLE_VIOLATION`
3. Else if (`residual >= 0.70` or `pps < 0.30`):
   - `BLOCKED_PRINCIPLE_VIOLATION`
4. Else if any of:
   - forbidden hits
   - `residual >= 0.40`
   - `pps < 0.40`
   - action `"rephrase:high-risk"`
   then:
   - `REQUIRES_TRANSFORMATION`
5. Else:
   - `APPROVED`

### 3.2 TRI truth-signal override
If mirror provides canonical TRI signal:
- `tri_coherence` is used as `tri_score`
- recompute:

```text
tri_gap = max(0, tri_min_score - tri_coherence)
```

And pass `tri_band`, `anchor_id`, `tri_drift_z` through result metadata.

## 4. Context-Aware Adaptation Math (`context_aware_synthesis.py`)

### 4.1 Pressure bands
- `critical` if pressure `>= 0.95`
- `high` if pressure `>= 0.8`
- `medium` if pressure `>= 0.6`
- `low` otherwise

### 4.2 Pressure complexity reduction
Reduction factors:
- `medium -> 0.8`
- `high -> 0.6`
- `critical -> 0.4`

If `complexity_factor` exists:

```text
complexity_factor *= reduction_factor
```

For `high/critical`, set `cultural_nuance_depth="simplified"` and cap recommendations to top 3.

### 4.3 Breaker-state adaptations
- breaker `open`:
  - `synthesis_mode="conservative"`
  - `risk_tolerance="low"`
  - `adaptation_rate = min(adaptation_rate, 0.3)` (if present)
  - `innovation_factor *= 0.5` (if present)
- breaker `half-open`:
  - `synthesis_mode="cautious"`
  - `adaptation_rate = min(adaptation_rate, 0.6)` (if present)

### 4.4 Resource adaptation
If resource utilization `> 0.7`:
- `computational_complexity="optimized"`
- `caching_strategy="aggressive"`
- `cultural_model_depth = min(cultural_model_depth, 3)` (if present)

### 4.5 Phase-lock depth control (`NOVA_LIGHTCLOCK_DEEP=1`)
Given `phase_lock`:

- if `>0.8`:
  - depth `deep`, layers `5`, confidence `min(1, 1.1*phase_lock)`
- elif `>0.6`:
  - depth `standard`, layers `3`, confidence `phase_lock`
- elif `>0.4`:
  - depth `shallow`, layers `2`, confidence `0.8*phase_lock`
- else:
  - depth `minimal`, layers `1`, confidence `max(0.1, 0.6*phase_lock)`

Additional scaling:

```text
adaptation_effectiveness *= (0.5 + 0.5*phase_lock)      # if field present
principle_preservation = min(1, principle_preservation + 0.2*phase_lock)   # if field present
```

## 5. Slot06 Unlearn/Decay Math (`receiver.py` + decay utilities)

### 5.1 Pulse weight decay
`receiver.py` computes:

```text
base_weight = 1.0 * get_anomaly_multiplier(slot="slot06")
half_life = get_dynamic_half_life(base_half_life=300.0, slot="slot06")
half_life *= (1 - 0.20*backpressure_level)
effective_weight = pulse_weight_decay(base_weight, age_seconds, half_life)
```

From `pulse_weight_decay`:

```text
decay_rate = ln(2)/half_life
effective_weight = base_weight * exp(-decay_rate*age_seconds)
```

Equivalent half-life form:

```text
effective_weight = base_weight * 2^(-age_seconds/half_life)
```

Decay metric increment:

```text
decay_amount = max(0, base_weight - effective_weight)
```

### 5.2 Dynamic half-life (anomaly module)
When anomaly mode enabled:

```text
tri_multiplier = 1 + 2*ewma_tri
pressure_divisor = 1 + 1.5*ewma_pressure
dynamic_half_life = base_half_life * tri_multiplier / pressure_divisor
dynamic_half_life = clamp(dynamic_half_life, min_half_life, max_half_life)
```

Defaults:
- `min_half_life=60`
- `max_half_life=1800`

Slot06 default anomaly component weights:
- `tri_drift_z=0.7`
- `system_pressure=0.5`
- `phase_jitter=0.1`

## 6. Plugin Contract Logic (`plugin.py`)

`CULTURAL_PROFILE@1` adapter:
- passes payload to `engine.synthesize(...)`
- includes `institution` in output
- on failure returns conservative fallback:
  - `residual_risk=0.8`
  - `consent_required=True`
  - neutral 0.5 scores for adaptation/principle fields.

## 7. What Slot06 Math Is in Practice

Slot06 combines:
- deterministic weighted scoring (adaptation/principle/risk),
- threshold-based guardrail classification,
- context-conditioned heuristic modulation (pressure/breaker/resource/phase-lock),
- exponential decay mechanics for unlearn pulse handling.

It is rule-based and bounded; no learned model inference is used in current Slot06 implementation.

# Slot 06 Canonical Equation Sheet

Source anchors:
- `src/nova/slots/slot06_cultural_synthesis/engine.py`
- `src/nova/slots/slot06_cultural_synthesis/adapter.py`
- `src/nova/slots/slot06_cultural_synthesis/context_aware_synthesis.py`
- `src/nova/slots/slot06_cultural_synthesis/receiver.py`
- `src/nova/orchestrator/contracts/decay.py`
- `src/nova/orchestrator/unlearn_weighting.py`

## 1. Core Synthesis Equations

Defaults:
- `tri_min_score = 0.8`
- `ideology_penalty = 0.05`
- method weights:
  - `scientific_empiricism=0.9`
  - `greek_logic=0.8`
  - `indigenous_longterm=0.8`
  - `confucian_precision=0.7`
  - `buddhist_impermanence=0.7`

All outputs are clamped to `[0,1]`.

### 1.1 Adaptation effectiveness

```text
c = clamp(clarity)
f = clamp(foresight)
e = clamp(empiricism)

adaptation_effectiveness =
  clamp(
    0.35*0.9*e +
    0.25*0.8*c +
    0.25*0.8*f +
    0.10*0.7*c +
    0.05*0.7*(1 - 2*abs(0.5-f))
  )
```

### 1.2 Principle preservation

```text
penalty = (0.05 if ideology_push else 0.0)
base_penalty = 1 - clamp(anchor_confidence)
penalty += base_penalty / (tri_score + 0.1)
principle_preservation_score = clamp(1 - penalty)
```

### 1.3 Residual risk

```text
risk = max(layer_scores.values()) if any else 0
tri_gap = max(0, tri_min_score - tri_score)

if tri_score < 0.3:
  base_risk = max(0.6, 0.5*risk + 0.5*tri_gap)
else:
  base_risk = 0.5*risk + 0.5*tri_gap

residual_risk = clamp(base_risk)
```

## 2. Guardrail Decision Thresholds

Constants:
- `RISK_BLOCK = 0.70`
- `RISK_TRANSFORM = 0.40`
- `PPS_BLOCK = 0.30`
- `PPS_MIN = 0.40`

Decision order:

```text
if consent_required or not consent_ok:
  BLOCKED_CULTURAL_SENSITIVITY
elif forbidden_hits and (residual>=0.70 or pps<0.30):
  BLOCKED_PRINCIPLE_VIOLATION
elif residual>=0.70 or pps<0.30:
  BLOCKED_PRINCIPLE_VIOLATION
elif forbidden_hits or residual>=0.40 or pps<0.40 or "rephrase:high-risk" in policy_actions:
  REQUIRES_TRANSFORMATION
else:
  APPROVED
```

Where `pps = clamp(principle_preservation_score, 0, 1)`.

## 3. TRI Truth-Signal Override

If canonical TRI signal exists:

```text
tri_score <- tri_coherence
tri_gap <- max(0, tri_min_score - tri_coherence)
```

Pass-through metadata: `tri_band`, `anchor_id`, `tri_drift_z`.

## 4. Context-Aware Adaptation Rules

### 4.1 Pressure classification

```text
critical if pressure>=0.95
high     if pressure>=0.80
medium   if pressure>=0.60
low      otherwise
```

### 4.2 Complexity reduction by pressure

```text
reduction_factor:
  medium -> 0.8
  high -> 0.6
  critical -> 0.4

complexity_factor *= reduction_factor
```

For `high/critical`: `cultural_nuance_depth="simplified"`, recommendations capped to top 3.

### 4.3 Breaker-state adaptations

```text
if breaker_state=="open":
  synthesis_mode="conservative"
  risk_tolerance="low"
  adaptation_rate=min(adaptation_rate,0.3)       (if present)
  innovation_factor*=0.5                         (if present)

if breaker_state=="half-open":
  synthesis_mode="cautious"
  adaptation_rate=min(adaptation_rate,0.6)       (if present)
```

### 4.4 Resource adaptation

```text
if resource_utilization > 0.7:
  computational_complexity="optimized"
  caching_strategy="aggressive"
  cultural_model_depth=min(cultural_model_depth,3)   (if present)
```

### 4.5 Phase-lock depth control (`NOVA_LIGHTCLOCK_DEEP=1`)

For phase lock `p`:

```text
if p>0.8:
  depth=deep, layers=5, adaptation_confidence=min(1,1.1*p)
elif p>0.6:
  depth=standard, layers=3, adaptation_confidence=p
elif p>0.4:
  depth=shallow, layers=2, adaptation_confidence=0.8*p
else:
  depth=minimal, layers=1, adaptation_confidence=max(0.1,0.6*p)
```

Additional scaling:

```text
adaptation_effectiveness *= (0.5 + 0.5*p)               (if present)
principle_preservation = min(1, principle_preservation + 0.2*p)   (if present)
```

## 5. Slot06 Unlearn Pulse Decay

### 5.1 Receiver equation

```text
base_weight = 1.0 * anomaly_multiplier(slot06)
half_life = dynamic_half_life(base=300, slot06)
half_life = half_life * (1 - 0.20*backpressure)
effective_weight = pulse_weight_decay(base_weight, age_seconds, half_life)
```

### 5.2 Half-life decay identity

```text
decay_rate = ln(2)/half_life
effective_weight = base_weight * exp(-decay_rate*age_seconds)
                = base_weight * 2^(-age_seconds/half_life)
```

Metrics:

```text
decay_amount += max(0, base_weight - effective_weight)
decay_events += 1
```

### 5.3 Dynamic half-life (anomaly module)

```text
tri_multiplier = 1 + 2*ewma_tri
pressure_divisor = 1 + 1.5*ewma_pressure
dynamic_half_life = base_half_life * tri_multiplier / pressure_divisor
dynamic_half_life = clamp(dynamic_half_life, min_half_life, max_half_life)
```

Defaults: `min=60`, `max=1800`.

## 6. Legacy Compatibility Controls

```text
if NOVA_BLOCK_LEGACY_SLOT6 == "1":
  importing multicultural_truth_synthesis raises ImportError
```

`ProfileWrapper` fallback defaults:

```text
adaptation_effectiveness=0.0
principle_preservation_score=0.0
residual_risk=1.0
```

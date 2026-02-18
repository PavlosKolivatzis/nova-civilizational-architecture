# Slot 03 Logic and Math Extraction

This document extracts Slot 03 logic and mathematics from implementation code:
- `src/nova/slots/slot03_emotional_matrix/emotional_matrix_engine.py`
- `src/nova/slots/slot03_emotional_matrix/escalation.py`
- `src/nova/slots/slot03_emotional_matrix/enhanced_engine.py`
- `src/nova/slots/slot03_emotional_matrix/advanced_policy.py`
- `src/nova/slots/slot03_emotional_matrix/safety_policy.py`
- `src/nova/continuity/emotional_posture.py` (optional ORP constriction path used by Slot03)

## 1. What Slot 03 Is (Mathematically)

Slot03 is a deterministic, rule-based affect classifier and escalation gate.
It is not a probabilistic model and does not implement Bayesian/Kalman/state-estimation math.

## 2. Core Emotional Score Math

### 2.1 Lexicon-based signal accumulation
Slot03 tokenizes input and accumulates sentiment strength:

- Positive tokens add to `pos`
- Negative tokens add to `neg`
- Intensifiers scale token magnitude (`boosters`/`dampeners`)
- Negation flips polarity for a local window (`negation_window`, default 3)

### 2.2 Score equation

```text
total_signal = pos + neg

score_raw =
  0                                  if total_signal == 0
  (pos - neg) / total_signal         otherwise
```

Then exclamation emphasis:

```text
if "!" present and score_raw >= 0:
  score_raw = score_raw * 1.05
```

Final clamped score:

```text
score = clamp(score_raw, -1.0, 1.0)
```

### 2.3 Tone thresholds
Config defaults:
- `positive_threshold = 0.10`
- `negative_threshold = -0.10`

Mapping:

```text
if score >= positive_threshold: tone = positive
elif score <= negative_threshold: tone = negative
else: tone = neutral
```

### 2.4 Confidence equation

```text
confidence = min(1.0, matched_sentiment_tokens / (len(tokens) + 2))
```

## 3. VOID Dormancy Logic (Phase 14.4)

For empty token stream:
- If `NOVA_ENABLE_VOID_MODE=1` and `context.graph_state == "void"`:
  - `emotional_tone = "dormant"`
  - `score = None`
  - `confidence = 1.0`
- Else legacy fallback:
  - `emotional_tone = "unknown"`
  - `score = 0.0`
  - `confidence = 0.0`

This is semantic null handling, not affect negativity.

## 4. Light-Clock Phase-Lock Math

### 4.1 Phase-lock value selection
If `NOVA_LIGHTCLOCK_DEEP=0` -> `phase_lock = None`.

Otherwise selection order:
1. `tri_coherence` from TRI truth signal if available.
2. `slot04.phase_coherence` from mirror.
3. pressure mapping from `slot07.pressure_level`:

```text
phase_lock = 0.60 - 0.15 * pressure
pressure clamped to [0, 1]
```

4. env fallback: `SLOT07_PHASE_LOCK`
5. hard default: `0.5`

### 4.2 Coherence-aware score damping
Threshold:
- `NOVA_EMO_PHASE_LOCK_THRESH` (default `0.6`)

If `phase_lock < threshold`, then:

```text
score = score * 0.8
```

(20% amplitude reduction, valence preserved by multiplication).

## 5. Optional ORP Emotional Constriction Math

Activated only when `NOVA_ENABLE_EMOTIONAL_CONSTRICTION=1`.

### 5.1 Regime multiplier table
From `src/nova/continuity/emotional_posture.py`:

- `normal` -> `1.00`
- `heightened`:
  - `< 300s` -> `0.95`
  - `>= 300s` -> `0.85`
- `controlled_degradation` -> `0.70`
- `emergency_stabilization` -> `0.50`
- `recovery` -> `0.60`

Unknown regime defaults to `1.00`.

### 5.2 Constriction equation
Slot03 converts signed score to intensity:

```text
intensity = abs(score)
intensity_constricted = clamp(intensity * multiplier, 0.0, 1.0)
score_constricted = sign(score) * intensity_constricted
```

Score is updated only when constriction reduces magnitude.
Valence sign is preserved.

## 6. Threat Classification Math (Escalation Manager)

From `src/nova/slots/slot03_emotional_matrix/escalation.py`:

```text
if confidence > 0.8 and score < -0.8 and tone in {anger, hatred, violence}:
  CRITICAL
elif confidence > 0.7 and score < -0.6 and tone in {anger, fear, disgust}:
  HIGH
elif confidence > 0.5 and score < -0.4:
  MEDIUM
elif score < -0.2 or confidence < 0.3:
  LOW
else:
  LOW
```

Routing map:
- `CRITICAL` -> Slot01, Slot04, Slot07
- `HIGH` -> Slot01, Slot04
- `MEDIUM` -> Slot04
- `LOW` -> none

## 7. Enhanced Wrapper Escalation Trigger (Pre-classifier)

From `enhanced_engine.py`:

```text
escalate if (confidence > 0.6 and score < -0.3)
or (tone in {anger, fear, disgust} and confidence > 0.5)
```

This is a lightweight trigger gate before/around full escalation handling.

## 8. Safety Policy / Rate-Limit Math

### 8.1 Sliding-window limiter (`RateLimiter`)
For each identifier:
- Keep timestamps within `window_seconds`
- Allow if `count < max_requests`

### 8.2 Token-bucket limiter (`AdvancedSafetyPolicy.rate_limit_ok`)

```text
allow_per_min = rate_per_min
refill = (now - last_ts) * (allow_per_min / 60)
tokens = min(allow_per_min, tokens + refill)

if tokens < 1: deny
else: tokens = tokens - 1, allow
```

### 8.3 Safety aggregate metric

```text
violation_rate = violations_detected / max(1, total_checks)
safety_effectiveness = 1.0 - violation_rate
```

## 9. What Math Is Not Present in Slot03

Not implemented in Slot03 code:
- Bayesian filtering
- Kalman filtering
- Learned embeddings/ML model inference
- Probabilistic calibration curves
- Continuous-time differential models

Current Slot03 math is deterministic thresholding, bounded arithmetic, and multiplicative modulation.


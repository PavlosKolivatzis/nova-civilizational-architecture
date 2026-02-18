# Slot 04 Logic and Math Extraction

This document extracts Slot 04 behavior from implementation code in:
- `src/nova/orchestrator/adapters/slot4_tri.py`
- `src/nova/slots/slot04_tri/core/tri_engine.py`
- `src/nova/slots/slot04_tri/core/detectors.py`
- `src/nova/slots/slot04_tri/core/repair_planner.py`
- `src/nova/slots/slot04_tri/core/safe_mode.py`
- `src/nova/slots/slot04_tri/core/snapshotter.py`
- `src/nova/slots/slot04_tri/wisdom_feedback.py`
- `src/nova/slots/slot04_tri/core/variance_decay.py`
- `src/nova/slots/slot04_tri/core/temporal_schema.py`
- `src/nova/slots/slot04_tri_engine/engine.py`
- `src/nova/slots/slot04_tri_engine/tri_truth_signal.py`
- `src/nova/slots/slot04_tri_engine/ids_integration.py`
- `src/nova/orchestrator/tri_truth_bridge.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `8601b42`: "Add TRI engine with Bayesian-Kalman status tracking"
- `13e32c6`: "Complete Phase 6.0 TRI belief state publication"
- `1f62f30`: "complete TRI truth canonization & slot realignment"

## 1. Runtime Logic

### 1.1 Dual-engine architecture (implemented)
Slot 04 currently has two runtime TRI engines, routed by adapter:

1. Operational/process engine:
- `nova.slots.slot04_tri.core.tri_engine.TriEngine`
- Used for `get_latest_report()` health/coherence outputs.

2. Content-analysis engine:
- `nova.slots.slot04_tri_engine.engine.TRIEngine`
- Used for `calculate(content, context)` content scoring.

Adapter behavior (`Slot4TRIAdapter`):
- `get_latest_report()`:
  - uses operational engine `assess()` when available
  - else returns deterministic fallback:
    - `coherence=0.7`, `phase_jitter=0.15`, `tri_score=0.75`
  - then tries truth-signal canonicalization via TRI bridge.
- `calculate()`:
  - tries content engine first
  - then operational engine `calculate()` fallback
  - then final no-op fallback payload.

### 1.2 Operational path (`slot04_tri.core.tri_engine.TriEngine`)
Main logic:
1. `observe(features, writes_in_last_sec)` computes bounded TRI score.
2. Updates running mean/std state.
3. Updates adaptive threshold and baseline.
4. Runs drift and surge detectors.
5. `assess()` returns `Health` with TRI coherence signals.
6. `auto_heal_once()` performs recovery decision (restore/safe-mode/noop).

### 1.3 Content-analysis path (`slot04_tri_engine.engine.TRIEngine`)
Main logic:
1. Extract feature vector from content/context.
2. Bayesian update (Beta posterior).
3. Kalman smoothing update.
4. Compute confidence interval, confidence score, layer analysis, pattern flags.
5. Publish TRI signals to Semantic Mirror (best effort).

### 1.4 TRI truth signal path
From adapter report:
1. Canonicalize (`canonicalize_truth_signal`)
2. Compute band/hash/anchor id
3. Publish to semantic mirror
4. If `NOVA_SLOT01_ROOT_MODE=1`, optionally register Slot01 anchor attestation.

## 2. Operational Engine Math (`slot04_tri`)

### 2.1 Running statistics (Welford-style)
For each observed score `x`:

```text
n <- n + 1
delta <- x - mean
mean <- mean + delta / n
m2 <- m2 + delta * (x - mean)
```

Sample standard deviation:

```text
std = sqrt(m2 / (n - 1))   if n > 1
std = 0                    otherwise
```

### 2.2 TRI score from feature dict

```text
score_raw = sum(0.1 * feature_i for all features)
score = clamp(score_raw, 0.0, 1.0)
```

### 2.3 Adaptive threshold + baseline dynamics
If `score > threshold`:

```text
threshold <- threshold + alpha_up * (max(score, baseline) - threshold)
```

Else:

```text
threshold <- threshold + revert_k * (baseline - threshold)
```

Then apply floor/cap:

```text
threshold <- max(0.0, max(min_rel_baseline * baseline, min(0.95, threshold)))
```

Baseline update:

```text
baseline <- 0.9 * baseline + 0.1 * score
```

Default policy constants:
- `alpha_up=0.4`
- `revert_k=0.6`
- `min_rel_baseline=0.9`

### 2.4 Drift detector math
Rolling O(1) sums over window `W`:

```text
mean = sum / n
var_pop = (sum2 / n) - mean^2
var_unbiased = var_pop * n/(n-1)    (n > 1)
std = sqrt(var_unbiased)
z = |(value - mean) / (std + 1e-12)|
```

Trigger condition:
- warmed up (`n >= max(10, int(min_warm_frac * W))`)
- and `z >= z_threshold` (default `3.0`)

### 2.5 Surge detector math
Rolling sum over integer counts in fixed window:

```text
window_sum = sum(last_window_counts)
```

Trigger when:
- window is full
- `window_sum > threshold` (strict greater-than)
- cooldown elapsed

Default policy:
- `surge_window=10`
- `surge_threshold=50`

### 2.6 Coherence signal equations (`assess`)
When `NOVA_LIGHTCLOCK_DEEP=1`:

```text
tri_score = clamp(mean, 0, 1)              if n > 0 else 0.5
cv = std / max(0.001, |mean|)
coherence = clamp(1 / (1 + cv), 0, 1)      if n >= 2 else 1.0
phase_jitter = clamp(|last_drift_z| / 3, 0, 1)
```

When `NOVA_LIGHTCLOCK_DEEP=0`:
- `tri_score=None`, `coherence=None`, `phase_jitter=None`

### 2.7 Confidence interval
Normal approximation:

```text
z = 1.96  (conf >= 0.95)
z = 1.64  (otherwise)
CI = [ clamp(mean - z*std, 0, 1), clamp(mean + z*std, 0, 1) ]
```

### 2.8 Auto-heal decision logic
If `drift_z` not set/truthy, engine estimates:

```text
drift_z <- |(mean - baseline) / (std + 1e-9)|
```

Planner rules:
- if `not data_ok` or `not perf_ok` or `drift_z >= 3.0`:
  - restore previous snapshot if available
  - else safe-mode block
- else `NOOP`

Outcome tracking uses Beta(1,1)-smoothed success rate:

```text
success_rate(action) = (successes + 1) / (successes + failures + 2)
```

### 2.9 Optional content scoring path (`TriEngine.calculate`)
Feature-gated by:
- `NOVA_ENABLE_TRI_LINK=1` required

If disabled: returns all-zero stub payload.

Implemented feature extraction:

```text
length_factor        = min(1, len(content)/1000)
word_density         = words / max(1, char_count)
sentence_complexity  = sentence_count / max(1, words)
caps_ratio           = uppercase_chars / max(1, char_count)
punctuation_density  = punct_chars("!?.,;:") / max(1, char_count)
uniqueness           = unique_lower_words / max(1, words)
```

Layer scores:

```text
structural = clamp((length_factor + sentence_complexity)/2, 0, 1)
semantic   = clamp((word_density + uniqueness)/2, 0, 1)
expression = clamp((caps_ratio + punctuation_density)/2, 0, 1)
```

Alias mapping:
- `delta <- structural`
- `sigma <- semantic`
- `theta <- expression`

## 3. Secondary Engine Math (`slot04_tri_engine`)

### 3.1 Base score

```text
base_score = mean(clamp(vector_i, 0, 1))
```

### 3.2 Bayesian update (Beta posterior)
Given cleaned vector values in `[0,1]`:

```text
successes = sum(vector_i)
failures = len(vector) - successes
alpha_post = alpha_prior + successes
beta_post  = beta_prior + failures
```

Beta mean and variance:

```text
measurement = alpha_post / (alpha_post + beta_post)
meas_var = (alpha_post * beta_post) /
           ((alpha_post + beta_post)^2 * (alpha_post + beta_post + 1))
```

### 3.3 Kalman smoothing (1D)

```text
prior_var = prev_variance + process_variance
K = prior_var / (prior_var + meas_var)
estimate = prior_est + K * (measurement - prior_est)
variance = (1 - K) * prior_var
```

Default `process_variance = 0.01`.

95% interval:

```text
std = sqrt(max(variance, 0))
ci_low  = clamp(estimate - 1.96*std, 0, 1)
ci_high = clamp(estimate + 1.96*std, 0, 1)
```

### 3.4 Content feature vector (engine 2)

```text
length_score = 2/(1 + exp(-len(content)/1000)) - 1
length_score = clamp(length_score, 0, 1)

diversity_score = min(1, unique_chars/26)
word_score = min(1, avg_word_len/10)      (or 0 if no words)
punct_ratio = min(1, punct_non_alnum_non_space / max(1, len(content)))

source_trusted feature = 0.8 if true else 0.3
verified feature       = 0.9 if true else 0.5
```

### 3.5 Layer math (engine 2)
- Syntactic:

```text
balance_score = 1 - |open_brackets - close_brackets| / max(1, len(content))
syntactic = clamp(balance_score, 0, 1)
```

- Semantic:

```text
semantic = min(1, repeated_word_types / unique_word_types)   if >2 words
semantic = 0.3                                                otherwise
```

- Pragmatic:

```text
pragmatic = min(1, 0.5 + 0.2*[domain_present] + 0.2*[purpose_present])
```

### 3.6 Confidence scoring (engine 2)

```text
base_confidence = 1 / (1 + variance)
iteration_boost = min(0.3, iterations/20)
ci_confidence = 1 - (ci_high - ci_low)

confidence_raw =
    0.5 * base_confidence
  + 0.3 * (base_confidence + iteration_boost)
  + 0.2 * ci_confidence

confidence = clamp(confidence_raw, 0, 1)
```

### 3.7 Derived TRI report signals (engine 2)

```text
coherence = estimate
phase_coherence = min(1, estimate + 0.1)
phase_jitter = max(0, 1 - estimate)
```

## 4. Canonical Truth Signal, IDS, and Auxiliary Slot04 Math

### 4.1 TRI truth-signal canonicalization
From report:

```text
coherence = clamp(report.coherence or report.tri_score or 0, 0, 1)
```

Drift derivation:
- if `drift_z` provided: use/clamp it
- else:

```text
baseline = report.tri_mean or coherence
drift = 0                               if baseline == 0
drift = (coherence - baseline) / 0.05   otherwise
drift = clamp(drift, -5, 5)
```

Jitter derivation:
- if provided, cast+clamp
- else `max(0, 1 - coherence)`
- final clamp `[0, 0.5]`

Band mapping:
- `green` if coherence `>= 0.72`
- `amber` if coherence `>= 0.50`
- `red` otherwise

Canonical hash:
- rounded JSON payload
- `blake2b(..., digest_size=32)`
- `anchor_id = "tri::" + first16hex`

### 4.2 IDS integration math (optional path)
If IDS enabled and not sandbox-only:

```text
stability_factor = stability^2
drift_penalty = |drift| * 0.3

adjusted =
  base_score * ((1 - IDS_WEIGHT) + IDS_WEIGHT * stability_factor)
  - IDS_WEIGHT * drift_penalty

final_score = base_score + clamp(adjusted - base_score, -0.15, +0.15)
final_score = clamp(final_score, 0, 1)
```

Defaults from `config/feature_flags.py`:
- `IDS_ENABLED=True`
- `IDS_WEIGHT=0.1`
- `IDS_SANDBOX_ONLY=True` (so adjustment is bypassed unless changed)

### 4.3 Wisdom feedback math (`slot04_tri/wisdom_feedback.py`)
Coherence-to-learning-rate-cap mapping:

```text
C = clamp(coherence, 0, 1)

if C >= high_thresh: eta_cap = eta_high
elif C <= low_thresh: eta_cap = eta_low
else:
  eta_cap = eta_low + (eta_high - eta_low) * (C - low_thresh)/(high_thresh - low_thresh)
```

Default parameters:
- `high_thresh=0.85`
- `low_thresh=0.40`
- `eta_high=0.18`
- `eta_low=0.08`

### 4.4 Temporal variance-decay math (Slot04 auxiliary modules)
In `variance_decay.py` and `temporal_schema.py`:

```text
decay_weight = exp(-variance * temporal_distance)
```

Temporal coherence aggregate (harmonic mean):

```text
temporal_coherence_score = 2 * trsi * decay / (trsi + decay)    if trsi>0 and decay>0
temporal_coherence_score = 0.5                                   otherwise
```

## 5. What Slot04 Math Is in Practice

Slot04 currently combines:
- deterministic control math (adaptive thresholds, detectors, safe-mode routing),
- probabilistic estimation math (Beta + Kalman in content engine),
- bounded heuristic feature math (both engines),
- canonicalization/attestation logic for truth signal transport.

It is not a single unified TRI equation; it is a routed, multi-path implementation.

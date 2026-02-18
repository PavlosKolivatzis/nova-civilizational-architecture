# Slot 04 Canonical Equation Sheet

Source anchors:
- `src/nova/slots/slot04_tri/core/tri_engine.py`
- `src/nova/slots/slot04_tri/core/detectors.py`
- `src/nova/slots/slot04_tri/core/repair_planner.py`
- `src/nova/slots/slot04_tri/wisdom_feedback.py`
- `src/nova/slots/slot04_tri_engine/engine.py`
- `src/nova/slots/slot04_tri_engine/tri_truth_signal.py`
- `src/nova/slots/slot04_tri_engine/ids_integration.py`

## 1. Adapter Routing Logic

```text
get_latest_report():
  use operational TriEngine.assess() if available
  else fallback -> coherence=0.7, phase_jitter=0.15, tri_score=0.75
  then attach canonical truth signal (best effort)

calculate(content, context):
  try content TRIEngine.calculate()
  else try operational TriEngine.calculate()
  else final no-op score/layers=0
```

## 2. Operational TRI (`slot04_tri`)

### 2.1 Running stats

```text
n <- n + 1
delta <- x - mean
mean <- mean + delta/n
m2 <- m2 + delta*(x - mean)
std = sqrt(m2/(n-1))   if n>1 else 0
```

### 2.2 Core score

```text
score = clamp(sum_i 0.1*feature_i, 0, 1)
```

### 2.3 Adaptive threshold dynamics

```text
if score > threshold:
  threshold <- threshold + alpha_up*(max(score, baseline)-threshold)
else:
  threshold <- threshold + revert_k*(baseline-threshold)

threshold <- max(0, max(min_rel_baseline*baseline, min(0.95, threshold)))
baseline  <- 0.9*baseline + 0.1*score
```

Defaults: `alpha_up=0.4`, `revert_k=0.6`, `min_rel_baseline=0.9`.

### 2.4 Drift detector

```text
mean = sum/n
var_pop = sum2/n - mean^2
var_unbiased = var_pop * n/(n-1)
std = sqrt(var_unbiased)
z = |(value-mean)/(std+1e-12)|
```

Trigger when warmed and `z >= z_threshold` (default `3.0`).

### 2.5 Surge detector

```text
window_sum = sum(last_window_counts)
trigger iff (window full) and (window_sum > threshold) and (cooldown elapsed)
```

### 2.6 Coherence signals

```text
tri_score = clamp(mean, 0, 1)                  if n>0 else 0.5
cv = std / max(0.001, |mean|)
coherence = clamp(1/(1+cv), 0, 1)              if n>=2 else 1.0
phase_jitter = clamp(|last_drift_z|/3, 0, 1)
```

If `NOVA_LIGHTCLOCK_DEEP=0`: all three are `None`.

### 2.7 Confidence interval

```text
z = 1.96 (conf>=0.95) else 1.64
CI = [clamp(mean-z*std,0,1), clamp(mean+z*std,0,1)]
```

### 2.8 Auto-heal decision

Fallback drift estimate (when missing):

```text
drift_z <- |(mean-baseline)/(std+1e-9)|
```

Decision:

```text
if (not data_ok) or (not perf_ok) or (drift_z >= 3.0):
  if snapshot exists: RESTORE_PREV_MODEL
  else: SAFE_MODE_BLOCK
else:
  NOOP
```

Outcome success-rate update:

```text
success_rate(action) = (succ + 1)/(succ + fail + 2)
```

## 3. Content TRI (`slot04_tri_engine`)

### 3.1 Beta posterior update

```text
successes = sum(cleaned_vector)
failures  = len(vector) - successes
alpha_post = alpha_prior + successes
beta_post  = beta_prior + failures

measurement = alpha_post/(alpha_post + beta_post)
meas_var = (alpha_post*beta_post) /
           ((alpha_post+beta_post)^2 * (alpha_post+beta_post+1))
```

### 3.2 Kalman update (1D)

```text
prior_var = prev_variance + process_variance
K = prior_var/(prior_var + meas_var)
estimate = prior_est + K*(measurement - prior_est)
variance = (1-K)*prior_var
```

Default `process_variance=0.01`.

### 3.3 95% CI

```text
std = sqrt(max(variance,0))
ci_low  = clamp(estimate - 1.96*std, 0, 1)
ci_high = clamp(estimate + 1.96*std, 0, 1)
```

### 3.4 Confidence scalar

```text
base_confidence = 1/(1+variance)
iteration_boost = min(0.3, iterations/20)
ci_confidence = 1 - (ci_high - ci_low)

confidence =
  clamp(
    0.5*base_confidence +
    0.3*(base_confidence + iteration_boost) +
    0.2*ci_confidence,
    0, 1
  )
```

### 3.5 Engine-2 derived TRI outputs

```text
coherence = estimate
phase_coherence = min(1, estimate + 0.1)
phase_jitter = max(0, 1 - estimate)
```

## 4. Canonical Truth Signal

### 4.1 Canonical fields

```text
coherence = clamp(report.coherence or report.tri_score or 0, 0, 1)
```

Drift:

```text
if report.drift_z exists:
  drift = clamp(float(report.drift_z), -5, 5)
else:
  baseline = report.tri_mean or coherence
  drift = 0 if baseline==0 else (coherence-baseline)/0.05
  drift = clamp(drift, -5, 5)
```

Jitter:

```text
if report.phase_jitter exists:
  jitter = clamp(float(report.phase_jitter), 0, 0.5)
else:
  jitter = clamp(max(0, 1-coherence), 0, 0.5)
```

Band:

```text
green if coherence >= 0.72
amber if coherence >= 0.50
red otherwise
```

Hash/anchor:

```text
canonical_hash = blake2b(canonical_json_bytes, digest_size=32).hexdigest()
anchor_id = "tri::" + canonical_hash[:16]
```

## 5. IDS TRI Adjustment (optional)

Applied only when `IDS_ENABLED=True` and `IDS_SANDBOX_ONLY=False`:

```text
stability_factor = stability^2
drift_penalty = |drift| * 0.3

adjusted =
  base_score * ((1 - IDS_WEIGHT) + IDS_WEIGHT*stability_factor)
  - IDS_WEIGHT*drift_penalty

final_score = base_score + clamp(adjusted-base_score, -0.15, +0.15)
final_score = clamp(final_score, 0, 1)
```

## 6. Wisdom Feedback Mapping

```text
C = clamp(coherence, 0, 1)

if C >= high_thresh: eta_cap = eta_high
elif C <= low_thresh: eta_cap = eta_low
else:
  eta_cap = eta_low + (eta_high-eta_low)*(C-low_thresh)/(high_thresh-low_thresh)
```

Defaults:
- `high_thresh=0.85`
- `low_thresh=0.40`
- `eta_high=0.18`
- `eta_low=0.08`

## 7. Temporal Decay (auxiliary Slot04 math)

```text
decay_weight = exp(-variance * temporal_distance)

temporal_coherence_score =
  2*trsi*decay/(trsi+decay)    if trsi>0 and decay>0
  0.5                           otherwise
```

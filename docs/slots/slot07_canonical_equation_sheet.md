# Slot 07 Canonical Equation Sheet

Source anchors:
- `src/nova/slots/slot07_production_controls/production_control_engine.py`
- `src/nova/slots/slot07_production_controls/reflex_emitter.py`
- `src/nova/slots/slot07_production_controls/core/reflex.py`
- `src/nova/slots/slot07_production_controls/core/rules.yaml`
- `src/nova/slots/slot07_production_controls/context_publisher.py`
- `src/nova/slots/slot07_production_controls/wisdom_backpressure.py`
- `src/nova/slots/slot07_production_controls/cognitive_loop.py`
- `src/nova/slots/slot07_production_controls/temporal_resonance.py`
- `src/nova/slots/slot07_production_controls/health.py`
- `src/nova/slots/slot07_production_controls/metrics.py`
- `src/nova/orchestrator/thresholds/manager.py`

## 1. Core Control Equations

### 1.1 Circuit breaker state machine

```text
initial state = closed

on protected exception:
  failure_count += 1
  if failure_count >= failure_threshold:
    state = open
    opened_at = now

while state == open:
  if now - opened_at >= reset_timeout:
    state = half-open

on success when state == half-open:
  state = closed
  failure_count = 0
```

Note: `error_threshold` and `recovery_time` are configured but not used in transition math.

### 1.2 Rate limiter (token bucket)

```text
tokens(t) = min(burst_size, tokens(t-1) + dt * (requests_per_minute / 60))

allow iff tokens >= 1
if allow: tokens -= 1
```

### 1.3 Resource gates

Payload estimate:

```text
size_mb = len(str(payload).encode("utf-8")) / (1024 * 1024)
reject if size_mb > max_payload_size_mb
```

Concurrency:

```text
reject if active_requests >= effective_max_concurrent_requests
```

where `effective_max_concurrent_requests` is static config or wisdom-adaptive cap.

## 2. Engine Metrics and Phase Lock

### 2.1 Request metrics

```text
success_rate = successful_requests / max(1, total_requests)
avg_processing_time_ms = mean(processing_times) * 1000
min_processing_time_ms = min(processing_times) * 1000
max_processing_time_ms = max(processing_times) * 1000
```

### 2.2 Health degradation criteria

```text
degraded if circuit_breaker.state == open
degraded if success_rate < 0.9 and total_requests > 10
```

### 2.3 Phase-lock equation

If `NOVA_LIGHTCLOCK_DEEP=0`:

```text
phase_lock = 1.0
```

Else:

```text
success_rate = successful_requests / max(1, total_requests)    (default 1.0 when no requests)
pressure_level = min(1, failure_count / max(1, failure_threshold))
phase_lock = clamp(0.7*success_rate + 0.3*(1 - pressure_level), 0, 1)
```

Belief update:

```text
new_belief = BeliefState.from_point_estimate(phase_lock, 0.05)
phase_lock_belief <- update_belief(previous_belief, new_belief)
```

## 3. Safeguard Violation -> Reflex Mapping

### 3.1 Circuit breaker violation

```text
failure_ratio = failure_count / max(1, failure_threshold)
state_bias = 1.0 (open), 0.8 (half-open), 0.0 (closed)
raw_pressure = min(1, max(failure_ratio, state_bias))
```

### 3.2 Resource violation (`memory_pressure`)

In emitter:

```text
request_pressure = active_requests / max(1, max_requests)
violation_pressure = min(1, resource_violations / 10)
raw_pressure = min(1, max(request_pressure, violation_pressure))
```

### 3.3 Rate-limit violation

```text
deficit = 1 - min(1, current_tokens / max(1, burst_size))
raw_pressure = clamp(deficit, 0, 1)
```

## 4. Reflex Backpressure Functions

### 4.1 Simple backpressure (`core/reflex.py`)

Defaults:
- `REFLEX_THRESHOLD = 0.70`
- `REFLEX_SLOPE = 1.50`

```text
if pressure <= threshold:
  base_level = 0
else:
  base_level = min(1, ((pressure - threshold) / (1 - threshold)) * slope)

error_boost = min(0.3, 0.5 * error_rate)
backpressure = min(1, base_level + error_boost)
```

### 4.2 Structured reflex emitter (`reflex_emitter.py`)

Smoothing:

```text
smoothed_pressure = alpha*raw_pressure + (1-alpha)*previous_smoothed
```

Hysteresis (raw pressure):

```text
if inactive and raw >= rise_threshold: activate and emit
if active and raw <= fall_threshold: deactivate and stop
if active and raw > fall_threshold: continue emit
```

Cooldown:

```text
if now - last_emission < cooldown_seconds:
  block
```

Global rate limit:

```text
window_size = 60
max_emissions_in_window = max_emission_rate * window_size
allow iff emissions_in_window < max_emissions_in_window
```

Clamp:

```text
clamped_pressure = clamp(smoothed_pressure, 0, 1)
```

`emissions_in_window` increments only when non-shadow emission is enabled and bus send succeeds.

## 5. Context Publisher Equations

### 5.1 Pressure level (`context_publisher.py`)

Breaker factor:

```text
if state == open: breaker_pressure = 1.0
elif state == half-open: breaker_pressure = 0.7
else:
  failure_rate = 1 - success_rate
  breaker_pressure = min(1, 2*failure_rate)
```

Resource factor:

```text
resource_pressure = min(1, active_requests / max(1, max_concurrent_requests))
```

Rate violations factor (only when violations > 0):

```text
rate_pressure = min(1, rate_limit_violations / 10)
```

Combination:

```text
avg_pressure = mean(factors)
max_pressure = max(factors)
pressure_level = min(1, 0.7*max_pressure + 0.3*avg_pressure)
```

Trend classifier:

```text
if pressure > 0.8: rising
elif pressure < 0.3: falling
else: stable
```

## 6. Wisdom Backpressure Job-Cap Equations

Defaults:
- `baseline=16`
- `frozen=2`
- `reduced=6`
- `slot07_stability_threshold=0.03`
- `slot07_stability_threshold_tri=0.05`
- `slot07_tri_drift_threshold=2.2`
- `tri_min_coherence=0.65`

Safety normalization:

```text
frozen = max(1, min(frozen, baseline//2))
reduced = max(frozen+1, min(reduced, baseline-1))
```

Decision:

```text
if governor_frozen or tri_band=="red" or (S is not None and S < 0.05):
  cap = frozen
  reason = 2
else:
  reduce = (
    (tri_drift_z is not None and tri_drift_z >= 2.2) or
    (tri_band == "amber") or
    (tri_coherence is not None and tri_coherence < 0.65) or
    (S is not None and S < 0.03)
  )
  if reduce:
    cap = reduced
    reason = 1
  else:
    cap = baseline
    reason = 0
```

Prometheus:

```text
nova_slot07_jobs_current = cap
nova_slot07_jobs_reason = reason
```

## 7. Cognitive Loop Controller Logic Math

Gating:

```text
enabled = (NOVA_ENABLE_COGNITIVE_LOOP == "1")
max_iterations = int(NOVA_COGNITIVE_LOOP_MAX_ITERATIONS, default=5)
collapse_threshold config default = 0.3
```

Termination:

```text
if graph_state == "void":
  converged = True
  return immediately

if oracle_decision == "ACCEPT":
  converged = True
  return

after max_iterations:
  converged = False
  return last attempt
```

Feedback thresholds:

```text
b_local > 0.7
b_global < 0.4
b_risk < 0.3
b_completion > 0.6
b_structural > 0.7
b_semantic > 0.6
b_refusal > 0.5
collapse_score > 0.5 (critical) / > 0.3 (moderate)
```

Aggregate metric:

```text
avg_iterations_per_loop = total_iterations_executed / total_loops_run    (0 if no loops)
```

## 8. Temporal Resonance Equations

TRSI:

```text
weight_i = decay_weight_i * resonance_coefficient_i
raw_trsi = mean(weight_i)

if raw_trsi > coupling_threshold:
  trsi = min(1, raw_trsi * resonance_amplification)
else:
  trsi = raw_trsi
```

Coupling:

```text
coupling_strength = mean(resonance_coefficient_i)
```

Coherence (harmonic mean):

```text
coherence_score = 2*trsi*coupling_strength / (trsi + coupling_strength)   if trsi>0 and coupling_strength>0 else 0
```

Window summaries:

```text
average_trsi = mean(window_trsi)
trsi_volatility = stdev(window_trsi) (or 0 when one sample)
temporal_coherence = mean(window_coherence)
resonance_strength = mean(window_coupling)
```

24h trend:

```text
trsi_trend_24h = newest_trsi(last_24h) - oldest_trsi(last_24h)
```

## 9. Health and Metrics Helpers

Health pressure (`health.py`):

```text
if circuit_state == open: pressure = 1.0
elif circuit_state == half-open: pressure = 0.7
else:
  failure_pressure = max(0, (0.9 - success_rate)/0.9)
  response_pressure = min(1, avg_response_time_ms/1000)
  pressure = min(1, max(failure_pressure, 0.5*response_pressure))

pressure = round(pressure, 3)
```

Metrics (`metrics.py`):

```text
breaker_state_numeric = {closed:0, open:1, half-open:2}
slot7_reflex_rate_recent_per_minute = emissions_last_5_minutes / 5
```

# Slot 07 Logic and Math Extraction

This document extracts Slot 07 behavior from implementation code in:
- `src/nova/slots/slot07_production_controls/production_control_engine.py`
- `src/nova/orchestrator/adapters/slot7_production_controls.py`
- `src/nova/slots/slot07_production_controls/reflex_emitter.py`
- `src/nova/slots/slot07_production_controls/core/reflex.py`
- `src/nova/slots/slot07_production_controls/core/rules.yaml`
- `src/nova/slots/slot07_production_controls/context_publisher.py`
- `src/nova/slots/slot07_production_controls/wisdom_backpressure.py`
- `src/nova/slots/slot07_production_controls/cognitive_loop.py`
- `src/nova/slots/slot07_production_controls/health.py`
- `src/nova/slots/slot07_production_controls/metrics.py`
- `src/nova/slots/slot07_production_controls/flag_metrics.py`
- `src/nova/slots/slot07_production_controls/temporal_resonance.py`
- `src/nova/orchestrator/thresholds/manager.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `2201b90`: Slot 7 folder structure introduction
- `85a47ce`: circuit breaker with metrics/timeout handling
- Slot7 skeleton/flow maturation entries (Production Controls path)
- `c2b3153`: Slot07 VOID freeze policy

## 1. Runtime Logic

### 1.1 Main processing path (`ProductionControlEngine.process`)
Per request:
1. Pre-checks:
   - rate limiter
   - payload size
   - concurrency gate
2. Protected execution:
   - circuit breaker guard
   - processing-time guard
3. Core processing (`_core_processing`)
4. Metrics update
5. Return:
   - `processed` on success
   - `degraded` on safeguard violation (if graceful degradation enabled)
   - exception when graceful degradation disabled
6. Always releases one active request slot in `finally`.

### 1.2 Adapter behavior
`Slot7ProductionControlsAdapter.process(payload)`:
- if engine unavailable -> `{"status":"unavailable"}`
- else delegates to engine
- exceptions return `{"status":"error"}`.

### 1.3 Safeguard components
Slot07 composes:
- `ProductionControlsCircuitBreaker`
- `RateLimiter` (token bucket)
- `ResourceProtector` (payload/concurrency/time monitor)
- optional reflex signaling on safeguard violations.

### 1.4 Feature-gated integrations
- `NOVA_WISDOM_BACKPRESSURE_ENABLED=1`:
  - ResourceProtector concurrency cap becomes wisdom-adaptive (`wisdom_backpressure.compute_max_concurrent_jobs`).
- `NOVA_LIGHTCLOCK_DEEP=0`:
  - `compute_phase_lock()` returns `1.0` (deep phase-lock path disabled).
- `NOVA_PUBLISH_PHASE_LOCK=1` and probabilistic contracts enabled:
  - publish `slot07.phase_lock_belief` to mirror.
- Reflex policy flags:
  - `NOVA_REFLEX_ENABLED`
  - `NOVA_REFLEX_SHADOW`.

### 1.5 Context publication contract (`context_publisher.py`)
When publish succeeds, Slot07 writes semantic mirror keys:
- `slot07.breaker_state`
- `slot07.pressure_level`
- `slot07.resource_status`
- `slot07.health_summary`
- optional `slot07.phase_lock` when `NOVA_LIGHTCLOCK_DEEP=1`.

TTL windows:
- 30s (`breaker_state`, `pressure_level`)
- 60s (`resource_status`)
- 120s (`health_summary`)
- 300s (`phase_lock`).

## 2. Core Math (`production_control_engine.py`)

### 2.1 Circuit breaker transition logic
State machine:
- initial: `closed`
- on each protected exception:
  - `failure_count += 1`
  - if `failure_count >= failure_threshold` -> `open`
- while `open`:
  - if `now - opened_at >= reset_timeout` -> `half-open`
- success in `half-open`:
  - state -> `closed`
  - `failure_count = 0`

Implementation note:
- `error_threshold` and `recovery_time` are in config but not used in current transition equations.

### 2.2 Rate limiter (token bucket)
Parameters:
- `requests_per_minute`
- `burst_size`

Update on each check:

```text
tokens += dt * (requests_per_minute / 60)
tokens = min(burst_size, tokens)
```

Decision:

```text
if tokens >= 1: tokens -= 1; allow
else: deny
```

### 2.3 Payload-size check
Approximate size:

```text
size_mb = len(str(payload).encode("utf-8")) / (1024*1024)
```

Reject if:

```text
size_mb > max_payload_size_mb
```

### 2.4 Concurrency gate
Reject when:

```text
active_requests >= effective_max_concurrent_requests
```

`effective_max_concurrent_requests` equals:
- baseline configured max, or
- wisdom-adaptive cap if wisdom backpressure is enabled.

### 2.5 Success-rate and latency metrics

```text
success_rate = successful_requests / max(1, total_requests)
avg_processing_time_ms = mean(processing_times)*1000
min_processing_time_ms = min(processing_times)*1000
max_processing_time_ms = max(processing_times)*1000
```

### 2.6 Engine health classification
`health_check()` sets degraded if:
- breaker is `open`, or
- `success_rate < 0.9` with `total_requests > 10`.

### 2.7 Phase-lock equation
When deep mode enabled:

```text
success_rate = successful_requests / max(1, total_requests)   (default 1.0 if no requests)
pressure_level = min(1, failure_count / max(1, failure_threshold))
phase_lock = clamp(0.7*success_rate + 0.3*(1 - pressure_level), 0, 1)
```

When `NOVA_LIGHTCLOCK_DEEP=0`:
- `phase_lock = 1.0`

Belief update:
- new observation belief: `BeliefState.from_point_estimate(phase_lock, 0.05)`
- posterior: `update_belief(previous_phase_lock_belief, new_observation_belief)`.

### 2.8 Reflex pressure values derived from violations
From `_emit_reflex_signal`:

1. Circuit breaker violation:

```text
failure_ratio = failure_count / max(1, failure_threshold)
state_bias = 1.0 if open else 0.8 if half-open else 0.0
raw_pressure = min(1, max(failure_ratio, state_bias))
```

2. Resource violation:
- delegated as memory-pressure signal using active requests, max requests, resource violation count.

3. Rate-limit violation:

```text
deficit = 1 - min(1, current_tokens / max(1, burst_size))
raw_pressure = clamp(deficit, 0, 1)
```

## 3. Reflex/Backpressure Math

### 3.1 Simple reflex mapping (`core/reflex.py`)
Config:
- `REFLEX_THRESHOLD` default `0.70`
- `REFLEX_SLOPE` default `1.50`

Base mapping:

```text
if pressure <= threshold: base_level = 0
else:
  excess = pressure - threshold
  max_excess = 1 - threshold
  base_level = min(1, (excess / max_excess) * slope)
```

Error boost:

```text
error_boost = min(0.3, 0.5 * error_rate)
backpressure = min(1, base_level + error_boost)
```

### 3.2 Structured reflex emitter (`reflex_emitter.py`)

Signal smoothing:

```text
smoothed = alpha*raw + (1-alpha)*previous_smoothed
```

Hysteresis (uses raw pressure):
- activate when `raw >= rise_threshold`
- deactivate when active and `raw <= fall_threshold`
- remain active otherwise.

Cooldown:

```text
if now - last_emission < cooldown_seconds: block
```

Global rate-limit window:

```text
window_size = 60s
max_emissions_in_window = max_emission_rate * 60
allow iff emissions_in_window < max_emissions_in_window
```

Clamp stage:
- pressure clamped to `[0,1]`
- frequency/weight multiplier bounds read from policy.

Emission behavior:
- if shadow mode or no bus: treated as successful computation path
- actual bus emission only when non-shadow, enabled, and bus available.
- `emissions_in_window` increases only on successful real-bus emission.

### 3.3 Reflex policy defaults (`core/rules.yaml`)
Global defaults:
- `max_emission_rate=1.0` signals/sec
- `smoothing_alpha=0.2`
- `debounce_window_seconds=5.0`.

Per-signal defaults:
- `breaker_pressure`: rise `0.8`, fall `0.6`, cooldown `10s`
- `memory_pressure`: rise `0.85`, fall `0.7`, cooldown `15s`
- `integrity_violation`: rise `0.8`, fall `0.5`, cooldown `30s`.

## 4. Context Publisher Math (`context_publisher.py`)

### 4.1 Pressure-level formula
Factors:
1. Breaker contribution:
   - `1.0` if open
   - `0.7` if half-open
   - else `min(1, 2*(1-success_rate))`
2. Resource pressure:

```text
min(1, active_requests / max(1, max_concurrent_requests))
```

3. Rate-violation pressure (if violations > 0):

```text
min(1, rate_limit_violations / 10)
```

Combine:

```text
avg_pressure = mean(factors)
max_pressure = max(factors)
pressure_level = min(1, 0.7*max_pressure + 0.3*avg_pressure)
```

### 4.2 Pressure trend classification

```text
if pressure > 0.8: trend = "rising"
elif pressure < 0.3: trend = "falling"
else: trend = "stable"
```

## 5. Wisdom-Aware Job Policy Math (`wisdom_backpressure.py`)

### 5.1 Configuration
Defaults:
- baseline jobs: `16`
- frozen jobs: `2`
- reduced jobs: `6`
- stability threshold: `slot07_stability_threshold` (default `0.03`)

Safety normalization:

```text
frozen = max(1, min(frozen, baseline//2))
reduced = max(frozen+1, min(reduced, baseline-1))
```

### 5.2 Decision logic
Threshold defaults from threshold manager:
- `slot07_stability_threshold = 0.03`
- `slot07_stability_threshold_tri = 0.05`
- `slot07_tri_drift_threshold = 2.2`
- `tri_min_coherence = 0.65`

Let observed stability `S`.

Freeze condition:

```text
if governor_frozen or tri_band == "red" or (S is not None and S < 0.05):
  cap = frozen_jobs
  reason = 2
```

Else reduced condition if any true:
- `tri_drift_z >= 2.2`
- `tri_band == "amber"`
- `tri_coherence < 0.65`
- `S < 0.03`

Then:

```text
cap = reduced_jobs
reason = 1
```

Else:

```text
cap = baseline_jobs
reason = 0
```

Prometheus gauges:
- `nova_slot07_jobs_current = cap`
- `nova_slot07_jobs_reason = reason`.

## 6. Slot07 Health/Export Math

### 6.1 Health-module pressure calculation (`slot07_production_controls/health.py`)
If breaker:
- open -> `1.0`
- half-open -> `0.7`

Else:

```text
failure_pressure = max(0, (0.9 - success_rate)/0.9)
response_pressure = min(1, avg_response_time_ms / 1000)
total_pressure = min(1, max(failure_pressure, 0.5*response_pressure))
```

### 6.2 Metrics-module derivations (`metrics.py`)
- breaker state numeric mapping:
  - closed `0`, open `1`, half-open `2`
- reflex recent rate:

```text
reflex_rate_recent_per_minute = emissions_in_last_5_min / 5
```

### 6.3 Feature-flag metrics (`flag_metrics.py`)
Slot07 exports operational booleans:
- TRI-link enabled
- lifespan enabled
- shared hash enabled/available
- effective hash method (`shared_blake2b` or `fallback_sha256`)
- Slot6 p95 residual risk passthrough for ops visibility.

## 7. Cognitive Loop Logic/Math (`cognitive_loop.py`)

### 7.1 Loop gating
- Enabled by `NOVA_ENABLE_COGNITIVE_LOOP=1`
- default max iterations `5`.

Disabled mode:
- one pass (generator + analyzer), no oracle loop, converged=true.

Enabled mode:
- iterative generator -> analyzer -> oracle -> attestor.

### 7.2 VOID freeze policy
If analyzer returns `graph_state == "void"`:
- skip oracle/refinement
- increment `slot07_regime_unchanged_on_void_total`
- immediate converged return.

### 7.3 Refinement suggestions thresholds
Suggestions triggered by bias vector thresholds:
- `b_local > 0.7`
- `b_global < 0.4`
- `b_risk < 0.3`
- `b_completion > 0.6`
- `b_structural > 0.7`
- `b_semantic > 0.6`
- `b_refusal > 0.5`
- plus collapse-score messages:
  - `C > 0.5` critical
  - `C > 0.3` moderate.

### 7.4 Controller-level aggregate metrics
From `get_metrics()`:

```text
avg_iterations_per_loop = total_iterations_executed / total_loops_run   (0 if loops=0)
```

## 8. Temporal Resonance Math (`temporal_resonance.py`)

Though physically in Slot07 package, this is a Phase-7 temporal engine module.

TRSI from entries:

```text
weight_i = decay_weight_i * resonance_coefficient_i
raw_trsi = mean(weight_i)
if raw_trsi > coupling_threshold (default 0.8):
  trsi = min(1, raw_trsi * resonance_amplification)   # default amplification 1.5
else:
  trsi = raw_trsi
```

Coupling strength:

```text
coupling_strength = mean(resonance_coefficient_i)
```

Coherence:

```text
coherence = 2*trsi*coupling_strength / (trsi + coupling_strength)   if both > 0 else 0
```

### 8.1 Windowed pattern summary
For sliding windows:

```text
average_trsi = mean(window_trsi_values)
trsi_volatility = stdev(window_trsi_values)   (0 when only 1 sample)
temporal_coherence = mean(window_coherence_values)
resonance_strength = mean(window_coupling_values)
```

### 8.2 24h TRSI trend

```text
trsi_trend_24h = newest_trsi_in_last_24h - oldest_trsi_in_last_24h
```

## 9. What Slot07 Math Is in Practice

Slot07 combines:
- finite-state fault control (circuit breaker),
- token-bucket throughput control,
- bounded resource gating,
- pressure/reflex mapping with smoothing+hysteresis+cooldowns,
- adaptive wisdom policy caps,
- optional phase-lock probabilistic belief updates,
- and loop orchestration with VOID short-circuit semantics.

It is a deterministic control layer with bounded heuristics; no learned optimization model is required for core behavior.

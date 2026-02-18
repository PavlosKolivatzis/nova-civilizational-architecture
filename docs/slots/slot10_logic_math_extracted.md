# Slot 10 Logic and Math Extraction

This document extracts Slot 10 behavior from implementation code in:
- `src/nova/slots/slot10_civilizational_deployment/deployer.py`
- `src/nova/slots/slot10_civilizational_deployment/mls.py`
- `src/nova/slots/slot10_civilizational_deployment/phase_space.py`
- `src/nova/slots/slot10_civilizational_deployment/models.py`
- `src/nova/slots/slot10_civilizational_deployment/core/policy.py`
- `src/nova/slots/slot10_civilizational_deployment/core/gatekeeper.py`
- `src/nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py`
- `src/nova/slots/slot10_civilizational_deployment/core/canary.py`
- `src/nova/slots/slot10_civilizational_deployment/core/lightclock_canary.py`
- `src/nova/slots/slot10_civilizational_deployment/core/snapshot_backout.py`
- `src/nova/slots/slot10_civilizational_deployment/core/audit.py`
- `src/nova/slots/slot10_civilizational_deployment/core/feedback.py`
- `src/nova/slots/slot10_civilizational_deployment/core/metrics.py`
- `src/nova/slots/slot10_civilizational_deployment/core/factory.py`
- `src/nova/orchestrator/adapters/slot10_civilizational.py`
- `src/nova/slots/slot10_civilizational_deployment/tests/test_*.py`
- `tests/test_slot10_*.py`
- `tests/slot10/test_slot10_*.py`
- `tests/slot10_civilizational_deployment/test_*.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `c7124c8`: Slot 10 folder structure.
- `e48ef03`: Slot 10 Civilizational Deployment Processual (4.0) implementation.
- `02f8478`: Light-Clock deployment-gate phase-lock system context.

## 1. Runtime Topology

### 1.1 Core deployment pipeline (`InstitutionalNodeDeployer.deploy`)
Execution order:
1. Build `ctx={"region": region}` and get cultural profile from Slot 6.
2. Run `MetaLegitimacySeal.assess(...)`.
3. If decision is `QUARANTINE`: block at `STEALTH_INTEGRATION`.
4. If payload has `capacity_block`: block at `CONSENSUS`.
5. If payload has `secure is False`: block at `SECURITY`.
6. Optionally calibrate Slot 4 TRI with timeout 5s (errors are swallowed).
7. Register node in phase space with `ThreatLevel.LOW`.
8. Return approved `REGISTER` result.

State counters:
- `metrics.deployments += 1` on success.
- `metrics.blocked += 1` on guardrail/capacity blocks.
- `metrics.security_failures += 1` on security block.

### 1.2 Geometric-memory profile cache (`_profile`)
- Cache key: `f"{institution_name}:{region}"`.
- If geomemory enabled:
  - read cached profile first,
  - otherwise compute via Slot 6 and write with `ttl_s=300`.

### 1.3 MetaLegitimacySeal decision mapping (`mls.assess`)
- `APPROVED -> ALLOW`
- `REQUIRES_TRANSFORMATION -> ALLOW_TRANSFORMED`
- all other guardrail outcomes -> `QUARANTINE`.

### 1.4 Optional Slot 2 screening helper (`mls._screen_with_slot2`)
The helper is implemented but not called in current deploy path.
When used, it adapts Slot 2 output and computes fallback threat:

```text
risk = max(layer_scores.values()) if layer_scores else 0
tri_gap = max(0, tri_min_score - tri_score)
threat_level = existing_threat_level or min(1, 0.5*risk + 0.5*tri_gap)
```

On any exception it returns:
- `threat_level=0.0`
- `patterns_detected=[]`.

## 2. Slot10Policy Numeric Configuration

### 2.1 Core defaults (`core/policy.py`)
- `mttr_target_s = 5.0`
- `canary_stage_timeout_s = 180`
- `rollback_timeout_s = 10.0`
- `canary_stages = [0.01, 0.05, 0.25, 0.50, 1.00]`
- `min_stage_duration_s = 300`
- `min_promotion_gap_s = 0.0`
- `max_stage_rollback_velocity_per_hour = 6`
- `frozen_baseline_window_s = 300`

Gate thresholds:
- `slot08_integrity_threshold = 0.7`
- `slot08_recovery_rate_threshold = 0.8`
- `slot04_drift_z_threshold = 3.0`

URF thresholds:
- `urf_composite_risk_threshold = 0.85`
- `urf_alignment_threshold = 0.6`
- `urf_risk_gap_threshold = 0.5`

MSE threshold:
- `mse_deployment_threshold = 0.12`

Canary SLO multipliers:
- `error_rate_multiplier = 1.15`
- `latency_p95_multiplier = 1.10`
- `saturation_threshold = 0.80`

Other operational constants:
- `snapshot_consistency_timeout_s = 30.0`
- `max_concurrent_rollbacks = 1`
- `acceptable_chaos_recovery_rate = 0.8`
- `metrics_collection_interval_s = 30`
- `alert_cooldown_s = 300`.

Derived properties:

```text
stage_count = len(canary_stages)
total_canary_duration_s = stage_count * canary_stage_timeout_s
```

## 3. Deployment Gate Logic (Gatekeeper)

### 3.1 Base gate conditions (`core/gatekeeper.py`)
Deployment fails if any condition fails:

Slot 8:
- `quarantine_active == True` -> fail `slot08_quarantine`.
- `integrity_score < slot08_integrity_threshold` -> fail `slot08_integrity`.
- `recent_recoveries.success_rate_5m < slot08_recovery_rate_threshold` -> fail `slot08_recovery_rate`.
- `checksum_mismatch == True` -> fail `slot08_checksum_mismatch`.
- `tamper_evidence == True` -> fail `slot08_tamper_evidence`.

Slot 4:
- `safe_mode_active == True` -> fail `slot04_safe_mode`.
- `drift_z >= slot04_drift_z_threshold` -> fail `slot04_drift`.

Overall:

```text
passed = (len(failed_conditions) == 0)
```

### 3.2 URF gates (flag: `NOVA_ENABLE_URF=1`)
Using `get_unified_risk_field()`:
- if `composite_risk >= urf_composite_risk_threshold` -> `urf_composite_risk_high`
- if `alignment_score < urf_alignment_threshold` -> `urf_alignment_low`
- if `risk_gap > urf_risk_gap_threshold` -> `urf_risk_gap_high`.

If MSE is also enabled, `record_composite_risk_sample(composite_risk)` is called.

### 3.3 MSE gate (flag: `NOVA_ENABLE_MSE=1`)
Using `get_meta_stability_snapshot()` and `should_block_deployment(meta_instability, threshold)`:
- if blocking predicate is true -> fail `mse_meta_instability_high`.

### 3.4 ORP posture (flag: `NOVA_ENABLE_ORP=1`)
Using `get_operational_regime()`:
- if `posture_adjustments.deployment_freeze == True` -> fail `orp_deployment_freeze`.
- regime in `{"emergency_stabilization", "recovery"}` logs rollback warning.
- `record_orp(snapshot)` called for telemetry.

ORP errors are swallowed; gate evaluation continues without ORP constraints.

## 4. Light-Clock Gate Logic

### 4.1 Inputs and thresholds (`core/lightclock_gatekeeper.py`)
Env defaults:
- `NOVA_TRI_GATE = 0.66`
- `NOVA_PHASE_LOCK_GATE = 0.70`
- `NOVA_PHASE_LOCK_MIN = 0.45`
- `NOVA_PHASE_LOCK_MAX = 0.60`
- `NOVA_SLOT9_ALLOWED = {ALLOW_FASTPATH, STANDARD_PROCESSING}`.

Registry/fallback thresholds:
- `tri_min_coherence = 0.65`
- `slot07_tri_drift_threshold = 2.2`
- `tri_max_jitter = 0.30`
- `slot07_stability_threshold_tri = 0.05`.

Base coherence gate:

```text
tri_gate = max(env_tri_gate, tri_min_coherence)
```

Phase window:
- `should_open_gate()` path (`use_window=True`):
  - `phase_min = max(env_phase_min, stability_threshold_tri)`
  - `phase_max = max(env_phase_max, phase_min + 0.1)`
- `evaluate_deploy_gate()` path (`use_window=False`):
  - `phase_min = max(env_phase_lock_gate, stability_threshold_tri)`
  - `phase_max = NOVA_PHASE_LOCK_CEILING (default 1.0)`.

### 4.2 Dynamic coherence tightening

```text
tri_gate_dynamic = tri_gate
if tri_jitter is not None and tri_jitter >= tri_max_jitter:
  tri_gate_dynamic += 0.05
if pressure_level:
  tri_gate_dynamic += 0.05 * clamp(pressure_level, 0, 1)
```

### 4.3 Light-Clock fail predicates
Fail if any:
- `tri_coherence is None or tri_coherence < tri_gate_dynamic`
- `tri_drift_z is not None and tri_drift_z > drift_threshold`
- `phase_lock is None or phase_lock not in [phase_min, phase_max]`
- `slot9_policy is not None and slot9_policy not in allowed_policy_set`.

Coherence label:
- `high` if `phase_lock >= phase_min + 0.1`
- `low` if `phase_lock < phase_min`
- `medium` otherwise (when phase_lock exists)
- `unknown` when missing.

## 5. Canary Progression Logic

### 5.1 Start semantics (`CanaryController.start_deployment`)
- stores baseline and frozen baseline copy,
- resets stage index to 0 and rollback flag false,
- starts stage 0 clock.

### 5.2 Stage evaluation order (`CanaryController.evaluate_stage`)
1. If rollback already triggered -> return rollback state.
2. Evaluate deployment gate; gate failure triggers rollback.
3. Validate stage index range; invalid index triggers rollback.
4. Promotion velocity guard:
   - active only when `min_promotion_gap_s > 0` and prior promotion exists.
   - if `time_since_last_promotion < min_promotion_gap_s` -> `continue`.
5. Minimum stage dwell:
   - if `stage_duration < min_stage_duration_s` -> `continue`.
6. SLO checks vs frozen baseline:
   - any violation triggers rollback.
7. Stage timeout:
   - if `stage_duration > canary_stage_timeout_s` -> rollback.
8. Otherwise promote stage.

### 5.3 SLO violation formulas (`_check_slo_violations`)

```text
error_violation if current_error_rate > baseline_error_rate * error_rate_multiplier
latency_violation if current_latency_p95 > baseline_latency_p95 * latency_p95_multiplier
saturation_violation if current_saturation > saturation_threshold
```

Comparators are strict `>` in all three checks.

### 5.4 Promotion and completion
- Current stage `end_time` set at promotion.
- Last stage promotion returns `action="promote"` with:

```text
total_duration = sum(stage.duration for all stages)
```

- Non-final promotion increments index and sets next stage `start_time`.

### 5.5 Rollback trigger
`_trigger_rollback(reason)`:
- sets `rollback_triggered=True`,
- closes current stage timing (`end_time=now`),
- returns `action="rollback"` with stage duration and violation count.

## 6. Light-Clock Canary Adjustments

### 6.1 Coherence-based timing/SLO tuning (`lightclock_canary.py`)
Threshold constants:
- `high_coherence_acceleration = 0.85`
- `low_coherence_deceleration = 0.4`
- `minimal_coherence_block = 0.3`.

If Light-Clock enabled and phase lock exists:

High coherence (`phase_lock > 0.85`):
- `adjusted_min_promotion_gap = max(0, base_gap * 0.7)`
- `adjusted_min_stage_duration = max(30, base_min_duration * 0.8)`
- `error_rate_multiplier = base_error_mult * 1.1` (more permissive)

Low coherence (`phase_lock < 0.4`):
- `adjusted_min_promotion_gap = base_gap * 1.5`
- `adjusted_min_stage_duration = base_min_duration * 1.2`
- `error_rate_multiplier = base_error_mult * 0.9` (stricter)
- `latency_p95_multiplier = base_latency_mult * 0.95` (stricter)

Minimal coherence branch (`phase_lock < 0.3`) exists in code with stronger penalties:
- gap `*2.0`, duration `*1.5`, error `*0.8`, latency `*0.9`.

As implemented, this branch is shadowed by the prior `phase_lock < 0.4` branch and is not reachable.

### 6.2 Coherence-adjusted SLO checks
Same inequalities as base canary, but with adjusted multipliers when present:

```text
current_error_rate > baseline_error_rate * adjusted_error_multiplier
current_latency_p95 > baseline_latency_p95 * adjusted_latency_multiplier
current_saturation > saturation_threshold
```

## 7. Snapshot Backout and MTTR

### 7.1 Snapshot record
`record_promotion(...)` stores:
- snapshot ids (`slot10_id`, `slot08_id`, `slot04_id`)
- `ts_ms = int(time.time() * 1000)`
- reason.

### 7.2 Rollback execution (`SnapshotBackout.rollback`)
- If no snapshot exists, returns failure with `"No snapshot set recorded"`.
- Executes restore callbacks sequentially for slot10, slot08, slot04.
- Success criterion:

```text
success = slot10_success and slot08_success and slot04_success
```

- Execution timer:

```text
execution_time_s = now - start
```

- MTTR violation:
  - if `execution_time_s > rollback_timeout_s`, add `"mttr"` error message.
  - does not force overall failure if all restores succeeded.

## 8. Audit Hash-Chain and Signature Logic

### 8.1 Audit hash method selection (`core/audit.py`)
Env truthiness:

```text
_env_truthy(name) == True only when os.getenv(name).strip() == "1"
```

When recording an event:
- if shared hash is available and `NOVA_USE_SHARED_HASH=1`:
  - `hash_method = "shared_blake2b"`
  - `hash = compute_audit_hash(body)`
- else:
  - `hash_method = "fallback_sha256"`
  - `hash = sha256(canonical_json(body)).hexdigest()`

Chain link:
- `prev = last_hash`
- set both `prev` and `previous_hash` fields in payload
- update `last_hash = hash`.

### 8.2 Signature formula
Default signer:

```text
sig = "hmac256:" + HMAC_SHA256(secret, canonical_json(body)).hexdigest()
```

Default secret is `b"default-nova-secret"` unless overridden.

### 8.3 Canary payload fields in audit body
If provided, canary rollout values are included:
- `canary.pct_from`
- `canary.pct_to`

Extra kwargs are preserved under `extra`.

## 9. Feedback Loop Math (Slot10 -> upstream)

### 9.1 Feedback normalization and publishing
`publish_deployment_feedback(...)` clamps:

```text
transform_rate = clamp(transform_rate, 0, 1)
error_rate = clamp(error_rate, 0, 1)
```

Then publishes `slot10.deployment_feedback` with `ttl=300s`.

### 9.2 Cultural adjustment (`compute_cultural_adjustment`)
Defaults:
- `residual_risk_delta = 0`
- `adaptation_effectiveness_delta = 0`
- action `maintain`.

Rules:
- if `transform_rate > 0.4`:
  - `residual_risk_delta = 0.15 * transform_rate`
  - action `stricter_validation`.
- if `rollback=True`:
  - `residual_risk_delta += 0.25`
  - `adaptation_effectiveness_delta = -0.20`
  - action `stabilize_memory`.
- else if `transform_rate < 0.1`:
  - `adaptation_effectiveness_delta = +0.10`
  - action `increase_adaptation`.

### 9.3 TRI feedback signal (`apply_tri_feedback_signal`)

```text
strict_mode = rollback OR (error_rate > 0.1)
validation_boost = min(0.3, error_rate * 2.0)
```

Published to `slot4.tri_feedback` with `ttl=180s`.

Hook thresholds:
- `on_canary_complete`: emit TRI signal when `not success` or `error_rate > 0.05`.
- `on_rollback_triggered`: forces rollback signal with `error_rate=1.0`.
- `on_deployment_success`: emits reset signal when `transform_rate < 0.1`.

## 10. Metrics Exporter Logic

### 10.1 Export cadence

```text
should_export = (now - last_export_ts) >= export_interval_s
```

### 10.2 Duration calculations

```text
stage_duration_s = current_stage.duration
total_duration_s = now - deployment_start_ts
```

### 10.3 Exported numeric mappings
- `deploy_active = 1 if deployment_active else 0`
- `gate_status = 1 if gate pass else 0`
- `rollback_triggered = 1 if rollback else 0`
- `saturation_pct = saturation * 100`
- `gate_failed_conditions_count = len(failed_conditions)`.

History keeps last 100 metric snapshots.

## 11. Factory and Adapter Contracts

### 11.1 Controller factory (`core/factory.py`)
- if `NOVA_LIGHTCLOCK_GATING=1` -> build `LightClockCanaryController`.
- else -> build base `CanaryController`.

### 11.2 Adapter contract (`orchestrator/adapters/slot10_civilizational.py`)
`Slot10DeploymentAdapter.deploy(...)` returns:
- deployment result dict on success,
- `{"approved": False, "reason": "unavailable"}` when engine missing,
- `{"approved": False, "reason": "error"}` on exception.

## 12. Slot10 Math in Practice

Slot 10 combines:
- hard gate predicates across Slot8/Slot4 + optional URF/MSE/ORP controls,
- baseline-relative canary SLO inequalities,
- deterministic rollback state machine,
- chain-linked audit hashing and signatures,
- feedback equations that modulate cultural risk and TRI strictness.

Most outputs are threshold-based booleans and bounded scalar adjustments rather than probabilistic models.

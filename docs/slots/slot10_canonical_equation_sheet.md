# Slot 10 Canonical Equation Sheet

Source anchors:
- `src/nova/slots/slot10_civilizational_deployment/core/policy.py`
- `src/nova/slots/slot10_civilizational_deployment/core/gatekeeper.py`
- `src/nova/slots/slot10_civilizational_deployment/core/lightclock_gatekeeper.py`
- `src/nova/slots/slot10_civilizational_deployment/core/canary.py`
- `src/nova/slots/slot10_civilizational_deployment/core/lightclock_canary.py`
- `src/nova/slots/slot10_civilizational_deployment/core/snapshot_backout.py`
- `src/nova/slots/slot10_civilizational_deployment/core/audit.py`
- `src/nova/slots/slot10_civilizational_deployment/core/feedback.py`
- `src/nova/slots/slot10_civilizational_deployment/core/metrics.py`
- `src/nova/slots/slot10_civilizational_deployment/mls.py`
- `src/nova/slots/slot10_civilizational_deployment/deployer.py`

## 1. Policy Defaults

```text
canary_stages = [0.01, 0.05, 0.25, 0.50, 1.00]
min_stage_duration_s = 300
canary_stage_timeout_s = 180
rollback_timeout_s = 10.0
min_promotion_gap_s = 0.0

slot08_integrity_threshold = 0.7
slot08_recovery_rate_threshold = 0.8
slot04_drift_z_threshold = 3.0

urf_composite_risk_threshold = 0.85
urf_alignment_threshold = 0.6
urf_risk_gap_threshold = 0.5

mse_deployment_threshold = 0.12

error_rate_multiplier = 1.15
latency_p95_multiplier = 1.10
saturation_threshold = 0.80
```

Derived:

```text
stage_count = len(canary_stages)
total_canary_duration_s = stage_count * canary_stage_timeout_s
```

## 2. Deployment Pipeline Gates

From `InstitutionalNodeDeployer.deploy`:

```text
MLSDecision:
  APPROVED -> ALLOW
  REQUIRES_TRANSFORMATION -> ALLOW_TRANSFORMED
  else -> QUARANTINE
```

Blocking logic:

```text
if decision == QUARANTINE:
  approved=False, reason=guardrail_block, phase=STEALTH_INTEGRATION

elif payload.capacity_block:
  approved=False, reason=capacity, phase=CONSENSUS

elif payload.secure is False:
  approved=False, reason=security, phase=SECURITY

else:
  approved=True, reason=registered, phase=REGISTER
```

## 3. Base Gatekeeper Predicates

Gate failures are appended; pass iff no failures:

```text
fail slot08_quarantine if quarantine_active == True
fail slot08_integrity if integrity_score < slot08_integrity_threshold
fail slot08_recovery_rate if success_rate_5m < slot08_recovery_rate_threshold
fail slot04_safe_mode if safe_mode_active == True
fail slot04_drift if drift_z >= slot04_drift_z_threshold
fail slot08_checksum_mismatch if checksum_mismatch == True
fail slot08_tamper_evidence if tamper_evidence == True

passed = (len(failed_conditions) == 0)
```

## 4. URF, MSE, ORP Gates

URF (flag: `NOVA_ENABLE_URF=1`):

```text
fail urf_composite_risk_high if composite_risk >= urf_composite_risk_threshold
fail urf_alignment_low if alignment_score < urf_alignment_threshold
fail urf_risk_gap_high if risk_gap > urf_risk_gap_threshold
```

MSE (flag: `NOVA_ENABLE_MSE=1`):

```text
fail mse_meta_instability_high if should_block_deployment(meta_instability, mse_deployment_threshold)
```

ORP (flag: `NOVA_ENABLE_ORP=1`):

```text
fail orp_deployment_freeze if posture_adjustments.deployment_freeze == True
```

Note: ORP emergency/recovery regimes log rollback warnings; blocking is driven by `deployment_freeze`.

## 5. Light-Clock Gate Equations

Env/registry composition:

```text
tri_gate = max(NOVA_TRI_GATE(default 0.66), tri_min_coherence(default 0.65))
drift_gate = slot07_tri_drift_threshold(default 2.2)
jitter_gate = tri_max_jitter(default 0.30)
stability_gate = slot07_stability_threshold_tri(default 0.05)
```

Phase window:

```text
if use_window:
  phase_min = max(NOVA_PHASE_LOCK_MIN(default 0.45), stability_gate)
  phase_max = max(NOVA_PHASE_LOCK_MAX(default 0.60), phase_min + 0.1)
else:
  phase_min = max(NOVA_PHASE_LOCK_GATE(default 0.70), stability_gate)
  phase_max = NOVA_PHASE_LOCK_CEILING(default 1.0)
```

Dynamic coherence threshold:

```text
tri_gate_dynamic = tri_gate
if tri_jitter >= jitter_gate: tri_gate_dynamic += 0.05
if pressure_level: tri_gate_dynamic += 0.05 * clamp(pressure_level, 0, 1)
```

Fail predicates:

```text
fail if tri_coherence is None or tri_coherence < tri_gate_dynamic
fail if tri_drift_z is not None and tri_drift_z > drift_gate
fail if phase_lock is None or phase_lock not in [phase_min, phase_max]
fail if slot9_policy is not None and slot9_policy not in allowed_slot9_policies
```

Coherence label:

```text
high if phase_lock >= phase_min + 0.1
low if phase_lock < phase_min
medium otherwise (if phase_lock exists)
unknown if phase_lock missing
```

## 6. Canary SLO Equations

Baseline:

```text
baseline = frozen_baseline if available else baseline_metrics
```

Violations:

```text
error_violation if current_error_rate > baseline_error_rate * error_rate_multiplier
latency_violation if current_latency_p95 > baseline_latency_p95 * latency_p95_multiplier
saturation_violation if current_saturation > saturation_threshold
```

All comparators are strict `>`.

## 7. Canary Progression State Machine

Evaluation order:

```text
if rollback_triggered: rollback
elif gate_fail: rollback
elif invalid_stage_idx: rollback
elif promotion_gap_guard_fails: continue
elif stage_duration < min_stage_duration_s: continue
elif slo_violation: rollback
elif stage_duration > canary_stage_timeout_s: rollback
else: promote
```

Promotion:

```text
if current_stage_idx >= len(stages)-1:
  total_duration = sum(stage.duration for stage in stages)
  action=promote(reason="Deployment completed")
else:
  current_stage_idx += 1
  next_stage.start_time = now
  action=promote(reason=f"Promoted to {next_stage.percentage:.1%}")
```

Rollback:

```text
rollback_triggered = True
current_stage.end_time = now
action = rollback
```

## 8. Light-Clock Canary Adjustments

Thresholds:

```text
high_coherence_acceleration = 0.85
low_coherence_deceleration = 0.4
minimal_coherence_block = 0.3
```

Adjustments:

```text
if phase_lock > 0.85:
  min_promotion_gap *= 0.7 (floor 0)
  min_stage_duration *= 0.8 (floor 30)
  error_rate_multiplier *= 1.1

elif phase_lock < 0.4:
  min_promotion_gap *= 1.5
  min_stage_duration *= 1.2
  error_rate_multiplier *= 0.9
  latency_p95_multiplier *= 0.95

elif phase_lock < 0.3:
  min_promotion_gap *= 2.0
  min_stage_duration *= 1.5
  error_rate_multiplier *= 0.8
  latency_p95_multiplier *= 0.9
```

As implemented, the `<0.3` branch is shadowed by the prior `<0.4` branch.

## 9. Snapshot Backout Equations

Snapshot timestamp:

```text
ts_ms = int(time.time() * 1000)
```

Rollback result:

```text
s10_ok = app_restore(slot10_id)
s8_ok = slot8_restore(slot08_id)
s4_ok = slot4_restore(slot04_id)

execution_time_s = now - start
success = s10_ok and s8_ok and s4_ok
```

MTTR annotation:

```text
if execution_time_s > rollback_timeout_s:
  errors["mttr"] = "...timeout..."
```

MTTR error does not override `success` when all restores are true.

## 10. Audit Hash and Signature Equations

Environment gate:

```text
env_truthy(name) := (os.getenv(name, "").strip() == "1")
```

Hash selection:

```text
if SHARED_HASH_AVAILABLE and env_truthy("NOVA_USE_SHARED_HASH"):
  hash_method = "shared_blake2b"
  hash = compute_audit_hash(body)
else:
  hash_method = "fallback_sha256"
  hash = sha256(canonical_json(body)).hexdigest()
```

Signature:

```text
sig = "hmac256:" + HMAC_SHA256(secret, canonical_json(body)).hexdigest()
```

Chain:

```text
body.prev = last_hash
body.previous_hash = last_hash
last_hash <- hash
```

## 11. Feedback Equations

Normalization:

```text
transform_rate = clamp(transform_rate, 0, 1)
error_rate = clamp(error_rate, 0, 1)
```

Cultural adjustment:

```text
if transform_rate > 0.4:
  residual_risk_delta = 0.15 * transform_rate
  action = stricter_validation

if rollback:
  residual_risk_delta += 0.25
  adaptation_effectiveness_delta = -0.20
  action = stabilize_memory
elif transform_rate < 0.1:
  adaptation_effectiveness_delta = +0.10
  action = increase_adaptation
```

TRI feedback:

```text
strict_mode = rollback or (error_rate > 0.1)
validation_boost = min(0.3, error_rate * 2.0)
```

Hook thresholds:

```text
on_canary_complete -> send TRI signal when (not success) or (error_rate > 0.05)
on_deployment_success -> send reset TRI signal when transform_rate < 0.1
```

## 12. Metrics Export Equations

Export scheduling:

```text
should_export = (now - last_export_ts) >= export_interval_s
```

Duration:

```text
stage_duration_s = current_stage.duration
total_duration_s = now - deployment_start_ts
```

Numeric encodings:

```text
deploy_active = 1 if deployment_active else 0
gate_status = 1 if gate_pass else 0
rollback_triggered = 1 if rollback else 0
saturation_pct = saturation * 100
gate_failed_conditions_count = len(gate_failed_conditions)
```

History retention:

```text
metrics_history keeps at most 100 latest snapshots
```

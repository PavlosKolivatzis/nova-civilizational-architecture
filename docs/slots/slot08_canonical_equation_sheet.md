# Slot 08 Canonical Equation Sheet

Source anchors:
- `src/nova/orchestrator/adapters/slot8_memory_ethics.py`
- `src/nova/orchestrator/router/advisors/slot08.py`
- `src/nova/slots/slot08_memory_ethics/lock_guard.py`
- `src/nova/slots/slot08_memory_ethics/ids_protection.py`
- `src/nova/slots/slot08_memory_lock/core/entropy_monitor.py`
- `src/nova/slots/slot08_memory_lock/core/repair_planner.py`
- `src/nova/slots/slot08_memory_lock/core/quarantine.py`
- `src/nova/slots/slot08_memory_lock/core/metrics.py`
- `src/nova/slots/slot08_memory_lock/core/integrity_store.py`
- `src/nova/slots/slot08_memory_lock/core/snapshotter.py`
- `src/nova/slots/slot08_memory_lock/ids/detectors.py`
- `src/nova/slots/slot08_memory_lock/pqc_verify.py`

## 1. Active Legacy Path Equations

### 1.1 Memory checksum

```text
checksum = sha3_256(serialize(data).encode()).hexdigest()
valid = compare_digest(current_checksum, stored_checksum)
```

### 1.2 IDS write gate

```text
deny if state != STABLE
deny if abs(drift) > 0.15
allow otherwise
```

### 1.3 Router score

```text
continuity = request.slot08_continuity
          or mirror["slot08.continuity_score"]
          or 0.6
score = clamp(continuity, 0, 1)
```

## 2. Entropy Monitor Equations

Given sliding window samples:

```text
schema_entropy = unique_schema_hashes / total_schema_hashes
size_entropy = min(1, stdev(content_sizes) / max(1, mean(content_sizes)))
operation_entropy = unique_operations / total_operations
```

Temporal term:

```text
if >=2 positive time deltas:
  temporal_variance = stdev(time_deltas) / max(0.1, mean(time_deltas))
  temporal_entropy = min(1, temporal_variance / 10)
else:
  temporal_entropy = 0
```

Combined:

```text
entropy_score = min(1,
  0.4*schema_entropy +
  0.2*size_entropy +
  0.2*operation_entropy +
  0.2*temporal_entropy
)
```

Anomaly:

```text
is_anomalous = entropy_score > adaptive_entropy_threshold
```

Adaptive threshold update (`theta`):

```text
if context == anomaly: alpha = entropy_alpha_up (default 0.35)
else: alpha = 0.10

theta = (1-alpha)*theta + alpha*obs
```

With frozen baseline `theta_base` (after 10 baseline samples) in normal/baseline context:

```text
theta = (1-beta)*theta + beta*theta_base     (beta default 0.50)
theta = max(entropy_min_rel_baseline * theta_base, theta)   (default factor 0.92)
adaptive_entropy_threshold = clamp(theta, 0.05, 0.95)
```

## 3. IDS Detector Equations

### 3.1 Surge detector

```text
current_rate = sum(write_counts within window_s)
```

Adaptive threshold:

```text
baseline_rate = mean(window_rate_i, i=1..5)
adaptive_threshold = max(threshold/2, min(3*threshold, int(3*baseline_rate)))
```

Fire condition:

```text
current_rate > adaptive_threshold
and (now - last_fire_ts) >= cooldown_s
```

### 3.2 Replay detector

```text
op_hash = sha256(json.dumps(operation_data, sort_keys=True))
replay if same op_hash seen within replay_window_s
```

### 3.3 Metadata anomaly

```text
anomaly if size mismatch
or abs(expected_mtime - actual_mtime) > 1
or permissions mismatch
```

## 4. Repair Planner Equations

### 4.1 Phase-lock derivation

If `NOVA_LIGHTCLOCK_DEEP=0`:

```text
phase_lock = None
```

Else priority:
1. mirror `slot04.phase_coherence`
2. mirror `slot07.pressure_level` mapping:

```text
phase_lock = 0.60 - 0.20 * clamp(pressure, 0, 1)
```

3. env `SLOT07_PHASE_LOCK`
4. default `0.5`.

### 4.2 Corruption severity score

```text
severity =
  0.3*I(corruption_detected) +
  0.4*I(tamper_evidence) +
  0.3*I(checksum_mismatch) +
  0.2*I(semantic_inversion) +
  0.2*I(entropy_score > 0.8) +
  0.1*repair_attempts*I(repair_attempts > 2)
```

Classification:
- critical `>=0.8`
- high `>=0.5`
- medium `>=0.2`
- low otherwise.

### 4.3 Restore option

```text
age_hours = (now_ms - snapshot.ts_ms)/(1000*3600)
data_loss_risk = age_hours/24
restore_time_s = 5 + 0.1*(content_size_mb) + 0.01*(file_count)
```

Restore success probability:

```text
base = 0.9
age_penalty = min(0.3, age_hours/168)
if snapshot_status != OK: base *= 0.7
historical = success_rates.get(RESTORE_LAST_GOOD, 0.85)

p_restore = max(0.1, base - age_penalty) * historical
```

### 4.4 Strategy score

```text
score = 40*success_probability - 30*data_loss_risk
if recovery_time > mttr_target_s:
  score -= 2*(recovery_time - mttr_target_s)
```

Bonuses:
- `+10` restore + malicious
- `+15` semantic patch + logical corruption
- `+8` majority vote + localized

Historical scaling:

```text
score *= success_rates.get(action, 0.7)
```

Phase-lock threshold (`SLOT08_PHASE_LOCK_THRESHOLD`, default `0.5`):
- low phase lock:
  - `+10` restore/block
  - `-5` semantic patch
- high phase lock: no numeric penalty/bonus.

Critical severity modifier:
- block: `+5`
- other strategies: `score *= 0.8`

Final:

```text
score = max(0, score)
```

### 4.5 Decision confidence

```text
base_conf = selection_score/100
analysis_conf = corruption_analysis_confidence
conf = (base_conf + analysis_conf)/2
if recent_failures_last5 > 2: conf *= 0.8
if historical_samples_for_action > 3: conf *= 1.1
decision_confidence = clamp(conf, 0, 1)
```

### 4.6 Learning posterior

```text
success_rate(action) = (s + 1) / (s + f + 2)
```

## 5. Quarantine and SLO Equations

### 5.1 Recovery gate

```text
recoverable =
  integrity_verified
  and threat_mitigated
  and (not ongoing_threats)
  and (system_health_score >= 0.8)
```

### 5.2 Quarantine metrics

```text
recovery_success_rate = successful_recoveries / max(1, total_activations)
average_quarantine_duration = mean(duration_seconds over deactivations)
auto_recovery_rate = auto_successes / max(1, total_activations)
```

### 5.3 Metrics SLOs

```text
mttr_slo = 1 - count(mttr>5s)/max(1, recent_recoveries)
flip_slo = 1 - count(activation_duration>1s)/max(1, recent_activations)
```

Deploy gate:

```text
integrity_ok = integrity_score >= 0.7
quarantine_ok = not quarantine_active
recovery_ok = recovery_success_rate_5m >= 0.8
gate_open = integrity_ok and quarantine_ok and recovery_ok
```

## 6. Integrity and Snapshot Equations

Merkle parent:

```text
parent = H(left + ":" + right)
```

Odd-leaf rule: `right = left`.

Directory integrity:

```text
is_valid = (current_merkle_root == expected_root)
```

Snapshot performance:

```text
average_snapshot_time = total_snapshot_time / max(1, snapshot_count)
```

Retention rule: keep newest `retention_snapshots`.

## 7. PQC Verification Logic

Counters update on each verification:
- total increments always
- success increments on valid signature
- failure increments on invalid/missing/exception.

No additional numerical scoring model is applied in current implementation.

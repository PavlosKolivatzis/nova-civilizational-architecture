# Slot 08 Logic and Math Extraction

This document extracts Slot 08 behavior from implementation code in:
- `src/nova/orchestrator/adapters/slot8_memory_ethics.py`
- `src/nova/orchestrator/router/advisors/slot08.py`
- `src/nova/slots/slot08_memory_ethics/lock_guard.py`
- `src/nova/slots/slot08_memory_ethics/ids_protection.py`
- `src/nova/slots/slot08_memory_lock/core/policy.py`
- `src/nova/slots/slot08_memory_lock/core/types.py`
- `src/nova/slots/slot08_memory_lock/core/entropy_monitor.py`
- `src/nova/slots/slot08_memory_lock/core/repair_planner.py`
- `src/nova/slots/slot08_memory_lock/core/quarantine.py`
- `src/nova/slots/slot08_memory_lock/core/metrics.py`
- `src/nova/slots/slot08_memory_lock/core/integrity_store.py`
- `src/nova/slots/slot08_memory_lock/core/snapshotter.py`
- `src/nova/slots/slot08_memory_lock/ids/detectors.py`
- `src/nova/slots/slot08_memory_lock/pqc_verify.py`
- `tests/test_slot08_lock_guard_api.py`
- `tests/test_slot08_mirror_integration.py`
- `src/nova/slots/slot08_memory_lock/tests/test_repair_planner_phase_lock.py`
- `src/nova/slots/slot08_memory_lock/tests/test_entropy_monitor_small_samples.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `e6a50d8`: Slot 8 folder structure introduction
- `ac80cc3`: memory lock and ethics guard introduction
- `a72dd47`: Slot 8 Processual (4.0) phase completion
- `ab09e1e`: quantum-verified attestation (Slot01+Slot08)
- `4172dbc`: real PQC verification integration via Slot08

## 1. Runtime Topology

### 1.1 Active orchestrator path (legacy ethics guard)
`Slot8MemoryEthicsAdapter` delegates to `slot08_memory_ethics`:
- register/read/write wrappers
- defensive fallback when unavailable.

This path uses:
- `MemoryLock` checksum/tamper verification
- `EthicsGuard` ACL policy checks
- `ids_protection` write eligibility guard.

### 1.2 Processual 4.0 path (advanced memory lock)
`slot08_memory_lock` is implemented and test-covered for:
- entropy drift monitoring
- IDS multi-detector suite
- quarantine and recovery
- repair strategy planning
- Merkle/snapshot integrity lifecycle
- PQC attestation verification service.

### 1.3 Router advisory path
`router/advisors/slot08.py` computes Slot08 routing score from continuity:
- request override `slot08_continuity`, else mirror `slot08.continuity_score`, else default `0.6`
- clamped to `[0,1]`.

## 2. Legacy Ethics Guard Math/Logic (`slot08_memory_ethics`)

### 2.1 MemoryLock integrity rule
Checksum:

```text
checksum = sha3_256(serialize(data).encode()).hexdigest()
```

Verification:

```text
valid = compare_digest(current_checksum, stored_checksum)
```

Read/write gates:
- read fails on tamper
- write fails if read-only
- write fails if pre-write integrity check fails.

### 2.2 ACL access logic (`EthicsGuard`)
For read/write:
- deny if object missing
- deny if policy set is non-empty and actor not in allowed set
- allow otherwise.

### 2.3 IDS write-eligibility logic (`ids_protection.py`)
Decision order:
1. If IDS disabled: allow.
2. If embedding vector empty: deny.
3. Analyze vector: `stability`, `drift`, `state`.
4. Deny if `state != STABLE`.
5. Deny if `abs(drift) > 0.15`.
6. Allow otherwise.

## 3. Processual 4.0 Core Math (`slot08_memory_lock`)

## 3.1 Entropy monitor (`core/entropy_monitor.py`)

### 3.1.1 Entropy components
Given sliding-window samples:

```text
schema_entropy = unique_schema_hashes / total_schema_hashes

size_entropy = min(1, stdev(content_sizes) / max(1, mean(content_sizes)))

operation_entropy = unique_operations / total_operations

temporal_entropy:
  if >=2 positive time deltas:
    temporal_variance = stdev(time_deltas) / max(0.1, mean(time_deltas))
    temporal_entropy = min(1, temporal_variance / 10)
  else:
    temporal_entropy = 0
```

Combined score:

```text
entropy_score = min(1,
  0.4*schema_entropy +
  0.2*size_entropy +
  0.2*operation_entropy +
  0.2*temporal_entropy
)
```

Anomaly predicate:

```text
is_anomalous = entropy_score > adaptive_entropy_threshold
```

### 3.1.2 Adaptive threshold update
When window has at least 5 samples:

```text
theta := adaptive_entropy_threshold
obs := current_entropy
```

If context is anomaly:

```text
alpha = policy.entropy_alpha_up   # default 0.35
theta = (1-alpha)*theta + alpha*obs
```

Else (normal/baseline):

```text
alpha = 0.10
theta = (1-alpha)*theta + alpha*obs
```

After 10 baseline-tagged samples, freeze baseline `theta_base`.
For normal/baseline contexts with frozen baseline:

```text
theta = (1-beta)*theta + beta*theta_base      # beta=policy.entropy_k_revert (default 0.50)
theta = max(policy.entropy_min_rel_baseline * theta_base, theta)   # default min factor 0.92
```

Final clamp:

```text
adaptive_entropy_threshold = clamp(theta, 0.05, 0.95)
```

## 3.2 IDS detector math (`ids/detectors.py`)

### 3.2.1 Surge detector
Windowed rate:

```text
current_rate = sum(write_counts in last window_s)
```

Adaptive threshold (after >10 events):

```text
baseline_rate = mean(sampled_window_rates_over_5_windows)
adaptive_threshold = max(threshold/2, min(3*threshold, int(3*baseline_rate)))
```

Surge fires when:

```text
current_rate > adaptive_threshold
and (now - last_fire_ts) >= cooldown_s
```

### 3.2.2 Forbidden path detector
Forbidden if:
- regex pattern match from denylist, or
- suspicious path indicators (traversal, proc/dev, secrets/git patterns).

### 3.2.3 Tamper detector
Flags tamper on:
- content hash mismatch
- signature verify failure
- metadata anomaly:
  - size mismatch, or
  - `abs(expected_mtime - actual_mtime) > 1s`, or
  - permission mismatch.

### 3.2.4 Replay detector
Operation hash:

```text
op_hash = sha256(json.dumps(operation_data, sort_keys=True))
```

Replay if same hash seen within replay window.

## 3.3 Repair planner math (`core/repair_planner.py`)

### 3.3.1 Phase-lock acquisition
If `NOVA_LIGHTCLOCK_DEEP=0` -> `None`.

Else priority:
1. `slot04.phase_coherence` from mirror
2. pressure-modulated fallback from `slot07.pressure_level`:

```text
phase_lock = 0.60 - 0.20 * clamp(pressure, 0, 1)   # range [0.40, 0.60]
```

3. env `SLOT07_PHASE_LOCK`
4. default `0.5`.

### 3.3.2 Corruption severity score

```text
severity_score = 0
+0.3 if corruption_detected
+0.4 if tamper_evidence
+0.3 if checksum_mismatch
+0.2 if semantic_inversion
+0.2 if entropy_score > 0.8
+0.1 * repair_attempts if repair_attempts > 2
```

Severity classes:
- `critical` if `>=0.8`
- `high` if `>=0.5`
- `medium` if `>=0.2`
- `low` otherwise.

Scope:
- widespread if `len(affected_files)/total_files > 0.5`
- moderate if `len(affected_files) > 10`
- localized otherwise.

Analysis confidence:

```text
confidence = min(1, severity_score)
```

### 3.3.3 Repair options
Restore option:

```text
age_hours = (now_ms - snapshot.ts_ms) / (1000*3600)
data_loss_risk = age_hours / 24
recovery_time = 5 + 0.1*(size_mb) + 0.01*(file_count)
```

Fixed options:
- majority vote: success `0.8`, risk `0.1`, time `30s`
- semantic patch (logical corruption): success `0.6`, risk `0.2`, time `15s`
- block: success `1.0`, risk `1.0`, time `0s`.

### 3.3.4 Restore success probability

```text
base = 0.9
age_penalty = min(0.3, age_hours/168)
if snapshot_status != OK: base *= 0.7
historical_rate = success_rates.get(RESTORE_LAST_GOOD, 0.85)

restore_success_probability = max(0.1, base - age_penalty) * historical_rate
```

### 3.3.5 Option scoring

```text
score = 40*success_probability - 30*data_loss_risk
if recovery_time > mttr_target_s:
  score -= 2*(recovery_time - mttr_target_s)
```

Type/context bonuses:
- `+10` restore + malicious
- `+15` semantic patch + logical corruption
- `+8` majority vote + localized scope.

Historical scaling:

```text
score *= success_rates.get(action, 0.7)
```

Phase-lock adjustment (`SLOT08_PHASE_LOCK_THRESHOLD`, default `0.5`):
- if below threshold:
  - `+10` for restore/block
  - `-5` for semantic patch
  - annotate conservative mode.
- else annotate normal mode.

Critical severity adjustment:
- block gets `+5`
- other actions scaled by `0.8`.

Final:

```text
score = max(0, score)
```

### 3.3.6 Decision confidence

```text
base_conf = selection_score / 100
analysis_conf = corruption_analysis.confidence
combined = (base_conf + analysis_conf) / 2

if recent_failures_in_last_5 > 2: combined *= 0.8
if historical_data_for_action_available: combined *= 1.1

decision_confidence = clamp(combined, 0, 1)
```

### 3.3.7 Learning update
Outcome posterior per action:

```text
success_rate = (s + 1) / (s + f + 2)
```

(`s`: success count, `f`: failure count; Beta(1,1) posterior mean).

## 3.4 Quarantine logic (`core/quarantine.py`)

### 3.4.1 Access semantics
- outside quarantine: read/write allowed
- active quarantine:
  - read allowed iff `allow_read_only_access=True`
  - write denied when active (or write-block flag).

### 3.4.2 Recovery gate checks
Recovery succeeds only if all true:
- `integrity_verified`
- `threat_mitigated`
- `not ongoing_threats`
- `system_health_score >= 0.8`.

### 3.4.3 Quarantine metrics

```text
recovery_success_rate = successful_recoveries / max(1, total_activations)
average_quarantine_duration = mean(deactivation_durations)
auto_recovery_rate = auto_recoveries / max(1, total_activations)
```

## 3.5 Metrics/SLO math (`core/metrics.py`)

Windowed SLOs:

```text
mttr_slo_compliance = 1 - (count(mttr>5s) / max(1, recent_recoveries))
quarantine_flip_slo_compliance = 1 - (count(activation_duration>1s) / max(1, recent_activations))
```

Deploy gate:
- `integrity_score >= 0.7`
- `quarantine_active == False`
- `recovery_success_rate_5m >= 0.8`.

Where:

```text
recovery_success_rate_5m = count(mttr<=5s in 5m) / recent_recoveries_in_5m
default = 1.0 if no recent recoveries
```

Gate:

```text
gate_open = all(conditions)
```

## 3.6 Integrity and snapshot math

### 3.6.1 Merkle integrity (`core/integrity_store.py`)
- leaf hash includes content hash and (optionally) metadata
- parent combine rule: `H(left + ":" + right)`
- odd leaf is duplicated (`right = left`)
- `EMPTY_TREE` and `EMPTY_DIR` sentinels for degenerate cases.

Verification:

```text
is_valid = (current_merkle_root == expected_root)
```

### 3.6.2 Snapshot metrics (`core/snapshotter.py`)
- snapshot ID: `snap_<epoch_ms>_<pid>`
- average snapshot time:

```text
average_snapshot_time = total_snapshot_time / max(1, snapshot_count)
```

- retention cleanup keeps newest `retention_snapshots`.

## 3.7 PQC verification logic (`pqc_verify.py`)
- key registry with active/inactive lifecycle
- verification counters:
  - `verifications_total`
  - `verifications_success`
  - `verifications_failure`
  - `key_rotations_total`
- verification decision = output of `PQCAttestationBuilder.verify_attestation(...)`.

## 4. Slot08 in Practice

Slot 8 currently operates as a dual stack:
1. Active legacy orchestrator integration (ACL + checksum + IDS drift gate).
2. Processual 4.0 advanced self-healing system with richer quantitative controls.

The strongest math appears in:
- entropy scoring + adaptive thresholds,
- repair strategy scoring + Bayesian success updates,
- IDS adaptive surge thresholds,
- quarantine/recovery SLO compliance and deployment gate checks.

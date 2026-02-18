# Slot 09 Canonical Equation Sheet

Source anchors:
- `src/nova/slots/slot09_distortion_protection/hybrid_api.py`
- `src/nova/slots/slot09_distortion_protection/ids_policy.py`
- `src/nova/slots/slot09_distortion_protection/void_bypass.py`
- `src/nova/continuity/slot09_sensitivity.py`
- `src/nova/orchestrator/adapters/slot9_distortion_protection.py`
- `tests/test_hybrid_api_coverage.py`
- `tests/test_policy_threat_mapping_consistency.py`
- `tests/test_slot09_shared_hash_coverage.py`
- `tests/slot09_distortion_protection/test_ids_policy.py`
- `tests/slot09_distortion_protection/test_slot09_sensitivity_integration.py`
- `tests/slots/slot09/test_void_bypass.py`

## 1. Core Defaults

```text
threat_threshold_warning = 0.6
threat_threshold_block = 0.8
ids_stability_threshold_low = 0.25
ids_stability_threshold_medium = 0.5
ids_stability_threshold_high = 0.75
ids_drift_threshold_low = 0.02
ids_drift_threshold_medium = 0.1
ids_drift_threshold_high = 0.3
confidence_stability_weight = 0.6
confidence_drift_weight = 0.4
```

## 2. Feature Vector Equations

Traits vector:

```text
[
  len(content)/1000,
  count('!')/max(1,len(content)),
  count('?')/max(1,len(content)),
  unique_words/max(1,word_count),
  uppercase_chars/max(1,len(content)),
  newline_count/max(1,len(content))
]
```

Content vector:

```text
[
  word_count/100,
  avg_word_length,
  sentence_count/max(1,len(content)),
  complex_word_ratio(len>7),
  comma_count/max(1,len(content)),
  unique_chars/max(1,len(content))
]
```

## 3. Fallback Heuristic Equations

```text
stability = clamp(0.8 - content_length/10000, 0, 1)
drift = clamp((word_count - 50)/100, -0.5, 0.5)

traits_stability = stability
traits_drift = drift
content_stability = stability * 0.9
content_drift = drift * 1.1
```

## 4. Threat Scoring Equations

Base threat by final policy:

```text
ALLOW_FASTPATH -> 0.1
ALLOW_WITH_MONITORING -> 0.2
STANDARD_PROCESSING -> 0.3
STAGED_DEPLOYMENT -> 0.5
RESTRICTED_SCOPE_DEPLOYMENT -> 0.6
DEGRADE_AND_REVIEW -> 0.7
BLOCK_OR_SANDBOX -> 0.9
default -> 0.3
```

Penalty terms:

```text
avg_stability = (traits_stability + content_stability) / 2
max_drift = max(abs(traits_drift), abs(content_drift))

stability_penalty =
  0.3 if avg_stability < ids_stability_threshold_low
  0.2 if avg_stability < ids_stability_threshold_medium
  0.1 if avg_stability < ids_stability_threshold_high
  0.0 otherwise

drift_penalty =
  0.2 if max_drift > ids_drift_threshold_high
  0.15 if max_drift > ids_drift_threshold_medium
  0.1 if max_drift > ids_drift_threshold_low
  0.0 otherwise

threat_level = round(clamp(base_threat + stability_penalty + drift_penalty, 0, 1), 3)
```

Status gate:

```text
if threat_level >= threat_threshold_block: status = BLOCKED
elif threat_level >= threat_threshold_warning: status = WARNING
else: status = SUCCESS
```

## 5. Confidence Equation

```text
stability_confidence =
  traits_stability * confidence_stability_weight +
  content_stability * (1 - confidence_stability_weight)

avg_abs_drift = (abs(traits_drift) + abs(content_drift)) / 2
drift_penalty = avg_abs_drift * confidence_drift_weight

confidence = round(clamp(stability_confidence * (1 - drift_penalty), 0.1, 1.0), 3)
```

## 6. Classification Mappings

Distortion type:

```text
if policy == BLOCK_OR_SANDBOX: SYSTEMATIC_MANIPULATION
elif severity == high: INFRASTRUCTURE_MAINTAINED
elif severity == medium: CULTURAL_TRADITIONAL
else: INDIVIDUAL_COGNITIVE
```

Infrastructure level:

```text
low -> individual
normal -> cultural
medium -> institutional
high -> infrastructure
```

Threat severity:

```text
low|normal|medium|high -> ThreatSeverity enum direct mapping
```

## 7. Threat Landscape Equations

```text
economic_score = min(1, keyword_matches / len(economic_keywords))
institutional_score = min(1, keyword_matches / len(institutional_keywords))
systematic_pattern_score = min(1, (abs(traits_drift) + abs(content_drift)) / 2)
persistence_score = 1 - avg_stability
```

Urgency gate:

```text
if avg_stability < 0.3: critical
elif avg_stability < 0.6: high
elif avg_stability < 0.8: medium
else: low
```

Intervention success probability:

```text
base =
  0.9 for low
  0.8 for normal
  0.6 for medium
  0.4 for high
  0.7 default

stability_bonus = (avg_stability - 0.5) * 0.2
success_probability = round(clamp(base + stability_bonus, 0.1, 1.0), 2)
```

## 8. IDS Policy Equations

Base IDS policy from one analysis result:

```text
if stability < 0.25:
  policy=BLOCK_OR_SANDBOX, severity=high
elif 0.25 <= stability < 0.5 and abs(drift) > 0.1:
  policy=DEGRADE_AND_REVIEW, severity=medium
elif stability >= 0.75 and abs(drift) < 0.02:
  policy=ALLOW_FASTPATH, severity=low
else:
  policy=STANDARD_PROCESSING, severity=normal
```

Phase-lock coherence categories:

```text
high if phase_lock > 0.8
medium if phase_lock > 0.6
low if phase_lock > 0.4
minimal otherwise
```

Phase-lock adjustments:

```text
high coherence:
  DEGRADE_AND_REVIEW+medium -> STANDARD_PROCESSING+normal

low coherence:
  ALLOW_FASTPATH -> STANDARD_PROCESSING+normal
  STANDARD_PROCESSING -> DEGRADE_AND_REVIEW+medium

minimal coherence:
  ALLOW_FASTPATH or STANDARD_PROCESSING -> DEGRADE_AND_REVIEW+medium
  DEGRADE_AND_REVIEW -> BLOCK_OR_SANDBOX+high
```

Dual-analysis merge priority:

```text
BLOCK_OR_SANDBOX(4) > DEGRADE_AND_REVIEW(3) > STANDARD_PROCESSING(2) > ALLOW_FASTPATH(1)
```

## 9. ORP Sensitivity Equations

Multiplier table:

```text
normal -> 1.00
heightened, duration < 300s -> 1.05
heightened, duration >= 300s -> 1.15
controlled_degradation -> 1.30
emergency_stabilization -> 1.50
recovery -> 1.20
unknown -> 1.00
```

Scaling:

```text
threshold_scaled = base_threshold * multiplier
threshold_scaled = clamp(threshold_scaled, base_threshold, 2 * base_threshold)
```

Applied only to IDS stability/drift thresholds (not threat response thresholds or resilience settings).

## 10. Resilience/Monitoring Equations

Circuit breaker:

```text
open when failure_count >= threshold
open -> half_open when (now - last_failure_time) > reset_timeout
half_open success -> closed and failure_count=0
closed success -> failure_count = max(0, failure_count - 1)
```

Cache:

```text
hit if key exists and (now - ts) < ttl
expired entries evicted on access
insert over max_size evicts LRU
hit_rate = hits / max(1, hits + misses)
```

Health metrics:

```text
avg_ms = mean(processing_times)
p50 = sorted_times[len//2]
p95 = sorted_times[int(len*0.95)]
p99 = sorted_times[int(len*0.99)]

error_rate = error_count / max(1,total_requests)
block_rate = blocked_requests / max(1,total_requests)
warning_rate = warning_requests / max(1,total_requests)
rps = total_requests / max(1,uptime_seconds)
cache_capacity_used = cache_size / max_cache_size
```

Health status gate:

```text
unhealthy if error_rate > 0.10 or circuit_breaker_open
degraded if error_rate > 0.05 or avg_ms > 100
healthy otherwise
```

## 11. Audit Hash Chain Equations

Environment gate:

```text
env_truthy(name) := (os.getenv(name,"").strip() == "1")
```

Shared-hash path:

```text
if SHARED_HASH_AVAILABLE and env_truthy("NOVA_USE_SHARED_HASH"):
  hash_signature = compute_audit_hash(structured_record)
  hash_method = shared_blake2b
```

Fallback path:

```text
parts = (
  trace_id, timestamp, policy_decision, decision_reason,
  json(compliance_markers), json(processing_path), str(processing_time_ms)
)
digest = sha256(previous_hash_bytes + "|".join(parts).encode("utf-8")).hexdigest()
hash_signature = "sha256:" + digest
hash_method = fallback_sha256
```

Chain state:

```text
previous_event_hash = last_audit_hash or ""
retention_policy = "7_years"
last_audit_hash <- hash_signature
```

## 12. Bulk and Adapter Logic

Bulk detect:

```text
concurrency_limit = 10
global_timeout_s = len(requests) * 2
```

Adapter return contract:

```text
success -> response dict
engine missing -> {"status":"unavailable"}
exception -> {"status":"error"}
```

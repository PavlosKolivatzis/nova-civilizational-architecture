# Slot 09 Logic and Math Extraction

This document extracts Slot 09 behavior from implementation code in:
- `src/nova/slots/slot09_distortion_protection/hybrid_api.py`
- `src/nova/slots/slot09_distortion_protection/ids_policy.py`
- `src/nova/slots/slot09_distortion_protection/void_bypass.py`
- `src/nova/slots/slot09_distortion_protection/health.py`
- `src/nova/continuity/slot09_sensitivity.py`
- `src/nova/orchestrator/adapters/slot9_distortion_protection.py`
- `tests/test_hybrid_api_coverage.py`
- `tests/test_distortion_protection_enhanced.py`
- `tests/test_policy_threat_mapping_consistency.py`
- `tests/test_slot09_shared_hash_coverage.py`
- `tests/slot09_distortion_protection/test_ids_policy.py`
- `tests/slot09_distortion_protection/test_slot09_sensitivity_integration.py`
- `tests/slots/slot09/test_void_bypass.py`
- `tests/slot09_distortion_protection/test_health.py`

Historical cross-check from `archive/NOVA_HISTORY.md`:
- `9136770`: `feat(slot9): add hybrid distortion protection API`
- Slot 09 appears in the operational-hardening phase alongside IDS/circuit-breaker work.

## 1. Runtime Logic

### 1.1 Main API path (`HybridDistortionDetectionAPI.detect_distortion`)
Per request:
1. Circuit breaker gate (`is_open`).
2. Content validation:
   - non-empty/non-whitespace.
   - UTF-8 byte length <= `max_content_length_bytes`.
3. Secure cache lookup (`slot9:<content_sha_prefix>:<context_sha_prefix>`).
4. Processing path:
   - VOID bypass path, or
   - IDS policy integration path, or
   - fallback heuristic path.
5. Response construction:
   - threat/status/confidence/classification/IDS analysis/audit trail.
6. Cache successful non-error responses.
7. Circuit-breaker success/failure update.
8. Metrics updates through async context:
   - `total_requests += 1`
   - append processing time
   - retain last 1000 latency samples.

### 1.2 Processing path selector (`_process_with_nova_integration`)
Priority:
1. VOID check with `should_bypass_distortion_check(graph_state=...)`.
2. If `NOVA_INTEGRATION_AVAILABLE and IDS_ENABLED`: `_process_with_ids_policy`.
3. Else fallback logic.

### 1.3 IDS integration path (`_process_with_ids_policy`)
- Builds two vectors (`traits`, `content`) from request text.
- Calls synchronous `policy_check_with_ids(...)` in executor.
- Timeout enforced by:

```text
timeout_s = max_processing_time_ms / 1000
```

- Timeout raises `TimeoutError("IDS processing timed out")`.

### 1.4 Fallback path (`_process_with_fallback_logic`)
If IDS path unavailable/fails over:
- derives heuristic stability/drift from content length and word count,
- emits `STANDARD_PROCESSING` policy envelope with synthetic traits/content analyses.

### 1.5 Bulk path and feedback shaping
`bulk_detect(...)`:
- concurrency bounded by semaphore size `10`,
- global timeout `len(requests) * 2` seconds,
- per-item exceptions converted to structured error responses.

`report_deployment_feedback(...)`:
- rounds measured threat/prediction and false positive/negative rates to 3 decimals.

## 2. Core Math in Hybrid API

### 2.1 Vector feature extraction
Traits vector:

```text
[
  len(content)/1000,
  count('!')/max(1,len(content)),
  count('?')/max(1,len(content)),
  unique_words/max(1,total_words),
  uppercase_chars/max(1,len(content)),
  linebreaks/max(1,len(content))
]
```

Content vector:

```text
[
  word_count/100,
  avg_word_length,
  sentence_count/max(1,len(content)),
  complex_words(>7 chars)/max(1,word_count),
  comma_count/max(1,len(content)),
  unique_chars/max(1,len(content))
]
```

### 2.2 Fallback stability/drift formulas

```text
stability = clamp(0.8 - content_length/10000, 0, 1)
drift = clamp((word_count - 50)/100, -0.5, 0.5)
```

Fallback content branch:

```text
content_stability = stability * 0.9
content_drift = drift * 1.1
```

### 2.3 Threat score (`_calculate_sophisticated_threat_level`)
Base threat from final policy:
- `ALLOW_FASTPATH=0.1`
- `ALLOW_WITH_MONITORING=0.2`
- `STANDARD_PROCESSING=0.3`
- `STAGED_DEPLOYMENT=0.5`
- `RESTRICTED_SCOPE_DEPLOYMENT=0.6`
- `DEGRADE_AND_REVIEW=0.7`
- `BLOCK_OR_SANDBOX=0.9`

Stability penalty from average stability:
- `+0.3` if `< ids_stability_threshold_low`
- `+0.2` if `< ids_stability_threshold_medium`
- `+0.1` if `< ids_stability_threshold_high`

Drift penalty from max absolute drift:
- `+0.2` if `> ids_drift_threshold_high`
- `+0.15` if `> ids_drift_threshold_medium`
- `+0.1` if `> ids_drift_threshold_low`

Final:

```text
threat = clamp(base + stability_penalty + drift_penalty, 0, 1)
```

Rounded to 3 decimals.

### 2.4 Status thresholds

```text
if threat >= threat_threshold_block: BLOCKED
elif threat >= threat_threshold_warning: WARNING
else: SUCCESS
```

Defaults:
- warning `0.6`
- block `0.8`

### 2.5 Confidence formula (`_calculate_ids_based_confidence`)

```text
stability_conf =
  traits_stability * confidence_stability_weight +
  content_stability * (1 - confidence_stability_weight)

avg_drift = (abs(traits_drift) + abs(content_drift))/2
drift_penalty = avg_drift * confidence_drift_weight

confidence = clamp(stability_conf * (1 - drift_penalty), 0.1, 1.0)
```

Rounded to 3 decimals.

Defaults:
- `confidence_stability_weight=0.6`
- `confidence_drift_weight=0.4`

### 2.6 Classification mappings
Distortion type:
- `BLOCK_OR_SANDBOX -> SYSTEMATIC_MANIPULATION`
- severity high -> `INFRASTRUCTURE_MAINTAINED`
- severity medium -> `CULTURAL_TRADITIONAL`
- severity low/normal -> `INDIVIDUAL_COGNITIVE`

Infrastructure level from severity:
- low -> individual
- normal -> cultural
- medium -> institutional
- high -> infrastructure

Threat severity enum mapping:
- low/normal/medium/high direct mapping.

### 2.7 Threat-landscape helper math

```text
economic_score = min(1, keyword_matches / len(economic_keywords))
institutional_score = min(1, keyword_matches / len(institutional_keywords))
systematic_patterns = min(1, (|traits_drift| + |content_drift|)/2)
persistence_score = 1 - avg_stability
```

Intervention urgency:
- critical if avg stability < 0.3
- high if < 0.6
- medium if < 0.8
- else low.

Success probability (`_estimate_success_probability`):
- base by severity:
  - low 0.9, normal 0.8, medium 0.6, high 0.4
- adjustment:

```text
stability_bonus = (avg_stability - 0.5) * 0.2
success_probability = clamp(base + stability_bonus, 0.1, 1.0)
```

Rounded to 2 decimals.

Threat-vector logic:
- policy `BLOCK_OR_SANDBOX` adds `systematic_manipulation`, `coordinated_campaign`.
- policy `DEGRADE_AND_REVIEW` adds `infrastructure_distortion`, `institutional_bias`.
- `abs(traits_drift) > 0.2` adds `behavioral_manipulation`.
- `abs(content_drift) > 0.2` adds `content_manipulation`.

### 2.8 Audit hash-chain logic
`_add_hash_chain` always includes:
- `previous_event_hash`
- `hash_signature`
- `hash_method`
- `retention_policy = "7_years"`

Flag parsing:

```text
_env_truthy(name) == True only when os.getenv(name).strip() == "1"
```

Shared mode:
- if `NOVA_USE_SHARED_HASH=1` and shared hash utility available:
  - uses shared Blake2b utility over structured record.
  - `hash_method = "shared_blake2b"`.

Fallback mode:

```text
parts = (
  trace_id, timestamp, policy_decision, decision_reason,
  json(compliance_markers), json(processing_path), str(processing_time_ms)
)
current_hash = sha256(previous_hash_bytes + "|".join(parts).encode("utf-8"))
hash_signature = "sha256:" + current_hash
hash_method = "fallback_sha256"
```

### 2.9 Circuit breaker and cache math
Circuit breaker:
- opens when `failure_count >= threshold`.
- while open, transitions to half-open when elapsed `> reset_timeout`.
- half-open success closes and resets failures to 0.
- closed-state success decrements failures by 1 down to 0.

Cache:
- hit when key exists and `now - timestamp < ttl`.
- expired key is evicted immediately on read.
- LRU eviction when inserting over `max_size`.
- hit rate:

```text
hit_rate = hits / max(1, hits + misses)
```

`clear_expired` removes keys with `now - ts >= ttl`.

### 2.10 Health and system-rate math (`get_comprehensive_system_health`)
Latency aggregates:
- average, p50, p95, p99 from tracked `processing_times`.
- percentile indexing is implemented as:
  - `p50 = sorted[len//2]`
  - `p95 = sorted[int(len*0.95)]`
  - `p99 = sorted[int(len*0.99)]`

Rates:

```text
error_rate = error_count / max(1, total_requests)
block_rate = blocked_requests / max(1, total_requests)
warning_rate = warning_requests / max(1, total_requests)
rps = total_requests / max(1, uptime_seconds)
cache_capacity_used = cache_size / max_size
```

Status decision:
- unhealthy if `error_rate > 0.10` or circuit breaker open.
- degraded if `error_rate > 0.05` or average processing time `> 100ms`.
- healthy otherwise.

## 3. IDS Policy Math (`ids_policy.py`)

### 3.1 Base IDS policy decision
From one analysis result (`stability`, `drift`, `state`):

```text
if stability < 0.25:
  BLOCK_OR_SANDBOX (high)
elif 0.25 <= stability < 0.50 and |drift| > 0.10:
  DEGRADE_AND_REVIEW (medium)
elif stability >= 0.75 and |drift| < 0.02:
  ALLOW_FASTPATH (low)
else:
  STANDARD_PROCESSING (normal)
```

### 3.2 Phase-lock context
If `NOVA_LIGHTCLOCK_DEEP=0`:
- unavailable.

Else reads mirror `slot07.phase_lock` and classifies:
- high `>0.8`
- medium `>0.6`
- low `>0.4`
- minimal otherwise.

### 3.3 Phase-lock policy adjustments
Given base policy:
- high coherence:
  - degrade+medium -> standard+normal
- low coherence:
  - allow_fastpath -> standard+normal
  - standard -> degrade+medium
- minimal coherence:
  - allow_fastpath/standard -> degrade+medium
  - degrade -> block+high

Reason string is always suffixed with `|phase_lock_<value>_<coherence_level>`.

### 3.4 Dual-vector final policy combine
`policy_check_with_ids` runs policy for:
- traits vector analysis,
- content vector analysis.

Priority selection:
- block (4) > degrade (3) > standard (2) > fastpath (1).

Highest-priority policy becomes final.

## 4. VOID Bypass Logic (`void_bypass.py`)

Feature flag:
- enabled by default (`NOVA_ENABLE_VOID_MODE=1`).

Bypass trigger function supports:
- direct `graph_state == "void"`,
- `bias_report.metadata.graph_state == "void"`.

Current hybrid API caller passes direct `graph_state` from request context.

Passthrough response constants:
- `final_policy = STANDARD_PROCESSING`
- `distortion_score = 0.0`
- `confidence = 1.0`
- `spectral_filter_disabled = True`
- `threat_level = 0.0`
- `risk_level = 0.0`
- `manipulation_score = 0.0`
- `extraction_score = 0.0`
- analysis includes `spectral_entropy = 0.0`, `equilibrium_ratio = None`.

Observability:
- increments `slot09_void_passthrough_total`.

## 5. ORP Sensitivity Scaling (`continuity/slot09_sensitivity.py`)

Used by `apply_orp_sensitivity_to_config` when `NOVA_ENABLE_SLOT09_SENSITIVITY=1`.

Multiplier table:
- normal: `1.0`
- heightened:
  - `<300s`: `1.05`
  - `>=300s`: `1.15`
- controlled_degradation: `1.30`
- emergency_stabilization: `1.50`
- recovery: `1.20`

Scaling formula:

```text
scaled_threshold = clamp(base_threshold * multiplier, base_threshold, 2*base_threshold)
```

Applied to:
- `ids_stability_threshold_low/medium/high`
- `ids_drift_threshold_low/medium/high`

Not applied to:
- threat response thresholds,
- resilience settings.

Any ORP-scaling exception falls back to unchanged base config.

## 6. Adapter Contract (`orchestrator/adapters/slot9_distortion_protection.py`)
- `detect(...)` returns:
  - API response dict on success,
  - `{"status":"unavailable"}` if engine unavailable,
  - `{"status":"error"}` on exception.

## 7. Slot09 Math in Practice
Slot09 combines:
- policy-first IDS gating,
- thresholded threat scoring,
- drift-attenuated confidence,
- ORP-driven IDS threshold desensitization,
- explicit VOID passthrough semantics,
- hash-chained audit trails (shared Blake2b or fallback SHA-256).

The slot is deterministic and threshold-based, with key risk/confidence values bounded in `[0,1]`.

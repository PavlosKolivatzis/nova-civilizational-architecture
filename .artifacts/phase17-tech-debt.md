# Phase 17: Technical Debt & Optimization Opportunities

**Phase**: Secret Scanning & Baseline Attestation
**Created**: 2025-11-15
**Status**: Deferred (no performance impact observed)

---

## Performance: Metrics Parse Latency

### Current Behavior

`orchestrator/prometheus_metrics.py:595-645` (`update_secrets_baseline_metrics()`) performs:
1. Read `.artifacts/secrets-baseline-attestation.json` (22 lines, ~500 bytes)
2. Read `.artifacts/secrets-audit.md` (14,437 lines, ~458 KB)
3. Regex parse for 5 risk levels: `rf'##.*{risk}.*\((\d+)\s+findings?\)'`

**Invocation frequency**: Every `/metrics` scrape (typically 15s interval = ~240/hour)

**Current latency**: Unknown (not measured)

**Acceptable threshold**: <100ms per invocation

### Why Deferred

- File size modest (458 KB)
- Scrape interval conservative (15s)
- No user-reported latency
- Premature optimization violates simplicity principle

### Trigger Conditions

Optimize when **any** of:
1. Measured latency >100ms (via reflex hook)
2. Scrape interval reduced <5s
3. Audit report grows >1 MB
4. CPU profiling shows >5% time in metrics parsing

---

## Optimization Options

### Option 1: Reflex Hook (Self-Diagnosing)

**Effort**: 10 lines
**File**: `orchestrator/prometheus_metrics.py:595`

```python
def update_secrets_baseline_metrics() -> None:
    """Update Phase 17 secret scanning metrics for Prometheus export."""
    import time
    from pathlib import Path
    import json
    from datetime import datetime

    start = time.perf_counter()

    try:
        # [existing logic...]

    finally:
        elapsed = time.perf_counter() - start
        if elapsed > 0.1:  # 100ms threshold
            logger.warning(
                f"Secrets baseline metrics parsing slow: {elapsed:.3f}s "
                f"(threshold: 0.1s) — consider caching optimization"
            )
            # Optional: emit nova_secrets_parse_latency_seconds gauge
```

**Benefit**: System self-reports when optimization becomes necessary
**Rollback**: Remove timing block
**Risk**: None (warning-only)

---

### Option 2: Attestation Schema Extension (Pre-Computed Counts)

**Effort**: 30 lines across 2 files
**Files**: `tools/attest_secrets_baseline.py`, `orchestrator/prometheus_metrics.py`

#### Change 1: Extend Attestation Schema

**File**: `tools/attest_secrets_baseline.py:138-164` (in `create_attestation()`)

```python
# After parsing baseline statistics, read risk counts from audit report
audit_path = Path('.artifacts/secrets-audit.md')
risk_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

if audit_path.exists():
    audit_content = audit_path.read_text()
    for risk in risk_counts.keys():
        match = re.search(rf'##.*{risk}.*\((\d+)\s+findings?\)', audit_content)
        if match:
            risk_counts[risk] = int(match.group(1))

# Add to attestation
attestation = {
    "kind": "SECRETS_BASELINE_ATTESTATION",
    "version": "1.1",  # Increment version
    "statistics": {
        "file_count": len(baseline_data.get("results", {})),
        "finding_count": sum(len(v) for v in baseline_data.get("results", {}).values()),
        "risk_counts": risk_counts,  # NEW: pre-computed counts
        "plugins": plugin_counts,
        "version": baseline_data.get("version", "unknown"),
    },
}
```

#### Change 2: Use Cached Counts in Metrics

**File**: `orchestrator/prometheus_metrics.py:628-645`

```python
# Load risk classification report if exists
risk_counts = attestation.get('statistics', {}).get('risk_counts')

if risk_counts:
    # Fast path: use pre-computed counts from attestation
    for risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
        secrets_baseline_findings_gauge.labels(risk_level=risk).set(
            risk_counts.get(risk, 0)
        )
else:
    # Fallback: parse report (backwards compatibility)
    report_path = Path('.artifacts/secrets-audit.md')
    if report_path.exists():
        report = report_path.read_text()
        for risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
            pattern = rf'##.*{risk}.*\((\d+)\s+findings?\)'
            match = re.search(pattern, report)
            if match:
                count = int(match.group(1))
                secrets_baseline_findings_gauge.labels(risk_level=risk).set(count)
            else:
                secrets_baseline_findings_gauge.labels(risk_level=risk).set(0)
```

**Benefit**:
- Single JSON parse (~500 bytes) vs. regex on 458 KB file
- Attestation v1.1 hash-links risk counts (provenance)
- Backwards compatible (fallback if `risk_counts` missing)

**Rollback**:
- Revert attestation to v1.0 schema
- Remove `risk_counts` key
- Metrics auto-fallback to regex path

**Risk**:
- Attestation hash changes (requires re-attest after schema update)
- Must regenerate attestation when switching

---

### Option 3: Feature Flag (Opt-In Optimization)

**Effort**: 15 lines
**File**: `orchestrator/prometheus_metrics.py:628-645`

```python
def update_secrets_baseline_metrics() -> None:
    """Update Phase 17 secret scanning metrics for Prometheus export."""
    from pathlib import Path
    import json
    import os
    from datetime import datetime

    use_cached = os.getenv("NOVA_SECRETS_METRICS_CACHE", "0") == "1"

    try:
        attestation_path = Path('.artifacts/secrets-baseline-attestation.json')
        if not attestation_path.exists():
            return

        attestation = json.loads(attestation_path.read_text())

        # [existing info + timestamp metrics...]

        # Risk counts: cached vs. parsed
        if use_cached and 'risk_counts' in attestation.get('statistics', {}):
            # Fast path: pre-computed counts
            risk_counts = attestation['statistics']['risk_counts']
            for risk in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']:
                secrets_baseline_findings_gauge.labels(risk_level=risk).set(
                    risk_counts.get(risk, 0)
                )
        else:
            # Slow path: parse report (current behavior)
            report_path = Path('.artifacts/secrets-audit.md')
            if report_path.exists():
                report = report_path.read_text()
                # [existing regex logic...]
```

**Usage**:
```bash
# Enable optimization
export NOVA_SECRETS_METRICS_CACHE=1

# Disable (default)
export NOVA_SECRETS_METRICS_CACHE=0
```

**Benefit**:
- Zero-downtime A/B testing
- Explicit opt-in (no surprise behavior changes)
- Easy rollback via environment variable

**Observability**:
Add metric to show which path active:
```python
secrets_cache_enabled_gauge = Gauge(
    "nova_secrets_metrics_cache_enabled",
    "Whether secrets metrics use cached counts (1) or parse report (0)",
    registry=_REGISTRY,
)
secrets_cache_enabled_gauge.set(1 if use_cached else 0)
```

**Rollback**: Set `NOVA_SECRETS_METRICS_CACHE=0` (or unset)

---

## Recommendation

### Immediate (Current Session)
**Action**: None — no performance issue observed.

**Evidence**: No latency warnings, scrape interval acceptable (15s).

### Phase 1 (Next Optimization Pass)
**Action**: Add reflex hook (Option 1)

**Trigger**: When revisiting metrics or performance tuning

**Effort**: 5 minutes

**Benefit**: System becomes self-diagnosing

### Phase 2 (If Reflex Hook Fires)
**Action**: Implement Option 2 (attestation v1.1) + Option 3 (feature flag)

**Sequence**:
1. Extend attestation schema with `risk_counts` (30 min)
2. Regenerate attestation: `python tools/attest_secrets_baseline.py create`
3. Add feature flag to metrics (15 min)
4. Test with flag enabled: `NOVA_SECRETS_METRICS_CACHE=1`
5. Monitor latency; compare cached vs. parsed
6. Enable by default if improvement >50ms

**Effort**: 1 hour total

**Rollback**: Unset flag; revert to attestation v1.0

---

## Comparison Matrix

| Option | Mechanism | Lines Changed | Latency Impact | Nova Property | Risk |
|--------|-----------|---------------|----------------|---------------|------|
| **Current** | Regex parse on scrape | 0 | Baseline | Sunlight (behavior visible) | None |
| **Reflex hook** | Emit warning @ 100ms | +10 | None (diagnostic only) | Observability | None |
| **Attestation v1.1** | Pre-compute in JSON | +30 | -90% (single parse) | Immutability (attested) | Schema change |
| **Feature flag** | Opt-in caching | +15 | Configurable | Reversibility | None |
| **Combined** | All three | +55 | -90% when enabled | All | Low (fallback safe) |

---

## Sunlight Compliance

- ✅ **Trade-off explicit**: Performance vs. simplicity documented
- ✅ **Threshold quantified**: 100ms latency, 5s scrape interval, 1MB file size
- ✅ **Self-diagnosing**: Reflex hook surfaces when optimization needed
- ✅ **Provenance preserved**: Attestation v1.1 hash-links risk counts
- ✅ **Reversible**: Feature flag allows instant rollback
- ✅ **Observable**: Metrics expose which code path active

---

## Related Files

- `orchestrator/prometheus_metrics.py:595-645` — Current implementation
- `tools/attest_secrets_baseline.py:138-164` — Attestation creation
- `.artifacts/secrets-baseline-attestation.json` — Current schema (v1.0)
- `.artifacts/secrets-audit.md` — 458 KB report parsed on every scrape

---

## Future Considerations

### Streaming Metrics (Architectural)

If secret findings grow >10K or scrape interval <1s, consider:
- **Event-driven updates**: Emit metrics only when attestation changes (not on every scrape)
- **Incremental parsing**: Stream-parse large reports instead of full read
- **Prometheus pushgateway**: Push metrics on attestation creation, not pull-based scrape

**Trigger**: Findings >10K or scrape interval <1s

**Effort**: 2-4 hours (architectural change)

### Baseline Scope Reduction

Current baseline includes `.venv/` (48 CRITICAL false positives).

**Option**: Exclude virtual environment from scans:
```bash
python -m detect_secrets scan --all-files \
  --exclude-files '\.venv/.*' \
  > .secrets.baseline
```

**Impact**:
- Reduces findings by ~48
- Requires re-scan + re-attest
- Changes attestation hash

**Trade-off**: Cleaner report vs. breaking existing hash reference

**Status**: Deferred (false positives documented, not blocking)

---

**Maintained by**: Phase 17 implementation
**Review cadence**: Quarterly or when trigger conditions met
**Last updated**: 2025-11-15

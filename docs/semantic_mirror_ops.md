# Semantic Mirror Operations Runbook

## Environment Configuration

### Staging Environment
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=true
export NOVA_SEMANTIC_MIRROR_SHADOW=true  # Collect metrics without affecting decisions
```

### Production Initial Deployment
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=false  # Feature disabled initially
export NOVA_SEMANTIC_MIRROR_SHADOW=true    # Shadow mode for delta tracking
```

### Production Full Deployment (after validation)
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=true
export NOVA_SEMANTIC_MIRROR_SHADOW=false   # Normal operation
```

## Key Metrics to Monitor

| Metric | Description | Normal Range |
|--------|-------------|--------------|
| `mirror_reads_total` | Total context queries | Increasing |
| `queries_successful` | Successful context retrievals | 60-95% of reads |
| `queries_access_denied` | ACL violations | <10% of reads |
| `queries_rate_limited` | Rate limit violations | <1% of reads |
| `entries_expired` | TTL cleanup count | Gradual increase |
| `active_contexts` | Live context entries | >0 when enabled |
| `publications_total` | Total context publications | Increasing |

## Performance Ratios

- **Hit Rate** = `queries_successful / mirror_reads_total`
- **Denial Rate** = `queries_access_denied / mirror_reads_total`  
- **Rate Limit Rate** = `queries_rate_limited / mirror_reads_total`

## Alert Thresholds (Starting Values)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Denial Rate | >10% sustained | **WARN** - Check ACL misconfigurations |
| Rate Limit Rate | >1% sustained | **WARN** - Investigate query patterns |
| Active Contexts | ==0 while enabled | **WARN** - Check context publishers |
| Hit Rate | <60% sustained | **WARN** - Review TTL settings or query patterns |

## Dashboard Commands

```bash
# One-time health check
python scripts/semantic_mirror_dashboard.py --once

# Continuous monitoring
python scripts/semantic_mirror_dashboard.py --watch --interval 2

# HTTP server for external monitoring
python scripts/semantic_mirror_dashboard.py --serve 8787

# CSV logging for historical analysis  
python scripts/semantic_mirror_dashboard.py --csv mirror_metrics.csv --watch

# Compact one-line output for automation
python scripts/semantic_mirror_dashboard.py --compact --once
```

## Troubleshooting

### High Denial Rate
1. Check ACL configuration: `docs/semantic_mirror_acl.md`
2. Verify context key naming follows `slot_name.context_type` pattern
3. Review access logs for unauthorized access attempts

### Zero Active Contexts
1. Verify `NOVA_SEMANTIC_MIRROR_ENABLED=true`
2. Check Slot 7 context publisher is running
3. Review publisher logs for publication failures

### High Rate Limiting
1. Check for runaway query loops in consuming slots
2. Review query patterns in application logs
3. Consider increasing rate limit if legitimate high volume

### Low Hit Rate
1. Review TTL settings (too short causes frequent expiration)
2. Check for queries to non-existent context keys
3. Verify publishers are actively publishing expected contexts

## Emergency Actions

### Disable Feature Immediately
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=false
# Restart affected services
```

### Reset Mirror State (Development Only)
```python
from orchestrator.semantic_mirror import reset_semantic_mirror
reset_semantic_mirror()  # Clears all contexts and metrics
```
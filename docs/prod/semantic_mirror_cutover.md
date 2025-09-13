# Semantic Mirror Production Cutover Runbook

## Deployment Modes & Environment Flags

### Staging Environment
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=true
export NOVA_SEMANTIC_MIRROR_SHADOW=true
```

### Production Day 0-1 (Shadow Soak)
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=false
export NOVA_SEMANTIC_MIRROR_SHADOW=true
```

### Production Live (After KPI Validation)
```bash
export NOVA_SEMANTIC_MIRROR_ENABLED=true
export NOVA_SEMANTIC_MIRROR_SHADOW=false
```

## Key Performance Indicators & Targets

| KPI | Target | Alert Threshold |
|-----|--------|----------------|
| Hit Rate | ≥ 85% | < 60% (warn) |
| Denial Rate | ≤ 5% | > 10% (warn) |
| Rate Limit Rate | ≈ 0% | > 1% (warn) |
| Active Contexts | > 0 when enabled | == 0 && ENABLED=true (warn) |

## Cutover Steps

### Phase 1: Shadow Soak (Day 0-1)
```bash
# 1. Deploy with shadow mode
python scripts/semantic_mirror_flip.py --disable --shadow

# 2. Monitor continuously
python scripts/semantic_mirror_dashboard.py --watch --interval 5

# 3. Collect baseline metrics
python scripts/semantic_mirror_dashboard.py --csv baseline_metrics.csv --watch

# 4. Verify compact output shows shadow metrics
python scripts/semantic_mirror_dashboard.py --compact --once
```

### Phase 2: Go Live (After 2 Green KPI Cycles)
```bash
# 1. Flip to live mode
python scripts/semantic_mirror_flip.py --enable --no-shadow

# 2. Immediate health check
python scripts/semantic_mirror_dashboard.py --compact --once

# 3. Monitor for first 15 minutes
python scripts/semantic_mirror_dashboard.py --watch --interval 10

# 4. Serve dashboard for team monitoring
python scripts/semantic_mirror_dashboard.py --serve 8787 --watch
```

## Rollback Plan

### Single-Step Rollback
```bash
# Immediately disable feature, keep shadow metrics
python scripts/semantic_mirror_flip.py --disable --shadow

# Verify return to baseline
python scripts/semantic_mirror_dashboard.py --compact --once
# Expected: status=healthy, minimal activity
```

### Verification Commands
```bash
# Confirm environment variables
cat .env.semantic_mirror

# Check dashboard shows disabled state
python scripts/semantic_mirror_dashboard.py --once | grep "Feature Enabled: No"

# Run regression tests
python scripts/semantic_mirror_quick_asserts.py
```

## Troubleshooting

| Symptom | Likely Cause | Confirm Command | Action |
|---------|--------------|-----------------|--------|
| denial_rate > 10% | ACL misconfiguration | `python scripts/semantic_mirror_dashboard.py --once` | Review ACL docs, check context keys |
| active_contexts == 0 | Publisher not running | `grep "context_published" logs/` | Restart Slot 7 context publisher |
| hit_rate < 60% | TTL too short | `python scripts/semantic_mirror_dashboard.py --compact --once` | Increase context TTL settings |
| rate_limit_rate > 1% | Query loops | `grep "rate_limited" logs/` | Check consuming slots for runaway queries |
| status=error | Import failures | `python scripts/semantic_mirror_quick_asserts.py` | Verify module imports and dependencies |

## Alert Configuration

### Prometheus/Grafana Queries
```yaml
# Hit rate below threshold
(semantic_mirror_queries_successful / semantic_mirror_reads_total) < 0.60

# Denial rate above threshold  
(semantic_mirror_queries_access_denied / semantic_mirror_reads_total) > 0.10

# Rate limiting active
semantic_mirror_queries_rate_limited > 0

# No active contexts when enabled
semantic_mirror_active_contexts == 0 and semantic_mirror_enabled == 1
```

### Dashboard Integration
```bash
# HTTP endpoint for external monitoring
curl http://localhost:8787/health | jq '.metrics'

# CSV export for log aggregation
python scripts/semantic_mirror_dashboard.py --csv /var/log/mirror_metrics.csv --once
```

## Pre-Cutover Checklist

- [ ] Shadow mode metrics collection active (≥24h)
- [ ] Dashboard accessible and showing healthy metrics
- [ ] ACL configuration reviewed and documented
- [ ] Rollback commands tested in staging
- [ ] Alert thresholds configured
- [ ] Team trained on troubleshooting procedures

## Post-Cutover Validation

### Immediate (0-15 minutes)
```bash
# Compact status every 30 seconds for first 5 minutes
for i in {1..10}; do python scripts/semantic_mirror_dashboard.py --compact --once; sleep 30; done

# Full dashboard snapshot
python scripts/semantic_mirror_dashboard.py --once > cutover_snapshot.txt
```

### Short-term (15 minutes - 2 hours)
```bash
# Continuous monitoring with CSV logging
python scripts/semantic_mirror_dashboard.py --csv cutover_metrics.csv --watch --interval 60
```

### Long-term (2+ hours)
```bash
# Daily health checks
python scripts/semantic_mirror_dashboard.py --csv daily_metrics.csv --once

# Weekly regression validation
python scripts/semantic_mirror_quick_asserts.py
```

## Success Criteria

- KPIs within target ranges for 2 consecutive monitoring cycles
- No critical alerts triggered
- Context-aware adaptations visible in Slot 6 behavior
- Shadow delta counter showing non-zero context influence
- Zero production incidents attributed to Semantic Mirror

## How to Verify

### Shadow Soak Monitoring
```bash
python scripts/semantic_mirror_dashboard.py --watch --interval 5
```

### Live Cutover
```bash
python scripts/semantic_mirror_flip.py --enable --no-shadow
python scripts/semantic_mirror_dashboard.py --compact --once
```

### CI Gate Testing
Include `.ci/snippets/semantic_mirror_kpi_gate.yml` in workflow and confirm failing thresholds cause job failure.

### Regression Sentinels
```bash
python scripts/semantic_mirror_quick_asserts.py
# Expected: All "OK:" lines, exit code 0
```
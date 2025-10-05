# NOVA System SLOs (Service Level Objectives)

## Slot 6 Cultural Synthesis SLOs

### Decision Quality SLOs
- **Residual Risk P99**: ≤ 0.7 (70th percentile)
- **Principle Preservation P95**: ≥ 0.4 (95th percentile) 
- **Decision Latency P95**: ≤ 100ms

### Safety SLOs  
- **False Approval Rate**: ≤ 0.1% (never approve high-risk content)
- **Blocked Rate Anomaly**: Alert if >20% decisions blocked in 1hr window
- **Legacy Usage**: Target 0 calls/day by next major release

### Availability SLOs
- **Health Endpoint**: 99.9% uptime
- **Synthesis Engine**: 99.95% success rate
- **Contract Compliance**: 100% (zero schema violations)

## Alert Thresholds

```yaml
slot6_alerts:
  residual_risk_p99:
    threshold: 0.75
    window: "5m"
    severity: "warning"
  
  blocked_rate_anomaly:
    threshold: 0.25  # 25% blocked rate
    window: "1h"
    severity: "critical"
  
  legacy_usage_spike:
    threshold: 10  # calls per hour
    window: "1h" 
    severity: "info"
  
  contract_violation:
    threshold: 1  # any violation
    window: "1m"
    severity: "critical"
```

## Monitoring Queries

### Prometheus/Grafana
```promql
# Residual risk P99
histogram_quantile(0.99, slot6_residual_risk_bucket)

# Blocked rate
rate(slot6_decisions{result="blocked"}[5m]) / rate(slot6_decisions_total[5m])

# Legacy usage trend  
rate(slot6_legacy_calls_total[1h])
```

### Health Check Integration
```bash
# SLO compliance check
curl /health/config | jq '.slot6 | {
  "decisions_total": .decisions_total,
  "legacy_calls": .legacy_calls_total, 
  "last_decision": .last_decision.residual_risk
}'
```

## Runbook References
See `ops/runbooks/README.md` for available runbooks.

Planned runbooks (not yet created):
- Blocked Deployment Remediation
- Legacy Gate Remediation
- Contract Violation Response

For immediate assistance, consult `/metrics` endpoint and `agents/nova_ai_operating_framework.md`.
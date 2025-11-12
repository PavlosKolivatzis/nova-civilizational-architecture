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

## Adaptive Wisdom Governor SLOs

Phase 15 introduced the Adaptive Wisdom Governor with Prometheus gauges exported via `nova_wisdom_*`.

### Stability & Generativity Targets
- **Stability Margin (`nova_wisdom_stability_margin`)**: ≥ 0.05 (p95), alert at < 0.03 for >5m
- **Hopf Distance (`nova_wisdom_hopf_distance`)**: ≥ 0.02; values < 0.02 trigger freeze protocol
- **Generativity (`nova_wisdom_generativity`)**: ≥ 0.65 (p90) with rolling window of 10m
- **Learning Rate Adjustments (`nova_wisdom_eta_current`)**: ≤ 4 major clamps per hour (alert if `rate(nova_wisdom_eta_current[1h]) > 0.06`)

### Monitoring Queries
```promql
# Stability trend
nova_wisdom_stability_margin

# Hopf risk
nova_wisdom_hopf_distance < 0.02

# Generativity health
histogram_quantile(0.9, nova_wisdom_generativity_bucket)
```

### Runbook Hook
- When any governor SLO degrades, follow [`ops/runbook/wisdom-governor-stability.md`](../ops/runbook/wisdom-governor-stability.md) before resuming Slot10 deployments.

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
- Slot 6 residual risk spikes: [`ops/runbook/slot6-residual-risk.md`](../ops/runbook/slot6-residual-risk.md)
- Adaptive Wisdom Governor stability: [`ops/runbook/wisdom-governor-stability.md`](../ops/runbook/wisdom-governor-stability.md)
- Federation / ledger continuity: [`ops/runbook/continuity-engine.md`](../ops/runbook/continuity-engine.md)

For immediate assistance, consult `/metrics`, `/health`, and `agents/nova_ai_operating_framework.md`.

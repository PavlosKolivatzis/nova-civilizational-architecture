# Belief State Daily Operations Checklist

## Morning Health Check (Daily)

### 1. Variance Levels
- [ ] Check `nova_slot_phase_lock_belief_variance{slot="4"}` < 0.20
- [ ] Check `nova_slot_phase_lock_belief_variance{slot="7"}` < 0.20
- [ ] If variance > 0.20 sustained > 5 min: Investigate mirror health

### 2. Mean Stability
- [ ] Verify `nova_slot_phase_lock_belief_mean{slot="4|7"}` between 0.3-0.7
- [ ] Alert if |mean - 0.5| > 0.45 for > 10 min: Check TRI inputs

### 3. Update Freshness
- [ ] Confirm belief updates within last 10 minutes
- [ ] Check `belief_stale_seconds{slot="4|7"}` < 600

### 4. Publication Status
- [ ] Verify belief publications are active (check mirror logs)
- [ ] Confirm no publication errors in application logs

## Incident Response

### High Variance Alert (> 0.20 sustained)
1. **Check Mirror Health:**
   ```bash
   curl -s http://localhost:9090/metrics | grep semantic_mirror
   ```
2. **Verify TRI Inputs:**
   ```bash
   curl -s http://localhost:8000/health/slot04 | jq '.tri_score'
   ```
3. **Check Transport Latency:**
   ```bash
   # Monitor network latency between slots
   ```

### Stale Belief States (> 10 min)
1. **Restart Slot 04 TRI Engine**
2. **Check Slot 07 Production Controls**
3. **Verify Mirror Connectivity**

### Extreme Mean Drift
1. **Audit Recent TRI Observations:**
   ```bash
   tail -n 50 run/belief_ledger.ndjson | jq '.slot04_belief'
   ```
2. **Check for Data Bias in TRI Features**
3. **Validate Bayesian Update Logic**

## Weekly Maintenance

### 1. Variance Trend Analysis
- [ ] Review 7-day variance trends
- [ ] Identify patterns (time-of-day, load-related)
- [ ] Adjust operational thresholds if needed

### 2. Belief Convergence Testing
- [ ] Run convergence tests in staging
- [ ] Verify outage simulation behavior
- [ ] Update thresholds based on observed patterns

### 3. Documentation Updates
- [ ] Update runbook with new patterns observed
- [ ] Review alert thresholds for effectiveness

## Emergency Procedures

### Complete Belief System Failure
```bash
# Immediate rollback
export NOVA_ENABLE_PROBABILISTIC_CONTRACTS=0
# Restart all slot services
systemctl restart nova-slot04
systemctl restart nova-slot07
systemctl restart nova-orchestrator
```

### Mirror Outage Response
1. Belief variance will grow monotonically (expected)
2. Means remain stable (expected)
3. Production controls may enter soft throttle mode
4. Monitor for recovery when mirror connectivity restored

## Key Metrics to Monitor

| Metric | Normal Range | Warning | Critical | Action |
|--------|-------------|---------|----------|--------|
| belief_variance{slot="4"} | < 0.15 | 0.15-0.20 | > 0.20 | Investigate TRI stability |
| belief_variance{slot="7"} | < 0.15 | 0.15-0.20 | > 0.20 | Check production load |
| belief_stale_seconds | < 300 | 300-600 | > 600 | Restart affected slot |
| belief_mean_drift | < 0.3 | 0.3-0.45 | > 0.45 | Audit TRI inputs |

## Log Patterns to Watch

### Normal Operation
```
INFO - Belief updated: mean=0.52, variance=0.08, confidence=0.92
INFO - Production controls: normal operation (variance=0.12)
```

### Warning Signs
```
WARN - High variance detected: slot=4, variance=0.23
WARN - Belief stale: slot=7, seconds=420
```

### Critical Issues
```
ERROR - Belief publication failed: mirror unavailable
CRIT - Circuit breaker tripped due to uncertainty (variance=0.28)
```

## Contact Information

- **Primary:** Nova Operations Team
- **Secondary:** TRI Engine Maintainers
- **Tertiary:** Production Controls Team

## References

- **Engineering Note:** `docs/engineering-notes/v6.0-probabilistic-belief-propagation.md`
- **Contract Schema:** `contracts/slot04-07-belief-state.yaml`
- **Release Notes:** `docs/releases/v6.0-belief-propagation.md`
- **Attestation:** `attest/2025-10-phase-6.0-belief-propagation.json`

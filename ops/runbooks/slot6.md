# Slot6 Cultural Synthesis Runbook

## Residual Risk Alerts

### Warning: p95 > 0.85
**Symptom:** Cultural synthesis decisions showing elevated residual risk
**Impact:** Potential degradation in content quality/safety
**Urgency:** Non-urgent, investigate within 1 hour

#### Investigation Steps
1. **Check recent deployments:**
   ```bash
   # Review recent commits affecting Slot6
   git log --oneline --grep="slot6" --since="24 hours ago"
   ```

2. **Verify metrics health:**
   ```bash
   # Check /metrics endpoint
   curl http://nova:8000/metrics | grep nova_slot6_p95_residual_risk

   # Confirm decision activity (should have recent samples)
   curl -s http://nova:8000/metrics | grep -A5 -B5 "slot6_p95"
   ```

3. **Review Grafana dashboard:**
   - Open "NOVA • Phase 2 Observability"
   - Check "Slot6 p95 Residual Risk (Timeseries)" for trend
   - Look for correlation with feature flag changes

#### Common Causes
- **Content distribution shift** - new input patterns exceeding thresholds
- **ΔThresh misconfiguration** - Slot2 thresholds too permissive
- **TRI engine changes** - if NOVA_ENABLE_TRI_LINK recently enabled
- **Window edge effects** - p95 calculation during sparse decision periods

#### Mitigation
- **Low risk:** Monitor for 30m, may self-resolve
- **Sustained elevation:** Consider raising Slot2 ΔThresh sensitivity temporarily
- **Content review:** Check recent decisions via Slot7 audit logs

---

### Critical: p95 > 0.93
**Symptom:** Cultural synthesis showing high residual risk
**Impact:** Content safety/quality at risk
**Urgency:** Immediate response required

#### Immediate Actions
1. **Throttle traffic temporarily** (if applicable):
   ```bash
   # Example: reduce upstream load balancer weights
   # Specific implementation depends on your deployment
   ```

2. **Enable stricter filtering:**
   ```bash
   # If available, enable more conservative Slot3 policies
   export NOVA_ENABLE_STRICT_FILTERING=1
   # Restart relevant services
   ```

3. **Review decision audit:**
   ```bash
   # Check Slot7 metrics for recent decision patterns
   curl -s http://nova:8000/health | jq '.slot7.recent_decisions'
   ```

#### Root Cause Analysis
- **Decision volume spike** - check input rate vs normal baseline
- **Model drift** - correlation with recent ML model updates
- **Feature flag interactions** - cross-reference with flag timeline
- **Infrastructure issues** - check resource constraints (CPU/memory)

#### Recovery
- **Monitor p95 trend** - should decrease within 15-20 minutes of mitigation
- **Gradual traffic restoration** - increase load incrementally
- **Post-incident review** - capture samples for analysis

---

### Missing Metrics Alert
**Symptom:** `nova_slot6_p95_residual_risk` absent from scrape
**Impact:** No visibility into cultural synthesis health
**Urgency:** High - restore monitoring capability

#### Troubleshooting
1. **Check metrics endpoint:**
   ```bash
   curl -v http://nova:8000/metrics
   # Should return 200 with prometheus metrics, not 404
   ```

2. **Verify Prometheus gating:**
   ```bash
   # Confirm NOVA_ENABLE_PROMETHEUS is set
   curl -s http://nova:8000/health | jq '.environment' | grep PROMETHEUS
   ```

3. **Check Prometheus scrape:**
   ```promql
   # In Prometheus UI
   up{job="nova"}
   ```

4. **Review application logs:**
   ```bash
   # Look for errors in metrics export
   kubectl logs -l app=nova --tail=100 | grep -i prometheus
   ```

## References
- **Dashboard:** [NOVA • Phase 2 Observability](../dashboards/nova-phase2-observability.json)
- **Metrics endpoint:** `GET /metrics` (requires `NOVA_ENABLE_PROMETHEUS=1`)
- **Related runbooks:** [observability.md](observability.md)

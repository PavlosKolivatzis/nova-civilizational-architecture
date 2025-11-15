# NOVA Observability Runbook

## Prometheus Metrics Missing

### NovaMetricsMissing Alert
**Symptom:** `absent(nova_slot6_p95_residual_risk{slot="6"})` firing
**Impact:** No visibility into NOVA system health
**Urgency:** Critical - restore monitoring immediately

#### Investigation Checklist

1. **Application Health**
   ```bash
   # Check if NOVA service is running
   kubectl get pods -l app=nova
   # or for direct deployment:
   curl -f http://nova:8000/health
   ```

2. **Metrics Endpoint Gating**
   ```bash
   # Verify NOVA_ENABLE_PROMETHEUS flag
   curl -v http://nova:8000/metrics

   # Expected responses:
   # ✅ 200 + prometheus metrics → correctly enabled
   # ❌ 404 → NOVA_ENABLE_PROMETHEUS not set or falsy
   # ❌ 5xx → application error
   ```

3. **Environment Variable Check**
   ```bash
   # Confirm flag is truthy in runtime environment
   kubectl exec deployment/nova -- env | grep NOVA_ENABLE_PROMETHEUS
   # Should show: NOVA_ENABLE_PROMETHEUS=1 (or true/yes/on)
   ```

4. **Prometheus Scrape Configuration**
   ```yaml
   # In prometheus.yml, confirm job exists:
   scrape_configs:
     - job_name: nova
       metrics_path: /metrics
       scheme: http
       static_configs:
         - targets: ['nova:8000']
   ```

5. **Prometheus Target Status**
   ```bash
   # Check Prometheus UI → Status → Targets
   # Look for job "nova" - should show "UP"
   # If DOWN, check network connectivity and service discovery
   ```

#### Common Fixes

**Case 1: 404 Response**
- **Root cause:** `NOVA_ENABLE_PROMETHEUS` not set or disabled
- **Fix:** Set environment variable and restart service
  ```bash
  export NOVA_ENABLE_PROMETHEUS=1
  # Restart NOVA service
  ```

**Case 2: Network Connectivity**
- **Root cause:** Prometheus cannot reach NOVA service
- **Fix:** Check service networking, DNS resolution, firewall rules
  ```bash
  # From Prometheus pod/host:
  curl -v http://nova:8000/metrics
  nslookup nova
  ```

**Case 3: Service Down**
- **Root cause:** NOVA application crashed or not running
- **Fix:** Restart service, check application logs for errors
  ```bash
  kubectl logs deployment/nova --tail=50
  kubectl rollout restart deployment/nova
  ```

---

## Feature Flag Drift Alerts

### NovaFlagUnexpected_* Alerts
**Symptom:** Observed feature flag state != expected state
**Impact:** Potential configuration drift or unintended deployment
**Urgency:** Info - verify deployment intent

#### Investigation Steps

1. **Check Current Flag States**
   ```bash
   # Query Prometheus for current values
   curl -s 'http://prometheus:9090/api/v1/query?query=nova_feature_flag_enabled' | jq .

   # Or via Grafana dashboard "Feature Flag States"
   ```

2. **Review Expected Configuration**
   ```yaml
   # In ops/alerts/nova-phase2.rules.yml
   # Look for nova:expected_flags record with labels:
   NOVA_ENABLE_TRI_LINK: "0"      # Expected: disabled
   NOVA_ENABLE_LIFESPAN: "0"      # Expected: disabled
   NOVA_USE_SHARED_HASH: "1"      # Expected: enabled
   NOVA_ENABLE_PROMETHEUS: "1"    # Expected: enabled
   ```

3. **Verify Deployment Intent**
   ```bash
   # Check recent deployments/config changes
   git log --oneline --grep="flag\|feature" --since="24 hours ago"

   # Review deployment pipeline or GitOps config
   kubectl get configmap nova-config -o yaml
   ```

#### Resolution Options

**Case 1: Intentional Change**
- **Action:** Update expected values in `nova:expected_flags` record
- **File:** `ops/alerts/nova-phase2.rules.yml`
- **Deploy:** Reload Prometheus rules

**Case 2: Configuration Drift**
- **Action:** Correct the environment variable to match expected state
- **Verification:** Confirm flag metrics return to expected values within 1-2 minutes

**Case 3: Deployment Rollback Needed**
- **Action:** Revert to previous known-good configuration
- **Monitor:** Ensure flags return to expected baseline

---

## Dashboard Troubleshooting

### Grafana "NOVA • Phase 2 Observability" Issues

**No Data in Panels:**
1. **Check Prometheus datasource** - verify connection in Grafana
2. **Confirm metrics availability** - query Prometheus directly
3. **Review time range** - ensure within metric retention period

**Flag Panels Show "N/A":**
1. **Metrics endpoint** - confirm `/metrics` returns flag gauges
2. **Scrape timing** - may take 30-60s for first scrape
3. **Template variables** - check DS_PROMETHEUS datasource selection

**p95 Panel Empty:**
1. **Decision activity** - Slot6 needs recorded decisions for percentiles
2. **Metrics window** - newly started systems may have empty p95
3. **Slot6 availability** - verify Slot6 adapter is processing requests

## Quick Commands

```bash
# Full health check pipeline
curl -f http://nova:8000/health && \
curl -f http://nova:8000/metrics | grep -E "(nova_feature_flag|nova_slot6)" && \
echo "✅ NOVA observability healthy"

# Reset metrics (if supported)
curl -X POST http://nova:8000/admin/reset-metrics

# Prometheus rule validation
promtool check rules ops/alerts/nova-phase2.rules.yml
```

## References
- **Metrics endpoint:** `GET /metrics` (gated by `NOVA_ENABLE_PROMETHEUS`)
- **Health endpoint:** `GET /health` (always available)
- **Alert rules:** [nova-phase2.rules.yml](../alerts/nova-phase2.rules.yml)
- **Dashboard:** [nova-phase2-observability.json](../dashboards/nova-phase2-observability.json)

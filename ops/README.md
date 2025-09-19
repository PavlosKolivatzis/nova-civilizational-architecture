# NOVA Operations

Complete observability and alerting infrastructure for NOVA Phase 2 feature flags and Slot6 cultural synthesis monitoring.

## Quick Start

### 1. Enable Prometheus Export
```bash
export NOVA_ENABLE_PROMETHEUS=1
# Restart NOVA service
curl http://nova:8000/metrics  # Should return metrics
```

### 2. Configure Prometheus
Add to `prometheus.yml`:
```yaml
# Scrape NOVA metrics
scrape_configs:
  - job_name: nova
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets: ['nova:8000']

# Load alert rules
rule_files:
  - ops/alerts/nova-phase2.rules.yml
```

### 3. Import Grafana Dashboard
1. Grafana → Dashboards → New → Import
2. Upload `dashboards/nova-phase2-observability.json`
3. Select Prometheus datasource

### 4. Configure Alertmanager (Optional)
Example minimal config:
```yaml
route:
  receiver: default
  group_by: ['alertname','service']
receivers:
  - name: default
    slack_configs:
      - send_resolved: true
        channel: "#nova-alerts"
        text: |
          *{{ .CommonLabels.severity | toUpper }}* {{ .CommonAnnotations.summary }}
          {{ .CommonAnnotations.description }}
```

## Directory Structure

```
ops/
├── alerts/              # Prometheus alerting rules
│   └── nova-phase2.rules.yml
├── dashboards/          # Grafana dashboard definitions
│   ├── nova-phase2-observability.json
│   └── README.md
├── runbooks/           # Incident response procedures
│   ├── slot6.md        # Slot6 residual risk alerts
│   └── observability.md # Metrics/monitoring issues
└── README.md          # This file
```

## Available Metrics

### Feature Flags
- `nova_feature_flag_enabled{flag="NOVA_ENABLE_TRI_LINK"}` - TRI↔Constellation link state
- `nova_feature_flag_enabled{flag="NOVA_ENABLE_LIFESPAN"}` - Lifespan manager state
- `nova_feature_flag_enabled{flag="NOVA_USE_SHARED_HASH"}` - Shared hash algorithm state
- `nova_feature_flag_enabled{flag="NOVA_ENABLE_PROMETHEUS"}` - Metrics export state

### Slot6 Cultural Synthesis
- `nova_slot6_p95_residual_risk{slot="6"}` - 95th percentile residual risk from decisions

## Alert Conditions

### Critical
- **NovaSlot6ResidualRiskCritical** - p95 > 0.93 for 5m
- **NovaMetricsMissing** - Metrics absent for 10m

### Warning
- **NovaSlot6ResidualRiskWarning** - p95 > 0.85 for 5m

### Info
- **NovaFlagUnexpected_*** - Feature flag drift from expected state for 10m

## Validation Commands

```bash
# Validate Prometheus rules syntax
promtool check rules ops/alerts/nova-phase2.rules.yml

# Test metrics endpoint
curl http://nova:8000/metrics | grep -E "(nova_feature_flag|nova_slot6)"

# Check Prometheus targets
curl http://prometheus:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="nova")'
```

## Troubleshooting

**No metrics showing:**
- Verify `NOVA_ENABLE_PROMETHEUS=1`
- Check `/metrics` returns 200 (not 404)
- Confirm Prometheus scrape config

**Alerts not firing:**
- Validate rule syntax with `promtool check rules`
- Check Prometheus rules are loaded
- Verify Alertmanager routing configuration

**Dashboard empty:**
- Confirm Grafana Prometheus datasource connection
- Check metric retention period vs dashboard time range
- Verify metrics are being scraped (Prometheus UI → Status → Targets)

## References

- **Application endpoint:** `GET /metrics` (requires `NOVA_ENABLE_PROMETHEUS=1`)
- **Health check:** `GET /health` (always available)
- **Grafana dashboard:** Import `dashboards/nova-phase2-observability.json`
- **Alert rules:** Load `alerts/nova-phase2.rules.yml` in Prometheus
- **Incident response:** See `runbooks/` directory
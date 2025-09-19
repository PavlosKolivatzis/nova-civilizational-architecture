# NOVA Phase 2 Observability Dashboards

This directory contains ready-to-import Grafana dashboards for monitoring NOVA's Phase 2 feature flags and operational metrics.

## Quick Import

1. **Open Grafana** → Dashboards → New → Import
2. **Upload JSON file** or paste contents from this directory
3. **Select Prometheus datasource** when prompted
4. **Save** - dashboard will auto-refresh every 30 seconds

## Available Dashboards

### `nova-phase2-observability.json`
**Real-time Phase 2 system status at a glance**

**Panels:**
- **Feature Flag States** (4 stat panels) - instant green/red status for each Phase 2 flag
- **Slot6 p95 Risk Gauge** - cultural synthesis residual risk with thresholds (green < 0.85, orange < 0.93, red)
- **Slot6 p95 Timeseries** - trend analysis over time
- **Flag Change Timeline** - deployment verification and audit trail

**Variables:**
- `DS_PROMETHEUS` - select your Prometheus datasource
- `window` - smoothing window (1m, 5m, 15m, 1h) for max_over_time queries

**Prerequisites:**
- Prometheus datasource configured in Grafana
- `NOVA_ENABLE_PROMETHEUS=1` on target NOVA instance
- Metrics available at `/metrics` endpoint

## Setting Up Alerts

### Option 1: Grafana Alerts
1. **Edit** "Slot6 p95 Residual Risk (Gauge)" panel
2. **Alert** tab → Create Alert
3. **Conditions:**
   - Warning: `WHEN last() OF query(A) IS ABOVE 0.85 FOR 5m`
   - Critical: `WHEN last() OF query(A) IS ABOVE 0.93 FOR 10m`

### Option 2: Prometheus Rules
See parent directory for `prometheus.yml` and `nova.rules.yml` examples.

## Troubleshooting

**No data showing:**
- Verify `NOVA_ENABLE_PROMETHEUS=1` in target environment
- Check `/metrics` endpoint returns data: `curl http://your-nova:8000/metrics`
- Confirm Prometheus is scraping: check Targets page

**Flag panels showing "N/A":**
- Ensure feature flag gauges are exported: look for `nova_feature_flag_enabled` in `/metrics`
- Check that Slot7 adapter is available and processing flag states

**p95 panel empty:**
- Slot6 needs recorded decisions to calculate percentiles
- Window may be empty if system just started - wait for decision activity
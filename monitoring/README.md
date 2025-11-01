# Nova Monitoring Stack

## Quick Start

1. **Start Nova API Server** (single worker for correct counters):
   ```bash
   cd /c/code/nova-civilizational-architecture
   FEDERATION_ENABLED=1 NOVA_ENABLE_PROMETHEUS=1 python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1
   ```

2. **Start Monitoring Stack**:
   ```bash
   cd monitoring
   docker-compose up -d
   ```

3. **Access Services**:
   - **Nova API**: http://localhost:8000
   - **Nova Metrics**: http://localhost:8000/metrics
   - **Prometheus**: http://localhost:9090
   - **Grafana**: http://localhost:3000 (admin/nova123)

## Services

- **Prometheus**: Scrapes Nova metrics every 5 seconds
- **Grafana**: Pre-configured with Nova Phase 2 Observability dashboard
- **Nova API**: Running with Prometheus metrics enabled

## Key Metrics

- `nova_slot1_*`: Truth anchor metrics
- `nova_feature_flag_enabled`: Feature flag states
- `nova_system_pressure_level`: System pressure
- `nova_tri_coherence`: TRI signal coherence
- `nova_deployment_gate_open`: Deployment gate status
- `nova_unlearn_pulses_sent_total`: Unlearn pulse activity
- `nova_federation_peers`: Enabled peer count (Phase 15-3)
- `nova_federation_pull_result_total{status="success"}` / `{status="error"}`: Federation pull outcomes
- `nova_federation_peer_up{peer="..."}`: Per-peer liveness (1=seen in last poll)
- `nova_federation_pull_seconds`: Poll duration histogram
- `nova_federation_ready`: Readiness gauge (1 when peers > 0 on latest poll)
- `nova_federation_peer_last_seen{peer="..."}`: Timestamp of most recent successful interaction per peer

Tune federation polling with `NOVA_FED_SCRAPE_INTERVAL` (seconds between polls, default 15) and `NOVA_FED_SCRAPE_TIMEOUT` (per-request timeout, default 2s).

## Phase 15-3 Metrics Highlights

- Timestamp refactor: `nova_federation_last_result_timestamp{status="success"|"error"}` replaces the deprecated `nova_federation_last_success_timestamp` gauge and the manual `pull_result_created` metric.
- Histogram verification: `nova_federation_pull_seconds_*` is the canonical pull latency histogram; see the Phase 15-3 verification block in the merge notes.
- Alerting: Federation alert suite lives in `monitoring/alerts/federation.rules.yml` and is documented in `monitoring/production-setup.md`.
- Reference: Architectural decisions are captured in `docs/adr/ADR-15-Federation-Metrics.md` for historical trace and rollout guidance.
- Readiness gauge: `nova_federation_ready` exposes coarse health for /ready; pair with `nova_federation_peer_last_seen{peer="..."}` for per-peer recency.
- Promtool fixtures: `monitoring/alerts/federation.rules.test.yml` exercises stalled, error-burst, and peer-low scenarios (`promtool test rules ...`).
- Recording helpers: import `monitoring/recording/federation.recording.yml` if you want precomputed p95 and 5m aggregates.
- CI: see `.github/workflows/monitoring.yml` template (copy from docs) for automated `promtool check/test` coverage.

### Recommended PromQL Panels

* **p95 pull latency**
  ```promql
  histogram_quantile(0.95, sum by (le) (rate(nova_federation_pull_seconds_bucket[5m])))
  ```
* **Pull outcomes (5m window)**
  ```promql
  increase(nova_federation_pull_result_total{status="success"}[5m])
  increase(nova_federation_pull_result_total{status="error"}[5m])
  ```
* **Peer availability**
  ```promql
  avg_over_time(nova_federation_peers[10m])
  ```
* **Last successful pull (single stat)**
  ```promql
  nova_federation_last_result_timestamp{status="success"}
  ```
* **Federation readiness**
  ```promql
  nova_federation_ready
  ```
* **Peer freshness (minutes since last contact)**
  ```promql
  (time() - nova_federation_peer_last_seen) / 60
  ```

### Dashboard Snapshots

![Federation peers](../docs/images/phase15/federation-peers.png)
![Federation p95 latency](../docs/images/phase15/federation-p95.png)
![Federation success vs error](../docs/images/phase15/federation-success-error.png)
![Federation last success](../docs/images/phase15/federation-last-success.png)

## Rollback

Stop monitoring stack:
```bash
docker-compose down
```

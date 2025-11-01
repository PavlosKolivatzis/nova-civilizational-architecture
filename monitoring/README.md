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

Tune federation polling with `NOVA_FED_SCRAPE_INTERVAL` (seconds between polls, default 15) and `NOVA_FED_SCRAPE_TIMEOUT` (per-request timeout, default 2s).

## Rollback

Stop monitoring stack:
```bash
docker-compose down
```

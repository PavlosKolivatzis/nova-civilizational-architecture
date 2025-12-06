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
  - **Nova Ready**: http://localhost:8000/ready
  - **Federation Health**: http://localhost:8000/federation/health
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
- **Slot02 Bias Detection (Phase 14.3):**
  - `slot02_bias_collapse_score`: Collapse score histogram (C(B) distribution)
  - `slot02_bias_vector_{component}`: Individual bias vector gauges (b_local, b_global, b_risk, b_completion, b_structural, b_semantic, b_refusal)
  - `slot02_bias_reports_total{graph_state}`: Total bias reports by graph state (void, normal, unknown)
- `nova_federation_peers`: Enabled peer count (Phase 15-3)
- `nova_federation_pull_result_total{status="success"}` / `{status="error"}`: Federation pull outcomes
- `nova_federation_peer_up{peer="..."}`: Per-peer liveness (1=seen in last poll)
- `nova_federation_pull_seconds`: Poll duration histogram
- `nova_federation_ready`: Readiness gauge (1 when peers > 0 and last success < 120s)
- `nova_federation_peer_last_seen{peer="..."}`: Timestamp of most recent successful interaction per peer
- `nova_federation_peer_quality{peer="..."}`: Composite 0–1 peer quality (success, latency, freshness)
- `nova_federation_peer_last_p95_seconds{peer="..."}`: Rolling per-peer p95 fetch latency (seconds)
- `nova_federation_peer_success_rate{peer="..."}`: Rolling per-peer success rate (0–1)
- `nova_federation_remediation_events_total{reason="..."}`: Auto-remediation actions grouped by trigger reason (e.g. error_spike, readiness_zero, config_error)
- `nova_federation_backoff_seconds`: Current poll interval after adaptive back-off adjustments
- `nova_federation_remediation_last_action_timestamp`: Unix timestamp of the most recent remediation event

Tune federation polling with `NOVA_FED_SCRAPE_INTERVAL` (seconds between polls, default 15) and `NOVA_FED_SCRAPE_TIMEOUT` (per-request timeout, default 2s).

## Federation Endpoints

- `/ready` – JSON `{ "ready": true|false }` derived from `nova_federation_ready`. Use it for Kubernetes/Compose health checks.
- `/federation/health` – Rich peer telemetry backed by the readiness metrics.

```bash
curl -s http://localhost:8000/federation/health | jq .
```

Example:

```json
{
  "ready": true,
  "peers": [
    {"id": "node-a", "state": "up", "last_seen": 1762021194.89},
    {"id": "node-b", "state": "unknown", "last_seen": 0.0}
  ],
  "checkpoint": {"height": 55},
  "remediation": {
    "reason": "error_spike",
    "interval": 30.0,
    "timestamp": 1762021250,
    "context": {"delta_errors": 3}
  }
}
```

## Peer Quality Scoring

Peer quality combines recent success rate, latency, and freshness within a 20-sample rolling window:
```
q = w1*s + w2*lat_score + w3*fresh
lat_score = clamp(1 - p95 / L, 0, 1)
fresh = exp(-Δt / τ)
```

Defaults: w1=0.5 (success), w2=0.3 (latency), w3=0.2 (freshness), L=2s, τ=300s. Configure via `NOVA_FED_QUALITY_W1/2/3`, `NOVA_FED_QUALITY_LAT_CAP_SEC`, and `NOVA_FED_QUALITY_TAU_SEC`.
Optional readiness gating (leave blank to disable) uses `NOVA_FED_MIN_PEER_QUALITY` and `NOVA_FED_MIN_GOOD_PEERS`.

PromQL references:
```promql
# Worst peers by quality (last 10m)
topk(5, 1 - max_over_time(nova_federation_peer_quality[10m]))

# Insufficient good peers (gate at 0.6)
sum(max_over_time(nova_federation_peer_quality[5m]) >= 0.6)

# Latency watch
max_over_time(nova_federation_peer_last_p95_seconds[10m])

# Success rate trend
avg_over_time(nova_federation_peer_success_rate[15m])
```
Grafana: add a table/heatmap combining peer ID, quality, p95, and success rate to spot regressions quickly.

## Ledger Correlation (Phase 15-7)

Track alignment between federation checkpoint height and local ledger state:

**Metrics:**
- `nova_ledger_height` – Current ledger checkpoint height
- `nova_ledger_head_age_seconds` – Time since ledger head timestamp
- `nova_ledger_federation_gap` – Signed difference (federation height - ledger height)
- `nova_ledger_federation_gap_abs` – Absolute gap magnitude

**Configuration:**

Provide ledger status via HTTP or shell command (see `.env.example`):
```bash
# Option 1: HTTP endpoint returning {"height": int, "head_ts": unix_timestamp}
NOVA_LEDGER_STATUS_URL=http://localhost:8080/ledger/status

# Option 2: Shell command emitting same JSON
NOVA_LEDGER_STATUS_CMD='python -c "import json,time; print(json.dumps({\"height\": 100, \"head_ts\": time.time()}))"'
```

On error or missing config, metrics default to zero (non-fatal).

**Health JSON:**

`/federation/health` includes ledger snapshot:
```json
{
  "ready": true,
  "peers": [...],
  "checkpoint": {"height": 120},
  "ledger": {"height": 100, "head_age": 42.0, "gap": 20},
  "remediation": {...}
}
```

**PromQL Queries:**
```promql
# Current gap
nova_ledger_federation_gap

# Ledger head staleness
nova_ledger_head_age_seconds

# Gap magnitude over 5m
avg_over_time(nova_ledger_federation_gap_abs[5m])

# Divergence detection (gap > 10 for 5m)
abs(nova_ledger_federation_gap) > 10
```

**Alerts:**
- `NovaLedgerFederationDivergence` – Triggers when `abs(gap) > 10` for 5 minutes
- `NovaLedgerHeadStalled` – Triggers when head age exceeds 300s for 5 minutes

See `monitoring/alerts/ledger.rules.yml` and `monitoring/recording/ledger.recording.yml`.

## Auto-Remediation Hooks

### Sustained empty peers (no_peers)

```
increase(nova_federation_remediation_events_total{reason="no_peers"}[1h])
```

- Toggle with `NOVA_FEDERATION_AUTOREMEDIATE=0|1` (default `1`). When enabled, the poller applies exponential back-off after consecutive failures and restarts itself once per cooldown window (5 min by default).
- Key metrics:
  - `nova_federation_remediation_events_total{reason}` - action counts (e.g., `error_spike`, `readiness_zero`, `config_error` when no peers are configured).
  - `nova_federation_backoff_seconds` - current poll interval after back-off.
  - `nova_federation_remediation_last_action_timestamp` - Unix timestamp of the last automated action.
- `/federation/health` → `remediation` mirrors the latest action (reason, interval, timestamp, context) for dashboards and audit logs.

## Phase 15-3 Metrics Highlights

- Timestamp refactor: `nova_federation_last_result_timestamp{status="success"|"error"}` replaces the deprecated `nova_federation_last_success_timestamp` gauge and the manual `pull_result_created` metric.
- Histogram verification: `nova_federation_pull_seconds_*` is the canonical pull latency histogram; see the Phase 15-3 verification block in the merge notes.
- Alerting: Federation alert suite lives in `monitoring/alerts/federation.rules.yml` and is documented in `monitoring/production-setup.md`.
- Reference: Architectural decisions are captured in `docs/adr/ADR-15-Federation-Metrics.md` for historical trace and rollout guidance.
- Readiness gauge: `nova_federation_ready` exposes coarse health for /ready; pair with `nova_federation_peer_last_seen{peer="..."}` for per-peer recency.
- Endpoints: `/ready` reflects the readiness gauge; `/federation/health` returns peer status JSON for dashboards and probes.
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
  max(nova_federation_ready)
  ```
* **Readiness over time (5m rolling window)**
  ```promql
  avg_over_time(nova_federation_ready[5m])
  ```
* **Peer freshness (minutes since last contact)**
  ```promql
  (time() - nova_federation_peer_last_seen) / 60
  ```
* **Remediation events (1h window)**
  ```promql
  increase(nova_federation_remediation_events_total[1h])
  ```

### Dashboard Snapshots

![Federation peers](../docs/images/phase15/federation-peers.png)
![Federation p95 latency](../docs/images/phase15/federation-p95.png)
![Federation success vs error](../docs/images/phase15/federation-success-error.png)
![Federation last success](../docs/images/phase15/federation-last-success.png)

## Bias Detection Dashboard (Phase 14.3)

**Dashboard:** `monitoring/grafana/dashboards/slot02-bias-detection.json`

**Panels:**
- **Collapse Score Distribution** (heatmap) - C(B) distribution over time
- **Collapse Score Current** (gauge) - P50 collapse score with threshold zones
- **Collapse Score Percentiles** (timeseries) - P50, P95, P99 trends
- **Bias Vector Components** (bargauge) - Current values of all 7 components
- **Bias Vector Trends** (timeseries) - Key components over time
- **Bias Reports Total** (stat) - Reports per second
- **Graph State Distribution** (pie) - void vs normal vs unknown
- **Feature Flag Status** (stat) - NOVA_ENABLE_BIAS_DETECTION
- **Void Mode Status** (stat) - NOVA_ENABLE_VOID_MODE

**Thresholds:**
- **C < 0.3**: Nova-aware (green)
- **0.3 ≤ C < 0.5**: Transitional (yellow)
- **0.5 ≤ C < 0.7**: Factory mode (orange)
- **C ≥ 0.7**: Severe factory mode (red)

**PromQL Examples:**
```promql
# P95 collapse score
histogram_quantile(0.95, rate(slot02_bias_collapse_score_bucket[5m]))

# Bias vector component (b_structural)
slot02_bias_vector_b_structural

# Reports by graph state
sum by (graph_state)(rate(slot02_bias_reports_total[5m]))

# Void graph rate
rate(slot02_bias_reports_total{graph_state="void"}[5m]) / rate(slot02_bias_reports_total[5m])
```

**Note:** Metrics only emit when `NOVA_ENABLE_BIAS_DETECTION=1`. Feature is default-off (Phase 14.3).

## Rollback

Stop monitoring stack:
```bash
docker-compose down
```

# Nova Production Monitoring Setup

## ?? Complete Unlearn Pulse Observability

The Nova system now has **full observability** for the Reciprocal Contextual Unlearning system:

### Live Metrics
- **Nova API**: http://localhost:8000/metrics
- **Dashboard**: http://localhost:9090
- **Health Check**: http://localhost:8000/health

### Key Metrics
- `nova_unlearn_pulses_sent_total`: Total unlearn pulses delivered
- `nova_entries_expired_total`: Contexts expired from semantic mirror
- `nova_unlearn_pulse_to_slot_total{slot="..."}`: Per-slot pulse delivery
- `nova_deployment_gate_open`: Gate status (1=open, 0=closed)
- `nova_federation_peers`: Enabled peer count
- `nova_federation_checkpoint_height`: Last verified checkpoint height
- `nova_federation_pull_result_total{status="success"}` / `{status="error"}`: Federation pull outcomes
- `nova_federation_peer_up{peer="..."}`: Per-peer liveness (1=seen in last poll)

### Production Configuration

**Required Environment Variables:**
```bash
UVICORN_WORKERS=1              # Single worker (shared semantic mirror + counters)
FEDERATION_ENABLED=1           # Enable federation router + poller
NOVA_ENABLE_PROMETHEUS=1       # Enable metrics export
NOVA_FED_SCRAPE_INTERVAL=15    # Federation poll cadence (seconds)
NOVA_FED_SCRAPE_TIMEOUT=2.0    # Federation poll timeout (seconds)
NOVA_SMEEP_INTERVAL=15         # Sweeper interval (seconds)
NOVA_ALLOW_EXPIRE_TEST=0       # Disable test context seeding in prod
```

**Verification Commands:**
```bash
# Test pulse generation (dev only)
curl -X POST http://localhost:8000/ops/expire-now

# Check live pulse metrics
curl http://localhost:8000/metrics | grep unlearn

# Check federation poller metrics
curl http://localhost:8000/metrics | grep nova_federation_

# Readiness probe
curl -f http://localhost:8000/ready

# Federation peer health JSON
curl -s http://localhost:8000/federation/health | jq '.'

# Test accounting invariants
curl -s http://localhost:9090/api/query?query="sum(nova_unlearn_pulse_to_slot_total)-nova_unlearn_pulses_sent_total"
```

## ?? Alerts

### Unlearn Pulse Suite

Production-ready alerts in `nova-alerts.yml`:

1. **UnlearnMetricsMissing** (critical) - Metrics export failure
2. **UnlearnPulseAccounting** (critical) - Per-slot totals don't sum
3. **UnlearnPulseUnderflow** (critical) - More expirations than pulses
4. **UnlearnPulseSilence** (warning) - No pulses for 30 minutes
5. **DeploymentGateOpen** (info) - Gate open alert

**Alert Features:**
- ? Delta-based (no restart flapping)
- ? Missing series detection
- ? Runbook links
- ? Dashboard references

### Federation Metrics Suite (Phase 15-3)

Phase 15-3 adds production alerts at `monitoring/alerts/federation.rules.yml`:

| Alert | Condition | Severity | Purpose |
| --- | --- | --- | --- |
| `NovaFederationStalled` | `time() - nova_federation_last_result_timestamp{status="success"} > 120` for `2m` | warning | Detects missing successful pulls |
| `NovaFederationErrorBurst` | `increase(nova_federation_pull_result_total{status="error"}[5m]) > 5` | critical | Flags sustained pull failures |
| `NovaFederationPeersLow` | `avg_over_time(nova_federation_peers[10m]) < 1` for `10m` | warning | Ensures at least one peer is reachable |

Roll out instructions:

```bash
# Validate syntax
promtool check rules monitoring/alerts/federation.rules.yml

# Simulate alert behaviour (stalled, error burst, peers low)
promtool test rules monitoring/alerts/federation.rules.test.yml
```

> **Note:** Promtool tests are optional but recommended before promoting to staging; see ADR-15 for rationale.

### Recording Rules

Optional helper rules live in `monitoring/recording/federation.recording.yml`:

```bash
promtool check rules monitoring/recording/federation.recording.yml
```

Load the file into Prometheus for precomputed p95 latency and 5m success/error deltas.

### Grafana & PromQL References

Import `monitoring/grafana/dashboards/nova-phase15-federation.json` into the Phase-15 board. Recommended panels:

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
* **Readiness (single stat, success within 120s)**
  ```promql
  nova_federation_ready
  ```
* **Peer freshness (minutes since last contact)**
  ```promql
  (time() - nova_federation_peer_last_seen) / 60
  ```

Attach dashboard screenshots to release notes when the federation board is published (Phase 15-3-b deliverable).

## ?? Operations

**Normal Operation:**
- Background sweeper runs every 15 seconds
- Contexts expire -> unlearn pulses sent
- Immunity respected (no pulses to slot01/slot07)
- Metrics updated real-time

**Troubleshooting:**
- Check sweeper logs: `SemanticMirror sweeper tick: expired=N`
- Verify single worker: `ps aux | grep uvicorn`
- Test context creation: Use `/ops/expire-now` (dev only)

**Rollback:**
- Disable: `NOVA_ENABLE_PROMETHEUS=0`
- Stop sweeper: Restart without `NOVA_SMEEP_INTERVAL`
- Emergency: `NOVA_ALLOW_EXPIRE_TEST=0`

## ? Validation

The system successfully demonstrates:
1. **Context expiry** -> 1 expired entry
2. **Multi-recipient pulses** -> 2 pulses (key slot + publisher slot)
3. **Per-slot accounting** -> slot06:1, slot05:1
4. **Immunity enforcement** -> No slot01/slot07 recipients
5. **Live metrics** -> Real-time dashboard updates

**Unlearn pulse metabolism is fully observable! ??**

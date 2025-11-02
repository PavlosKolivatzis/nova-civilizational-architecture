## Phase 15-5 Post-Release Runbook — Federation Auto-Remediation

### Environment Flags
- `NOVA_FEDERATION_AUTOREMEDIATE=1` (default): enable remediation hooks.
- `NOVA_FED_SCRAPE_INTERVAL` / `NOVA_FED_SCRAPE_MAX_INTERVAL`: base and max poll intervals.

### Quick Verification (after deploy)
```bash
# Readiness probe (expect 200/ready true)
curl -si http://<host>:8000/ready

# Peer & remediation snapshot
curl -s http://<host>:8000/federation/health | jq .remediation

# Metrics spot-check
curl -s http://<host>:8000/metrics | rg '^nova_federation_remediation_events_total'
curl -s http://<host>:8000/metrics | rg '^nova_federation_backoff_seconds'
```

### PromQL (Grafana Explore)
- `increase(nova_federation_remediation_events_total[1h])`
- `avg_over_time(nova_federation_ready[10m])`
- `histogram_quantile(0.95, sum by (le) (rate(nova_federation_pull_seconds_bucket[5m])))`

### Troubleshooting
1. **Repeated actions**: check cooldown (`nova_federation_remediation_last_action_timestamp`) and log `"Federation auto-remediation triggered"` events.
2. **Disable temporarily**: set `NOVA_FEDERATION_AUTOREMEDIATE=0`, restart orchestrator, investigate alerts/manual recovery.
3. **Peer freshness**: review `(time() - nova_federation_peer_last_seen) / 60` for stale nodes before re-enabling hooks.

### Monitoring Checklist
- Enable hooks (`NOVA_FEDERATION_AUTOREMEDIATE=1`); default cooldown and thresholds are set in code, override via env only if necessary.
- Watch `increase(nova_federation_remediation_events_total[1h])` alongside readiness/error panels to confirm remediation aligns with failure patterns.


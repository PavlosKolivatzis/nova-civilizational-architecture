# Observability Completion Note — Phases 15-3 & 15-4

- **Date:** 2025-11-01
- **Author:** Project Maintainers (Nova Civilizational Architecture)
- **Context:** Closure of the Federation Observability and Readiness workstream (v15.3.x → v15.4).

## Summary
Phase 15 delivered full-stack federation observability: a guarded Prometheus registry (latency histogram, peer gauges, labeled timestamps, readiness flags), a resilient background poller with freshness checks, readiness and peer-health HTTP endpoints, alert fixtures, recording rules, Grafana assets, and runbook updates. The effort culminated with `/ready` and `/federation/health` probes, ensuring federation health is visible to operators and CI/CD pipelines.

Major highlights:
- **Metrics:** Dedicated federation registry exposing `nova_federation_pull_seconds_*`, `nova_federation_last_result_timestamp{status}`, `nova_federation_peer_last_seen{peer}`, `nova_federation_ready`, peers, and checkpoint height.
- **Poller:** Idempotent lifecycle with stale-peer resets and 120 s freshness rule; readiness drops immediately on errors.
- **Endpoints:** `GET /ready` for probes (200 `{ready: true}` vs 503 `{ready: false}`) and `GET /federation/health` for enriched peer telemetry (`{ready, peers[{id,state,last_seen}], checkpoint{height}}`).
- **Alerting & Recording:** Prometheus rules for stalled success, error bursts, and low peers; promtool fixtures/tests; recording rules for p95 latency and 5 m success/error deltas.
- **Docs & Dashboards:** Updated production setup, monitoring README, federation runbook, and ADR‑15; Grafana screenshots and PromQL snippets shipped with the release artifact.
- **Testing:** Full `pytest -q` (1263 pass / 4 skip / 1 warning), health lane (49 pass / 0 fail), targeted endpoint/poller suites, and `promtool check/test` validation.

Blocks mitigated during delivery:
- Ensuring readiness gauge initialization defaulted to 0 before first poll.
- Removing legacy `/federation/health` handler from the federation router to avoid route collisions.
- Eliminating duplicate gauge creation when tests cleared metrics state.

Tags: `v15.3.0` (metrics & poller), `v15.3.1` (alerts/docs/recording). Readiness endpoints merged on `main` post-15.3.1 for Phase 15-4 kickoff.

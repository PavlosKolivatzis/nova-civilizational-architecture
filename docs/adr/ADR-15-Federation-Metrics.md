# ADR-15: Federation Metrics Timestamp Refactor

## Status
Accepted – Phase 15-3 federation metrics integration (tag `v15.3.0-beta`).

## Context
- Phase 15-3 introduced a dedicated Prometheus registry for federation signals (`src/nova/federation/metrics.py`).
- The initial implementation exported both `nova_federation_last_success_timestamp` and `nova_federation_pull_result_created{status=...}`.
- Health lane (`pytest -q -m health`) verified the poller startup, but observability review flagged the redundant timestamp pair and missing alerts.

## Decision
1. Consolidate pull-completion timestamps into `nova_federation_last_result_timestamp{status="success"|"error"}` initialized in `src/nova/federation/metrics.py:37`.
2. Update the background poller to set the labeled gauge for each outcome (`orchestrator/federation_poller.py:92`), keeping counters accurate under single-worker Uvicorn.
3. Confirmed Prometheus export shows the histogram bucket spread (`nova_federation_pull_seconds_*`) alongside the labeled timestamps; health lane remains green (49 pass, expected Slot06 deprecation warning).

## Consequences
- Grafana Phase-15 board and alerting rules now reference the labeled gauge; legacy `last_success` consumers must migrate.
- Alert pack (`monitoring/alerts/federation.rules.yml`) triggers on stalled polls, error bursts, and peer drops using the new metric.
- Ensures continuity for Phase 15-3-b (alerts + docs finalize) while keeping the federation metrics registry singleton guarded.

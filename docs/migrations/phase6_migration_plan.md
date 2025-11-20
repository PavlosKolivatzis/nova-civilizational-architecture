# Phase 6 Migration Plan — Temporal Intelligence Layer

This plan captures the required steps, verification points, and rollback strategy for landing Phase-6 (temporal intelligence + multi-node consistency) in Nova.

## 1. Scope & Intent
- Promote the temporal subsystem (ledger + engine + routing/governance integration) to first-class status.
- Ensure deterministic routing honours temporal drift/variance/prediction signals before ANR executes.
- Provide governance with temporal-aware veto paths so systemic holds trigger when prediction diverges.
- Export canonical contract (`temporal_consistency@1`) across slot map + ontology to prepare for federation.

## 2. Temporal Engine & Ledger
- `orchestrator/temporal/engine.py` computes `temporal_drift`, `temporal_variance`, `prediction_error`, `convergence_score`, and `divergence_penalty` per snapshot.
- `orchestrator/temporal/ledger.py` acts as the append-only hash chain (monotonic timestamps enforced).
- Snapshots update both semantic mirror contexts (`temporal.snapshot`, `temporal.ledger_head`) and Prometheus gauges.
- Rollback strategy: reset temporal ledger (`scripts/temporal_reset.py` forthcoming) and disable NOVA temporal thresholds via env overrides if anomalies surface.

## 3. Threshold Manager Extensions
- Added `temporal_drift_threshold`, `temporal_variance_threshold`, `temporal_prediction_error_threshold`, and `min_temporal_coherence` to `ThresholdManager`.
- `.env.example` documents defaults so deployments can gate via env overrides.
- Router penalties obey variance / prediction thresholds, governance enforces drift + prediction failure gates.

## 4. Router Integration
- `EpistemicRouter` now executes `TemporalConstraintEngine` before ANR, merges temporal reasons into `ConstraintResult`, and surfaces penalties via `metadata`.
- Router publishes `temporal.router_modifiers` to the semantic mirror so Slot07/Slot10/governance can trace why penalties occurred.
- Migration safe-guard: if NOVA temporal env flags are unset, router still computes snapshots but thresholds fall back to defaults (no extra env wiring required).

## 5. Governance Alignment
- Governance engine reads temporal contexts from the mirror (fallbacks to computing if absent), includes router modifiers/ledger head in snapshots, and blocks on:
  - Low coherence
  - High drift
  - High prediction error (new Phase-6 rule)
- Ledger entries now capture temporal metadata alongside ethics/policy results for full-chain auditing.

## 6. Observability & Endpoints
- Endpoints: `/temporal/snapshot`, `/temporal/ledger`, `/temporal/debug`, `/metrics/temporal`, `/metrics/internal` all live and tested.
- Metrics: `nova_temporal_drift`, `nova_temporal_variance`, `nova_temporal_prediction_error`, `nova_temporal_convergence`, `nova_temporal_divergence`, `nova_temporal_router_state`, alongside threshold gauges exposed via the existing threshold helpers.
- Router/governance tests ensure penalties vs holds behave deterministically under drift/variance/prediction scenarios.

## 7. Contracts & Ontology Notes
- `contracts/temporal_consistency@1.yaml` now lists publisher/consumers (Temporal Engine, Slot07, Slot10, Governance) and the full payload schema (drift, variance, prediction error, convergence/divergence indicators, gate state, governance state, hash).
- `contracts/slot_map.json` and `specs/nova_framework_ontology.v1.yaml` reference the contract via the new TemporalIntegrity framework so `scripts/contract_audit.py --strict` passes.

## 8. Verification Checklist
1. `python -m pytest tests/temporal tests/router tests/governance tests/integration/test_temporal_pipeline.py tests/web/test_temporal_* -q`
2. `python scripts/contract_audit.py --strict`
3. `curl http://localhost:8000/temporal/debug` (ensure head + entry count > 0 after a routing call)
4. `curl http://localhost:8000/metrics/temporal` (requires `NOVA_ENABLE_PROMETHEUS=1`)
5. `python -m pytest -q` (full suite) once targeted checks pass

## 9. Rollback Strategy
- If temporal metrics or governance holds regress, disable Phase-6 by toggling env overrides:
  - `NOVA_TEMPORAL_DRIFT_THRESHOLD=1.0`
  - `NOVA_TEMPORAL_PREDICTION_ERROR_THRESHOLD=1.0`
  - `NOVA_TEMPORAL_VARIANCE_THRESHOLD=1.0`
- Reset semantic mirror contexts via `reset_semantic_mirror()` to clear stale temporal entries, then re-run validation commands.

Phase-6 is considered stable once all observability tests, contract audits, routing/governance integration suites, and targeted curls succeed with no regressions.

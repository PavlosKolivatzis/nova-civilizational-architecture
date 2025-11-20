| Section | Details |
|---------|---------|
| Goal | Introduce governance (Slot11 conceptual) to ensure global policy, ethics, and cross-slot coherence prior to routing/deployment. |
| Components | GovernanceEngine (`orchestrator/governance/engine.py`), Ethics checker (`ethics.py`), State ledger (`state_ledger.py`), Governance Prometheus metrics, Semantic Mirror contexts, FastAPI endpoints. |
| Data Sources | TRI truth signal (Slot04), Slot07 backpressure, Slot10 gate, Slot05/Slot08 advisors, routing decisions, consent profiles. |
| Outputs | GovernanceResult {allowed, reason, snapshot, ethics}. If blocked → hold mode. Ledger append + metrics record. |
| Semantic Mirror | Publishes `governance.snapshot`, `governance.ethics`, `governance.policy_scores`, `governance.final_decision`. |
| Prometheus | `nova_governance_allowed`, `nova_governance_block_reason`, `nova_governance_policy_score`, `nova_governance_ethics_violations_total`, `nova_governance_state_stability`. |
| Endpoints | `POST /governance/evaluate`, `GET /governance/debug`, router endpoints now include governance context. |
| Tests | `tests/governance/*`, `tests/integration/test_governance_pipeline.py`, `tests/web/test_governance_app.py`, router/web/integration suites updated. |
| Rollback | Disable new endpoints, revert governance modules, remove metrics + semantic mirror keys, clear ledger. |

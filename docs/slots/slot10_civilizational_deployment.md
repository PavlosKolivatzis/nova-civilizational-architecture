# Slot 10 – Civilizational Deployment

- **Purpose:** Progressive canary deployment, MetaLegitimacySeal gating, and audit logging for system rollout.
- **Emits:** audit.emit, MetaLegitimacySeal decisions
- **Consumes:** CULTURAL_PROFILE@1, api.slot09.hybrid.v1 hashes
- **Configuration Flags:** NOVA_SLOT10_ENABLED, NOVA_USE_SHARED_HASH, CanaryController stage thresholds, MLS guardrails
- **Key Metrics:** canary_stage_latency_seconds, mls_decisions_total, audit_emit_latency_ms, deployment_health_feed gauges
- **Authoritative Docs:** [slot10_civilizational_deployment](../../src/nova/slots/slot10_civilizational_deployment/README.md)

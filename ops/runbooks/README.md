# NOVA Operational Runbooks

This directory contains operational runbooks for NOVA Civilizational Architecture incidents and maintenance.

## Available Runbooks

### Core System
- [Slot6 Cultural Synthesis Issues](slot6.md) - High residual risk, synthesis failures
- [Observability Issues](observability.md) - Prometheus export down, metrics missing

### In Development
The following runbooks are planned but not yet created (tracked as tech debt):
- **Slot1 Truth Anchor Problems** - Verification failures, recovery issues
- **Feature Flag Drift** - Unexpected flag state changes
- **TRI Link Integration** - Slot4 ↔ Slot5 coordination issues
- **Lifespan Manager** - FastAPI startup/shutdown problems
- **Shared Hash** - Blake2b audit chain issues

For these scenarios, consult:
- `/metrics` endpoint for current system state
- `agents/nova_ai_operating_framework.md` for general troubleshooting
- Source code comments in relevant slot directories

## Quick Reference

### Immediate Actions
1. Check `/metrics` endpoint for current system state
2. Verify feature flag configuration matches expected state
3. Review recent commits for flag changes or slot modifications
4. Check Prometheus scrape health and alert manager

### Escalation
- **Critical (Slot6 p95 > 0.93)**: Immediate slot team notification
- **Warning (Slot6 p95 > 0.85)**: Schedule slot team review
- **Info (Flag drift)**: Verify deployment intent with ops team

### Tools
- **Dashboard**: `ops/dashboards/nova-phase2-observability.json`
- **Alerts**: `ops/alerts/nova-phase2.rules.yml`
- **Framework**: `agents/nova_ai_operating_framework.md`

### Key Metrics
- `nova_slot6_p95_residual_risk` - Cultural synthesis residual risk
- `nova_slot1_anchors_total` - Truth anchor count
- `nova_slot1_failures_total` - Verification failures
- `nova_feature_flag_enabled` - Flag state visibility

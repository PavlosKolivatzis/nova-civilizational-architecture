# Slot 03 – Emotional Matrix Guardian

- **Purpose:** High-volume emotional safety analysis with cross-slot escalation and policy enforcement.
- **Emits:** EMOTION_REPORT@1, PRODUCTION_CONTROL@1, DELTA_THREAT@1
- **Consumes:** DELTA_THREAT@1 inputs from Slot2 adapters
- **Configuration Flags:** SLOT3_ESCALATION_ENABLED, SLOT3_RATE_PER_MIN, SLOT3_SWING_WINDOW, SLOT3_SWING_DELTA, SLOT3_PREVIEW_MAXLEN
- **Key Metrics:** threat_level_distribution, escalation_events_total, policy_violation_total, slot3_health heartbeat
- **Authoritative Docs:** [slot03_emotional_matrix](../../src/nova/slots/slot03_emotional_matrix/README.md)

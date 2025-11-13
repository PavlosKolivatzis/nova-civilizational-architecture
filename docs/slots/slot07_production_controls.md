# Slot 07 – Production Controls

- **Purpose:** Circuit breaker, reflex emission, and system context publisher for the entire stack.
- **Emits:** Semantic Mirror contexts (pressure, breaker_state), reflex emissions
- **Consumes:** PRODUCTION_CONTROL@1, health feeds
- **Configuration Flags:** NOVA_REFLEX_ENABLED, reflex_policy.max_emission_rate, breaker thresholds, SLOT07_PHASE_LOCK
- **Key Metrics:** slot7_breaker_state, slot7_pressure_level, reflex_emissions_total, slot7_requests_total
- **Authoritative Docs:** [slot07_production_controls](../../src/nova/slots/slot07_production_controls/README.md)

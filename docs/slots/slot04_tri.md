# Slot 04 – TRI Engine

- **Purpose:** Truth Resonance Index scoring, drift detection, and flow-mesh coherence feeds.
- **Emits:** TRI_REPORT@1 (tri.calculate / tri.gated_calculate), operational TRI health snapshot
- **Consumes:** Adaptive link weights from flow fabric, Slot7 pressure/context (for gating)
- **Configuration Flags:** NOVA_ENABLE_TRI_LINK, TriPolicy drift_z_threshold, safe_mode_max_s
- **Key Metrics:** tri_calculation_ms, tri_link_enabled_counter, tri_score_distribution, drift_z & surge_events
- **Authoritative Docs:** [slot04_tri](../../src/nova/slots/slot04_tri/README.md)

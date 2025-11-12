# Slot 05 – Constellation Navigation

- **Purpose:** Spatial positioning + navigation mesh translating TRI scores into cultural coordinates.
- **Emits:** CONSTELLATION_STATE@1, constellation.position, constellation.update_from_tri
- **Consumes:** TRI_REPORT@1
- **Configuration Flags:** NOVA_ENABLE_TRI_LINK, NavigationMesh path_guard rails, PositionCache TTL
- **Key Metrics:** constellation_position_updates, tri_integration_latency_ms, stability_index_distribution
- **Authoritative Docs:** [slot05_constellation](../../src/nova/slots/slot05_constellation/README.md)

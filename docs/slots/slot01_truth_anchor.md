# Slot 01 – Truth Anchor

- **Purpose:** Foundational truth anchoring plus RealityLock cryptography and persistence for the entire system.
- **Emits:** anchor.compute, anchor.verify, anchor.recover
- **Consumes:** (none)
- **Configuration Flags:** SLOT1_STORAGE_PATH, SLOT1_ENHANCED_MODE, NOVA_GM_ENABLED
- **Key Metrics:** nova_slot1_anchors_total, nova_slot1_lookups_total, nova_slot1_recoveries_total, nova_slot1_failures_total
- **Authoritative Docs:** [slot01_truth_anchor](../../src/nova/slots/slot01_truth_anchor/README.md)

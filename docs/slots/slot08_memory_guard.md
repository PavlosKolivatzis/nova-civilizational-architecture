# Slot 08 – Memory Ethics & Lock

- **Purpose:** Legacy ACL guard plus Processual 4.0 self-healing memory lock / IDS pipeline.
- **Emits:** MemoryLock ACL tokens (legacy), PROCESSUAL_CLASSIFICATION_REPORT
- **Consumes:** Semantic Mirror hooks, IDS detectors
- **Configuration Flags:** ACL readers/writers per register(), quarantine thresholds, entropy_drift alarms
- **Key Metrics:** ids_alerts_total, quarantine_duration_seconds, entropy_drift_gauge
- **Authoritative Docs:** [slot08_memory_lock](../../src/nova/slots/slot08_memory_lock/README.md)

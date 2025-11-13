# Slot 02 – ΔTHRESH Content Processing

- **Purpose:** Advanced pattern detection, manipulation filtering, and META_LENS hosting with dual processors.
- **Emits:** DETECTION_REPORT@1, DELTA_THREAT@1, META_LENS_REPORT@1
- **Consumes:** EMOTION_REPORT@1, slot1 anchor snapshots (optional)
- **Configuration Flags:** ProcessingConfig.operational_mode (stable_lock/pass_through), ProcessingConfig.processing_mode (hybrid/simulator), META_LENS_MAX_ITERS / META_LENS_ALPHA / META_LENS_EPSILON, META_LENS_STRICT_VALIDATION, META_LENS_ADAPTER_TIMEOUT_MS / RETRIES / BREAKER_TTL
- **Key Metrics:** total_processed & quarantine_rate (PerformanceTracker), avg_processing_time, avg_tri_score, layer_detections, pass_through_breaches
- **Authoritative Docs:** [slot02_deltathresh](../../src/nova/slots/slot02_deltathresh/README.md)

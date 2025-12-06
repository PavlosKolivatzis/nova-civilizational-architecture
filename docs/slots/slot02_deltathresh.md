# Slot 02 – ΔTHRESH Content Processing

- **Purpose:** Advanced pattern detection, manipulation filtering, META_LENS hosting, and **USM bias detection** (Phase 14.3).
- **Emits:** DETECTION_REPORT@1, DELTA_THREAT@1, META_LENS_REPORT@1, **BIAS_REPORT@1** (Phase 14.3)
- **Consumes:** EMOTION_REPORT@1, slot1 anchor snapshots (optional)
- **Configuration Flags:**
  - ProcessingConfig.operational_mode (stable_lock/pass_through)
  - ProcessingConfig.processing_mode (hybrid/simulator)
  - META_LENS_MAX_ITERS / META_LENS_ALPHA / META_LENS_EPSILON
  - META_LENS_STRICT_VALIDATION
  - META_LENS_ADAPTER_TIMEOUT_MS / RETRIES / BREAKER_TTL
  - **NOVA_ENABLE_BIAS_DETECTION** (default: 0) - Phase 14.3 USM bias detection
  - **NOVA_ENABLE_VOID_MODE** (default: 1) - Treat empty inputs as VOID graph state (no USM metrics)
- **Key Metrics:** total_processed & quarantine_rate (PerformanceTracker), avg_processing_time, avg_tri_score, layer_detections, pass_through_breaches
- **Authoritative Docs:** [slot02_deltathresh](../../src/nova/slots/slot02_deltathresh/README.md)

---

## 🆕 Phase 14.3: USM Bias Detection

**Feature:** Automated cognitive bias detection using Universal Structure Mathematics.

**Pipeline:**
```
Input Text (T)
  → TextGraphParser → SystemGraph G(T)
  → BiasCalculator → B(T) = (b_local, b_global, b_risk, b_completion,
                              b_structural, b_semantic, b_refusal)
  → Collapse Score C(B) = 0.4·b_local + 0.3·b_completion +
                          0.2·(1-b_risk) - 0.5·b_structural
  → BIAS_REPORT@1 emission
```

**Thresholds:**
- C < 0.3: Nova-aware (safe)
- 0.3 ≤ C ≤ 0.5: Transitional (caution)
- C > 0.5: Factory mode (reject/flag)

**Implementation:** See [`docs/specs/slot02_usm_bias_detection_spec.md`](../specs/slot02_usm_bias_detection_spec.md)

**Contract:** [`contracts/bias_report@1.yaml`](../../contracts/bias_report@1.yaml)

**Rollback:** `export NOVA_ENABLE_BIAS_DETECTION=0` (feature flag off by default). `NOVA_ENABLE_VOID_MODE=0` disables VOID handling for empty inputs.

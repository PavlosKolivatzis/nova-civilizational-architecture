# Slot 09 – Distortion Protection

- **Purpose:** Hybrid distortion detection API with infrastructure-aware threat levels and Blake2b audit chains.
- **Emits:** distortion.detect responses, audit.add_hash_chain
- **Consumes:** api.common.hashutils.v1, IDS vector streams
- **Configuration Flags:** NOVA_USE_SHARED_HASH, HybridApiConfig.retries / jitter, Circuit breaker policies
- **Key Metrics:** audit_hash_method_counter, shared_hash_enabled_counter, hash_chain_generation_ms, ids_eval latency
- **Authoritative Docs:** [slot09_distortion_protection](../../src/nova/slots/slot09_distortion_protection/README.md)

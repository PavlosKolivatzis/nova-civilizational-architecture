# Slot 06 – Cultural Synthesis

- **Purpose:** Cultural guardrail validation with anomaly-aware unlearning and Semantic Mirror context.
- **Emits:** CULTURAL_PROFILE@1, GuardrailValidationResult
- **Consumes:** TRI_REPORT@1, Slot7 production pressure contexts, Slot2 threat bridge
- **Configuration Flags:** SynthesisConfig.tri_min_score, anomaly pulse multipliers (receiver.py), Semantic Mirror channel bindings
- **Key Metrics:** adaptation_effectiveness, principle_preservation, residual_risk, unlearn_decay_total
- **Authoritative Docs:** [slot06_cultural_synthesis](../../src/nova/slots/slot06_cultural_synthesis/README.md)

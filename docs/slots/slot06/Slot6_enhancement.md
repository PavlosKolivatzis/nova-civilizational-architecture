# Slot 6 — Adaptive Synthesis Engine v7.4.1
ΔTHRESH v6.6 | Unified Cultural & Ethical Simulation

The Slot 6 Adaptive Synthesis Engine powers Nova’s cultural adaptation matrix. It balances truth anchoring with cultural flexibility to ensure safe deployment across diverse contexts while preserving epistemic integrity.

## Technical Highlights
- Non-recursive breadth-first traversal with cycle and depth caps
- Regex-hardened canonical forbidden mapping and boundary-safe scanning
- Consent-aware simulation gating
- Constellation budget integration (Slot 5)
- Thread-safe metrics preserving exponential moving averages
- Timeout and memory caps with graceful shutdown

## Usage
```python
from nova.slots.slot06_cultural_synthesis.engine import AdaptiveSynthesisEngine

engine = AdaptiveSynthesisEngine()
profile = engine.analyze_cultural_context(
    "Test University",
    {"region": "EU", "language": "en", "empiricism_priority": 0.8}
)

result = engine.validate_cultural_deployment(
    profile,
    "academic",
    {"content": "normal content", "messaging": {}}
)

print(result.result, result.compliance_score)
```
Additional scenarios are covered in the Slot 6 test suite under `tests/test_slot06_*`.

## Implementation
See [engine.py](src/nova/slots/slot06_cultural_synthesis/engine.py) for the core engine implementation, [adapter.py](src/nova/slots/slot06_cultural_synthesis/adapter.py) for the Slot 10 adapter, and [serializers.py](src/nova/slots/slot06_cultural_synthesis/serializers.py) for serialization helpers.

## Metrics
`get_performance_metrics()` returns analysis counts, guardrail blocks, and principle preservation rate along with engine fingerprint and configuration.

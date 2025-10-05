# Slot 4b: TRI Content Analysis Engine

## Status: Operational ✅ (Engine 2 of Dual-Engine Architecture)

**Purpose:** Plugin-based content analysis and TRI scoring for text/artifacts

## Architecture

Slot 4 uses a **dual-engine architecture** via `Slot4TRIAdapter`:

- **Engine 1 (slot04_tri):** Operational monitoring, real-time TRI reports (`get_latest_report()`)
- **Engine 2 (slot04_tri_engine):** Content analysis, plugin-based scoring (`calculate(content, context)`)

Both engines are active and serve different purposes. The adapter routes requests to the appropriate engine based on method called.

## Components

- Truth Resonance Index (TRI) calculation for content
- Kalman filter estimation
- Bayesian inference systems
- Confidence interval tracking
- Plugin-based scoring (structural, semantic, expression layers)

## Integration Points

- **Adapter:** `orchestrator/adapters/slot4_tri.py` routes to this engine for `calculate()` calls
- **Content Analysis:** Provides TRI scores for text/artifact analysis
- **Fallback:** If unavailable, adapter falls back to Engine 1 or safe defaults

## Usage

```python
from orchestrator.adapters.slot4_tri import Slot4TRIAdapter

adapter = Slot4TRIAdapter()

# Content analysis uses Engine 2 (this engine)
result = adapter.calculate("content to analyze", context={})
# Returns: {"score": 0.x, "layer_scores": {...}, "metadata": {...}}

# Operational monitoring uses Engine 1 (slot04_tri)
report = adapter.get_latest_report()
# Returns: {"coherence": 0.x, "phase_jitter": 0.x, "tri_score": 0.x}
```

## Tests

- `tests/test_orchestrator_slot4_tri_adapter.py` - Adapter routing tests
- `tests/e2e/test_constellation_with_tri.py` - End-to-end TRI integration

## Notes

- README last updated: 2025-10-04 (was stale since 2025-08-13)
- False claims removed: Slot 6/7 direct integration claims (adapter-mediated instead)
- See `orchestrator/adapters/slot4_tri.py` for smart routing logic

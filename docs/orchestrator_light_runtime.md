# NovaGate Light Runtime

**Goal:** Extract the runtime kernel already latent in the orchestrator—no rewrite, minimal risk.

## Components
- **EventBus (enhanced):** Adds `trace_id` and lifecycle hooks (`start/success/failure`) for every event.
- **PerformanceMonitor (new):** Centralizes per-slot health: `avg_latency_ms`, `error_rate`, `throughput`.
- **AdaptiveRouter (new):** Chooses primary or fallback slot based on health thresholds.

## Behavior
1. A request is wrapped in an `Event` and published to the bus (trace starts).
2. The router selects a target slot (primary or fallback) using monitor health.
3. The orchestrator invokes the slot with existing timeout/retry/circuit-breaker logic.
4. Monitor captures outcomes for live health + observability.

## Why this is “Light”
- Zero breaking changes to slot contracts.
- No rewrite of orchestrator core; additions are orthogonal.
- Immediate observability + basic self-healing.

## Configure
```python
router.fallback_map = {"slot6": "slot6_fallback"}
router.latency_threshold_ms = 1000.0
router.error_threshold = 0.2
```

## Test

Run:

```
pytest -q
```

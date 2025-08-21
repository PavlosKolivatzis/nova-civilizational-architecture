# Slot 6 — Adaptive Synthesis Engine v7.4.1
**ΔTHRESH v6.6 | Unified Cultural & Ethical Simulation**
Production-consolidated module for multicultural truth synthesis with bounded ethical simulation.
## Highlights
- **Safety:** Non-recursive BFS traversal, cycle/depth caps, byte-safe decoding, timeout + memory caps.
- **Correctness:** Canonical forbidden-term mapping (snake_case) with boundary-safe regex.
- **Consent-Aware:** Simulation triggers require explicit/educational consent.
- **Constellation Integration:** Slot 5 budgets via `_apply_creativity_budget` with hard safety clamps.
- **Observability:** Thread-safe metrics + EMA `principle_preservation_rate`.
- **Compatibility:** Slot 10 adapter (`MulticulturalTruthSynthesisAdapter`) with stable APIs.
## Quick Start
```python
from slot6.engine import AdaptiveSynthesisEngine, MulticulturalTruthSynthesisAdapter
engine = AdaptiveSynthesisEngine()
adapter = MulticulturalTruthSynthesisAdapter(engine)
res = engine.analyze_and_simulate(
    "Oxford_Ethics_Institute",
    {"content": "Imagine ethical implications of AI governance"},
    {"region": "EU", "constellation_budget": {"scale": 0.8, "max_depth": 2, "temporal_window": 0.08}}
)
print(res.simulation_status, res.compliance_score)
```
## Configuration Knobs
| Key | Default | Notes |
|---|---:|---|
| `regex_text_cap` | 2_000_000 | Max bytes scanned for forbidden terms |
| `max_container_depth` | 50 | BFS traversal depth cap |
| `analysis_timeout` | 5.0 | Hard timeout for scans |
| `max_string_length` | 100_000 | Per-string truncation |
| `min_safe_adaptation` | 0.15 | Floor for adaptation |
| `max_safe_adaptation` | 0.85 | Ceiling for adaptation |
| `max_budget_relaxation` | 0.10 | Max extra allowed via Slot 5 budget |
## CI / Smoke Test
Run `pytest -q` to execute the smoke test in `tests/test_smoke.py`.

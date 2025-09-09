## Maturity Matrix (0–4)
| Slot | Level | Rationale |
|------|-------|-----------|
|1|4 – Processual|Cryptographic RealityLock with recovery & metrics|
|2|4 – Processual|ΔΣΘΩ detection pipeline, metrics, full tests|
|3|3 – Structural|Escalation manager, advanced safety policy, health contract, feature flags|
|4|3 – Structural|TRI engine with IDS integration; lacks adaptive loop|
|5|2 – Relational|Constellation engine minimal; needs routing logic|
|6|4 – Processual|Adaptive synthesis engine + legacy bridge|
|7|2 – Relational|Basic controls; feature flags without observability|
|8|3 – Structural|Comprehensive IDS memory guard; no recovery loop|
|9|4 – Processual|Hybrid IDS policies, Slot10 interoperability|
|10|3 – Structural|Deployment flow with MLS; no adaptive rollout|

## Quality & Risk
* **Testing breadth:** Slot3 (7 tests), Slot5 (3), Slot6 (6), Slot7 (3), Slot8 (4), Slot9 (1), Slot10 (5), Slot1 (2); other slots lack direct tests. Contract suite adds `test_slot_map_imports.py` to ensure path integrity.
* **CI signals:** `nova-ci.yml` validates architecture, runs tests with/without Slot6 legacy, and checks enhancement docs. `health-config-matrix.yml` runs health smoke tests across Python versions and serverless/watchdog permutations. `ids-ci.yml` validates IDS schemas; `health-config-ci.yml` performs lightweight checks.
* **Error handling:** Adapters wrap optional imports, returning null objects on failure. Event Bus employs per-handler timeouts.
* **Thread-safety:** Slot3’s `AdvancedSafetyPolicy` uses `threading.RLock`; Event Bus uses `asyncio` without explicit locks.

## Security
* JWT/IDS handled in `auth.py` and Slot9 policies. Slot8’s `lock_guard` ensures memory tamper detection.
* Potential unauthenticated endpoints: internal health endpoints rely on FastAPI defaults; consider explicit auth middleware.

:::task-stub{title="Authenticate health endpoints"}
Add authentication/authorization checks for `/health` and `/health/config` in `orchestrator/app.py` using existing auth utilities to restrict access.
:::

## Performance
* Event Bus metrics track average handler time, events, and errors.
* IDS p99 targets not codified; slot3 escalation rate limiter and Slot7 production controls enforce throughput caps.

:::task-stub{title="Define p99 latency targets"}
Introduce configurable p99 latency thresholds and export them via metrics in `orchestrator/health.py` for alerting.
:::

## Gaps & Duplication
* Slots 7–10 lack meta.yaml contracts; inconsistent adapter naming.
* Legacy Slot6 engine still present alongside new API.

:::task-stub{title="Add meta.yaml for remaining slots"}
Create `{slotXX}.meta.yaml` files for Slots 7–10 under each slot directory with contract info mirroring existing schemas.
:::

## Roadmap (Prioritized)
1. **PluginLoader + NullAdapters everywhere** – ensure every contract ID has a default null implementation.
2. **Contract freeze tests** – verify schemas (e.g., `slot3_health_schema.json`) remain stable.
3. **Uniform contract naming** – align adapters to canonical IDs (EMOTION_REPORT@1, etc.).
4. **Observability** – export counters (`slot3.threat_*`, `rate_limited`) and set SLO alerts.

:::task-stub{title="Implement contract freeze tests"}
Add JSON‑schema regression tests for public contracts (starting with `slot3_health_schema.json`) under `tests/contracts/`.
:::

:::task-stub{title="Standardize contract naming in adapters"}
Audit all `orchestrator/adapters/*.py` and slot plugins to ensure contract IDs follow `NAME@VERSION` format; update mismatches.
:::

:::task-stub{title="Export observability counters"}
Instrument Slots 3 and 7 to expose Prometheus counters (`slot3.threat_*`, `slot7.rate_limited`) via `orchestrator/metrics.py`.
:::

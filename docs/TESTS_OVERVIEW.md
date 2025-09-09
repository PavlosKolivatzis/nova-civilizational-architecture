| Slot | Test Files | Notes |
|------|------------|-------|
|1|2|Reality-lock checks|
|2|0|ΔTHRESH covered indirectly|
|3|7|Advanced policy, escalation, adapters, health|
|4|0|No dedicated TRI tests|
|5|3|Connectivity & engine|
|6|6|Legacy compatibility, adapter logging, properties|
|7|3|Active safeguards & production controls|
|8|4|Lock guard & memory write|
|9|1|Auth integration|
|10|5|Deployment flow & guardrails|

Contract suite: `tests/contracts/` (schema freezes, path imports).

### CI Workflows
* `nova-ci.yml` – main matrix (`standard-blocked`, `legacy-compat`) plus Slot6 legacy tests.
* `health-config-matrix.yml` – Python 3.10–3.12 × watchdog/serverless permutations; smoke tests for `/health` and `/health/config`.
* `ids-ci.yml` – IDS schema validation and sandbox toggles.
* `health-config-ci.yml` – lightweight health check run.

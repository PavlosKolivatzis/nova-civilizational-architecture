# Contract Versioning & Rollout Playbook

**Scope:** NOVA data contracts (e.g., `slot3_health_schema.json`, `slot6_cultural_profile_schema.json`) and payloads that implement them.

---

## Principles

- **Compatibility first.** Prefer additive, backward-compatible changes.
- **Explicit versioning.** Contracts include `schema_version` (and optional `schema_id` URI) for traceability.
- **Guarded evolution.** CI freeze gate + contract tests + CODEOWNERS review are mandatory for schema edits.
- **Boring rollouts.** Use dual-write/dual-read patterns for any breaking changes.

---

## Change Types

| Type                         | Examples                                             | `schema_version` | PR tag(s)                 | Notes                                  |
|------------------------------|------------------------------------------------------|------------------|---------------------------|----------------------------------------|
| **Compatible**               | Add optional field; widen enum; add description      | bump minor (e.g., `1.1`) or keep | `CONTRACT:EXPLAIN`       | No consumer breakage                   |
| **Breaking**                 | Remove/rename field; tighten bounds; change types    | bump major (e.g., `2.0`)          | `CONTRACT:BUMP`, `CONTRACT:EXPLAIN` | Requires migration plan                |
| **Emergency (hotfix)**       | Fix typo in description; doc only                    | no bump           | `CONTRACT:EXPLAIN`        | Documentation only                     |

> **Freeze gate:** PRs that touch `contracts/*.json` must include the proper `CONTRACT:*` tag(s) or CI will fail.

---

## Rollout Workflow (Breaking Changes)

1. **Design**
   - Write migration notes in the PR description.
   - Include a brief impact assessment and fallback plan.

2. **Add v2 Schema**
   - Introduce new fields / stricter rules as needed.
   - Update `schema_version` and keep `schema_id` stable or versioned as you prefer.

3. **Dual-Write (Producers)**
   - Producers (e.g., Slot 3/6) optionally emit both legacy and new payloads behind a feature flag.
   - Keep legacy consumers untouched during this phase.

4. **Dual-Read (Consumers)**
   - Consumers accept both v1 and v2 payloads (prefer v2 if present).
   - Track validation metrics during canary rollout.

5. **Flip Default**
   - Switch producers to v2 as default.
   - Keep v1 for a grace period.

6. **Deprecation / Removal**
   - Remove v1 write path.
   - Clean tests and samples for v1.
   - Announce deprecation timeline in `docs/CHANGELOG.md`.

---

## Required Signals & Tests

- **Contract tests** (CI): validate sample payloads and live health payloads against the current schema.
- **Presence guard**: test asserts schemas exist (`contracts/slot*_*.json`).
- **Nightly drift sentinel**: validates all schemas + example payloads (auto-run).
- **Provenance in payloads**: `schema_id`, `schema_version` present (health and profile).

---

## Runtime Validation (Optional but Recommended)

- **Feature flag**: `CONTRACT_RUNTIME_VALIDATE_SAMPLE_RATE` (0.0–1.0; default 0.0).
- **Behavior**: Validate a sample of runtime payloads (non-blocking).
- **Metrics**:
  - `contract_validation_attempts_total{slot=...}`
  - `contract_validation_failures_total{slot=...}`

This gives early warning for drift without impacting latency.

---

## Local & CI Commands

- **Validate all schemas**  
  `python scripts/validate-schemas.py`

- **Run contract tests only**  
  `pytest -q tests/contracts/`

- **Smoke health**  
  `curl -s http://localhost:8000/health | jq .`  
  *(or use the FastAPI `TestClient` in CI)*

---

## Governance Checkpoints

- **CODEOWNERS**: Schema changes require owner review.
- **Commitlint**: Conventional messages enforced.
- **Docs**: Update `docs/ARCHITECTURE.md` links and the "Contract Schemas & Governance" section on any change.
- **Changelog**: Record breaking changes and deprecations in `docs/CHANGELOG.md`.

---

## FAQ

**Q: Do I always need to bump `schema_version`?**  
A: Bump for anything that risks consumer breakage. Purely additive, optional fields can keep the same version, but consider a minor bump for clarity.

**Q: Where must `schema_id` and `schema_version` appear?**  
A: In all **contract-governed** payloads (e.g., Slot 3 health objects, Slot 6 cultural profiles) so provenance is observable in logs and `/health`.
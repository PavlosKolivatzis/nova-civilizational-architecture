## Copilot / AI Assistant Instructions for Nova Civilizational Architecture

Purpose: quickly orient an AI coding assistant to the repository's architecture, conventions, and common developer workflows so suggestions and edits are safe, consistent, and productive.

- **Big picture:** Core runtime lives under `src/nova/` organized by slot (e.g. `src/nova/slots/slot05_constellation`). The orchestrator and service entrypoints live in `orchestrator/` and the top-level `app.py` / `orchestrator.app`. Many operational scripts and runbooks live in `scripts/` and `ops/`.

- **Primary goals for edits:** keep slot behavior contract-compliant, preserve feature-flag semantics, and avoid changing cross-slot contracts in `contracts/` without updating `contracts/slot_map.json` and relevant tests.

- **Key files to consult before coding:**
  - `AGENTS.md`, `CLAUDE.md`, `README.md` — high-level workflows and commands
  - `docs/ARCHITECTURE.md` and `docs/slots/*` — architecture and slot briefs
  - `contracts/` — contract schemas and `contracts/slot_map.json`
  - `src/nova/slots/` — canonical slot implementations
  - `orchestrator/` and `monitoring/` — service orchestration and observability

- **Common developer commands (use as examples when suggesting runs):**
  - Install dev deps: `pip install --only-binary :all: -r requirements.txt`
  - Run unit tests: `python -m pytest -q` or targeted tests `python -m pytest tests/test_slot02_deltathresh.py -q`
  - Lint and typecheck: `python -m ruff check src/nova orchestrator tests` and `python -m mypy src/nova orchestrator scripts`
  - Maturity check (npm): `npm run maturity` (see `CLAUDE.md` for usage)

- **Runtime caveats to preserve:**
  - Feature flags use strict string equality: only the literal string `"1"` enables a flag (e.g. `NOVA_ENABLE_PROMETHEUS=1`). Do not suggest toggling flags to `true/false` booleans.
  - Some counters and metrics require single-worker uvicorn for correctness; prefer `--workers 1` when suggesting `uvicorn` run commands.
  - Sensitive defaults: never commit real secrets. Tests assume `JWT_SECRET` exists; use a test secret locally (`JWT_SECRET="test-secret-..."`).

- **Project-specific patterns and conventions:**
  - Namespaced imports: prefer `from nova.slots.slotXX import ...` over legacy `slots.*` imports.
  - Slot plugin model: slots can be enabled via `NOVA_SLOTS` or gate flags (check `src/nova/slots/*` and plugin loaders).
  - NullAdapters: missing producers degrade gracefully; prefer returning adapter-compatible null objects rather than raising when integrating cross-slot flows.
  - Thresholds & safety: numeric thresholds are validated at startup via `nova.config.thresholds`; changes must keep values inside documented safe ranges.

- **When changing public contracts (schemas / events):**
  - Update `contracts/` schema files and `contracts/slot_map.json`.
  - Add / update contract tests in `tests/` and a changelog entry.
  - Add a `CONTRACT:BUMP` tag to the PR description and run CI contract lanes.

- **Testing guidance for AI-generated changes:**
  - Suggest a minimal targeted test to verify behavior (unit test in `tests/` mirroring slot layout). Use existing test patterns and markers (e.g. `@pytest.mark.health`, `integration`).
  - Recommend running `pytest -q` locally and include the exact failing test command in PR description when relevant.
  - For schema changes, run schema validation examples under `tests/` that reference `meta.yaml` in `src/nova/slots/**`.

- **Quick examples to include in edits or PR notes:**
  - Run single-slot tests: ``python -m pytest tests/test_slot05_constellation.py -q``
  - Start orchestrator locally: ``python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1``

- **Do not:**
  - Replace the feature-flag string-equality checks with boolean flags.
  - Change `contracts/` or slot APIs without adding tests and updating `contracts/slot_map.json`.
  - Propose multi-worker uvicorn without verifying counter/metric implications.

If anything here is unclear or you'd like examples expanded (more command snippets, additional code references), tell me which section to expand and I will iterate.

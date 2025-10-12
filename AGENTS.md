# Repository Guidelines

## Project Structure & Module Organization
Nova currently executes from the legacy tree: `orchestrator/` hosts coordination services, `slots/` contains the ten cognitive slot packages, and `api/`, `services/`, plus `config/` provide external surfaces and shared settings. Scenario, contract, and regression suites live under `tests/`, mirroring the production module layout; reference scripts and runbooks sit in `scripts/` and `ops/`. The `src/nova/` namespace is only a placeholder; keep active modules in place until the staged migration plan lands.

## Build, Test, and Development Commands
Create an isolated environment and install runtime dependencies with `pip install --only-binary :all: -r requirements.txt`. Execute the full suite through `python -m pytest -q`, or limit to health checks with `pytest -m health --ignore=tests/contracts`. Regenerate maturity metrics via `npm run maturity`, and run the orchestrator locally with `python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1`.

## Coding Style & Naming Conventions
Follow PEP 8 semantics: four-space indentation, 120-character soft limit, and descriptive docstrings aligned with `orchestrator/app.py`. Keep modules, packages, and fixtures in snake_case; for example `slots/slot06_cultural_synthesis` and `tests/test_slot06_dispatch.py`. Before submitting, run `ruff check orchestrator slots tests` and `python -m mypy orchestrator slots scripts` to hold formatting and typing baselines.

## Testing Guidelines
Pytest governs the stack and custom markers are enumerated in `pytest.ini`; new smoke tests must include `@pytest.mark.health` for CI fan-out. Property-driven checks rely on Hypothesis and belong under `tests/property/` with deterministic seeds or explicit seed logging. Use focused loops like `pytest tests/slots/test_slot06_* --maxfail=1 -q` while developing, then finish with a clean `python -m pytest` execution to confirm coverage targets tracked in `TEST_GAPS.md`.

## Commit & Pull Request Guidelines
Commits must use Conventional Commits enforced by commitlint: `type(scope): subject` with a lowercase subject and kebab-case scope. Example: `feat(orchestrator-health): enforce single-worker guard`, which stays under 72 characters. Pull requests should describe intent, link tickets, list the commands you ran (pytest, maturity, optional mypy/ruff), and attach evidence for behavioral changes.

## Migration Watchpoints
The `src/nova/` packaging effort resumes once compatibility shims are ready; incremental import rewrites should maintain both legacy and namespaced entry points during transition. When experimenting, adjust `PYTHONPATH` helpers in the fixtures and confirm slot-specific monkeypatches survive before pushing.

## Namespaced Slots
All slot implementations now live under `src/nova/slots/`. The legacy `slots/slotXX_*` packages remain as lightweight shims so older imports continue to work, but new code should always import via `nova.slots.<slot_name>` (e.g., `from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine`). Use the shared `src_bootstrap.ensure_src_on_path()` helper when interacting with modules executed from the repository root.
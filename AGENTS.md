# Repository Guidelines

## Project Structure & Module Organization
Nova now ships from the namespaced tree under `src/nova/`. Slot packages live in `src/nova/slots/slotXX_*`, shared runtime helpers sit beside them (for example `src/nova/slot_loader.py` and `src_bootstrap.py`), and package entry points re-export through `nova.*`. The legacy `slots/` folder remains as thin compatibility shims; treat it as read-only. Core orchestration modules continue to reside in `orchestrator/`, while scenarios, contracts, and regression suites inhabit `tests/`. Operational scripts, dashboards, and runbooks stay in `scripts/` and `ops/`.

## Build, Test, and Development Commands
Create an isolated environment and install runtime dependencies with `pip install --only-binary :all: -r requirements.txt`. Execute the full suite via `python -m pytest -q`. Scope work by running `python -m pytest tests/test_slot03_enhanced_health.py -q` or `python -m pytest tests/health/test_slot_health_units.py -k slot06`. Rebuild maturity metrics with `npm run maturity`, and launch the orchestrator locally using `python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1`.

## Coding Style & Naming Conventions
Follow PEP 8 conventions: four-space indentation, a 120-character soft limit, and docstrings that explain intent rather than restating the signature. Modules, packages, and fixtures stay in snake_case and should import through the namespace—e.g., `from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine`, not legacy `slots.*`. Before submitting, run `python -m ruff check src/nova orchestrator tests` and `python -m mypy src/nova orchestrator scripts` to keep formatting and typing baselines clean.

## Testing Guidelines
Pytest orchestrates the stack; custom markers live in `pytest.ini` (`health`, `integration`, `slow`). Property-based tests belong under `tests/property/` with deterministic seeds or explicit logging. Lean on tight loops such as `python -m pytest tests/test_slot03_enhanced_health.py --maxfail=1 -q` while iterating, then finish with a full `python -m pytest` run to confirm coverage bounds tracked in `TEST_GAPS.md`.

## Commit & Pull Request Guidelines
Commits must follow Conventional Commits (`type(scope): subject`) enforced by commitlint; keep subjects lowercase and ≤72 characters. Pull requests should summarize intent, link issues, list verification commands (pytest lanes, maturity job, optional mypy/ruff), and attach evidence or screenshots for behavioral changes.

## Migration Watchpoints
Prefer imports through `nova.*` and update adapters or fixtures that still reference `slots.*` when you touch them. When experimenting with shims, call `src_bootstrap.ensure_src_on_path()` inside scripts so relative invocations resolve against `src/`. Confirm slot-specific monkeypatch paths match the new module locations before pushing.

## Namespaced Slots
All production implementations originate from `nova.slots.<slot_name>`. The compatibility packages under `slots/slotXX_*` forward imports but will be removed once downstream integrations migrate. New code, tests, and documentation should reference `src/nova/slots/` paths and `nova.slots.*` imports explicitly.


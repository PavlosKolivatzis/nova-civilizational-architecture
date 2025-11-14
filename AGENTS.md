# Repository Guidelines

## Project Structure & Module Organization
- Core Python sources live under `src/nova/`, namespaced by slot (e.g., `src/nova/slots/slot01_truth_anchor/`), with shared helpers beside them (`src/nova/slots/config/`, `src/nova/quantum/`).
- Compatibility shims under `slots/` are legacy—treat as read-only.
- Orchestration code resides in `orchestrator/`; observability assets are in `monitoring/`.
- Tests are in `tests/`, mirroring the slot layout (e.g., `tests/slot01/`); docs and ADRs live under `docs/`.

## Build, Test, and Development Commands
- Create a virtual env, then install dependencies: `pip install --only-binary :all: -r requirements.txt`.
- Run targeted tests, e.g., `python -m pytest tests/slot01/test_quantum_entropy.py -q`, or full suite: `python -m pytest -q`.
- Lint and type-check before pushing: `python -m ruff check src/nova orchestrator tests` and `python -m mypy src/nova orchestrator scripts`.
- Launch the orchestrator locally: `python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1`.

## Coding Style & Naming Conventions
- Follow PEP 8 with 4-space indentation and a 120-character soft line limit.
- Use descriptive docstrings that explain intent; default to snake_case for modules, packages, and fixtures.
- Prefer namespaced imports (e.g., `from nova.slots.slot06_cultural_synthesis...`) rather than legacy `slots.*`.
- Run formatters (`ruff`, `mypy`) prior to commits; avoid mixing unrelated changes.

## Testing Guidelines
- Pytest orchestrates the test suite; property-based tests belong in `tests/property/` with deterministic seeds.
- Use existing markers from `pytest.ini` (`health`, `integration`, `slow`, etc.) and adhere to slot-based naming.
- Keep coverage expectations in mind (`TEST_GAPS.md` tracks outstanding work); add regression tests when touching slot behavior.

## Commit & Pull Request Guidelines
- Commits must follow Conventional Commits (`type(scope): subject`, lowercase, ≤72 chars) as enforced by commitlint.
- Pull requests should include: intent summary, linked issues, verification commands (`pytest`, `ruff`, `mypy` lanes), and evidence/screenshots for behavior changes.
- Keep PRs focused; document any configuration toggles (e.g., feature flags in `.env.example`) and note post-merge activation steps.

## Security & Configuration Tips
- `.env.example` documents all supported environment variables; never commit real secrets-use local `.env`.
- Quantum entropy features are feature-flagged; default to simulator backend and confirm metrics before enabling in production.***

## Flag Semantics (Canonical Format)
- All Nova feature flags use strict string equality.
- The literal string `"1"` enables a feature; `"0"` or any other value disables it.
- This rule applies across orchestrator services, slot bootstraps, CI, and runbooks.

```bash
NOVA_ENABLE_PROMETHEUS=1   # Enabled
NOVA_ENABLE_PROMETHEUS=0   # Disabled
```

Use [.env.example](./.env.example) as the authoritative reference when defining environment files.

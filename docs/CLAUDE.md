# Claude Code Instructions

## Commands to use by default

- **Maturity (machine-safe):**
  - Windows: `powershell -NoLogo -NoProfile -Command ./tools/maturity.ps1`
  - Unix/Git Bash: `./tools/maturity.sh`
  - Or: `npm run maturity`
- **After changes:** re-run `pytest -q` and then the maturity command above.

## Environment Setup

```bash
# Set JWT secret for tests
export JWT_SECRET=dev

# Run tests
pytest -q

# Run maturity check
npm run maturity
```

## Rules

- Always prefer the maturity command with `--format json` (via the wrappers/aliases).
- Do not fail the session on thresholds; only surface JSON output and continue.
- Use `python -m pytest tests/test_slot02_deltathresh.py -q` for specific slot testing.
- Check for `meta.yaml` files under `src/nova/slots/**` for schema validation.

## Quick Commands

- Full test suite: `pytest -q`
- Slot 2 tests: `python -m pytest tests/test_slot02_deltathresh.py -q`
- Maturity check: `npm run maturity`
- Maturity diff: `npm run maturity:diff`


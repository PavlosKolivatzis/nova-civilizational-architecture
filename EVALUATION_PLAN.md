# Nova System Cleanup & Audit - Evaluation Plan

**Branch:** `audit/system-cleanup-v1`
**Start Date:** 2025-10-04 (Europe/Athens)
**Baseline Commit:** b4d1793349181ab4e5c02ad4e8c66d5f01e9a3f9
**Commit Message:** "chore: clean experimental artifacts and add to gitignore"
**Commit Date:** 2025-10-03 09:33:16 +0300

---

## Mission Goals (Ordered Priority)

1. **Truth Map** the repo: files, modules, ownership, runtime flows, external deps
2. **Verify behavior**: run tests, smoke endpoints/CLIs, confirm CI gates
3. **Detect drift**: code↔docs mismatches, dead configs, unused files, broken links, stale ADRs
4. **Find defects**: logic bugs, exceptions, security smells, race/IO issues, boundary gaps
5. **Prune/Update**: remove or archive outdated docs/code; update remaining docs to match reality
6. **Harden**: add/upgrade tests, enforce quality gates, fix CI fragilities
7. **Deliver**: open granular PRs with atomic changes, clear diffs, roll-back plans

---

## Environment Baseline

**Recorded:** 2025-10-04 05:16:36 EET

| Component | Version/Details |
|-----------|----------------|
| Python | 3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)] |
| Pip | 25.2 |
| Git | 2.51.0.windows.1 |
| Platform | Windows-11-10.0.26100-SP0 |
| Machine | AMD64 |

**Repository Inventory:**
- Total files (tracked extensions): 553
- Python files: 378
- Markdown files: 84
- YAML files: 42 (.yml + .yaml)
- JSON files: 34
- PowerShell scripts: 10
- Shell scripts: 4
- INI files: 1

---

## Phase Execution Checklist

### ✅ Phase 0: Environment & Baseline

- [x] Create branch `audit/system-cleanup-v1`
- [x] Record baseline commit hash: b4d1793
- [x] Capture Python, pip, git versions
- [x] Generate file inventory by extension
- [ ] Record installed package versions (pip list)
- [ ] Generate dependency tree
- [ ] Create initial AUDIT_LOG.md
- [ ] Create initial REPO_MAP.md skeleton
- [ ] Commit EVALUATION_PLAN.md

**Status:** IN PROGRESS
**Started:** 2025-10-04 05:16 EET

---

### Phase 1: Build, Test, CI, Runtime Smoke

- [ ] Run full test matrix: `pytest -q --maxfail=1 --disable-warnings`
- [ ] Run fast test suite: `pytest -q -k "not slow" -x`
- [ ] Generate coverage report (htmlcov/, coverage.xml)
- [ ] Record test results in AUDIT_LOG.md
- [ ] Start FastAPI service (orchestrator.app)
- [ ] Smoke test critical endpoints (/health, /metrics, /reflection)
- [ ] Record service startup logs and response times
- [ ] Check CI configuration (.github/workflows/)
- [ ] Verify CI gate definitions

**Status:** PENDING
**Estimated Start:** After Phase 0 complete

---

### Phase 2: Static + Semantic Analysis

- [ ] Run ruff check
- [ ] Run ruff format --check
- [ ] Run mypy (capture warnings, don't fail)
- [ ] Run bandit security scan
- [ ] Run pip-audit for dependency vulnerabilities
- [ ] Generate dependency tree with pipdeptree
- [ ] Run vulture for dead code detection
- [ ] Search for audit tags (TODO/FIXME/HACK/XXX/BUG)
- [ ] Search for risky patterns (eval/exec/subprocess)
- [ ] Search for potential secrets in code
- [ ] Record all findings in AUDIT_LOG.md

**Status:** PENDING

---

### Phase 3: Drift & Docs Integrity

- [ ] Map all README.md files and their claims
- [ ] Verify README claims against actual code
- [ ] Check API surface vs documentation
- [ ] Validate configuration specs vs actual env vars
- [ ] Run link checker on all markdown files
- [ ] Cross-reference meta.yaml contracts with flow_fabric_init.py
- [ ] Document mismatches in OUTDATED_DOCS.md
- [ ] Document drift in DRIFT_REPORT.md

**Status:** PENDING

---

### Phase 4: Issues, Tests, and Fix PRs

- [ ] Prioritize defects from DEFECTS_REGISTER.yml
- [ ] For each P0/P1 defect:
  - [ ] Create topic branch
  - [ ] Write failing test
  - [ ] Implement fix
  - [ ] Verify green tests
  - [ ] Update docs
  - [ ] Open PR with evidence and rollback plan
- [ ] Document test gaps in TEST_GAPS.md
- [ ] Document risks in RISK_REGISTER.md

**Status:** PENDING

---

### Phase 5: Cleanup & Alignment

- [ ] Identify truly dead files (zero references)
- [ ] Archive or remove dead files with justification
- [ ] Normalize config files (.env.example, settings)
- [ ] Update quality gates in CI
- [ ] Finalize REPO_MAP.md
- [ ] Finalize CLEANUP_PLAYBOOK.md
- [ ] Create standardized PR/issue templates
- [ ] Create/update CODEOWNERS

**Status:** PENDING

---

## Deliverables Tracking

| Document | Status | Location | Last Updated |
|----------|--------|----------|--------------|
| EVALUATION_PLAN.md | ✅ CREATED | / | 2025-10-04 05:16 EET |
| AUDIT_LOG.md | ⏳ IN PROGRESS | / | - |
| REPO_MAP.md | 📝 PLANNED | / | - |
| OUTDATED_DOCS.md | 📝 PLANNED | / | - |
| DRIFT_REPORT.md | 📝 PLANNED | / | - |
| DEFECTS_REGISTER.yml | 📝 PLANNED | / | - |
| TEST_GAPS.md | 📝 PLANNED | / | - |
| RISK_REGISTER.md | 📝 PLANNED | / | - |
| CLEANUP_PLAYBOOK.md | 📝 PLANNED | / | - |
| LINKCHECK_REPORT.md | 📝 PLANNED | / | - |
| .github/ISSUE_TEMPLATE/bug_report.yml | 📝 PLANNED | .github/ | - |
| .github/pull_request_template.md | 📝 PLANNED | .github/ | - |
| CODEOWNERS | 📝 PLANNED | / | - |

---

## Quality Gates (Target)

- **Tests:** ≥ 85% line coverage overall; 100% on critical gates
- **Static:** ruff clean; mypy --strict warnings triaged
- **Security:** bandit high-severity = 0; pip-audit criticals = 0
- **Docs:** link checker clean; OUTDATED_DOCS.md resolved
- **Runtime:** smoke tests green (HTTP 2xx, latency baseline ±20%)

---

## Notes & Blockers

### Access Limitations
- **tzdata module missing:** Cannot use zoneinfo for Europe/Athens timezone. Using UTC+2 offset instead.

### Workarounds Applied
- Timezone: Using `timezone(timedelta(hours=2))` instead of `zoneinfo.ZoneInfo('Europe/Athens')`

---

**Next Action:** Continue Phase 0 - record installed packages and create AUDIT_LOG.md

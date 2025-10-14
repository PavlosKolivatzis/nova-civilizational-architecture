# Nova Test Gaps Analysis

**Generated:** 2025-10-04
**Branch:** audit/system-cleanup-v1
**Baseline:** b4d1793
**Phase 1 Coverage:** 80% (Target: ≥85%)

---

## Executive Summary

**Current Coverage:** 80% overall (23,496 statements, 4,657 missed)
**Coverage Gap:** 5% below target
**Test Suite:** 858 passing, 6 skipped

**Critical Gaps:**
1. No contract metadata completeness validation
2. No integration tests for claimed but non-existent Slot 4 → Slot 6/7 links
3. No .env.example completeness validation
4. No single source of truth validation for duplicate slots
5. No CI quality gates (ruff, mypy, formatting)

---

## Coverage Gaps by Component

### Low Coverage Files (<85%)

| File | Coverage | Missed | Critical? |
|------|----------|--------|-----------|
| tools/fuzzy_loader.py | 84% | TBD | ❌ |
| tests/perf/test_health_perf.py | 81% | TBD | ❌ |
| tests/slot07/test_slot07_adapter_metrics.py | 81% | TBD | ❌ |

**Source:** phase1_summary.txt

**Recommendation:** Add tests to bring these files to ≥85%

---

## Missing Test Categories

### 1. Contract Metadata Validation

**Gap:** No test validates that all flow fabric contracts have metadata declarations

**Impact:** DEF-001 (6 out of 10 contracts missing metadata) was not caught

**Missing Tests:**
```python
def test_all_flow_fabric_contracts_have_metadata():
    """Verify every KNOWN_CONTRACTS entry has produces/consumes in meta.yaml"""
    from orchestrator.flow_fabric_init import KNOWN_CONTRACTS
    from pathlib import Path
    import yaml

    all_produces = set()
    for meta_file in Path('slots').rglob('*.meta.yaml'):
        data = yaml.safe_load(open(meta_file))
        all_produces.update(data.get('produces', []))

    for contract in KNOWN_CONTRACTS:
        assert contract in all_produces, f"{contract} missing from metadata"
```

**Evidence:** DRIFT_REPORT.md:141-153

---

### 2. Integration Tests for Claimed Functionality

**Gap:** No integration tests for Slot 4 → Slot 6/7 integrations

**Impact:** DEF-002 (false README claims) was not caught

**Missing Tests:**
```python
def test_slot04_tri_engine_integrates_with_slot06():
    """Verify slot04_tri_engine is imported/used by slot06"""
    # This test SHOULD FAIL because integration doesn't exist
    from nova.slots.slot06_cultural_synthesis import some_module
    assert 'slot04_tri_engine' in dir(some_module)

def test_slot04_tri_engine_integrates_with_slot07():
    """Verify slot04_tri_engine is imported/used by slot07"""
    # This test SHOULD FAIL because integration doesn't exist
    from nova.slots.slot07_production_controls import some_module
    assert 'slot04_tri_engine' in dir(some_module)
```

**Evidence:** DRIFT_REPORT.md:37-49, grep verification showed 0 imports

**Note:** These tests would FAIL today, proving README claims are false

---

### 3. Environment Variable Documentation Validation

**Gap:** No test validates .env.example completeness

**Impact:** DEF-005 (135/143 env vars undocumented) was not caught

**Missing Tests:**
```python
def test_env_example_documents_all_env_vars():
    """Verify .env.example contains all env vars used in code"""
    import re
    from pathlib import Path

    # Extract all env vars from code
    code_vars = set()
    for pyfile in Path('.').rglob('*.py'):
        if '.venv' not in str(pyfile):
            content = open(pyfile).read()
            code_vars.update(re.findall(r'os\.getenv\(["\']([^"\']+)', content))

    # Extract all env vars from .env.example
    with open('.env.example') as f:
        example_vars = set(re.findall(r'^([A-Z_]+)=', f.read(), re.MULTILINE))

    missing = code_vars - example_vars
    assert not missing, f"Undocumented env vars: {missing}"
```

**Evidence:** DRIFT_REPORT.md:228-238 (135/143 undocumented)

---

### 4. Single Source of Truth Validation

**Gap:** No test validates only one implementation exists for each slot

**Impact:** DEF-003, DEF-004 (duplicate Slot 4 and Slot 8) were not caught

**Missing Tests:**
```python
def test_only_one_slot04_implementation():
    """Verify only one Slot 4 implementation exists"""
    from pathlib import Path
    slot04_dirs = [d for d in Path('slots').iterdir()
                   if d.is_dir() and d.name.startswith('slot04')]
    assert len(slot04_dirs) == 1, f"Multiple Slot 4 implementations: {slot04_dirs}"

def test_only_one_slot08_implementation():
    """Verify only one Slot 8 implementation exists"""
    from pathlib import Path
    slot08_dirs = [d for d in Path('slots').iterdir()
                   if d.is_dir() and d.name.startswith('slot08')]
    assert len(slot08_dirs) == 1, f"Multiple Slot 8 implementations: {slot08_dirs}"
```

**Evidence:** DRIFT_REPORT.md:21-62 (Slot 4), DRIFT_REPORT.md:65-77 (Slot 8)

---

### 5. API Endpoint Uniqueness Validation

**Gap:** No test validates each endpoint is defined only once

**Impact:** DEF-011 (duplicate /metrics endpoint) was not caught

**Missing Tests:**
```python
def test_no_duplicate_api_endpoints():
    """Verify each API endpoint is defined exactly once"""
    import re
    from pathlib import Path
    from collections import Counter

    endpoints = []
    for pyfile in Path('orchestrator').rglob('*.py'):
        content = open(pyfile).read()
        # Extract @app.METHOD and @router.METHOD decorators
        endpoints.extend(re.findall(r'@(?:app|router)\.\w+\(["\']([^"\']+)', content))

    duplicates = {ep: count for ep, count in Counter(endpoints).items() if count > 1}
    assert not duplicates, f"Duplicate endpoints: {duplicates}"
```

**Evidence:** DRIFT_REPORT.md:196 (/metrics defined twice)

---

### 6. Documentation Link Integrity

**Gap:** No CI link checker for markdown files

**Impact:** DEF-012 (9 broken links) was not caught

**Missing Tests:**
```python
def test_all_markdown_links_valid():
    """Verify all local links in markdown files are valid"""
    import re
    from pathlib import Path

    broken_links = []
    for mdfile in Path('.').rglob('*.md'):
        if '.venv' in str(mdfile):
            continue
        content = open(mdfile).read()
        for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
            link = match.group(2)
            if link.startswith(('http', 'mailto:', '#')):
                continue
            link_path = mdfile.parent / link.split('#')[0]
            if not link_path.exists():
                broken_links.append((str(mdfile), link))

    assert not broken_links, f"Broken links: {broken_links}"
```

**Evidence:** DRIFT_REPORT.md:318-335 (9 broken links)

---

### 7. Documentation Staleness Detection

**Gap:** No automated staleness alerting for README files

**Impact:** DEF-013 (2 stale READMEs >30 days) was not caught

**Missing Tests:**
```python
def test_readmes_not_stale():
    """Verify README files are not >30 days stale relative to code"""
    import subprocess
    from pathlib import Path
    from datetime import datetime

    stale_docs = []
    for readme in Path('slots').rglob('README.md'):
        # Get last README update
        doc_result = subprocess.run(['git', 'log', '-1', '--format=%ci', str(readme)],
                                    capture_output=True, text=True)
        # Get last code update in same dir
        dir_result = subprocess.run(['git', 'log', '-1', '--format=%ci', str(readme.parent)],
                                    capture_output=True, text=True)

        if doc_result.stdout and dir_result.stdout:
            doc_date = datetime.fromisoformat(doc_result.stdout.strip().rsplit(' ', 1)[0])
            code_date = datetime.fromisoformat(dir_result.stdout.strip().rsplit(' ', 1)[0])
            lag_days = (code_date - doc_date).days

            if lag_days > 30:
                stale_docs.append((str(readme), lag_days))

    assert not stale_docs, f"Stale READMEs (>30d): {stale_docs}"
```

**Evidence:** DRIFT_REPORT.md:318-331 (slot04_tri_engine: 49d, slot08_memory_ethics: 48d)

---

### 8. Version Consistency Validation

**Gap:** No test validates single version string per slot

**Impact:** DEF-014 (Slot 2 has 3 different versions) was not caught

**Missing Tests:**
```python
def test_slot_version_consistency():
    """Verify each slot has exactly one canonical version"""
    import re
    from pathlib import Path

    for slot_dir in Path('slots').glob('slot*'):
        if not slot_dir.is_dir():
            continue

        versions = set()
        for pyfile in slot_dir.rglob('*.py'):
            content = open(pyfile).read()
            versions.update(re.findall(r'VERSION\s*=\s*["\']([^"\']+)', content))

        assert len(versions) <= 1, \
            f"{slot_dir.name} has multiple versions: {versions}"
```

**Evidence:** DRIFT_REPORT.md:151 (Slot 2: 1.0.0, 2.0.0, 6.5)

---

### 9. Security Scanning in CI

**Gap:** No CI gate for HIGH security findings

**Impact:** DEF-009 (1 HIGH severity bandit issue) reached main

**Missing CI Step:**
```yaml
# .github/workflows/quality.yml
- name: Security scan (bandit)
  run: |
    bandit -r orchestrator slots --severity-level=high --exit-zero
    bandit -r orchestrator slots --severity-level=high --format=json -o bandit.json
    python -c "import json; exit(1 if json.load(open('bandit.json'))['results'] else 0)"
```

**Evidence:** phase2_summary.txt (1 HIGH finding)

---

### 10. Quality Gates in CI

**Gap:** No CI gates for ruff, mypy, formatting

**Impact:** DEF-007 (249 ruff), DEF-008 (23 mypy), DEF-015 (325 format) issues accumulated

**Missing CI Steps:**
```yaml
# .github/workflows/quality.yml
- name: Lint (ruff)
  run: ruff check . --output-format=github

- name: Type check (mypy)
  run: mypy orchestrator slots --ignore-missing-imports

- name: Format check (ruff)
  run: ruff format --check .
```

**Evidence:** phase2_summary.txt

---

## Test Organization Gaps

### Missing Test Suites

| Category | Current Tests | Missing Coverage |
|----------|---------------|------------------|
| Contract validation | ❌ None | Metadata completeness, naming conventions |
| Integration tests | Partial | Slot-to-slot claimed integrations |
| Configuration tests | ❌ None | .env.example completeness |
| Architecture tests | ❌ None | Single implementation per slot |
| API tests | Basic | Endpoint uniqueness, duplicate detection |
| Documentation tests | ❌ None | Link integrity, staleness detection |
| Security tests | ❌ None | HIGH finding gates |
| Quality gates | ❌ None | Ruff, mypy, formatting in CI |

---

## Test Infrastructure Gaps

### Pre-commit Hooks

**Gap:** No pre-commit hooks enforcing quality

**Missing:**
- ruff check
- ruff format
- mypy (optional, warn only)

**Recommendation:** Create `.pre-commit-config.yaml`

### CI/CD Quality Gates

**Gap:** No quality gates in GitHub Actions

**Missing:**
- Ruff clean gate
- MyPy clean gate (or baseline)
- Bandit HIGH severity gate
- Link checker
- Coverage ≥85% gate

**Recommendation:** Create `.github/workflows/quality.yml`

---

## Property-Based Testing Gaps

**Current:** tests/property/ directory exists but coverage unknown

**Missing Property Tests:**
- Contract schema validation (any valid contract matches schema)
- Flow fabric routing (any valid message reaches destination)
- TRI calculation invariants (TRI always in [0,1])
- Semantic mirror TTL (expired entries always removed)

**Recommendation:** Expand hypothesis-based tests

---

## Remediation Priority

### P0 - Add Immediately
1. Contract metadata completeness test (prevents DEF-001)
2. Single implementation per slot test (prevents DEF-003, DEF-004)
3. No duplicate endpoints test (prevents DEF-011)

### P1 - Add This Sprint
4. .env.example completeness test (prevents DEF-005)
5. Link integrity test (prevents DEF-012)
6. HIGH security finding CI gate (prevents DEF-009)

### P2 - Add Next Sprint
7. Staleness detection test (prevents DEF-013)
8. Version consistency test (prevents DEF-014)
9. Ruff/mypy/format CI gates (prevents DEF-007, DEF-008, DEF-015)

### P3 - Add When Convenient
10. Property-based contract tests
11. Chaos engineering for ANR
12. Performance regression tests

---

## Coverage Improvement Plan

**Goal:** Increase from 80% to ≥85%

**Actions:**
1. Add missing tests from this document (estimated +3% coverage)
2. Test uncovered branches in fuzzy_loader.py (+1%)
3. Add edge case tests for slot adapters (+1%)
4. Test error paths in health checks (+0.5%)

**Timeline:** 1 sprint

**Rollback:** If coverage drops, CI fails (add coverage gate)

---

**Status:** TEST_GAPS.md COMPLETE
**Next:** RISK_REGISTER.md
**Evidence:** phase1_summary.txt, DRIFT_REPORT.md, DEFECTS_REGISTER.yml

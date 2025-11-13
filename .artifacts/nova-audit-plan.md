# Nova Civilizational Architecture — Stability & Security Audit Plan

**Status**: Draft
**Created**: 2025-11-13
**Purpose**: Systematic audit to increase stability, detect vulnerabilities, identify unused code, and optimize configuration

---

## Audit Principles (Following Nova Doctrine)

1. **Observable**: All findings → Prometheus metrics or audit logs
2. **Reversible**: Test in shadow mode before enabling
3. **Provenance**: Hash-linked attestation of findings
4. **Separation**: Audit by layer (Core → Governors → Slots)
5. **Sunlight**: No hidden assumptions, document everything

---

## Phase 1: Automated Discovery (Safe, Fast)

### 1.1 Feature Flag Inventory

**Goal**: Document all NOVA_* environment variables and their current state

**Commands**:
```bash
# Extract all NOVA_* environment variables from codebase
grep -rh "NOVA_[A-Z_]*" --include="*.py" --include="*.md" src/ orchestrator/ | \
  grep -oE "NOVA_[A-Z_]+" | sort -u > .artifacts/audit_flags_found.txt

# Check which are documented
grep -rh "NOVA_[A-Z_]*" docs/ README.md CLAUDE.md | \
  grep -oE "NOVA_[A-Z_]+" | sort -u > .artifacts/audit_flags_documented.txt

# Find undocumented flags
comm -23 .artifacts/audit_flags_found.txt .artifacts/audit_flags_documented.txt
```

**Output**: List of undocumented flags requiring documentation

---

### 1.2 Dead Code Detection

**Goal**: Find unused imports, functions, classes

**Tools**:
- `vulture` - Detects unused code
- `coverage` - Identifies untested code paths

**Commands**:
```bash
# Install tools
pip install vulture coverage

# Run vulture (detects unused code)
vulture src/ orchestrator/ --min-confidence 80 > .artifacts/audit_dead_code.txt

# Check test coverage
pytest --cov=src --cov=orchestrator --cov-report=term-missing \
  --cov-report=json:.artifacts/audit_coverage.json -q

# Find files with <80% coverage
python -c "
import json
with open('.artifacts/audit_coverage.json') as f:
    data = json.load(f)
    for file, metrics in data['files'].items():
        pct = metrics['summary']['percent_covered']
        if pct < 80:
            print(f'{file}: {pct:.1f}%')
" > .artifacts/audit_low_coverage.txt
```

**Output**:
- `.artifacts/audit_dead_code.txt` - Unused code candidates
- `.artifacts/audit_low_coverage.txt` - Files needing more tests

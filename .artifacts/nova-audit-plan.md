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

---

### 1.3 Dependency Audit

**Goal**: Find vulnerable dependencies, outdated packages

**Commands**:
```bash
# Audit dependencies for known vulnerabilities
pip install pip-audit
pip-audit --format json > .artifacts/audit_dependencies.json

# Check for outdated packages
pip list --outdated --format json > .artifacts/audit_outdated.json

# Verify requirements.txt matches installed
pip freeze > .artifacts/audit_installed.txt
diff requirements.txt .artifacts/audit_installed.txt > .artifacts/audit_dep_drift.txt || true
```

**Output**: CVE findings, version drift

---

### 1.4 Import Cycle Detection

**Goal**: Find circular imports (like the orchestrator.app issue we just fixed)

**Commands**:
```bash
# Install pydeps
pip install pydeps

# Generate dependency graph (will show cycles)
pydeps src/nova --max-bacon=2 --cluster --show-cycles \
  -o .artifacts/audit_import_cycles.svg 2>&1 | grep -i cycle || echo "No cycles detected"

# Manual check with Python
python -c "
import sys
sys.path.insert(0, 'src')
sys.path.insert(0, 'orchestrator')
import importlib
import pkgutil

def find_cycles(package_name):
    try:
        pkg = importlib.import_module(package_name)
        for importer, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + '.'):
            try:
                importlib.import_module(modname)
            except ImportError as e:
                if 'circular' in str(e).lower():
                    print(f'Cycle: {modname} - {e}')
    except Exception as e:
        print(f'Error scanning {package_name}: {e}')

find_cycles('nova')
" > .artifacts/audit_import_cycles.txt 2>&1
```

**Output**: List of circular import risks

---

## Phase 2: Configuration Audit

### 2.1 Environment Variable Documentation

**Goal**: Document every NOVA_* flag with default, purpose, impact

**Method**: Generate inventory table

**Script**:
```python
# .artifacts/audit_config_inventory.py
import os
import re
from pathlib import Path

flags = {}

# Scan all Python files
for fpath in Path('src').rglob('*.py'):
    content = fpath.read_text(encoding='utf-8', errors='ignore')
    matches = re.finditer(r'os\.getenv\(["\']([A-Z_]+)["\']\s*,\s*["\']([^"\']+)["\']', content)
    for m in matches:
        var, default = m.groups()
        if var.startswith('NOVA_'):
            if var not in flags:
                flags[var] = {'default': default, 'files': []}
            flags[var]['files'].append(str(fpath))

# Output as markdown table
print("| Flag | Default | Files | Documented? |")
print("|------|---------|-------|-------------|")
for var, info in sorted(flags.items()):
    files = ', '.join(set(info['files']))
    print(f"| {var} | `{info['default']}` | {files[:50]}... | ❌ |")
```

**Output**: `.artifacts/audit_config_inventory.md` - Full flag inventory

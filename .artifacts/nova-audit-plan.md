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

---

### 2.2 Threshold Review

**Goal**: Validate all hardcoded thresholds have rationale

**Files to audit**:
- `src/nova/slots/slot07_production_controls/wisdom_backpressure.py` - Job caps (16/6/2), threshold (0.03)
- `src/nova/governor/adaptive_wisdom_governor.py` - Learning rates, stability margins
- `orchestrator/federation_remediator.py` - Backoff intervals
- All `rules.yaml` files - Reflex thresholds

**Questions for each threshold**:
1. What happens if doubled? Halved?
2. Is it configurable via env var?
3. Is there a Prometheus metric for it?
4. Is it documented?

**Output**: `.artifacts/audit_thresholds.md` - Threshold inventory with risk assessment

---

### 2.3 Default State Audit

**Goal**: Verify safe defaults (fail-closed, not fail-open)

**Check**:
```bash
# Find all default="1" (enabled by default - risky)
grep -rn 'getenv.*default.*"1"' src/ orchestrator/ > .artifacts/audit_defaults_enabled.txt

# Find all default="0" (disabled by default - safe)
grep -rn 'getenv.*default.*"0"' src/ orchestrator/ > .artifacts/audit_defaults_disabled.txt

# Count ratio
wc -l .artifacts/audit_defaults_*.txt
```

**Principle**: New features should default OFF, require explicit enable

**Output**: List of features enabled by default (review for safety)

---

## Phase 3: Security Scan (OWASP Top 10)

### 3.1 Dependency Vulnerabilities

**Already covered in Phase 1.3** (pip-audit)

---

### 3.2 Authentication & Authorization

**Goal**: Verify JWT handling, no hardcoded secrets

**Checks**:
```bash
# Find hardcoded secrets (patterns)
grep -rn -E "(password|secret|token|key)\s*=\s*['\"][^'\"]{8,}" src/ orchestrator/ \
  --exclude-dir=__pycache__ > .artifacts/audit_hardcoded_secrets.txt || echo "None found"

# Verify JWT_SECRET not hardcoded
grep -rn "JWT_SECRET.*=" src/ orchestrator/ | grep -v "getenv" || echo "Safe"

# Check for weak crypto
grep -rn "md5\|sha1" src/ orchestrator/ > .artifacts/audit_weak_crypto.txt || echo "None found"
```

**Output**: Potential secret leaks, weak algorithms

---

### 3.3 Input Validation

**Goal**: Prevent injection attacks (SQL, command, XSS)

**Manual review files**:
- `orchestrator/app.py` - All FastAPI endpoints
- `src/nova/slots/*/endpoints.py` - Slot-specific APIs
- Any `subprocess.run()` or `os.system()` calls

**Checks**:
```bash
# Find dangerous patterns
grep -rn "os.system\|subprocess.call\|eval\|exec" src/ orchestrator/ \
  > .artifacts/audit_dangerous_calls.txt || echo "None found"

# Find SQL (we don't use SQL, but check anyway)
grep -rn "execute.*SELECT\|INSERT\|UPDATE" src/ orchestrator/ \
  > .artifacts/audit_sql.txt || echo "None found (expected)"

# Find user input passed to shell
grep -rn "subprocess.*shell=True" src/ orchestrator/ \
  > .artifacts/audit_shell_injection_risk.txt || echo "None found"
```

**Output**: Injection risk points requiring validation

---

### 3.4 Rate Limiting & DoS Protection

**Goal**: Verify all public endpoints have rate limits

**Check**:
```bash
# Find endpoints without rate limiting
python -c "
import ast
from pathlib import Path

endpoints = []
for fpath in Path('orchestrator').rglob('*.py'):
    try:
        tree = ast.parse(fpath.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Call):
                        if hasattr(decorator.func, 'attr') and 'get' in decorator.func.attr.lower():
                            # Found a route decorator
                            has_limiter = any('limit' in ast.unparse(d).lower() for d in node.decorator_list)
                            if not has_limiter:
                                endpoints.append(f'{fpath}:{node.lineno} - {node.name}')
    except:
        pass

for ep in endpoints:
    print(ep)
" > .artifacts/audit_unlimited_endpoints.txt
```

**Output**: Endpoints needing rate limits

---

### 3.5 Secret Management

**Goal**: No secrets in git, all secrets via env vars

**Checks**:
```bash
# Check .gitignore covers sensitive files
cat .gitignore | grep -E "\.env|secret|credential|key" || echo "Add to .gitignore"

# Find .env files accidentally committed
git log --all --full-history -- "*.env" > .artifacts/audit_env_in_git.txt || echo "None found"

# Check for API keys in code
grep -rn -E "['\"]sk-[a-zA-Z0-9]{32,}['\"]" src/ orchestrator/ \
  > .artifacts/audit_api_keys.txt || echo "None found"
```

**Output**: Secret management gaps

---

## Phase 4: Observability Verification

### 4.1 Prometheus Metrics Coverage

**Goal**: Every critical path has metrics

**Check**:
```bash
# Extract all metric names
curl -s localhost:8000/metrics | grep "^nova_" | cut -d' ' -f1 | sort -u \
  > .artifacts/audit_metrics_exported.txt

# Find all metric definitions in code
grep -rh "Gauge\|Counter\|Histogram" src/ orchestrator/ | \
  grep -oE '"nova_[a-z_]+"' | sort -u > .artifacts/audit_metrics_defined.txt

# Find metrics defined but not exported
comm -13 .artifacts/audit_metrics_exported.txt .artifacts/audit_metrics_defined.txt
```

**Output**: Metrics defined but never exported (dead code)

---

### 4.2 Health Endpoint Completeness

**Goal**: /health returns all critical system state

**Current coverage** (from federation_health.py):
- ✅ Federation ready
- ✅ Peer count
- ✅ Ledger height
- ✅ Peer sync status
- ❓ Wisdom governor state
- ❓ Circuit breaker state
- ❓ Slot maturity levels

**Check**:
```bash
# Query health endpoint
curl -s localhost:8000/health | jq . > .artifacts/audit_health_current.json

# Compare to desired state
python -c "
import json
desired = {
    'federation': ['ready', 'peers', 'ledger'],
    'wisdom': ['gamma', 'frozen', 'stability_margin'],
    'slot07': ['breaker_state', 'backpressure', 'jobs_current'],
    'semantic_mirror': ['key_count', 'slot_states']
}
with open('.artifacts/audit_health_current.json') as f:
    current = json.load(f)

# Find missing keys
for section, keys in desired.items():
    for key in keys:
        path = f'{section}.{key}'
        # Simplified check
        print(f'Checking: {path}')
" > .artifacts/audit_health_gaps.txt
```

**Output**: Missing health checks

---

### 4.3 Audit Log Coverage

**Goal**: All state changes logged with trace_id

**Check**:
```bash
# Find state-changing functions without logging
grep -rn "def.*set_\|def.*update_\|def.*delete_" src/ orchestrator/ | \
  while read line; do
    file=$(echo "$line" | cut -d: -f1)
    lineno=$(echo "$line" | cut -d: -f2)
    # Check if file has logger.info/warning near that line
    context=$(sed -n "$((lineno-5)),$((lineno+20))p" "$file")
    if ! echo "$context" | grep -q "logger\|logging"; then
      echo "$line - NO LOGGING"
    fi
  done > .artifacts/audit_unlogged_mutations.txt
```

**Output**: State changes without audit trail

---

## Phase 5: Code Quality Analysis

### 5.1 Type Coverage

**Goal**: Increase type hint coverage to 95%+

**Commands**:
```bash
# Install mypy
pip install mypy

# Run strict type checking
mypy src/ orchestrator/ --strict --ignore-missing-imports \
  --html-report .artifacts/mypy_report 2>&1 | tee .artifacts/audit_type_errors.txt

# Count files with type issues
grep -c "error:" .artifacts/audit_type_errors.txt || echo "0"
```

**Output**: Type errors requiring fixes

---

### 5.2 Complexity Metrics

**Goal**: Identify functions needing refactoring (cyclomatic complexity > 10)

**Commands**:
```bash
# Install radon
pip install radon

# Find complex functions
radon cc src/ orchestrator/ -a -nc -s > .artifacts/audit_complexity.txt

# Extract high-complexity functions (grade C or worse)
grep -E "^[A-Z] " .artifacts/audit_complexity.txt | grep -v "^A \|^B " \
  > .artifacts/audit_high_complexity.txt
```

**Output**: Functions to refactor

---

### 5.3 Documentation Coverage

**Goal**: All public functions have docstrings

**Commands**:
```bash
# Install interrogate
pip install interrogate

# Check docstring coverage
interrogate src/ orchestrator/ -v --fail-under=80 \
  --generate-badge .artifacts/audit_docstring_badge.svg \
  > .artifacts/audit_docstrings.txt 2>&1
```

**Output**: Functions missing docstrings

---

## Phase 6: Attestation Report Generation

### 6.1 Aggregate Findings

**Script**: `.artifacts/generate_audit_attestation.py`

```python
"""Generate hash-linked audit attestation."""
import json
import hashlib
from datetime import datetime
from pathlib import Path

findings = {
    "timestamp": datetime.utcnow().isoformat(),
    "phase": "7.0-audit",
    "categories": {
        "flags": {"undocumented": 0, "total": 0},
        "security": {"high": 0, "medium": 0, "low": 0},
        "code_quality": {"dead_code_items": 0, "complexity_issues": 0},
        "observability": {"missing_metrics": 0, "missing_health_keys": 0},
        "configuration": {"unsafe_defaults": 0, "undocumented_thresholds": 0}
    },
    "files_scanned": 0,
    "provenance": {
        "git_commit": "",  # Fill from git rev-parse HEAD
        "scanner_version": "1.0.0",
        "hash_method": "sha256"
    }
}

# Load individual audit files and aggregate
audit_dir = Path('.artifacts')
for fpath in audit_dir.glob('audit_*.txt'):
    line_count = len(fpath.read_text().strip().split('\n'))
    if 'flags' in fpath.name:
        findings['categories']['flags']['undocumented'] = line_count
    # ... more aggregation logic

# Compute hash of findings (excluding hash field itself)
canonical = json.dumps(findings, sort_keys=True)
findings['attestation_hash'] = hashlib.sha256(canonical.encode()).hexdigest()

# Write attestation
output = audit_dir / f"audit_attestation_{datetime.utcnow().strftime('%Y%m%d')}.json"
output.write_text(json.dumps(findings, indent=2))
print(f"Attestation: {output}")
```

**Output**: `.artifacts/audit_attestation_YYYYMMDD.json`

---

### 6.2 Remediation Roadmap

**Based on findings severity**:

1. **Critical (fix immediately)**:
   - CVE vulnerabilities in dependencies
   - Hardcoded secrets
   - Command injection risks

2. **High (fix this sprint)**:
   - Missing authentication
   - Unvalidated inputs
   - Missing rate limits

3. **Medium (fix next sprint)**:
   - Dead code removal
   - High complexity functions
   - Missing docstrings

4. **Low (backlog)**:
   - Type hint improvements
   - Outdated dependencies (no CVE)

**Output**: `.artifacts/audit_remediation_roadmap.md`

---

## Execution Plan (Recommended Order)

### Day 1: Safe Automated Scans
```bash
# Run all Phase 1 commands (no risk, read-only)
bash .artifacts/run_phase1_audit.sh
```

### Day 2: Configuration Review
```bash
# Run Phase 2 (documentation audit)
python .artifacts/audit_config_inventory.py > .artifacts/audit_config_inventory.md
```

### Day 3: Security Deep-Dive
```bash
# Run Phase 3 (manual review + automated scans)
bash .artifacts/run_phase3_security.sh
```

### Day 4: Observability Check
```bash
# Run Phase 4 (requires orchestrator running)
bash .artifacts/run_phase4_observability.sh
```

### Day 5: Attestation & Roadmap
```bash
# Generate final report
python .artifacts/generate_audit_attestation.py
```

---

## Rollback

All audit scripts are **read-only** and safe. No code changes during audit phase.

If audit tooling causes issues:
```bash
pip uninstall vulture radon interrogate pydeps pip-audit -y
rm -rf .artifacts/audit_*
```

---

## Success Criteria

1. ✅ All NOVA_* flags documented with defaults
2. ✅ Zero critical CVEs in dependencies
3. ✅ Zero hardcoded secrets
4. ✅ <5% dead code by LOC
5. ✅ >80% test coverage on src/
6. ✅ All public endpoints rate-limited
7. ✅ All state changes logged
8. ✅ <10 high-complexity functions
9. ✅ Attestation report generated with SHA-256 hash

---

**Next Step**: Review this plan, then execute Phase 1 (safe, automated).

**Estimated Time**: 5 days (1 phase per day)

**Risk**: Low (read-only scans, no production changes)

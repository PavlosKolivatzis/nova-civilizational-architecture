# Phase 17: Secret Scanning Enhancement - Continuation

**Session End**: 2025-11-15 (auto-compact issue)
**Context**: Nova-enhanced secret scanning implementation 95% complete
**Status**: Tools created, baseline generated, needs final steps

---

## Work Completed ✅

### 1. Tools Created
- ✅ `tools/classify_secrets.py` - Risk classification with OWASP patterns (267 lines)
- ✅ `tools/attest_secrets_baseline.py` - BLAKE2b hash attestation (235 lines)
- ✅ Prometheus metrics added to `orchestrator/prometheus_metrics.py`

### 2. Baseline Generated
- ✅ `.secrets.baseline` - 45,947 lines, 5,723 findings
- ✅ `.artifacts/secrets-audit.md` - Risk-classified report
  - 🔴 48 CRITICAL (mostly .venv/ package metadata - false positives)
  - 🟡 5,669 MEDIUM
  - ⚪ 6 INFO (docs/tests)

### 3. Known Issue: Windows Emoji Encoding
**Problem**: `attest_secrets_baseline.py` has emoji in print statements → UnicodeEncodeError on Windows
**Fix needed**: Replace emoji with ASCII in print statements

---

## Next Steps (15 minutes)

### Step 1: Fix Emoji Encoding in Attestation Tool

**File**: `tools/attest_secrets_baseline.py`

**Lines to change**:
- Line 203: `print(f"✅ Baseline attested:` → `print(f"[OK] Baseline attested:`
- Line 204: `print(f"📝 Attestation:` → `print(f"[INFO] Attestation:`
- Line 205: `print(f"📊 Statistics:` → `print(f"[STATS] Statistics:`
- Line 218: `print("✅ Baseline matches` → `print("[OK] Baseline matches`
- Line 222: `print("❌ Baseline does NOT` → `print("[ERROR] Baseline does NOT`
- Line 226: `print(f"❌ Error:` → `print(f"[ERROR] Error:`

**Quick fix command**:
```bash
cd /c/code/nova-civilizational-architecture

# Replace all emoji in attest tool
python -c "
from pathlib import Path
content = Path('tools/attest_secrets_baseline.py').read_text()
content = content.replace('✅', '[OK]')
content = content.replace('📝', '[INFO]')
content = content.replace('📊', '[STATS]')
content = content.replace('❌', '[ERROR]')
Path('tools/attest_secrets_baseline.py').write_text(content)
print('Fixed emoji encoding issues')
"
```

### Step 2: Create Attestation

```bash
cd /c/code/nova-civilizational-architecture
python tools/attest_secrets_baseline.py create
```

**Expected output**:
```
[OK] Baseline attested: a1b2c3d4e5f6g7h8...
[INFO] Attestation: .artifacts/secrets-baseline-attestation.json
[STATS] Statistics:
   - Files scanned: 2847
   - Findings: 5723
   - Plugins: 15
```

### Step 3: Verify Attestation

```bash
python tools/attest_secrets_baseline.py verify
```

**Expected**: `[OK] Baseline matches attestation - integrity verified`

### Step 4: Test Metrics Endpoint

```bash
# Check if orchestrator is running
curl -s http://localhost:8000/metrics | grep -E "nova_secrets"
```

**Expected metrics**:
```
nova_secrets_baseline_findings_total{risk_level="CRITICAL"} 48.0
nova_secrets_baseline_findings_total{risk_level="HIGH"} 0.0
nova_secrets_baseline_findings_total{risk_level="MEDIUM"} 5669.0
nova_secrets_baseline_findings_total{risk_level="LOW"} 0.0
nova_secrets_baseline_findings_total{risk_level="INFO"} 6.0
nova_secrets_scan_timestamp <unix_timestamp>
nova_secrets_baseline_info{...} 1
```

**If metrics not showing**: Restart orchestrator or wait for next `/metrics` call (they load on-demand).

### Step 5: Commit Everything

```bash
git status
# Should show:
#   modified: orchestrator/prometheus_metrics.py
#   new file: tools/classify_secrets.py
#   new file: tools/attest_secrets_baseline.py
#   new file: .secrets.baseline
#   new file: .artifacts/secrets-audit.md
#   new file: .artifacts/secrets-baseline-attestation.json

git add orchestrator/prometheus_metrics.py \
        tools/classify_secrets.py \
        tools/attest_secrets_baseline.py \
        .secrets.baseline \
        .artifacts/secrets-audit.md \
        .artifacts/secrets-baseline-attestation.json

git commit -m "$(cat <<'EOF'
feat(security): Phase 17 - Nova-enhanced secret scanning

Implements comprehensive secret scanning with risk classification,
hash-based attestation, and Prometheus observability.

Changes:
- tools/classify_secrets.py: OWASP-aligned risk classification
  (CRITICAL/HIGH/MEDIUM/LOW/INFO with file pattern analysis)
- tools/attest_secrets_baseline.py: BLAKE2b hash attestation
  for tamper-evident audit trail
- orchestrator/prometheus_metrics.py: Phase 17 metrics
  - nova_secrets_baseline_findings_total (by risk level)
  - nova_secrets_baseline_info (hash, timestamp, counts)
  - nova_secrets_scan_timestamp (unix timestamp)

Baseline scan results:
- Total findings: 5,723
- Critical: 48 (mostly .venv false positives)
- Medium: 5,669
- Info: 6 (docs/tests)

Sunlight principle: All findings classified, documented, and attested.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

git log -1 --stat
```

---

## File Reference

### Created Files

1. **`tools/classify_secrets.py`** (267 lines)
   - Purpose: Risk classification of secret findings
   - Usage: `python tools/classify_secrets.py .secrets.baseline -o .artifacts/secrets-audit.md`
   - Patterns: CRITICAL (api_key, password), HIGH (jwt, oauth), MEDIUM (hash, salt), LOW (test, demo)
   - Output: Markdown report with remediation guidance

2. **`tools/attest_secrets_baseline.py`** (235 lines)
   - Purpose: Hash-based attestation for baseline integrity
   - Usage: `python tools/attest_secrets_baseline.py create`
   - Algorithm: BLAKE2b-512
   - Output: `.artifacts/secrets-baseline-attestation.json`

3. **`.secrets.baseline`** (45,947 lines)
   - Purpose: detect-secrets baseline (all findings)
   - Generated: `python -m detect_secrets scan --all-files > .secrets.baseline`
   - Format: JSON with hashed secrets

4. **`.artifacts/secrets-audit.md`**
   - Purpose: Human-readable risk report
   - Sections: Risk summary, findings by level, remediation guide
   - Encoding: UTF-8 (contains emoji)

5. **`.artifacts/secrets-baseline-attestation.json`**
   - Purpose: Tamper-evident attestation record
   - Fields: baseline_hash, timestamp, statistics, attested_by
   - Usage: Verify with `python tools/attest_secrets_baseline.py verify`

### Modified Files

1. **`orchestrator/prometheus_metrics.py`**
   - Added: Lines 291-309 (Phase 17 metric definitions)
   - Added: Lines 596-645 (update_secrets_baseline_metrics function)
   - Modified: Line 656 (added update_secrets_baseline_metrics() call)

---

## Known Issues & Triage

### Critical Findings (48)

**All in `.venv/` directory** - Package metadata, not actual secrets:
- `.venv/Lib/site-packages/PyJWT-*/METADATA` - "JSON Web Token" string
- `.venv/Lib/site-packages/alembic/context.pyi` - Comments mentioning "password"

**Action**: Exclude `.venv/` from future scans:
```bash
# Re-scan excluding .venv
python -m detect_secrets scan --all-files \
  --exclude-files '\.venv/.*' \
  > .secrets.baseline
```

**OR** add to `.secrets.baseline` exclude list and regenerate report.

### Medium Findings (5,669)

Mostly legitimate patterns in:
- Tests (test secrets, mock credentials)
- Docs (example configurations)
- Audit artifacts (historical insecure configs documented for safety)

**Action**: Review `.artifacts/secrets-audit.md` and add pragma comments where appropriate.

---

## Architecture Notes

### Nova Enhancements vs. Standard Approach

**Standard**:
- Run detect-secrets
- Review baseline manually
- Suppress false positives

**Nova-Enhanced**:
1. **Risk Classification**: OWASP-aligned severity levels with file pattern analysis
2. **Attestation**: BLAKE2b hash-linked to prevent baseline tampering
3. **Observability**: Prometheus metrics expose scan health in dashboards
4. **Provenance**: Pragma comments require WHY explanation, not just suppression
5. **Integration**: Metrics update on every `/metrics` scrape

### Sunlight Principle Compliance

- ✅ All findings visible and classified
- ✅ Attestation provides tamper evidence
- ✅ Metrics make scan status observable
- ✅ Remediation guidance documents safe practices
- ✅ Pragma comments require provenance explanation

---

## Testing

### Quick Validation

```bash
cd /c/code/nova-civilizational-architecture

# 1. Verify tools work
python tools/classify_secrets.py --help
python tools/attest_secrets_baseline.py --help

# 2. Verify baseline exists
wc -l .secrets.baseline  # Should be ~45,947

# 3. Verify report exists
head -20 .artifacts/secrets-audit.md

# 4. Verify metrics load
curl -s http://localhost:8000/metrics | grep nova_secrets | head -10

# 5. Test attestation verification
python tools/attest_secrets_baseline.py verify
```

### Expected Test Results

All commands should succeed with no errors. Metrics should show:
- 48 CRITICAL findings
- 5,669 MEDIUM findings
- 6 INFO findings
- Timestamp matching scan time

---

## Rollback

If issues arise:

```bash
# Remove generated files
rm .secrets.baseline
rm .artifacts/secrets-audit.md
rm .artifacts/secrets-baseline-attestation.json

# Revert code changes
git checkout HEAD -- orchestrator/prometheus_metrics.py
git clean -f tools/classify_secrets.py tools/attest_secrets_baseline.py

# Restart orchestrator if metrics causing issues
# (kill uvicorn process and restart)
```

---

## Future Enhancements (Optional)

### 1. Exclude .venv from Scans

**File**: `.pre-commit-config.yaml`

Add exclude pattern:
```yaml
- repo: https://github.com/Yelp/detect-secrets
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
      exclude: '^\.venv/.*$'
```

### 2. CI Validation

**File**: `.github/workflows/secrets-validation.yml`

Ensure no new secrets in PRs:
```yaml
- name: Scan for new secrets
  run: |
    python -m detect_secrets scan --baseline .secrets.baseline \
      --exclude-files '\.venv/.*' --all-files
```

### 3. Dashboard

Add Grafana panel for `nova_secrets_baseline_findings_total` to monitor scan health.

---

## Quick Start (New Session)

```bash
cd /c/code/nova-civilizational-architecture

# 1. Fix emoji encoding
python -c "
from pathlib import Path
content = Path('tools/attest_secrets_baseline.py').read_text()
content = content.replace('✅', '[OK]').replace('📝', '[INFO]')
content = content.replace('📊', '[STATS]').replace('❌', '[ERROR]')
Path('tools/attest_secrets_baseline.py').write_text(content)
print('Fixed')
"

# 2. Create attestation
python tools/attest_secrets_baseline.py create

# 3. Verify
python tools/attest_secrets_baseline.py verify

# 4. Test metrics
curl -s http://localhost:8000/metrics | grep nova_secrets

# 5. Commit
git add -A
git commit -m "feat(security): Phase 17 - Nova-enhanced secret scanning"
git push
```

**Time**: 5-10 minutes to complete.

---

**Status**: Ready to finalize Phase 17 in new session.
**Priority**: Low urgency (audit complete, this is enhancement)
**Benefit**: Observable, attested secret scanning with risk classification

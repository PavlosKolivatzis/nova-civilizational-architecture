# Phase 7.0-RC Steps 6-7 Design Document

**Status:** Design Phase
**Dependencies:** Steps 1-5 complete (Memory Window, RIS, Stress, Attestation, Monitoring)
**Target:** Production promotion via `v7.0-rc-complete` tag

---

## Current State

**Completed (Steps 1-5):**
- ✅ Memory Resonance Window (7-day TRSI rolling stability)
- ✅ RIS Calculator (sqrt(M_s × E_c) composite trust metric)
- ✅ Stress Simulation (drift injection + recovery measurement)
- ✅ RC Attestation (immutable SHA-256 signed records)
- ✅ Prometheus Monitoring (13 gauges for observability)
- ✅ E2E Validation (all RC criteria passing)

**Artifacts Generated:**
- `attest/phase-7.0-rc_20250121.json` (manual attestation)
- `attest/phase-7.0-rc_e2e_validation.json` (E2E validation attestation)
- `scripts/validate_rc_e2e.py` (validation script)
- 1685 tests passing (13 new metrics tests)

**RC Criteria Status:**
- Memory stability: 0.823 ≥ 0.80 ✓
- RIS score: 0.907 ≥ 0.75 ✓
- Stress recovery: 0.950 ≥ 0.90 ✓
- Samples: 48 ≥ 24 ✓
- **Overall: PASS**

---

## Step 6: CI/CD Integration

**Goal:** Automate weekly RC validation in GitHub Actions

### 6.1 Existing Workflow Analysis

**File:** `.github/workflows/temporal-resonance-validation.yml`

**Current capabilities:**
- Daily TRSI computation (lines 39-74)
- Weekly RC memory analysis (lines 169-236)
- RC promotion criteria validation (lines 238-267)

**Gaps:**
- No memory window population (currently placeholder)
- No RIS computation integration
- No stress simulation execution
- No attestation generation
- No Prometheus metrics collection

### 6.2 Workflow Enhancements

#### Option A: Extend Existing Workflow (Recommended)

Modify `temporal-resonance-validation.yml` to add RC validation job:

```yaml
  rc-validation:
    name: "RC Validation (Weekly)"
    runs-on: ubuntu-latest
    if: github.event.schedule == '0 10 * * 1'  # Monday 10:00 UTC
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run E2E RC validation
        run: |
          python scripts/validate_rc_e2e.py

      - name: Upload attestation artifact
        if: success()
        uses: actions/upload-artifact@v4
        with:
          name: rc-attestation-${{ github.run_id }}
          path: attest/phase-7.0-rc_e2e_validation.json

      - name: Check RC criteria
        run: |
          RC_PASS=$(jq -r '.rc_criteria.overall_pass' attest/phase-7.0-rc_e2e_validation.json)
          if [ "$RC_PASS" != "true" ]; then
            echo "❌ RC validation failed"
            exit 1
          fi
          echo "✅ RC validation passed"
```

**Pros:**
- Minimal changes (1 new job)
- Reuses existing infrastructure
- Weekly cadence matches 7-day memory window

**Cons:**
- Runs in CI environment (no persistent memory window)
- Requires synthetic data or mocking

#### Option B: Standalone RC Workflow

Create `.github/workflows/rc-validation.yml`:

```yaml
name: "RC Validation"

on:
  schedule:
    - cron: '0 10 * * 1'  # Monday 10:00 UTC (weekly)
  workflow_dispatch:  # Manual trigger

jobs:
  validate-rc:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run RC validation
        id: rc_validation
        run: |
          python scripts/validate_rc_e2e.py | tee rc_validation.log
          echo "exit_code=$?" >> $GITHUB_OUTPUT

      - name: Parse results
        run: |
          MEMORY=$(grep "Memory Window:" rc_validation.log | awk '{print $5}')
          RIS=$(grep "RIS Calculator:" rc_validation.log | awk '{print $3}')
          STRESS=$(grep "Stress Simulation:" rc_validation.log | awk '{print $3}')

          echo "memory_stability=$MEMORY" >> $GITHUB_ENV
          echo "ris_score=$RIS" >> $GITHUB_ENV
          echo "stress_recovery=$STRESS" >> $GITHUB_ENV

      - name: Create attestation summary
        run: |
          cat <<EOF > $GITHUB_STEP_SUMMARY
          ## Phase 7.0-RC Validation Results

          | Metric | Value | Threshold | Status |
          |--------|-------|-----------|--------|
          | Memory Stability | ${{ env.memory_stability }} | ≥0.80 | ✅ |
          | RIS Score | ${{ env.ris_score }} | ≥0.75 | ✅ |
          | Stress Recovery | ${{ env.stress_recovery }} | ≥0.90 | ✅ |

          **Overall:** PASS

          Attestation: \`attest/phase-7.0-rc_e2e_validation.json\`
          EOF

      - name: Upload attestation
        uses: actions/upload-artifact@v4
        with:
          name: rc-attestation-${{ github.sha }}
          path: attest/phase-7.0-rc_e2e_validation.json
          retention-days: 90

      - name: Fail if RC criteria not met
        if: steps.rc_validation.outputs.exit_code != '0'
        run: exit 1
```

**Pros:**
- Dedicated workflow for RC validation
- Clear separation of concerns
- GitHub summary with results table
- 90-day artifact retention

**Cons:**
- New workflow file to maintain
- Potential duplication with existing workflow

### 6.3 Recommended Approach

**Use Option B** (standalone workflow) with these additions:

1. **Manual trigger:** Allow `workflow_dispatch` for on-demand validation
2. **Slack/Discord notification:** Post RC results to team channel
3. **PR comment:** If triggered by PR, comment results
4. **Metrics export:** Publish RC metrics to GitHub Pages dashboard

### 6.4 Implementation Plan

**File:** `.github/workflows/rc-validation.yml`

```yaml
name: "Phase 7.0-RC Validation"

on:
  schedule:
    - cron: '0 10 * * 1'  # Weekly Monday 10:00 UTC
  workflow_dispatch:
    inputs:
      manual_trigger:
        description: 'Manual RC validation'
        required: false
        default: 'true'

env:
  PYTHON_VERSION: '3.13'

jobs:
  rc-validation:
    name: "Validate RC Criteria"
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python ${{ env.PYTHON_VERSION }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run RC E2E validation
        id: validate
        run: |
          echo "Starting Phase 7.0-RC validation..."
          python scripts/validate_rc_e2e.py | tee rc_validation.log
          EXIT_CODE=${PIPESTATUS[0]}
          echo "exit_code=$EXIT_CODE" >> $GITHUB_OUTPUT

          if [ $EXIT_CODE -eq 0 ]; then
            echo "result=PASS" >> $GITHUB_OUTPUT
          else
            echo "result=FAIL" >> $GITHUB_OUTPUT
          fi

      - name: Extract metrics from attestation
        if: always()
        id: metrics
        run: |
          if [ -f attest/phase-7.0-rc_e2e_validation.json ]; then
            MEMORY=$(jq -r '.memory_resonance.stability' attest/phase-7.0-rc_e2e_validation.json)
            RIS=$(jq -r '.ris.score' attest/phase-7.0-rc_e2e_validation.json)
            STRESS=$(jq -r '.stress_resilience.recovery_rate' attest/phase-7.0-rc_e2e_validation.json)
            OVERALL=$(jq -r '.rc_criteria.overall_pass' attest/phase-7.0-rc_e2e_validation.json)
            HASH=$(jq -r '.attestation_hash' attest/phase-7.0-rc_e2e_validation.json | cut -c1-16)

            echo "memory_stability=$MEMORY" >> $GITHUB_OUTPUT
            echo "ris_score=$RIS" >> $GITHUB_OUTPUT
            echo "stress_recovery=$STRESS" >> $GITHUB_OUTPUT
            echo "overall_pass=$OVERALL" >> $GITHUB_OUTPUT
            echo "hash=$HASH" >> $GITHUB_OUTPUT
          else
            echo "memory_stability=N/A" >> $GITHUB_OUTPUT
            echo "ris_score=N/A" >> $GITHUB_OUTPUT
            echo "stress_recovery=N/A" >> $GITHUB_OUTPUT
            echo "overall_pass=false" >> $GITHUB_OUTPUT
            echo "hash=N/A" >> $GITHUB_OUTPUT
          fi

      - name: Generate validation summary
        if: always()
        run: |
          MEMORY="${{ steps.metrics.outputs.memory_stability }}"
          RIS="${{ steps.metrics.outputs.ris_score }}"
          STRESS="${{ steps.metrics.outputs.stress_recovery }}"
          OVERALL="${{ steps.metrics.outputs.overall_pass }}"
          RESULT="${{ steps.validate.outputs.result }}"

          # Determine status icons
          if [ "$MEMORY" != "N/A" ] && (( $(echo "$MEMORY >= 0.80" | bc -l) )); then
            MEM_STATUS="✅"
          else
            MEM_STATUS="❌"
          fi

          if [ "$RIS" != "N/A" ] && (( $(echo "$RIS >= 0.75" | bc -l) )); then
            RIS_STATUS="✅"
          else
            RIS_STATUS="❌"
          fi

          if [ "$STRESS" != "N/A" ] && (( $(echo "$STRESS >= 0.90" | bc -l) )); then
            STRESS_STATUS="✅"
          else
            STRESS_STATUS="❌"
          fi

          if [ "$OVERALL" = "true" ]; then
            OVERALL_STATUS="✅ PASS"
          else
            OVERALL_STATUS="❌ FAIL"
          fi

          cat <<EOF > $GITHUB_STEP_SUMMARY
          # Phase 7.0-RC Validation Results

          **Overall Status:** $OVERALL_STATUS

          ## RC Criteria

          | Metric | Value | Threshold | Status |
          |--------|-------|-----------|--------|
          | Memory Stability | $MEMORY | ≥ 0.80 | $MEM_STATUS |
          | RIS Score | $RIS | ≥ 0.75 | $RIS_STATUS |
          | Stress Recovery | $STRESS | ≥ 0.90 | $STRESS_STATUS |

          ## Attestation

          - **File:** \`attest/phase-7.0-rc_e2e_validation.json\`
          - **Hash:** \`${{ steps.metrics.outputs.hash }}...\`
          - **Signature:** "The sun shines on this work."

          ## Next Steps

          $( [ "$OVERALL" = "true" ] && echo "✅ System ready for production promotion. Create tag \`v7.0-rc-complete\`." || echo "❌ RC criteria not met. Review metrics and re-validate." )
          EOF

      - name: Upload attestation artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: phase-7-rc-attestation-${{ github.run_id }}
          path: |
            attest/phase-7.0-rc_e2e_validation.json
            rc_validation.log
          retention-days: 90

      - name: Fail job if RC criteria not met
        if: steps.validate.outputs.exit_code != '0'
        run: |
          echo "::error::RC validation failed - criteria not met"
          exit 1
```

**Key Features:**
- Weekly automated validation (Monday 10:00 UTC)
- Manual trigger via `workflow_dispatch`
- GitHub summary with formatted table
- Attestation artifact with 90-day retention
- Job fails if RC criteria not met (alerts maintainers)

---

## Step 7: Final RC Review + Tag

**Goal:** Comprehensive review and production promotion tag

### 7.1 RC Review Document

**File:** `docs/releases/phase-7.0-rc-review.md`

**Structure:**

```markdown
# Phase 7.0-RC Review — Memory Resonance & Integrity Scoring

**Review Date:** YYYY-MM-DD
**Reviewers:** [Engineering Team]
**Status:** APPROVED / PENDING / REJECTED

---

## Executive Summary

Phase 7.0-RC introduces long-term memory coherence validation for production readiness:
- 7-day TRSI stability tracking (Memory Window)
- Composite trust metric (RIS = sqrt(M_s × E_c))
- Automated stress resilience testing
- Immutable attestation records
- Real-time Prometheus observability

**Outcome:** All RC criteria PASSED → Ready for production promotion

---

## Implementation Review

### Step 1: Memory Resonance Window
- **Status:** ✅ Complete
- **Tests:** 12 tests passing
- **Code:** `orchestrator/predictive/memory_resonance.py` (220 lines)
- **Validation:** 7-day rolling window with hourly sampling
- **Metrics:** Stability = mean(TRSI) - stdev(TRSI)

### Step 2: RIS Calculator
- **Status:** ✅ Complete
- **Tests:** 8 tests passing
- **Code:** `orchestrator/predictive/ris_calculator.py` (180 lines)
- **Formula:** RIS = sqrt(memory_stability × ethics_compliance)
- **Integration:** Slot06 principle_preservation + governance fallback

### Step 3: Stress Simulation
- **Status:** ✅ Complete
- **Tests:** 6 tests passing
- **Code:** `orchestrator/predictive/stress_simulation.py` (410 lines)
- **Modes:** Drift, jitter, combined injection
- **Recovery:** ≥0.90 recovery rate within 24h validated

### Step 4: RC Attestation
- **Status:** ✅ Complete
- **Tests:** 23 tests passing
- **Code:** `scripts/generate_rc_attestation.py` (374 lines)
- **Schema:** JSON Schema 2020-12 with 13 required fields
- **Hash:** SHA-256 canonical (excluding signature + hash fields)

### Step 5: Prometheus Monitoring
- **Status:** ✅ Complete
- **Tests:** 13 tests passing
- **Metrics:** 13 gauges (memory, RIS, stress, RC gates)
- **Integration:** Auto-recording at publish/compute points

---

## Validation Results

### E2E Validation (scripts/validate_rc_e2e.py)

**Execution Date:** 2025-11-21
**Commit:** 9330aec

| Step | Component | Result | Details |
|------|-----------|--------|---------|
| 1 | Memory Window | ✅ PASS | 48 samples, stability=0.823 |
| 2 | RIS Calculator | ✅ PASS | ris=0.907 (≥0.75) |
| 3 | Stress Simulation | ✅ PASS | recovery=0.950 (≥0.90) |
| 4 | RC Attestation | ✅ PASS | All gates passing |
| 5 | Prometheus Metrics | ✅ PASS | 4 gauges exported |

**Overall:** ✅ PASS

### RC Criteria Status

| Criterion | Value | Threshold | Status |
|-----------|-------|-----------|--------|
| Memory Stability | 0.823 | ≥ 0.80 | ✅ PASS |
| RIS Score | 0.907 | ≥ 0.75 | ✅ PASS |
| Stress Recovery | 0.950 | ≥ 0.90 | ✅ PASS |
| Samples | 48 | ≥ 24 | ✅ PASS |

**Attestation:** `attest/phase-7.0-rc_e2e_validation.json`
**Hash:** `04bd4f7fb49f2eba...`
**Signature:** "The sun shines on this work."

---

## Test Coverage

**Total Tests:** 1685 passing
**New Tests (Phase 7.0-RC):** 62
- Memory: 12 tests
- RIS: 8 tests
- Stress: 6 tests
- Attestation: 23 tests
- Metrics: 13 tests

**Coverage:** 100% for RC validation components

---

## Risk Assessment

### Low Risk
- ✅ All tests passing (1685/1685)
- ✅ E2E validation complete
- ✅ No breaking changes to existing features
- ✅ Feature-flagged components (can disable)

### Medium Risk
- ⚠️ Memory window requires persistent state (7-day retention)
- ⚠️ RIS depends on Slot06 data availability
- ⚠️ Stress simulation not executed in CI (synthetic data)

### Mitigation
- Memory window uses singleton pattern with in-memory fallback
- RIS has 3-tier fallback (Slot06 → governance → 1.0 neutral)
- Stress simulation validated via unit tests

---

## Performance Impact

| Component | Overhead | Acceptable |
|-----------|----------|------------|
| Memory Window | <1ms per sample | ✅ Yes |
| RIS Calculation | <1ms per call | ✅ Yes |
| Stress Simulation | N/A (test-only) | ✅ Yes |
| Prometheus Metrics | <1ms per recording | ✅ Yes |

**Total:** <5ms per governance evaluation cycle

---

## Deployment Plan

### Phase 1: Staging Validation (1 week)
- Deploy to staging environment
- Monitor memory window population (7 days)
- Verify RIS computation with live governance data
- Validate Prometheus metrics export

### Phase 2: Production Rollout (Gradual)
- Enable memory window (flag: `NOVA_ENABLE_MEMORY_RESONANCE=true`)
- Monitor stability metrics for 7 days
- Generate weekly RC attestations
- Review Grafana dashboards

### Phase 3: Full Activation
- Enable all RC components
- Weekly automated validation via CI
- Tag `v7.0-rc-complete`

---

## Rollback Plan

**Immediate Rollback:**
```bash
# Disable RC components
export NOVA_ENABLE_MEMORY_RESONANCE=false
export NOVA_ENABLE_RIS=false
export NOVA_ENABLE_STRESS_TEST=false

# Restart orchestrator
systemctl restart nova-orchestrator
```

**Git Revert:**
```bash
git revert 9330aec..751c736  # Revert Steps 4-5
git revert c0fbf66..3b5fbb9  # Revert Steps 1-3
git push origin main
```

**Recovery Time:** <5 minutes

---

## Approval

- [ ] Engineering Lead: _________________
- [ ] Operations: _________________
- [ ] Security: _________________

**Approved for production promotion:** YES / NO

**Tag:** `v7.0-rc-complete`

---

## Appendix

### Commits (Phase 7.0-RC)
- `c0fbf66` - Step 1: Memory window scaffold
- `7433d8d` - Step 1: Predictive foresight framework
- `67f46ea` - Step 2: RIS calculator + tests
- `9321c4a` - Step 3: Foresight ledger integration
- `3b5fbb9` - Step 3: Predictive routing penalties
- `751c736` - Step 4: RC attestation system
- `23f653f` - Step 5: Prometheus monitoring
- `9330aec` - E2E validation

### Artifacts
- `attest/phase-7.0-rc_20250121.json` (manual)
- `attest/phase-7.0-rc_e2e_validation.json` (automated)
- `scripts/validate_rc_e2e.py` (validation script)
- `.artifacts/phase-7-rc-*.md` (design docs)

### References
- Blueprint: `docs/releases/phase-7.0-rc-blueprint.md`
- Design: `.artifacts/phase-7-rc-design.md`
- Connections: `.artifacts/phase7-phase14-attestation-connections.md`
```

### 7.2 Tagging Process

**Prerequisites:**
- ✅ RC review document approved
- ✅ All tests passing (1685+)
- ✅ E2E validation passed
- ✅ CI workflow validated
- ✅ Documentation updated

**Tag Command:**
```bash
git tag -a v7.0-rc-complete -m "Phase 7.0-RC — Memory Resonance & Integrity Scoring

RC Validation Complete:
- Memory stability: 0.823 ≥ 0.80 ✓
- RIS score: 0.907 ≥ 0.75 ✓
- Stress recovery: 0.950 ≥ 0.90 ✓
- All 1685 tests passing ✓

Components:
- Memory Window (7-day TRSI rolling stability)
- RIS Calculator (sqrt(M_s × E_c) composite trust)
- Stress Simulation (drift injection + recovery)
- RC Attestation (SHA-256 immutable records)
- Prometheus Monitoring (13 gauges)

Attestation: attest/phase-7.0-rc_e2e_validation.json
Hash: 04bd4f7fb49f2eba...
Signature: The sun shines on this work.

Ready for production promotion."

git push origin v7.0-rc-complete
```

### 7.3 Post-Tag Actions

1. **GitHub Release:**
   - Create release from tag `v7.0-rc-complete`
   - Attach attestation artifact
   - Link to RC review document

2. **Documentation Update:**
   - Update `README.md` with RC status
   - Add Phase 7.0-RC to changelog
   - Update architecture diagrams

3. **Notification:**
   - Post to team Slack/Discord
   - Email stakeholders
   - Update project board

4. **Monitoring Setup:**
   - Import Grafana dashboard JSON
   - Configure Prometheus alert rules
   - Set up on-call rotation

---

## Implementation Timeline

| Step | Task | Duration | Dependencies |
|------|------|----------|--------------|
| 6.1 | Create RC validation workflow | 1h | Steps 1-5 complete |
| 6.2 | Test workflow locally (act) | 30min | 6.1 |
| 6.3 | Commit workflow + trigger manual run | 30min | 6.2 |
| 6.4 | Validate workflow execution | 1h | 6.3 |
| 7.1 | Write RC review document | 1h | 6.4 passing |
| 7.2 | Review approval (async) | 1-2 days | 7.1 |
| 7.3 | Create production tag | 15min | 7.2 approved |
| 7.4 | Post-tag actions | 30min | 7.3 |

**Total Estimate:** 4-5 hours active work + 1-2 days review

---

## Success Criteria

**Step 6 (CI/CD):**
- ✅ Weekly workflow runs successfully
- ✅ RC validation completes in <5 minutes
- ✅ Attestation artifact uploaded
- ✅ GitHub summary displays results
- ✅ Job fails if criteria not met

**Step 7 (Review + Tag):**
- ✅ RC review document approved by stakeholders
- ✅ Tag `v7.0-rc-complete` created
- ✅ GitHub release published
- ✅ Documentation updated
- ✅ Team notified

---

## Open Questions

1. **Prometheus endpoint:** Do we expose `/metrics` in production or keep internal-only?
   - **Recommendation:** Internal-only, scrape from within cluster

2. **Attestation storage:** Should attestations be committed to git or stored externally?
   - **Recommendation:** Commit to `attest/` (immutable audit trail)

3. **Weekly cadence:** Is Monday 10:00 UTC optimal for team review?
   - **Recommendation:** Yes, allows Monday review + Wednesday remediation if needed

4. **Stress simulation in CI:** Should we run live stress tests or use synthetic data?
   - **Recommendation:** Synthetic for CI (fast feedback), live for staging

5. **Grafana dashboard:** Export to `ops/grafana/` or keep as design doc?
   - **Recommendation:** Export JSON in Step 6 for ops team deployment

---

## Next Immediate Step

**Option A:** Implement Step 6 (CI/CD workflow)
**Option B:** Write Step 7 (RC review document first, for stakeholder preview)
**Option C:** Both in parallel (workflow + review doc)

**Recommendation:** Option C — write review doc concurrently while implementing workflow, then request stakeholder approval before tagging.

---

**Weakest Assumption:** That weekly CI runs will provide sufficient RC validation frequency. If system degrades rapidly (<7 days), we may need daily validation or continuous monitoring thresholds.

**Next Reversible Step:** Create `.github/workflows/rc-validation.yml` with manual trigger only (no schedule), test via `workflow_dispatch`, iterate before enabling weekly schedule.

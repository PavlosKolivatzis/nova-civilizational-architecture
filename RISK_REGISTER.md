# Nova Risk Register

**Generated:** 2025-10-04
**Branch:** audit/system-cleanup-v1
**Baseline:** b4d1793

---

## Risk Summary

| Risk Level | Count | Requires Immediate Action |
|-----------|-------|--------------------------|
| 🔴 CRITICAL | 6 | Yes - This Sprint |
| 🟡 HIGH | 5 | Yes - Next Sprint |
| 🟢 MEDIUM | 4 | Monitor |
| ⚪ LOW | 2 | Track |

**Total Risks:** 17

---

## CRITICAL Risks (Immediate Action Required)

### RISK-001: Contract System Fragmentation 🔴

**Description:** 60% of flow fabric contracts lack metadata declarations, making contract lifecycle management impossible.

**Impact:**
- Cannot version or deprecate contracts safely
- Breaking changes propagate without warning
- Flow fabric becomes technical debt anchor

**Probability:** Already Occurred (6/10 contracts affected)

**Technical Details:**
- **Affected Contracts:** EMOTION_REPORT@1, DELTA_THREAT@1, PRODUCTION_CONTROL@1, META_LENS_REPORT@1, CONSTELLATION_REPORT@1, SIGNALS@1
- **Root Cause:** Missing meta.yaml files (slot03, slot07, slot08) OR incomplete metadata (slot02, slot05)
- **Evidence:** DRIFT_REPORT.md:141-153, DEFECTS_REGISTER.yml:DEF-001

**Mitigation:**
1. **Immediate (This Week):** Create stub meta.yaml for slot03, slot07
2. **Short-term (2 weeks):** Update slot02, slot05 with missing contracts
3. **Long-term:** Implement meta.yaml validation in CI (TEST_GAPS.md:Contract Validation)

**Rollback Plan:** If metadata addition breaks contracts, revert commits and use legacy flow routing

**Owner:** TBD
**Deadline:** 2025-10-11

---

### RISK-002: Architectural Ambiguity in Slot Implementations 🔴

**Description:** Duplicate implementations for Slot 4 and Slot 8 with unclear ownership create architectural uncertainty.

**Impact:**
- Developers don't know which implementation to use
- Bug fixes applied to wrong implementation
- Wasted effort maintaining zombie code

**Probability:** 100% (Currently affecting 2 slots)

**Technical Details:**
- **Slot 4 Duplicates:** slot04_tri (operational) vs slot04_tri_engine (content, 49d stale README)
- **Slot 8 Duplicates:** slot08_memory_ethics (48d stale) vs slot08_memory_lock (active)
- **Adapter Impact:** orchestrator/adapters/slot4_tri.py routes to BOTH slot04 implementations
- **Evidence:** DRIFT_REPORT.md:21-62, 65-77; DEFECTS_REGISTER.yml:DEF-003, DEF-004

**Mitigation:**
1. **Immediate:** Document which implementation is canonical (update REPO_MAP.md)
2. **This Sprint:** Archive or delete non-canonical implementations
3. **Validation:** Add test_only_one_slotNN_implementation() per TEST_GAPS.md

**Decision Required:** Are dual implementations intentional (document) or legacy (delete)?

**Rollback Plan:** If deletion breaks system, restore from git and mark as deprecated with feature flag

**Owner:** TBD
**Deadline:** 2025-10-11

---

### RISK-003: Undocumented Configuration Surface 🔴

**Description:** 94% of environment variables (135/143) are undocumented, making system impossible to configure without reading source.

**Impact:**
- Deployment failures due to missing env vars
- Security issues from incorrect configuration
- Developer onboarding takes days instead of hours

**Probability:** 100% (Active pain point)

**Technical Details:**
- **Documented:** 8 vars in .env.example
- **Undocumented:** 135 vars across 10 categories
- **Categories:** Feature flags (30), Unlearn (18), ANR (12), Creativity (17), Slot weights (18), etc.
- **Evidence:** DRIFT_REPORT.md:228-238, DEFECTS_REGISTER.yml:DEF-005

**Mitigation:**
1. **Immediate:** Document top 20 most-used env vars in .env.example
2. **Sprint 1:** Complete .env.example with all 143 vars (defaults + descriptions)
3. **Validation:** Add test_env_example_documents_all_env_vars() per TEST_GAPS.md

**Rollback Plan:** If expanded .env.example causes confusion, revert and create separate CONFIGURATION.md

**Owner:** TBD
**Deadline:** 2025-10-18

---

### RISK-004: False Documentation Claims Erode Trust 🔴

**Description:** slot04_tri_engine README claims integrations that don't exist (grep-verified 0 imports), undermining documentation credibility.

**Impact:**
- Developers waste hours chasing phantom integrations
- Trust in all documentation erodes
- Architecture understanding degrades

**Probability:** 100% (Verified false claims)

**Technical Details:**
- **False Claims:**
  - "Cultural effectiveness weighting (Slot 6)" - grep shows 0 imports in slot06
  - "Performance metrics for Slot 7 monitoring" - grep shows 0 imports in slot07
- **Verification:** `grep -r "slot04_tri_engine" slots/slot06_cultural_synthesis/` → 0 results
- **Evidence:** DRIFT_REPORT.md:37-49, DEFECTS_REGISTER.yml:DEF-002

**Mitigation:**
1. **Immediate:** Add warning banner to slot04_tri_engine README.md
2. **This Sprint:** Either implement claimed integrations OR correct README to reflect reality
3. **Validation:** Add integration tests per TEST_GAPS.md to prevent future false claims

**Rollback Plan:** If README correction breaks downstream assumptions, restore and mark sections as "Planned"

**Owner:** TBD
**Deadline:** 2025-10-11

---

### RISK-005: Test Coverage Below Threshold Creates Regression Risk 🔴

**Description:** 80% coverage is 5% below ≥85% target, with critical gaps in contract validation, integration tests, and architecture enforcement.

**Impact:**
- Regressions reach production undetected
- Defects like duplicate slots, false README claims go unnoticed
- Refactoring becomes risky

**Probability:** 100% (Gap exists, regressions likely)

**Technical Details:**
- **Current:** 80% (23,496 statements, 4,657 missed)
- **Target:** ≥85%
- **Critical Gaps:** 10 missing test categories documented in TEST_GAPS.md
- **Low Coverage Files:** fuzzy_loader.py (84%), test_health_perf.py (81%), test_slot07_adapter_metrics.py (81%)
- **Evidence:** phase1_summary.txt, TEST_GAPS.md, DEFECTS_REGISTER.yml:DEF-006

**Mitigation:**
1. **This Sprint:** Add P0 missing tests (contract validation, single slot implementation)
2. **Next Sprint:** Add P1 tests (.env.example validation, link integrity)
3. **CI Gate:** Add coverage ≥85% gate in GitHub Actions

**Rollback Plan:** If new tests are flaky, mark as xfail and track separately

**Owner:** TBD
**Deadline:** 2025-10-25

---

### RISK-006: Code Quality Debt Accumulation 🔴

**Description:** 249 linting issues, 23 type errors, 325 format violations accumulated without CI gates.

**Impact:**
- Technical debt compounds faster than remediation
- Code quality degrades over time
- Bugs hide in linting violations

**Probability:** 100% (Debt accumulating)

**Technical Details:**
- **Ruff:** 249 violations (F401 unused imports, E402 import order, etc.)
- **MyPy:** 23 type errors (missing stubs: types-PyYAML, types-requests, types-jsonschema)
- **Format:** 325 files out of compliance
- **Evidence:** phase2_summary.txt, DEFECTS_REGISTER.yml:DEF-007, DEF-008, DEF-015

**Mitigation:**
1. **Immediate:** Install missing type stubs (types-PyYAML, types-requests, types-jsonschema)
2. **This Sprint:** Fix HIGH priority ruff violations, add ruff to pre-commit hooks
3. **Next Sprint:** Fix all violations, add CI gates per TEST_GAPS.md

**Rollback Plan:** If pre-commit hooks block commits, make them advisory-only (warn but don't block)

**Owner:** TBD
**Deadline:** 2025-10-25

---

## HIGH Risks (Next Sprint)

### RISK-007: Security Vulnerability in Dependencies 🟡

**Description:** 1 HIGH severity security issue (bandit), 1 pip vulnerability (CVE tarfile extraction).

**Impact:**
- Potential code injection via subprocess patterns
- Tarfile extraction vulnerability in pip 25.2

**Probability:** HIGH (Bandit flagged, CVE published)

**Technical Details:**
- **Bandit:** 1 HIGH severity (details unavailable due to encoding error in output)
- **pip-audit:** GHSA-4xh5-x5gv-qwph (pip 25.2 tarfile extraction flaw)
- **Evidence:** phase2_summary.txt, phase2_bandit.json, DEFECTS_REGISTER.yml:DEF-009, DEF-010

**Mitigation:**
1. **This Sprint:** Investigate HIGH bandit finding in phase2_bandit.json
2. **This Sprint:** Upgrade pip to patched version
3. **CI Gate:** Add bandit HIGH severity gate per TEST_GAPS.md

**Rollback Plan:** If pip upgrade breaks dependencies, pin to working version and track CVE separately

**Owner:** TBD
**Deadline:** 2025-10-18

---

### RISK-008: API Endpoint Collision 🟡

**Description:** /metrics endpoint defined twice (orchestrator/app.py + orchestrator/http_metrics.py), unclear which is active.

**Impact:**
- Unpredictable metrics behavior
- Monitoring inconsistency
- Debugging difficulty

**Probability:** 100% (Duplicate exists)

**Technical Details:**
- **Definition 1:** orchestrator/app.py @app.get("/metrics")
- **Definition 2:** orchestrator/http_metrics.py @router.get("/metrics")
- **Active:** Depends on router inclusion order
- **Evidence:** DRIFT_REPORT.md:196, DEFECTS_REGISTER.yml:DEF-011

**Mitigation:**
1. **This Sprint:** Determine canonical implementation (test both, check router order)
2. **This Sprint:** Remove duplicate
3. **Validation:** Add test_no_duplicate_api_endpoints() per TEST_GAPS.md

**Rollback Plan:** If removal breaks metrics, restore and namespace endpoints (/metrics/v1, /metrics/v2)

**Owner:** TBD
**Deadline:** 2025-10-18

---

### RISK-009: Broken Documentation Navigation 🟡

**Description:** 9 broken links (5 missing runbooks, 3 invalid git refs, 1 missing contract doc) break documentation flow.

**Impact:**
- Users can't find critical runbooks
- Attestation links broken
- Documentation frustration

**Probability:** 100% (Links broken)

**Technical Details:**
- **Missing Runbooks:** feature-flags.md, lifespan.md, shared-hash.md, slot1.md, tri-link.md
- **Invalid Git Refs:** docs/attestations/2025-09-30-anr-5_1.md links to ../../../commit/XXXXXX
- **Missing Doc:** docs/runbooks/contract_violation.md
- **Evidence:** DRIFT_REPORT.md:318-335, DEFECTS_REGISTER.yml:DEF-012

**Mitigation:**
1. **Next Sprint:** Create missing runbooks OR remove links from ops/runbooks/README.md
2. **Next Sprint:** Fix git commit link format (use full GitHub URLs or correct relative path)
3. **CI Gate:** Add link integrity checker per TEST_GAPS.md

**Rollback Plan:** If link fix breaks references, revert and add "Coming Soon" markers

**Owner:** TBD
**Deadline:** 2025-10-25

---

### RISK-010: Documentation Staleness 🟡

**Description:** 2 READMEs >30 days stale (slot04_tri_engine: 49d, slot08_memory_ethics: 48d), both duplicate implementations.

**Impact:**
- Documentation doesn't reflect current code
- Developers misled by outdated info
- Pattern: stale docs correlate with zombie code

**Probability:** 100% (Staleness verified)

**Technical Details:**
- **Stale Docs:**
  - slot04_tri_engine/README.md: 49 days lag (last updated 2025-08-13, code 2025-10-01)
  - slot08_memory_ethics/README.md: 48 days lag (last updated 2025-08-13, code 2025-10-01)
- **Pattern:** Both are duplicate implementations with unclear ownership
- **Evidence:** DRIFT_REPORT.md:318-331, DEFECTS_REGISTER.yml:DEF-013

**Mitigation:**
1. **Next Sprint:** Update stale READMEs OR archive if implementations are zombie
2. **Long-term:** Add test_readmes_not_stale() per TEST_GAPS.md
3. **Policy:** README updates mandatory in PR checklist

**Rollback Plan:** If README update reveals breaking changes, add deprecation warnings

**Owner:** TBD
**Deadline:** 2025-10-25

---

### RISK-011: Untracked Technical Debt 🟡

**Description:** 113 TODO/FIXME tags across 45 files, 166 potential secret references unreviewed.

**Impact:**
- Technical debt invisible to planning
- Secrets may leak to logs/repos
- Critical TODOs forgotten

**Probability:** HIGH (Accumulation ongoing)

**Technical Details:**
- **Audit Tags:** 113 TODO/FIXME across 45 files
- **Secrets:** 166 references to api_key, secret, token, password (manual review required)
- **Evidence:** phase2_summary.txt, DEFECTS_REGISTER.yml:DEF-016, DEF-018

**Mitigation:**
1. **Next Sprint:** Convert TODOs to tracked GitHub issues
2. **Next Sprint:** Manual review of 166 secret references, implement secret scanning
3. **CI:** Add TODO inventory to quality dashboard

**Rollback Plan:** If TODO conversion creates noise, use "TODO-P0" tags for critical items only

**Owner:** TBD
**Deadline:** 2025-10-25

---

## MEDIUM Risks (Monitor)

### RISK-012: Version Inconsistency Within Slots 🟢

**Description:** Slot 2 has 3 different version strings (1.0.0 core, 2.0.0 enhanced, 6.5 config).

**Impact:**
- Version tracking confused
- Release management unclear

**Probability:** MEDIUM (Non-critical but confusing)

**Technical Details:**
- **Slot 2 Versions:** 1.0.0, 2.0.0, 6.5
- **Evidence:** DRIFT_REPORT.md:151, DEFECTS_REGISTER.yml:DEF-014

**Mitigation:**
- Standardize to single version per slot
- Add test_slot_version_consistency() per TEST_GAPS.md

**Owner:** TBD
**Deadline:** 2025-11-01

---

### RISK-013: Risky Code Patterns Unreviewed 🟢

**Description:** 3 subprocess/eval patterns flagged, 6 MEDIUM severity bandit issues.

**Impact:**
- Potential code injection if inputs unsanitized
- Security review gap

**Probability:** MEDIUM (Patterns exist, exploitation unclear)

**Technical Details:**
- **Risky Calls:** 3 subprocess or eval uses
- **Bandit MEDIUM:** 6 findings
- **Evidence:** phase2_summary.txt, DEFECTS_REGISTER.yml:DEF-017, DEF-026

**Mitigation:**
- Review and sanitize subprocess calls
- Remediate MEDIUM bandit findings

**Owner:** TBD
**Deadline:** 2025-11-01

---

### RISK-014: Missing Contract Producers/Consumers 🟢

**Description:** SIGNALS@1 contract registered but no slot claims to produce/consume it.

**Impact:**
- Orphaned contract clutters flow fabric
- May be legacy or general-purpose (unclear)

**Probability:** MEDIUM (May be intentional)

**Technical Details:**
- **Contract:** SIGNALS@1 in flow_fabric_init.py
- **Metadata:** Not found in any slot meta.yaml
- **Evidence:** DRIFT_REPORT.md:149, DEFECTS_REGISTER.yml:DEF-028

**Mitigation:**
- Document SIGNALS@1 purpose OR remove if unused
- Add test_all_contracts_have_producers() per TEST_GAPS.md

**Owner:** TBD
**Deadline:** 2025-11-01

---

### RISK-015: Dual Contract Naming Conventions 🟢

**Description:** Flow fabric uses @1 notation, operation contracts use dot notation, no documentation explaining dual system.

**Impact:**
- Developer confusion
- Contract naming inconsistency

**Probability:** MEDIUM (Confusing but functional)

**Technical Details:**
- **Flow Fabric:** TRI_REPORT@1 (@ versioning)
- **Operations:** tri.calculate (dot notation)
- **Evidence:** DRIFT_REPORT.md:105-139, DEFECTS_REGISTER.yml:DEF-027

**Mitigation:**
- Document dual contract system in INTERSLOT_CONTRACTS.md
- Add naming convention validation

**Owner:** TBD
**Deadline:** 2025-11-08

---

## LOW Risks (Track)

### RISK-016: Incomplete Runbook Coverage ⚪

**Description:** 5 runbooks referenced but not created (feature-flags, lifespan, shared-hash, slot1, tri-link).

**Impact:**
- Operators lack troubleshooting guides
- Incident response slower

**Probability:** LOW (System functional, runbooks nice-to-have)

**Technical Details:**
- **Missing:** 5 runbooks in ops/runbooks/
- **Evidence:** DRIFT_REPORT.md:318-323, DEFECTS_REGISTER.yml:DEF-023

**Mitigation:**
- Create runbooks when issues arise OR remove links

**Owner:** TBD
**Deadline:** Backlog

---

### RISK-017: Invalid Attestation Links ⚪

**Description:** 3 git commit links in attestations use incorrect format (../../../commit/HASH).

**Impact:**
- Attestation verification broken
- Historical traceability reduced

**Probability:** LOW (Attestations still readable)

**Technical Details:**
- **Broken Links:** docs/attestations/2025-09-30-anr-5_1.md
- **Evidence:** DRIFT_REPORT.md:329-331, DEFECTS_REGISTER.yml:DEF-024

**Mitigation:**
- Fix commit link format (use GitHub URLs)

**Owner:** TBD
**Deadline:** Backlog

---

## Risk Mitigation Dashboard

| Risk ID | Risk | Priority | Deadline | Status |
|---------|------|----------|----------|--------|
| RISK-001 | Contract metadata gap | 🔴 CRITICAL | 2025-10-11 | 🔶 OPEN |
| RISK-002 | Duplicate slot implementations | 🔴 CRITICAL | 2025-10-11 | 🔶 OPEN |
| RISK-003 | Undocumented env vars | 🔴 CRITICAL | 2025-10-18 | 🔶 OPEN |
| RISK-004 | False README claims | 🔴 CRITICAL | 2025-10-11 | 🔶 OPEN |
| RISK-005 | Test coverage gap | 🔴 CRITICAL | 2025-10-25 | 🔶 OPEN |
| RISK-006 | Code quality debt | 🔴 CRITICAL | 2025-10-25 | 🔶 OPEN |
| RISK-007 | Security vulnerabilities | 🟡 HIGH | 2025-10-18 | 🔶 OPEN |
| RISK-008 | Duplicate /metrics endpoint | 🟡 HIGH | 2025-10-18 | 🔶 OPEN |
| RISK-009 | Broken doc links | 🟡 HIGH | 2025-10-25 | 🔶 OPEN |
| RISK-010 | Stale documentation | 🟡 HIGH | 2025-10-25 | 🔶 OPEN |
| RISK-011 | Untracked tech debt | 🟡 HIGH | 2025-10-25 | 🔶 OPEN |
| RISK-012 | Version inconsistency | 🟢 MEDIUM | 2025-11-01 | 🔶 OPEN |
| RISK-013 | Risky code patterns | 🟢 MEDIUM | 2025-11-01 | 🔶 OPEN |
| RISK-014 | Orphaned contracts | 🟢 MEDIUM | 2025-11-01 | 🔶 OPEN |
| RISK-015 | Dual naming conventions | 🟢 MEDIUM | 2025-11-08 | 🔶 OPEN |
| RISK-016 | Missing runbooks | ⚪ LOW | Backlog | 🔶 OPEN |
| RISK-017 | Invalid attestation links | ⚪ LOW | Backlog | 🔶 OPEN |

---

## Next Actions

1. **Immediate (This Week):**
   - Assign owners to RISK-001, RISK-002, RISK-004
   - Create stub meta.yaml files for slot03, slot07
   - Add warning banner to slot04_tri_engine README
   - Document canonical slot implementations

2. **This Sprint (2 weeks):**
   - Execute RISK-003 mitigation (document top 20 env vars)
   - Execute RISK-007 mitigation (investigate bandit HIGH, upgrade pip)
   - Execute RISK-008 mitigation (remove duplicate /metrics)

3. **Next Sprint:**
   - Execute RISK-005 mitigation (add P0/P1 missing tests)
   - Execute RISK-006 mitigation (fix quality issues, add CI gates)
   - Execute RISK-009, RISK-010, RISK-011 mitigations

---

**Status:** RISK_REGISTER.md COMPLETE
**Evidence:** DEFECTS_REGISTER.yml, TEST_GAPS.md, DRIFT_REPORT.md, phase1_summary.txt, phase2_summary.txt

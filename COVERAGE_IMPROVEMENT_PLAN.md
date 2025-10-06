# Test Coverage Improvement Plan (DEF-006)

**Status**: Draft
**Target**: 72% → 85% (+13 percentage points)
**Baseline**: commit ed7329a
**Date**: 2025-10-06

---

## Executive Summary

Current coverage: **72%** (10,119 / 14,107 statements)
Target coverage: **85%** (11,990 / 14,107 statements)
**Gap: 1,871 statements**

**Dual Strategy**:
1. **Remove dead code**: 567 lines (-4% denominator) → 73.9% coverage (no new tests)
2. **Write targeted tests**: Cover 1,304 high-ROI statements → 85%+ coverage

**Effort estimate**: 3-5 focused sprints (15-25 hours)

---

## Strategy 1: Dead Code Removal (Quick Win)

### Removable Modules (0% coverage, zero imports)

| Lines | Module | Evidence |
|-------|--------|----------|
| 385 | `slots/slot06_cultural_synthesis/legacy_engine.py` | grep shows zero imports |
| 107 | `slots/slot10_civilizational_deployment/core/canary_backup.py` | Backup module, never activated |
| 59 | `debug_negation_bug.py` | Debug script in repo root |
| 16 | `slots/slot06_cultural_synthesis/usage_example.py` | Example file |

**Total removable**: 567 lines

**Impact**:
- New denominator: 13,540 statements
- Coverage with no new tests: 10,119 / 13,540 = **74.7%**
- Remaining gap to 85%: 1,390 statements

**Rollback**: `git revert <commit>` restores files

**Verification**:
```bash
pytest --cov=. --cov-report=term | grep TOTAL
```

**Effort**: 1 hour (grep verification + commit + test)

---

## Strategy 2: Targeted Test Coverage (High-ROI Modules)

### Tier 1: Critical Infrastructure (Top 5 modules)

| Module | Missing | Total | Cov% | Priority | Effort |
|--------|---------|-------|------|----------|--------|
| `orchestrator/semantic_creativity.py` | 239 | 355 | 32.7% | P0 | High (8h) |
| `slots/slot01_truth_anchor/orchestrator_adapter.py` | 128 | 128 | 0.0% | P1 | Medium (3h) |
| `orchestrator/router/anr_bandit.py` | 125 | 125 | 0.0% | P2 | Medium (4h) |
| `orchestrator/health_pulse.py` | 122 | 122 | 0.0% | P2 | Low (2h) |
| `orchestrator/semantic_mirror_setup.py` | 77 | 77 | 0.0% | P2 | Low (2h) |

**Subtotal**: 691 statements (37% of gap)
**Cumulative coverage**: 76.9%
**Effort**: 19 hours

### Tier 2: Adapter Layer (4 modules)

| Module | Missing | Total | Cov% | Priority | Effort |
|--------|---------|-------|------|----------|--------|
| `orchestrator/adapters/enhanced_slot5_constellation.py` | 86 | 158 | 45.6% | P1 | Medium (3h) |
| `orchestrator/app.py` | 93 | 234 | 60.3% | P0 | High (5h) |
| `src/runtime/memory_ethics_api.py` | 53 | 53 | 0.0% | P2 | Low (2h) |
| `api/security.py` | 29 | 29 | 0.0% | P1 | Low (1h) |

**Subtotal**: 261 statements (14% of gap)
**Cumulative coverage**: 78.8%
**Effort**: 11 hours

### Tier 3: Slot Internals (6 modules)

| Module | Missing | Total | Cov% | Priority | Effort |
|--------|---------|-------|------|----------|--------|
| `slots/slot08_memory_lock/ids/detectors.py` | 73 | 193 | 62.2% | P1 | Medium (3h) |
| `slots/slot08_memory_lock/core/integrity_store.py` | 52 | 99 | 47.5% | P1 | Medium (2h) |
| `slots/slot09_distortion_protection/hybrid_api.py` | 137 | 717 | 80.9% | P0 | High (6h) |
| `slots/slot01_truth_anchor/enhanced_truth_anchor_engine.py` | 61 | 150 | 59.3% | P1 | Medium (3h) |
| `slots/slot06_cultural_synthesis/context_aware_synthesis.py` | 70 | 215 | 67.4% | P1 | Medium (3h) |
| `slots/slot03_emotional_matrix/enhanced_engine.py` | 24 | 39 | 38.5% | P2 | Low (1h) |

**Subtotal**: 417 statements (22% of gap)
**Cumulative coverage**: 82.0%
**Effort**: 18 hours

### Tier 4: Stretch Goals (4 modules to reach 85%)

| Module | Missing | Total | Cov% | Priority | Effort |
|--------|---------|-------|------|----------|--------|
| `slots/slot05_constellation/plugin.py` | 23 | 37 | 37.8% | P2 | Low (1h) |
| `slots/slot10_civilizational_deployment/core/tri_gating.py` | 18 | 27 | 33.3% | P1 | Low (1h) |
| `orchestrator/adapters/slot10_civilizational.py` | 18 | 27 | 33.3% | P1 | Low (1h) |
| `slots/slot04_tri_engine/ids_integration.py` | 14 | 19 | 26.3% | P2 | Low (1h) |

**Subtotal**: 73 statements (4% of gap)
**Cumulative coverage**: 82.5%
**Effort**: 4 hours

---

## Combined Strategy Roadmap

### Phase 1: Quick Wins (1-2 hours)
- ✅ Remove dead code (567 lines) → 74.7% coverage
- ✅ Generate module-specific test plans

### Phase 2: Critical Infrastructure (Sprint 1, 8-10 hours)
- `semantic_creativity.py` (239 lines) - Creativity governor, search tree
- `app.py` (93 lines) - FastAPI app, lifespan, endpoints
- `slot09_distortion_protection/hybrid_api.py` (137 lines) - Distortion detection

**Milestone**: 77.8% coverage

### Phase 3: Adapter Layer (Sprint 2, 6-8 hours)
- `slot01_truth_anchor/orchestrator_adapter.py` (128 lines)
- `enhanced_slot5_constellation.py` (86 lines)
- `security.py` + `memory_ethics_api.py` (82 lines combined)

**Milestone**: 80.2% coverage

### Phase 4: Slot Internals (Sprint 3, 10-12 hours)
- `anr_bandit.py` (125 lines) - ANR routing logic
- `health_pulse.py` (122 lines) - Health monitoring
- `semantic_mirror_setup.py` (77 lines)
- Slot 8 IDS detectors (125 lines combined)

**Milestone**: 83.4% coverage

### Phase 5: Stretch to 85% (Sprint 4, 4-6 hours)
- Slot 6 context-aware synthesis (70 lines)
- Slot 1 enhanced anchor (61 lines)
- Slot 5/10 plugins (59 lines combined)

**Milestone**: **85.0%+ coverage**

---

## Effort Summary

| Phase | Effort | Coverage Gain | Cumulative |
|-------|--------|---------------|------------|
| Dead code removal | 1h | +2.7% | 74.7% |
| Sprint 1 (Critical) | 10h | +3.1% | 77.8% |
| Sprint 2 (Adapters) | 8h | +2.4% | 80.2% |
| Sprint 3 (Slots) | 12h | +3.2% | 83.4% |
| Sprint 4 (Stretch) | 6h | +1.6% | 85.0% |

**Total effort**: 37 hours (5 focused sprints)
**Minimum viable** (80%): 19 hours (3 sprints)
**Target** (85%): 37 hours (5 sprints)

---

## Test Authoring Principles

1. **Follow existing patterns**: Use `@pytest.mark.health` for smoke tests
2. **Test boundaries, not internals**: Focus on public API contracts
3. **Mock external dependencies**: SemanticMirror, config, slots
4. **Document assumptions**: Add docstrings explaining test purpose
5. **Measure incrementally**: Run `pytest --cov` after each module

---

## Risk Mitigation

### Risk 1: Tests break existing behavior
- **Mitigation**: Run full suite after each module (`pytest -x`)
- **Rollback**: `git revert <commit>` for failing tests

### Risk 2: Coverage targets require excessive mocking
- **Mitigation**: If module needs >5 mocks, consider excluding from coverage
- **Alternative**: Document in `.coveragerc` as "hard to test"

### Risk 3: Dead code removal breaks production
- **Mitigation**: grep verification + `pytest --import-mode=importlib` before commit
- **Rollback**: Restore files from git history

---

## Success Criteria

- ✅ Coverage ≥ 85% (TOTAL line in pytest --cov)
- ✅ All existing tests still pass (916/916)
- ✅ No new warnings introduced
- ✅ CI green on all lanes
- ✅ DEFECTS_REGISTER.yml updated (DEF-006 status: RESOLVED)

---

## Next Actions

1. **Approve plan**: Review with stakeholders
2. **Create branch**: `git checkout -b feat/coverage-improvement`
3. **Phase 1**: Remove dead code, verify 74.7% baseline
4. **Sprint 1**: `semantic_creativity.py`, `app.py`, `hybrid_api.py`
5. **Measure**: `pytest --cov` after each sprint
6. **Iterate**: Adjust plan based on actual effort vs estimates

---

**Weakest assumption**: Effort estimates based on line counts. Complex modules like `semantic_creativity.py` may require 2x estimated time.

**Rollback plan**: Each sprint is a separate commit. Revert sprint commits in reverse order if target proves unreachable.

**Rule of Sunlight**: All test additions documented with clear intent, rollback instructions, and coverage delta measurement.

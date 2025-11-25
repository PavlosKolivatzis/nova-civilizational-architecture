# Phase 9: Unified Risk Field (URF) — Minimal Design

**Date:** 2025-11-25
**Phase:** 9/14
**Purpose:** Reconcile RRI (epistemic-semantic risk) and predictive_collapse_risk (temporal-physical risk)
**Status:** Design

---

## Problem Statement

**Observed Discrepancy:**
- **RRI (Reflective Resonance Index)** — `orchestrator/rri.py`
  - Measures epistemic quality via reflection/forecast/counterfactual traces
  - Slot 2 (ΔTHRESH) + Slot 4 (TRI) lineage
  - 5-minute rolling window
  - Gauge: `nova_reflective_resonance_index`

- **predictive_collapse_risk** — `orchestrator/predictive/trajectory_engine.py`
  - Measures temporal drift acceleration → collapse probability
  - Slot 7 (Production Controls) lineage
  - Forward-projected from temporal ledger
  - Gauge: `nova_predictive_collapse_risk`

**Risk:** Both signals measure systemic stress, but from orthogonal dimensions. Without unification:
- Phase 10 deployment sees phantom conflicts
- Governance gates receive contradictory signals
- Operators cannot distinguish false alarms from true convergent crises

---

## Proposed Solution: Unified Risk Field (URF)

**Core Principle:** Normalize + fuse RRI and predictive_collapse_risk into single risk alignment metric.

### Architecture

```
┌─────────────────┐       ┌────────────────────────┐
│ RRI (epistemic) │       │ predictive_collapse_   │
│ [0.0, 1.0]      │       │ risk (temporal)        │
│ Slot 2+4        │       │ [0.0, 1.0]             │
└────────┬────────┘       └───────────┬────────────┘
         │                            │
         └─────────┬──────────────────┘
                   │
         ┌─────────▼─────────┐
         │ Risk Reconciler   │
         │ (continuity/      │
         │  risk_reconciliation.py)
         └─────────┬─────────┘
                   │
         ┌─────────▼─────────┐
         │ Unified Risk      │
         │ Field (URF)       │
         │ - risk_gap        │
         │ - alignment_score │
         │ - composite_risk  │
         └───────────────────┘
```

---

## Implementation Plan

### File: `src/nova/continuity/risk_reconciliation.py`

**Functions:**

1. **`compute_risk_alignment(rri: float, collapse_risk: float) -> dict`**
   - Normalize both to [0.0, 1.0]
   - Compute risk_gap = abs(rri - collapse_risk)
   - Compute alignment_score = 1.0 - risk_gap
   - Compute composite_risk = weighted mean

2. **`get_unified_risk_field() -> dict`**
   - Query current RRI from `orchestrator.rri.RRI_GAUGE`
   - Query current collapse_risk from `orchestrator.prometheus_metrics.predictive_collapse_risk_gauge`
   - Return URF breakdown

**Outputs:**
```python
{
    "rri": float,  # [0.0, 1.0]
    "predictive_collapse_risk": float,  # [0.0, 1.0]
    "risk_gap": float,  # [0.0, 1.0]
    "alignment_score": float,  # [0.0, 1.0], 1.0 = perfect alignment
    "composite_risk": float,  # [0.0, 1.0], weighted fusion
    "weights": {"rri": 0.4, "collapse_risk": 0.6}  # Temporal risk weighted higher
}
```

---

## Prometheus Metrics

**Gauges to add:**

1. `nova_risk_alignment` — Alignment score [0.0, 1.0]
2. `nova_risk_gap` — Absolute gap between RRI and collapse_risk
3. `nova_composite_risk` — Unified risk signal for governance

**Recording function:** `orchestrator/prometheus_metrics.py::record_urf()`

---

## Semantic Mirror Integration

**Mirror key:** `predictive.risk_alignment`

**Contract:** `contracts/urf@1.yaml`

**Fields:**
- `rri`: float
- `predictive_collapse_risk`: float
- `risk_gap`: float
- `alignment_score`: float
- `composite_risk`: float
- `timestamp`: iso8601

---

## Test Coverage

**File:** `tests/continuity/test_risk_reconciliation.py`

**Tests (5 minimum):**
1. `test_compute_risk_alignment_perfect` — rri = collapse_risk → gap = 0.0, alignment = 1.0
2. `test_compute_risk_alignment_divergent` — large gap → low alignment
3. `test_risk_gap_clamping` — out-of-range inputs clamped
4. `test_composite_risk_weighting` — verify weighted mean formula
5. `test_get_unified_risk_field_integration` — end-to-end gauge reads

---

## Governance Integration

**Where URF is consumed:**

1. **Router (Phase 5):** `orchestrator/router/epistemic_router.py`
   - Use `composite_risk` for route penalty calculation
   - Replace separate RRI/collapse_risk checks with URF

2. **Governance (Phase 5):** `orchestrator/governance/engine.py`
   - Gate deployment if `composite_risk > 0.7`
   - Alert if `alignment_score < 0.5` (signals divergent)

3. **Slot 10 (Deployment):** `src/nova/slots/slot10_civilizational_deployment/core/gatekeeper.py`
   - Pre-deployment check: `alignment_score >= 0.6`
   - Block if `risk_gap > 0.4` (contradictory signals)

---

## Rollback Strategy

**If URF causes issues:**
1. Disable recording: Comment out `record_urf()` calls
2. Revert to separate signals: Router/Governance read RRI and collapse_risk independently
3. Remove contract: `rm contracts/urf@1.yaml`
4. Remove tests: `rm tests/continuity/test_risk_reconciliation.py`

**Rollback commits:**
```bash
git revert <phase9_commit_hash>
```

---

## Validation Criteria

**Before Phase 9 merge:**
- [ ] 5 tests passing in `test_risk_reconciliation.py`
- [ ] Prometheus metrics visible at `/metrics`
- [ ] URF contract validates via `pytest tests/test_ontology_compliance.py`
- [ ] Governance gates accept `composite_risk` signal
- [ ] No regressions in full test suite (1700+ tests)

---

## Next Steps (Implementation Order)

1. **Create contract:** `contracts/urf@1.yaml`
2. **Implement calculator:** `src/nova/continuity/risk_reconciliation.py`
3. **Add Prometheus recording:** `orchestrator/prometheus_metrics.py::record_urf()`
4. **Write tests:** `tests/continuity/test_risk_reconciliation.py`
5. **Integrate with governance:** Update `orchestrator/governance/engine.py`
6. **Update ontology:** Add URF to coordination frameworks (lines 983+)
7. **Run full suite:** `pytest -q`
8. **Commit:** `feat(phase9): add Unified Risk Field (URF) reconciliation`

---

## Open Questions

1. **Weight tuning:** Currently `{rri: 0.4, collapse_risk: 0.6}`. Should temporal risk dominate?
2. **Alignment threshold:** What `alignment_score` triggers alerts? Propose 0.5.
3. **Composite risk formula:** Simple weighted mean or exponential penalty for divergence?

---

**Status:** Ready for implementation
**Estimated effort:** 1-2 hours (code + tests)
**Risk:** LOW (additive, no breaking changes)
**Rollback:** Clean (revert single commit)

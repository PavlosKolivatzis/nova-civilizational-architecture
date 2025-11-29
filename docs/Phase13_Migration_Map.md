# Phase 13: Migration Map

**Phase:** 13 - Autonomous Verification Ledger (AVL)
**Status:** Complete
**Reference:** `docs/Phase13_Initiation_Plan.md`, `docs/adr/ADR-13-Init.md`

---

## Simulation → Ledger Entry Mapping

This document maps simulation outputs to AVL entry fields for migration from
simulation-based testing to production AVL logging.

### Field Mapping Table

| Simulation Output | AVL Entry Field | Transformation |
|-------------------|-----------------|----------------|
| `step_result.timestamp` | `timestamp` | Direct copy (ISO8601) |
| `step_result.elapsed_s` | `elapsed_s` | Direct copy |
| `step_result.orp_regime` | `orp_regime` | Direct copy |
| `step_result.orp_regime_score` | `orp_regime_score` | Direct copy |
| `step_result.contributing_factors` | `contributing_factors` | Direct copy (dict) |
| `step_result.posture_adjustments` | `posture_adjustments` | Direct copy (dict) |
| `step_result.oracle_regime` | `oracle_regime` | From `compute_and_classify()` |
| `step_result.oracle_regime_score` | `oracle_regime_score` | From `compute_and_classify()` |
| `orp_regime == oracle_regime` | `dual_modality_agreement` | Boolean comparison |
| `step_result.transition_from` | `transition_from` | Direct copy (nullable) |
| `step_result.time_in_regime_s` | `time_in_previous_regime_s` | Direct copy |
| Previous entry hash | `prev_entry_hash` | `compute_entry_hash(prev_entry)` |
| `(timestamp, regime, factors)` | `entry_id` | `compute_entry_id(entry)` |

### Invariant Fields

These fields are set based on ORP invariant enforcement:

| Field | Default Value | Notes |
|-------|---------------|-------|
| `hysteresis_enforced` | `True` | ORP always enforces hysteresis |
| `min_duration_enforced` | `True` | ORP always enforces min-duration |
| `ledger_continuity` | `True` | Validated by AVL on append |
| `amplitude_valid` | Computed | `0.5 <= threshold_multiplier <= 2.0` AND `0.0 <= traffic_limit <= 1.0` |

### Drift Detection Fields

These fields are populated by the DriftGuard:

| Field | Source | Notes |
|-------|--------|-------|
| `drift_detected` | `DriftGuard.check()` | True if any drift rule triggered |
| `drift_reasons` | `DriftGuard.check()` | List of violation messages |

### Metadata Fields

| Field | Source | Notes |
|-------|--------|-------|
| `node_id` | `NOVA_AVL_NODE_ID` env var | Default: "default" |
| `orp_version` | Hardcoded | "phase13.1" |

---

## Ledger Storage

### Format

- **Type:** JSON Lines (`.jsonl`)
- **Encoding:** UTF-8
- **Line terminator:** `\n`
- **One entry per line**

### Location

- **Default:** `data/avl/avl_ledger.jsonl`
- **Configurable:** `NOVA_AVL_PATH` environment variable

### Example Entry

```json
{"entry_id":"a1b2c3d4...","prev_entry_hash":"0000000000000000000000000000000000000000000000000000000000000000","timestamp":"2025-01-01T12:00:00+00:00","elapsed_s":0.0,"orp_regime":"normal","orp_regime_score":0.15,"contributing_factors":{"urf_composite_risk":0.15,"mse_meta_instability":0.03,"predictive_collapse_risk":0.10,"consistency_gap":0.05,"csi_continuity_index":0.95},"posture_adjustments":{"threshold_multiplier":1.0,"traffic_limit":1.0,"deployment_freeze":false,"safe_mode_forced":false,"monitoring_interval_s":60},"oracle_regime":"normal","oracle_regime_score":0.15,"dual_modality_agreement":true,"transition_from":null,"time_in_previous_regime_s":0.0,"hysteresis_enforced":true,"min_duration_enforced":true,"ledger_continuity":true,"amplitude_valid":true,"drift_detected":false,"drift_reasons":[],"node_id":"default","orp_version":"phase13.1"}
```

---

## Migration Steps

### Step 1: Enable AVL in Development

```bash
# .env.local
NOVA_ENABLE_AVL=1
NOVA_AVL_PATH=data/avl/dev_ledger.jsonl
NOVA_AVL_HALT_ON_DRIFT=0
```

### Step 2: Run Simulation with AVL

```bash
# Run single trajectory
python scripts/validate_avl_e2e.py --trajectory canonical_normal_to_heightened.json

# Run all trajectories
python scripts/validate_avl_e2e.py
```

### Step 3: Validate Ledger Integrity

```python
from src.nova.continuity.avl_ledger import AVLLedger
from src.nova.continuity.continuity_proof import ContinuityProof

ledger = AVLLedger("data/avl/dev_ledger.jsonl")

# Verify hash chain
is_valid, violations = ledger.verify_integrity()
print(f"Integrity: {is_valid}")

# Run continuity proofs
proof = ContinuityProof()
results = proof.prove_all(ledger.get_entries())
for name, result in results.items():
    print(f"{name}: {'PASS' if result.passed else 'FAIL'}")
```

### Step 4: Enable in Production

```bash
# .env.production
NOVA_ENABLE_AVL=1
NOVA_AVL_PATH=/var/nova/avl/production_ledger.jsonl
NOVA_AVL_HALT_ON_DRIFT=0  # Start with logging only
NOVA_AVL_NODE_ID=prod-node-01
```

### Step 5: Enable Halt-on-Drift (Optional)

After validating no false positives in production:

```bash
NOVA_AVL_HALT_ON_DRIFT=1
```

---

## Query API Examples

### Query by Time Window

```python
ledger = AVLLedger("data/avl/ledger.jsonl")

# Get entries from specific time range
entries = ledger.query_by_time_window(
    "2025-01-01T12:00:00+00:00",
    "2025-01-01T13:00:00+00:00"
)
```

### Query by Regime

```python
# Get all heightened regime entries
heightened = ledger.query_by_regime("heightened")
```

### Query Drift Events

```python
# Get all drift events
drift_events = ledger.query_drift_events()
for event in drift_events:
    print(f"{event.timestamp}: {event.drift_reasons}")
```

### Get Latest Entries

```python
# Get last 10 entries
latest = ledger.get_latest(10)
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVA_ENABLE_AVL` | `0` | Enable AVL logging (`1`=enabled) |
| `NOVA_AVL_PATH` | `data/avl/avl_ledger.jsonl` | Ledger file path |
| `NOVA_AVL_HALT_ON_DRIFT` | `0` | Halt on drift (`1`=halt) |
| `NOVA_AVL_NODE_ID` | `default` | Node identifier |

---

## Rollback Plan

If issues arise with AVL:

### Disable AVL

```bash
export NOVA_ENABLE_AVL=0
```

### Revert Code (if needed)

```bash
git revert <avl-commit-range>
```

### Clear Ledger (development only)

```python
from src.nova.continuity.avl_ledger import reset_avl_ledger
reset_avl_ledger()
```

---

## Validation Results

### E2E Validation Summary

```
Total trajectories: 20
Passed: 20
Failed: 0
Total entries: 117
Drift events: 0
```

### Test Coverage

| Test Suite | Tests | Status |
|------------|-------|--------|
| `test_avl_ledger.py` | 28 | PASS |
| `test_drift_guard.py` | 21 | PASS |
| `test_continuity_proof.py` | 21 | PASS |
| `test_orp_avl.py` | 9 | PASS |
| `test_orp.py` | 31 | PASS |
| **Total** | **110** | **PASS** |

---

## Files Created/Modified

### New Files

- `src/nova/continuity/avl_ledger.py` - AVL ledger core
- `src/nova/continuity/drift_guard.py` - Drift detection engine
- `src/nova/continuity/continuity_proof.py` - Continuity proof validators
- `src/nova/continuity/__init__.py` - Module exports
- `tests/continuity/test_avl_ledger.py` - AVL unit tests
- `tests/continuity/test_drift_guard.py` - Drift guard unit tests
- `tests/continuity/test_continuity_proof.py` - Proof unit tests
- `tests/integration/test_orp_avl.py` - Integration tests
- `scripts/validate_avl_e2e.py` - E2E validation script
- `docs/Phase13_Migration_Map.md` - This document

### Modified Files

- `src/nova/continuity/operational_regime.py` - AVL integration

---

## Next Steps

1. **Phase 14:** Ledger archival strategy (unbounded growth mitigation)
2. **Prometheus metrics:** Add `nova_avl_entries_total`, `nova_avl_drift_events_total`
3. **Grafana dashboard:** AVL health monitoring
4. **Async writes:** Performance optimization for high-throughput scenarios

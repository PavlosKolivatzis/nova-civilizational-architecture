# Phase 13: Simulation → AVL Migration Mapping

**Purpose:** Define exact transformation from simulation engine output to AVL ledger entries.

**Source:** `scripts/simulate_nova_cycle.py` → `StepResult` dataclass
**Target:** `src/nova/continuity/avl_ledger.py` → `AVLEntry` dataclass

---

## Field Mapping Table

| Simulation Output Field | AVL Entry Field | Transformation | Notes |
|-------------------------|-----------------|----------------|-------|
| `step_result.step` | _Not mapped_ | Omit | AVL uses entry_id instead |
| `step_result.timestamp` | `timestamp` | Direct copy | Already ISO8601 with timezone |
| `step_result.elapsed_s` | `elapsed_s` | Direct copy | Seconds since start |
| `step_result.contributing_factors` | `contributing_factors` | Direct copy | Dict unchanged |
| `step_result.orp_regime_score` | `orp_regime_score` | Direct copy | Float [0.0, 1.0] |
| `step_result.orp_regime` | `orp_regime` | Direct copy | String (enum value) |
| `step_result.orp_transition_from` | `transition_from` | Direct copy | Optional[str] |
| `step_result.time_in_regime_s` | `time_in_previous_regime_s` | Direct copy | Duration in previous regime |
| `step_result.oracle_regime_score` | `oracle_regime_score` | Direct copy | Float [0.0, 1.0] |
| `step_result.oracle_regime` | `oracle_regime` | Direct copy | String (enum value) |
| `step_result.dual_modality_agreement` | `dual_modality_agreement` | Direct copy | Boolean |
| `step_result.hysteresis_enforced` | `hysteresis_enforced` | Direct copy | Boolean |
| `step_result.min_duration_enforced` | `min_duration_enforced` | Direct copy | Boolean |
| `step_result.ledger_continuity` | `ledger_continuity` | Direct copy | Boolean |
| `step_result.amplitude_valid` | `amplitude_valid` | Direct copy | Boolean |
| `step_result.threshold_multiplier` | `posture_adjustments["threshold_multiplier"]` | Nest in dict | Part of posture |
| `step_result.traffic_limit` | `posture_adjustments["traffic_limit"]` | Nest in dict | Part of posture |
| `step_result.deployment_freeze` | `posture_adjustments["deployment_freeze"]` | Nest in dict | Part of posture |
| `step_result.safe_mode_forced` | `posture_adjustments["safe_mode_forced"]` | Nest in dict | Part of posture |
| `step_result.violations` | `drift_reasons` | Map list | Empty if no drift |
| `len(step_result.violations) > 0` | `drift_detected` | Compute boolean | True if violations non-empty |
| _Previous entry hash_ | `prev_entry_hash` | Compute | SHA256(previous entry) |
| _(timestamp, regime, factors)_ | `entry_id` | Compute | SHA256(canonical JSON) |
| _System hostname_ | `node_id` | Compute | From environment |
| _"phase13.1"_ | `orp_version` | Hardcode | Version string |

---

## Transformation Code

```python
def step_result_to_avl_entry(
    step_result: StepResult,
    prev_entry_hash: str = "0" * 64,
    node_id: str = socket.gethostname(),
    orp_version: str = "phase13.1",
) -> AVLEntry:
    """Convert simulation StepResult to AVL entry."""

    # Build posture_adjustments dict
    posture_adjustments = {
        "threshold_multiplier": step_result.threshold_multiplier,
        "traffic_limit": step_result.traffic_limit,
        "deployment_freeze": step_result.deployment_freeze,
        "safe_mode_forced": step_result.safe_mode_forced,
    }

    # Compute drift detection
    drift_detected = len(step_result.violations) > 0
    drift_reasons = step_result.violations if drift_detected else []

    # Create entry (entry_id computed by AVLLedger.append())
    entry = AVLEntry(
        entry_id="",  # Will be computed
        prev_entry_hash=prev_entry_hash,
        timestamp=step_result.timestamp,
        elapsed_s=step_result.elapsed_s,
        orp_regime=step_result.orp_regime,
        orp_regime_score=step_result.orp_regime_score,
        contributing_factors=step_result.contributing_factors,
        posture_adjustments=posture_adjustments,
        oracle_regime=step_result.oracle_regime,
        oracle_regime_score=step_result.oracle_regime_score,
        dual_modality_agreement=step_result.dual_modality_agreement,
        transition_from=step_result.orp_transition_from,
        time_in_previous_regime_s=step_result.time_in_regime_s,
        hysteresis_enforced=step_result.hysteresis_enforced,
        min_duration_enforced=step_result.min_duration_enforced,
        ledger_continuity=step_result.ledger_continuity,
        amplitude_valid=step_result.amplitude_valid,
        drift_detected=drift_detected,
        drift_reasons=drift_reasons,
        node_id=node_id,
        orp_version=orp_version,
    )

    return entry
```

---

## Example Transformation

**Simulation Output (StepResult):**
```json
{
  "step": 0,
  "timestamp": "2025-01-01T00:00:00+00:00",
  "elapsed_s": 0.0,
  "contributing_factors": {
    "urf_composite_risk": 0.12,
    "mse_meta_instability": 0.02,
    "predictive_collapse_risk": 0.08,
    "consistency_gap": 0.04,
    "csi_continuity_index": 0.96
  },
  "orp_regime_score": 0.067,
  "orp_regime": "normal",
  "orp_transition_from": null,
  "time_in_regime_s": 0.0,
  "oracle_regime_score": 0.067,
  "oracle_regime": "normal",
  "dual_modality_agreement": true,
  "hysteresis_enforced": true,
  "min_duration_enforced": true,
  "ledger_continuity": true,
  "amplitude_valid": true,
  "threshold_multiplier": 1.0,
  "traffic_limit": 1.0,
  "deployment_freeze": false,
  "safe_mode_forced": false,
  "violations": []
}
```

**AVL Entry (after transformation):**
```json
{
  "entry_id": "a3c5e8f2b1d4e9a7...",
  "prev_entry_hash": "0000000000000000...",
  "timestamp": "2025-01-01T00:00:00+00:00",
  "elapsed_s": 0.0,
  "orp_regime": "normal",
  "orp_regime_score": 0.067,
  "contributing_factors": {
    "urf_composite_risk": 0.12,
    "mse_meta_instability": 0.02,
    "predictive_collapse_risk": 0.08,
    "consistency_gap": 0.04,
    "csi_continuity_index": 0.96
  },
  "posture_adjustments": {
    "threshold_multiplier": 1.0,
    "traffic_limit": 1.0,
    "deployment_freeze": false,
    "safe_mode_forced": false
  },
  "oracle_regime": "normal",
  "oracle_regime_score": 0.067,
  "dual_modality_agreement": true,
  "transition_from": null,
  "time_in_previous_regime_s": 0.0,
  "hysteresis_enforced": true,
  "min_duration_enforced": true,
  "ledger_continuity": true,
  "amplitude_valid": true,
  "drift_detected": false,
  "drift_reasons": [],
  "node_id": "nova-prod-01",
  "orp_version": "phase13.1"
}
```

---

## Migration Script

**Script:** `scripts/migrate_simulation_to_avl.py`

**Purpose:** Convert existing simulation results to AVL ledger format.

**Usage:**
```bash
# Migrate single trajectory
python scripts/migrate_simulation_to_avl.py \
  --input test_output/canonical_normal_stable_results.jsonl \
  --output data/avl/canonical_normal_stable.avl.jsonl

# Migrate all trajectories
python scripts/migrate_simulation_to_avl.py \
  --input-dir test_output/ \
  --output-dir data/avl/
```

**Script skeleton:**
```python
#!/usr/bin/env python3
"""Migrate simulation results to AVL ledger format."""

import argparse
import json
from pathlib import Path
from src.nova.continuity.avl_ledger import AVLLedger, AVLEntry

def load_simulation_results(path: Path) -> List[StepResult]:
    """Load simulation JSONL file."""
    results = []
    with open(path) as f:
        for line in f:
            results.append(StepResult(**json.loads(line)))
    return results

def migrate_to_avl(results: List[StepResult], output_path: Path):
    """Convert simulation results to AVL ledger."""
    ledger = AVLLedger(str(output_path))

    for step_result in results:
        entry = step_result_to_avl_entry(step_result)
        ledger.append(entry)

    print(f"Migrated {len(results)} entries to {output_path}")
    print(f"Ledger integrity: {ledger.verify_integrity()}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = load_simulation_results(args.input)
    migrate_to_avl(results, args.output)

if __name__ == "__main__":
    main()
```

---

## Validation Checklist

After migration, validate:

- [ ] **Entry count matches:** AVL entries == simulation steps
- [ ] **Hash chain intact:** `verify_integrity()` passes
- [ ] **Timestamps preserved:** All timestamps match simulation
- [ ] **Regime sequence preserved:** Regime transitions identical
- [ ] **Dual-modality agreement:** Same as simulation (100% on canonical)
- [ ] **Drift events match:** drift_detected matches violations
- [ ] **Continuity proofs hold:** All proofs pass on migrated ledger

---

## Notes

- Migration is **one-way** (simulation → AVL, not reversible)
- AVL is **append-only** (no updates/deletes)
- `entry_id` and `prev_entry_hash` are **computed**, not copied
- `node_id` and `orp_version` are **metadata**, not in simulation
- Simulation `step` field is **discarded** (AVL uses entry_id)

# Trajectory JSON Schema

## Purpose

Trajectories define signal evolution sequences for testing ORP regime transitions, hysteresis, min-duration enforcement, and dual-modality agreement.

## Schema

```json
{
  "trajectory_id": "string (unique identifier, snake_case)",
  "description": "string (human-readable description)",
  "steps": [
    {
      "step": "integer (0-indexed step number)",
      "timestamp": "string (ISO 8601 timestamp)",
      "elapsed_s": "float (seconds since step 0)",
      "contributing_factors": {
        "urf_composite_risk": "float [0.0, 1.0]",
        "mse_meta_instability": "float [0.0, 1.0]",
        "predictive_collapse_risk": "float [0.0, 1.0]",
        "consistency_gap": "float [0.0, 1.0]",
        "csi_continuity_index": "float [0.0, 1.0]"
      },
      "expected_regime": "string (optional, for validation)",
      "expected_transition": "string (optional, expected from_regime)"
    }
  ]
}
```

## Signal Weights (from orp@1.yaml)

- `urf_composite_risk`: 0.30
- `mse_meta_instability`: 0.25
- `predictive_collapse_risk`: 0.20
- `consistency_gap`: 0.15
- `csi_continuity_index`: 0.10 (inverted: `1.0 - csi`)

## Regime Score Calculation

```
regime_score = (
    urf * 0.30 +
    mse * 0.25 +
    pred * 0.20 +
    gap * 0.15 +
    (1.0 - csi) * 0.10
)
```

## Regime Thresholds

- `normal`: [0.0, 0.30)
- `heightened`: [0.30, 0.50)
- `controlled_degradation`: [0.50, 0.70)
- `emergency_stabilization`: [0.70, 0.85)
- `recovery`: [0.85, 1.0]

## Hysteresis and Min-Duration

- **Downgrade hysteresis**: 0.05 (must drop 0.05 below threshold)
- **Min regime duration**: 300s (5 minutes before downgrade allowed)
- **Upgrades**: Immediate (no hysteresis, no min-duration)

## Examples

### Normal Regime
```json
"contributing_factors": {
  "urf_composite_risk": 0.12,
  "mse_meta_instability": 0.02,
  "predictive_collapse_risk": 0.08,
  "consistency_gap": 0.04,
  "csi_continuity_index": 0.96
}
// regime_score = 0.067 → normal
```

### Heightened Regime
```json
"contributing_factors": {
  "urf_composite_risk": 0.60,
  "mse_meta_instability": 0.10,
  "predictive_collapse_risk": 0.40,
  "consistency_gap": 0.20,
  "csi_continuity_index": 0.80
}
// regime_score = 0.355 → heightened
```

### Emergency Regime
```json
"contributing_factors": {
  "urf_composite_risk": 0.90,
  "mse_meta_instability": 0.30,
  "predictive_collapse_risk": 0.85,
  "consistency_gap": 0.70,
  "csi_continuity_index": 0.30
}
// regime_score = 0.732 → emergency_stabilization
```

## Trajectory Categories

### Canonical (10)
- Single-regime stability
- Gradual escalation
- Gradual recovery
- Hysteresis prevention
- Min-duration enforcement

### Adversarial (6)
- Rapid oscillation
- Boundary conditions
- Signal collapse
- Immediate spikes
- Zero-duration attempts

### Noise-Injected (4)
- Random jitter (±10%)
- Random spikes
- Gradual drift with noise
- Unstable recovery

### Temporal Invariance (4)
- 10s evaluation intervals
- 60s evaluation intervals
- Compressed (drop every 2nd step)
- Expanded (interpolated midpoints)

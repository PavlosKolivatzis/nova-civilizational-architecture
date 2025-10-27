# Phase 12B – Quantum Entropy & ΔTHRESH Weighting Dashboard

This dashboard highlights entropy fidelity signals coming from Slot01 and the corresponding weighting applied by Slot02 (ΔTHRESH). Import the JSON at `monitoring/grafana/dashboards/nova-phase12b-quantum-entropy.json` via Grafana → Dashboards → **Import**.

## Panels

| Panel | Metric | Healthy range |
| --- | --- | --- |
| **Entropy Fidelity (mean)** | `slot01_entropy_fidelity_mean` | ≥ 0.97 (yellow < 0.95, red < 0.90) |
| **Fidelity CI Width** | `slot01_entropy_fidelity_ci_width` | ≤ 0.06 (warn at 0.10, critical 0.15) |
| **Entropy Abs Bias** | `slot01_entropy_bias_abs` | ≤ 0.03 (warn 0.05, critical 0.10) |
| **Quantum Jobs by Status** | `increase(slot01_entropy_quantum_jobs_total[5m])` | Errors should stay at zero |
| **ΔTHRESH Fidelity Weight (last)** | `slot2_fidelity_weight_applied` | 0.9 – 1.1 (bounded by config clamps) |
| **Weighting Events /5m** | `increase(slot2_fidelity_weighting_events_total[5m])` | Expect steady increments when Slot02 is active |

## Alert suggestions

```promql
# High bias
slot01_entropy_bias_abs > 0.1

# Wide confidence interval
slot01_entropy_fidelity_ci_width > 0.15

# Adapter errors
increase(slot01_entropy_quantum_jobs_total{status="err"}[15m]) > 3

# Weight out of band (should not happen if clamps hold)
slot2_fidelity_weight_applied < 0.9 or slot2_fidelity_weight_applied > 1.1
```

## Staging smoke checklist

1. Enable Slot02 fidelity weighting in staging:
   ```yaml
   slot2:
     fidelity_weighting:
       enabled: true
       base: 1.0
       slope: 0.2
       clamp_lo: 0.9
       clamp_hi: 1.1
   ```
2. Generate 5–10 anchors (normal flow) then inspect dashboard:
   - Fidelity mean ≥ 0.97
   - CI width ≤ 0.06
   - Abs bias ≤ 0.03
   - ΔTHRESH weight within clamps
3. Confirm metrics are present in `/metrics` and Grafana panels populate before enabling in production.

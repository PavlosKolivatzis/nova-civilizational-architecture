# Phase 15-8.5 — A/B Soak Calibration Report

## Objective
Tune κ (kappa) and G₀ for optimal stability + creativity.

## Parameter Space
κ ∈ {0.01, 0.02}, G₀ ∈ {0.55, 0.60, 0.65}, 30 min per combo.

## Success Criteria
S ≥ 0.03, H ≥ 0.02, |Δη| ≤ 0.01, G* ≥ 0.6 with σ(G*) < 0.05, clamp ratio < 10%.

## Method
- Runner: `scripts/soak_ab_wisdom_governor.py`
- Data: `.artifacts/wisdom_ab_runs.csv`
- Notebook: `notebooks/phase_15_8_5_ab_analysis.ipynb`

## Results (fill after runs)
| κ | G₀ | S_mean | H_min | |Δη|_mean | G*_mean | σ(G*) | clamp_ratio | η_p95 | Verdict |
|---|----|--------|-------|----------|---------|-------|-------------|-------|---------|
|   |    |        |       |          |         |       |             |       |         |

## Recommendation
- Selected: κ = __, G₀ = __
- Rationale: __
- Next steps: roll to staging, 24h soak, promote if alerts remain green.

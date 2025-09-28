# Phase 5.1 — Adaptive Neural Routing (ANR) • Milestone

**Date:** 2025-09-28
**Status:** ✅ Verified — Pilot-ready (10% live config available)

## Summary
ANR moves Nova from fixed paths to self-optimizing routing with strict safety. Learning comes from immediate (latency, TRI Δ) and delayed (deployment) rewards; safety layers cap risk under anomalies and provide instant rollback.

## What's live in code
- Shadow router + pilot gating (ε-greedy → LinUCB when available)
- 11D features (+bias) across TRI, pressure/jitter, culture, back-pressure, budgets
- Route set: R1/R2/R3/R4/R5 with concrete slot adapter calls
- Safety: kill-switch (R4), fast-cap for R3 under anomaly, anomaly masks
- Reward shaping:
  - Immediate: `+tri_delta_norm - latency_norm`
  - Deploy: `slo_ok - rollback - error_rate - 0.5*transform_rate`
- Persistence: JSON bandit state (`NOVA_ANR_STATE_PATH`)

## Verification evidence
- Tests: **17 ANR tests** passing (fast-cap, pilot gating, kill-switch, LinUCB state)
- Lint: ACL extractor scoped to mirror APIs; all `router.*` keys documented
- `verify_pilot_ready.py`: kill-switch ✔, fast-cap ✔, gating ✔, persistence ✔

## Semantic Mirror Keys
- `router.anr_shadow_decision` - Shadow routing decisions
- `router.anr_live_decision` - Live pilot decisions
- `router.current_decision_id` - Active correlation ID
- `router.anr_reward_immediate` - Latency/TRI feedback
- `router.anr_reward_deployment` - SLO/rollback feedback

## Pilot config (10%)
```bash
export NOVA_ANR_ENABLED=1
export NOVA_ANR_PILOT=0.10
export NOVA_ANR_MAX_FAST_PROB=0.15
export NOVA_ANR_STRICT_ON_ANOMALY=1
export NOVA_ANR_LEARN_SHADOW=1
```

## Rollback
```bash
export NOVA_ANR_ENABLED=0     # instant (forces R4 via safety)
```

## Promotion gates (24h rolling)
* RSI (live==shadow-argmax) ≥ **0.85**
* Rollbacks ≤ **0.1 / 1k** decisions
* Median TRI Δ ≥ **0**
* Fast-cap under anomaly never > **0.15**

## Development Notes
Windows console encoding fix: `set PYTHONIOENCODING=utf-8`

---
*Phase 5.1 ANR - pilot ready (shadow + 10% config)*
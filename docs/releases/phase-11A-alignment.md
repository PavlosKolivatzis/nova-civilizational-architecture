# Phase 11A Alignment Baseline

## Overview
- Locks the ten-slot stack against Phase‑11A guardrails.
- Establishes health smoke automation (`alignment-smoke`) for every PR.
- Documents the operational flags required for ANR and ARC pilots.
- Confirms telemetry alignment before we elevate to Phase‑11B.

## Slot Readiness Matrix
| Slot | Capability Pillar | Alignment Status | Notes |
| --- | --- | --- | --- |
| slot01_truth_anchor | Integrity nucleus | ✅ Healthy | No action required |
| slot02_deltathresh | ΔTHRESH anomaly routing | ✅ Healthy | Kill-switch verified |
| slot03_emotional_matrix | Empathic modulation | ✅ Healthy | Escalation paths green |
| slot04_tri | TRI synthesis | ✅ Healthy | TRI drift within ±0.01 |
| slot05_constellation | Cultural constellation | ✅ Healthy | Constellation cache rotated |
| slot06_cultural_synthesis | Cultural synthesis engine | ✅ Healthy | Pulse queue empty |
| slot07_production_controls | Production guardrails | ✅ Healthy | Circuit breaker armed |
| slot08_memory_lock | Memory lock & ethics | ✅ Healthy | Shadow ledger clean |
| slot09_distortion_protection | Distortion & perspective | ✅ Healthy | L2 caches synced |
| slot10_civilizational_deploy | Civilizational deployment orchestration | ✅ Healthy | Gatekeeper thresholds reloaded |

## Feature Flags & Environment
```
NOVA_ANR_ENABLED=0          # enable when pilot ready (10% = 0.10)
NOVA_ANR_PILOT=0.0
NOVA_ANR_MAX_FAST_PROB=0.15
NOVA_ANR_LEARN_SHADOW=1
NOVA_ANR_STRICT_ON_ANOMALY=1

# ARC (Autonomous Reflection Cycle)
NOVA_ARC_ENABLED=0
NOVA_ARC_SAMPLE=0.10

# RRI weights (windowed calculation)
NOVA_RRI_W_REFLECT=0.4
NOVA_RRI_W_FORECAST=0.4
NOVA_RRI_W_COUNTER=0.2
```

## Gates & Telemetry
- **nova_reflective_resonance_index** ≥ 0.60 (windowed 5‑minute average).
- **nova_arc_consistency** ≥ 0.75 after ARC rollout.
- **nova_anr_rollbacks_per_1k** ≤ 0.10; **nova_anr_fast_cap_prob** ≤ 0.15.
- Dashboards: `docs/grafana/phase11_panels.json`.

## Validation Checklist
1. `python scripts/slot_registry_check.py`
2. `pytest -m health -q`
3. `python scripts/verify_vault.py`
4. CI `alignment-smoke` job (runs 1&2 automatically).

## Rollback Playbook
- Disable ARC: `export NOVA_ARC_ENABLED=0`
- Disable ANR pilot: `export NOVA_ANR_ENABLED=0`
- Re-run validation checklist to confirm stable Phase‑10 posture.

Once all checks remain green for 48 hours under staged traffic, we progress to Phase‑11B (pilot activation).

# Phase-4 Migration Plan — Deterministic Routing

## Overview

Phase-4 introduces the deterministic routing layer (Mode 1). Routing decisions now pass through a constraint engine driven by TRI coherence, Slot07 backpressure, and Slot10 gate status. ANR executes only when constraints permit. Advisory scores from Slot05/08 are read-only and cannot override constraints.

## Components

1. `orchestrator/router/constraints.py` — evaluates TRI coherence, drift, jitter, Slot07 backpressure, and Slot10 gate state using Threshold Manager + Semantic Mirror.
2. `orchestrator/router/anr_static_policy.py` — deterministic ANR policy with fixed coefficients.
3. `orchestrator/router/epistemic_router.py` — orchestrates constraints, ANR, advisors, mirror publications, and metrics.
4. `orchestrator/router/advisors/slot05.py` / `slot08.py` — advisory scores for constellation alignment and semantic continuity.
5. FastAPI endpoints `/router/decide` and `/router/debug`.

## Slot Interactions

| Slot | Interaction |
|------|-------------|
| 04   | Provides canonical TRI signal (`slot04.tri_truth_signal`). |
| 05   | Advisory alignment score (`slot05.constellation_alignment`). |
| 07   | Backpressure state (`slot07.backpressure_state`). |
| 08   | Semantic continuity score (`slot08.continuity_score`). |
| 10   | Gatekeeper status (`slot10.lightclock_gate`). |

## Backwards Compatibility

- Legacy ANR remains available; the deterministic router is additive.
- Semantic Mirror keys are optional; router defaults to conservative values when missing.
- Feature flags not required. Deterministic router runs whenever endpoints are invoked.

## Rollback Plan

1. Disable new `/router/*` endpoints.
2. Revert `orchestrator/router` to previous commit (pre-Phase-4).
3. Remove new Prometheus metrics exporters.
4. Restart orchestrator to flush semantic mirror keys.

## Test Matrix

| Test Suite | Purpose |
|------------|---------|
| `tests/router/test_constraints.py` | Verifies constraint evaluation. |
| `tests/router/test_epistemic_router.py` | Ensures routing honours constraints and advisors. |
| `tests/integration/test_routing_pipeline.py` | End-to-end routing pipeline. |
| `tests/web/test_router_decide.py` | API contract for `/router/decide`. |
| `tests/web/test_router_metrics.py` | Observability coverage. |

## Deployment Checklist

1. Deploy Phase-4 code.
2. Ensure Semantic Mirror keys `router.*` start populating.
3. Verify Prometheus exposes `nova_route_selected` and router Infos.
4. Run targeted suites:
   - `python -m pytest tests/router -q`
   - `python -m pytest tests/integration/test_routing_pipeline.py -q`
   - `python -m pytest tests/web/test_router_decide.py -q`
5. Monitor `/router/decide` in staging before production rollout.

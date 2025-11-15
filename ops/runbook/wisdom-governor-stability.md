# Adaptive Wisdom Governor Stability Runbook

_Last updated: 2025-11-12_

## 1. Detection

- Alerts: `nova_wisdom_stability_margin < 0.05`, `nova_wisdom_hopf_distance < 0.02`, or `nova_wisdom_generativity < 0.6`.
- Verify metrics:
  ```bash
  curl -s http://localhost:8000/metrics | rg 'nova_wisdom'
  ```

## 2. Immediate Actions

1. **Clamp η (learning rate)**
   ```bash
   export NOVA_WISDOM_ETA_OVERRIDE=0.05
   python orchestrator/adaptive_wisdom_poller.py --apply-override
   ```

2. **Freeze Governor if Hopf Distance Critical**
   ```bash
  curl -s -X POST http://localhost:8000/wisdom/freeze -d '{"reason":"hopf"}'
   ```
   Resume only after H ≥ 0.03 AND S ≥ 0.05.

3. **Inspect TRI + Slot7 Pressure**
   ```bash
   curl -s http://localhost:8000/semantic/context | jq '.slot04, .slot07'
   ```
   - High Slot7 pressure (>0.8) often precedes stability drops; throttle concurrency.

4. **Restart Poller (if metrics stale)**
   ```bash
   systemctl restart nova-wisdom-poller
   tail -f /var/log/nova/wisdom_poller.log
   ```

## 3. Parameter Tuning

| Metric | Safe Range | Action |
| --- | --- | --- |
| `nova_wisdom_eta_current` | 0.08–0.12 | Adjust `NOVA_WISDOM_KP/KD` if drifting |
| `nova_wisdom_generativity` | ≥ 0.65 | If low, reduce damping (`k_d`) but only when S ≥ 0.10 |
| `nova_wisdom_spectral_radius` | ≤ 1.0 | >1 indicates runaway gain; force η override |

## 4. Escalation

- **S < 0.01 or repeated oscillations** → Notify Phase 15 steward, halt Slot10 deployments.
- **No metric updates for >5m** → Check `orchestrator/adaptive_wisdom_poller.py` for liveness and inspect `peer_store`.

## 5. Recovery Checklist

1. Ensure Slot4 drift detectors report healthy values (`tri_drift_z < 2.0`).
2. Unfreeze governor, remove overrides, verify metrics trend back to nominal.
3. Attach `nova_wisdom_*` screenshots to incident retro and update [`docs/wisdom_governor_mvs.md`](../../docs/wisdom_governor_mvs.md) with tuning notes.

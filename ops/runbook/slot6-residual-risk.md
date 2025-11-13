# Slot 6 Residual Risk Spike Runbook

_Last updated: 2025-11-12_

## 1. Detection

- Alert source: `slot6_residual_risk_p99` or `slot6_blocked_rate_anomaly` firing from Prometheus.
- Confirm raw metrics:
  ```bash
  curl -s http://localhost:8000/metrics | rg 'slot6_(residual_risk|decisions)'
  curl -s http://localhost:8000/health | jq '.slot6'
  ```

## 2. Immediate Actions

1. **Freeze high-risk adapters**  
   - Toggle `SLOT3_ESCALATION_ENABLED=0` if emotional escalations are looping.
   - Set `slot06.receiver.force_decay=1.0` via Semantic Mirror to flush stuck pulses.

2. **Inspect Semantic Mirror Contexts**  
   ```bash
   curl -s http://localhost:8000/semantic/context | jq '.slot07'
   ```
   - Ensure `breaker_state != "open"`. If open, resolve Slot7 issues first.

3. **Re-run Cultural Synthesis Health Checks**  
   ```bash
   python -m tests.test_slot6_adapter_logging -k health
   ```

4. **Trigger Guardrail Snapshot**  
   ```bash
   python - <<'PY'
   from nova.slots.slot06_cultural_synthesis.engine import CulturalSynthesisEngine
   eng = CulturalSynthesisEngine()
   print(eng.synthesize({"tri_score": 0.95, "clarity": 0.8}))
   PY
   ```

## 3. Stabilization

- If residual risk stays >0.75 for 15 minutes:
  1. Reduce `SynthesisConfig.tri_min_score` to 0.7.
  2. Increase anomaly pulse multipliers to 1.5 to accelerate decay.
  3. Re-run Slot7 reflex emitter to broadcast lowered pressure.

## 4. Escalation Matrix

| Symptom | Escalate To | Notes |
| --- | --- | --- |
| `slot6_residual_risk_p99 > 0.85` for >30m | Phase steward | Activate deployment hold |
| `slot6_legacy_calls_total` rising | Slot8 owner | Legacy enforcement bypass |
| Contract violations (`slot6_contract_violation`) | Compliance | File incident ticket |

## 5. Post-mortem

- Append findings to `docs/reports/phase14-final-reflection.md` if ledger persistence impacted.
- Update [`docs/slots/slot06_cultural_synthesis.md`](../../docs/slots/slot06_cultural_synthesis.md) with any new flags introduced.

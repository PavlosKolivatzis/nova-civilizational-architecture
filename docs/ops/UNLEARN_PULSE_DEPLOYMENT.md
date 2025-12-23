# UNLEARN_PULSE@1 Production Deployment Guide

## Overview

Nova's Reciprocal Contextual Unlearning system emits UNLEARN_PULSE@1 contracts when semantic mirror contexts expire. This provides structured notifications to slots about context lifecycle events.

> **Scope of Effect:** UNLEARN_PULSE@1 is an observability and coordination mechanism. It does not change regimes or external traffic on its own; behavioral authority remains gated by operator-controlled flags and configuration in the orchestrator.

## Deployment Status

- ✅ **Phase 1**: Observable Pulse prototype implemented
- ✅ **Phase 2**: UNLEARN_PULSE@1 contracts with JsonlEmitter
- 🚧 **Phase 3**: Weight decay in receiving slots (planned)

## Production Controls

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVA_UNLEARN_PULSE_PATH` | `logs/unlearn_pulses.ndjson` | Output path for contract emissions |
| `NOVA_UNLEARN_PULSE_LOG` | `1` | Enable/disable pulse logging (1=on, 0=off) |

### Instant Rollback

**Emergency disable** (no deployment required):
```python
# In orchestrator/app.py, _startup() function:
set_contract_emitter(NoOpEmitter())  # <-- Uncomment this line
# set_contract_emitter(JsonlEmitter())  # <-- Comment this line
```

Reload orchestrator service to apply immediately.

### Safe Deployment Sequence

1. **Enable on staging**: Set custom path via `NOVA_UNLEARN_PULSE_PATH`
2. **Monitor metrics**: `nova_unlearn_pulses_sent_total` should show activity
3. **Verify output**: Check JSONL file contains valid contract records
4. **Enable in production**: Use default path or configure as needed
5. **Monitor alerts**: UnlearnPulseSpike and UnlearnPulseSilence

## Observability

### Prometheus Metrics

```promql
# Delivered pulses per minute (after immunity filtering)
rate(nova_unlearn_pulses_sent_total[5m]) * 60

# Top recipients (who is being asked to unlearn)
topk(5, sum by (slot) (rate(nova_unlearn_pulse_to_slot_total[5m])))

# Context expiration rate
rate(nova_entries_expired_total[5m]) * 60
```

### Alerts

```yaml
- alert: UnlearnPulseSpike
  expr: rate(nova_unlearn_pulses_sent_total[5m]) > 10
  for: 3m
  labels: {severity: warning}
  annotations:
    summary: "Unlearn pulses spiking"
    description: "rate={{ $value }} > 10/min (check upstream TTLs / context churn)."

- alert: UnlearnPulseSilence
  expr: rate(nova_unlearn_pulses_sent_total[15m]) == 0
  for: 30m
  labels: {severity: warning}
  annotations:
    summary: "No unlearn pulses observed"
    description: "Possible stuck cleanup loop or emitter disabled."
```

### JSONL Format

Each emitted contract follows this schema:

```json
{
  "schema_id": "UNLEARN_PULSE",
  "schema_version": 1,
  "key": "slot03.phase_lock",
  "target_slot": "slot03",
  "published_by": "slot04",
  "ttl_seconds": 300.0,
  "access_count": 5,
  "age_seconds": 285.2,
  "scope": "internal",
  "reason": "ttl_expired",
  "ts": 1758828000.0
}
```

## Safety Features

- **Immunity filtering**: Foundational slots (slot01, slot07) never receive pulses
- **Emission threshold**: Only contexts with access_count > 1 and ttl_seconds ≥ 60 emit pulses
- **Error isolation**: Contract emission failures don't break context cleanup
- **Configurable paths**: Avoid conflicts with existing log infrastructure

## Testing

```bash
# Validate emitter binding
python -m pytest tests/flow/test_unlearn_emitter_binding.py -v

# Full regression test
python -m pytest -q --tb=short

# Manual emission test
python -c "
from orchestrator.semantic_mirror import get_semantic_mirror
from orchestrator.contracts.emitter import set_contract_emitter

class LogEmitter:
    def emit(self, contract):
        print(f'CONTRACT: {contract.schema_id}@{contract.schema_version} → {contract.target_slot}')

set_contract_emitter(LogEmitter())
sm = get_semantic_mirror()
sm.publish_context('slot05.test', 'expires_fast', 'test_publisher', ttl_seconds=60, scope='internal')
import time; time.sleep(2)
sm._cleanup_expired_entries(time.time() + 100)
"
```

## Rollback Scenarios

| Scenario | Action | Recovery Time |
|----------|--------|---------------|
| **High emission rate** | Reduce TTLs or increase thresholds | Immediate |
| **Disk space issues** | Change `NOVA_UNLEARN_PULSE_PATH` to `/tmp` | < 1 minute |
| **Complete disable** | Switch to `NoOpEmitter()` + reload | < 2 minutes |
| **Format issues** | Revert to previous JsonlEmitter version | < 5 minutes |

All rollbacks are **non-breaking** - semantic mirror continues normal operation regardless of emitter state.

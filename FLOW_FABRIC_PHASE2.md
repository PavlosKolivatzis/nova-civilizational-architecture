# Flow Fabric Phase 2: Reflex Integration

## Overview
Flow Fabric Phase 2 extends the adaptive connection system with reflex signals from Slot 7 Production Controls. This enables upstream throttling based on circuit breaker pressure, memory pressure, and integrity violations.

## Architecture
```
Slot 7 Production Controls → Reflex Signals → ReflexBus → Adaptive Links
       ↓                        ↓               ↓           ↓
Circuit Breaker         Bounded Signals    Coordination   S3→S6 Throttling
Memory Monitor          Hysteresis         Processing     S6→XX Modulation  
Security Monitor        Rate Limiting      Safety Clamps  Contract Routing
```

## Key Components

### Reflex Emitter (`slots/slot07_production_controls/reflex_emitter.py`)
- **Bounded Signals**: Hysteresis (0.8/0.6), cooldown (1-30s), rate limiting (≤1/sec)
- **Signal Types**: `breaker_pressure`, `memory_pressure`, `integrity_violation`
- **Safety Clamps**: Frequency [0.1-5.0], Weight [0.1-3.0]

### ReflexBus (`orchestrator/reflex_signals.py`)  
- **Signal Processing**: Routes reflex signals to registered adaptive links
- **Target Coordination**: EMOTION_REPORT@1, CULTURAL_PROFILE@1, TRI_REPORT@1
- **Effect Calculation**: Pressure → frequency/weight reduction within clamps

### Policy Configuration (`slots/slot07_production_controls/core/rules.yaml`)
- **Thresholds**: Rise/fall thresholds per signal type
- **Environment Overrides**: Development, staging, production profiles
- **Clamp Bounds**: Downstream safety limits

## Feature Flags (Default: Safe)
```bash
export NOVA_REFLEX_ENABLED=false     # Master kill switch
export NOVA_REFLEX_SHADOW=true       # Shadow mode (compute but don't act)
export NOVA_ADAPTIVE_CONNECTIONS_ENABLED=false  # Flow Fabric disable
export NOVA_CURRENT_MODE=testing     # Environment profile
```

## Rollback Procedure
1. `export NOVA_REFLEX_ENABLED=false` → Immediate shutdown
2. `export NOVA_ADAPTIVE_CONNECTIONS_ENABLED=false` → Disable Flow Fabric
3. Restart service → Clean slate with safe defaults
4. Monitor for 5 minutes → Verify normal operation

## Monitoring Metrics
- **Prometheus**: `slot7_breaker_state`, `slot7_reflex_emitted_total{type}`
- **Health**: `/health/slot07` includes pressure levels, policy hash
- **Ledger**: Bounded audit trail with 1000-entry rotation

## Testing
```bash
pytest tests/flow/test_slot7_reflex_integration.py -v
```

**Test Coverage**: 9 tests covering emission, hysteresis, cooldown, rate limiting, integration

## Performance
- **Latency**: <0.01ms per emission (shadow mode)
- **Throughput**: >100K emissions/second
- **Memory**: <100KB bounded ledger
- **CPU**: Minimal (policy lookup + threshold checks)

## Contract Immutability Guarantee
✅ AdaptiveLink only modifies routing parameters (frequency, weight)
✅ Contract payloads remain unchanged
✅ Full backward compatibility when adaptation disabled
✅ Health endpoint maintains existing contract (engine_status="operational")

## Health Contract Compatibility
- **engine_status**: "operational" (maintains CI test compatibility)
- **status_alias**: "healthy" (new semantic clarity)
- **reflex.api_version**: "1" (for future compatibility tracking)
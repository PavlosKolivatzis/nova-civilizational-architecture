# Nova Production Monitoring Setup

## 🎯 Complete Unlearn Pulse Observability

The Nova system now has **full observability** for the Reciprocal Contextual Unlearning system:

### Live Metrics
- **Nova API**: http://localhost:8000/metrics
- **Dashboard**: http://localhost:9090
- **Health Check**: http://localhost:8000/health

### Key Metrics
- `nova_unlearn_pulses_sent_total`: Total unlearn pulses delivered
- `nova_entries_expired_total`: Contexts expired from semantic mirror
- `nova_unlearn_pulse_to_slot_total{slot="..."}`: Per-slot pulse delivery
- `nova_deployment_gate_open`: Gate status (1=open, 0=closed)

### Production Configuration

**Required Environment Variables:**
```bash
UVICORN_WORKERS=1              # Single worker (shared semantic mirror)
NOVA_ENABLE_PROMETHEUS=1       # Enable metrics export
NOVA_SMEEP_INTERVAL=15         # Sweeper interval (seconds)
NOVA_ALLOW_EXPIRE_TEST=0       # Disable test context seeding in prod
```

**Verification Commands:**
```bash
# Test pulse generation (dev only)
curl -X POST http://localhost:8000/ops/expire-now

# Check live pulse metrics
curl http://localhost:8000/metrics | grep unlearn

# Test accounting invariants
curl -s http://localhost:9090/api/query?query="sum(nova_unlearn_pulse_to_slot_total)-nova_unlearn_pulses_sent_total"
```

## 🚨 Alerts

Production-ready alerts in `nova-alerts.yml`:

1. **UnlearnMetricsMissing** (critical) - Metrics export failure
2. **UnlearnPulseAccounting** (critical) - Per-slot totals don't sum
3. **UnlearnPulseUnderflow** (critical) - More expirations than pulses
4. **UnlearnPulseSilence** (warning) - No pulses for 30 minutes
5. **DeploymentGateOpen** (info) - Gate open alert

**Alert Features:**
- ✅ Delta-based (no restart flapping)
- ✅ Missing series detection
- ✅ Runbook links
- ✅ Dashboard references

## 🔧 Operations

**Normal Operation:**
- Background sweeper runs every 15 seconds
- Contexts expire → unlearn pulses sent
- Immunity respected (no pulses to slot01/slot07)
- Metrics updated real-time

**Troubleshooting:**
- Check sweeper logs: `SemanticMirror sweeper tick: expired=N`
- Verify single worker: `ps aux | grep uvicorn`
- Test context creation: Use `/ops/expire-now` (dev only)

**Rollback:**
- Disable: `NOVA_ENABLE_PROMETHEUS=0`
- Stop sweeper: Restart without `NOVA_SMEEP_INTERVAL`
- Emergency: `NOVA_ALLOW_EXPIRE_TEST=0`

## ✅ Validation

The system successfully demonstrates:
1. **Context expiry** → 1 expired entry
2. **Multi-recipient pulses** → 2 pulses (key slot + publisher slot)
3. **Per-slot accounting** → slot06:1, slot05:1
4. **Immunity enforcement** → No slot01/slot07 recipients
5. **Live metrics** → Real-time dashboard updates

**Unlearn pulse metabolism is fully observable! 🎉**
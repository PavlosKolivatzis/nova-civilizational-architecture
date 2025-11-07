# Phase 16-2: 2-Node Smoke Test

**Goal**: Validate live peer synchronization, Novelty (N) component, and context switching.

**Time**: 30 minutes

**Prerequisites**:
- Phase 16-2 merged to main (commit 24761ae)
- 2 terminal windows or 2 machines
- Ports 8000 and 8001 available

---

## Setup: 2-Node Configuration

### Terminal 1: Node A (Port 8000)

```bash
cd orchestrator

# Set environment
export NOVA_ENABLE_PROMETHEUS=1
export NOVA_WISDOM_GOVERNOR_ENABLED=1
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8001
export NOVA_FED_SYNC_INTERVAL=10
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_WISDOM_G_KAPPA=0.02
export NOVA_WISDOM_G0=0.60

# Start node A
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Terminal 2: Node B (Port 8001)

```bash
cd orchestrator

# Set environment
export NOVA_ENABLE_PROMETHEUS=1
export NOVA_WISDOM_GOVERNOR_ENABLED=1
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8000
export NOVA_FED_SYNC_INTERVAL=10
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_WISDOM_G_KAPPA=0.03
export NOVA_WISDOM_G0=0.55

# Start node B
uvicorn app:app --host 0.0.0.0 --port 8001
```

**Note**: Different κ and G₀ values ensure peer diversity for Novelty calculation.

---

## Validation Checklist

### 1. Startup Verification (2 min)

**Node A**:
```bash
curl -s http://localhost:8000/health | jq '{peer_sync, status}'
```

**Expected**:
```json
{
  "peer_sync": {
    "enabled": true,
    "peer_count": 0,
    "context": "solo",
    "last_sync": null
  },
  "status": "healthy"
}
```

**Node B**:
```bash
curl -s http://localhost:8001/health | jq '{peer_sync, status}'
```

**Expected**: Same structure, peer_count=0, context="solo"

---

### 2. Peer Sync Endpoint Test (2 min)

**Node A summary**:
```bash
curl -s http://localhost:8000/federation/sync/summary | jq
```

**Expected**:
```json
{
  "node_id": "nova-...",
  "ts": 1234567890.123,
  "version": "16.2",
  "metrics": {
    "peer_quality": 0.7,
    "stability_margin": 0.05,
    "hopf_distance": 0.10,
    "spectral_radius": 0.85,
    "gamma": 0.68,
    "g_components": {"progress": 0.0, "novelty": 0.0, "consistency": 1.0},
    "g_star": 0.30
  },
  "sig": null
}
```

**Node B summary**:
```bash
curl -s http://localhost:8001/federation/sync/summary | jq
```

**Expected**: Similar structure with potentially different metrics

---

### 3. Wait for Sync Cycle (15 seconds)

Peer sync interval is 10 seconds. Wait 15s for first sync to complete.

```bash
sleep 15
```

---

### 4. Peer Discovery Verification (3 min)

**Node A - Check peer count**:
```bash
curl -s http://localhost:8000/health | jq .peer_sync
```

**Expected**:
```json
{
  "enabled": true,
  "peer_count": 1,
  "context": "federated",
  "last_sync": 1234567890.123,
  "novelty": 0.05
}
```

**Key checks**:
- ✅ `peer_count: 1` (Node B discovered)
- ✅ `context: "federated"` (switched from "solo")
- ✅ `novelty > 0` (N component active)
- ✅ `last_sync` is recent timestamp

**Node B - Check peer count**:
```bash
curl -s http://localhost:8001/health | jq .peer_sync
```

**Expected**: Same structure, peer_count=1, context="federated", novelty>0

---

### 5. Prometheus Metrics Verification (5 min)

**Node A metrics**:
```bash
curl -s http://localhost:8000/metrics | grep -E "nova_wisdom_peer_count|nova_wisdom_novelty|nova_wisdom_context|nova_wisdom_generativity"
```

**Expected output**:
```
nova_wisdom_peer_count 1.0
nova_wisdom_novelty 0.05
nova_wisdom_context 1.0
nova_wisdom_generativity 0.55
```

**Key checks**:
- ✅ `nova_wisdom_peer_count 1.0` (1 peer discovered)
- ✅ `nova_wisdom_novelty > 0.0` (N component active, not 0.0)
- ✅ `nova_wisdom_context 1.0` (federated mode, was 0.0 initially)
- ✅ `nova_wisdom_generativity > 0.30` (G* above solo cap with N>0)

**Node B metrics**:
```bash
curl -s http://localhost:8001/metrics | grep -E "nova_wisdom_peer_count|nova_wisdom_novelty|nova_wisdom_context|nova_wisdom_generativity"
```

**Expected**: Similar values, all > 0

---

### 6. Peer Diversity Test (5 min)

**Check if peers have divergent G***:

```bash
# Node A G*
curl -s http://localhost:8000/metrics | grep "^nova_wisdom_generativity " | awk '{print "Node A G*: " $2}'

# Node B G*
curl -s http://localhost:8001/metrics | grep "^nova_wisdom_generativity " | awk '{print "Node B G*: " $2}'
```

**Expected**:
```
Node A G*: 0.55
Node B G*: 0.52
```

**Key check**:
- ✅ G* values differ (due to different κ and G₀ settings)
- ✅ Novelty (N) calculated from this variance
- ✅ Both nodes' Novelty reflects peer diversity

---

### 7. Context Switching Test (5 min)

**Stop Node B to trigger context switch back to solo**:

In Terminal 2, press `Ctrl+C` to stop Node B.

**Wait for hysteresis delay (120s default)**:
```bash
sleep 125
```

**Check Node A context switch**:
```bash
curl -s http://localhost:8000/health | jq .peer_sync
```

**Expected**:
```json
{
  "enabled": true,
  "peer_count": 0,
  "context": "solo",
  "last_sync": 1234567890.123,
  "novelty": 0.0
}
```

**Key checks**:
- ✅ `peer_count: 0` (Node B lost)
- ✅ `context: "solo"` (switched back from "federated")
- ✅ `novelty: 0.0` (N=0 in solo mode)
- ✅ Switch took ~120s (hysteresis delay)

**Check Node A metrics**:
```bash
curl -s http://localhost:8000/metrics | grep -E "nova_wisdom_context|nova_wisdom_novelty"
```

**Expected**:
```
nova_wisdom_context 0.0
nova_wisdom_novelty 0.0
```

---

## Success Criteria

Phase 16-2 smoke test **PASSES** if:

1. ✅ Both nodes start without errors
2. ✅ `/federation/sync/summary` returns valid JSON on both nodes
3. ✅ Both nodes discover each other (peer_count=1)
4. ✅ Context switches solo → federated (context=1.0)
5. ✅ Novelty > 0 when peers present (N component active)
6. ✅ G* > 0.30 in federated mode (above solo cap)
7. ✅ Context switches federated → solo after peer loss (120s delay)
8. ✅ Novelty = 0 after returning to solo mode

---

## Troubleshooting

### Issue: peer_count stays 0

**Check**:
```bash
curl -s http://localhost:8000/metrics | grep nova_federation_sync_errors
```

**If errors > 0**: Check firewall, URL format, or peer availability

---

### Issue: context stays "solo"

**Check minimum peer threshold**:
```bash
echo $NOVA_WISDOM_G_MIN_PEERS
```

**Should be**: 1 (default)

**Check peer count**:
```bash
curl -s http://localhost:8000/metrics | grep nova_wisdom_peer_count
```

**Must be**: >= NOVA_WISDOM_G_MIN_PEERS

---

### Issue: Novelty stays 0

**Check peer diversity**:
```bash
# Compare G* values
curl -s http://localhost:8000/federation/sync/summary | jq .metrics.g_star
curl -s http://localhost:8001/federation/sync/summary | jq .metrics.g_star
```

**Must differ** for N > 0. Adjust κ or G₀ if identical.

---

## Logs to Monitor

**Node A logs** (startup):
```
INFO: Peer sync started (peers=1, interval=10s)
```

**Node A logs** (sync cycle):
```
INFO: Peer sync: fetched 1/1 peers successfully
```

**Node A logs** (context switch):
```
INFO: Context switched: solo -> federated (peer_count=1)
```

---

## Next Steps After Smoke Test

### If PASS ✅:
- Document results in `.artifacts/phase-16-2-smoke-test-results.md`
- Proceed to Phase 16 soak test design
- Configure multi-parameter sweep for G* validation

### If FAIL ❌:
- Document failure mode
- Check logs for errors
- Review `.env` configuration
- Verify peer URLs reachable
- Debug peer sync logic

---

## Clean Up

Stop both nodes:
```bash
# Ctrl+C in both terminals
```

Unset environment variables (optional):
```bash
unset NOVA_FED_SYNC_ENABLED NOVA_FED_PEERS
```

---

**Time**: ~30 minutes total
**Risk**: Low (isolated 2-node test)
**Rollback**: Set `NOVA_FED_SYNC_ENABLED=0` to disable

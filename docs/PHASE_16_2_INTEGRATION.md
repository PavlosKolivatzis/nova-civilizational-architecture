# Phase 16-2 Integration Guide

This document specifies the exact changes needed to complete Phase 16-2 integration.

## Status: Foundation Complete ✅

**Completed:**
- ✅ PeerStore & PeerSync (orchestrator/federation_synchronizer.py)
- ✅ GenerativityContext with hysteresis (src/nova/wisdom/generativity_context.py)
- ✅ Peer sync route (orchestrator/routes/peer_sync.py)
- ✅ Environment configuration (.env.example)

**Remaining:** App wiring, metrics, wisdom poller integration

---

## 1. App.py Integration

**File:** `orchestrator/app.py`

### 1.1 Add module-level globals (after line 88)

```python
_peer_store = None
_peer_sync = None
```

### 1.2 Wire peer sync route (after line 404, where federation_router is added)

```python
# Phase 16-2: Peer sync route
try:
    from orchestrator.routes.peer_sync import create_peer_sync_router
    peer_sync_router = create_peer_sync_router()
    if peer_sync_router is not None:
        app.include_router(peer_sync_router)
except Exception:
    logger.warning("Failed to add peer sync router")
```

### 1.3 Start PeerSync in _startup() (after line 342, after wisdom poller)

```python
# Phase 16-2: Peer synchronization
peer_sync_enabled = os.getenv("NOVA_FED_SYNC_ENABLED", "0") == "1"
if peer_sync_enabled:
    try:
        from orchestrator.federation_synchronizer import PeerStore, PeerSync

        global _peer_store, _peer_sync
        _peer_store = PeerStore()
        _peer_sync = PeerSync(_peer_store)
        _peer_sync.start()
        logger.info(
            "Peer sync started (peers=%d, interval=%ss)",
            len(_peer_sync._peers),
            _peer_sync._interval,
        )
    except Exception:
        logger.exception("Failed to start peer sync")
```

### 1.4 Stop PeerSync in _shutdown() (after line 374, after wisdom poller)

```python
# Phase 16-2: Peer synchronization
global _peer_sync
if _peer_sync:
    try:
        _peer_sync.stop()
    except Exception:
        logger.exception("Failed to stop peer sync")
    finally:
        _peer_sync = None
```

---

## 2. Adaptive Wisdom Poller Integration

**File:** `orchestrator/adaptive_wisdom_poller.py`

### 2.1 Add imports at top of file

```python
from nova.wisdom.generativity_core import compute_novelty
from nova.wisdom.generativity_context import get_context, current_g0, ContextState
```

### 2.2 Access PeerStore in poller loop

Find the main polling loop function and add:

```python
# Get live peers for novelty calculation
live_peers = []
try:
    from orchestrator.app import _peer_store
    if _peer_store:
        live_peers = _peer_store.get_live_peers(max_age_seconds=90)
except Exception:
    pass

# Compute novelty from peer diversity
N = compute_novelty(live_peers) if live_peers else 0.0

# Determine context (solo vs federated)
peer_count = len(live_peers)
context = get_context(peer_count)
g0 = current_g0()  # 0.30 for solo, 0.60 for federated

# Use N in G* calculation alongside P and Cc
# (Update compute_gstar call to use actual N instead of 0.0)
```

### 2.3 Store state for /federation/sync/summary endpoint

```python
# Module-level state dict
_wisdom_state = {
    "S": 0.05,
    "H": 0.10,
    "rho": 0.85,
    "gamma": 0.68,
    "g_star": 0.30,
    "g_components": {"progress": 0.0, "novelty": 0.0, "consistency": 1.0},
    "peer_quality": 0.70,
}

def get_state():
    """Get current wisdom state for peer sync endpoint."""
    return _wisdom_state.copy()

# In poller loop, update _wisdom_state with latest values
_wisdom_state.update({
    "S": S,
    "H": H,
    "rho": rho,
    "gamma": gamma_avg,
    "g_star": gstar,
    "g_components": {"progress": P, "novelty": N, "consistency": Cc},
    "peer_quality": compute_peer_quality(S, H, rho),  # or 0.7 default
})
```

---

## 3. Prometheus Metrics

**File:** `orchestrator/prometheus_metrics.py` (or create new file)

### 3.1 Add metric definitions

```python
from prometheus_client import Gauge, Histogram, Counter

# Wisdom context metrics
nova_wisdom_peer_count = Gauge(
    'nova_wisdom_peer_count',
    'Number of live federation peers'
)

nova_wisdom_novelty = Gauge(
    'nova_wisdom_novelty',
    'Novelty (N) component from peer diversity [0,1]'
)

nova_wisdom_context = Gauge(
    'nova_wisdom_context',
    'Generativity context: 0=solo, 1=federated'
)

# Peer sync metrics
nova_federation_sync_latency = Histogram(
    'nova_federation_sync_latency_seconds',
    'Peer sync HTTP request latency',
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

nova_federation_sync_errors = Counter(
    'nova_federation_sync_errors_total',
    'Peer sync error count',
    ['peer_id', 'error_type']
)

nova_federation_peer_last_seen = Gauge(
    'nova_federation_peer_last_seen_timestamp',
    'Unix timestamp when peer was last successfully synced',
    ['peer_id']
)
```

### 3.2 Update metrics in wisdom poller

```python
# In adaptive_wisdom_poller.py loop
nova_wisdom_peer_count.set(peer_count)
nova_wisdom_novelty.set(N)
nova_wisdom_context.set(1.0 if context == ContextState.FEDERATED else 0.0)
```

### 3.3 Update metrics in PeerSync

In `orchestrator/federation_synchronizer.py`, `_fetch_peer()` method:

```python
# After successful fetch
from orchestrator.prometheus_metrics import (
    nova_federation_sync_latency,
    nova_federation_peer_last_seen
)

nova_federation_sync_latency.observe(duration)
nova_federation_peer_last_seen.labels(peer_id=payload.node_id).set(time.time())

# On error
from orchestrator.prometheus_metrics import nova_federation_sync_errors
nova_federation_sync_errors.labels(peer_id=peer_url, error_type="http_error").inc()
```

---

## 4. Health Endpoint Update

**File:** `orchestrator/federation_health.py`

Add peer sync status to health payload:

```python
def get_peer_health():
    # ... existing code ...

    # Phase 16-2: Add peer sync status
    try:
        from orchestrator.app import _peer_store, _peer_sync
        from nova.wisdom.generativity_context import get_context

        peer_count = 0
        context_state = "solo"
        novelty = 0.0

        if _peer_store:
            peers = _peer_store.get_live_peers()
            peer_count = len(peers)

            if peers:
                from nova.wisdom.generativity_core import compute_novelty
                novelty = compute_novelty(peers)

            context = get_context(peer_count)
            context_state = context.value

        health["peer_sync"] = {
            "enabled": bool(_peer_sync),
            "peer_count": peer_count,
            "context": context_state,
            "novelty": novelty,
        }
    except Exception:
        health["peer_sync"] = {"enabled": False, "error": "not_available"}

    return health
```

---

## 5. Testing Integration

### 5.1 Smoke Test

```bash
# Terminal 1: Start first node
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://127.0.0.1:8200
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_ENABLE_PROMETHEUS=1
uvicorn orchestrator.app:app --port 8100 --workers 1

# Terminal 2: Start second node
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://127.0.0.1:8100
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_ENABLE_PROMETHEUS=1
uvicorn orchestrator.app:app --port 8200 --workers 1

# Terminal 3: Verify
curl http://127.0.0.1:8100/federation/sync/summary
curl http://127.0.0.1:8100/metrics | grep nova_wisdom_peer_count
curl http://127.0.0.1:8100/health | jq '.peer_sync'
```

Expected output:
- `/federation/sync/summary` returns valid JSON with metrics
- `nova_wisdom_peer_count` shows 1 (one peer)
- `nova_wisdom_context` shows 1.0 (federated)
- After ~30s, `nova_wisdom_novelty` > 0.0

---

## 6. Verification Checklist

Before committing integration:

- [ ] No import errors on startup
- [ ] `/federation/sync/summary` endpoint responds with valid JSON
- [ ] PeerSync background task starts and stops cleanly
- [ ] Metrics appear at `/metrics` endpoint
- [ ] Health endpoint includes `peer_sync` block
- [ ] Two-node demo shows peer_count=1 and context=federated
- [ ] Novelty > 0 when peers have different g_star values

---

## Files Modified Summary

1. ✅ `.env.example` - Environment variables
2. ✅ `orchestrator/federation_synchronizer.py` - PeerStore & PeerSync
3. ✅ `src/nova/wisdom/generativity_context.py` - Context switching
4. ✅ `orchestrator/routes/peer_sync.py` - FastAPI route
5. ⏳ `orchestrator/app.py` - Lifecycle wiring
6. ⏳ `orchestrator/adaptive_wisdom_poller.py` - Novelty integration
7. ⏳ `orchestrator/prometheus_metrics.py` - New metrics
8. ⏳ `orchestrator/federation_health.py` - Health endpoint update

---

## Next Steps

1. Apply changes to app.py (sections 1.1-1.4)
2. Update adaptive_wisdom_poller.py (section 2)
3. Add Prometheus metrics (section 3)
4. Update health endpoint (section 4)
5. Run smoke test (section 5.1)
6. Verify checklist (section 6)

**Estimated effort:** 30-45 minutes for integration + testing

**Note:** Full test suite (test_peer_sync_*.py, test_context_auto.py, etc.) can be added after integration verification.

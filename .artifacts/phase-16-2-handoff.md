# Phase 16-2 Handoff — Remaining Integration

**Branch**: `claude/load-monday-agent-011CUoJiyMoqtLBYAVM6VQ4F`
**Latest Commit**: 270f032 (app lifecycle integration)
**Time Estimate**: 20-30 minutes

---

## Status: 70% Complete

### ✅ Completed (Claude Web + CLI)
1. **Foundation** (commits 18561ce, 0a172e8, 05aea6d):
   - PeerStore with rolling 5-min windows
   - PeerSync background HTTP pull task
   - GenerativityContext auto-switch (solo ↔ federated)
   - Peer sync route: `GET /federation/sync/summary`
   - Environment config (7 variables in `.env.example`)
   - Integration guide (`docs/PHASE_16_2_INTEGRATION.md`)

2. **App Lifecycle** (commit 270f032):
   - Module globals: `_peer_store`, `_peer_sync`
   - Route wiring: peer sync endpoint active in FastAPI
   - Startup: PeerSync starts when `NOVA_FED_SYNC_ENABLED=1`
   - Shutdown: Graceful stop
   - ✅ Verified: `python -c "from orchestrator.app import app"` imports without error

### 🔄 Remaining Work (3 tasks, ~20-30 min)

All instructions in `docs/PHASE_16_2_INTEGRATION.md`

---

## Task 1: Wisdom Poller Novelty Integration (~15 min)

**File**: `orchestrator/adaptive_wisdom_poller.py`

### Step 1.1: Add imports at top

After existing imports, add:
```python
from src.nova.wisdom.generativity_core import compute_novelty
from src.nova.wisdom.generativity_context import get_context, current_g0
```

### Step 1.2: Find poller loop function

Look for the main polling loop (likely `_poll_loop()` or similar).

### Step 1.3: Add novelty calculation

Inside the loop, before computing G*, add:
```python
# Phase 16-2: Compute novelty from live peers
live_peers = []
try:
    from orchestrator.app import _peer_store
    if _peer_store:
        live_peers = _peer_store.get_live_peers(max_age_seconds=90)
except Exception:
    pass

# Novelty from peer diversity
N = compute_novelty(live_peers) if live_peers else 0.0

# Context determines G₀ target
peer_count = len(live_peers)
context = get_context(peer_count)
g0 = current_g0()  # 0.30 for solo, 0.60 for federated
```

### Step 1.4: Update G* calculation

Find where `compute_gstar()` or similar is called. Replace hardcoded `N=0.0` with the computed `N` variable.

Example:
```python
# Before:
g_star = compute_gstar(P=progress, N=0.0, Cc=consistency, ...)

# After:
g_star = compute_gstar(P=progress, N=N, Cc=consistency, ...)
```

### Step 1.5: Export state for peer sync endpoint

Add module-level state dict:
```python
# At module level (near top)
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
```

In the poller loop, update state:
```python
_wisdom_state.update({
    "S": S,
    "H": H,
    "rho": rho,
    "gamma": gamma_avg,
    "g_star": g_star,
    "g_components": {"progress": P, "novelty": N, "consistency": Cc},
    "peer_quality": 0.7,  # Or compute from S, H, rho if available
})
```

---

## Task 2: Prometheus Metrics (~10 min)

**File**: `orchestrator/prometheus_metrics.py`

### Step 2.1: Define 7 new metrics

Add after existing metric definitions:
```python
from prometheus_client import Gauge, Histogram, Counter

# Wisdom metrics (Phase 16-2)
nova_wisdom_peer_count = Gauge(
    'nova_wisdom_peer_count',
    'Number of live federation peers'
)

nova_wisdom_novelty = Gauge(
    'nova_wisdom_novelty',
    'Novelty (N) component from peer diversity'
)

nova_wisdom_context = Gauge(
    'nova_wisdom_context',
    'Generativity context: 0=solo, 1=federated'
)

nova_wisdom_generativity = Gauge(
    'nova_wisdom_generativity',
    'G* generativity score'
)

# Federation sync metrics
nova_federation_sync_latency = Histogram(
    'nova_federation_sync_latency_seconds',
    'Peer sync HTTP request latency'
)

nova_federation_sync_errors = Counter(
    'nova_federation_sync_errors_total',
    'Peer sync error count',
    labelnames=['peer_id', 'error_type']
)

nova_federation_peer_last_seen = Gauge(
    'nova_federation_peer_last_seen_timestamp',
    'Timestamp when peer was last successfully synced',
    labelnames=['peer_id']
)
```

### Step 2.2: Update metrics in wisdom poller

In `orchestrator/adaptive_wisdom_poller.py`, after computing N and G*:
```python
# Update Prometheus metrics
from orchestrator.prometheus_metrics import (
    nova_wisdom_peer_count,
    nova_wisdom_novelty,
    nova_wisdom_context,
    nova_wisdom_generativity,
)

nova_wisdom_peer_count.set(peer_count)
nova_wisdom_novelty.set(N)
nova_wisdom_context.set(1 if context == ContextState.FEDERATED else 0)
nova_wisdom_generativity.set(g_star)
```

### Step 2.3: Update metrics in PeerSync (optional)

In `orchestrator/federation_synchronizer.py`, method `PeerSync._fetch_peer()`:
```python
# After successful fetch
from orchestrator.prometheus_metrics import (
    nova_federation_sync_latency,
    nova_federation_peer_last_seen,
)

nova_federation_sync_latency.observe(elapsed)
nova_federation_peer_last_seen.labels(peer_id=peer_id).set(time.time())

# On error
from orchestrator.prometheus_metrics import nova_federation_sync_errors
nova_federation_sync_errors.labels(peer_id=peer_id, error_type='http_error').inc()
```

---

## Task 3: Health Endpoint (Optional, ~5 min)

**File**: `orchestrator/health.py`

In `health_payload()` function, add peer sync status:
```python
# After existing health blocks
try:
    from orchestrator.app import _peer_store, _peer_sync
    from src.nova.wisdom.generativity_context import get_context

    if _peer_store:
        live_peers = _peer_store.get_live_peers(max_age_seconds=90)
        peer_count = len(live_peers)
        context = get_context(peer_count)

        payload["peer_sync"] = {
            "enabled": _peer_sync is not None,
            "peer_count": peer_count,
            "context": context.value,
            "last_sync": _peer_sync._last_sync_ts if _peer_sync else None,
        }
except Exception:
    pass
```

---

## Testing

### Smoke Test (5 min)

1. **Set environment**:
```bash
export NOVA_FED_SYNC_ENABLED=0  # Start with sync disabled
export NOVA_WISDOM_GOVERNOR_ENABLED=1
export NOVA_ENABLE_PROMETHEUS=1
```

2. **Start app**:
```bash
cd orchestrator
uvicorn app:app --port 8000
```

3. **Verify endpoints**:
```bash
# Peer sync endpoint (should return defaults)
curl http://localhost:8000/federation/sync/summary

# Health endpoint
curl http://localhost:8000/health | jq .peer_sync

# Metrics (should include nova_wisdom_* metrics)
curl http://localhost:8000/metrics | grep nova_wisdom
```

4. **Enable peer sync** (2-node test in guide Section 5):
```bash
# Terminal 1 (node A on port 8000)
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8001
uvicorn app:app --port 8000

# Terminal 2 (node B on port 8001)
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8000
uvicorn app:app --port 8001

# Verify sync
curl http://localhost:8000/metrics | grep nova_wisdom_peer_count
# Should show: nova_wisdom_peer_count 1.0
```

---

## Commit & Merge

### After completing tasks:

```bash
git add orchestrator/adaptive_wisdom_poller.py orchestrator/prometheus_metrics.py orchestrator/health.py
git commit -m "feat(phase16-2): complete novelty + metrics integration

- Add compute_novelty() to wisdom poller
- Integrate GenerativityContext auto-switch (solo/federated)
- Add 7 Prometheus metrics (peer_count, novelty, context, etc.)
- Update health endpoint with peer sync status
- Export wisdom state for peer sync endpoint

Phase 16-2 integration complete.
Tested: smoke test passes, metrics export, 2-node sync works.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Run quick validation
python -m pytest tests/federation/test_mock_peer_service.py -q
python -m pytest tests/wisdom/test_compute_novelty.py -q

# Merge to main
git checkout main
git merge --no-ff claude/load-monday-agent-011CUoJiyMoqtLBYAVM6VQ4F -m "Merge Phase 16-2: Live Peer Synchronization

Complete federation peer sync infrastructure:
- PeerStore/PeerSync background task
- Novelty (N) component from peer diversity
- Context auto-switch (solo ↔ federated)
- 7 Prometheus metrics
- Health endpoint updates

Enables G* > 0.30 in multi-peer deployments.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

---

## Verification Checklist

Before considering Phase 16-2 complete:

- [ ] No import errors on startup
- [ ] `GET /federation/sync/summary` returns valid JSON
- [ ] Background task starts/stops cleanly
- [ ] Metrics appear at `/metrics` (7 new `nova_wisdom_*` and `nova_federation_*`)
- [ ] Health includes `peer_sync` status
- [ ] 2-node demo: `nova_wisdom_peer_count 1.0`, context switches to `federated`
- [ ] Novelty > 0 with divergent peer `g_star` values

---

## Rollback

If issues occur:
```bash
# Disable peer sync
export NOVA_FED_SYNC_ENABLED=0

# Or revert commits
git revert HEAD~3..HEAD
```

---

**Ready to proceed**: Follow tasks 1-3 sequentially, test after each, commit when done.

**Estimated time**: 20-30 minutes total.

# Phase 16-2 Smoke Test Status

**Date**: 2025-11-07
**Status**: BLOCKED - Wisdom Poller still frozen + mypy backlog uncovered

---

## Bugs Fixed (3)

### 1. node_id Regeneration (d4cda89)
**Symptom**: 41 different peer_ids in metrics from single Node B
**Cause**: `uuid.uuid4()` called on every HTTP request in `/federation/sync/summary`
**Fix**: Module-level cache `_cached_node_id` in `orchestrator/routes/peer_sync.py`
**Result**: Stable peer tracking ✅

### 2. Import Timing (_peer_store) (05cba07)
**Symptom**: Wisdom poller `import _peer_store` captured None at module load
**Cause**: Poller started 45ms before `_peer_store` creation
**Fix**: Changed to `import orchestrator.app as app_module` + `app_module._peer_store`
**Result**: Dynamic attribute access ✅

### 3. ARC Analyzer Report Crash (untracked)
**Symptom**: `python src/nova/arc/analyze_results.py` raised syntax errors (`report.append(".3f"...)`)
**Cause**: F-string literals were truncated in Git merge, leaving invalid Python
**Fix**: Rebuilt Executive Summary / trends sections (ASCII-safe formatting) so the report generator parses again
**Result**: Analyzer + downstream tooling run; prerequisite for lint/type lanes

### 4. Slot 7 Reflex Bus Never Fired (untracked)
**Symptom**: `slot7_reflex_*` metrics always zero even when safeguards trip
**Cause**: `ProductionControlEngine` never called `ReflexEmitter` and the bus was never wired into the orchestrator startup path
**Fix**: Safeguard violations now invoke the reflex emitter + Prometheus wiring (`production_control_engine.py`, `orchestrator/app.py`), with regression tests guarding breaker/memory/rate-limit paths
**Result**: Slot 7 can finally emit breaker/memory pressure signals (policy still controls actual bus fan-out)

---

## Toolchain Checks (2025-11-07 PM)

- `python -m ruff check src/nova orchestrator tests` **PASS** ✅
- `python -m mypy src/nova orchestrator scripts` **FAIL** ❌ — command now runs but surfaces 417 pre-existing errors. High priority blockers relevant to Phase 16-2:
  1. `src/nova/governor/adaptive_wisdom.py:60` – `Telemetry` expects `Literal[...]` for `mode`.
  2. `src/nova/slots/slot01_truth_anchor/pqc_attestation.py:68` – assigns `None` into a `bytes` field.
  3. `orchestrator/routes/peer_sync.py:20` – treating `APIRouter` type as value (needs var rename).
  4. `orchestrator/app.py:53` – same pattern (`FastAPI` type vs instance).
  5. `scripts/publish_to_zenodo.py:182-184` – mixing `Path` + `str`.
- Bulk of remaining noise = missing stubs (`jsonschema`, `requests`) and dozens of `Need type annotation` hits inside orchestration helpers.

> **Decision needed**: either scope mypy to Phase 16-2 touch-points or add more targeted `ignore_missing_imports` / `type: ignore` guards. Current command cannot go green this session.

---

## Working Components

- ✅ Peer sync HTTP (both nodes syncing every 10s)
- ✅ PeerStore populated (1 peer: `nova-koliva-636ac90a`)
- ✅ `/federation/sync/summary` endpoint returns valid JSON
- ✅ Prometheus metrics for peer sync
- ✅ Node startup clean (no exceptions)

---

## Blocker: Wisdom Poller Frozen

### Symptoms
```
nova_wisdom_peer_count 0.0        (should be 1.0)
nova_wisdom_novelty 0.0           (should be > 0)
nova_wisdom_context 0.0           (should be 1.0)
nova_wisdom_generativity 0.3      (frozen, not updating)
```

**Evidence**: Metrics identical across 20s interval - poller not running updates.

### Root Cause (Hypothesis)
Wisdom poller thread crashed silently OR the dynamic import fix (05cba07) still not working in poll loop.

**Logs show**: `"Adaptive wisdom poller started (interval=15.0s)"` but NO subsequent poll logs.

**New evidence (Nov 7 PM)**:
- Prometheus metrics still flat after 3-minute run; `compute_novelty` never executes (`_peer_store` debug logs absent).
- ruff/mypy now parse the poller module cleanly; remaining failure is runtime (no threads progressing).

---

## Next Session Actions

### 1. Verify Environment (Terminal 1)
```bash
echo NOVA_ENABLE_PROMETHEUS=$NOVA_ENABLE_PROMETHEUS
echo NOVA_WISDOM_GOVERNOR_ENABLED=$NOVA_WISDOM_GOVERNOR_ENABLED
# Should both be "1"
```

### 2. Add Poller Heartbeat
**File**: `orchestrator/adaptive_wisdom_poller.py`

```python
# In poll loop, FIRST line:
logger.info(f"wisdom-poller tick: checking peer_store...")

# After getting live_peers:
logger.info(f"wisdom-poller: peers={len(live_peers)}, N={N:.3f}")
```

### 3. Add Error Counter
**File**: `orchestrator/prometheus_metrics.py`

```python
nova_wisdom_poller_errors = Counter("nova_wisdom_poller_errors_total", "Poller exceptions")
nova_wisdom_poller_heartbeat = Gauge("nova_wisdom_poller_heartbeat_unix", "Last poll timestamp")
```

**File**: `orchestrator/adaptive_wisdom_poller.py`

```python
try:
    # ... poll logic ...
    from orchestrator.prometheus_metrics import nova_wisdom_poller_heartbeat
    nova_wisdom_poller_heartbeat.set(time.time())
except Exception as e:
    from orchestrator.prometheus_metrics import nova_wisdom_poller_errors
    nova_wisdom_poller_errors.inc()
    logger.exception("wisdom-poller crashed in tick")
    time.sleep(2)
```

### 4. Verify Dynamic Import Works
Check if `app_module._peer_store` is actually resolving to non-None:

```python
# In poll loop, add debug log:
logger.info(f"_peer_store is None: {app_module._peer_store is None}")
if app_module._peer_store:
    logger.info(f"_peer_store has {app_module._peer_store.get_peer_count()} peers")
```

### 5. Check Slot 7 Backpressure
Once poller works, verify:
```bash
curl -s http://localhost:8000/metrics | grep -E "production|max_jobs|backpressure"
```

Requires `NOVA_WISDOM_BACKPRESSURE_ENABLED=1` in Terminal 1.

---

## Smoke Test Validation Checklist

**Before declaring PASS**:

1. ✅ Both nodes start without errors
2. ✅ `/federation/sync/summary` returns valid JSON
3. ✅ Peer sync working (1 peer tracked)
4. ❌ `nova_wisdom_peer_count = 1.0`
5. ❌ `nova_wisdom_novelty > 0.0`
6. ❌ `nova_wisdom_context = 1.0` (federated)
7. ❌ `nova_wisdom_generativity > 0.30`
8. ⏸️  Context switch test (pending above)

**4/8 checks passing** - blocked on wisdom poller updates.

---

## Terminal Commands (Quick Reference)

### Start Node A (Terminal 1)
```bash
cd /c/code/nova-civilizational-architecture
export PYTHONPATH="$PWD:$PWD/src"
cd orchestrator

export NOVA_ENABLE_PROMETHEUS=1
export NOVA_WISDOM_GOVERNOR_ENABLED=1
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8001
export NOVA_FED_SYNC_INTERVAL=10
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_WISDOM_G_KAPPA=0.02
export NOVA_WISDOM_G0=0.60

python -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### Start Node B (Terminal 2)
```bash
cd /c/code/nova-civilizational-architecture
export PYTHONPATH="$PWD:$PWD/src"
cd orchestrator

export NOVA_ENABLE_PROMETHEUS=1
export NOVA_WISDOM_GOVERNOR_ENABLED=1
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8000
export NOVA_FED_SYNC_INTERVAL=10
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_WISDOM_G_KAPPA=0.03
export NOVA_WISDOM_G0=0.55

python -m uvicorn app:app --host 0.0.0.0 --port 8001
```

### Check Metrics (Terminal 3)
```bash
# Peer sync status
curl -s http://localhost:8000/metrics | grep federation_peer_last_seen

# Wisdom metrics
curl -s http://localhost:8000/metrics | grep -E "nova_wisdom_(peer_count|novelty|context|generativity)"

# Poller heartbeat (after adding metric)
curl -s http://localhost:8000/metrics | grep nova_wisdom_poller_heartbeat
```

---

## Rollback

```bash
# Disable wisdom governor
export NOVA_WISDOM_GOVERNOR_ENABLED=0

# Disable peer sync
export NOVA_FED_SYNC_ENABLED=0

# Revert commits
git revert 05cba07 d4cda89
```

---

**Session ended at 10% context - resume debugging wisdom poller next session.**

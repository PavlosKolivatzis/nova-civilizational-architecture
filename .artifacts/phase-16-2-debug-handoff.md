# Phase 16-2 Debug Handoff — Peer Sync Integration

**Date**: 2025-11-07
**Status**: BLOCKED - Two bugs found, fixes identified
**Branch**: `fix/phase16-2-poller-heartbeat-and-slot7`

---

## Critical Findings

### Bug #1: Wisdom Poller Gets `None` from `get_peer_store()`

**Evidence**:
```
{"timestamp": 1762534863.4706378, "level": "INFO", "logger": "wisdom_poller",
 "message": "wisdom_poller: store_id=None", "module": "adaptive_wisdom_poller",
 "function": "_loop", "line": 243}
```

**Root Cause**: Despite moving peer sync startup before wisdom poller in `orchestrator/app.py:342-378`, the `_peer_store` global is still `None` when `get_peer_store()` is called.

**Hypothesis**: The `global _peer_store` statement inside the startup function's `if peer_sync_enabled:` block may not be executing, OR there's an import-time issue where `adaptive_wisdom_poller` imports `get_peer_store` before app startup completes.

---

### Bug #2: AttributeError in Diagnostic Code

**Evidence**:
```
{"timestamp": 1762534869.5452924, "level": "ERROR",
 "logger": "orchestrator.federation_synchronizer",
 "message": "Unexpected error fetching http://localhost:8001/federation/sync/summary:
 'PeerSync' object has no attribute '_peer_store'",
 "module": "federation_synchronizer", "function": "_fetch_peer", "line": 276}
```

**Root Cause**: Diagnostic log added in `orchestrator/federation_synchronizer.py:236` references `self._peer_store`, but `PeerSync` doesn't store the peer_store with that name.

**Check**:
```python
# Line 186 in federation_synchronizer.py shows:
class PeerSync:
    def __init__(self, peer_store: PeerStore):
        self._peer_store_ref = peer_store  # or just peer_store?
```

Need to verify actual attribute name used in `PeerSync.__init__()`.

---

## Fixes Required

### Fix #1: Ensure `_peer_store` Global is Set

**File**: `orchestrator/app.py:349`

**Current Code**:
```python
global _peer_store, _peer_sync
_peer_store = PeerStore()
_peer_sync = PeerSync(_peer_store)
```

**Verify**:
1. Check if `peer_sync_enabled` evaluates to `True` (add log before `if`)
2. Add log immediately after `_peer_store = PeerStore()`:
   ```python
   logger.info(f"Created _peer_store at startup: id={hex(id(_peer_store))}")
   ```
3. Add log in `get_peer_store()`:
   ```python
   def get_peer_store():
       logger.info(f"get_peer_store() called: _peer_store={_peer_store}, id={hex(id(_peer_store)) if _peer_store else 'None'}")
       return _peer_store
   ```

---

### Fix #2: Correct Diagnostic Attribute Reference

**File**: `orchestrator/federation_synchronizer.py:236`

**Current (broken)**:
```python
self._logger.info(
    f"peersync: stored peer {payload.node_id}, store_id={hex(id(self._peer_store))}, "
    f"peer_count={self._peer_store.get_peer_count()}, g*={payload.metrics.g_star:.3f}"
)
```

**Find correct attribute name**:
```bash
grep -n "def __init__" orchestrator/federation_synchronizer.py
# Look for PeerSync.__init__ signature
grep -A10 "class PeerSync" orchestrator/federation_synchronizer.py
```

**Expected Fix** (assuming attribute is `self.peer_store` or `self._store`):
```python
self._logger.info(
    f"peersync: stored peer {payload.node_id}, store_id={hex(id(self.peer_store))}, "
    f"peer_count={self.peer_store.get_peer_count()}, g*={payload.metrics.g_star:.3f}"
)
```

---

## Files Modified This Session

1. **orchestrator/app.py** (lines 342-378):
   - Moved peer sync startup BEFORE wisdom poller startup
   - Added comment explaining dependency

2. **orchestrator/adaptive_wisdom_poller.py** (lines 237-248):
   - Added diagnostic logging for `peer_store` identity
   - Changed from `log.info("peer_store=present/None")` to showing store ID and peer count

3. **orchestrator/federation_synchronizer.py** (lines 235-238):
   - Added diagnostic logging (BROKEN - wrong attribute name)

---

## Current State

**Both nodes running**:
- Node A: localhost:8000
- Node B: localhost:8001

**Environment variables set**:
```bash
export NOVA_ENABLE_PROMETHEUS=1
export NOVA_WISDOM_GOVERNOR_ENABLED=1
export NOVA_FED_SYNC_ENABLED=1
export NOVA_FED_PEERS=http://localhost:8001  # (8000 for Node B)
export NOVA_FED_SYNC_INTERVAL=10
export NOVA_WISDOM_G_CONTEXT=auto
export NOVA_WISDOM_G_KAPPA=0.02  # (0.03 for Node B)
export NOVA_WISDOM_G0=0.60  # (0.55 for Node B)
```

**Metrics**:
- ✅ Wisdom poller alive (heartbeat advancing, no errors)
- ✅ Peer sync HTTP fetching successfully (200 OK responses)
- ❌ Wisdom poller sees `None` from `get_peer_store()`
- ❌ Peer sync diagnostic log crashes with AttributeError

---

## Investigation Steps for Next Session

### Step 1: Find PeerSync Attribute Name

```bash
cd /c/code/nova-civilizational-architecture
grep -A15 "class PeerSync:" orchestrator/federation_synchronizer.py | grep "def __init__"
```

Expected output will show parameter name used for peer_store.

### Step 2: Add Startup Debug Logs

**File**: `orchestrator/app.py`

Before line 343 (`peer_sync_enabled = os.getenv...`):
```python
logger.info(f"DEBUG: About to check NOVA_FED_SYNC_ENABLED, value={os.getenv('NOVA_FED_SYNC_ENABLED')}")
```

After line 349 (`_peer_store = PeerStore()`):
```python
logger.info(f"DEBUG: Created _peer_store, id={hex(id(_peer_store))}, module_global={hex(id(globals()['_peer_store']))}")
```

In `get_peer_store()` function (line 90):
```python
def get_peer_store():
    """Expose the current PeerStore instance (if initialized)."""
    import sys
    app_module = sys.modules.get('orchestrator.app')
    logger.info(f"DEBUG: get_peer_store() called, _peer_store={_peer_store}, "
                f"app_module._peer_store={getattr(app_module, '_peer_store', 'MISSING')}")
    return _peer_store
```

### Step 3: Fix PeerSync Diagnostic Log

**File**: `orchestrator/federation_synchronizer.py:236`

Replace `self._peer_store` with correct attribute name found in Step 1.

### Step 4: Restart and Capture Logs

Restart both nodes with environment variables, wait 30s, then:

```bash
# Terminal 3
grep -E "DEBUG:|peersync:|wisdom_poller:" /tmp/node_a_startup.log > .artifacts/phase-16-2-debug-trace.txt
```

Look for:
1. "Created _peer_store, id=0x..."
2. "peersync: stored peer ..., store_id=0x..."
3. "wisdom_poller: store_id=0x..."

If IDs match → peer sync and poller see same store, investigate why `get_live_peers()` returns empty.

If IDs differ or missing → `_peer_store` global not being set correctly.

---

## Suspected Root Cause

**Hypothesis**: The `get_peer_store()` function is being imported/called at module load time by `adaptive_wisdom_poller.py:24`, capturing the initial `None` value before app startup runs.

**Check**:
```bash
grep -n "from orchestrator.app import get_peer_store" orchestrator/adaptive_wisdom_poller.py
```

If this import is at the top level (line 24), it's executed when the module loads, but it's importing the *function*, not the variable. The function should still access the current value of `_peer_store` when called.

**Possible Issue**: Circular import or module reload causing two different `orchestrator.app` module instances.

**Test**:
```python
# In adaptive_wisdom_poller.py:239
import sys
app_module_id = id(sys.modules.get('orchestrator.app'))
log.info(f"wisdom_poller: app_module_id={hex(app_module_id)}")
```

Compare with:
```python
# In app.py startup
import sys
logger.info(f"DEBUG: app startup, this module id={hex(id(sys.modules.get('orchestrator.app')))}")
```

If IDs differ → module loaded twice (circular import issue).

---

## Alternative Fix (If Module Issue Persists)

**Make PeerStore a singleton** managed via dependency injection:

**File**: `orchestrator/peer_store_singleton.py` (NEW):
```python
"""Singleton PeerStore instance for app-wide access."""

_instance = None

def init_peer_store(store):
    """Initialize the singleton PeerStore (called once at app startup)."""
    global _instance
    _instance = store

def get_peer_store():
    """Get the singleton PeerStore instance."""
    return _instance
```

**File**: `orchestrator/app.py:349`:
```python
from orchestrator.peer_store_singleton import init_peer_store

_peer_store = PeerStore()
init_peer_store(_peer_store)  # Register singleton
```

**File**: `orchestrator/adaptive_wisdom_poller.py:24`:
```python
from orchestrator.peer_store_singleton import get_peer_store
```

This avoids direct module global access.

---

## Expected Outcome After Fixes

**Logs should show**:
```
[startup] Created _peer_store, id=0x1a2b3c4d
[10s later] peersync: stored peer nova-koliva-xyz, store_id=0x1a2b3c4d, peer_count=1
[15s later] wisdom_poller: store_id=0x1a2b3c4d, peer_count=1
```

**Metrics should show**:
```
nova_wisdom_peer_count 1.0
nova_wisdom_novelty 0.0  # (still 0 with 1 peer, N=std_dev needs 2+ peers)
nova_wisdom_context 1.0  # (federated mode)
nova_wisdom_generativity > 0.30  # (context switched to G₀=0.60)
```

---

## Rollback

```bash
git diff orchestrator/app.py orchestrator/adaptive_wisdom_poller.py orchestrator/federation_synchronizer.py
git checkout orchestrator/app.py orchestrator/adaptive_wisdom_poller.py orchestrator/federation_synchronizer.py
```

Or keep fixes and just disable peer sync:
```bash
export NOVA_FED_SYNC_ENABLED=0
```

---

## Test Commands for Next Session

### Startup (Git Bash, 2 terminals)

**Terminal 1 (Node A)**:
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
python -m uvicorn app:app --host 0.0.0.0 --port 8000 2>&1 | tee /tmp/node_a.log
```

**Terminal 2 (Node B)**:
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
python -m uvicorn app:app --host 0.0.0.0 --port 8001 2>&1 | tee /tmp/node_b.log
```

### Verification (Terminal 3)

```bash
# Wait 30s after both nodes start
sleep 30

# Check for store_id logs
grep -E "Created _peer_store|peersync: stored|wisdom_poller: store_id" /tmp/node_a.log

# Check metrics
curl -s http://localhost:8000/metrics | grep -E "nova_wisdom_(peer_count|novelty|context|generativity)" | grep -v "#"

# Check peer sync status
curl -s http://localhost:8000/metrics | grep federation_peer_last_seen
```

---

**Resume point**: Apply fixes from Steps 1-3, restart nodes, verify store_id consistency.

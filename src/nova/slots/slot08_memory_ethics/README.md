# Slot 8a: Memory Ethics & Protection (Legacy)

## Status: Operational ✅ (Currently Active in Orchestrator)

**Purpose:** Simple ACL-based memory protection with tampering detection

## Architecture Note

**Dual Implementation Strategy:**
- **This implementation (slot08_memory_ethics)**: Legacy simple protection - **CURRENTLY USED** by orchestrator
- **Advanced implementation (slot08_memory_lock)**: Processual 4.0 self-healing system - **MIGRATION-READY**
- **Orchestrator Integration**: `orchestrator/adapters/slot8_memory_ethics.py` imports this implementation

## Components

- `lock_guard.py` - MemoryLock with SHA-256 verification + EthicsGuard ACL system
- `ids_protection.py` - Basic intrusion detection
- `health.py` - Health check integration

## Current Usage

```python
from orchestrator.adapters.slot8_memory_ethics import Slot8MemoryEthicsAdapter

adapter = Slot8MemoryEthicsAdapter()

# Register protected memory with ACL
lock = adapter.register("config", data, actor="admin",
                       readers={"slot01", "slot02"},
                       writers={"admin"})

# Read/write with actor validation
data = adapter.read("config", actor="slot01")
success = adapter.write("config", actor="admin", new_data)
```

## Tests

- `tests/test_slot08_lock_guard_api.py` - ACL and tampering tests
- `tests/test_slot08_mirror_integration.py` - Semantic Mirror integration

## Migration Path

See `slot08_memory_lock/README.md` for advanced Processual 4.0 capabilities:
- Autonomous self-healing with RepairPlanner
- Multi-vector intrusion detection (IDS)
- Cryptographic Merkle tree integrity
- Read-only operational continuity during incidents
- Sub-second quarantine activation (MTTR ≤5s)

**Status**: This legacy implementation remains operational; migration to Processual 4.0 system available when needed.

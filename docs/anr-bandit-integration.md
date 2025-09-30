# ANR Bandit Integration Guide

## Bulletproof Multi-Process State Management

The ANR system now includes cross-platform file locking and atomic writes for bulletproof multi-process deployments.

### Core Components

1. **`orchestrator/anr_mutex.py`** - Cross-platform file locking (Windows msvcrt + Unix fcntl)
2. **`orchestrator/router/anr_bandit.py`** - Production LinUCB with atomic persistence
3. **Legacy compatibility** - Drop-in replacement for existing implementations

### Integration Pattern

```python
# In your ANR router implementation
from orchestrator.router.anr_bandit import LinUCBBandit
from orchestrator.anr_mutex import file_lock, save_json_atomic

class ANRRouter:
    def __init__(self, state_path: str = "run/anr_state.json"):
        self.bandit = LinUCBBandit(
            arms=["R1", "R2", "R3", "R4"],
            context_dim=5,  # Adjust based on your context features
            alpha=1.0,
            state_path=state_path,
            save_interval=10  # Save every 10 updates
        )

    def route_decision(self, context_features: List[float]) -> str:
        """Make routing decision with LinUCB."""
        arm, metadata = self.bandit.select_arm(context_features)

        # Log decision metadata for observability
        logger.info(f"ANR decision: {arm}", extra={
            "arm": arm,
            "confidence": metadata["confidence_bound"],
            "total_pulls": metadata["total_pulls"]
        })

        return arm

    def update_reward(self, reward: float) -> bool:
        """Update bandit with outcome reward."""
        return self.bandit.update_reward(reward)

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive diagnostics."""
        return self.bandit.get_diagnostics()
```

### Multi-Process Safety

The new implementation provides:

1. **Cross-platform file locking**:
   - Windows: `msvcrt.locking` (byte-level lock)
   - Unix: `fcntl.flock` (advisory lock)
   - Timeout with polling to prevent deadlocks

2. **Atomic writes**:
   - Write to temporary file in same directory
   - `fsync()` before rename (crash safety)
   - `os.replace()` for atomic rename
   - Directory fsync for durability

3. **Deterministic JSON**:
   - Sorted keys for consistent diffs
   - UTF-8 encoding without BOM
   - Compact format (no indentation)

### Testing Multi-Process Safety

```python
# Test concurrent writers (simulate multi-process)
import threading
from orchestrator.anr_mutex import file_lock, save_json_atomic

def stress_test_concurrent_writes():
    state_path = "run/anr_state.json"
    lock_path = f"{state_path}.lock"

    def writer_thread(thread_id: int):
        for i in range(100):
            with file_lock(lock_path, timeout=5.0):
                # Simulate bandit state update
                state = {
                    "thread_id": thread_id,
                    "iteration": i,
                    "timestamp": time.time()
                }
                save_json_atomic(state_path, state)
            time.sleep(0.001)  # Small delay

    # Launch 5 concurrent writers
    threads = [
        threading.Thread(target=writer_thread, args=(i,))
        for i in range(5)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify final state is valid JSON
    with open(state_path, 'rb') as f:
        final_state = json.load(f)
    print(f"Final state valid: {final_state}")

# Run the test
stress_test_concurrent_writes()
```

### Environment Configuration

```python
# Configuration for production deployment
ANR_CONFIG = {
    "state_path": os.getenv("NOVA_ANR_STATE_PATH", "run/anr_state.json"),
    "save_interval": int(os.getenv("NOVA_ANR_SAVE_INTERVAL", "10")),
    "lock_timeout": float(os.getenv("NOVA_ANR_LOCK_TIMEOUT", "10.0")),
    "alpha": float(os.getenv("NOVA_ANR_ALPHA", "1.0")),
}
```

### Prometheus Metrics Integration

```python
# Add state write error metrics
from prometheus_client import Counter

anr_state_write_errors = Counter(
    'nova_anr_state_write_errors_total',
    'Total ANR state write errors'
)

class LinUCBBandit:
    def _save_state(self) -> bool:
        try:
            # ... existing save logic ...
            return True
        except Exception as e:
            anr_state_write_errors.inc()
            logger.error(f"Failed to save ANR state: {e}")
            return False
```

### Health Monitoring

```python
# Add to Slot 10 health checks
def check_anr_state_freshness(state_path: str, max_age_minutes: int = 60) -> bool:
    """Verify ANR state file is being updated regularly."""
    try:
        if not os.path.exists(state_path):
            return False

        mtime = os.path.getmtime(state_path)
        age_minutes = (time.time() - mtime) / 60

        return age_minutes <= max_age_minutes
    except Exception:
        return False
```

### Rollback and Recovery

```python
# Emergency procedures for state corruption
def reset_anr_state(state_path: str) -> bool:
    """Reset ANR state to clean slate (emergency use)."""
    try:
        if os.path.exists(state_path):
            backup_path = f"{state_path}.backup.{int(time.time())}"
            os.rename(state_path, backup_path)
            logger.warning(f"ANR state reset, backup saved: {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to reset ANR state: {e}")
        return False

def restore_anr_state(backup_path: str, state_path: str) -> bool:
    """Restore ANR state from backup."""
    try:
        # Validate backup is loadable
        with open(backup_path, 'rb') as f:
            json.load(f)

        # Atomic restore
        lock_path = f"{state_path}.lock"
        with file_lock(lock_path, timeout=10.0):
            os.replace(backup_path, state_path)

        logger.info(f"ANR state restored from {backup_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to restore ANR state: {e}")
        return False
```

### Production Deployment Checklist

1. ✅ **File permissions**: Ensure write access to state directory
2. ✅ **Lock timeout**: Configure appropriate timeout for your workload
3. ✅ **Save interval**: Balance between durability and performance
4. ✅ **Monitoring**: Track state write errors and freshness
5. ✅ **Backup strategy**: Regular state backups with retention
6. ✅ **Recovery plan**: Procedures for state corruption or loss

### Performance Characteristics

- **Lock acquisition**: ~1ms typical, configurable timeout
- **Atomic write**: ~5-10ms for typical state size (<1KB)
- **Memory usage**: O(arms × context_dim²) for LinUCB matrices
- **Disk usage**: ~1KB per state snapshot

### Future Enhancements

- **Distributed coordination**: Redis-based locking for multi-node
- **State compression**: gzip for large context dimensions
- **Incremental updates**: Delta-based persistence for high frequency
- **Backup automation**: Automated state archival with retention
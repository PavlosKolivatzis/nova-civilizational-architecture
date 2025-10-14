# NOVA Slot 10 - Surgical Patches Guide

## Overview
Three small patches to integrate enhanced Slot 6 with existing Slot 10 code.

## Prerequisites
- Have your existing Slot 10 files open in Acode
- Use Ctrl+F to search for the exact strings below

---

## Patch 1: MetaLegitimacySeal - Threat Level Bridge

### What to find
Search for: `def _screen_with_slot2(self, plan_snapshot: Dict[str, Any]) -> Dict[str, Any]:`

### What to replace
Replace the entire `_screen_with_slot2` method with:

```python
def _screen_with_slot2(self, plan_snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """Screen deployment plan through Slot 2 ΔTHRESH."""
    try:
        slot2 = self.slot_managers[2]
        content = json.dumps(plan_snapshot, sort_keys=True)
        result = slot2.process_content(content, 'deployment_verification')

        # Compatibility bridge: compute threat if Slot 2 lacks it
        layer_scores = getattr(result, 'layer_scores', {}) or {}
        tri_score    = float(getattr(result, 'tri_score', 1.0))
        tri_min      = float(getattr(getattr(slot2, 'config', type('C', (), {'tri_min_score': 0.8})), 'tri_min_score', 0.8))
        risk = max(layer_scores.values()) if layer_scores else 0.0
        tri_gap = max(0.0, tri_min - tri_score)
        threat_level = getattr(result, 'threat_level', None)
        if threat_level is None:
            threat_level = min(1.0, 0.5 * risk + 0.5 * tri_gap)
        return {
            'threat_level': float(threat_level),
            'patterns_detected': list(getattr(result, 'patterns_detected', [])) or list(layer_scores.keys())
        }
    except Exception:
        return {'threat_level': 0.0, 'patterns_detected': []}
```

---

## Patch 2: InstitutionalNodeDeployer - Rate Limiting

### Part A: Add import
Add to your imports:

```python
from collections import deque
```

### Part B: Add rate limiting storage
Search for `def __init__(self, phase_space_sim, slot_managers: Dict[int, Any]):`.
Find the line `self.node_signatures: Dict[str, str] = {}` and add the following line right after it:

```python
self._deploy_ts = deque(maxlen=256)  # rolling timestamps for rate limiting
```

### Part C: Update health monitoring signature
Search for `async def monitor_node_health(self):` and replace it with:

```python
async def monitor_node_health(self, stop_event: Optional[asyncio.Event] = None):
    """Monitor health of all deployed nodes with cultural factors (cancellable)."""
    while not (stop_event and stop_event.is_set()):
        ...
```

### Part D: Add rate limiting to deployment
Search for `async def deploy_institutional_node(self, institution_name: str, node_type: NetworkNodeType,`.
Find the line `deployment_start = time.time()` and add this block right after it:

```python
# Rate limiting check
now = time.time()
one_hour_ago = now - 3600.0
while self._deploy_ts and self._deploy_ts[0] < one_hour_ago:
    self._deploy_ts.popleft()
if len(self._deploy_ts) >= self.deployment_config.get('deployment_rate_limit_per_hour', 10):
    return {
        'success': False,
        'reason': 'rate_limited',
        'window': '1h',
        'limit': self.deployment_config.get('deployment_rate_limit_per_hour', 10)
    }
```

---

## Patch 3: CivilizationalOrchestrator - Health Management + Diversity

### Part A: Add import
Add to the top of the file:

```python
import contextlib
```

### Part B: Update orchestrator initialization
Search for `def __init__(self, slot_managers: Dict[int, Any]):`.
Find `self.monitoring_active = True` and replace the line `self._start_monitoring_loop()` with:

```python
self._stop_event = asyncio.Event()
self._health_task = None
self._start_monitoring_loop()
```

### Part C: Replace monitoring loop
Search for `def _start_monitoring_loop(self):` and replace the entire method with:

```python
def _start_monitoring_loop(self):
    """Start autonomous monitoring loop."""

    def monitoring_thread():
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()

        # also run health monitor with stop event
        async def runner():
            # start node health task
            self._health_task = asyncio.create_task(
                self.node_deployer.monitor_node_health(stop_event=self._stop_event)
            )
            try:
                await self._autonomous_monitoring_loop()
            finally:
                self._stop_event.set()
                if self._health_task:
                    self._health_task.cancel()
                    with contextlib.suppress(Exception):
                        await self._health_task

        loop.run_until_complete(runner())

    monitoring_thread_obj = threading.Thread(target=monitoring_thread, daemon=True)
    monitoring_thread_obj.start()
```

### Part D: Update intervention calculations
Search for `async def _evaluate_and_execute_interventions(self):`.
Find the line `cultural_health = self.cultural_metrics['principle_preservation_rate']` and add the following lines right after it:

```python
diversity = self.cultural_metrics.get('cultural_diversity_index', 0.0)
diversity_gap = max(0.0, 0.9 - diversity)  # target ~0.9 Shannon
```

Then find the line `combined_risk = (1 - current_stability) * 0.5 + threat_risk * 0.3 + cultural_risk * 0.2` and replace it with:

```python
combined_risk = (1 - current_stability) * 0.45 + threat_risk * 0.35 + cultural_risk * 0.10 + diversity_gap * 0.10
```

### Part E: Update diversity optimization
Search for `async def _optimize_cultural_diversity(self):` and replace the entire method with:

```python
async def _optimize_cultural_diversity(self):
    """Optimize cultural diversity across the network."""
    self.logger.info("🌈 Optimizing cultural diversity")
    # Minimal nudge: flag one over-represented bucket for redeploy
    status = self.node_deployer.get_deployment_status()
    dist = status['health_summary'].get('cultural_adaptation_distribution', {})
    if dist:
        # naive policy: if 'low_adaptation' dominates, prefer deploying one more with higher adaptation
        if dist.get('low_adaptation', 0) > (dist.get('high_adaptation', 0) + dist.get('medium_adaptation', 0)):
            self.logger.info("Rebalance hint: prioritize institutions with stronger adaptation readiness")
```

---

## Summary of Changes
- **Patch 1:** Adds threat level compatibility bridge (1 method replacement)
- **Patch 2:** Adds rate limiting and cancellable health monitoring (4 small additions)
- **Patch 3:** Adds diversity weighting and health task management (5 small changes)
- Total: ~30 lines of changes across your existing codebase.

# Nova Phase 3 — Production Runbook (Cutover & Triage)

## Cutover (Day-0)
**POSIX**
```bash
export PYTHONPATH=.; export NOVA_SEMANTIC_MIRROR_ENABLED=true; export NOVA_SEMANTIC_MIRROR_SHADOW=false
python - <<'PY'
from orchestrator.semantic_mirror_setup import setup_semantic_mirror_integration, get_semantic_mirror_health
from orchestrator.semantic_mirror import publish
setup_semantic_mirror_integration()
publish("slot07.cutover_tick", {"ok":1}, "slot07_production_controls", ttl=120.0)
print(get_semantic_mirror_health())
PY
python scripts/semantic_mirror_dashboard.py --compact --once
```

**Windows (PowerShell)**
```powershell
$env:PYTHONPATH="."; $env:NOVA_SEMANTIC_MIRROR_ENABLED="true"; $env:NOVA_SEMANTIC_MIRROR_SHADOW="false"
python - <<'PY'
from orchestrator.semantic_mirror_setup import setup_semantic_mirror_integration, get_semantic_mirror_health
from orchestrator.semantic_mirror import publish
setup_semantic_mirror_integration()
publish("slot07.cutover_tick", {'ok':1}, 'slot07_production_controls', ttl=120.0)
print(get_semantic_mirror_health())
PY
python scripts\semantic_mirror_dashboard.py --compact --once
```

## Monitoring (Serve + Heartbeat)

* Terminal A: `python scripts/semantic_mirror_dashboard.py --serve 8787 --watch --interval 5`
* Terminal B: publish a heartbeat to show activity:

  ```bash
  export PYTHONPATH=.; python - <<'PY'
  from orchestrator.semantic_mirror import publish
  publish("slot07.heartbeat", {"tick":1}, "slot07_production_controls", ttl=180.0)
  print("heartbeat")
  PY
  ```

## Acceptance Gates

* hit ≥ 0.85, deny ≤ 0.05, rl ≈ 0.00, active > 0
* Quick asserts: all `OK:`
* Flow integration tests: pass

## Rollback (Kill Switch)

```bash
python scripts/semantic_mirror_flip.py --disable --shadow
```

## Triage Cheatsheet

* **active=0** (≥2 intervals): publish heartbeat, verify flags; if persists → rollback.
* **deny > 10% (3+ probes):** ACL drift/typo or TTL too short — review rules, bump TTL if needed.
* **rl > 0.5% (twice):** identify bursty requester; reduce QPM / widen interval.

## Process Semantics (Important)

* Semantic Mirror is **in-process**. Each CLI invocation starts **empty**.
* Use `--serve` or single-process probes for live visibility.
# Nova Semantic Mirror — Daily Operations (Day-1 → Day-7)

## Micro-Ritual (≤3 min)
- `python scripts/semantic_mirror_dashboard.py --compact --once` (log line)
- `python scripts/semantic_mirror_quick_asserts.py` (expect all `OK:`)
- End-of-day: `python scripts/semantic_mirror_dashboard.py --once >> daily_snapshots.txt`

> Shortcut: source `ops/nova-shortcuts.sh` then run `nova-pulse` (auto-decode + self-heal).

## "Good Day" Thresholds
- hit ≥ **0.85**
- deny ≤ **0.05**
- rl ≈ **0.00**
- active **> 0**
- Quick asserts: all **OK**

## Rapid Triage
| Issue                    | First Action                                      |
|-------------------------|---------------------------------------------------|
| `active=0`              | Publish heartbeat in same shell; re-probe         |
| `deny > 10%` (3+ probes)| Review ACL changes/typos; consider TTL bump       |
| `rl > 0.5%` (twice)     | Identify bursty requester; reduce QPM / widen int |

## Escalation
- **P0:** `active=0` (≥2 intervals) or any sentinel **FAIL** → invoke kill switch:
  `python scripts/semantic_mirror_flip.py --disable --shadow`
- **P1:** deny spike / rl drift without impact → investigate same day
- **P2:** optics-only quirks (empty probe/flag display) → document only

## Weekly Audit (Day-7)
- `python scripts/semantic_mirror_dashboard.py --once --csv week_metrics.csv`
- Confirm anchors: hit ≥ 0.85, deny ≤ 0.05, rl ≈ 0.00, active > 0
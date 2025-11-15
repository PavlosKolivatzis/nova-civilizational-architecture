# ANR Week-1 Daily Checklist (5 minutes)

## Essential Gates (Check Daily)

- [ ] **RSI ≥ 0.85** (24h window) → `python scripts/anr_daily_report.py --ledger run/anr_ledger.ndjson`
- [ ] **Rollbacks ≤ 0.1 / 1k live decisions**
- [ ] **TRI median ≥ 0** (if present)
- [ ] **No fast-cap breaches** (R3 ≤ 0.15 under anomaly)
- [ ] **Critical slots healthy** (04 / 08_lock / 09 / 10) → `curl -s http://localhost:8001/health/slots`

## System Health (Quick Checks)

- [ ] **Bandit state advancing** (mtime < 6h) → `Get-Item run/anr_state.json | Select LastWriteTime`
- [ ] **Latest receipt complete** → Check `build_sha`, `env_snapshot_path`, `runbook_url`
- [ ] **Ledger archives rotating** → `Get-ChildItem run/anr_ledger_archive/*.zip`
- [ ] **Backups present** → `Get-ChildItem run/anr_state_backups/*.json`

## Automation Validation

- [ ] **Auto-promotion dry-run green?** → `.\ops\anr-pilot.ps1 -Auto -DryRun -RequireTRI`
- [ ] **Build metrics visible** → `curl -s :8000/metrics | findstr nova_build_info`

## Escalation Triggers

**Escalate immediately if:**
- Any gate shows red status for >2h
- Stalled learning (state mtime > 6h during live traffic)
- Repeated fast-cap breaches (>3 in 1h)
- Auto-promotion consistently failing dry-run

## Weekly Tasks

- [ ] **Monday**: Run DR drill → `.\ops\anr-dr-drill.ps1`
- [ ] **Wednesday**: Review promotion receipts for patterns
- [ ] **Friday**: Verify ledger rotation working → Check archive count

---

**Emergency Contacts:**
- Immediate rollback: `.\ops\anr-pilot.ps1 -Rollback`
- Runbook: See `runbook_url` in latest receipt
- On-call escalation: [Your escalation path here]

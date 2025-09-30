# ANR Operations Runbook

## Daily Operations

### Automated Daily Promotion
```powershell
# Scheduled daily at 09:05 via Windows Task Scheduler
.\ops\anr-autopromo-daily.ps1
```

**What it does:**
1. Generates fresh 24h metrics report from ledger
2. Runs auto-promotion with TRI enforcement
3. File lock prevents double-execution (30m stale protection)

### Schedule Setup (Windows Task Scheduler)
```powershell
schtasks /Create /SC DAILY /TN "Nova ANR AutoPromotion" /TR "powershell -ExecutionPolicy Bypass -File C:\code\nova-civilizational-architecture\ops\anr-autopromo-daily.ps1" /ST 09:05
```

## Emergency Procedures

### Immediate Rollback
```powershell
# Forces R4 guardrail (ANR disabled)
.\ops\anr-pilot.ps1 -Rollback
```

### Freeze on Page
If any ANR alert fires (RSI < 0.85, rollbacks > 0.1/1k, fast-cap breach):
1. Disable scheduled task: `schtasks /Change /TN "Nova ANR AutoPromotion" /DISABLE`
2. Force rollback: `.\ops\anr-pilot.ps1 -Rollback`
3. Set environment: `$env:NOVA_ANR_ENABLED="0"`
4. Investigate root cause before re-enabling

## Go/No-Go Criteria for 100% Deployment

Promote only if last 24h meets ALL criteria:
- ✅ RSI ≥ **0.85** (route selection quality)
- ✅ Rollbacks ≤ **0.1 / 1k live decisions** (deployment stability)
- ✅ Median TRI Δ ≥ **0** (truth coherence maintained)
- ✅ No fast-cap breaches (R3 ≤ **0.15** under anomaly)
- ✅ Critical slots health: 04/08_lock/09/10 all green

## Maintenance Commands

### Manual Promotion
```powershell
# Preview auto-promotion (safe)
.\ops\anr-pilot.ps1 -Auto -DryRun

# Manual stage promotion
.\ops\anr-pilot.ps1 -Stage 25

# Auto with TRI enforcement (production mode)
.\ops\anr-pilot.ps1 -Auto -RequireTRI
```

### State Management
```powershell
# Backup bandit state (keep 7 days)
.\ops\backup-anr-state.ps1

# Restore state (replace with backup)
Copy-Item .\run\anr_state_backups\anr_state_YYYYMMDD_HHMMSS.json .\run\anr_state.json
```

### Reports and Metrics
```powershell
# Generate daily report manually
python scripts\anr_daily_report.py --ledger run\anr_ledger.ndjson

# View recent receipts
Get-ChildItem ops\logs\anr_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

## Operational Guardrails

### Single Writer Requirement
- Keep uvicorn `--workers 1` on router process
- OR gate bandit state writes behind mutex for multi-process

### Retention Policies
- **Receipts**: Prune `ops/logs/anr_*.json` older than 90 days weekly
- **State backups**: Keep 7 most recent (automatic in backup script)
- **Ledger**: Archive monthly, keep 12 months

### Monitoring Integration
- Prometheus alerts configured in `ops/prometheus-anr-rules.yaml`
- Add to your Prometheus rules configuration
- Configure alertmanager routing for ANR component alerts

## Troubleshooting

### Common Issues
1. **Lock file stuck**: Remove `run\anr_autopromo.lock` if job hangs
2. **Missing ledger**: Auto-promotion will use N/A metrics (fails gates)
3. **State corruption**: Restore from backup or delete to reinitialize
4. **Permission errors**: Ensure script execution policy allows PowerShell

### Debug Mode
```powershell
# Test with verbose output
.\ops\anr-pilot.ps1 -Auto -DryRun -ReportPath .\run\anr_daily_report.json -Verbose
```

### Health Checks
```powershell
# Verify environment
$env:NOVA_ANR_ENABLED
$env:NOVA_ANR_PILOT

# Check state file
Get-Content run\anr_state.json | ConvertFrom-Json | Format-Table

# Test readiness
python scripts\verify_pilot_ready.py
```
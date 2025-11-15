# ANR Week-1 Operations Checklist

## Daily Watch List (5 min/day)

### Key Metrics Validation
```powershell
# Check latest daily report
Get-Content run\anr_daily_report.json | ConvertFrom-Json | Select-Object rsi, rollbacks, tri_median, decisions
```

**Green Criteria:**
- ✅ **RSI ≥ 0.85** (route selection quality)
- ✅ **Rollbacks ≤ 0.1/1k** (deployment stability)
- ✅ **TRI median ≥ 0** (truth coherence maintained)
- ✅ **Decisions > 100** (sufficient traffic volume)

### System Health Checks
```powershell
# Verify bandit state file is updating
$stateFile = "run\anr_state.json"
if (Test-Path $stateFile) {
  $age = ((Get-Date) - (Get-Item $stateFile).LastWriteTime).TotalMinutes
  Write-Host "Bandit state age: $([math]::Round($age,1)) minutes"
  if ($age -gt 60) { Write-Host "⚠️ State file stale" -ForegroundColor Yellow }
}

# Check backup rotation
Get-ChildItem run\anr_state_backups\*.json | Sort-Object LastWriteTime -Desc | Select-Object -First 3 | Format-Table Name, LastWriteTime, Length
```

### Prometheus Alerts Monitor
- No **fast-cap breaches** (R3 ≤ 0.15 during anomaly windows)
- No **RSI degradation** alerts
- No **rollback rate** threshold breaches
- **Bandit state freshness** within 1 hour

## Weekly Tasks

### DR Drill (10 minutes)
```powershell
# Test disaster recovery
.\ops\anr-dr-drill.ps1

# Verify graceful restart
# (Restart your app service to confirm learn-on-start)
```

### Environment Audit
```powershell
# Review environment snapshots
Get-ChildItem run\anr_env_*.txt | Sort-Object LastWriteTime -Desc | Select-Object -First 5

# Check receipt audit trail
Get-ChildItem ops\logs\anr_*.json | Sort-Object LastWriteTime -Desc | Select-Object -First 10 | ForEach-Object {
  $receipt = Get-Content $_.FullName | ConvertFrom-Json
  "$($receipt.ts) - $($receipt.action) - Stage $($receipt.stage) - SHA $($receipt.git_sha)"
}
```

### Performance Review
```powershell
# Analyze promotion history
Get-ChildItem ops\logs\anr_*.json | ForEach-Object {
  $r = Get-Content $_.FullName | ConvertFrom-Json
  if ($r.action -eq "promote") {
    [PSCustomObject]@{
      Timestamp = $r.ts
      Stage = $r.stage
      RSI = $r.summary.rsi
      Rollbacks = $r.summary.rollbacks
      GitSHA = $r.git_sha
    }
  }
} | Sort-Object Timestamp | Format-Table
```

## Safety Procedures

### Immediate Response Commands
```powershell
# Preview current promotion status
.\ops\anr-pilot.ps1 -Auto -DryRun -RequireTRI

# Emergency rollback (R4 guardrail)
.\ops\anr-pilot.ps1 -Rollback

# Manual stage control
.\ops\anr-pilot.ps1 -Stage 10  # Back to 10% pilot
.\ops\anr-pilot.ps1 -Stage 25  # Advance to 25%
```

### Auto-Promotion Control
```powershell
# Disable daily automation (during issues)
schtasks /Change /TN "Nova ANR AutoPromotion" /DISABLE

# Re-enable after 24h green at current stage
schtasks /Change /TN "Nova ANR AutoPromotion" /ENABLE
```

### Chaos Testing
```powershell
# Test instant rollback response
.\ops\anr-pilot.ps1 -Rollback
Start-Sleep 30
.\ops\anr-pilot.ps1 -Stage 10  # Verify quick recovery
```

## Graduation Criteria

### Stage Progression Gates
- **Stage 10% → 25%**: 48h green metrics, no alerts
- **Stage 25% → 50%**: 72h green metrics, TRI positive trend
- **Stage 50% → 75%**: 96h green metrics, decision volume stable
- **Stage 75% → 100%**: 7 days green metrics, full confidence

### Auto-Promotion Enablement
**Enable daily job ONLY after:**
1. ✅ Manual 10% stage runs 24h without issues
2. ✅ All gates consistently green in dry-run mode
3. ✅ DR drill passes successfully
4. ✅ Manual promotion/rollback tested

```powershell
# Final enablement command
schtasks /Change /TN "Nova ANR AutoPromotion" /ENABLE
Write-Host "🚀 Auto-promotion ENABLED - monitoring begins" -ForegroundColor Green
```

## Troubleshooting Quick Reference

### State File Issues
```powershell
# Reset corrupted state (emergency)
Remove-Item run\anr_state.json
# Bandit will reinitialize on next decision

# Restore from backup
.\ops\anr-dr-drill.ps1
```

### Promotion Failures
```powershell
# Debug gate failures
.\ops\anr-pilot.ps1 -Auto -DryRun -Verbose

# Force manual promotion (bypass gates)
.\ops\anr-pilot.ps1 -Stage 25  # Manual override
```

### Lock File Issues
```powershell
# Clear stuck promotion lock
Remove-Item run\anr_autopromo.lock -ErrorAction SilentlyContinue
```

---

**Week-1 Success**: All daily checks green, smooth stage progression, auto-promotion functioning, team confident with emergency procedures.

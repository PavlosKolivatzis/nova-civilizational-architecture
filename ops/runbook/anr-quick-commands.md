# ANR Quick Command Reference

## 🚀 Daily Operations

```powershell
# Daily auto-promotion job (scheduled)
.\ops\anr-autopromo-daily.ps1

# Preview what auto-promotion would do (safe)
.\ops\anr-pilot.ps1 -Auto -DryRun

# Manual promotion to specific stage
.\ops\anr-pilot.ps1 -Stage 25
```

## 🛡️ Emergency Controls

```powershell
# IMMEDIATE ROLLBACK (forces R4 guardrail)
.\ops\anr-pilot.ps1 -Rollback

# Disable scheduled auto-promotion
schtasks /Change /TN "Nova ANR AutoPromotion" /DISABLE

# Re-enable scheduled auto-promotion
schtasks /Change /TN "Nova ANR AutoPromotion" /ENABLE
```

## 📊 Monitoring & Reports

```powershell
# Generate fresh metrics report
python scripts\anr_daily_report.py --ledger run\anr_ledger.ndjson

# View recent promotion receipts
Get-ChildItem ops\logs\anr_*.json | Sort-Object LastWriteTime -Desc | Select-Object -First 5

# Check current environment
echo "Enabled: $env:NOVA_ANR_ENABLED | Pilot: $env:NOVA_ANR_PILOT"

# View last receipt
Get-Content (Get-ChildItem ops\logs\anr_*.json | Sort-Object LastWriteTime -Desc | Select-Object -First 1).FullName | ConvertFrom-Json | Format-Table
```

## 🔧 State Management

```powershell
# Backup bandit state (keeps 7 days)
.\ops\backup-anr-state.ps1

# Restore from backup
Copy-Item ".\run\anr_state_backups\anr_state_YYYYMMDD_HHMMSS.json" ".\run\anr_state.json"

# Reset bandit state (fresh learning)
Remove-Item run\anr_state.json
```

## 🧪 Testing & Validation

```powershell
# Test pilot readiness
python scripts\verify_pilot_ready.py

# Auto-promotion with TRI enforcement (production mode)
.\ops\anr-pilot.ps1 -Auto -RequireTRI

# Test with custom report file
.\ops\anr-pilot.ps1 -Auto -DryRun -ReportPath ".\path\to\custom_report.json"

# Manual stage with dry-run env preview
.\ops\anr-pilot.ps1 -Stage 50 -DryRun
```

## 📋 Health Checks

```powershell
# Quick status check
python -c "from orchestrator.config import config; print(f'ANR Enabled: {getattr(config, \"ANR_ENABLED\", \"Not Set\")}')"

# View bandit state summary
if (Test-Path run\anr_state.json) { (Get-Content run\anr_state.json | ConvertFrom-Json | Select-Object arms, total_pulls, best_arm) }

# Check state file size and age
Get-Item run\anr_state.json | Select-Object Length, LastWriteTime

# Verify Prometheus metrics endpoint
curl http://localhost:8000/metrics | Select-String "nova_anr"
```

## 🔥 One-Liners for Ops

```powershell
# Full status snapshot
Write-Host "=== ANR Status ===" -ForegroundColor Cyan; echo "ENV: ENABLED=$env:NOVA_ANR_ENABLED PILOT=$env:NOVA_ANR_PILOT"; Get-ChildItem ops\logs\anr_*.json | Sort-Object LastWriteTime -Desc | Select-Object -First 1 | % { (Get-Content $_.FullName | ConvertFrom-Json) | Select-Object action, stage, ts }

# Schedule the daily job (run once)
schtasks /Create /SC DAILY /TN "Nova ANR AutoPromotion" /TR "powershell -ExecutionPolicy Bypass -File C:\code\nova-civilizational-architecture\ops\anr-autopromo-daily.ps1" /ST 09:05

# Clean old receipts (keep 30 days)
Get-ChildItem ops\logs\anr_*.json | Where-Object LastWriteTime -lt (Get-Date).AddDays(-30) | Remove-Item

# Emergency: full stop and reset
.\ops\anr-pilot.ps1 -Rollback; schtasks /Change /TN "Nova ANR AutoPromotion" /DISABLE; Write-Host "ANR FULLY STOPPED" -ForegroundColor Red
```

## 🎯 Go/No-Go Decision (100% Deployment)

```powershell
# Check all gates manually
$report = Get-Content run\anr_daily_report.json | ConvertFrom-Json
echo "RSI: $($report.rsi) (need ≥0.85)"
echo "Rollbacks: $($report.rollbacks) per $($report.decisions) decisions"
echo "TRI Median: $($report.tri_median) (need ≥0)"

# Auto-check with detailed gate output
.\ops\anr-pilot.ps1 -Auto -DryRun -RequireTRI -Verbose
```
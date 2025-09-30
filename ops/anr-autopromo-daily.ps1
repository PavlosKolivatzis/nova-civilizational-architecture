# ANR Daily Auto-Promotion Job
# Generates fresh daily report and runs auto-promotion with TRI enforcement
# File lock prevents double-execution

param(
  [string]$LedgerPath = "run\anr_ledger.ndjson",
  [string]$ReportJson = "run\anr_daily_report.json"
)

Write-Host "ANR Daily Auto-Promotion Job" -ForegroundColor Cyan
Write-Host "Ledger: $LedgerPath"
Write-Host "Report: $ReportJson"

# File lock (30m stale protection)
$lock = "run\anr_autopromo.lock"
if (Test-Path $lock) {
  $ageMin = ((Get-Date) - (Get-Item $lock).LastWriteTime).TotalMinutes
  if ($ageMin -lt 30) {
    Write-Host "Another run is active (lock). Exiting." -ForegroundColor Yellow
    exit 0
  }
  Write-Host "Removing stale lock (age: $([math]::Round($ageMin,1))m)" -ForegroundColor Yellow
}

New-Item -ItemType File -Force -Path $lock | Out-Null
Write-Host "Lock acquired: $lock"

try {
  # 1) Rotate ledger if needed (before report generation)
  Write-Host ""
  Write-Host "=== Checking Ledger Rotation ===" -ForegroundColor Green
  if (Test-Path -LiteralPath "ops\anr-ledger-rotate.ps1") {
    & powershell -ExecutionPolicy Bypass -File "ops\anr-ledger-rotate.ps1" -LedgerPath $LedgerPath
  }

  # 2) Build fresh report (JSON)
  Write-Host ""
  Write-Host "=== Generating Daily Report ===" -ForegroundColor Green
  if (-not (Test-Path -LiteralPath "scripts\anr_daily_report.py")) {
    Write-Error "scripts/anr_daily_report.py not found"
    exit 2
  }

  $reportOutput = & python "scripts\anr_daily_report.py" --ledger $LedgerPath
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Daily report generation failed"
    exit 2
  }

  $reportOutput | Out-File -FilePath $ReportJson -Encoding utf8
  Write-Host "Report generated: $ReportJson"

  # 3) Auto-promotion (respect gates, TRI enforced)
  Write-Host ""
  Write-Host "=== Running Auto-Promotion ===" -ForegroundColor Green
  & powershell -ExecutionPolicy Bypass -File "ops\anr-pilot.ps1" -Auto -RequireTRI -ReportPath $ReportJson

  Write-Host ""
  Write-Host "Auto-promotion job completed (exit code: $LASTEXITCODE)" -ForegroundColor Green
}
catch {
  Write-Error "Auto-promotion job failed: $_"
  exit 1
}
finally {
  Remove-Item -LiteralPath $lock -ErrorAction SilentlyContinue
  Write-Host "Lock released"
}
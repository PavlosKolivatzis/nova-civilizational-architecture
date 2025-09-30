# ANR Disaster Recovery Drill
# Safe state backup restoration and validation test

param(
  [string]$StatePath = "run\anr_state.json",
  [string]$BackupDir = "run\anr_state_backups"
)

Write-Host "ANR DR Drill" -ForegroundColor Cyan

# Ensure a current backup exists
if (!(Test-Path $BackupDir)) { New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null }
if (Test-Path $StatePath) {
  $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
  Copy-Item -LiteralPath $StatePath -Destination (Join-Path $BackupDir "anr_state_$stamp.json") -Force
}

# Pick latest backup to restore
$latest = Get-ChildItem $BackupDir -Filter "anr_state_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $latest) { Write-Host "  - No backups found to restore" -ForegroundColor Yellow; exit 0 }

Copy-Item -LiteralPath $latest.FullName -Destination $StatePath -Force
Write-Host "  [OK] Restored state from $($latest.Name)" -ForegroundColor Green

# Validate JSON
try {
  $json = Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json
  Write-Host "  [OK] State JSON valid" -ForegroundColor Green
  exit 0
} catch {
  Write-Host "  [FAIL] State JSON invalid after restore: $_" -ForegroundColor Yellow
  exit 1
}
# ANR Ledger Rotation Script
# Manages NDJSON ledger file rotation with size caps and compression

param(
  [string]$LedgerPath = "run\anr_ledger.ndjson",
  [int]$MaxSizeMB = 100,
  [int]$KeepDays = 30
)

Write-Host "ANR Ledger Rotation" -ForegroundColor Cyan
Write-Host "Ledger: $LedgerPath"
Write-Host "Max size: ${MaxSizeMB}MB, Keep: ${KeepDays} days"

# Check if ledger file exists and needs rotation
if (-not (Test-Path $LedgerPath)) {
  Write-Host "No ledger file found at $LedgerPath" -ForegroundColor Yellow
  exit 0
}

$ledgerFile = Get-Item $LedgerPath
$sizeMB = [math]::Round($ledgerFile.Length / 1MB, 2)

Write-Host "Current ledger size: ${sizeMB}MB"

if ($sizeMB -lt $MaxSizeMB) {
  Write-Host "Ledger under size limit, no rotation needed" -ForegroundColor Green
  exit 0
}

# Rotate the ledger
$timestamp  = (Get-Date).ToString("yyyyMMdd_HHmmss")
$archiveDir = "run\anr_ledger_archive"
$rotated    = Join-Path $archiveDir "anr_ledger_$timestamp.ndjson"

# Create archive directory
if (-not (Test-Path $archiveDir)) {
  New-Item -ItemType Directory -Force -Path $archiveDir | Out-Null
}

try {
  # Try atomic-ish rename first (same-volume move)
  try {
    Move-Item -LiteralPath $LedgerPath -Destination $rotated -Force -ErrorAction Stop
    Write-Host "Rotated ledger to: $rotated" -ForegroundColor Green
  } catch {
    # Fallback if file is locked: copy then truncate
    Copy-Item -LiteralPath $LedgerPath -Destination $rotated -Force
    Clear-Content -LiteralPath $LedgerPath
    Write-Host "Copied & truncated ledger (locked source): $rotated" -ForegroundColor Yellow
  }

  # Zip the rotated file (native PS)
  $zip = "$rotated.zip"
  Compress-Archive -Path $rotated -DestinationPath $zip -Force
  Remove-Item -LiteralPath $rotated -Force
  Write-Host "Compressed to: $zip" -ForegroundColor Green

  # Create fresh empty ledger
  New-Item -ItemType File -Path $LedgerPath -Force | Out-Null
  Write-Host "Created new empty ledger" -ForegroundColor Green

  # Cleanup old archives
  $cutoff = (Get-Date).AddDays(-$KeepDays)
  $old = Get-ChildItem $archiveDir -Filter "anr_ledger_*.ndjson.zip" |
         Where-Object { $_.LastWriteTime -lt $cutoff }
  if ($old) {
    Write-Host "Removing $($old.Count) old archive(s):"
    foreach ($f in $old) { Write-Host "  - $($f.Name)"; Remove-Item -LiteralPath $f.FullName -Force }
  } else {
    Write-Host "No old archives to clean up"
  }

  $count = (Get-ChildItem $archiveDir -Filter "anr_ledger_*.ndjson.zip").Count
  Write-Host "Total archived files: $count" -ForegroundColor Green
  Write-Host "Ledger rotation completed successfully" -ForegroundColor Green
} catch {
  Write-Error "Ledger rotation failed: $_"
  exit 1
}
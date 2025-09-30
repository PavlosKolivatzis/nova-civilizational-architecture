# ANR State Backup Script
# Backs up ANR bandit state with timestamp and manages retention

param(
  [string]$StatePath = "run\anr_state.json",
  [string]$BackupDir = "run\anr_state_backups",
  [int]$Keep = 7
)

Write-Host "ANR State Backup Script" -ForegroundColor Cyan
Write-Host "State Path: $StatePath"
Write-Host "Backup Dir: $BackupDir"
Write-Host "Retention: $Keep backups"

# Check if state file exists
if (!(Test-Path $StatePath)) {
    Write-Host "No state file found at $StatePath" -ForegroundColor Yellow
    exit 0
}

# Create backup directory
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

# Generate timestamped backup filename
$timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$backupFile = Join-Path $BackupDir ("anr_state_" + $timestamp + ".json")

# Perform backup
try {
    Copy-Item -LiteralPath $StatePath -Destination $backupFile -Force
    Write-Host "Backed up to: $backupFile" -ForegroundColor Green

    # Get file size for verification
    $size = (Get-Item $backupFile).Length
    Write-Host "Backup size: $size bytes"
} catch {
    Write-Error "Backup failed: $_"
    exit 1
}

# Clean up old backups (keep only the most recent N)
try {
    $oldBackups = Get-ChildItem $BackupDir -Filter "anr_state_*.json" |
                  Sort-Object LastWriteTime -Descending |
                  Select-Object -Skip $Keep

    if ($oldBackups) {
        Write-Host "Cleaning up $($oldBackups.Count) old backup(s):"
        foreach ($backup in $oldBackups) {
            Write-Host "  Removing: $($backup.Name)"
            Remove-Item $backup.FullName -Force
        }
    } else {
        Write-Host "No old backups to clean up"
    }
} catch {
    Write-Warning "Cleanup failed: $_"
}

# Show current backup count
$totalBackups = (Get-ChildItem $BackupDir -Filter "anr_state_*.json").Count
Write-Host "Total backups retained: $totalBackups" -ForegroundColor Green

Write-Host "Backup completed successfully" -ForegroundColor Green
<# =====================================================================
  ANR Pilot Orchestrator
  File: ops/anr-pilot.ps1
  Usage:
    # Promote to 10% (default)
    .\ops\anr-pilot.ps1 -Stage 10 -AppUrl http://127.0.0.1:8000

    # Promote to 25%, with custom ledger path
    .\ops\anr-pilot.ps1 -Stage 25 -LedgerPath .\run\anr_ledger.ndjson

    # Roll back immediately (forces R4 guardrail)
    .\ops\anr-pilot.ps1 -Rollback

  Notes:
    • Reads/writes env in *this* session; run in the same shell as uvicorn for convenience
    • RSI/rollback summary reads a ledger NDJSON if present (schema below)
    • Fallback prints N/A if ledger not available
    • Writes a promotion receipt to ops/logs/anr_<timestamp>.json
    • Expects scripts/verify_pilot_ready.py to be present

  Suggested ledger NDJSON schema (one JSON per line):
    {
      "id":"<uuid>",
      "t":"2025-09-30T09:00:00Z",
      "shadow": {"route":"R2", "argmax":"R2"},
      "live":   {"route":"R2", "pilot":0.10},
      "rewards":{"deployment":{"slo_ok":1,"rollback":0,"error_rate":0.00}}
    }
===================================================================== #>

[CmdletBinding()]
param(
  [ValidateSet('10','25','50','75','100')]
  [string]$Stage = '10',

  [switch]$Rollback,

  [switch]$Auto,           # Auto-promotion mode
  [switch]$DryRun,         # Preview mode - don't apply env changes
  [switch]$RequireTRI,     # Enforce TRI median >= 0 if available

  # Your running app base URL (for /metrics etc. if you add those later)
  [string]$AppUrl = 'http://127.0.0.1:8000',

  # Where to persist bandit state (make it stable across restarts)
  [string]$StatePath = "$PSScriptRoot\..\run\anr_state.json",

  # Optional ledger NDJSON for RSI/rollback summary (if available)
  [string]$LedgerPath = "$PSScriptRoot\..\run\anr_ledger.ndjson",

  # Optional report JSON for auto-promotion (faster than parsing ledger)
  [string]$ReportPath = "$PSScriptRoot\..\run\anr_daily_report.json",

  # Lookback window (minutes) when computing RSI from ledger timestamps
  [int]$LookbackMinutes = 1440,  # 24h

  # Promotion gates (tune as needed)
  [double]$GateRSI = 0.85,
  [double]$GateRollbacksPerK = 0.1
)

function Write-Section($title) {
  Write-Host ""
  Write-Host ("=" * 58) -ForegroundColor DarkGray
  Write-Host ("  {0}" -f $title) -ForegroundColor Cyan
  Write-Host ("=" * 58) -ForegroundColor DarkGray
}

function Ensure-Dir($path) {
  # Create the parent directory of a file path, even if the file doesn't exist yet.
  $parent = Split-Path -Parent $path
  if (-not $parent -or $parent -eq "") { $parent = (Resolve-Path .).Path }
  if (-not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
  }
}

function Set-AnrEnv([double]$Pilot, [bool]$Enabled=$true) {
  # Core ANR flags (PS 5.1 compatible)
  if ($Enabled) { $env:NOVA_ANR_ENABLED = "1" } else { $env:NOVA_ANR_ENABLED = "0" }
  $env:NOVA_ANR_PILOT = ("{0:N2}" -f $Pilot)
  $env:NOVA_ANR_MAX_FAST_PROB = "0.15"
  $env:NOVA_ANR_STRICT_ON_ANOMALY = "1"
  $env:NOVA_ANR_LEARN_SHADOW = "1"
  $rp = Resolve-Path -LiteralPath $StatePath -ErrorAction SilentlyContinue
  $env:NOVA_ANR_STATE_PATH = if ($rp) { $rp.Path } else { $StatePath }

  # Common observability toggles (safe defaults)
  if (-not $env:NOVA_ENABLE_PROMETHEUS) { $env:NOVA_ENABLE_PROMETHEUS = "1" }

  Write-Host "ANR Enabled     : $($env:NOVA_ANR_ENABLED)"
  Write-Host "Pilot Fraction  : $($env:NOVA_ANR_PILOT)"
  Write-Host "State Path      : $($env:NOVA_ANR_STATE_PATH)"
  Write-Host "Strict/Anomaly  : $($env:NOVA_ANR_STRICT_ON_ANOMALY)"
}

function Invoke-Readiness() {
  Write-Section "Pilot Readiness Check"
  if (-not (Test-Path -LiteralPath ".\scripts\verify_pilot_ready.py")) {
    Write-Warning "scripts/verify_pilot_ready.py not found; skipping readiness check."
    return
  }
  $cmd = "python", ".\scripts\verify_pilot_ready.py"
  $p = Start-Process -FilePath $cmd[0] -ArgumentList $cmd[1..($cmd.Length-1)] -NoNewWindow -PassThru -Wait
  if ($p.ExitCode -ne 0) {
    throw "Readiness verification failed with exit code $($p.ExitCode)."
  }
  Write-Host "Readiness verification PASSED." -ForegroundColor Green
}

function Parse-Ndjson([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path)) { return @() }
  $lines = Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue
  $objs = @()
  foreach ($line in $lines) {
    $lineTrim = $line.Trim()
    if ($lineTrim.Length -eq 0) { continue }
    try {
      $o = $lineTrim | ConvertFrom-Json
      $objs += ,$o
    } catch {
      # skip bad line
    }
  }
  return $objs
}

function Get-AnrSummary([string]$Path, [int]$Minutes) {
  $summary = [ordered]@{
    source       = "ledger"
    lookback_min = $Minutes
    count        = 0
    live_rate    = $null
    rsi          = $null
    rollbacks    = $null
    tri_median   = $null
  }

  $objs = Parse-Ndjson -Path $Path
  if ($objs.Count -eq 0) {
    $summary.source = "none"
    return $summary
  }

  # Filter by time window if 't' field present
  $now = Get-Date
  $windowStart = $now.AddMinutes(-$Minutes)
  $windowObjs = @()
  foreach ($o in $objs) {
    if ($o.PSObject.Properties.Name -contains 't') {
      try {
        $ts = Get-Date $o.t
        if ($ts -ge $windowStart) { $windowObjs += ,$o }
      } catch {
        # skip bad timestamp
      }
    } else {
      $windowObjs = $objs  # no timestamps; use all
      break
    }
  }

  if ($windowObjs.Count -eq 0) {
    $summary.source = "ledger-empty-window"
    return $summary
  }

  $total = $windowObjs.Count
  $liveDec = 0
  $agree  = 0
  $rolls  = 0
  $tris = @()

  foreach ($o in $windowObjs) {
    if ($o.PSObject.Properties.Name -contains 'live') { $liveDec++ }
    $liveRoute   = $o.live.route
    $shadowArg   = $o.shadow.argmax
    if ($liveRoute -and $shadowArg -and ($liveRoute -eq $shadowArg)) { $agree++ }
    $rb = $o.rewards.deployment.rollback
    if ($rb -is [int] -or $rb -is [double]) { if ($rb -gt 0) { $rolls++ } }

    # Extract TRI delta for median calculation
    $triDelta = $null
    if ($o.PSObject.Properties.Name -contains 'rewards' -and $o.rewards.PSObject.Properties.Name -contains 'immediate') {
      $triDelta = $o.rewards.immediate.tri_delta_norm
    }
    if ($triDelta -is [int] -or $triDelta -is [double]) { $tris += ,[double]$triDelta }
  }

  $summary.count     = $total
  $summary.live_rate = if ($total -gt 0) { [math]::Round($liveDec / $total, 4) } else { $null }
  $summary.rsi       = if ($liveDec -gt 0) { [math]::Round($agree / $liveDec, 4) } else { $null }
  $summary.rollbacks = $rolls

  # Calculate TRI median if we have data
  if ($tris.Count -gt 0) {
    $sorted = $tris | Sort-Object
    $mid = [int]([math]::Floor($sorted.Count / 2))
    if ($sorted.Count % 2 -eq 1) {
      $summary.tri_median = $sorted[$mid]
    } else {
      $summary.tri_median = ($sorted[$mid-1] + $sorted[$mid]) / 2.0
    }
  }

  return $summary
}

function Write-Receipt([hashtable]$data) {
  $dir = "$PSScriptRoot\logs"
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
  $file = Join-Path $dir ("anr_" + $stamp + ".json")
  ($data | ConvertTo-Json -Depth 8) | Out-File -FilePath $file -Encoding UTF8
  Write-Host "Receipt written: $file" -ForegroundColor DarkGreen
}

function Stage-To-Pilot([string]$s) {
  switch ($s) {
    '10'  { return 0.10 }
    '25'  { return 0.25 }
    '50'  { return 0.50 }
    '75'  { return 0.75 }
    '100' { return 1.00 }
    default { throw "Unknown stage: $s" }
  }
}

function Get-GitShaShort {
  try {
    $sha = (git rev-parse --short HEAD) 2>$null
    if ($sha) { return "$sha".Trim() }
  } catch {}
  return $null
}

function Set-BuildSha {
  # Ensure NOVA_BUILD_SHA is available for containers/metrics
  $sha = Get-GitShaShort
  if ($sha) {
    $env:NOVA_BUILD_SHA = $sha
  } elseif (-not $env:NOVA_BUILD_SHA) {
    $env:NOVA_BUILD_SHA = "unknown"
  }
}

function Snapshot-NovaEnv {
  param([string]$OutPath)
  $dir = Split-Path -Parent $OutPath
  if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Get-ChildItem Env: | Where-Object { $_.Name -like 'NOVA_*' } |
    ForEach-Object { "$($_.Name)=$($_.Value)" } |
    Out-File -FilePath $OutPath -Encoding UTF8
  try { return (Resolve-Path -LiteralPath $OutPath).Path } catch { return $OutPath }
}

function Read-ReportOrLedger([string]$ReportPath, [string]$LedgerPath, [int]$Minutes) {
  # Try JSON report first (faster), fallback to ledger NDJSON
  if (Test-Path -LiteralPath $ReportPath) {
    try {
      $content = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json
      if ($content.window_minutes -eq $Minutes) {
        return $content
      }
    } catch {
      # Fall through to ledger
    }
  }

  # Fallback: parse ledger directly
  $summary = Get-AnrSummary -Path $LedgerPath -Minutes $Minutes
  return @{
    window_minutes = $Minutes
    decisions = $summary.count
    live_rate = $summary.live_rate
    rsi = $summary.rsi
    rollbacks = $summary.rollbacks
    tri_median = $summary.tri_median
  }
}

function Pilot-To-Stage([double]$pilot) {
  if ($pilot -ge 1.00) { return '100' }
  if ($pilot -ge 0.75) { return '75' }
  if ($pilot -ge 0.50) { return '50' }
  if ($pilot -ge 0.25) { return '25' }
  if ($pilot -ge 0.10) { return '10' }
  return '0'
}

function Next-Stage([string]$current) {
  switch ($current) {
    '0'   { return '10' }
    '10'  { return '25' }
    '25'  { return '50' }
    '50'  { return '75' }
    '75'  { return '100' }
    '100' { return '100' }  # Already at max
    default { return '10' }
  }
}

function Read-LastStage([string]$LogsDir) {
  if (-not (Test-Path -LiteralPath $LogsDir)) { return '0' }
  $latest = Get-ChildItem $LogsDir -Filter "anr_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not $latest) { return '0' }

  try {
    $receipt = Get-Content -LiteralPath $latest.FullName -Raw | ConvertFrom-Json
    if ($receipt.action -eq "promote") {
      return $receipt.stage
    }
  } catch {
    # Ignore bad receipt
  }
  return '0'
}

function Check-CriticalSlotsHealth([string]$HealthUrl = "http://localhost:8001/health/slots") {
  $criticalSlots = @('slot04', 'slot08_lock', 'slot09', 'slot10')
  try {
    $response = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 10 -ErrorAction Stop
    $unhealthy = @()

    foreach ($slot in $criticalSlots) {
      $status = $response.slots.$slot.status
      if ($status -ne 'healthy') {
        $unhealthy += "$slot ($status)"
      }
    }

    return @{
      healthy = ($unhealthy.Count -eq 0)
      unhealthy_slots = $unhealthy
    }
  } catch {
    return @{
      healthy = $false
      unhealthy_slots = @("health-check-failed: $_")
    }
  }
}

function Gates-Pass($metrics, [double]$GateRSI, [double]$GateRollbacksPerK, [bool]$RequireTRI, [bool]$CheckHealth = $true) {
  $reasons = @()

  # Health gate (check critical slots before other gates)
  if ($CheckHealth) {
    $healthCheck = Check-CriticalSlotsHealth
    if (-not $healthCheck.healthy) {
      $reasons += "Unhealthy slots: $($healthCheck.unhealthy_slots -join ', ')"
    }
  }

  # --- safe numeric extracts ---
  $rsi = $null;       if ($null -ne $metrics.rsi)       { [double]::TryParse("$($metrics.rsi)",       [ref]$rsi)       | Out-Null }
  $dec = 0;           if ($null -ne $metrics.decisions) { [int]::TryParse("$($metrics.decisions)",    [ref]$dec)       | Out-Null }
  $liveRate = $null;  if ($null -ne $metrics.live_rate) { [double]::TryParse("$($metrics.live_rate)", [ref]$liveRate)  | Out-Null }
  $roll = 0;          if ($null -ne $metrics.rollbacks) { [int]::TryParse("$($metrics.rollbacks)",    [ref]$roll)      | Out-Null }
  $triMed = $null;    if ($null -ne $metrics.tri_median){ [double]::TryParse("$($metrics.tri_median)",[ref]$triMed)    | Out-Null }

  # RSI gate
  if ($null -eq $rsi -or $rsi -lt $GateRSI) {
    $rsiVal = if ($null -eq $rsi) { "N/A" } else { $rsi }
    $reasons += "RSI $rsiVal < $GateRSI"
  }

  # Rollback rate per 1k *live* decisions (fallback to decisions if live_rate missing)
  $live = if ($null -ne $liveRate) { [int]([math]::Max(1, [math]::Round($liveRate * $dec))) } else { [int]([math]::Max(1,$dec)) }
  $rbPerK = [double]$roll * 1000.0 / [double]$live
  if ($rbPerK -gt $GateRollbacksPerK) {
    $reasons += "Rollbacks $([math]::Round($rbPerK,3))/1k > $GateRollbacksPerK/1k"
  }

  # TRI gate (if required)
  if ($RequireTRI -and ($null -eq $triMed -or $triMed -lt 0)) {
    $triVal = if ($null -eq $triMed) { "N/A" } else { $triMed }
    $reasons += "TRI median $triVal < 0"
  }
  return @{ pass = ($reasons.Count -eq 0); reasons = $reasons }
}

# ------------------ MAIN ------------------
Write-Section "ANR Pilot Orchestrator"

# Ensure build SHA is available for metrics/traceability
Set-BuildSha

if ($Rollback) {
  Write-Host "Rollback requested -> forcing R4 (ANR off)" -ForegroundColor Yellow
  Set-AnrEnv -Pilot 0.0 -Enabled:$false

  $receipt = @{
    action     = "rollback"
    ts         = (Get-Date).ToString("o")
    runbook_url = "https://github.com/your-org/nova-civilizational-architecture/blob/main/ops/runbook/anr-operations.md"
    env        = @{
      NOVA_ANR_ENABLED        = $env:NOVA_ANR_ENABLED
      NOVA_ANR_PILOT          = $env:NOVA_ANR_PILOT
      NOVA_ANR_STATE_PATH     = $env:NOVA_ANR_STATE_PATH
      NOVA_ANR_MAX_FAST_PROB  = $env:NOVA_ANR_MAX_FAST_PROB
      NOVA_ANR_STRICT_ON_ANOMALY = $env:NOVA_ANR_STRICT_ON_ANOMALY
    }
  }

  # Add git commit and environment snapshot
  $receipt.build_sha = Get-GitShaShort
  $envSnapPath = Join-Path $PSScriptRoot ("logs\env_" + (Get-Date).ToString("yyyyMMdd_HHmmss") + ".txt")
  $receipt.env_snapshot_path = Snapshot-NovaEnv -OutPath $envSnapPath

  Write-Receipt -data $receipt
  exit 0
}

# AUTO-PROMOTION MODE
if ($Auto) {
  Write-Host "Auto-promotion mode enabled" -ForegroundColor Cyan

  # Read metrics from report or ledger
  $metrics = Read-ReportOrLedger -ReportPath $ReportPath -LedgerPath $LedgerPath -Minutes $LookbackMinutes

  # Show current metrics
  Write-Section "Current Metrics (${LookbackMinutes}m window)"
  Write-Host ("Decisions: {0}" -f $metrics.decisions)
  Write-Host ("Live Rate: {0}" -f ($metrics.live_rate))
  Write-Host ("RSI      : {0}" -f ($metrics.rsi))
  Write-Host ("Rollbacks: {0}" -f ($metrics.rollbacks))
  if ($null -ne $metrics.tri_median) {
    Write-Host ("TRI Med. : {0:N3}" -f $metrics.tri_median)
  }

  # Determine current stage
  $logsDir = "$PSScriptRoot\logs"
  $currentStage = Read-LastStage -LogsDir $logsDir
  $nextStage = Next-Stage -current $currentStage

  Write-Host ""
  Write-Host "Current stage: $currentStage%  ->  Next: $nextStage%" -ForegroundColor Green

  # Check promotion gates
  $gateResult = Gates-Pass -metrics $metrics -GateRSI $GateRSI -GateRollbacksPerK $GateRollbacksPerK -RequireTRI $RequireTRI

  if ($gateResult.pass) {
    Write-Host "PASS All gates -> promoting to $nextStage%" -ForegroundColor Green
    if ($DryRun) {
      Write-Host "[DRY-RUN] Would promote to stage $nextStage%" -ForegroundColor Yellow
      exit 0
    }
    $Stage = $nextStage
  } else {
    Write-Host "FAIL Gates -> staying at $currentStage%" -ForegroundColor Red
    foreach ($reason in $gateResult.reasons) {
      Write-Host "   - $reason" -ForegroundColor Red
    }
    if ($currentStage -eq '0') {
      Write-Host "Cannot auto-promote from stage 0. Manual promotion required." -ForegroundColor Yellow
    }
    exit 1
  }
}

$p = Stage-To-Pilot -s $Stage
Write-Host "Target Stage: $Stage%  (Pilot=$p)" -ForegroundColor Green

# Ensure state path's directory exists (for later use)
Ensure-Dir -path $StatePath

# Readiness verification BEFORE applying pilot env (tests expect defaults)
try {
  Invoke-Readiness
} catch {
  Write-Error $_
  exit 2
}

# Now apply env for the target stage
Set-AnrEnv -Pilot $p -Enabled:$true

# Optional: compute RSI/rollback summary from ledger if present
Write-Section "RSI / Rollback Summary (Lookback=${LookbackMinutes}m)"
$summary = Get-AnrSummary -Path $LedgerPath -Minutes $LookbackMinutes
if ($summary.source -eq 'none') {
  Write-Host "Ledger not found: $LedgerPath" -ForegroundColor DarkYellow
  Write-Host "RSI: N/A   Rollbacks: N/A"
} elseif ($summary.source -eq 'ledger-empty-window') {
  Write-Host "Ledger has no entries in last $LookbackMinutes minutes." -ForegroundColor DarkYellow
  Write-Host "RSI: N/A   Rollbacks: N/A"
} else {
  Write-Host ("Count     : {0}" -f $summary.count)
  $lr  = if ($null -ne $summary.live_rate) { $summary.live_rate } else { "N/A" }
  $rsi = if ($null -ne $summary.rsi)       { $summary.rsi }       else { "N/A" }
  $rb  = if ($null -ne $summary.rollbacks) { $summary.rollbacks } else { "N/A" }
  Write-Host ("LiveRate  : {0}" -f $lr)
  Write-Host ("RSI       : {0}" -f $rsi)
  Write-Host ("Rollbacks : {0}" -f $rb)
}

# Write promotion receipt with full traceability
$receipt = @{
  action     = "promote"
  stage      = $Stage
  pilot      = $p
  ts         = (Get-Date).ToString("o")
  app_url    = $AppUrl
  runbook_url = "https://github.com/your-org/nova-civilizational-architecture/blob/main/ops/runbook/anr-operations.md"
  env        = @{
    NOVA_ANR_ENABLED        = $env:NOVA_ANR_ENABLED
    NOVA_ANR_PILOT          = $env:NOVA_ANR_PILOT
    NOVA_ANR_STATE_PATH     = $env:NOVA_ANR_STATE_PATH
    NOVA_ANR_MAX_FAST_PROB  = $env:NOVA_ANR_MAX_FAST_PROB
    NOVA_ANR_STRICT_ON_ANOMALY = $env:NOVA_ANR_STRICT_ON_ANOMALY
    NOVA_ANR_LEARN_SHADOW   = $env:NOVA_ANR_LEARN_SHADOW
  }
  summary    = $summary
}

# Add git commit and environment snapshot
$receipt.build_sha = Get-GitShaShort
$envSnapPath = Join-Path $PSScriptRoot ("logs\env_" + (Get-Date).ToString("yyyyMMdd_HHmmss") + ".txt")
$receipt.env_snapshot_path = Snapshot-NovaEnv -OutPath $envSnapPath

Write-Receipt -data $receipt

Write-Host ""
Write-Host "Pilot stage applied. Keep uvicorn single-worker for counter accuracy:" -ForegroundColor DarkCyan
Write-Host "  uvicorn orchestrator.app:app --host 0.0.0.0 --port 8000 --workers 1"
Write-Host ""
Write-Host "Rollback any time:" -ForegroundColor Yellow
Write-Host "  .\ops\anr-pilot.ps1 -Rollback"
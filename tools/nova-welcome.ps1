# Nova Welcome — Agent Entry Protocol (PowerShell)
# Displays Nova metadata + live runtime state
# Usage: .\tools\nova-welcome.ps1 [-Json] [-Compact]

param(
    [switch]$Json,
    [switch]$Compact
)

$ErrorActionPreference = "SilentlyContinue"
Set-Location (Split-Path $PSScriptRoot -Parent)

# ============================================================================
# Gather Live State
# ============================================================================

$gitCommit = (git log -1 --format='%h' 2>$null) -replace "`n", ""
$gitDate = (git log -1 --format='%ai' 2>$null) -replace "`n", ""
$gitSubject = (git log -1 --format='%s' 2>$null) -replace "`n", ""
$gitBranch = (git branch --show-current 2>$null) -replace "`n", ""

if (-not $gitCommit) { $gitCommit = "unknown" }
if (-not $gitDate) { $gitDate = "unknown" }
if (-not $gitBranch) { $gitBranch = "detached" }

# Maturity score
$maturityJson = npm run maturity --silent 2>$null | Out-String
$maturityScore = if ($maturityJson) {
    try {
        ($maturityJson | ConvertFrom-Json).overall
    } catch {
        "N/A"
    }
} else {
    "N/A"
}

# Test count
$testCount = if (Test-Path "docs/maturity.yaml") {
    (Select-String -Path "docs/maturity.yaml" -Pattern "tests_passed:" -List | Select-Object -First 1).Line -replace '.*:\s*', ''
} else {
    "N/A"
}

# Phase
$phase = if (Test-Path ".nova/meta.yaml") {
    (Select-String -Path ".nova/meta.yaml" -Pattern "^\s+phase:" -List | Select-Object -First 1).Line -replace '.*:\s*', '' -replace '"', ''
} else {
    "unknown"
}

# Audit date
$auditDate = if (Test-Path ".artifacts/audit_master_summary.md") {
    (Select-String -Path ".artifacts/audit_master_summary.md" -Pattern "^\*\*Audit Period\*\*:" -List | Select-Object -First 1).Line -replace '.*:\s*', ''
} else {
    "N/A"
}

# ============================================================================
# Output Modes
# ============================================================================

if ($Json) {
    @{
        system = @{
            name = "Nova Civilizational Architecture"
            tagline = "Observe → Canonize → Attest → Publish"
            phase = $phase
        }
        runtime = @{
            git = @{
                commit = $gitCommit
                date = $gitDate
                branch = $gitBranch
                subject = $gitSubject
            }
            maturity = @{
                score = $maturityScore
                test_count = $testCount
            }
            audit = @{
                date = $auditDate
            }
        }
        learning_path = @{
            primer = "agents/nova_ai_operating_framework.md"
            architecture = "docs/architecture.md"
            slot_specs = "docs/slots/"
            metadata = ".nova/meta.yaml"
        }
    } | ConvertTo-Json -Depth 10
} elseif ($Compact) {
    Write-Output "Nova | commit=$gitCommit | phase=$phase | maturity=$maturityScore | tests=$testCount | branch=$gitBranch"
} else {
    Write-Output @"
╔════════════════════════════════════════════════════════════════════════════╗
║                   Nova Civilizational Architecture                         ║
║                  Observe → Canonize → Attest → Publish                     ║
╚════════════════════════════════════════════════════════════════════════════╝

🌟 Welcome to Nova

  Nova is a 10-slot AI governance system implementing provenance-first,
  immutable attestation, and civilizational-scale safety protocols.

📊 Current State

  Phase:     $phase
  Commit:    $gitCommit ($gitDate)
  Branch:    $gitBranch
  Maturity:  $maturityScore (Processual = 4.0)
  Tests:     $testCount passing
  Audit:     Last run $auditDate

🧭 Quick Start

  1. Read the primer:
     → agents/nova_ai_operating_framework.md
     (Understand: Rule of Sunlight, 3 ledgers, 6 invariants)

  2. Explore the architecture:
     → docs/architecture.md (10-slot system map)
     → docs/slots/*.md (individual slot specs)

  3. Inspect metadata:
     → .nova/meta.yaml (this file is your navigation index)

  4. Verify runtime state:
     → pytest -q -m "not slow"  (run tests)
     → npm run maturity         (check maturity scores)
     → curl localhost:8000/metrics | grep nova_  (if NOVA_ENABLE_PROMETHEUS=1)

🎰 The 10 Slots

  Slot 01: Truth Anchor             Slot 06: Cultural Synthesis
  Slot 02: ΔTHRESH Manager           Slot 07: Production Controls
  Slot 03: Emotional Matrix          Slot 08: Memory Ethics Guard
  Slot 04: TRI Engine                Slot 09: Distortion Protection
  Slot 05: Constellation             Slot 10: Civilizational Deployment

🔐 Agent Protocol

  • Default mode: read-only
  • Consent required for writes (request from Slot10)
  • All actions observable (logged, metered, auditable)
  • Follow: .nova/meta.yaml → agent_protocol section

📚 Deep Dive

  Learn more:
    .nova/meta.yaml           → Full navigation index + learning path
    agents/nova_ai_operating_framework.md → Operating doctrine
    docs/INTERSLOT_CONTRACTS.md → Contract stability model

  Get live state:
    .\tools\nova-welcome.ps1 -Json     → Machine-readable JSON
    .\tools\nova-welcome.ps1 -Compact  → Single-line status

╔════════════════════════════════════════════════════════════════════════════╗
║  Nova is self-aware. This metadata reflects its current architecture.     ║
║  To update: edit .nova/meta.yaml (stable) or re-run this script (live).   ║
╚════════════════════════════════════════════════════════════════════════════╝

"@
}

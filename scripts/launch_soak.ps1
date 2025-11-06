# Phase 15-8.5 A/B Soak — PowerShell Launch Helper
# Run this in PowerShell to start the soak server

param(
    [string]$Combo = "1",
    [string]$Port = "8100"
)

# Combo configurations
$configs = @{
    "1" = @{ kappa = "0.01"; g0 = "0.55"; desc = "κ=0.01, G₀=0.55 (low bias, low target)" }
    "2" = @{ kappa = "0.01"; g0 = "0.60"; desc = "κ=0.01, G₀=0.60 (low bias, current target)" }
    "3" = @{ kappa = "0.01"; g0 = "0.65"; desc = "κ=0.01, G₀=0.65 (low bias, high target)" }
    "4" = @{ kappa = "0.02"; g0 = "0.55"; desc = "κ=0.02, G₀=0.55 (current bias, low target)" }
    "5" = @{ kappa = "0.02"; g0 = "0.60"; desc = "κ=0.02, G₀=0.60 (CURRENT DEFAULTS)" }
    "6" = @{ kappa = "0.02"; g0 = "0.65"; desc = "κ=0.02, G₀=0.65 (current bias, high target)" }
}

if (-not $configs.ContainsKey($Combo)) {
    Write-Host "Error: Invalid combo '$Combo'. Use 1-6." -ForegroundColor Red
    Write-Host ""
    Write-Host "Available combos:"
    foreach ($key in 1..6) {
        $c = $configs["$key"]
        Write-Host "  $key - $($c.desc)"
    }
    exit 1
}

$config = $configs[$Combo]

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Starting Soak Server - Combo $Combo" -ForegroundColor Cyan
Write-Host $config.desc -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
$env:NOVA_WISDOM_GOVERNOR_ENABLED = "1"
$env:NOVA_WISDOM_BACKPRESSURE_ENABLED = "1"
$env:NOVA_WISDOM_TRI_FEEDBACK_ENABLED = "1"
$env:NOVA_ENABLE_PROMETHEUS = "1"
$env:JWT_SECRET = "dev"
$env:NOVA_WISDOM_G_KAPPA = $config.kappa
$env:NOVA_WISDOM_G_TARGET = $config.g0

Write-Host "Environment configured:" -ForegroundColor Green
Write-Host "  NOVA_WISDOM_G_KAPPA  = $env:NOVA_WISDOM_G_KAPPA"
Write-Host "  NOVA_WISDOM_G_TARGET = $env:NOVA_WISDOM_G_TARGET"
Write-Host ""
Write-Host "Starting uvicorn on port $Port..." -ForegroundColor Green
Write-Host ""

# Start uvicorn
python -m uvicorn orchestrator.app:app --host 127.0.0.1 --port $Port --workers 1

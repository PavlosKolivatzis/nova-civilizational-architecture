#!/usr/bin/env pwsh
# =============================================================================
# Nova Orchestrator - Development Server Launcher
# =============================================================================
# Phase 14.6 operational integration - runs orchestrator with Phase 14 flags
#
# Usage:
#   .\scripts\run_orchestrator_dev.ps1
#   .\scripts\run_orchestrator_dev.ps1 -EnableGovernance  # Enable temporal governance
#
# Rollback: Ctrl+C to stop server
# =============================================================================

param(
    [switch]$EnableGovernance = $false,
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1"
)

# Set PYTHONPATH to src/ so 'nova' module is importable
$env:PYTHONPATH = "$PSScriptRoot\..\src"

# Phase 14 feature flags (metrics-only mode by default)
$env:NOVA_ENABLE_BIAS_DETECTION = "1"
$env:NOVA_ENABLE_USM_TEMPORAL = "1"
$env:NOVA_ENABLE_TEMPORAL_GOVERNANCE = if ($EnableGovernance) { "1" } else { "0" }
$env:NOVA_ENABLE_PROMETHEUS = "1"  # Enable /metrics endpoint

# Development settings
$env:NOVA_LOG_LEVEL = "INFO"
$env:JWT_SECRET = "dev-secret-minimum-32-characters-long-for-testing-only"

Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "Nova Orchestrator - Development Server (Phase 14.6)" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  PYTHONPATH:                     $env:PYTHONPATH"
Write-Host "  NOVA_ENABLE_BIAS_DETECTION:     $env:NOVA_ENABLE_BIAS_DETECTION"
Write-Host "  NOVA_ENABLE_USM_TEMPORAL:       $env:NOVA_ENABLE_USM_TEMPORAL"
Write-Host "  NOVA_ENABLE_TEMPORAL_GOVERNANCE: $env:NOVA_ENABLE_TEMPORAL_GOVERNANCE"
Write-Host "  NOVA_ENABLE_PROMETHEUS:         $env:NOVA_ENABLE_PROMETHEUS"
Write-Host ""
Write-Host "Server:" -ForegroundColor Yellow
Write-Host "  URL:     http://${BindHost}:${Port}"
Write-Host "  Metrics: http://${BindHost}:${Port}/metrics"
Write-Host "  Health:  http://${BindHost}:${Port}/health"
Write-Host ""
Write-Host "Press Ctrl+C to stop server" -ForegroundColor Gray
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

# Start uvicorn with orchestrator app
python -m uvicorn nova.orchestrator.app:app --host $BindHost --port $Port --workers 1

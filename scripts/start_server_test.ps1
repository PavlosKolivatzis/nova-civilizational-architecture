# PowerShell script to start uvicorn with creativity env vars
$env:NOVA_CREATIVITY_EARLY_STOP = "1"
$env:NOVA_CREATIVITY_TWO_PHASE = "1"
$env:NOVA_CREATIVITY_BNB = "1"
$env:NOVA_CREATIVITY_EARLY_STOP_SCORE = "0.62"
$env:NOVA_CREATIVITY_BNB_Q = "0.40"
$env:NOVA_CREATIVITY_BNB_MARGIN = "0.05"

Write-Host "Starting uvicorn with creativity flags enabled..."
Write-Host "Env vars set:"
Write-Host "  NOVA_CREATIVITY_EARLY_STOP=$env:NOVA_CREATIVITY_EARLY_STOP"
Write-Host "  NOVA_CREATIVITY_TWO_PHASE=$env:NOVA_CREATIVITY_TWO_PHASE"
Write-Host "  NOVA_CREATIVITY_BNB=$env:NOVA_CREATIVITY_BNB"

python -m uvicorn orchestrator.app:app --host 0.0.0.0 --port 8002 --workers 1 --log-level info
